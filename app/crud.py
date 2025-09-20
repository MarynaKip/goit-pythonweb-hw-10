from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List, Optional
from datetime import date, datetime, timedelta

from . import models, schemas

def create_contact(db: Session, contact_in: schemas.ContactCreate) -> models.Contact:
    db_contact = models.Contact(**contact_in.dict())
    db.add(db_contact)
    db.commit()
    db.refresh(db_contact)
    return db_contact

def get_contact(db: Session, contact_id: int) -> Optional[models.Contact]:
    return db.query(models.Contact).filter(models.Contact.id == contact_id).first()

def get_contacts(db: Session, skip: int =0, limit: int =100) -> List[models.Contact]:
    return db.query(models.Contact).offset(skip).limit(limit).all()

def search_contacts(db: Session, first_name: Optional[str]=None, last_name: Optional[str]=None, email: Optional[str]=None):
    query = db.query(models.Contact)
    filters = []
    if first_name:
        filters.append(models.Contact.first_name.ilike(f"%{first_name}%"))
    if last_name:
        filters.append(models.Contact.last_name.ilike(f"%{last_name}%"))
    if email:
        filters.append(models.Contact.email.ilike(f"%{email}%"))
    if filters:
        query = query.filter(*filters)
    return query.all()

def update_contact(db: Session, contact_id: int, contact_update: schemas.ContactUpdate):
    db_contact = get_contact(db, contact_id)
    if not db_contact:
        return None
    for key, value in contact_update.dict(exclude_unset=True).items():
        setattr(db_contact, key, value)
    db.add(db_contact)
    db.commit()
    db.refresh(db_contact)
    return db_contact

def delete_contact(db: Session, contact_id: int) -> bool:
    db_contact = get_contact(db, contact_id)
    if not db_contact:
        return False
    db.delete(db_contact)
    db.commit()
    return True

def upcoming_birthdays_from_list(contacts, days: int = 7):
    today = date.today()
    result = []
    for c in contacts:
        b = c.birthday
        try:
            next_b = date(today.year, b.month, b.day)
        except ValueError:
            next_b = date(today.year, 2, 28)
        if next_b < today:
            try:
                next_b = date(today.year + 1, b.month, b.day)
            except ValueError:
                next_b = date(today.year + 1, 2, 28)
        delta = (next_b - today).days
        if 0 <= delta <= days:
            result.append({"contact": c, "days_until": delta, "next_birthday": next_b})
    result.sort(key=lambda x: x['days_until'])
    return result