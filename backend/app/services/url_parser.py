import re
from dataclasses import dataclass
from urllib.parse import parse_qs, urlparse

from fastapi import HTTPException, status

from app.models.enums import Marketplace


DOMAIN_TO_MARKETPLACE = {
    "www.ebay.com": Marketplace.EBAY_US,
    "ebay.com": Marketplace.EBAY_US,
    "www.ebay.co.uk": Marketplace.EBAY_UK,
    "ebay.co.uk": Marketplace.EBAY_UK,
    "www.ebay.de": Marketplace.EBAY_DE,
    "ebay.de": Marketplace.EBAY_DE,
    "www.ebay.com.au": Marketplace.EBAY_AU,
    "ebay.com.au": Marketplace.EBAY_AU,
}

PATH_PATTERNS = [
    re.compile(r"/itm/(?:[^/]+/)?(?P<item_id>\d{9,15})"),
    re.compile(r"/p/(?P<item_id>\d{9,15})"),
]


@dataclass(slots=True)
class ParsedEbayUrl:
    marketplace: Marketplace
    legacy_item_id: str
    normalized_url: str


def parse_ebay_item_url(url: str) -> ParsedEbayUrl:
    parsed = urlparse(url)
    host = parsed.netloc.lower()

    if host not in DOMAIN_TO_MARKETPLACE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported eBay marketplace domain.",
        )

    legacy_item_id = _extract_legacy_item_id(parsed.path, parsed.query)
    normalized_url = f"{parsed.scheme}://{host}{parsed.path}"

    return ParsedEbayUrl(
        marketplace=DOMAIN_TO_MARKETPLACE[host],
        legacy_item_id=legacy_item_id,
        normalized_url=normalized_url,
    )


def _extract_legacy_item_id(path: str, query: str) -> str:
    for pattern in PATH_PATTERNS:
        matched = pattern.search(path)
        if matched:
            return matched.group("item_id")

    query_params = parse_qs(query)
    for key in ("item", "itemId", "legacy_item_id"):
        values = query_params.get(key, [])
        for value in values:
            if re.fullmatch(r"\d{9,15}", value):
                return value

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Could not extract legacy_item_id from eBay URL.",
    )
