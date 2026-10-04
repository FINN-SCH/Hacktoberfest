"""Step A app: health + production SPA. No DB/provider initialization on import."""
from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from app.config import Settings
from app.routers.health import router as health_router

DEFAULT_DIST = Path(__file__).resolve().parents[2] / "frontend" / "dist"

def create_app(settings: Settings | None = None, *, frontend_dist: Path | None = None) -> FastAPI:
    application = FastAPI(title="Voice Language Tutor", version="0.1.0")
    application.state.settings = settings or Settings()
    application.include_router(health_router)
    root = (frontend_dist or DEFAULT_DIST).resolve()

    # Register Step C API routers ABOVE this fallback.
    @application.api_route("/{path:path}", methods=["GET", "HEAD"], include_in_schema=False)
    async def frontend(path: str):
        if path == "api" or path.startswith("api/"):
            return JSONResponse({"error": {"code": "not_found"}}, status_code=404)
        candidate = (root / path).resolve()
        if not candidate.is_relative_to(root) or any(part.startswith(".") for part in Path(path).parts):
            return JSONResponse({"error": {"code": "not_found"}}, status_code=404)
        if candidate.is_file():
            return FileResponse(candidate)
        # Missing asset URLs must never receive index.html with an incorrect MIME type.
        if path.startswith(("assets/", "vad/")) or Path(path).suffix:
            return JSONResponse({"error": {"code": "not_found"}}, status_code=404)
        index = root / "index.html"
        if not index.is_file():
            return JSONResponse({"error": {"code": "frontend_not_built",
                "message": "Run npm ci and npm run build in frontend."}}, status_code=503)
        return FileResponse(index, headers={"Cache-Control": "no-cache"})

    return application

app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=app.state.settings.port)
