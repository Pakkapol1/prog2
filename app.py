import os
from datetime import datetime

from flask import Flask, render_template, request, redirect, url_for, session, send_file
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import pandas as pd
from docx import Document
from fpdf import FPDF

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///inventory.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'change-this-key'

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

class Asset(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    asset_code = db.Column(db.String(50), nullable=False)
    sub_code = db.Column(db.String(50))
    budget_year = db.Column(db.String(10))
    name = db.Column(db.String(200), nullable=False)
    details = db.Column(db.Text)
    serial_number = db.Column(db.String(100))
    category = db.Column(db.String(100))
    quantity = db.Column(db.Integer, default=1)
    acquisition_date = db.Column(db.Date)
    unit = db.Column(db.String(100))
    price = db.Column(db.Float)
    note = db.Column(db.Text)


class InventoryItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    quantity = db.Column(db.Integer, default=0)
    location = db.Column(db.String(100))
    note = db.Column(db.Text)

def login_required(view_func):
    def wrapper(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return view_func(*args, **kwargs)
    wrapper.__name__ = view_func.__name__
    return wrapper

@app.route('/initdb')
def initdb():
    db.create_all()
    if not User.query.filter_by(username='admin').first():
        admin = User(username='admin')
        admin.set_password('admin')
        db.session.add(admin)
        db.session.commit()
    return 'Database initialized with admin/admin'

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            session['user_id'] = user.id
            return redirect(url_for('asset_list'))
        return render_template('login.html', error='Invalid credentials')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))

@app.route('/')
@login_required
def asset_list():
    assets = Asset.query.all()
    return render_template('asset_list.html', assets=assets)

@app.route('/assets/add', methods=['GET', 'POST'])
@login_required
def asset_add():
    if request.method == 'POST':
        asset = Asset(
            asset_code=request.form['asset_code'],
            sub_code=request.form.get('sub_code'),
            budget_year=request.form.get('budget_year'),
            name=request.form['name'],
            details=request.form.get('details'),
            serial_number=request.form.get('serial_number'),
            category=request.form.get('category'),
            quantity=int(request.form.get('quantity', 1)),
            acquisition_date=datetime.strptime(request.form.get('acquisition_date'), '%Y-%m-%d') if request.form.get('acquisition_date') else None,
            unit=request.form.get('unit'),
            price=float(request.form.get('price')) if request.form.get('price') else None,
            note=request.form.get('note')
        )
        db.session.add(asset)
        db.session.commit()
        return redirect(url_for('asset_list'))
    return render_template('asset_form.html', asset=None)

@app.route('/assets/<int:asset_id>/edit', methods=['GET', 'POST'])
@login_required
def asset_edit(asset_id):
    asset = Asset.query.get_or_404(asset_id)
    if request.method == 'POST':
        asset.asset_code = request.form['asset_code']
        asset.sub_code = request.form.get('sub_code')
        asset.budget_year = request.form.get('budget_year')
        asset.name = request.form['name']
        asset.details = request.form.get('details')
        asset.serial_number = request.form.get('serial_number')
        asset.category = request.form.get('category')
        asset.quantity = int(request.form.get('quantity', 1))
        asset.acquisition_date = datetime.strptime(request.form.get('acquisition_date'), '%Y-%m-%d') if request.form.get('acquisition_date') else None
        asset.unit = request.form.get('unit')
        asset.price = float(request.form.get('price')) if request.form.get('price') else None
        asset.note = request.form.get('note')
        db.session.commit()
        return redirect(url_for('asset_list'))
    return render_template('asset_form.html', asset=asset)

@app.route('/assets/<int:asset_id>/delete', methods=['POST'])
@login_required
def asset_delete(asset_id):
    asset = Asset.query.get_or_404(asset_id)
    db.session.delete(asset)
    db.session.commit()
    return redirect(url_for('asset_list'))


@app.route('/inventory')
@login_required
def inventory_list():
    items = InventoryItem.query.all()
    return render_template('inventory_list.html', items=items)


@app.route('/inventory/add', methods=['GET', 'POST'])
@login_required
def inventory_add():
    if request.method == 'POST':
        item = InventoryItem(
            name=request.form['name'],
            quantity=int(request.form.get('quantity', 0)),
            location=request.form.get('location'),
            note=request.form.get('note'),
        )
        db.session.add(item)
        db.session.commit()
        return redirect(url_for('inventory_list'))
    return render_template('inventory_form.html', item=None)


@app.route('/inventory/<int:item_id>/edit', methods=['GET', 'POST'])
@login_required
def inventory_edit(item_id):
    item = InventoryItem.query.get_or_404(item_id)
    if request.method == 'POST':
        item.name = request.form['name']
        item.quantity = int(request.form.get('quantity', 0))
        item.location = request.form.get('location')
        item.note = request.form.get('note')
        db.session.commit()
        return redirect(url_for('inventory_list'))
    return render_template('inventory_form.html', item=item)


@app.route('/inventory/<int:item_id>/delete', methods=['POST'])
@login_required
def inventory_delete(item_id):
    item = InventoryItem.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    return redirect(url_for('inventory_list'))

@app.route('/export/<string:fmt>')
@login_required
def export(fmt):
    assets = Asset.query.all()
    data = [
        {
            'ลำดับ': a.id,
            'รหัสครุภัณฑ์': a.asset_code,
            'รหัสย่อย': a.sub_code,
            'ปีงบประมาณที่ได้มา': a.budget_year,
            'ชื่อครุภัณฑ์': a.name,
            'รายละเอียด': a.details,
            'หมายเลขเครื่อง/SN': a.serial_number,
            'ประเภท': a.category,
            'จำนวน': a.quantity,
            'วันที่ได้มา': a.acquisition_date.strftime('%Y-%m-%d') if a.acquisition_date else '',
            'หน่วยเบิก': a.unit,
            'ราคา': a.price,
            'หมายเหตุ': a.note,
        }
        for a in assets
    ]
    if fmt == 'excel':
        df = pd.DataFrame(data)
        path = 'assets.xlsx'
        df.to_excel(path, index=False)
        return send_file(path, as_attachment=True)
    elif fmt == 'word':
        doc = Document()
        table = doc.add_table(rows=1, cols=len(data[0]) if data else 1)
        hdr_cells = table.rows[0].cells
        for i, key in enumerate(data[0].keys() if data else ['รายการ']):
            hdr_cells[i].text = key
        for item in data:
            row_cells = table.add_row().cells
            for i, key in enumerate(item.keys()):
                row_cells[i].text = str(item[key])
        path = 'assets.docx'
        doc.save(path)
        return send_file(path, as_attachment=True)
    elif fmt == 'pdf':
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font('Arial', size=10)
        for item in data:
            line = ' | '.join([f"{k}: {v}" for k, v in item.items()])
            pdf.multi_cell(0, 5, line)
            pdf.ln(1)
        path = 'assets.pdf'
        pdf.output(path)
        return send_file(path, as_attachment=True)
    return redirect(url_for('asset_list'))

if __name__ == '__main__':
    app.run(debug=True)
