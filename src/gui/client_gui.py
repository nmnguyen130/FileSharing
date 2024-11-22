import tkinter as tk
from tkinter import ttk
from src.gui.main_app_page import MainAppPage
from src.gui.auth_gui import AuthGUI
from src.dhcp.dhcp_client import DhcpClient
from src.file_sharing.file_client import FileClient

class MainApplication(tk.Tk):
    """Main Application Entry Point"""
    def __init__(self, file_client):
        super().__init__()
        self.file_client = file_client
        self.title("File Sharing Application")
        self.geometry("500x400")
        self.resizable(False, False)
        self.style = ttk.Style(self)
        self.configure_styles(self.style)
        self.switch_frame(AuthGUI)

    def configure_styles(self, style):
        """Apply styles to the application."""
        style.theme_use("clam")  # Change to a modern theme
        style.configure("TButton", font=("Arial", 12), padding=5, background="#007BFF", foreground="white")
        style.map("TButton", background=[("active", "#0056b3")])
        style.configure("TLabel", font=("Arial", 12), background="#f8f9fa")
        style.configure("TFrame", background="#f8f9fa")

    def on_authenticated(self):
        self.switch_frame(MainAppPage)

    def on_logout(self):
        self.switch_frame(AuthGUI)

    def switch_frame(self, frame_class, **kwargs):
        """Switch to a new frame."""
        new_frame = frame_class(self, self.file_client, **kwargs)
        if hasattr(self, "_frame"):
            self._frame.destroy()
        self._frame = new_frame
        container = tk.Frame(self, bg="#f8f9fa")
        container.place(relx=0.5, rely=0.5, anchor="center")  # Center in the window

        # Make sure child frame fills the container
        new_frame.pack(expand=True, fill="both")

def main():
    dhcp_client = DhcpClient()
    dhcp_client.request_ip()

    if dhcp_client.assigned_ip:
        file_client = FileClient(dhcp_client.assigned_ip)
        app = MainApplication(file_client)
        app.mainloop()


if __name__ == "__main__":
    main()