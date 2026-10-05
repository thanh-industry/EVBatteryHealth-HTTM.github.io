"""Import every model so Base.metadata is fully populated for create_all()."""
from app.models.battery import Battery
from app.models.dataset import Dataset
from app.models.diagnostic import Diagnostic
from app.models.maintenance_item import MaintenanceItem
from app.models.measurement import BatteryMeasurement
from app.models.model_deployment import ModelDeployment
from app.models.notification import Notification
from app.models.training_run import TrainingRun
from app.models.user import User
from app.models.vehicle import Vehicle

__all__ = [
    "Battery",
    "Dataset",
    "Diagnostic",
    "MaintenanceItem",
    "BatteryMeasurement",
    "ModelDeployment",
    "Notification",
    "TrainingRun",
    "User",
    "Vehicle",
]
