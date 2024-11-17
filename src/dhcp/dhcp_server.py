import json
import socket

from src.dhcp.dhcp_lease import DhcpLease

class DhcpServer:
    # DHCP Server configurations
    DHCP_SERVER_IP = '192.168.1.1'
    DHCP_POOL_START = '192.168.1.100'
    DHCP_POOL_END = '192.168.1.200'
    SUBNET_MASK = '255.255.255.0'
    GATEWAY = '192.168.1.1'
    SERVER_PORT = 67
    BUFFER_SIZE = 1024
    LEASE_TIME = 3600  # Lease time in seconds (1 hour)

    def __init__(self, ip_range_start=DHCP_POOL_START, ip_range_end=DHCP_POOL_END):
        self.ip_range_start = ip_range_start
        self.ip_range_end = ip_range_end
        self.leases = {}

    def allocate_ip(self, client_mac):
        """Allocate an IP address to a client"""
        start_int = int(self.ip_range_start.split('.')[-1])
        end_int = int(self.ip_range_end.split('.')[-1])
        
        # Generate available IPs within the pool range
        available_ips = [
            f'192.168.1.{i}' for i in range(start_int, end_int + 1)
            if f'192.168.1.{i}' not in self.leases.values()
        ]
        
        if available_ips:
            allocated_ip = available_ips[0]
            self.leases[client_mac] = DhcpLease(allocated_ip, self.LEASE_TIME)
            return allocated_ip
        return None
    
    def handle_dhcp_discover(self, client_mac):
        allocated_ip = self.allocate_ip(client_mac)

        if not allocated_ip:
            print("No IP addresses available.")
            return None

        return self.create_dhcp_offer(allocated_ip)
    
    def create_dhcp_offer(self, allocated_ip):
        """Create a DHCP Offer message."""
        offer_message = {
            "op": 2,  # DHCP Offer
            "yiaddr": allocated_ip,
            "siaddr": self.DHCP_SERVER_IP,
            "giaddr": self.GATEWAY,
            "subnet_mask": self.SUBNET_MASK,
            "lease_time": self.LEASE_TIME
        }
        return json.dumps(offer_message)

    def start_dhcp_server(self):
        """Start the DHCP server to listen for requests."""
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as dhcp_socket:
            dhcp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            dhcp_socket.bind(('0.0.0.0', self.SERVER_PORT))
            print("DHCP Server is running...")

            while True:
                try:
                    packet, client_address = dhcp_socket.recvfrom(self.BUFFER_SIZE)
                    message = json.loads(packet.decode())
                    client_mac = message.get("chaddr", "")

                    if message.get("op") == 1:  # DHCPDISCOVER
                        response = self.handle_dhcp_discover(client_mac)
                        if response:
                            dhcp_socket.sendto(response.encode(), client_address)
                except Exception as e:
                    print(f"An error occurred: {e}")
                    continue

if __name__ == "__main__":
    dhcp_server = DhcpServer()
    dhcp_server.start_dhcp_server()