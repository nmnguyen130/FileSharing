import sqlite3
from datetime import datetime

class DatabaseHandler:
    def __init__(self, db_name='file_server.db'):
        self.db_name = db_name
        self.init_database()

    def init_database(self):
        # Khởi tạo database và tạo các bảng users, directories và files
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()

            # Bảng users để lưu thông tin người dùng
            cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                username TEXT NOT NULL UNIQUE,
                                password_hash TEXT NOT NULL,
                                created_at TEXT NOT NULL
                             )''')

            # Bảng directories để lưu thông tin về thư mục
            cursor.execute('''CREATE TABLE IF NOT EXISTS directories (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                user_id INTEGER,
                                name TEXT NOT NULL,
                                path TEXT NOT NULL,
                                created_at TEXT NOT NULL,
                                FOREIGN KEY (user_id) REFERENCES users(id)
                             )''')

            # Bảng files để lưu thông tin về file trong các thư mục
            cursor.execute('''CREATE TABLE IF NOT EXISTS files (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                directory_id INTEGER,
                                user_id INTEGER,
                                name TEXT NOT NULL,
                                file_size INTEGER,
                                file_type TEXT,
                                created_at TEXT NOT NULL,
                                FOREIGN KEY (directory_id) REFERENCES directories(id),
                                FOREIGN KEY (user_id) REFERENCES users(id)
                             )''')
            
            conn.commit()

    def register_user(self, username, password_hash):
        # Thêm người dùng mới vào bảng users
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute('''INSERT INTO users (username, password_hash, created_at)
                                  VALUES (?, ?, ?)''', (username, password_hash, created_at))
                conn.commit()
                print(f"Tài khoản '{username}' đã được tạo thành công.")
        except sqlite3.IntegrityError:
            print("Username đã tồn tại. Vui lòng chọn tên khác.")

    def get_user(self, username, password_hash):
        # Lấy thông tin người dùng từ bảng users
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('''SELECT * FROM users WHERE username = ? AND password_hash = ?''', (username, password_hash))
            user = cursor.fetchone()
            if user:
                return {
                    'id': user[0],
                    'username': user[1],
                    'password_hash': user[2],
                    'created_at': user[3]
                }
            return None

    def remove_user(self, username):
        # Xóa người dùng khỏi bảng users
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('''DELETE FROM users WHERE username = ?''', (username,))
            conn.commit()
            print(f"Tài khoản '{username}' đã được xóa.")

    def remove_all_users(self):
        # Xóa tất cả người dùng khỏi bảng users
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('''DELETE FROM users''')
            conn.commit()
            print("Tất cả tài khoản đã được xóa.")

    def add_directory(self, user_id, name):
        # Thêm thư mục mới vào bảng directories
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        path = f"D:/shared_directories/{user_id}/{name}"
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            print(path, created_at)
            cursor.execute('''INSERT INTO directories (user_id, name, path, created_at)
                              VALUES (?, ?, ?, ?)''', (user_id, name, path, created_at))
            conn.commit()
            print(f"Thư mục '{name}' đã được tạo cho user ID {user_id}.")

    def get_user_directories(self, user_id):
        # Lấy danh sách thư mục của người dùng từ bảng directories
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('''SELECT * FROM directories WHERE user_id = ?''', (user_id,))
            directories = cursor.fetchall()
            return [{'id': d[0], 'user_id': d[1], 'name': d[2], 'path': d[3], 'created_at': d[4]} for d in directories]

    def add_file(self, directory_id, user_id, name, file_size, file_type):
        # Thêm file mới vào bảng files
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('''INSERT INTO files (directory_id, user_id, name, file_size, file_type, created_at)
                              VALUES (?, ?, ?, ?, ?, ?)''', (directory_id, user_id, name, file_size, file_type, created_at))
            conn.commit()
            print(f"File '{name}' đã được thêm vào thư mục ID {directory_id}.")