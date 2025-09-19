from pydantic import BaseModel, EmailStr, Field, constr, StringConstraints
from typing import Optional
from datetime import date
from typing_extensions import Annotated

phone_type = Annotated[str, StringConstraints(pattern=r'^\+?\d{7,15}$')]

class ContactBase(BaseModel):
    first_name: str = Field(..., min_length=1)
    last_name: str = Field(..., min_length=1)
    email: EmailStr
    phone: phone_type
    birthday: date
    additional_data: Optional[str] = None

class ContactCreate(ContactBase):
    pass

class ContactUpdate(BaseModel):
    first_name: Optional[str]
    last_name: Optional[str]
    email: Optional[EmailStr]
    phone: Optional[phone_type]
    birthday: Optional[date]
    additional_data: Optional[str]

class ContactOut(ContactBase):
    id: int
    class Config:
        orm_mode = True

class ContactBirthday(BaseModel):
    contact: ContactOut
    days_until: int
    next_birthday: date
    class Config:
        orm_mode = True
