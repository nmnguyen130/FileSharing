import tkinter as tk
from tkinter import ttk, messagebox

class AuthGUI(tk.Frame):
    """Authentication GUI for Login/Register."""
    def __init__(self, master, file_client):
        super().__init__(master, bg="#f8f9fa")
        self.file_client = file_client

        tk.Label(self, text="Welcome to File Sharing", font=("Arial", 18, "bold"), bg="#f8f9fa", fg="#343a40").pack(pady=(20, 20))

        ttk.Button(self, text="Login", command=lambda: master.switch_frame(LoginPage)).pack(pady=10, ipadx=30)
        ttk.Button(self, text="Register", command=lambda: master.switch_frame(RegisterPage)).pack(pady=10, ipadx=30)

class LoginPage(tk.Frame):
    """Login Page."""
    def __init__(self, master, file_client):
        super().__init__(master, bg="#f8f9fa")
        self.file_client = file_client
        self.master = master

        # Create a container for vertical alignment
        container = tk.Frame(self, bg="#f8f9fa")
        container.pack(expand=True, fill="both")

        tk.Label(container, text="Login", font=("Arial", 24, "bold"), bg="#f8f9fa", fg="#343a40").pack(pady=20)

        tk.Label(container, text="Username", bg="#f8f9fa").pack(anchor="w", padx=50, pady=5)
        self.username_entry = ttk.Entry(container, font=("Arial", 12))
        self.username_entry.pack(fill="x", padx=50, pady=5)

        tk.Label(container, text="Password", bg="#f8f9fa").pack(anchor="w", padx=50, pady=5)
        self.password_entry = ttk.Entry(container, font=("Arial", 12), show="*")
        self.password_entry.pack(fill="x", padx=50, pady=5)

        ttk.Button(container, text="Login", command=self.login).pack(pady=20, ipadx=20)
        ttk.Button(container, text="Back", command=lambda: master.on_logout()).pack(pady=10, ipadx=20)

    def login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        if username and password:
            result = self.file_client.login(username, password)
            if result:
                messagebox.showinfo("Login", "Login Successful")
                self.master.on_authenticated()
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

        # Create a container for vertical alignment
        container = tk.Frame(self, bg="#f8f9fa")
        container.pack(expand=True, fill="both")

        tk.Label(container, text="Register", font=("Arial", 24, "bold"), bg="#f8f9fa", fg="#343a40").pack(pady=20)

        tk.Label(container, text="Username", bg="#f8f9fa").pack(anchor="w", padx=50, pady=5)
        self.username_entry = ttk.Entry(container, font=("Arial", 12))
        self.username_entry.pack(fill="x", padx=50, pady=5)

        tk.Label(container, text="Password", bg="#f8f9fa").pack(anchor="w", padx=50, pady=5)
        self.password_entry = ttk.Entry(container, font=("Arial", 12), show="*")
        self.password_entry.pack(fill="x", padx=50, pady=5)

        ttk.Button(container, text="Register", command=self.register).pack(pady=20, ipadx=20)
        ttk.Button(container, text="Back", command=lambda: master.switch_frame(AuthGUI)).pack(pady=10, ipadx=20)

    def register(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        if username and password:
            self.file_client.register(username, password)
            messagebox.showinfo("Registration", "Registration successful!")
            self.master.switch_frame(LoginPage)
        else:
            messagebox.showerror("Input Error", "Please enter both username and password.")