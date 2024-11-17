import tkinter as tk
from tkinter import ttk, messagebox
from src.dhcp.dhcp_client import DhcpClient
from src.file_sharing.file_client import FileClient

class MainApplication(tk.Tk):
    """Main Application Entry Point"""
    def __init__(self, file_client):
        super().__init__()
        self.file_client = file_client
        self.title("File Sharing Application")
        self.geometry("500x500")
        self.resizable(False, False)
        self.style = ttk.Style(self)
        self.configure_style()
        self.switch_frame(AuthGUI)

    def configure_style(self):
        """Apply styles to the application."""
        self.style.theme_use("clam")
        self.style.configure("TButton", font=("Arial", 12), padding=5)
        self.style.configure("TLabel", font=("Arial", 12))
        self.style.configure("TFrame", background="#f8f9fa")

    def switch_frame(self, frame_class):
        """Switch to a new frame."""
        new_frame = frame_class(self, self.file_client)
        if hasattr(self, "_frame"):
            self._frame.destroy()
        self._frame = new_frame
        self._frame.grid(sticky="nsew", padx=20, pady=20)


class AuthGUI(tk.Frame):
    """Authentication GUI for Login/Register."""
    def __init__(self, master, file_client):
        super().__init__(master, bg="#f8f9fa")
        self.file_client = file_client
        self.master = master
        self.grid_columnconfigure(0, weight=1)

        # Welcome Label
        tk.Label(self, text="Welcome to File Sharing", font=("Arial", 18, "bold"), bg="#f8f9fa", fg="#343a40").grid(row=0, column=0, pady=(10, 20))

        # Login Button
        login_button = ttk.Button(self, text="Login", command=lambda: master.switch_frame(LoginPage))
        login_button.grid(row=1, column=0, pady=(10, 10), ipadx=20)

        # Register Button
        register_button = ttk.Button(self, text="Register", command=lambda: master.switch_frame(RegisterPage))
        register_button.grid(row=2, column=0, pady=(10, 10), ipadx=20)


class LoginPage(tk.Frame):
    """Login Page."""
    def __init__(self, master, file_client):
        super().__init__(master, bg="#f8f9fa")
        self.file_client = file_client
        self.master = master
        self.grid_columnconfigure(1, weight=1)

        tk.Label(self, text="Login", font=("Arial", 24, "bold"), bg="#f8f9fa", fg="#343a40").grid(row=0, column=0, columnspan=2, pady=(0, 20))

        tk.Label(self, text="Username", bg="#f8f9fa").grid(row=1, column=0, sticky="w", pady=5)
        self.username_entry = ttk.Entry(self, font=("Arial", 12))
        self.username_entry.grid(row=1, column=1, pady=5)

        tk.Label(self, text="Password", bg="#f8f9fa").grid(row=2, column=0, sticky="w", pady=5)
        self.password_entry = ttk.Entry(self, font=("Arial", 12), show="*")
        self.password_entry.grid(row=2, column=1, pady=5)

        login_button = ttk.Button(self, text="Login", command=self.login)
        login_button.grid(row=3, column=0, columnspan=2, pady=15)

        back_button = ttk.Button(self, text="Back", command=lambda: master.switch_frame(AuthGUI))
        back_button.grid(row=4, column=0, columnspan=2)

    def login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        if username and password:
            if self.file_client.login(username, password):
                messagebox.showinfo("Login", "Login Successful")
                self.master.switch_frame(MainAppPage)
            else:
                messagebox.showerror("Login Error", "Login failed. Please try again.")
        else:
            messagebox.showerror("Input Error", "Please enter both username and password.")


class RegisterPage(tk.Frame):
    """Registration Page."""
    def __init__(self, master, file_client):
        super().__init__(master, bg="#f8f9fa")
        self.file_client = file_client
        self.master = master
        self.grid_columnconfigure(1, weight=1)

        tk.Label(self, text="Register", font=("Arial", 24, "bold"), bg="#f8f9fa", fg="#343a40").grid(row=0, column=0, columnspan=2, pady=(0, 20))

        tk.Label(self, text="Username", bg="#f8f9fa").grid(row=1, column=0, sticky="w", pady=5)
        self.username_entry = ttk.Entry(self, font=("Arial", 12))
        self.username_entry.grid(row=1, column=1, pady=5)

        tk.Label(self, text="Password", bg="#f8f9fa").grid(row=2, column=0, sticky="w", pady=5)
        self.password_entry = ttk.Entry(self, font=("Arial", 12), show="*")
        self.password_entry.grid(row=2, column=1, pady=5)

        register_button = ttk.Button(self, text="Register", command=self.register)
        register_button.grid(row=3, column=0, columnspan=2, pady=15)

        back_button = ttk.Button(self, text="Back", command=lambda: master.switch_frame(AuthGUI))
        back_button.grid(row=4, column=0, columnspan=2)

    def register(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        if username and password:
            self.file_client.register(username, password)
            messagebox.showinfo("Registration", "Registration successful!")
            self.master.switch_frame(LoginPage)
        else:
            messagebox.showerror("Input Error", "Please enter both username and password.")


class MainAppPage(tk.Frame):
    """Main Application Page."""
    def __init__(self, master, file_client):
        super().__init__(master, bg="#f8f9fa")
        self.file_client = file_client
        self.master = master

        tk.Label(self, text="Welcome to the File Sharing App", font=("Arial", 18, "bold"), bg="#f8f9fa", fg="#343a40").pack(pady=20)
        ttk.Button(self, text="Logout", command=lambda: master.switch_frame(AuthGUI)).pack(pady=10)


def main():
    dhcp_client = DhcpClient()
    dhcp_client.request_ip()

    if dhcp_client.assigned_ip:
        file_client = FileClient(dhcp_client.assigned_ip)
        app = MainApplication(file_client)
        app.mainloop()


if __name__ == "__main__":
    main()