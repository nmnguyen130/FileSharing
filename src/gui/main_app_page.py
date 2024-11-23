import os
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog

class MainAppPage(tk.Frame):
    """Main Application Page."""
    def __init__(self, master, file_client):
        super().__init__(master, bg="#f8f9fa")
        self.file_client = file_client
        self.master = master
        self.current_path = "/"  # Root directory by default
        self.build_ui()

    def build_ui(self):
        """Build the main UI for the application."""
        # Header Section
        header_frame = tk.Frame(self, bg="#343a40", height=50)
        header_frame.pack(fill="x")

        tk.Label(
            header_frame,
            text="File Sharing Application",
            font=("Arial", 18, "bold"),
            bg="#343a40",
            fg="white"
        ).pack(side="left", padx=20, pady=10)

        ttk.Button(
            header_frame,
            text="Logout",
            command=lambda: self.master.on_logout(),
            style="Logout.TButton"
        ).pack(side="right", padx=20, pady=10)

        # Info Section
        info_frame = tk.Frame(self, bg="#f8f9fa", bd=1, relief="solid")
        info_frame.pack(fill="x", padx=10, pady=5)

        tk.Label(info_frame, text="Client Info:", font=("Arial", 12, "bold"), bg="#f8f9fa").pack(anchor="w", padx=5, pady=5)
        tk.Label(info_frame, text=f"IP Address: {self.file_client.local_ip}", bg="#f8f9fa").pack(anchor="w", padx=15)
        tk.Label(info_frame, text=f"Connected to: {self.file_client.server_ip}", bg="#f8f9fa").pack(anchor="w", padx=15)

        create_folder_button = ttk.Button(
            info_frame,
            text="Create Folder",
            command=self.create_folder
        )
        create_folder_button.pack(anchor="e", padx=10, pady=5)

        # Directory Explorer Section
        explorer_frame = tk.Frame(self, bg="#f8f9fa")
        explorer_frame.pack(expand=True, fill="both", padx=10, pady=10)

        # Path Display
        path_frame = tk.Frame(explorer_frame, bg="#e9ecef", bd=1, relief="solid")
        path_frame.pack(fill="x", pady=5)
        self.path_label = tk.Label(
            path_frame,
            text=f"Path: {self.current_path}",
            font=("Arial", 12, "italic"),
            bg="#e9ecef",
            fg="#343a40"
        )
        self.path_label.pack(anchor="w", padx=10, pady=5)

        # Directory Content Display
        content_frame = tk.Frame(explorer_frame, bg="#f8f9fa")
        content_frame.pack(expand=True, fill="both")

        self.treeview = ttk.Treeview(content_frame, show="tree")
        self.treeview.pack(expand=True, fill="both", pady=5)

        # Define Treeview style
        style = ttk.Style()
        style.configure(
            "Treeview",
            font=("Arial", 12),
            rowheight=30,
            background="#ffffff",
            fieldbackground="#ffffff",
        )
        style.configure("Treeview.Heading", font=("Arial", 12, "bold"))

        self.treeview.bind("<Double-1>", self.on_treeview_click)

        # Control Buttons
        button_frame = tk.Frame(explorer_frame, bg="#f8f9fa")
        button_frame.pack(fill="x", pady=10)

        ttk.Button(button_frame, text="Back", command=self.go_back).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Refresh", command=self.refresh_directory).pack(side="right", padx=5)

        # Load initial directory
        self.refresh_directory()

    def create_folder(self):
        """Create a new folder in the current directory."""
        folder_name = simpledialog.askstring("Create Folder", "Enter folder name:")
        if folder_name:
            try:
                # Use the file_client's create_directory method to create the folder
                success = self.file_client.create_directory(folder_name)
                if success:
                    messagebox.showinfo("Success", f"Folder '{folder_name}' created!")
                    self.refresh_directory()  # Refresh the directory to show the new folder
                else:
                    messagebox.showerror("Error", "Failed to create folder.")
            except Exception as e:
                messagebox.showerror("Error", f"Error creating folder: {e}")
        else:
            messagebox.showwarning("Cancelled", "Folder creation cancelled.")

    def refresh_directory(self):
        """Fetch and display the list of directories and files shared by users."""
        self.treeview.delete(*self.treeview.get_children())  # Clear existing items

        # Get active directories shared by users
        self.active_dirs = self.file_client.get_active_directories()  # Fetch directories

        if self.active_dirs:
            for user in self.active_dirs:
                user_id = user['user_id']
                if user_id != self.file_client.user_id:
                    directories = user['directories']

                    # Insert user_id as a root node
                    user_node = self.treeview.insert("", "end", user_id, text=f"User {user_id}", tags=("user",))

                    for directory in directories:
                        # Insert directory names under the user node with the path as a hidden value
                        directory_node = self.treeview.insert(
                            user_node,
                            "end",
                            f"{user_id}_{directory['name']}",  # Use directory name as the item ID for simplicity
                            text=directory['name'],  # Display the name in the tree view
                            values=(user['ip'], user['port'], directory['path']),  # Store the hidden path in 'values'
                            tags=("directory",)
                        )
                        # Insert a placeholder for files to be fetched when the directory is clicked
                        self.treeview.insert(directory_node, "end", text="...", tags=("loading",))  # Placeholder for files

        self.treeview.tag_configure("user", foreground="#007BFF")  # Style for user nodes
        self.treeview.tag_configure("directory", foreground="#6c757d")  # Style for directories

    def on_treeview_click(self, event):
        """Handle treeview item double-click."""
        selected_item = self.treeview.selection()
        if selected_item:
            item = self.treeview.item(selected_item[0])
            selected_name = item["text"]
            hidden_values = item["values"]

            if hidden_values:
                target_ip, target_port, path = hidden_values
                if item['tags'][0] == 'directory':  # Check if it's a directory
                    self.refresh_directory_contents(selected_item[0], target_ip, target_port, path)
                elif item['tags'][0] == 'file':  # Check if it's a file
                    self.download_file(target_ip, target_port, path)

    def refresh_directory_contents(self, parent_item, target_ip, target_port, directory_path):
        """Fetch and display contents of a directory."""
        # Clear existing placeholders
        for child in self.treeview.get_children(parent_item):
            if self.treeview.item(child)["tags"][0] == "loading":
                self.treeview.delete(child)

        # Get the files in the directory
        files = self.file_client.list_file_in_directory(target_ip, target_port, directory_path)
        if files:
            for file in files:
                self.treeview.insert(
                    parent_item,
                    "end",
                    file['name'],  # Display file name
                    text=file['name'],
                    values=(target_ip, target_port, file['path']),  # Store file path in 'values'
                    tags=("file",)  # Tag the item as a file
                )

    def download_file(self, target_ip, target_port, file_path):
        """Download the selected file from the peer."""
        try:
            file_name = os.path.basename(file_path)
            download_directory = f"D:/shared_directories/{self.file_client.user_id}/download"
            download_path = os.path.join(download_directory, file_name)

            peers = self.file_client.search_file_across_peers(file_name)

            if len(peers) > 1:
                response = messagebox.askyesno("BitTorrent Download", f"File '{file_name}' found on {len(peers)} peers. Do you want to download using BitTorrent?")
                if response:
                    self.file_client.download_file_bittorrent(file_name, peers)
                    return

            self.file_client.download_file(target_ip, target_port, file_path)

            # Confirm success
            messagebox.showinfo("Download Complete", f"File '{file_name}' has been downloaded to '{download_path}'")

        except Exception as e:
            messagebox.showerror("Error", f"Error downloading file: {e}")

    def go_back(self):
        """Navigate back to the parent directory."""
        if self.current_path != "/":
            self.current_path = os.path.dirname(self.current_path.rstrip("/"))
            self.refresh_directory()
