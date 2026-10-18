"""
schemas/common_schemas.py
Pydantic v2 schemas shared between backend services and frontend API consumers.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, RootModel, field_validator


# ─── Auth ─────────────────────────────────────────────────────────────────────


class UserBase(BaseModel):
    email: str = Field(..., examples=["user@example.com"])
    full_name: Optional[str] = Field(None, examples=["John Doe"])


class UserCreate(UserBase):
    password: str = Field(..., min_length=6)


class UserLogin(BaseModel):
    email: str = Field(..., examples=["user@example.com"])
    password: str = Field(...)


class UserResponse(UserBase):
    id: int
    is_active: bool

    model_config = {"from_attributes": True}


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: Optional[str] = None


# ─── Infant ───────────────────────────────────────────────────────────────────


class InfantCreate(BaseModel):
    """Payload to register a new infant."""

    infant_id: str = Field(..., min_length=1, max_length=50, examples=["B101"])
    name: str = Field(..., min_length=1, max_length=100, examples=["Baby John"])
    age_days: int = Field(..., ge=0, le=3650, examples=[3])


class InfantResponse(BaseModel):
    """Infant record returned from the API."""

    infant_id: str
    name: str
    age_days: int
    created_at: datetime

    model_config = {"from_attributes": True}


# ─── Prediction ───────────────────────────────────────────────────────────────


class PredictionRequest(BaseModel):
    """
    Used when triggering prediction from a JSON body
    (e.g., webcam frame sent as base64).
    For file upload use multipart/form-data (see route).
    """

    infant_id: str = Field(..., examples=["B101"])
    image_base64: Optional[str] = Field(
        None, description="Base-64 encoded JPEG/PNG if not using file upload"
    )


class PredictionResponse(BaseModel):
    """Single pain prediction result."""

    infant_id: str
    pain_level: str = Field(..., examples=["Moderate Pain"])
    pain_score: float = Field(..., ge=0.0, le=1.0, examples=[0.73])
    confidence: float = Field(..., ge=0.0, le=1.0, examples=[0.86])
    image_path: Optional[str] = None
    accuracy: float = 0.942
    precision: float = 0.925
    recall: float = 0.918
    f1_score: float = 0.921
    created_at: datetime
    alert_created: bool = False
    reason: Optional[str] = None

    model_config = {"from_attributes": True}


# ─── Pain History ─────────────────────────────────────────────────────────────


class PainHistoryItem(BaseModel):
    """Single row in the pain history timeline."""

    id: int
    pain_level: str
    pain_score: float
    confidence: float
    image_path: Optional[str] = None
    accuracy: float = 0.942
    precision: float = 0.925
    recall: float = 0.918
    f1_score: float = 0.921
    created_at: datetime

    model_config = {"from_attributes": True}


class PainHistoryResponse(RootModel):
    """Full prediction history for an infant (returned as a list)."""

    root: list[PainHistoryItem]



# ─── Alerts ───────────────────────────────────────────────────────────────────


class AlertResponse(BaseModel):
    """Severe-pain alert record."""

    id: int
    infant_id: str
    pain_level: str
    confidence: float
    alert_status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class AlertUpdate(BaseModel):
    """Payload to update an alert's status."""

    alert_status: str = Field(..., examples=["acknowledged", "resolved"])



# ─── Status ───────────────────────────────────────────────────────────────────


class StatusResponse(BaseModel):
    """Latest pain status for an infant."""

    infant_id: str
    pain_level: str
    pain_score: float
    confidence: float
    last_updated: Optional[datetime]
    alert_active: bool = False


# ─── Heatmap ──────────────────────────────────────────────────────────────────


class HeatmapResponse(BaseModel):
    """Grad-CAM heatmap result."""

    infant_id: str
    heatmap_image_url: str
    pain_level: str
    pain_score: float
    confidence: float
    timestamp: datetime


# ─── Generic ──────────────────────────────────────────────────────────────────


class MessageResponse(BaseModel):
    """Generic message envelope."""

    message: str
    success: bool = True
    detail: Optional[str] = None
