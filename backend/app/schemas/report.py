from pydantic import BaseModel


class CsvImportItemResult(BaseModel):
    url: str
    note: str | None
    status: str
    item_id: str | None = None
    message: str


class CsvImportResponse(BaseModel):
    total_rows: int
    created_count: int
    skipped_count: int
    failed_count: int
    results: list[CsvImportItemResult]
