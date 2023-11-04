from fastapi import FastAPI

from irony.routers import items, users, whatsapp

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello World"}

app.include_router(whatsapp.router)
app.include_router(users.router)
app.include_router(items.router)