from fastapi import FastAPI
from app.api import auth, brut_force

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

app = FastAPI()

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    # Преобразуем стандартные ошибки в более читаемый формат
    custom_errors = []
    for error in exc.errors():
        field = " -> ".join(map(str, error.get("loc", [])))
        message = error.get("msg")
        custom_errors.append({"field": field, "error": message})
    return JSONResponse(
        status_code=422,
        content={"detail": custom_errors},
    )


# Если вы задаёте префиксы, учтите их при запросах
app.include_router(auth.router, tags=["auth"], prefix="/auth")
app.include_router(brut_force.router, tags=["brut"], prefix="/brut")
