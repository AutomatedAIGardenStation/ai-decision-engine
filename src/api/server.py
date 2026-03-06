from fastapi import FastAPI
from src.routers import health, decide

app = FastAPI(
    title="GardenStation AI Decision Engine",
    version="0.1.0",
    description="Stateless FastAPI decision engine for GardenStation",
)

app.include_router(health.router)
app.include_router(decide.router)

if __name__ == "__main__":
    import uvicorn
    # Runtime decision path is purely stateless. Serial side effects are isolated
    # to the optional CLI adapter (src/cli.py).
    uvicorn.run("src.api.server:app", host="0.0.0.0", port=8000, reload=True)
