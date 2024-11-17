import socket
import os
import threading
import hashlib
from src.db.database_handler import DatabaseHandler

class FileServer:
    # File sharing configurations
    SERVER_IP = '127.0.0.1'
    SERVER_PORT = 5001
    BUFFER_SIZE = 1024
    ROOT_DIR = "D:/shared_directories"

    def __init__(self):
        self.db_handler = DatabaseHandler()

    def hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()

    def handle_client(self, client_socket):
        while True:
            try:
                request = client_socket.recv(self.BUFFER_SIZE).decode()
                command, *args = request.split()

                if command == 'REGISTER':
                    self.handle_register(client_socket, args)
                elif command == 'LOGIN':
                    self.handle_login(client_socket, args)
                elif command == 'CREATE_DIR':
                    self.handle_create_directory(client_socket, args)
                elif command == 'LIST_DIRS':
                    self.handle_list_directories(client_socket, args)
                else:
                    client_socket.send("ERROR: Unknown command".encode())
            except Exception as e:
                print(f"Error handling client request: {e}")
                break

        client_socket.close()  # Close the client socket after handling

    def handle_register(self, client_socket, args):
        if len(args) < 2:
            client_socket.send("ERROR: Thiếu thông tin đăng ký.".encode())
            return

        username, password = args[0], args[1]
        password_hash = self.hash_password(password)
        self.db_handler.register_user(username, password_hash)
        client_socket.send("Đăng ký thành công.".encode())

    def handle_login(self, client_socket, args):
        if len(args) < 2:
            client_socket.send("ERROR: Thiếu thông tin đăng nhập.".encode())
            return

        username, password = args[0], args[1]
        password_hash = self.hash_password(password)
        user = self.db_handler.get_user(username, password_hash)
        if user:
            client_socket.send(f"LOGIN_SUCCESS {user['id']} {user['username']}".encode())
        else:
            client_socket.send("LOGIN_FAILED".encode())

    def handle_create_directory(self, client_socket, args):
        if len(args) < 2:
            client_socket.send("ERROR: Thiếu thông tin để tạo thư mục.".encode())
            return

        user_id, directory_name = int(args[0]), args[1]
        
        # Kiểm tra xem thư mục đã tồn tại chưa
        dir_path = os.path.join(self.ROOT_DIR, str(user_id), directory_name)
        if os.path.exists(dir_path):
            client_socket.send(f"ERROR: Thư mục '{directory_name}' đã tồn tại.".encode())
            return

        # Tạo thư mục trên hệ thống file
        os.makedirs(dir_path)

        # Lưu thông tin vào database
        self.db_handler.add_directory(user_id, directory_name)
        client_socket.send(f"Thư mục '{directory_name}' đã được tạo.".encode())

    def handle_list_directories(self, client_socket, args):
        if len(args) < 1:
            client_socket.send("ERROR: Thiếu thông tin user ID.".encode())
            return

        user_id = int(args[0])
        directories = self.db_handler.get_user_directories(user_id)
        print(directories)
        if directories:
            dir_list = "\n".join(f"{d['id']} - {d['name']} - {d['path']}" for d in directories)
            client_socket.send(dir_list.encode())
        else:
            client_socket.send("Không có thư mục nào.".encode())

    def start_file_server(self):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind((self.SERVER_IP, self.SERVER_PORT))
        server_socket.listen(5)
        print("File Server is running...")

        while True:
            client_socket, addr = server_socket.accept()
            print(f"Connection from {addr}")
            client_thread = threading.Thread(target=self.handle_client, args=(client_socket,))
            client_thread.start()

if __name__ == "__main__":
    file_server = FileServer()
    file_server.start_file_server() 