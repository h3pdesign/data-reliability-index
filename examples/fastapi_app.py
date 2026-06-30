from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from data_reliability.core import ReliabilityMetadata, ReliabilityPolicy, DataTier

app = FastAPI(title="Data Reliability API")

STRICT_POLICY = ReliabilityPolicy(minimum_score=90, maximum_tier=DataTier.TIER_2)

class IngestionPayload(BaseModel):
    sensor_id: str
    value: float
    reliability: ReliabilityMetadata

@app.post("/ingest")
def ingest_data(payload: IngestionPayload):
    if not STRICT_POLICY.allows(payload.reliability):
        raise HTTPException(
            status_code=422,
            detail=f"Data rejected. Fails policy: min_score={STRICT_POLICY.minimum_score}, max_tier={STRICT_POLICY.maximum_tier.name}"
        )
    return {"status": "accepted", "stored_value": payload.value}
