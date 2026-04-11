import base64
import string
import time
from decimal import Decimal
from typing import Any

import httpx
from fastapi import HTTPException, status

from app.core.config import get_settings
from app.schemas.ebay import EbayItemData


def _build_basic_authorization_header(client_id: str, client_secret: str) -> tuple[str, str]:
    raw_credentials = f"{client_id}:{client_secret}"
    encoded = base64.b64encode(raw_credentials.encode("utf-8")).decode("utf-8")
    return f"Basic {encoded}", raw_credentials


def _mask_authorization_header(header_value: str) -> str:
    if not header_value.startswith("Basic "):
        return header_value
    token = header_value[6:]
    if len(token) <= 12:
        return "Basic ***"
    return f"Basic {token[:8]}...{token[-8:]}"


def get_access_token(debug: bool = False) -> str:
    payload = request_access_token(debug=debug)
    return payload["access_token"]


def request_access_token(debug: bool = False) -> dict[str, Any]:
    settings = get_settings()

    client_id = settings.ebay_client_id.strip()
    client_secret = settings.ebay_client_secret.strip()
    if not client_id or not client_secret:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Missing eBay API credentials.",
        )

    request_url = f"{settings.ebay_auth_base_url.rstrip('/')}/identity/v1/oauth2/token"
    authorization_header, raw_credentials = _build_basic_authorization_header(client_id, client_secret)
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization": authorization_header,
    }
    body = {
        "grant_type": "client_credentials",
        "scope": settings.ebay_oauth_scope,
    }

    if debug:
        print(f"Request URL: {request_url}")
        print(f"Authorization Header: {_mask_authorization_header(authorization_header)}")
        print(f"Credential Pair Contains Colon: {':' in raw_credentials}")

    try:
        with httpx.Client(timeout=settings.ebay_request_timeout_seconds) as client:
            response = client.post(
                request_url,
                headers=headers,
                data=body,
            )
    except (httpx.TimeoutException, httpx.NetworkError) as exc:
        if debug:
            print(f"Response Body: network_error={exc}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to obtain eBay access token: {exc}",
        ) from exc

    response_body: Any
    try:
        response_body = response.json()
    except ValueError:
        response_body = response.text

    if debug:
        print(f"Response Status: {response.status_code}")
        print(f"Response Body: {response_body}")

    if response.status_code >= 400:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to obtain eBay access token: status={response.status_code}, body={response_body}",
        )

    return response_body


