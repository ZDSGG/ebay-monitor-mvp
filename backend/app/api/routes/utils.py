from fastapi import APIRouter

from app.schemas.url_parser import EbayUrlParseRequest, EbayUrlParseResponse
from app.services.url_parser import parse_ebay_item_url


router = APIRouter(prefix="/utils", tags=["utils"])


@router.post("/parse-ebay-url", response_model=EbayUrlParseResponse)
def parse_ebay_url(payload: EbayUrlParseRequest) -> EbayUrlParseResponse:
    result = parse_ebay_item_url(str(payload.url))
    return EbayUrlParseResponse(
        marketplace=result.marketplace.value,
        legacy_item_id=result.legacy_item_id,
        normalized_url=result.normalized_url,
    )
