from dataclasses import dataclass
from urllib.parse import parse_qs, urlparse

from fastapi import HTTPException, status

from app.models.enums import Marketplace


_HOST_MARKETPLACE_MAP = {
    "www.ebay.com": Marketplace.EBAY_US,
    "ebay.com": Marketplace.EBAY_US,
    "www.ebay.co.uk": Marketplace.EBAY_UK,
    "ebay.co.uk": Marketplace.EBAY_UK,
    "www.ebay.de": Marketplace.EBAY_DE,
    "ebay.de": Marketplace.EBAY_DE,
    "www.ebay.com.au": Marketplace.EBAY_AU,
    "ebay.com.au": Marketplace.EBAY_AU,
}


@dataclass(slots=True)
class ParsedShopUrl:
    marketplace: Marketplace
    seller_username: str
    shop_name: str
    normalized_url: str


def parse_ebay_shop_url(url: str) -> ParsedShopUrl:
    parsed = urlparse(url)
    host = parsed.netloc.lower()
    marketplace = _HOST_MARKETPLACE_MAP.get(host)
    if marketplace is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported eBay marketplace host for shop URL.",
        )

    path_parts = [part for part in parsed.path.split("/") if part]
    query = parse_qs(parsed.query)

    seller_username: str | None = None
    shop_name: str | None = None

    if len(path_parts) >= 2 and path_parts[0] == "usr":
        seller_username = path_parts[1]
        shop_name = seller_username
    elif len(path_parts) >= 2 and path_parts[0] == "str":
        shop_name = path_parts[1]
        seller_username = query.get("_ssn", [None])[0] or path_parts[1]
    elif path_parts and path_parts[0] == "sch":
        seller_username = query.get("_ssn", [None])[0]
        shop_name = seller_username

    if seller_username:
        seller_username = seller_username.strip()
    if shop_name:
        shop_name = shop_name.strip()

    if not seller_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not extract seller username from eBay shop URL.",
        )

    normalized_shop_name = shop_name or seller_username
    if len(path_parts) >= 2 and path_parts[0] == "str" and query.get("_ssn", [None])[0] is None:
        normalized_url = f"https://{host}/str/{normalized_shop_name}"
    else:
        normalized_url = f"https://{host}/usr/{seller_username}"

    return ParsedShopUrl(
        marketplace=marketplace,
        seller_username=seller_username,
        shop_name=normalized_shop_name,
        normalized_url=normalized_url,
    )
