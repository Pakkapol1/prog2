from __future__ import annotations

import argparse
import getpass
from datetime import datetime
from typing import Optional

from sqlalchemy import Column, Date, Float, Integer, String, Text, create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker
from werkzeug.security import check_password_hash, generate_password_hash

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
        if not session.query(User).filter_by(username="admin").first():
            admin = User(username="admin")
            admin.set_password("admin")
            session.add(admin)
            session.commit()
            print("Initialized database with admin/admin")


def login(session: Session) -> bool:
    username = input("Username: ")
    password = getpass.getpass("Password: ")
    user = session.query(User).filter_by(username=username).first()
    if user and user.check_password(password):
        print("Login successful")
        return True
    print("Invalid credentials")
    return False


def list_assets(session: Session) -> None:
    assets = session.query(Asset).all()
    if not assets:
        print("No assets found")
        return
    for a in assets:
        print(f"{a.id}: {a.name} (code {a.asset_code}) qty={a.quantity}")


def add_asset(session: Session) -> None:
    asset_code = input("Asset code: ")
    name = input("Name: ")
    quantity = int(input("Quantity: ") or 1)
    asset = Asset(asset_code=asset_code, name=name, quantity=quantity)
    session.add(asset)
    session.commit()
    print("Asset added")


def main() -> None:
    parser = argparse.ArgumentParser(description="Simple inventory CLI program")
    parser.add_argument("--initdb", action="store_true", help="Initialize the database and exit")
    args = parser.parse_args()

    engine = create_engine("sqlite:///inventory.db")
    if args.initdb:
        init_db(engine)
        return

    init_db(engine)
    SessionLocal = sessionmaker(bind=engine)
    with SessionLocal() as session:
        if not login(session):
            return
        while True:
            print("\n1. List assets\n2. Add asset\n3. Quit")
            choice = input("Select: ")
            if choice == "1":
                list_assets(session)
            elif choice == "2":
                add_asset(session)
            elif choice == "3":
                break


if __name__ == "__main__":
    main()