class EbayClient:
    def __init__(self) -> None:
        self.settings = get_settings()
        self._access_token: str | None = None
        self._access_token_expires_at: float = 0.0

    def get_item_by_legacy_id(self, legacy_item_id: str, marketplace_id: str) -> EbayItemData:
        token = self._get_valid_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "X-EBAY-C-MARKETPLACE-ID": marketplace_id,
        }
        params = {"legacy_item_id": legacy_item_id}

        last_exception: Exception | None = None
        for attempt in range(1, self.settings.ebay_max_retries + 1):
            try:
                with httpx.Client(timeout=self.settings.ebay_request_timeout_seconds) as client:
                    response = client.get(
                        f"{self.settings.ebay_api_base_url}/buy/browse/v1/item/get_item_by_legacy_id",
                        headers=headers,
                        params=params,
                    )

                if response.status_code == status.HTTP_401_UNAUTHORIZED and attempt < self.settings.ebay_max_retries:
                    self._access_token = None
                    self._access_token_expires_at = 0.0
                    token = self._get_valid_token()
                    headers["Authorization"] = f"Bearer {token}"
                    continue

                if response.status_code >= 500 and attempt < self.settings.ebay_max_retries:
                    time.sleep(0.5 * attempt)
                    continue

                response.raise_for_status()
                payload = response.json()
                return self._map_item_payload(payload)
            except (httpx.TimeoutException, httpx.NetworkError, httpx.HTTPStatusError) as exc:
                last_exception = exc
                if attempt >= self.settings.ebay_max_retries:
                    break
                time.sleep(0.5 * attempt)

        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to fetch eBay item data after retries: {last_exception}",
        )

    def search_items_by_seller_username(self, seller_username: str, marketplace_id: str) -> list[Any]:
        token = self._get_valid_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "X-EBAY-C-MARKETPLACE-ID": marketplace_id,
        }

        # Browse Search currently rejects seller-only queries for some accounts.
        # Use a sharded q-search strategy and merge by legacy item id.
        all_items: dict[str, dict[str, Any]] = {}
        limit = 50
        max_items = 500
        query_seeds = list(string.ascii_lowercase) + list(string.digits)

        for seed in query_seeds:
            offset = 0
            for _ in range(2):
                params = {
                    "q": seed,
                    "filter": f"sellers:{{{seller_username}}}",
                    "limit": str(limit),
                    "offset": str(offset),
                }
                payload = self._request_with_retries(
                    path="/buy/browse/v1/item_summary/search",
                    headers=headers,
                    params=params,
                )
                items = payload.get("itemSummaries", [])
                if not items:
                    break

                for item in items:
                    legacy_item_id = str(item.get("legacyItemId") or item.get("itemId") or "").split("|")[-1]
                    if not legacy_item_id:
                        continue
                    all_items[legacy_item_id] = item
                    if len(all_items) >= max_items:
                        break

                if len(all_items) >= max_items or len(items) < limit:
                    break
                offset += limit

            if len(all_items) >= max_items:
                break

        from app.services.shop_scan_service import ShopListingSnapshot

        return [self._map_item_summary_payload(item) for item in all_items.values()]

    def _get_valid_token(self) -> str:
        now = time.time()
        if self._access_token and now < self._access_token_expires_at:
            return self._access_token

        payload = request_access_token(debug=False)
        self._access_token = payload["access_token"]
        expires_in = int(payload.get("expires_in", 7200))
        self._access_token_expires_at = now + max(expires_in - 60, 60)
        return self._access_token

    def _request_with_retries(self, path: str, headers: dict[str, str], params: dict[str, str]) -> dict[str, Any]:
        last_exception: Exception | None = None
        request_headers = headers.copy()

        for attempt in range(1, self.settings.ebay_max_retries + 1):
            try:
                with httpx.Client(timeout=self.settings.ebay_request_timeout_seconds) as client:
                    response = client.get(
                        f"{self.settings.ebay_api_base_url}{path}",
                        headers=request_headers,
                        params=params,
                    )

                if response.status_code == status.HTTP_401_UNAUTHORIZED and attempt < self.settings.ebay_max_retries:
                    self._access_token = None
                    self._access_token_expires_at = 0.0
                    token = self._get_valid_token()
                    request_headers["Authorization"] = f"Bearer {token}"
                    continue

                if response.status_code >= 500 and attempt < self.settings.ebay_max_retries:
                    time.sleep(0.5 * attempt)
                    continue

                response.raise_for_status()
                return response.json()
            except (httpx.TimeoutException, httpx.NetworkError, httpx.HTTPStatusError) as exc:
                last_exception = exc
                if attempt >= self.settings.ebay_max_retries:
                    break
                time.sleep(0.5 * attempt)

        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to fetch eBay data after retries: {last_exception}",
        )

    def _map_item_payload(self, payload: dict) -> EbayItemData:
        price_payload = payload.get("price") or {}
        shipping_payload = payload.get("shippingOptions") or []
        first_shipping = shipping_payload[0] if shipping_payload else {}
        shipping_cost_payload = first_shipping.get("shippingCost") or {}
        image_payload = payload.get("image") or {}
        seller_payload = payload.get("seller") or {}
        condition_payload = payload.get("condition") or payload.get("conditionId")

        return EbayItemData(
            title=payload.get("title") or "",
            price=Decimal(price_payload.get("value") or "0"),
            currency=price_payload.get("currency") or "",
            shipping_cost=Decimal(shipping_cost_payload.get("value") or "0"),
            seller_name=seller_payload.get("username"),
            condition=str(condition_payload) if condition_payload is not None else None,
            availability=payload.get("availability") or payload.get("estimatedAvailabilities", [{}])[0].get("availabilityStatus"),
            image=image_payload.get("imageUrl"),
            item_url=payload.get("itemWebUrl") or "",
        )

    def _map_item_summary_payload(self, payload: dict) -> Any:
        from app.services.shop_scan_service import ShopListingSnapshot

        price_payload = payload.get("price") or {}
        shipping_payload = payload.get("shippingOptions") or []
        first_shipping = shipping_payload[0] if shipping_payload else {}
        shipping_cost_payload = first_shipping.get("shippingCost") or {}
        image_payload = payload.get("image") or {}
        item_id = payload.get("legacyItemId") or payload.get("itemId") or ""

        price = Decimal(price_payload.get("value")) if price_payload.get("value") is not None else None
        shipping_cost = (
            Decimal(shipping_cost_payload.get("value")) if shipping_cost_payload.get("value") is not None else Decimal("0")
        )
        total_cost = None if price is None else (price + shipping_cost).quantize(Decimal("0.01"))

        return ShopListingSnapshot(
            legacy_item_id=str(item_id).split("|")[-1],
            title=payload.get("title") or "",
            item_url=payload.get("itemWebUrl") or "",
            image_url=image_payload.get("imageUrl"),
            currency=price_payload.get("currency"),
            price=price,
            shipping_cost=shipping_cost,
            total_cost=total_cost,
            availability=payload.get("availability") or payload.get("buyingOptions", [None])[0],
        )
