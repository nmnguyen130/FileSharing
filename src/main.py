import threading
from src.dhcp.dhcp_server import DhcpServer
from src.file_sharing.file_server import FileServer

def start_dhcp_server_thread():
    dhcp_server = DhcpServer()
    dhcp_server.start_dhcp_server()

def start_file_server_thread():
    file_server = FileServer()
    file_server.start_file_server()

if __name__ == "__main__":
    dhcp_thread = threading.Thread(target=start_dhcp_server_thread)
    file_server_thread = threading.Thread(target=start_file_server_thread)

    dhcp_thread.start()
    file_server_thread.start()

    dhcp_thread.join()
    file_server_thread.join() 