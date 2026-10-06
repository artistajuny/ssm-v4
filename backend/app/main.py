from fastapi import FastAPI

from backend.app.core.config import settings

app = FastAPI(
    title=settings.app_name,
    description="SSM V4 API",
    version=settings.app_version,
    debug=settings.debug,
)


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "ssm-v4-api",
        "version": settings.app_version,
        "environment": settings.app_env.value,
    }
