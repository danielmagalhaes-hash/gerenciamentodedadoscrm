from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class SendflowRelease(BaseModel):
    id: str
    name: str
    type: str
    archived: bool = False


class SendflowGroup(BaseModel):
    id: str
    name: str
    participants_amount: int = Field(alias="participantsAmount", default=0)

    model_config = {"populate_by_name": True}


class SendflowAnalyticsMetric(BaseModel):
    dates: dict[str, int] = {}
    total: int = 0


class SendflowAnalytics(BaseModel):
    add: SendflowAnalyticsMetric
    remove: SendflowAnalyticsMetric
    clicks: SendflowAnalyticsMetric


class SendflowAction(BaseModel):
    id: str
    type: str
    release_id: str = Field(alias="releaseId")
    scheduled: bool = False
    scheduled_to: Optional[datetime] = Field(None, alias="scheduledTo")
    processed: bool = False
    success: Optional[bool] = None
    finished_at: Optional[datetime] = Field(None, alias="finishedAt")
    created_at: datetime = Field(alias="createdAt")

    model_config = {"populate_by_name": True}
