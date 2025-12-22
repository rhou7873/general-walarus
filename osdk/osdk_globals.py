from bw_secrets import FOUNDRY_CLIENT_ID, FOUNDRY_CLIENT_SECRET, FOUNDRY_URL
from general_walarus_python_osdk_sdk import ConfidentialClientAuth, FoundryClient

auth = ConfidentialClientAuth(
    client_id=FOUNDRY_CLIENT_ID,
    client_secret=FOUNDRY_CLIENT_SECRET,
    hostname=FOUNDRY_URL,
    should_refresh=True,
    scopes=[
		"api:use-ontologies-read",
		"api:use-ontologies-write"
    ],
)

osdk = FoundryClient(auth=auth, hostname=FOUNDRY_URL)
