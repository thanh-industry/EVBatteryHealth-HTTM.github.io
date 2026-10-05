from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Diagnostic(Base):
    __tablename__ = "diagnostics"

    id: Mapped[int] = mapped_column(primary_key=True)
    vehicle_id: Mapped[int] = mapped_column(ForeignKey("vehicles.id"), nullable=False)
    battery_id: Mapped[int] = mapped_column(ForeignKey("batteries.id"), nullable=False)
    run_id: Mapped[int] = mapped_column(ForeignKey("training_runs.id"), nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    soh: Mapped[float] = mapped_column(Float, nullable=False)
    predicted_class: Mapped[str] = mapped_column(String(16), nullable=False)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    class_probabilities_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    model_version: Mapped[str] = mapped_column(String(16), nullable=False)
    model_algorithm: Mapped[str] = mapped_column(String(32), nullable=False)

    technician_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    recommendation: Mapped[str] = mapped_column(Text, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
