import tkinter as tk
from tkinter import messagebox, filedialog
from PIL import Image, ImageTk
import os
import re
from pathlib import Path
from Login_database import (
    get_user_details, update_password, verify_password,
    update_email, update_profile_image, get_profile_image_path,
    delete_user
)

LANGUAGES = {
    "en": {
        "title": "Settings",
        "username": "Username",
        "phone": "Phone",
        "email": "Email ID",
        "update_email": "Update Email",
        "change_pwd": "Change Password",
        "old_pwd": "Old Password",
        "new_pwd": "New Password",
        "update_pwd": "Update Password",
        "close": "Close",
        "upload_pic": "Upload Profile Picture",
        "language": "Language: English",
        "toggle_dark": "Toggle Dark Mode",
        "strength": "Strength",
        "delete_acc": "Delete Account",
        "back": "Back"
    },
    "ta": {
        "title": "அமைப்புகள்",
        "username": "பயனர் பெயர்",
        "phone": "தொலைபேசி",
        "email": "மின்னஞ்சல்",
        "update_email": "மின்னஞ்சலை புதுப்பிக்கவும்",
        "change_pwd": "கடவுச்சொல்லை மாற்று",
        "old_pwd": "பழைய கடவுச்சொல்",
        "new_pwd": "புதிய கடவுச்சொல்",
        "update_pwd": "புதுப்பி",
        "close": "மூடு",
        "upload_pic": "புகைப்படத்தை பதிவேற்று",
        "language": "மொழி: தமிழ்",
        "toggle_dark": "இருண்ட நிலையை மாற்று",
        "strength": "வலிமை",
        "delete_acc": "கணக்கை நீக்கு",
        "back": "பின்வாங்கு"
    }
}

