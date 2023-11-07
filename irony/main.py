from fastapi import FastAPI

from irony.routers import users, whatsapp

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}


app.include_router(whatsapp.router, prefix="/whatsapp")
app.include_router(users.router)
