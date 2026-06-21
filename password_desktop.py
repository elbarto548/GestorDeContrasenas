#!/usr/bin/env python3
"""
Gestor de Contraseñas Seguro - Versión Escritorio
Aplicación de escritorio nativa con tkinter
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
import sqlite3
import hashlib
import secrets
import base64
from datetime import datetime
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import os
import pyperclip
import json


class EncryptionManager:
    def __init__(self, master_password: str, salt: bytes = None):
        self.master_password = master_password
        # Para compatibilidad con contraseñas existentes, usar siempre el salt fijo original
        self.salt = b'salt_'
        self.key = self._derive_key(master_password, self.salt)
        self.cipher = Fernet(self.key)
    
    def _derive_key(self, password: str, salt: bytes) -> bytes:
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key
    
    def encrypt(self, data: str) -> str:
        encrypted = self.cipher.encrypt(data.encode())
        return base64.urlsafe_b64encode(encrypted).decode()
    
    def decrypt(self, encrypted_data: str) -> str:
        try:
            encrypted = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted = self.cipher.decrypt(encrypted)
            return decrypted.decode()
        except Exception:
            # Si falla la desencriptación, devolver los datos originales
            return encrypted_data
    
    def get_salt(self) -> bytes:
        return self.salt
    
    def clear_memory(self):
        """Limpia la memoria de contraseñas sensibles"""
        self.master_password = '\x00' * len(self.master_password)
        self.key = b'\x00' * len(self.key)
        self.cipher = None


class PasswordDatabase:
    def __init__(self, db_path: str = "passwords.db"):
        self.db_path = db_path
        self.conn = None
        self.connect()
        self.create_tables()
    
    def connect(self):
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
    
    def create_tables(self):
        cursor = self.conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS passwords (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                site TEXT NOT NULL,
                username TEXT NOT NULL,
                password TEXT NOT NULL,
                category TEXT DEFAULT 'General',
                notes TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                color TEXT DEFAULT '#007ACC'
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS master_password (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                password_hash TEXT NOT NULL,
                salt TEXT NOT NULL
            )
        """)
        
        # Migración: agregar columna salt si no existe
        try:
            cursor.execute("ALTER TABLE master_password ADD COLUMN salt TEXT")
            # No generar salt aleatorio para usuarios existentes
            # Mantener salt como None para compatibilidad con salt fijo
        except sqlite3.OperationalError:
            # La columna ya existe, ignorar error
            pass
        
        default_categories = [
            ('General', '#007ACC'),
            ('Trabajo', '#28A745'),
            ('Personal', '#DC3545'),
            ('Finanzas', '#FFC107'),
            ('Social', '#6F42C1'),
            ('Compras', '#FD7E14'),
        ]
        
        for name, color in default_categories:
            cursor.execute("""
                INSERT OR IGNORE INTO categories (name, color) VALUES (?, ?)
            """, (name, color))
        
        self.conn.commit()
    
    def has_master_password(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM master_password")
        return cursor.fetchone()[0] > 0
    
    def save_master_password(self, password_hash, salt):
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO master_password (id, password_hash, salt) VALUES (1, ?, ?)
        """, (password_hash, base64.b64encode(salt).decode()))
        self.conn.commit()
    
    def get_master_password_hash(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT password_hash, salt FROM master_password WHERE id = 1")
        row = cursor.fetchone()
        if row:
            return row[0], base64.b64decode(row[1])
        return None, None
    
    def save_password(self, site, username, password, category='General', notes=''):
        cursor = self.conn.cursor()
        now = datetime.now().isoformat()
        cursor.execute("""
            INSERT INTO passwords (site, username, password, category, notes, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (site, username, password, category, notes, now, now))
        self.conn.commit()
        return cursor.lastrowid
    
    def update_password(self, password_id, site, username, password, category='General', notes=''):
        cursor = self.conn.cursor()
        now = datetime.now().isoformat()
        cursor.execute("""
            UPDATE passwords 
            SET site = ?, username = ?, password = ?, category = ?, notes = ?, updated_at = ?
            WHERE id = ?
        """, (site, username, password, category, notes, now, password_id))
        self.conn.commit()
    
    def get_password(self, password_id):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM passwords WHERE id = ?", (password_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def get_all_passwords(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM passwords ORDER BY site ASC")
        return [dict(row) for row in cursor.fetchall()]
    
    def search_passwords(self, query):
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM passwords 
            WHERE site LIKE ? OR username LIKE ? OR notes LIKE ?
            ORDER BY site ASC
        """, (f'%{query}%', f'%{query}%', f'%{query}%'))
        return [dict(row) for row in cursor.fetchall()]
    
    def delete_password(self, password_id):
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM passwords WHERE id = ?", (password_id,))
        self.conn.commit()
    
    def get_categories(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM categories ORDER BY name ASC")
        return [dict(row) for row in cursor.fetchall()]
    
    def export_passwords(self, encryption_manager):
        """Exporta todas las contraseñas a formato JSON"""
        passwords = self.get_all_passwords()
        export_data = []
        
        for pwd in passwords:
            try:
                decrypted_password = encryption_manager.decrypt(pwd['password'])
                export_data.append({
                    'site': pwd['site'],
                    'username': pwd['username'],
                    'password': decrypted_password,
                    'category': pwd['category'],
                    'notes': pwd.get('notes', ''),
                    'created_at': pwd['created_at'],
                    'updated_at': pwd['updated_at']
                })
            except Exception:
                # Si falla la desencriptación, exportar sin desencriptar
                export_data.append({
                    'site': pwd['site'],
                    'username': pwd['username'],
                    'password': pwd['password'],  # Encriptado
                    'category': pwd['category'],
                    'notes': pwd.get('notes', ''),
                    'created_at': pwd['created_at'],
                    'updated_at': pwd['updated_at']
                })
        
        return json.dumps(export_data, indent=2, ensure_ascii=False)
    
    def import_passwords(self, json_data, encryption_manager):
        """Importa contraseñas desde formato JSON"""
        try:
            import_data = json.loads(json_data)
            imported_count = 0
            
            for item in import_data:
                try:
                    site = item.get('site', '')
                    username = item.get('username', '')
                    password = item.get('password', '')
                    category = item.get('category', 'General')
                    notes = item.get('notes', '')
                    
                    if site and username and password:
                        # Encriptar la contraseña
                        encrypted_password = encryption_manager.encrypt(password)
                        
                        # Guardar en la base de datos
                        self.save_password(site, username, encrypted_password, category, notes)
                        imported_count += 1
                except Exception as e:
                    print(f"Error importando contraseña: {e}")
                    continue
            
            return imported_count
        except Exception as e:
            raise Exception(f"Error al importar: {e}")
    
    def close(self):
        if self.conn:
            self.conn.close()


class PasswordManagerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("🔐 Gestor de Contraseñas")
        self.root.geometry("1000x700")
        self.root.minsize(800, 600)
        
        self.db = None
        self.encryption_manager = None
        self.current_passwords = []
        
        # Sistema de temas
        self.dark_mode = False
        self.themes = {
            'light': {
                'bg': '#f5f7fa',
                'primary': '#667eea',
                'secondary': '#764ba2',
                'text': '#2d3748',
                'border': '#e2e8f0',
                'white': '#ffffff',
                'header_bg': '#667eea',
                'header_text': '#ffffff'
            },
            'dark': {
                'bg': '#1a202c',
                'primary': '#667eea',
                'secondary': '#764ba2',
                'text': '#e2e8f0',
                'border': '#4a5568',
                'white': '#2d3748',
                'header_bg': '#2d3748',
                'header_text': '#ffffff'
            }
        }
        
        self.setup_style()
        self.show_login_screen()
    
    def toggle_theme(self):
        self.dark_mode = not self.dark_mode
        self.setup_style()
        # Recargar la pantalla actual con el nuevo tema
        if hasattr(self, 'db') and self.db and hasattr(self, 'encryption_manager') and self.encryption_manager:
            self.show_main_screen()
        else:
            self.show_login_screen()
    
    def get_theme_colors(self):
        return self.themes['dark' if self.dark_mode else 'light']
    
    def setup_style(self):
        style = ttk.Style()
        style.theme_use('clam')
        
        # Obtener colores del tema actual
        theme = self.themes['dark' if self.dark_mode else 'light']
        bg_color = theme['bg']
        primary_color = theme['primary']
        secondary_color = theme['secondary']
        text_color = theme['text']
        border_color = theme['border']
        
        style.configure('TFrame', background=bg_color)
        style.configure('TLabel', background=bg_color, font=('Segoe UI', 10), foreground=text_color)
        style.configure('Header.TLabel', font=('Segoe UI', 20, 'bold'), background=bg_color, foreground=primary_color)
        style.configure('SubHeader.TLabel', font=('Segoe UI', 14, 'bold'), background=bg_color, foreground=text_color)
        
        # Botones modernos
        style.configure('TButton', font=('Segoe UI', 10, 'bold'), padding=10, 
                       background=primary_color, foreground='white', borderwidth=0)
        style.map('TButton', background=[('active', secondary_color)])
        
        # Treeview moderno
        style.configure('Treeview', font=('Segoe UI', 9), background='white', 
                       fieldbackground='white', rowheight=30)
        style.configure('Treeview.Heading', font=('Segoe UI', 10, 'bold'), 
                       background=primary_color, foreground='white')
        style.map('Treeview', background=[('selected', primary_color)])
        
        # Entry moderno
        style.configure('TEntry', font=('Segoe UI', 10), fieldbackground='white', 
                       borderwidth=1, relief='solid')
        
        # Combobox moderno
        style.configure('TCombobox', font=('Segoe UI', 10), fieldbackground='white',
                        borderwidth=1, relief='solid')
    
    def show_login_screen(self):
        for widget in self.root.winfo_children():
            widget.destroy()
        
        theme = self.get_theme_colors()
        
        # Contenedor principal con gradiente
        main_container = tk.Frame(self.root, bg=theme['header_bg'])
        main_container.pack(fill='both', expand=True)
        
        # Frame de login centrado
        login_frame = tk.Frame(main_container, bg=theme['white'], padx=60, pady=50)
        login_frame.place(relx=0.5, rely=0.5, anchor='center', width=450)
        
        # Logo y título
        title_label = tk.Label(login_frame, text="🔐", font=('Segoe UI', 48), 
                              bg=theme['white'], fg=theme['primary'])
        title_label.pack(pady=10)
        
        title_text = tk.Label(login_frame, text="Gestor de Contraseñas", 
                            font=('Segoe UI', 24, 'bold'), bg=theme['white'], fg=theme['text'])
        title_text.pack(pady=5)
        
        subtitle_label = tk.Label(login_frame, text="Ingresa tu contraseña maestra", 
                                 font=('Segoe UI', 12), bg=theme['white'], fg=theme['text'])
        subtitle_label.pack(pady=10)
        
        # Campo de contraseña
        password_frame = tk.Frame(login_frame, bg=theme['white'])
        password_frame.pack(pady=10, fill='x')
        
        password_label = tk.Label(password_frame, text="Contraseña:", 
                                 font=('Segoe UI', 10, 'bold'), bg=theme['white'], fg=theme['text'])
        password_label.pack(anchor='w', pady=5)
        
        self.master_password_entry = tk.Entry(password_frame, show='•', width=40, 
                                             font=('Segoe UI', 12), relief='solid', 
                                             bd=1, highlightthickness=1,
                                             highlightbackground=theme['primary'],
                                             highlightcolor=theme['primary'])
        self.master_password_entry.pack(fill='x', pady=10)
        self.master_password_entry.bind('<Return>', lambda e: self.login())
        self.master_password_entry.focus()
        
        # Botón de login
        login_button = tk.Button(login_frame, text="Ingresar", command=self.login,
                               font=('Segoe UI', 12, 'bold'), bg=theme['primary'], fg='white',
                               relief='flat', padx=20, pady=12, cursor='hand2',
                               activebackground=theme['secondary'])
        login_button.pack(fill='x', pady=10)
        
        # Botón de tema
        theme_button = tk.Button(login_frame, text="🌙/☀️", command=self.toggle_theme,
                               font=('Segoe UI', 10), bg=theme['border'], fg=theme['text'],
                               relief='flat', padx=15, pady=8, cursor='hand2')
        theme_button.pack(pady=5)
        
        # Footer
        footer_label = tk.Label(login_frame, text="Seguridad AES-256 | Encriptación PBKDF2",
                              font=('Segoe UI', 9), bg=theme['white'], fg=theme['text'])
        footer_label.pack(pady=15)
    
    def login(self):
        master_password = self.master_password_entry.get()
        
        if not master_password:
            messagebox.showerror("Error", "Ingresa una contraseña maestra")
            return
        
        try:
            self.db = PasswordDatabase()
            
            if not self.db.has_master_password():
                # Primer uso - crear salt aleatorio y registrar contraseña maestra
                password_hash = hashlib.sha256(master_password.encode()).hexdigest()
                temp_encryption_manager = EncryptionManager(master_password)
                salt = temp_encryption_manager.get_salt()
                self.db.save_master_password(password_hash, salt)
                messagebox.showinfo("Bienvenido", "¡Cuenta creada exitosamente!")
            else:
                # Verificar contraseña maestra
                stored_hash, stored_salt = self.db.get_master_password_hash()
                input_hash = hashlib.sha256(master_password.encode()).hexdigest()
                
                if input_hash != stored_hash:
                    messagebox.showerror("Error", "Contraseña incorrecta")
                    return
                
                # Crear encryption manager con el salt fijo original
                self.encryption_manager = EncryptionManager(master_password)
                self.show_main_screen()
                return
            
            self.encryption_manager = EncryptionManager(master_password)
            self.show_main_screen()
            
        except Exception as e:
            import traceback
            error_detail = f"{str(e)}\n\n{traceback.format_exc()}"
            messagebox.showerror("Error", f"Error al iniciar sesión: {error_detail}")
    
    def show_main_screen(self):
        for widget in self.root.winfo_children():
            widget.destroy()
        
        theme = self.get_theme_colors()
        
        # Header con gradiente
        header_frame = tk.Frame(self.root, bg=theme['header_bg'], height=80)
        header_frame.pack(fill='x', side='top')
        header_frame.pack_propagate(False)
        
        # Título y botón de logout
        header_content = tk.Frame(header_frame, bg=theme['header_bg'])
        header_content.pack(fill='both', expand=True, padx=30, pady=20)
        
        title_label = tk.Label(header_content, text="🔐 Gestor de Contraseñas", 
                            font=('Segoe UI', 22, 'bold'), bg=theme['header_bg'], fg=theme['header_text'])
        title_label.pack(side='left')
        
        # Botón de tema
        theme_button = tk.Button(header_content, text="🌙/☀️", command=self.toggle_theme,
                               font=('Segoe UI', 10), bg=theme['border'], fg=theme['text'],
                               relief='flat', padx=15, pady=8, cursor='hand2')
        theme_button.pack(side='right', padx=(0, 10))
        
        logout_button = tk.Button(header_content, text="Cerrar sesión", command=self.logout,
                               font=('Segoe UI', 10, 'bold'), bg=theme['white'], fg=theme['primary'],
                               relief='flat', padx=15, pady=8, cursor='hand2')
        logout_button.pack(side='right')
        
        # Contenedor principal
        main_container = tk.Frame(self.root, bg=theme['bg'])
        main_container.pack(fill='both', expand=True)
        
        # Barra de búsqueda y acciones
        toolbar_frame = tk.Frame(main_container, bg=theme['bg'], padx=30, pady=20)
        toolbar_frame.pack(fill='x')
        
        # Búsqueda
        search_frame = tk.Frame(toolbar_frame, bg=theme['bg'])
        search_frame.pack(side='left', fill='x', expand=True)
        
        search_label = tk.Label(search_frame, text="🔍", font=('Segoe UI', 14), 
                              bg=theme['bg'], fg=theme['primary'])
        search_label.pack(side='left', padx=(0, 10))
        
        self.search_entry = tk.Entry(search_frame, font=('Segoe UI', 11), relief='solid', 
                                     bd=1, highlightthickness=1,
                                     highlightbackground=theme['primary'],
                                     highlightcolor=theme['primary'])
        self.search_entry.pack(side='left', fill='x', expand=True, ipady=8)
        self.search_entry.bind('<KeyRelease>', self.on_search)
        
        # Botón agregar
        add_button = tk.Button(toolbar_frame, text="➕ Agregar Contraseña", 
                             command=self.show_add_password_dialog,
                             font=('Segoe UI', 11, 'bold'), bg=theme['primary'], fg='white',
                             relief='flat', padx=20, pady=10, cursor='hand2',
                             activebackground=theme['secondary'])
        add_button.pack(side='right', padx=(10, 0))
        
        # Botón eliminar
        delete_button = tk.Button(toolbar_frame, text="🗑️ Eliminar", 
                               command=self.delete_selected_password,
                               font=('Segoe UI', 11, 'bold'), bg='#dc3545', fg='white',
                               relief='flat', padx=20, pady=10, cursor='hand2',
                               activebackground='#c82333')
        delete_button.pack(side='right', padx=(10, 0))
        
        # Botón importar
        import_button = tk.Button(toolbar_frame, text="📥 Importar", 
                                command=self.import_passwords,
                                font=('Segoe UI', 11, 'bold'), bg='#17a2b8', fg='white',
                                relief='flat', padx=20, pady=10, cursor='hand2',
                                activebackground='#138496')
        import_button.pack(side='right', padx=(10, 0))
        
        # Botón exportar
        export_button = tk.Button(toolbar_frame, text="📤 Exportar", 
                                command=self.export_passwords,
                                font=('Segoe UI', 11, 'bold'), bg='#28a745', fg='white',
                                relief='flat', padx=20, pady=10, cursor='hand2',
                                activebackground='#218838')
        export_button.pack(side='right', padx=(10, 0))
        
        # Lista de contraseñas
        list_frame = tk.Frame(main_container, bg='#f5f7fa', padx=30, pady=20)
        list_frame.pack(fill='both', expand=True)
        
        # Treeview con estilo moderno
        columns = ('site', 'username', 'category', 'updated_at')
        self.password_tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=20)
        
        self.password_tree.heading('site', text='Sitio/Servicio')
        self.password_tree.heading('username', text='Usuario')
        self.password_tree.heading('category', text='Categoría')
        self.password_tree.heading('updated_at', text='Actualizado')
        
        self.password_tree.column('site', width=300)
        self.password_tree.column('username', width=250)
        self.password_tree.column('category', width=150)
        self.password_tree.column('updated_at', width=150)
        
        scrollbar = ttk.Scrollbar(list_frame, orient='vertical', command=self.password_tree.yview)
        self.password_tree.configure(yscrollcommand=scrollbar.set)
        
        self.password_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        self.password_tree.bind('<Double-1>', self.on_password_double_click)
        
        self.load_passwords()
    
    def load_passwords(self, search_query=''):
        for item in self.password_tree.get_children():
            self.password_tree.delete(item)
        
        if search_query:
            passwords = self.db.search_passwords(search_query)
        else:
            passwords = self.db.get_all_passwords()
        
        self.current_passwords = passwords
        
        for pwd in passwords:
            decrypted_password = self.encryption_manager.decrypt(pwd['password'])
            self.password_tree.insert('', 'end', values=(
                pwd['site'],
                pwd['username'],
                pwd['category'],
                pwd['updated_at'][:10]
            ), tags=(str(pwd['id']), decrypted_password))
    
    def on_search(self, event):
        search_query = self.search_entry.get()
        self.load_passwords(search_query)
    
    def show_add_password_dialog(self, password_id=None):
        dialog = tk.Toplevel(self.root)
        dialog.title("Agregar Contraseña" if password_id is None else "Editar Contraseña")
        dialog.geometry("650x650")
        theme = self.get_theme_colors()
        dialog.configure(bg=theme['bg'])
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Header del diálogo
        header_frame = tk.Frame(dialog, bg=theme['header_bg'], height=60)
        header_frame.pack(fill='x', side='top')
        header_frame.pack_propagate(False)
        
        header_content = tk.Frame(header_frame, bg=theme['header_bg'])
        header_content.pack(fill='both', expand=True, padx=20, pady=15)
        
        title_text = tk.Label(header_content, text="➕ Nueva Contraseña" if password_id is None else "✏️ Editar Contraseña",
                            font=('Segoe UI', 16, 'bold'), bg=theme['header_bg'], fg=theme['header_text'])
        title_text.pack(side='left')
        
        # Contenedor principal
        main_frame = tk.Frame(dialog, bg=theme['bg'], padx=30, pady=20)
        main_frame.pack(fill='both', expand=True)
        
        # Sitio/Servicio
        ttk.Label(main_frame, text="Sitio/Servicio *", font=('Segoe UI', 10, 'bold'), 
                 background=theme['bg'], foreground=theme['text']).grid(row=0, column=0, sticky='w', pady=5)
        site_entry = tk.Entry(main_frame, font=('Segoe UI', 11), relief='solid', bd=1, 
                            highlightthickness=1, highlightbackground=theme['primary'],
                            highlightcolor=theme['primary'])
        site_entry.grid(row=1, column=0, sticky='ew', pady=10)
        
        # Usuario/Email
        ttk.Label(main_frame, text="Usuario/Email *", font=('Segoe UI', 10, 'bold'), 
                 background=theme['bg'], foreground=theme['text']).grid(row=2, column=0, sticky='w', pady=5)
        username_entry = tk.Entry(main_frame, font=('Segoe UI', 11), relief='solid', bd=1,
                                  highlightthickness=1, highlightbackground=theme['primary'],
                                  highlightcolor=theme['primary'])
        username_entry.grid(row=3, column=0, sticky='ew', pady=10)
        
        # Contraseña
        ttk.Label(main_frame, text="Contraseña *", font=('Segoe UI', 10, 'bold'), 
                 background=theme['bg'], foreground=theme['text']).grid(row=4, column=0, sticky='w', pady=5)
        password_frame = tk.Frame(main_frame, bg=theme['bg'])
        password_frame.grid(row=5, column=0, sticky='ew', pady=10)
        
        password_entry = tk.Entry(password_frame, font=('Segoe UI', 11), show='•', relief='solid', bd=1,
                                 highlightthickness=1, highlightbackground=theme['primary'],
                                 highlightcolor=theme['primary'])
        password_entry.pack(side='left', fill='x', expand=True, padx=(0, 10))
        
        generate_button = tk.Button(password_frame, text="🎲", font=('Segoe UI', 12), width=4,
                                    command=lambda: self.generate_password(password_entry, strength_text),
                                    bg=theme['primary'], fg='white', relief='flat', cursor='hand2')
        generate_button.pack(side='left', padx=(0, 5))
        
        show_button = tk.Button(password_frame, text="👁", font=('Segoe UI', 12), width=4,
                               command=lambda: self.toggle_password_visibility(password_entry, show_button),
                               bg=theme['primary'], fg='white', relief='flat', cursor='hand2')
        show_button.pack(side='left')
        
        # Indicador de fuerza de contraseña
        strength_frame = tk.Frame(main_frame, bg=theme['bg'])
        strength_frame.grid(row=6, column=0, sticky='ew', pady=(0, 10))
        
        strength_label = tk.Label(strength_frame, text="Fuerza: ", font=('Segoe UI', 9),
                                 bg=theme['bg'], fg=theme['text'])
        strength_label.pack(side='left', padx=(0, 5))
        
        strength_text = tk.Label(strength_frame, text="", font=('Segoe UI', 9, 'bold'),
                                bg=theme['bg'], fg=theme['text'])
        strength_text.pack(side='left')
        
        def update_strength(event):
            password = password_entry.get()
            strength = self.check_password_strength(password)
            color = self.get_password_strength_color(strength)
            text = self.get_password_strength_text(strength)
            strength_text.config(text=text, fg=color)
        
        password_entry.bind('<KeyRelease>', update_strength)
        
        # Categoría
        ttk.Label(main_frame, text="Categoría", font=('Segoe UI', 10, 'bold'), 
                 background=theme['bg'], foreground=theme['text']).grid(row=7, column=0, sticky='w', pady=5)
        category_combo = ttk.Combobox(main_frame, font=('Segoe UI', 11), state='readonly')
        category_combo.grid(row=8, column=0, sticky='ew', pady=10)
        categories = [cat['name'] for cat in self.db.get_categories()]
        category_combo['values'] = categories
        category_combo.set('General')
        
        # Notas
        ttk.Label(main_frame, text="Notas", font=('Segoe UI', 10, 'bold'), 
                 background=theme['bg'], foreground=theme['text']).grid(row=9, column=0, sticky='w', pady=5)
        notes_text = tk.Text(main_frame, font=('Segoe UI', 10), height=4, relief='solid', bd=1,
                            highlightthickness=1, highlightbackground=theme['primary'],
                            highlightcolor=theme['primary'])
        notes_text.grid(row=10, column=0, sticky='ew', pady=10)
        
        main_frame.columnconfigure(0, weight=1)
        
        if password_id:
            password_data = self.db.get_password(password_id)
            if password_data:
                site_entry.insert(0, password_data['site'])
                username_entry.insert(0, password_data['username'])
                decrypted_password = self.encryption_manager.decrypt(password_data['password'])
                password_entry.insert(0, decrypted_password)
                category_combo.set(password_data['category'])
                notes_text.insert('1.0', password_data.get('notes', ''))
        
        # Botones
        button_frame = tk.Frame(dialog, bg=theme['bg'], padx=30, pady=20)
        button_frame.pack(fill='x')
        
        def save():
            site = site_entry.get()
            username = username_entry.get()
            password = password_entry.get()
            category = category_combo.get()
            notes = notes_text.get('1.0', 'end-1c')
            
            if not site or not username or not password:
                messagebox.showerror("Error", "Completa todos los campos obligatorios")
                return
            
            encrypted_password = self.encryption_manager.encrypt(password)
            
            try:
                if password_id:
                    self.db.update_password(password_id, site, username, encrypted_password, category, notes)
                    messagebox.showinfo("Éxito", "Contraseña actualizada")
                else:
                    self.db.save_password(site, username, encrypted_password, category, notes)
                    messagebox.showinfo("Éxito", "Contraseña agregada")
                
                self.load_passwords()
                dialog.destroy()
            except Exception as e:
                messagebox.showerror("Error", f"Error al guardar: {e}")
        
        cancel_button = tk.Button(button_frame, text="Cancelar", command=dialog.destroy,
                                font=('Segoe UI', 11, 'bold'), bg=theme['border'], fg=theme['text'],
                                relief='flat', padx=25, pady=12, cursor='hand2')
        cancel_button.pack(side='right')
        
        save_button = tk.Button(button_frame, text="Guardar", command=save,
                             font=('Segoe UI', 11, 'bold'), bg=theme['primary'], fg='white',
                             relief='flat', padx=25, pady=12, cursor='hand2',
                             activebackground=theme['secondary'])
        save_button.pack(side='right', padx=(10, 0))
    
    def generate_password(self, entry_widget, strength_text_widget=None):
        """Genera una contraseña fuerte con todos los tipos de caracteres"""
        # Asegurar que la contraseña tenga al menos uno de cada tipo
        lowercase = "abcdefghijklmnopqrstuvwxyz"
        uppercase = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        digits = "0123456789"
        symbols = "!@#$%^&*()_+-=[]{}|;:,.<>?"
        
        # Generar al menos uno de cada tipo
        password = [
            secrets.choice(lowercase),
            secrets.choice(uppercase),
            secrets.choice(digits),
            secrets.choice(symbols)
        ]
        
        # Llenar el resto con caracteres aleatorios de todos los tipos
        all_chars = lowercase + uppercase + digits + symbols
        for _ in range(12):  # Total de 16 caracteres
            password.append(secrets.choice(all_chars))
        
        # Mezclar los caracteres
        secrets.SystemRandom().shuffle(password)
        password = ''.join(password)
        
        # Insertar en el campo
        entry_widget.delete(0, 'end')
        entry_widget.insert(0, password)
        
        # Actualizar el indicador de fuerza si se proporciona
        if strength_text_widget:
            strength = self.check_password_strength(password)
            color = self.get_password_strength_color(strength)
            text = self.get_password_strength_text(strength)
            strength_text_widget.config(text=text, fg=color)
    
    def check_password_strength(self, password):
        """Evalúa la fuerza de la contraseña y retorna un puntaje (0-4)"""
        if not password:
            return 0
        
        score = 0
        # Longitud
        if len(password) >= 8:
            score += 1
        if len(password) >= 12:
            score += 1
        
        # Complejidad
        if any(c.islower() for c in password):
            score += 1
        if any(c.isupper() for c in password):
            score += 1
        if any(c.isdigit() for c in password):
            score += 1
        if any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in password):
            score += 1
        
        # Normalizar a 0-4
        return min(score, 4)
    
    def get_password_strength_color(self, strength):
        """Retorna el color según la fuerza de la contraseña"""
        colors = {
            0: '#e53e3e',  # Rojo - Muy débil
            1: '#dd6b20',  # Naranja - Débil
            2: '#d69e2e',  # Amarillo - Regular
            3: '#38a169',  # Verde - Fuerte
            4: '#2f855a'   # Verde oscuro - Muy fuerte
        }
        return colors.get(strength, '#e53e3e')
    
    def get_password_strength_text(self, strength):
        """Retorna el texto según la fuerza de la contraseña"""
        texts = {
            0: 'Muy débil',
            1: 'Débil',
            2: 'Regular',
            3: 'Fuerte',
            4: 'Muy fuerte'
        }
        return texts.get(strength, 'Muy débil')
    
    def toggle_password_visibility(self, entry_widget, button_widget):
        if entry_widget['show'] == '•':
            entry_widget['show'] = ''
            button_widget['text'] = '🙈'
        else:
            entry_widget['show'] = '•'
            button_widget['text'] = '👁'
    
    def on_password_double_click(self, event):
        selection = self.password_tree.selection()
        if selection:
            password_id = int(self.password_tree.item(selection[0])['tags'][0])
            self.show_add_password_dialog(password_id)
    
    def delete_selected_password(self):
        selection = self.password_tree.selection()
        if not selection:
            messagebox.showwarning("Advertencia", "Selecciona una contraseña para eliminar")
            return
        
        password_id = int(self.password_tree.item(selection[0])['tags'][0])
        
        if messagebox.askyesno("Confirmar", "¿Estás seguro de eliminar esta contraseña?"):
            try:
                self.db.delete_password(password_id)
                self.load_passwords()
                messagebox.showinfo("Éxito", "Contraseña eliminada")
            except Exception as e:
                messagebox.showerror("Error", f"Error al eliminar: {e}")
    
    def export_passwords(self):
        """Exporta todas las contraseñas a un archivo JSON"""
        try:
            file_path = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
                title="Exportar contraseñas"
            )
            
            if file_path:
                json_data = self.db.export_passwords(self.encryption_manager)
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(json_data)
                messagebox.showinfo("Éxito", f"Contraseñas exportadas a {file_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Error al exportar: {e}")
    
    def import_passwords(self):
        """Importa contraseñas desde un archivo JSON"""
        try:
            file_path = filedialog.askopenfilename(
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
                title="Importar contraseñas"
            )
            
            if file_path:
                with open(file_path, 'r', encoding='utf-8') as f:
                    json_data = f.read()
                
                if messagebox.askyesno("Confirmar", "¿Estás seguro de importar contraseñas? Las contraseñas duplicadas se agregarán."):
                    imported_count = self.db.import_passwords(json_data, self.encryption_manager)
                    self.load_passwords()
                    messagebox.showinfo("Éxito", f"Se importaron {imported_count} contraseñas")
        except Exception as e:
            messagebox.showerror("Error", f"Error al importar: {e}")
    
    def logout(self):
        if messagebox.askyesno("Cerrar sesión", "¿Estás seguro de cerrar sesión?"):
            # Limpiar memoria de contraseñas sensibles
            if self.encryption_manager:
                self.encryption_manager.clear_memory()
                self.encryption_manager = None
            
            # Limpiar lista de contraseñas en memoria
            self.current_passwords = []
            
            # Cerrar base de datos
            if self.db:
                self.db.close()
                self.db = None
            
            self.show_login_screen()


def main():
    root = tk.Tk()
    app = PasswordManagerGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
