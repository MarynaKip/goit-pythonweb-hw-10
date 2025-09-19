from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app import models, schemas, crud
from app.database import SessionLocal, engine, Base

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Contacts API", version="1.0")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/contacts/", response_model=schemas.ContactOut, status_code=201)
def create_contact(contact: schemas.ContactCreate, db: Session = Depends(get_db)):
    if db.query(models.Contact).filter(models.Contact.email == contact.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    return crud.create_contact(db, contact)

@app.get("/contacts/", response_model=List[schemas.ContactOut])
def list_contacts(skip: int = 0, limit: int = 100,
                  first_name: Optional[str] = Query(None),
                  last_name: Optional[str] = Query(None),
                  email: Optional[str] = Query(None),
                  db: Session = Depends(get_db)):
    if first_name or last_name or email:
        return crud.search_contacts(db, first_name, last_name, email)
    return crud.get_contacts(db, skip=skip, limit=limit)

@app.get("/contacts/{contact_id}", response_model=schemas.ContactOut)
def get_contact(contact_id: int, db: Session = Depends(get_db)):
    contact = crud.get_contact(db, contact_id)
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    return contact

@app.put("/contacts/{contact_id}", response_model=schemas.ContactOut)
def update_contact(contact_id: int, contact_in: schemas.ContactUpdate, db: Session = Depends(get_db)):
    updated = crud.update_contact(db, contact_id, contact_in)
    if not updated:
        raise HTTPException(status_code=404, detail="Contact not found")
    return updated

@app.delete("/contacts/{contact_id}", status_code=204)
def delete_contact(contact_id: int, db: Session = Depends(get_db)):
    ok = crud.delete_contact(db, contact_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Contact not found")
    return

@app.get("/contacts/upcoming_birthdays", response_model=List[schemas.ContactBirthday])
def get_upcoming_birthdays(days: int = Query(7, ge=1, le=365), db: Session = Depends(get_db)):
    items = crud.upcoming_birthdays(db, days)
    return [{"contact": it["contact"], "days_until": it["days_until"], "next_birthday": it["next_birthday"]} for it in items]
