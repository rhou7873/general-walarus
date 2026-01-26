from bw_secrets import API_TOKEN
from cogs import ElectionCog, ElectionCogException
import discord
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel
import uvicorn

app = FastAPI()
security = HTTPBearer()

# region Data Models


class ElectionStartRequest(BaseModel):
    server_id: str
    channel_id: str | None = None


# endregion

# region Helper Functions


def verify_bearer_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication scheme",
        )

    if credentials.credentials != API_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    return credentials.credentials


def get_bot(request: Request):
    return request.app.state.bot


# endregion

# region Endpoints


@app.get("/status")
async def status():
    return {"status": "alive"}


@app.post("/election/start")
async def start_election(
    request_body: ElectionStartRequest,
    token: str = Depends(verify_bearer_token),
    bot: discord.Bot = Depends(get_bot)
):
    server_id: str = request_body.server_id
    channel_id: str | None = request_body.channel_id
    election_cog = bot.get_cog("Election")

    if election_cog is None:
        raise HTTPException(
            status_code=500,
            detail="Couldn't load Election Cog"
        )

    assert isinstance(election_cog, ElectionCog)

    try:
        guild, channel = await election_cog.initiate_election(
            server=server_id,
            channel=channel_id
        )
    except ElectionCogException as e:
        raise HTTPException(
            status_code=500,
            detail=e.message
        )

    return {
        "status": "ok",
        "message": "Election successfully started",
        "server_name": guild.name,
        "server_id": guild.id,
        "channel_name": channel.name,
        "channel_id": channel.id
    }


# endregion

async def run_api(bot: discord.Bot):
    """Run FastAPI server in a separate thread"""
    app.state.bot = bot
    config = uvicorn.Config(app, host="0.0.0.0", port=8000, loop="asyncio")
    server = uvicorn.Server(config)
    await server.serve()
