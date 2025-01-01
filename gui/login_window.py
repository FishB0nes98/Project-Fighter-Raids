import tkinter as tk
from tkinter import ttk, messagebox
from config.login_config import LoginManager

class LoginWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        
        self.login_manager = LoginManager()
        self.title("Project Fighter - Login")
        self.geometry("300x200")
        self.resizable(False, False)
        
        # Center window
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width - 300) // 2
        y = (screen_height - 200) // 2
        self.geometry(f"300x200+{x}+{y}")
        
        self.create_widgets()
        self.try_auto_login()
    
    def create_widgets(self):
        # Main frame
        main_frame = ttk.Frame(self, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Username
        ttk.Label(main_frame, text="Username:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.username_var = tk.StringVar()
        self.username_entry = ttk.Entry(main_frame, textvariable=self.username_var)
        self.username_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=5)
        
        # Password
        ttk.Label(main_frame, text="Password:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.password_var = tk.StringVar()
        self.password_entry = ttk.Entry(main_frame, textvariable=self.password_var, show="*")
        self.password_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5)
        
        # Remember me checkbox
        self.remember_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(main_frame, text="Remember me", variable=self.remember_var).grid(
            row=2, column=0, columnspan=2, pady=10
        )
        
        # Login button
        ttk.Button(main_frame, text="Login", command=self.login).grid(
            row=3, column=0, columnspan=2, pady=10
        )
        
        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        main_frame.grid_columnconfigure(1, weight=1)
    
    def try_auto_login(self):
        credentials = self.login_manager.load_credentials()
        if credentials:
            username, stored_hash = credentials
            self.username_var.set(username)
            self.password_entry.focus()
    
    def login(self):
        username = self.username_var.get().strip()
        password = self.password_var.get().strip()
        
        if not username or not password:
            messagebox.showerror("Error", "Please enter both username and password")
            return
        
        # For demo purposes, accept any non-empty credentials
        # In a real application, you would validate against a server
        
        if self.remember_var.get():
            self.login_manager.save_credentials(username, password)
        
        self.destroy()  # Close login window
        
    def run(self) -> tuple[str, str]:
        self.mainloop()
        return self.username_var.get(), self.password_var.get() 