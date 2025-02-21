import hashlib
import hmac
import subprocess

from fastapi import HTTPException, Request

from irony.config import config
from irony.config.logger import logger

# TODO: Move this to secure configuration
GITHUB_WEBHOOK_SECRET = config.GITHUB_WEBHOOK_SECRET


async def handle_github_webhook(request: Request):
    signature = request.headers.get("X-Hub-Signature-256")
    if not signature:
        raise HTTPException(status_code=400, detail="No signature header")

    body = await request.body()
    secret = GITHUB_WEBHOOK_SECRET.encode()
    expected_signature = "sha256=" + hmac.new(secret, body, hashlib.sha256).hexdigest()

    if not hmac.compare_digest(signature, expected_signature):
        raise HTTPException(status_code=401, detail="Invalid signature")

    payload = await request.json()
    if payload.get("ref") == "refs/heads/dev":
        try:
            subprocess.run(["make", "update"], check=True)
            return {"message": "Update triggered successfully"}
        except subprocess.CalledProcessError as e:
            logger.error(f"Update failed: {str(e)}")
            raise HTTPException(status_code=500, detail="Update failed")

    return {"message": "Ignored non-dev branch push"}
