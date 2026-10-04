"""App factory: no DB, credentials or heavy providers are initialized during OpenAPI export."""
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException
from fastapi.responses import FileResponse, JSONResponse
from app.config import Settings
from app.db import make_engine, init_db
from app.providers.factory import build_providers
from app.providers.errors import ProviderError
from app.services.errors import ApiError
from app.schemas.api import ErrorEnvelope
from app.routers import health, profiles, sessions, turns, quizzes, analysis

DEFAULT_DIST = Path(__file__).resolve().parents[2] / "frontend" / "dist"

def create_app(settings: Settings | None = None, *, frontend_dist: Path | None = None) -> FastAPI:
    settings = settings or Settings()
    @asynccontextmanager
    async def lifespan(application):
        engine = make_engine(str(settings.db_path))
        application.state.engine = engine
        providers = None
        try:
            init_db(engine)
            providers = build_providers(settings)
            application.state.providers = providers
            yield
        finally:
            if providers is not None:
                await providers.aclose()
            engine.dispose()
    application = FastAPI(title="Voice Language Tutor",version="0.2.0",lifespan=lifespan,
        responses={422:{"model":ErrorEnvelope},404:{"model":ErrorEnvelope},409:{"model":ErrorEnvelope},502:{"model":ErrorEnvelope}})
    application.state.settings = settings

    @application.exception_handler(ApiError)
    async def api_error(request,exc):
        return JSONResponse(exc.envelope(),status_code=exc.status)

    @application.exception_handler(ProviderError)
    async def provider_error(request,exc):
        err = ApiError(502,exc.code,str(exc),stage="analysis" if exc.stage=="llm" else exc.stage,retryable=exc.retryable)
        return JSONResponse(err.envelope(),status_code=502)

    @application.exception_handler(RequestValidationError)
    async def validation_error(request,exc):
        err = ApiError(422,"invalid_request","Check the supplied fields and try again.",stage="request")
        return JSONResponse(err.envelope(),status_code=422)

    @application.exception_handler(HTTPException)
    async def http_error(request,exc):
        err = ApiError(exc.status_code,"not_found" if exc.status_code==404 else "request_failed",str(exc.detail),stage="request")
        return JSONResponse(err.envelope(),status_code=exc.status_code)

    @application.exception_handler(Exception)
    async def unexpected_error(request,exc):
        err = ApiError(500,"internal_error","The request could not be completed.",stage="request")
        return JSONResponse(err.envelope(),status_code=500)

    for module in (health,profiles,sessions,turns,quizzes,analysis):
        application.include_router(module.router)
    root = (frontend_dist or DEFAULT_DIST).resolve()

    @application.api_route("/{path:path}",methods=["GET","HEAD"],include_in_schema=False)
    async def frontend(path: str):
        if path=="api" or path.startswith("api/"):
            raise ApiError(404,"not_found","API route not found.",stage="request")
        candidate = (root/path).resolve()
        if not candidate.is_relative_to(root) or any(part.startswith(".") for part in Path(path).parts):
            raise ApiError(404,"not_found","File not found.")
        if candidate.is_file():
            # Windows MIME registry entries can label modules as text/plain.
            media_type = {".js": "text/javascript", ".mjs": "text/javascript", ".wasm": "application/wasm"}.get(candidate.suffix.lower())
            return FileResponse(candidate, media_type=media_type)
        if path.startswith(("assets/","vad/")) or Path(path).suffix:
            raise ApiError(404,"not_found","Asset not found.")
        index = root/"index.html"
        if not index.is_file():
            raise ApiError(503,"frontend_not_built","Run npm ci and npm run build in frontend.")
        return FileResponse(index,headers={"Cache-Control":"no-cache"})
    return application

app = create_app()

if __name__=="__main__":
    import uvicorn
    uvicorn.run(app,host=app.state.settings.host,port=app.state.settings.port)
