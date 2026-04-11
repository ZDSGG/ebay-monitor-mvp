from fastapi import Header, HTTPException, status

from app.core.config import get_settings


settings = get_settings()


def require_app_access(x_app_secret: str | None = Header(default=None)) -> None:
    if not settings.app_access_secret:
        return

    if x_app_secret != settings.app_access_secret:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid app secret.",
        )
