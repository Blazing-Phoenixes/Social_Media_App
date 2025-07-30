import tkinter as tk
from tkinter import messagebox, filedialog
from PIL import Image, ImageTk
import re
import os

from Login_database import (
    connect_db, add_user, login_user, update_email,
    update_profile_image, validate_email, update_password
)
from home_screen import HomeScreen

connect_db()

class LoginSignupApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Login / Signup")
        self.root.configure(bg="#f0f0f0")

        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        self.root.geometry(f"{screen_width}x{screen_height}")

        # Scrollable UI with fixed-width content frame
        self.canvas = tk.Canvas(self.root, bg="#f0f0f0", highlightthickness=0)
        self.scrollbar = tk.Scrollbar(self.root, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas, bg="#f0f0f0")
        self.inner_frame = tk.Frame(self.scrollable_frame, bg="#f0f0f0", width=360)
        self.inner_frame.pack(pady=40)

        self.scrollable_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        self.is_password_shown = False
        self.create_login_ui()

    def clear_frame(self):
        for widget in self.inner_frame.winfo_children():
            widget.destroy()

    def toggle_password_visibility(self):
        if self.is_password_shown:
            self.pass_input.config(show="●")
            self.show_password_btn.config(text="Show Password")
        else:
            self.pass_input.config(show="")
            self.show_password_btn.config(text="Hide Password")
        self.is_password_shown = not self.is_password_shown

    def clear_placeholder(self, entry, placeholder, secure=False):
        if entry.get() == placeholder:
            entry.delete(0, tk.END)
            if secure:
                entry.config(show="●")

    def create_login_ui(self):
        self.clear_frame()

# Center title
        tk.Label(self.inner_frame, text="Login", font=("Arial", 26, "bold"), bg="#f0f0f0").pack(pady=30, padx=20)

# Username label aligned left
        tk.Label(self.inner_frame, text="Username or Phone", anchor="w", bg="#f0f0f0", font=("Arial", 12)).pack(fill="x", padx=40)

