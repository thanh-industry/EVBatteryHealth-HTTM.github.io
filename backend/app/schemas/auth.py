from typing import Literal

from pydantic import BaseModel, ConfigDict

Role = Literal["data_scientist", "technician", "ev_user"]


class LoginRequest(BaseModel):
    email: str
    password: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    name: str
    role: Role


class TokenResponse(BaseModel):
    token: str
    user: UserOut
