from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class BatteryMeasurement(Base):
    __tablename__ = "battery_measurements"

    id: Mapped[int] = mapped_column(primary_key=True)
    battery_id: Mapped[int] = mapped_column(ForeignKey("batteries.id"), index=True, nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    soh: Mapped[float] = mapped_column(Float, nullable=False)
    state_of_charge: Mapped[float | None] = mapped_column(Float, nullable=True)
    internal_resistance: Mapped[float | None] = mapped_column(Float, nullable=True)
    cell_voltage_avg: Mapped[float | None] = mapped_column(Float, nullable=True)
    cell_temperature_avg: Mapped[float | None] = mapped_column(Float, nullable=True)
    cell_temperature_max: Mapped[float | None] = mapped_column(Float, nullable=True)
    charge_efficiency: Mapped[float | None] = mapped_column(Float, nullable=True)
    cycle_count: Mapped[float | None] = mapped_column(Float, nullable=True)

    battery = relationship("Battery", back_populates="measurements")
