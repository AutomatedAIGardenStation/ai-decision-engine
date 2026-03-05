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
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)
