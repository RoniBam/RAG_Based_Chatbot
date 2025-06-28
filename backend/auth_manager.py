import sqlite3
import hashlib
import os
from datetime import datetime
from typing import Optional, Tuple

class AuthManager:
    def __init__(self, db_path: str = "users.db"):
        self.db_path = db_path
        self.init_database()
        self.create_admin_user()
    
    def init_database(self):
        """Initialize the SQLite database with users table"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create users table with admin field
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    is_admin BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP
                )
            ''')
            
            conn.commit()
            conn.close()
        except Exception as e:
            raise Exception(f"Database initialization failed: {str(e)}")
    
    def create_admin_user(self):
        """Create default admin user if it doesn't exist"""
        try:
            admin_username = "admin"
            admin_email = "admin@admin.com"
            admin_password = "admin123"
            
            if not self.user_exists(admin_username, admin_email):
                success, message = self.register_user(
                    admin_username, 
                    admin_email, 
                    admin_password, 
                    is_admin=True
                )
                print(f"Admin user creation: {message}")
        except Exception as e:
            print(f"Error creating admin user: {str(e)}")
    
    def hash_password(self, password: str) -> str:
        """Hash password using SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def register_user(self, username: str, email: str, password: str, is_admin: bool = False) -> Tuple[bool, str]:
        """Register a new user"""
        try:
            # Validate input
            if not username or not email or not password:
                return False, "All fields are required"
            
            if len(password) < 6:
                return False, "Password must be at least 6 characters long"
            
            if len(username) < 3:
                return False, "Username must be at least 3 characters long"
            
            # Check if user already exists
            if self.user_exists(username, email):
                return False, "Username or email already exists"
            
            # Hash password and store user
            password_hash = self.hash_password(password)
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO users (username, email, password_hash, is_admin)
                VALUES (?, ?, ?, ?)
            ''', (username, email, password_hash, is_admin))
            
            conn.commit()
            conn.close()
            
            return True, "User registered successfully"
            
        except Exception as e:
            return False, f"Registration failed: {str(e)}"
    
    def login_user(self, username: str, password: str) -> Tuple[bool, str, Optional[dict]]:
        """Login a user"""
        try:
            if not username or not password:
                return False, "Username and password are required", None
            
            password_hash = self.hash_password(password)
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, username, email, is_admin, created_at
                FROM users 
                WHERE (username = ? OR email = ?) AND password_hash = ?
            ''', (username, username, password_hash))
            
            user = cursor.fetchone()
            
            if user:
                # Update last login
                cursor.execute('''
                    UPDATE users SET last_login = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (user[0],))
                
                conn.commit()
                conn.close()
                
                user_data = {
                    'id': user[0],
                    'username': user[1],
                    'email': user[2],
                    'is_admin': user[3],
                    'created_at': user[4]
                }
                
                return True, "Login successful", user_data
            else:
                conn.close()
                return False, "Invalid username or password", None
                
        except Exception as e:
            return False, f"Login failed: {str(e)}", None
    
    def user_exists(self, username: str, email: str) -> bool:
        """Check if user already exists"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT COUNT(*) FROM users 
                WHERE username = ? OR email = ?
            ''', (username, email))
            
            count = cursor.fetchone()[0]
            conn.close()
            
            return count > 0
            
        except Exception:
            return False
    
    def get_user_by_id(self, user_id: int) -> Optional[dict]:
        """Get user data by ID"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, username, email, is_admin, created_at, last_login
                FROM users WHERE id = ?
            ''', (user_id,))
            
            user = cursor.fetchone()
            conn.close()
            
            if user:
                return {
                    'id': user[0],
                    'username': user[1],
                    'email': user[2],
                    'is_admin': user[3],
                    'created_at': user[4],
                    'last_login': user[5]
                }
            return None
            
        except Exception:
            return None
    
    def get_all_users(self) -> list:
        """Get all users (admin only)"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, username, email, is_admin, created_at, last_login
                FROM users ORDER BY created_at DESC
            ''')
            
            users = cursor.fetchall()
            conn.close()
            
            return [
                {
                    'id': user[0],
                    'username': user[1],
                    'email': user[2],
                    'is_admin': user[3],
                    'created_at': user[4],
                    'last_login': user[5]
                }
                for user in users
            ]
            
        except Exception:
            return []
    
    def delete_user(self, user_id: int) -> Tuple[bool, str]:
        """Delete a user (admin only)"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
            
            if cursor.rowcount > 0:
                conn.commit()
                conn.close()
                return True, "User deleted successfully"
            else:
                conn.close()
                return False, "User not found"
                
        except Exception as e:
            return False, f"Delete failed: {str(e)}"