class ProfileScreen:
    def __init__(self, identifier):
        self.identifier = identifier
        self.dark_mode = False
        self.lang = "en"

        self.root = tk.Toplevel()
        self.root.title("Settings")
        self.root.geometry("450x650")
        self.root.resizable(True, True)

        self.container = tk.Frame(self.root, padx=10, pady=10)
        self.container.pack(expand=True, fill=tk.BOTH)

        self.theme_btn = tk.Button(self.container, command=self.toggle_theme)
        self.theme_btn.pack(anchor="ne", padx=5, pady=5)

        self.lang_btn = tk.Button(self.container, command=self.switch_language)
        self.lang_btn.pack(anchor="ne", padx=5)

        self.title_label = tk.Label(self.container, font=("Arial", 16, "bold"))
        self.title_label.pack(pady=10)

        user = get_user_details(identifier)
        if not user:
            tk.Label(self.container, text="User not found.", fg="red").pack()
            return

        self.username, self.phone, self.email, _ = user
        self.profile_pic_path = get_profile_image_path(self.identifier)
        if not self.profile_pic_path or not os.path.exists(self.profile_pic_path):
            self.profile_pic_path = f"profile_pics/{self.username}.png"

        self.profile_img = None
        self.pic_label = tk.Label(self.container)
        self.pic_label.pack()
        self.load_profile_image()

        self.upload_btn = tk.Button(self.container, command=self.upload_picture)
        self.upload_btn.pack(pady=5)

        self.info_labels = [
            tk.Label(self.container, font=("Arial", 12)),
            tk.Label(self.container, font=("Arial", 12))
        ]
        for label in self.info_labels:
            label.pack(pady=3)

        self.email_label = tk.Label(self.container)
        self.email_label.pack(pady=(15, 0))
        self.email_entry = tk.Entry(self.container, width=30)
        self.email_entry.insert(0, self.email or "")
        self.email_entry.pack()
        self.email_btn = tk.Button(self.container, command=self.update_email_func)
        self.email_btn.pack(pady=5)

        self.pass_section = tk.Label(self.container, font=("Arial", 14, "bold"))
        self.pass_section.pack(pady=15)

        self.old_label = tk.Label(self.container)
        self.old_label.pack()
        self.old_entry = tk.Entry(self.container, show="*", width=30)
        self.old_entry.pack()

        self.new_label = tk.Label(self.container)
        self.new_label.pack()
        self.new_entry = tk.Entry(self.container, show="*", width=30)
        self.new_entry.pack()
        self.new_entry.bind("<KeyRelease>", self.check_strength)

        self.strength_label = tk.Label(self.container)
        self.strength_label.pack()

        self.update_pass_btn = tk.Button(self.container, command=self.change_password)
        self.update_pass_btn.pack(pady=10)

        self.delete_btn = tk.Button(self.container, fg="red", command=self.delete_account)
        self.delete_btn.pack(pady=10)

        self.close_btn = tk.Button(self.container, command=self.root.destroy)
        self.close_btn.pack(pady=5)

        self.apply_language()
        self.apply_theme()

    def toggle_theme(self):
        self.dark_mode = not self.dark_mode
        self.apply_theme()

    def apply_theme(self):
        bg = "#121212" if self.dark_mode else "#ffffff"
        fg = "#ffffff" if self.dark_mode else "#000000"
        self.root.configure(bg=bg)
        self.container.configure(bg=bg)
        for widget in self.container.winfo_children():
            try:
                widget.configure(bg=bg, fg=fg)
            except:
                pass
        self.strength_label.configure(bg=bg)

    def switch_language(self):
        self.lang = "ta" if self.lang == "en" else "en"
        self.apply_language()

    def apply_language(self):
        t = LANGUAGES[self.lang]
        self.title_label.config(text=t["title"])
        self.info_labels[0].config(text=f"{t['username']}: {self.username}")
        self.info_labels[1].config(text=f"{t['phone']}: {self.phone}")
        self.email_label.config(text=t["email"])
        self.email_btn.config(text=t["update_email"])
        self.pass_section.config(text=t["change_pwd"])
        self.old_label.config(text=t["old_pwd"])
        self.new_label.config(text=t["new_pwd"])
        self.update_pass_btn.config(text=t["update_pwd"])
        self.close_btn.config(text=t["back"])
        self.upload_btn.config(text=t["upload_pic"])
        self.theme_btn.config(text=t["toggle_dark"])
        self.lang_btn.config(text=t["language"])
        self.delete_btn.config(text=t["delete_acc"])

    def load_profile_image(self):
        try:
            if os.path.exists(self.profile_pic_path):
                img = Image.open(self.profile_pic_path).resize((100, 100))
                self.profile_img = ImageTk.PhotoImage(img)
                self.pic_label.configure(image=self.profile_img)
                self.pic_label.image = self.profile_img
            else:
                self.pic_label.configure(image="", text="No image", font=("Arial", 10))
        except Exception as e:
            print("Image load error:", e)
            self.pic_label.configure(text="Error loading image", font=("Arial", 10))

    def upload_picture(self):
        path = filedialog.askopenfilename(filetypes=[("Image Files", "*.png *.jpg *.jpeg")])
        if path and Path(path).suffix.lower() in [".png", ".jpg", ".jpeg"]:
            if update_profile_image(self.identifier, path):
                self.profile_pic_path = path
                self.load_profile_image()
                messagebox.showinfo("Success", "Profile picture updated successfully!")
            else:
                messagebox.showerror("Error", "Failed to update profile image in database.")
        else:
            messagebox.showerror("Invalid File", "Please select a valid image file (.png/.jpg/.jpeg)")

    def update_email_func(self):
        email = self.email_entry.get().strip()
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            messagebox.showerror("Invalid Email", "Please enter a valid email address.")
            return
        msg = update_email(self.identifier, email)
        messagebox.showinfo("Email", msg)

    def change_password(self):
        old_pass = self.old_entry.get().strip()
        new_pass = self.new_entry.get().strip()
        if not old_pass or not new_pass:
            messagebox.showerror("Error", "Fill all password fields.")
            return
        if not verify_password(self.identifier, old_pass):
            messagebox.showerror("Error", "Old password is incorrect.")
            return
        msg = update_password(self.identifier, new_pass)
        messagebox.showinfo("Password", msg)
        self.root.destroy()

    def check_strength(self, event=None):
        pwd = self.new_entry.get()
        score = sum(bool(re.search(p, pwd)) for p in [r"[A-Z]", r"[a-z]", r"[0-9]", r"[!@#$%^&*()]"])
        strength = "Weak" if score < 2 else "Medium" if score == 2 else "Strong"
        color = {"Weak": "red", "Medium": "orange", "Strong": "green"}[strength]
        self.strength_label.config(text=f"{LANGUAGES[self.lang]['strength']}: {strength}", fg=color)

    def delete_account(self):
        if messagebox.askyesno("Delete", "Are you sure you want to delete this account? This action cannot be undone."):
            msg = delete_user(self.identifier)
            messagebox.showinfo("Account", msg)
            self.root.destroy()
