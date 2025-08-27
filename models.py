from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, Date, Float, Integer, String, Text
from sqlalchemy.orm import declarative_base, sessionmaker
from werkzeug.security import generate_password_hash, check_password_hash

Base = declarative_base()


class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    username = Column(String(80), unique=True, nullable=False)
    password_hash = Column(String(128), nullable=False)

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)


class Asset(Base):
    __tablename__ = 'asset'

    id = Column(Integer, primary_key=True)
    asset_code = Column(String(50), nullable=False)
    sub_code: Optional[str] = Column(String(50))
    budget_year: Optional[str] = Column(String(10))
    name = Column(String(200), nullable=False)
    details: Optional[str] = Column(Text)
    serial_number: Optional[str] = Column(String(100))
    category: Optional[str] = Column(String(100))
    quantity = Column(Integer, default=1)
    acquisition_date: Optional[datetime] = Column(Date)
    unit: Optional[str] = Column(String(100))
    price: Optional[float] = Column(Float)
    note: Optional[str] = Column(Text)


def init_db(engine) -> None:
    """Create tables and default admin user."""
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    with SessionLocal() as session:
        if not session.query(User).filter_by(username='admin').first():
            admin = User(username='admin')
            admin.set_password('admin')
            session.add(admin)
            session.commit()
