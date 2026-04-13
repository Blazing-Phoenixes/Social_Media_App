import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk
import re

from Login_database import (
    connect_db, add_user, login_user, update_email,
    update_profile_image, validate_email, update_password
)

connect_db()

# ---------------- COLORS ----------------
BACKGROUND = "#0f172a"
CARD = "#1e293b"
INPUT = "#334155"
BUTTON = "#6366f1"
HOVER = "#4f46e5"
TEXT = "#e2e8f0"
SUBTEXT = "#94a3b8"
SUCCESS = "#22c55e"
ERROR = "#ef4444"

# ---------------- FONTS ----------------
TITLE_FONT = ("Segoe UI", 26, "bold")
LABEL_FONT = ("Segoe UI", 10)
ENTRY_FONT = ("Segoe UI", 12)
BTN_FONT = ("Segoe UI", 11, "bold")


class LoginSignupApp(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=BACKGROUND)
        self.app = app

        self.is_password_shown = False
        self.profile_image_path = None

        # FULL SCREEN RESPONSIVE CENTERING
        self.pack(fill="both", expand=True)

        self.container = tk.Frame(self, bg=BACKGROUND)
        self.container.place(relx=0.5, rely=0.5, anchor="center")

        self.card = tk.Frame(self.container, bg=CARD)
        self.card.pack()

        self.create_login_ui()

    # ---------------- TOAST ----------------
    def show_toast(self, message, color=SUCCESS):
        toast = tk.Label(self, text=message,
                         bg=color, fg="white",
                         font=("Segoe UI", 10, "bold"),
                         padx=20, pady=10)

        toast.place(relx=0.5, rely=0.9, anchor="center")

        self.after(2000, toast.destroy)

    # ---------------- CLEAR FIELDS ----------------
    def clear_fields(self):
        for widget in self.card.winfo_children():
            if isinstance(widget, tk.Entry):
                widget.delete(0, tk.END)

    def clear_card(self):
        for widget in self.card.winfo_children():
            widget.destroy()

    # ---------------- ENTRY ----------------
    def create_entry(self, label, varname, show=None):
        tk.Label(self.card, text=label, fg=SUBTEXT, bg=CARD,
                 font=LABEL_FONT).pack(anchor="w", padx=40, pady=(10, 2))

        entry = tk.Entry(self.card, bg=INPUT, fg=TEXT,
                         insertbackground="white",
                         relief="flat", font=ENTRY_FONT,
                         width=30)
        entry.pack(ipady=8, padx=40)

        if show:
            entry.config(show=show)

        setattr(self, varname, entry)

    # ---------------- BUTTON ----------------
    def create_button(self, text, command):
        btn = tk.Label(self.card, text=text,
                       bg=BUTTON, fg="white",
                       font=BTN_FONT,
                       padx=10, pady=8,
                       cursor="hand2")

        btn.pack(pady=10, padx=40, fill="x")

        def on_enter(e): btn.config(bg=HOVER)
        def on_leave(e): btn.config(bg=BUTTON)

        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)
        btn.bind("<Button-1>", lambda e: command())

    # ---------------- LINK ----------------
    def create_link(self, text, command):
        link = tk.Label(self.card, text=text,
                        fg="#60a5fa", bg=CARD,
                        cursor="hand2")
        link.pack(pady=4)
        link.bind("<Button-1>", lambda e: command())

    # ---------------- PASSWORD TOGGLE ----------------
    def toggle_password_visibility(self):
        if self.is_password_shown:
            self.pass_input.config(show="●")
            self.show_password_btn.config(text="Show Password")
        else:
            self.pass_input.config(show="")
            self.show_password_btn.config(text="Hide Password")

        self.is_password_shown = not self.is_password_shown

    # ---------------- LOGIN UI ----------------
    def create_login_ui(self):
        self.clear_card()

        tk.Label(self.card, text="Welcome Back",
                 bg=CARD, fg=TEXT, font=TITLE_FONT).pack(pady=20)

        self.create_entry("Username or Phone", "user_input")
        self.create_entry("Password", "pass_input", show="●")

        self.show_password_btn = tk.Label(
            self.card,
            text="Show Password",
            bg=CARD, fg=SUBTEXT,
            cursor="hand2"
        )
        self.show_password_btn.pack(pady=5)
        self.show_password_btn.bind("<Button-1>", lambda e: self.toggle_password_visibility())

        self.create_button("Login", self.login)

        self.create_link("Forgot Password?", self.forgot_password_ui)
        self.create_link("Don't have an account? Signup", self.create_signup_ui)

    # ---------------- SIGNUP UI ----------------
    def create_signup_ui(self):
        self.clear_card()

        tk.Label(self.card, text="Create Account",
                 bg=CARD, fg=TEXT, font=TITLE_FONT).pack(pady=20)

        self.create_entry("Username", "signup_user")
        self.create_entry("Phone Number", "signup_phone")
        self.create_entry("Email (optional)", "signup_email")
        self.create_entry("Password", "signup_pass", show="●")

        self.profile_image_preview = tk.Label(self.card, bg=CARD)
        self.profile_image_preview.pack(pady=10)

        tk.Label(self.card, text="Choose Profile Image",
                 bg="#475569", fg="white",
                 padx=10, pady=6,
                 cursor="hand2").pack(pady=5)

        self.card.winfo_children()[-1].bind("<Button-1>", lambda e: self.choose_profile_image())

        self.create_button("Signup", self.signup)

        self.create_link("Back to Login", self.create_login_ui)

    # ---------------- IMAGE ----------------
    def choose_profile_image(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("Image files", "*.png *.jpg *.jpeg")]
        )
        if file_path:
            self.profile_image_path = file_path
            try:
                img = Image.open(file_path).resize((80, 80))
                img_tk = ImageTk.PhotoImage(img)
                self.profile_image_preview.configure(image=img_tk)
                self.profile_image_preview.image = img_tk
            except tk.TclError:
                self.show_toast("Image load failed", ERROR)

    # ---------------- LOGIN ----------------
    def login(self):
        user = self.user_input.get()
        pwd = self.pass_input.get()

        if login_user(user, pwd):
            self.app.current_user = user
            self.clear_fields()
            self.show_toast("Login successful", SUCCESS)
            self.app.show_frame("HomeFrame", user=user)
        else:
            self.show_toast("Invalid credentials", ERROR)
            self.clear_fields()

    # ---------------- SIGNUP ----------------
    def signup(self):
        user = self.signup_user.get().strip()
        phone = self.signup_phone.get().strip()
        email = self.signup_email.get().strip()
        pwd = self.signup_pass.get().strip()

        if not re.fullmatch(r'[A-Za-z0-9_]+', user):
            self.show_toast("Invalid username", ERROR)
            return

        if not phone.isdigit() or len(phone) != 10:
            self.show_toast("Invalid phone number", ERROR)
            return

        if email and not validate_email(email):
            self.show_toast("Invalid email", ERROR)
            return

        if not re.fullmatch(r'(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*]).{8,}', pwd):
            self.show_toast("Weak password", ERROR)
            return

        msg = add_user(user, phone, pwd)

        if "success" in msg.lower():
            if email:
                update_email(user, email)
            if self.profile_image_path:
                update_profile_image(user, self.profile_image_path)

            self.show_toast("Signup successful", SUCCESS)
            self.clear_fields()
            self.create_login_ui()
        else:
            self.show_toast(msg, ERROR)

    # ---------------- RESET UI ----------------
    def forgot_password_ui(self):
        self.clear_card()

        tk.Label(self.card, text="Reset Password",
                 bg=CARD, fg=TEXT, font=TITLE_FONT).pack(pady=20)

        self.create_entry("Username or Phone", "reset_user_input")
        self.create_entry("New Password", "new_pass_input", show="●")

        self.create_button("Submit", self.reset_password)
        self.create_link("Back to Login", self.create_login_ui)

    # ---------------- RESET ----------------
    def reset_password(self):
        identifier = self.reset_user_input.get()
        new_pwd = self.new_pass_input.get()

        if not identifier:
            self.show_toast("Enter username/phone", ERROR)
            return

        result = update_password(identifier, new_pwd)

        if "success" in result.lower():
            self.show_toast("Password updated", SUCCESS)
            self.clear_fields()
            self.create_login_ui()
        else:
            self.show_toast(result, ERROR)