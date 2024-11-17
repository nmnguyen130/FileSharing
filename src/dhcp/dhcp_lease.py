import time

class DhcpLease:
    def __init__(self, ip, lease_time):
        self.ip = ip
        self.start_time = time.time()
        self.lease_time = lease_time

    def is_expired(self):
        """Check if the lease has expired."""
        return time.time() > self.start_time + self.lease_time

    def renew(self, additional_time):
        """Extend the lease time."""
        self.lease_time += additional_time
        print(f"[INFO] Lease for IP {self.ip} has been extended by {additional_time} seconds.")