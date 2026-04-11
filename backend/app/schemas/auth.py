from pydantic import BaseModel


class AppSecretVerifyRequest(BaseModel):
    secret: str


class AppSecretVerifyResponse(BaseModel):
    authenticated: bool
