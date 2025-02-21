import hashlib
import hmac
import os
import subprocess
from pathlib import Path

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse

# TODO: Move this to secure configuration
# Get webhook secret from environment variable, with a helpful error if not set
GITHUB_WEBHOOK_SECRET = os.environ.get("GITHUB_WEBHOOK_SECRET")
if not GITHUB_WEBHOOK_SECRET:
    raise ValueError("GITHUB_WEBHOOK_SECRET environment variable must be set")

MAKEFILE_DIR = Path(__file__).resolve().parents[1]
print(f"MAKEFILE_DIR: {MAKEFILE_DIR}")


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
                ["make", "update"],
                check=True,
                capture_output=True,
                text=True,
                cwd=str(MAKEFILE_DIR),  # Run command in the correct directory
            )
            print(f"Update triggered: {result.stdout}")
            return JSONResponse(
                content={"message": "Update triggered successfully"}, status_code=200
            )
        except subprocess.CalledProcessError as e:
            print(f"Update failed: {e.stderr}")
            return JSONResponse(
                content={"message": "Update failed", "error": e.stderr}, status_code=500
            )

    return JSONResponse(
        content={"message": "Ignored non-dev branch push"}, status_code=200
    )
