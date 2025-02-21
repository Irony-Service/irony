import hashlib
import hmac
import subprocess
from pathlib import Path

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse

from irony.config import config
from irony.config.logger import logger

# TODO: Move this to secure configuration
GITHUB_WEBHOOK_SECRET = config.GITHUB_WEBHOOK_SECRET

MAKEFILE_DIR = Path(__file__).resolve().parents[2]


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
            result = subprocess.run(
                ["sh", "-c", "cd {} && make update".format(MAKEFILE_DIR)],
                check=True,
                capture_output=True,
                text=True,
                cwd=str(MAKEFILE_DIR),  # Run command in the correct directory
            )
            logger.info(f"Update triggered: {result.stdout}")
            return JSONResponse(
                content={"message": "Update triggered successfully"}, status_code=200
            )
        except subprocess.CalledProcessError as e:
            logger.error(f"Update failed: {e.stderr}")
            return JSONResponse(
                content={"message": "Update failed", "error": e.stderr}, status_code=500
            )

    return JSONResponse(
        content={"message": "Ignored non-dev branch push"}, status_code=200
    )
