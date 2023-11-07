from pydantic import BaseModel


class ContactDetails(BaseModel):
    name: str
    wa_id: str
