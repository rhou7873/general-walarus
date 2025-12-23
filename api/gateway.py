from fastapi import FastAPI
import uvicorn

app = FastAPI()


@app.get("/status")
async def status():
    return {"status": "alive"}


def run_api():
    """Run FastAPI server in a separate thread"""
    uvicorn.run(app, host="0.0.0.0", port=8000)
