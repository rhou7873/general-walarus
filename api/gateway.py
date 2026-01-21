from bw_secrets import API_TOKEN
from cogs import ElectionCog
from fastapi import FastAPI, Header, HTTPException
import uvicorn

app = FastAPI()


@app.get("/status")
async def status():
    return {"status": "alive"}


@app.post("/election/start")
async def start_election(
    server_id: str,
    authorization: str = Header(None)
):
    if authorization != f"Bearer {API_TOKEN}":
        raise HTTPException(status_code=401, detail="Unauthorized")
    elif not server_id:
        raise HTTPException(status_code=400, detail="Server ID is required")

    # TODO: Call carry_out_election from ElectionCog

    return {
        "status": "success",
        "message": f"Election initiated successfully in server (id {server_id})"
    }


def run_api():
    """Run FastAPI server in a separate thread"""
    uvicorn.run(app, host="0.0.0.0", port=8000)
