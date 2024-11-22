import os
import json
import socket
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
        self.active_users = {}

    def hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()

    def handle_client(self, client_socket):
        client_address = client_socket.getpeername()
        self.active_users[client_address] = "Unknown"
        while True:
            try:
                request = client_socket.recv(self.BUFFER_SIZE).decode()
                command, *args = request.split()

                commands = {
                    'REGISTER': self.handle_register,
                    'LOGIN': self.handle_login,
                    'CREATE_DIR': self.handle_create_directory,
                    'LIST_DIRS': self.handle_list_directories,
                    'GET_ACTIVE_DIRS': self.handle_get_active_directories,
                }
                if command in commands:
                    commands[command](client_socket, args, client_address)
                else:
                    client_socket.send("ERROR: Unknown command".encode())
            except Exception as e:
                print(f"Error handling client request: {e}")
                break

        if client_address in self.active_users:
            del self.active_users[client_address]
        client_socket.close()  # Close the client socket after handling

    def handle_register(self, client_socket, args, *_):
        if len(args) < 2:
            client_socket.send("ERROR: Missing registration info.".encode())
            return

        username, password = args[0], args[1]
        password_hash = self.hash_password(password)
        self.db_handler.register_user(username, password_hash)
        client_socket.send("Registration successful.".encode())

    def handle_login(self, client_socket, args, client_address):
        if len(args) < 3:
            client_socket.send("ERROR: Missing login info.".encode())
            return

        username, password, client_ip, client_port = args[0], args[1], args[2], int(args[3])
        password_hash = self.hash_password(password)
        user = self.db_handler.get_user(username, password_hash)
        if user:
            self.active_users[client_address] = {"id": user["id"], "ip": client_ip, "port": client_port}
            client_socket.send(f"LOGIN_SUCCESS {user['id']} {user['username']}".encode())
        else:
            client_socket.send("LOGIN_FAILED".encode())

    def handle_create_directory(self, client_socket, args, *_):
        if len(args) < 2:
            client_socket.send("ERROR: Missing directory info.".encode())
            return

        user_id, directory_name = int(args[0]), args[1]
        
        # Kiểm tra xem thư mục đã tồn tại chưa
        dir_path = os.path.join(self.ROOT_DIR, str(user_id), directory_name)
        if os.path.exists(dir_path):
            client_socket.send(f"ERROR: Directory '{directory_name}' already exists.".encode())
            return
        os.makedirs(dir_path)

        self.db_handler.add_directory(user_id, directory_name)
        client_socket.send(f"Directory '{directory_name}' created.".encode())

    def handle_list_directories(self, client_socket, args, *_):
        if len(args) < 1:
            client_socket.send("ERROR: Missing user ID.".encode())
            return
        
        user_id = int(args[0])
        directories = self.db_handler.get_user_directories(user_id)
        if directories:
            dir_list = "\n".join(f"{d['name']} - {d['path']}" for d in directories)
            client_socket.send(dir_list.encode())
        else:
            client_socket.send("No directories found.".encode())

    def handle_get_active_directories(self, client_socket, *_):
        if not self.active_users:
            response = json.dumps({"status": "ACTIVE_DIRS", "message": "Không có thư mục nào."})
            client_socket.send(response.encode())
            return
        
        grouped_directories = {
            user["id"]: {
                "ip": user["ip"],
                "port": user["port"],
                "directories": [
                    {"name": d["name"], "path": d["path"]}
                    for d in self.db_handler.get_user_directories(user["id"])
                ],
            }
            for addr, user in self.active_users.items()
        }
        response = {
            "status": "ACTIVE_DIRS",
            "data": [
                {"user_id": user_id, **details}
                for user_id, details in grouped_directories.items()
            ],
        }
        client_socket.send(json.dumps(response).encode())

    def start_file_server(self):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind((self.SERVER_IP, self.SERVER_PORT))
        server_socket.listen(5)
        print("File Server is running...")

        try:
            while True:
                client_socket, addr = server_socket.accept()
                print(f"Connection from {addr}")
                client_thread = threading.Thread(target=self.handle_client, daemon=True, args=(client_socket,))
                client_thread.start()
        except KeyboardInterrupt:
            print("\nServer shutting down...")
        finally:
            server_socket.close()

if __name__ == "__main__":
    file_server = FileServer()
    file_server.start_file_server() 