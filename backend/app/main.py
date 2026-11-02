from fastapi import FastAPI
from fastapi.responses import JSONResponse

from app.core.error_handlers import register_error_handlers
from app.routers import expenses, groups
from app.schemas import HealthOut
from app.utils.responses import ok

app = FastAPI(
    title="SplitBill API",
    version="0.1.0",
)


@app.get("/health", response_model=HealthOut)
def health_check() -> JSONResponse:
    return ok({"status": "ok"})


register_error_handlers(app)
app.include_router(groups.router)
app.include_router(expenses.router)
