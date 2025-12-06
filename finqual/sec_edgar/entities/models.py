from pydantic import BaseModel

class IdCode(BaseModel):
    cik: str
    name: str
    ticker: str
    exchange: str | None 