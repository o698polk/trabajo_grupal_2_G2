from sqlalchemy.orm import Session
from . import models, auth
from .config import settings
import os

def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()

def create_admin_user(db: Session):
   
    admin_username = os.getenv("ADMIN_USER")
    admin_email = os.getenv("EMAIL_USER")
    admin_password = os.getenv("PASSWORD_USER")
    
    existing_admin = get_user_by_username(db, admin_username)
    if not existing_admin:
        admin_user = models.User(
            username=admin_username,
            email=admin_email,
            hashed_password=auth.get_password_hash(admin_password),
            role="admin"
        )
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        return admin_user
    return existing_admin

def get_all_products(db: Session):
    return db.query(models.ProductResult).order_by(models.ProductResult.created_at.desc()).all()