# Entry centered with padding
        self.user_input = tk.Entry(self.inner_frame, font=("Arial", 14), width=40)
        self.user_input.pack(pady=10, padx=40)

        tk.Label(self.inner_frame, text="Password", anchor="w", bg="#f0f0f0", font=("Arial", 12)).pack(fill="x", padx=40)
        self.pass_input = tk.Entry(self.inner_frame, font=("Arial", 14), show="●", width=40)
        self.pass_input.pack(pady=5)

        self.show_password_btn = tk.Button(self.inner_frame, text="Show Password", command=self.toggle_password_visibility)
        self.show_password_btn.pack(pady=40, padx=20)

        tk.Button(self.inner_frame, text="Login", width=20, command=self.login,
                  bg="#4CAF50", fg="white", font=("Arial", 14)).pack(pady=30, padx=10)

        tk.Button(self.inner_frame, text="Forgot Password?", command=self.forgot_password_ui,
                  fg="blue", bg="#f0f0f0", borderwidth=0).pack(pady=5)

        tk.Button(self.inner_frame, text="Don't have an account? Signup",
                  command=self.create_signup_ui, fg="blue", bg="#f0f0f0", borderwidth=0).pack()

        tk.Button(self.inner_frame, text="Exit", command=self.root.quit,
                  bg="red", fg="white", font=("Arial", 12, "bold")).pack(pady=30)

    def create_signup_ui(self):
        self.clear_frame()
        tk.Label(self.inner_frame, text="Signup", font=("Arial", 26, "bold"), bg="#f0f0f0").pack(pady=20)

        def add_entry(label_text, varname, placeholder="", secure=False):
            tk.Label(self.inner_frame, text=label_text, anchor="w", bg="#f0f0f0", font=("Arial", 12)).pack(fill=None)
            e = tk.Entry(self.inner_frame, font=("Arial", 14), width=40)
            e.pack(pady=5)
            if placeholder:
                e.insert(0, placeholder)
            if secure:
                e.config(show="●")
            setattr(self, varname, e)

        add_entry("Username", "signup_user")
        add_entry("Phone Number", "signup_phone")
        add_entry("Email (optional)", "signup_email")
        add_entry("Password", "signup_pass", secure=True)

        # Profile image
        self.profile_image_path = None
        self.profile_image_preview = tk.Label(self.inner_frame, bg="#f0f0f0")
        self.profile_image_preview.pack(pady=5)

        tk.Button(self.inner_frame, text="Choose Profile Image", command=self.choose_profile_image,
                  bg="#607D8B", fg="white", font=("Arial", 12)).pack(pady=10)

        tk.Button(self.inner_frame, text="Signup", width=30, command=self.signup,
                  bg="#2196F3", fg="white", font=("Arial", 14)).pack(pady=15)

        tk.Button(self.inner_frame, text="Already have an account? Login",
                  command=self.create_login_ui, fg="blue", bg="#f0f0f0", borderwidth=0).pack()

        tk.Button(self.inner_frame, text="Exit", command=self.root.quit,
                  bg="red", fg="white", font=("Arial", 12, "bold")).pack(pady=30)

    def choose_profile_image(self):
        file_path = filedialog.askopenfilename(filetypes=[("Image files", "*.png *.jpg *.jpeg *.gif")])
        if file_path:
            self.profile_image_path = file_path
            try:
                img = Image.open(file_path).resize((80, 80))
                img_tk = ImageTk.PhotoImage(img)
                self.profile_image_preview.configure(image=img_tk)
                self.profile_image_preview.image = img_tk
            except Exception:
                messagebox.showerror("Error", "Failed to load image.")

    def login(self):
        user = self.user_input.get().strip()
        pwd = self.pass_input.get().strip()

        if login_user(user, pwd):
            self.root.destroy()
            HomeScreen(user)
        else:
            messagebox.showerror("Error", "Invalid credentials!")

    def signup(self):
        user = self.signup_user.get().strip()
        phone = self.signup_phone.get().strip()
        email = self.signup_email.get().strip()
        pwd = self.signup_pass.get().strip()

        if not re.fullmatch(r'[A-Za-z0-9_]+', user):
            messagebox.showerror("Invalid Username", "Username must only contain letters, numbers, and underscores.")
            return

        if not phone.isdigit() or len(phone) != 10:
            messagebox.showerror("Invalid Phone", "Phone number must be exactly 10 digits.")
            return

        if email and not validate_email(email):
            messagebox.showerror("Invalid Email", "Please enter a valid email address.")
            return

        if not re.fullmatch(r'(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*(),.?":{}|<>]).{8,}', pwd):
            messagebox.showerror("Invalid Password", "Password must have at least 8 characters with upper, lower, digit, and special character.")
            return

        msg = add_user(user, phone, pwd)
        if "success" in msg.lower():
            if email:
                update_email(user, email)
            if self.profile_image_path:
                update_profile_image(user, self.profile_image_path)

            messagebox.showinfo("Success", msg)
            self.create_login_ui()
        else:
            messagebox.showerror("Error", msg)

    def forgot_password_ui(self):
        self.clear_frame()
        tk.Label(self.inner_frame, text="Reset Password", font=("Arial", 24, "bold"), bg="#f0f0f0").pack(pady=30)

        tk.Label(self.inner_frame, text="Username or Phone", anchor="w", bg="#f0f0f0", font=("Arial", 12)).pack(fill=None)
        self.reset_user_input = tk.Entry(self.inner_frame, font=("Arial", 14), width=40)
        self.reset_user_input.pack(pady=10)

        tk.Label(self.inner_frame, text="New Password", anchor="w", bg="#f0f0f0", font=("Arial", 12)).pack(fill=None)
        self.new_pass_input = tk.Entry(self.inner_frame, font=("Arial", 14), show="●", width=40)
        self.new_pass_input.pack(pady=10)

        tk.Button(self.inner_frame, text="Submit", width=30, command=self.reset_password,
                  bg="#4CAF50", fg="white", font=("Arial", 14)).pack(pady=25)

        tk.Button(self.inner_frame, text="Back to Login", command=self.create_login_ui,
                  fg="blue", bg="#f0f0f0", borderwidth=0).pack(pady=10)

    def reset_password(self):
        identifier = self.reset_user_input.get().strip()
        new_pwd = self.new_pass_input.get().strip()

        if not identifier:
            messagebox.showerror("Error", "Please enter your username or phone number.")
            return

        if not re.fullmatch(r'(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*(),.?":{}|<>]).{8,}', new_pwd):
            messagebox.showerror("Invalid Password", "Password must contain uppercase, lowercase, digit, and special character (min 8 chars).")
            return

        result = update_password(identifier, new_pwd)
        if "success" in result.lower():
            messagebox.showinfo("Success", "Password reset successfully. You can now login.")
            self.create_login_ui()
        else:
            messagebox.showerror("Error", result)


if __name__ == "__main__":
    root = tk.Tk()
    app = LoginSignupApp(root)
    root.mainloop()