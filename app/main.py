from fastapi import FastAPI, Depends, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware

from slowapi import Limiter
from slowapi.util import get_remote_address

from sqlalchemy.orm import Session
from typing import List, Optional

from app import models, schemas, crud
from app.auth import get_current_user
from app.database import SessionLocal, engine, Base
from app.models import User
from app.routers import auth

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Contacts API", version="1.0")
app.include_router(auth.router, prefix="/auth", tags=["auth"])

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/contacts/", response_model=schemas.ContactOut, status_code=201)
def create_contact(contact: schemas.ContactCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if db.query(models.Contact).filter(
        models.Contact.email == contact.email,
        models.Contact.user_id == current_user.id
    ).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    return crud.create_contact(db, contact, current_user.id)

@app.get("/contacts/", response_model=List[schemas.ContactOut])
def list_contacts(skip: int = 0, limit: int = 100,
                  first_name: Optional[str] = Query(None),
                  last_name: Optional[str] = Query(None),
                  email: Optional[str] = Query(None),
                  db: Session = Depends(get_db),
                  current_user: User = Depends(get_current_user)):
    contacts = db.query(models.Contact).filter(
        models.Contact.user_id == current_user.id
    ).all()
    return contacts

@app.get("/contacts/{contact_id}", response_model=schemas.ContactOut)
def get_contact(contact_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    contact = db.query(models.Contact).filter(
        models.Contact.id == contact_id,
        models.Contact.user_id == current_user.id
    ).first()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    return contact

@app.put("/contacts/{contact_id}", response_model=schemas.ContactOut)
def update_contact(contact_id: int, contact_in: schemas.ContactUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    contact = db.query(models.Contact).filter(
        models.Contact.id == contact_id,
        models.Contact.user_id == current_user.id
    ).first()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")

    for key, value in contact_in.dict(exclude_unset=True).items():
        setattr(contact, key, value)

    db.commit()
    db.refresh(contact)
    return contact

@app.delete("/contacts/{contact_id}", status_code=204)
def delete_contact(contact_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    contact = db.query(models.Contact).filter(
        models.Contact.id == contact_id,
        models.Contact.user_id == current_user.id
    ).first()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")

    db.delete(contact)
    db.commit()
    return

@app.get("/contacts/upcoming_birthdays", response_model=List[schemas.ContactBirthday])
def get_upcoming_birthdays(days: int = Query(7, ge=1, le=365), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    items = crud.upcoming_birthdays(db, days)
    return [{"contact": it["contact"], "days_until": it["days_until"], "next_birthday": it["next_birthday"]} for it in items]


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    response = await call_next(request)
    return response

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/me")
@limiter.limit("5/minute")
def read_users_me(request: Request, current_user: models.User = Depends(get_current_user)):
    return current_user