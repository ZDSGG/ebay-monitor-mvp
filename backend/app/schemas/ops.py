from pydantic import BaseModel


class CrawlTriggerResponse(BaseModel):
    requested: int
    succeeded: int
    failed: int
    trigger_source: str
