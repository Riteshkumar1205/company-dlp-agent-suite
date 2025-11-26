import requests, json
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import logging
from typing import Optional

logger = logging.getLogger("transport.sender")

class SecureSender:
    def __init__(self, base_url: str, client_cert: Optional[tuple]=None, jwt_token: Optional[str]=None, ca_bundle: Optional[str]=None):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        retries = Retry(total=5, backoff_factor=1, status_forcelist=[502,503,504])
        self.session.mount("https://", HTTPAdapter(max_retries=retries))
        self.client_cert = client_cert
        self.jwt_token = jwt_token
        self.ca_bundle = ca_bundle

    def _headers(self):
        h = {"Content-Type": "application/json"}
        if self.jwt_token:
            h["Authorization"] = f"Bearer {self.jwt_token}"
        return h

    def send_event(self, event_json: dict):
        url = f"{self.base_url}/api/v1/events"
        logger.debug("POST %s", url)
        resp = self.session.post(url, data=json.dumps(event_json), headers=self._headers(), cert=self.client_cert, verify=self.ca_bundle or True, timeout=10)
        resp.raise_for_status()
        return resp.json()

    def upload_thumbnail(self, event_id: str, thumbnail_path: str):
        url = f"{self.base_url}/api/v1/events/{event_id}/thumbnail"
        with open(thumbnail_path, "rb") as f:
            files = {"thumbnail": ("thumbnail.png", f, "image/png")}
            resp = self.session.post(url, files=files, headers={}, cert=self.client_cert, verify=self.ca_bundle or True, timeout=15)
            resp.raise_for_status()
            return resp.json()
