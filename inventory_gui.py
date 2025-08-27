import tkinter as tk
from tkinter import messagebox, ttk

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models import Asset, User, init_db


def get_session():
    engine = create_engine('sqlite:///inventory.db')
    init_db(engine)
    SessionLocal = sessionmaker(bind=engine)
    return SessionLocal()


class LoginWindow:
    def __init__(self, session):
        self.session = session
        self.root = tk.Tk()
        self.root.title('Login')
        tk.Label(self.root, text='Username').grid(row=0, column=0, padx=5, pady=5)
        self.username_var = tk.StringVar()
        tk.Entry(self.root, textvariable=self.username_var).grid(row=0, column=1, padx=5, pady=5)
        tk.Label(self.root, text='Password').grid(row=1, column=0, padx=5, pady=5)
        self.password_var = tk.StringVar()
        tk.Entry(self.root, textvariable=self.password_var, show='*').grid(row=1, column=1, padx=5, pady=5)
        tk.Button(self.root, text='Login', command=self.attempt_login).grid(row=2, column=0, columnspan=2, pady=10)

    def attempt_login(self):
        username = self.username_var.get()
        password = self.password_var.get()
        user = self.session.query(User).filter_by(username=username).first()
        if user and user.check_password(password):
            self.root.destroy()
            main_root = tk.Tk()
            InventoryGUI(main_root, self.session)
            main_root.mainloop()
        else:
            messagebox.showerror('Error', 'Invalid credentials')

    def run(self):
        self.root.mainloop()


class InventoryGUI:
    def __init__(self, root, session):
        self.root = root
        self.session = session
        self.root.title('Inventory Manager')
        self.search_var = tk.StringVar()
        self._build_ui()
        self.refresh_assets()

    def _build_ui(self):
        search_frame = tk.Frame(self.root)
        search_frame.pack(fill=tk.X, padx=10, pady=5)
        tk.Label(search_frame, text='Search:').pack(side=tk.LEFT)
        tk.Entry(search_frame, textvariable=self.search_var).pack(side=tk.LEFT, fill=tk.X, expand=True)
        tk.Button(search_frame, text='Go', command=self.refresh_assets).pack(side=tk.LEFT, padx=5)

        columns = ('id', 'asset_code', 'name', 'quantity')
        self.tree = ttk.Treeview(self.root, columns=columns, show='headings')
        for col in columns:
            self.tree.heading(col, text=col)
        self.tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        btn_frame = tk.Frame(self.root)
        btn_frame.pack(fill=tk.X, padx=10, pady=5)
        tk.Button(btn_frame, text='Add', command=self.add_asset).pack(side=tk.LEFT)
        tk.Button(btn_frame, text='Edit', command=self.edit_asset).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text='Delete', command=self.delete_asset).pack(side=tk.LEFT)

    def refresh_assets(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        query = self.session.query(Asset)
        search = self.search_var.get()
        if search:
            like = f"%{search}%"
            query = query.filter(Asset.name.ilike(like) | Asset.asset_code.ilike(like))
        for asset in query.all():
            self.tree.insert('', tk.END, values=(asset.id, asset.asset_code, asset.name, asset.quantity))

    def add_asset(self):
        AssetForm(self.root, self.session, callback=self.refresh_assets)

    def edit_asset(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning('Select', 'Please select an asset')
            return
        asset_id = self.tree.item(selected[0])['values'][0]
        asset = self.session.get(Asset, asset_id)
        AssetForm(self.root, self.session, asset, self.refresh_assets)

    def delete_asset(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning('Select', 'Please select an asset')
            return
        asset_id = self.tree.item(selected[0])['values'][0]
        asset = self.session.get(Asset, asset_id)
        if messagebox.askyesno('Delete', f'Delete {asset.name}?'):
            self.session.delete(asset)
            self.session.commit()
            self.refresh_assets()


class AssetForm:
    def __init__(self, master, session, asset=None, callback=None):
        self.session = session
        self.asset = asset
        self.callback = callback
        self.window = tk.Toplevel(master)
        self.window.title('Edit Asset' if asset else 'Add Asset')
        tk.Label(self.window, text='Asset Code').grid(row=0, column=0, padx=5, pady=5)
        self.code_var = tk.StringVar(value=asset.asset_code if asset else '')
        tk.Entry(self.window, textvariable=self.code_var).grid(row=0, column=1, padx=5, pady=5)
        tk.Label(self.window, text='Name').grid(row=1, column=0, padx=5, pady=5)
        self.name_var = tk.StringVar(value=asset.name if asset else '')
        tk.Entry(self.window, textvariable=self.name_var).grid(row=1, column=1, padx=5, pady=5)
        tk.Label(self.window, text='Quantity').grid(row=2, column=0, padx=5, pady=5)
        self.qty_var = tk.StringVar(value=str(asset.quantity) if asset else '1')
        tk.Entry(self.window, textvariable=self.qty_var).grid(row=2, column=1, padx=5, pady=5)
        tk.Button(self.window, text='Save', command=self.save).grid(row=3, column=0, columnspan=2, pady=10)

    def save(self):
        code = self.code_var.get().strip()
        name = self.name_var.get().strip()
        try:
            qty = int(self.qty_var.get())
        except ValueError:
            messagebox.showerror('Error', 'Quantity must be integer')
            return
        if not code or not name:
            messagebox.showerror('Error', 'Code and Name required')
            return
        if self.asset:
            self.asset.asset_code = code
            self.asset.name = name
            self.asset.quantity = qty
        else:
            self.session.add(Asset(asset_code=code, name=name, quantity=qty))
        self.session.commit()
        if self.callback:
            self.callback()
        self.window.destroy()


def main():
    session = get_session()
    login = LoginWindow(session)
    login.run()


if __name__ == '__main__':
    main()
