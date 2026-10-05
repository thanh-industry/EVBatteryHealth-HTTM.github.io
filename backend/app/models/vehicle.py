from sqlalchemy import Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Vehicle(Base):
    __tablename__ = "vehicles"

    id: Mapped[int] = mapped_column(primary_key=True)
    vehicle_code: Mapped[str] = mapped_column(String(32), unique=True, index=True, nullable=False)
    brand: Mapped[str | None] = mapped_column(String(64), nullable=True)
    model: Mapped[str | None] = mapped_column(String(64), nullable=True)
    vehicle_type: Mapped[str | None] = mapped_column(String(32), nullable=True)
    manufacturing_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    drive_type: Mapped[str | None] = mapped_column(String(16), nullable=True)
    odometer_km: Mapped[float | None] = mapped_column(Float, nullable=True)
    fleet_or_private: Mapped[str | None] = mapped_column(String(16), nullable=True)

    battery_id: Mapped[int] = mapped_column(ForeignKey("batteries.id"), unique=True, nullable=False)
    owner_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)

    battery = relationship("Battery", back_populates="vehicle")
