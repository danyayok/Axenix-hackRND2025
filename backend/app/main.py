from fastapi import FastAPI
from fastapi.responses import ORJSONResponse, RedirectResponse, PlainTextResponse
from app.core.config import settings

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    default_response_class=ORJSONResponse,
    docs_url="/docs",      # Swagger UI
    redoc_url="/redoc",    # ReDoc
)

@app.get("/", include_in_schema=False)
def root():
    # удобный редирект на swagger
    return RedirectResponse(url="/docs")

@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    # чтобы не сыпались 404 на иконку
    return PlainTextResponse("", status_code=204)

@app.get("/health")
def health():
    return {"status": "ok", "env": settings.app_env}
