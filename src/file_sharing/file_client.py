from asyncio import Queue
import os
import json
import socket
import threading
from src.dhcp.dhcp_client import DhcpClient

class FileClient:
    SERVER_IP = '127.0.0.1'
    SERVER_PORT = 5001
    BUFFER_SIZE = 1024
    ROOT_DIR = "D:/shared_directories"

    def __init__(self, assigned_ip):
        self.server_ip = self.SERVER_IP
        self.assigned_ip = assigned_ip
        self.local_ip = self.get_local_ip()
        self.client_port = self.find_available_port()
        self.peer_connections = {}
        
        self.setup_server_connection()
        self.setup_peer_socket()

    @staticmethod
    def get_local_ip():
        hostname = socket.gethostname()
        return socket.gethostbyname(hostname)
    
    def find_available_port(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.bind(('', 0))  # Bind to an available port
            return sock.getsockname()[1]  # Return the port number
    
    def setup_server_connection(self):
        """Establish TCP connection to the server."""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.connect((self.SERVER_IP, self.SERVER_PORT))
        except Exception as e:
            print(f"Error connecting to server: {e}")
            self.server_socket = None

    def setup_peer_socket(self):
        """Set up TCP socket for P2P communication."""
        self.peer_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.peer_socket.bind((self.local_ip, self.client_port))
        self.peer_socket.listen(5)
        print(f"Listening for peers on {self.local_ip}:{self.client_port}")
        threading.Thread(target=self.listen_for_peers, daemon=True).start()

    def send_to_server(self, command):
        """Send command to server via TCP and return the response."""
        try:
            self.server_socket.send(command.encode())
            response = self.server_socket.recv(self.BUFFER_SIZE).decode()
            print(f"Server response: {response}")
            return response  # Return the response for further processing
        except Exception as e:
            print(f"Error sending to server: {e}")
            return "Error: Could not connect to server."

    def listen_for_peers(self):
        while True:
            try:
                conn, addr = self.peer_socket.accept()
                threading.Thread(target=self.handle_peer_connection, args=(conn, addr), daemon=True).start()
            except Exception as e:
                print(f"Error accepting peer connection: {e}")

    def handle_peer_connection(self, conn, addr):
        try:
            while True:
                command = conn.recv(self.BUFFER_SIZE).decode()
                if not command:
                    break
                print(f"Received command from {addr}: {command}")

                if command.startswith("DOWNLOAD_FILE"):
                    _, file_path = command.split(maxsplit=1)
                    self.send_file(file_path, conn)
                elif command.startswith("LIST_FILE"):
                    _, directory_path = command.split(maxsplit=1)
                    self.list_files_in_directory(directory_path, conn)
                elif command.startswith("GET_FILE_SIZE"):
                    _, file_path = command.split(maxsplit=1)
                    self.get_size(file_path, conn)
                elif command.startswith("DOWNLOAD_CHUNK"):
                    _, file_path, start, end = command.split()
                    start, end = int(start), int(end)
                    if os.path.exists(file_path):
                        with open(file_path, "rb") as f:
                            f.seek(start)
                            while start <= end:
                                chunk = f.read(min(self.BUFFER_SIZE, end - start + 1))
                                if not chunk:
                                    break
                                conn.sendall(chunk)
                                start += len(chunk)
                                print(start)
                        conn.sendall(b"END_OF_CHUNK")
                    else:
                        conn.sendall(b"ERROR: File not found")
                else:
                    print(f"Unknown command: {command}")

        except Exception as e:
            print(f"Error handling peer connection: {e}")
        finally:
            conn.close()

    def list_files_in_directory(self, directory_path, conn):
        if os.path.exists(directory_path) and os.path.isdir(directory_path):
            try:
                files = [{
                    "name": entry,
                    "path": os.path.join(directory_path, entry)
                } for entry in os.listdir(directory_path) if os.path.isfile(os.path.join(directory_path, entry))]
                print(files)
                self.send_data_in_chunks(json.dumps(files), conn)
                conn.sendall(b"END_OF_LIST")
            except Exception as e:
                print(f"Error getting list of files: {e}")
        else:
            print(f"Invalid directory: {directory_path}")

    def get_size(self, file_path, conn):
        if os.path.exists(file_path):
            file_size = os.path.getsize(file_path)
            conn.sendall(str(file_size).encode())
        else:
            conn.sendall(b"ERROR: File not found")

    def register(self, username, password):
        self.send_to_server(f"REGISTER {username} {password}")

    def login(self, username, password):
        response = self.send_to_server(f"LOGIN {username} {password} {self.local_ip} {self.client_port}")
        if response.startswith("LOGIN_SUCCESS"):
            _, user_id, user_name = response.split()
            self.user_id = int(user_id)
            self.username = user_name
            print(f"Login successful! User ID: {self.user_id}, Username: {self.username}")
            return True
        else:
            print("Login failed.")
            return False

    def create_directory(self, directory_name):
        # Kiểm tra xem thư mục đã tồn tại chưa
        dir_path = os.path.join(self.ROOT_DIR, str(self.user_id), directory_name)
        if os.path.exists(dir_path):
            print(f"ERROR: Directory '{directory_name}' already exists.")
            return
        os.makedirs(dir_path)

        self.send_to_server(f"CREATE_DIR {self.user_id} {directory_name}")
        return True

    def list_directories(self, user_id):
        self.send_to_server(f"LIST_DIRS {user_id}")

    def get_active_directories(self):
        response = self.send_to_server("GET_ACTIVE_DIRS")
        try:
            data = json.loads(response)
            if data["status"] == "ACTIVE_DIRS":
                return data.get("data", [])
            else:
                print(f"Error: {data.get('message', 'Unable to fetch directory list.')}")
                return None
        except json.JSONDecodeError:
            print("Error: Failed to parse server response as JSON.")
            return []
        except Exception as e:
            print(f"Unexpected error: {e}")
            return []
        
    def list_file_in_directory(self, target_ip, target_port, directory_path):
        """Request the contents of a directory from a peer."""
        try:
            with socket.create_connection((target_ip, target_port)) as peer_socket:
                command = f"LIST_FILE {directory_path}"
                peer_socket.sendall(command.encode())

                # Receive the response
                response_data = b""
                while True:
                    data = peer_socket.recv(self.BUFFER_SIZE)
                    if data == b"END_OF_LIST":
                        break
                    response_data += data

                try:
                    response = json.loads(response_data.decode())
                    return response
                except json.JSONDecodeError as e:
                    print(f"Error decoding JSON: {e}")
                    return []
        except Exception as e:
            print(f"Error listing files: {e}")
            return []

    def send_file(self, file_path, conn):
        """Send file via TCP to a connected peer."""
        if not os.path.exists(file_path):
                conn.sendall(b"ERROR: File not found")
                return
        try:
            with open(file_path, "rb") as file:
                while (data := file.read(self.BUFFER_SIZE)):
                    conn.sendall(data)
            conn.sendall(b"END_OF_FILE")  # Mark end of file
            print(f"File '{file_path}' sent successfully.")
        except Exception as e:
            print(f"Error sending file: {e}")

    def download_file(self, target_ip, target_port, file_path):
        """Download a file from a peer via TCP."""
        # Receive the file
        file_name = os.path.basename(file_path)
        download_directory = f"D:/shared_directories/{self.user_id}/download"
        os.makedirs(download_directory, exist_ok=True)  # Create folder if it doesn't exist
        download_path = os.path.join(download_directory, file_name)
        
        try:
            with socket.create_connection((target_ip, target_port)) as peer_socket:
                peer_socket.sendall(f"DOWNLOAD_FILE {file_path}".encode())

                with open(download_path, "wb") as file:
                    while True:
                        data = peer_socket.recv(self.BUFFER_SIZE)
                        if data == b"END_OF_FILE":
                            print(f"File '{file_name}' downloaded successfully to '{download_path}'.")
                            break
                        file.write(data)
        except Exception as e:
            print(f"Error downloading file: {e}")

    def search_file_across_peers(self, file_name):
        """Search for a file across all peers."""
        peers_with_file = []
        for user in self.get_active_directories():
            user_ip = user["ip"]
            user_port = user["port"]
            directories = user["directories"]

            for directory in directories:
                files = self.list_file_in_directory(user_ip, user_port, directory["path"])
                for file in files:
                    if file["name"] == file_name:
                        peers_with_file.append({
                            "ip": user_ip,
                            "port": user_port,
                            "path": file["path"]
                        })
        return peers_with_file
    
    def get_file_size(self, peer, file_path):
        """Request file size from a peer."""
        try:
            with socket.create_connection((peer["ip"], peer["port"])) as peer_socket:
                command = f"GET_FILE_SIZE {file_path}"
                peer_socket.sendall(command.encode())
                size = peer_socket.recv(1024).decode()
                return int(size)
        except Exception as e:
            print(f"Error retrieving file size from {peer['ip']}:{peer['port']}: {e}")
            return None

    def download_file_bittorrent(self, file_name, peers):
        """Download file from multiple peers without knowing file size."""
        chunk_size = 1024 * 1024  # 1MB
        download_directory = f"D:/shared_directories/{self.user_id}/download"
        os.makedirs(download_directory, exist_ok=True)
        download_path = os.path.join(download_directory, file_name)

        # Get file size from one of the peers
        file_size = self.get_file_size(peers[0], peers[0]["path"])
        if not file_size:
            print("Failed to retrieve file size. Aborting.")
            return
        
        # Prepare chunk download queue
        num_chunks = (file_size + chunk_size - 1) // chunk_size
        file_chunks = {}
        chunk_lock = threading.Lock()

        def worker(peer, chunk_id, chunk_start, chunk_end):
            try:
                with socket.create_connection((peer["ip"], peer["port"])) as peer_socket:
                    command = f"DOWNLOAD_CHUNK {peer['path']} {chunk_start} {chunk_end}"
                    peer_socket.sendall(command.encode())

                    data = b""
                    while True:
                        packet = peer_socket.recv(self.BUFFER_SIZE)
                        if packet == b"END_OF_CHUNK":
                            break
                        data += packet

                    with chunk_lock:
                        file_chunks[chunk_id] = data
                        print(f"Đã tải chunk {chunk_id} từ {peer['ip']}:{peer['port']}")
            except Exception as e:
                print(f"Lỗi khi tải chunk {chunk_id} từ {peer['ip']}:{peer['port']}: {e}")

        # Start threads for each peer
        threads = []
        for chunk_id in range(num_chunks):
            chunk_start = chunk_id * chunk_size
            chunk_end = min((chunk_id + 1) * chunk_size - 1, file_size - 1)

            # Lấy peer để tải chunk này
            peer = peers[chunk_id % len(peers)]  # Sử dụng vòng lặp qua các peers

            # Tạo luồng worker cho mỗi chunk
            thread = threading.Thread(target=worker, args=(peer, chunk_id, chunk_start, chunk_end))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # Combine chunks
        with open(download_path, "wb") as output_file:
            for chunk_id in sorted(file_chunks):
                output_file.write(file_chunks[chunk_id])

        print(f"File '{file_name}' downloaded successfully using BitTorrent to '{download_path}'.")

    def send_data_in_chunks(self, data, conn):
        while data:
            chunk = data[:self.BUFFER_SIZE]
            conn.sendall(chunk.encode())
            data = data[self.BUFFER_SIZE:]

def main():
    # Step 1: Obtain an IP from the DHCP server
    dhcp_client = DhcpClient()
    dhcp_client.request_ip()

    # Step 2: Connect to the file server using the obtained IP
    if dhcp_client.assigned_ip:
        client = FileClient(dhcp_client.assigned_ip)
        while True:
            print("\n1. Đăng ký tài khoản")
            print("2. Đăng nhập")
            print("3. Tạo thư mục mới")
            print("4. Liệt kê thư mục")
            print("5. Tải file từ peer")
            print("6. Thoát")
            choice = input("Chọn một tùy chọn: ")

            if choice == '1':
                username = input("Nhập tên người dùng: ")
                password = input("Nhập mật khẩu: ")
                client.register(username, password)
            elif choice == '2':
                username = input("Nhập tên người dùng: ")
                password = input("Nhập mật khẩu: ")
                client.login(username, password)
            elif choice == '3':
                directory_name = input("Nhập tên thư mục: ")
                client.create_directory(directory_name)
            elif choice == '4':
                user_id = int(input("Nhập user ID: "))
                client.list_directories(user_id)
            elif choice == '5':
                target_ip = input("Nhập địa chỉ IP của peer: ")
                target_port = int(input("Nhập cổng của peer: "))
                file_path = input("Nhập đường dẫn file cần tải: ")
                client.download_file(target_ip, target_port, file_path)
            elif choice == '6':
                break
            else:
                print("Lựa chọn không hợp lệ. Vui lòng thử lại.")

if __name__ == "__main__":
    main()