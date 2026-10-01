from fastapi import FastAPI

app = FastAPI(
    title="SSM V4 API",
    description="Stock Safety Monitor V4 API",
    version="0.1.0",
)


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "ssm-v4-api",
        "version": "0.1.0",
    }
