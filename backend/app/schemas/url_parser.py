from pydantic import BaseModel, ConfigDict, HttpUrl


class EbayUrlParseRequest(BaseModel):
    url: HttpUrl


class EbayUrlParseResponse(BaseModel):
    marketplace: str
    legacy_item_id: str
    normalized_url: str

    model_config = ConfigDict(from_attributes=True)
