from fastapi import APIRouter, HTTPException, status

from app.core.config import get_settings
from app.schemas.auth import AppSecretVerifyRequest, AppSecretVerifyResponse


router = APIRouter(prefix="/auth", tags=["auth"])
settings = get_settings()


@router.post("/verify", response_model=AppSecretVerifyResponse)
def verify_app_secret(payload: AppSecretVerifyRequest) -> AppSecretVerifyResponse:
    if not settings.app_access_secret:
        return AppSecretVerifyResponse(authenticated=True)

    if payload.secret != settings.app_access_secret:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid app secret.",
        )

    return AppSecretVerifyResponse(authenticated=True)
