import json
import random
import socket

class DhcpClient:
    # DHCP Client configurations
    SERVER_PORT = 67
    CLIENT_PORT = 68
    BUFFER_SIZE = 1024

    def __init__(self):
        self.client_mac = self.generate_mac_address()
        self.assigned_ip = None

    def generate_mac_address(self):
        """Generate a random MAC address."""
        mac = [0x00, 0x0c, 0x29, random.randint(0x00, 0x7f), random.randint(0x00, 0x7f), random.randint(0x00, 0x7f)]
        return ':'.join(map(lambda x: format(x, '02x'), mac))
    
    def create_discover_message(self):
        """Create DHCPDISCOVER message to send to server."""
        discover_message = {
            "op": 1,  # DHCP Discover
            "chaddr": self.client_mac
        }
        return json.dumps(discover_message)

    def request_ip(self):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.bind(('', self.CLIENT_PORT))
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

            discover_message = self.create_discover_message()
            sock.sendto(discover_message.encode(), ('<broadcast>', self.SERVER_PORT))

            # Listen for DHCP OFFER from the server
            data, _ = sock.recvfrom(self.BUFFER_SIZE)
            offer_message = json.loads(data.decode())

            if offer_message.get("op") == 2:  # DHCP Offer
                self.assigned_ip = offer_message.get("yiaddr")
                print(f"Assigned IP: {self.assigned_ip}")
            else:
                print("No DHCP offer received.")