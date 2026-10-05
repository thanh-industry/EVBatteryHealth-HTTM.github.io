from sqlalchemy import Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Battery(Base):
    __tablename__ = "batteries"

    id: Mapped[int] = mapped_column(primary_key=True)
    serial: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    manufacturer: Mapped[str | None] = mapped_column(String(128), nullable=True)
    chemistry: Mapped[str | None] = mapped_column(String(32), nullable=True)
    capacity_kwh: Mapped[float | None] = mapped_column(Float, nullable=True)
    cycle_count: Mapped[float | None] = mapped_column(Float, nullable=True)
    current_soh: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Internal only: a one-time, CSV-derived demo snapshot of this battery's
    # feature row (JSON; leakage blocklist and the derived label already
    # stripped), used to build the model input vector at diagnosis time. This
    # is NOT live sensor telemetry - it is a static copy taken at seed time.
    # Never serialized to the API - the Battery/Measurement schemas in
    # ARCHITECTURE.md 4.6 do not include it.
    feature_snapshot_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    measurements = relationship(
        "BatteryMeasurement", back_populates="battery", cascade="all, delete-orphan"
    )
    vehicle = relationship("Vehicle", back_populates="battery", uselist=False)
