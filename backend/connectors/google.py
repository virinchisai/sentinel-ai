"""Google APIs using an OAuth refresh token, with fixed upstream endpoints."""

import json
import httpx


class GoogleAPI:
    def __init__(self, raw):
        self.credentials = json.loads(raw)

    def request(self, service, method, path, **kwargs):
        c = self.credentials
        with httpx.Client(timeout=30) as client:
            token = client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "client_id": c["client_id"],
                    "client_secret": c["client_secret"],
                    "refresh_token": c["refresh_token"],
                    "grant_type": "refresh_token",
                },
            )
            token.raise_for_status()
            base = {
                "gmail": "https://gmail.googleapis.com/gmail/v1/users/me/",
                "calendar": "https://www.googleapis.com/calendar/v3/",
            }[service]
            response = client.request(
                method,
                base + path,
                headers={"Authorization": "Bearer " + token.json()["access_token"]},
                **kwargs,
            )
            response.raise_for_status()
            return response.json()
