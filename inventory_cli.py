from __future__ import annotations

import argparse
import getpass

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from models import Asset, Base, User, init_db


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
