from pydantic import BaseModel
import polars as pl

class CompanyIdCode(BaseModel):
    cik: str
    name: str
    ticker: str
    exchange: str | None
    
class CompanyFacts(BaseModel):
    sec_data: pl.DataFrame
    taxonomy: str
    currency: str
    dei: dict | None
    
    model_config = {
        "arbitrary_types_allowed": True
    }
    
class CompanySubmission(BaseModel):
    latest_10k: int
    report_date: str
    sector: str | None
    reports: pl.DataFrame
    