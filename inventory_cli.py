from __future__ import annotations

import argparse
import getpass
from datetime import datetime

import pandas as pd
from docx import Document
from fpdf import FPDF
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
        print(
            f"{a.id}: code {a.asset_code}, sub {a.sub_code}, year {a.budget_year},"
            f" name {a.name}, details {a.details}, SN {a.serial_number},"
            f" category {a.category}, qty {a.quantity}, acquired {a.acquisition_date},"
            f" unit {a.unit}, price {a.price}, note {a.note}"
        )


def add_asset(session: Session) -> None:
    asset_code = input("Asset code: ")
    sub_code = input("Sub code: ")
    budget_year = input("Budget year: ")
    name = input("Name: ")
    details = input("Details: ")
    serial_number = input("Serial number: ")
    category = input("Category: ")
    quantity = int(input("Quantity: ") or 1)
    acq_str = input("Acquisition date (YYYY-MM-DD): ")
    acquisition_date = (
        datetime.strptime(acq_str, "%Y-%m-%d").date() if acq_str else None
    )
    unit = input("Unit: ")
    price_str = input("Price: ")
    price = float(price_str) if price_str else None
    note = input("Note: ")
    asset = Asset(
        asset_code=asset_code,
        sub_code=sub_code or None,
        budget_year=budget_year or None,
        name=name,
        details=details or None,
        serial_number=serial_number or None,
        category=category or None,
        quantity=quantity,
        acquisition_date=acquisition_date,
        unit=unit or None,
        price=price,
        note=note or None,
    )
    session.add(asset)
    session.commit()
    print("Asset added")


def delete_asset(session: Session) -> None:
    asset_id = input("Asset ID to delete: ")
    asset = session.get(Asset, int(asset_id)) if asset_id else None
    if not asset:
        print("Asset not found")
        return
    session.delete(asset)
    session.commit()
    print("Asset deleted")


def export_assets(session: Session) -> None:
    fmt = input("Format (excel/word/pdf): ").lower()
    assets = session.query(Asset).all()
    data = [
        {
            "ลำดับ": a.id,
            "รหัสครุภัณฑ์": a.asset_code,
            "รหัสย่อย": a.sub_code,
            "ปีงบประมาณที่ได้มา": a.budget_year,
            "ชื่อครุภัณฑ์": a.name,
            "รายละเอียด": a.details,
            "หมายเลขเครื่อง/SN": a.serial_number,
            "ประเภท": a.category,
            "จำนวน": a.quantity,
            "วันที่ได้มา": a.acquisition_date.strftime("%Y-%m-%d") if a.acquisition_date else "",
            "หน่วยเบิก": a.unit,
            "ราคา": a.price,
            "หมายเหตุ": a.note,
        }
        for a in assets
    ]
    if fmt == "excel":
        df = pd.DataFrame(data)
        df.to_excel("assets.xlsx", index=False)
        print("Exported to assets.xlsx")
    elif fmt == "word":
        doc = Document()
        table = doc.add_table(rows=1, cols=len(data[0]) if data else 1)
        hdr_cells = table.rows[0].cells
        for i, key in enumerate(data[0].keys() if data else ["รายการ"]):
            hdr_cells[i].text = key
        for item in data:
            row_cells = table.add_row().cells
            for i, key in enumerate(item.keys()):
                row_cells[i].text = str(item[key])
        doc.save("assets.docx")
        print("Exported to assets.docx")
    elif fmt == "pdf":
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=10)
        for item in data:
            line = " | ".join([f"{k}: {v}" for k, v in item.items()])
            pdf.multi_cell(0, 5, line)
            pdf.ln(1)
        pdf.output("assets.pdf")
        print("Exported to assets.pdf")
    else:
        print("Unknown format")


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
            print(
                "\n1. List assets\n2. Add asset\n3. Delete asset\n4. Export assets\n5. Quit"
            )
            choice = input("Select: ")
            if choice == "1":
                list_assets(session)
            elif choice == "2":
                add_asset(session)
            elif choice == "3":
                delete_asset(session)
            elif choice == "4":
                export_assets(session)
            elif choice == "5":
                break


if __name__ == "__main__":
    main()
