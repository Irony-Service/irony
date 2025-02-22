import uvicorn
from fastapi import FastAPI, Request
from github_webhook import handle_github_webhook

app = FastAPI(title="Irony Git Webhook Service")


@app.post("/api/webhook/github")
async def github_webhook(request: Request):
    return await handle_github_webhook(request)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8100)
