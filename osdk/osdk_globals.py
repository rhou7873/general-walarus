from bw_secrets import FOUNDRY_URL, OSDK_RUN_TOKEN
from general_walarus_python_osdk_sdk import UserTokenAuth, FoundryClient
import logging

log = logging.getLogger(__name__)
auth = UserTokenAuth(token=OSDK_RUN_TOKEN)
osdk = FoundryClient(auth=auth, hostname=FOUNDRY_URL)
