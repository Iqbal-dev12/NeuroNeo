"""
database/models.py
SQLAlchemy ORM models for the infant pain detection system.

Tables
------
- Infant           → infants
- PainPrediction   → pain_predictions
- Alert            → alerts
"""

from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.db import Base

# ─── Auth / User ─────────────────────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


# ─── Infant ───────────────────────────────────────────────────────────────────


class Infant(Base):
    __tablename__ = "infants"

    infant_id: Mapped[str] = mapped_column(String(50), primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    age_days: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # relationships
    predictions: Mapped[list["PainPrediction"]] = relationship(
        "PainPrediction", back_populates="infant", cascade="all, delete-orphan"
    )
    alerts: Mapped[list["Alert"]] = relationship(
        "Alert", back_populates="infant", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Infant id={self.infant_id} name={self.name}>"


# ─── Pain Prediction ─────────────────────────────────────────────────────────


class PainPrediction(Base):
    __tablename__ = "pain_predictions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    infant_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("infants.infant_id", ondelete="CASCADE"), index=True
    )
    pain_level: Mapped[str] = mapped_column(
        Enum("No Pain", "Mild Pain", "Moderate Pain", "Severe Pain", name="pain_level_enum"),
        nullable=False,
    )
    pain_score: Mapped[float] = mapped_column(Float, nullable=False)       # probability of predicted class
    confidence: Mapped[float] = mapped_column(Float, nullable=False)       # max softmax score
    image_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    infant: Mapped["Infant"] = relationship("Infant", back_populates="predictions")

    def __repr__(self) -> str:
        return f"<PainPrediction id={self.id} infant={self.infant_id} level={self.pain_level}>"


# ─── Alert ────────────────────────────────────────────────────────────────────


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    infant_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("infants.infant_id", ondelete="CASCADE"), index=True
    )
    pain_level: Mapped[str] = mapped_column(String(50), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    alert_status: Mapped[str] = mapped_column(
        Enum("active", "acknowledged", "resolved", name="alert_status_enum"),
        default="active",
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    infant: Mapped["Infant"] = relationship("Infant", back_populates="alerts")

    def __repr__(self) -> str:
        return f"<Alert id={self.id} infant={self.infant_id} status={self.alert_status}>"
