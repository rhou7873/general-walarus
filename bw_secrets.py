"""Secrets management"""
from bitwarden_sdk import BitwardenClient, DeviceType, client_settings_from_dict
import os

API_URL = os.getenv("BW_API_URL")
IDENTITY_URL = os.getenv("BW_ID_URL")
ACCESS_TOKEN = os.getenv("BW_ACCESS_TOKEN")
ENVIRONMENT = os.getenv("ENVIRONMENT")

if (API_URL is None or
    IDENTITY_URL is None or
        ACCESS_TOKEN is None):
    raise Exception(
        "Environment variables aren't set: "
        f"API_URL={API_URL}, "
        f"IDENTITY_URL={IDENTITY_URL}, "
        f"ACCESS_TOKEN={ACCESS_TOKEN}")

client = BitwardenClient(
    client_settings_from_dict(
        {
            "apiUrl": API_URL,
            "deviceType": DeviceType.SDK,
            "identityUrl": IDENTITY_URL,
            "userAgent": "Python",
        }
    )
)

client.access_token_login(ACCESS_TOKEN)

################# ENVIRONMENT VARIABLES #################

# Discord
BOT_TOKEN = (
    client.secrets().get(  # BOT_TOKEN_PROD
    "d7c5b115-4cfb-4479-9d4c-b38000008a66").data.value
    if ENVIRONMENT == "production"
    else client.secrets().get(  # BOT_TOKEN_DEV
    "8e56d9a2-3e34-4131-8257-b2e300451fca").data.value
)
CMD_PREFIX = (
    client.secrets().get(  # CMD_PREFIX_PROD
    "be8ee3a4-36b9-4018-8238-b3800004dc1b").data.value
    if ENVIRONMENT == "production"
    else client.secrets().get(  # CMD_PREFIX_DEV
    "1586f5d6-2a3d-470b-bdbd-b3800004d238").data.value
)

# GCP
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = client.secrets().get(
    "0e25b878-c47d-4a26-8f1c-b3800001507c").data.value

# MongoDB
ARCHIVE_DATE_ID = client.secrets().get(
    "8dec00f8-5db4-4f40-90e6-b3800000c4f9").data.value
MONGO_CONN_STRING = client.secrets().get(
    "0106e8c3-5a99-409e-bb52-b3800000b4b9").data.value

# OPENAI
os.environ["OPENAI_API_KEY"] = client.secrets().get(
    "d1234f7d-bf37-4c00-8744-b3800000e0f6").data.value
OPENAI_ASST_ID = client.secrets().get(
    "43d19e39-2fff-43d9-a7d3-b380000109e1").data.value
OPENAI_MODEL = client.secrets().get(
    "48833c1b-308f-4064-bca7-b38000011ea5").data.value
