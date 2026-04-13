import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk
import os
import re
from pathlib import Path

from Login_database import (
    get_user_details, update_password, verify_password,
    update_email, update_profile_image, get_profile_image_path,
    delete_user
)

# ---------------- MODERN UI ----------------
BG = "#f8fafc"
CARD = "#ffffff"
PRIMARY = "#6366f1"
HOVER = "#4f46e5"
TEXT = "#0f172a"
SUBTEXT = "#64748b"
BORDER = "#e5e7eb"
SUCCESS = "#22c55e"
ERROR = "#ef4444"

FONT = ("Segoe UI", 11)
TITLE_FONT = ("Segoe UI", 22, "bold")


# ---------------- TOAST ----------------
class Toast(tk.Toplevel):
    def __init__(self, parent, message, color=SUCCESS):
        super().__init__(parent)
        self.overrideredirect(True)
        self.configure(bg=color)

        tk.Label(self, text=message, bg=color, fg="white",
                 font=("Segoe UI", 10, "bold")).pack(ipadx=14, ipady=8)

        self.after(2200, self.destroy)

        self.update_idletasks()
        x = parent.winfo_rootx() + parent.winfo_width() - 280
        y = parent.winfo_rooty() + 30
        self.geometry(f"+{x}+{y}")


# ---------------- CONFIRM DIALOG ----------------
class ConfirmDialog(tk.Toplevel):
    def __init__(self, parent, text, confirm_callback):
        super().__init__(parent)
        self.configure(bg=CARD)
        self.geometry("320x160")
        self.resizable(False, False)
        self.title("Confirm")

        tk.Label(self, text=text, bg=CARD, fg=TEXT,
                 font=FONT, wraplength=260).pack(pady=25)

        btn_frame = tk.Frame(self, bg=CARD)
        btn_frame.pack()

        tk.Button(btn_frame, text="Cancel", bg=BORDER,
                  relief="flat", width=10,
                  command=self.destroy).pack(side="left", padx=10)

        tk.Button(btn_frame, text="Yes", bg=ERROR, fg="white",
                  relief="flat", width=10,
                  command=lambda: [confirm_callback(), self.destroy()]
                  ).pack(side="left", padx=10)


# ---------------- SCROLLABLE ----------------
class ScrollableFrame(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=BG)

        self.canvas = tk.Canvas(self, bg=BG, highlightthickness=0)
        self.scrollbar = tk.Scrollbar(self, command=self.canvas.yview)

        self.inner = tk.Frame(self.canvas, bg=BG)

        self.inner.bind("<Configure>",
                        lambda e: self.canvas.configure(
                            scrollregion=self.canvas.bbox("all")))

        self.canvas.create_window((0, 0), window=self.inner, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        # Smooth scroll (Windows + touchpad)
        self.canvas.bind_all("<MouseWheel>",
                             lambda e: self.canvas.yview_scroll(
                                 int(-1 * (e.delta / 120)), "units"))

        self.canvas.bind_all("<Button-4>",
                             lambda e: self.canvas.yview_scroll(-1, "units"))
        self.canvas.bind_all("<Button-5>",
                             lambda e: self.canvas.yview_scroll(1, "units"))


# ---------------- MODERN BUTTON ----------------
def modern_button(parent, text, cmd, bg=PRIMARY, fg="white"):
    btn = tk.Label(parent, text=text, bg=bg, fg=fg,
                   font=("Segoe UI", 10, "bold"),
                   padx=14, pady=7, cursor="hand2")

    def on_enter(e): btn.config(bg=HOVER)
    def on_leave(e): btn.config(bg=bg)

    btn.bind("<Enter>", on_enter)
    btn.bind("<Leave>", on_leave)
    btn.bind("<Button-1>", lambda e: cmd())

    return btn


# ---------------- FLOATING ENTRY ----------------
class FloatingEntry(tk.Frame):
    def __init__(self, parent, placeholder="", show=None):
        super().__init__(parent, bg=CARD,
                         highlightbackground=BORDER,
                         highlightthickness=1)

        self.placeholder = placeholder

        self.entry = tk.Entry(self, bd=0, font=FONT, show=show)
        self.entry.pack(fill="both", padx=12, pady=10)

        self.label = tk.Label(self, text=placeholder, fg=SUBTEXT,
                              bg=CARD, font=("Segoe UI", 9))
        self.label.place(x=14, y=10)

        self.entry.bind("<FocusIn>", self.float_up)
        self.entry.bind("<FocusOut>", self.float_down)

    def float_up(self, e=None):
        self.label.config(font=("Segoe UI", 8))
        self.label.place(x=10, y=-8)

    def float_down(self, e=None):
        if not self.entry.get():
            self.label.config(font=("Segoe UI", 9))
            self.label.place(x=14, y=10)

    def get(self):
        return self.entry.get()

    def clear(self):
        self.entry.delete(0, tk.END)
        self.float_down()


# ---------------- PROFILE FRAME ----------------
class ProfileFrame(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=BG)
        self.app = app
        self.identifier = None

        self.scroll = ScrollableFrame(self)
        self.scroll.pack(fill="both", expand=True)

        wrapper = tk.Frame(self.scroll.inner, bg=BG)
        wrapper.pack(expand=True)

        self.container = tk.Frame(wrapper, bg=CARD, padx=50, pady=40)
        self.container.pack(pady=50)

        tk.Label(self.container, text="Account Settings",
                 font=TITLE_FONT, bg=CARD, fg=TEXT).pack(pady=15)

        self.pic_label = tk.Label(self.container, bg=CARD)
        self.pic_label.pack(pady=10)

        modern_button(self.container, "Upload Picture",
                      self.upload_picture).pack(pady=8)

        self.info1 = tk.Label(self.container, bg=CARD, fg=TEXT, font=FONT)
        self.info1.pack()

        self.info2 = tk.Label(self.container, bg=CARD, fg=TEXT, font=FONT)
        self.info2.pack(pady=(0, 10))

        # EMAIL
        self.email_entry = FloatingEntry(self.container, "Email")
        self.email_entry.pack(fill="x", pady=10)

        modern_button(self.container, "Update Email",
                      self.update_email_func).pack(pady=10)

        # PASSWORD
        tk.Label(self.container, text="Change Password",
                 font=("Segoe UI", 15, "bold"),
                 bg=CARD).pack(pady=20)

        self.old_entry = FloatingEntry(self.container, "Old Password", "*")
        self.old_entry.pack(fill="x", pady=6)

        self.new_entry = FloatingEntry(self.container, "New Password", "*")
        self.new_entry.pack(fill="x", pady=6)

        self.new_entry.entry.bind("<KeyRelease>", self.check_strength)

        self.strength_label = tk.Label(self.container, bg=CARD, font=FONT)
        self.strength_label.pack(pady=5)

        modern_button(self.container, "Update Password",
                      self.change_password).pack(pady=12)

        modern_button(self.container, "Delete Account",
                      self.confirm_delete, bg=ERROR).pack(pady=10)

        modern_button(self.container, "Back",
                      lambda: self.app.show_frame(
                          "HomeFrame", user=self.app.current_user),
                      bg=BORDER, fg=TEXT).pack(pady=5)

    # ---------------- LOAD ----------------
    def load_data(self, user):
        self.identifier = user
        data = get_user_details(user)

        if not data:
            Toast(self, "User not found", ERROR)
            return

        self.username, self.phone, self.email, _ = data
        self.profile_pic_path = get_profile_image_path(user) or ""

        self.info1.config(text=f"Username: {self.username}")
        self.info2.config(text=f"Phone: {self.phone}")

        self.email_entry.entry.delete(0, tk.END)
        self.email_entry.entry.insert(0, self.email or "")

        self.load_image()

    # ---------------- IMAGE ----------------
    def load_image(self):
        try:
            if self.profile_pic_path and os.path.exists(self.profile_pic_path):
                img = Image.open(self.profile_pic_path).resize((110, 110))
                self.img = ImageTk.PhotoImage(img)
                self.pic_label.config(image=self.img, text="")
            else:
                self.pic_label.config(text="No Image", image="")
        except tk.TclError:
            self.pic_label.config(text="Error loading image", image="")

    def upload_picture(self):
        path = filedialog.askopenfilename(
            filetypes=[("Image Files", "*.png *.jpg *.jpeg")])

        if path and Path(path).suffix.lower() in [".png", ".jpg", ".jpeg"]:
            if update_profile_image(self.identifier, path):
                self.profile_pic_path = path
                self.load_image()
                Toast(self, "Profile updated")
            else:
                Toast(self, "Update failed", ERROR)

    # ---------------- EMAIL ----------------
    def update_email_func(self):
        email = self.email_entry.get().strip()

        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            Toast(self, "Invalid email", ERROR)
        else:
            Toast(self, update_email(self.identifier, email))

        self.email_entry.clear()   # ✅ ALWAYS CLEAR

    # ---------------- PASSWORD ----------------
    def change_password(self):
        old = self.old_entry.get().strip()
        new = self.new_entry.get().strip()

        if not verify_password(self.identifier, old):
            Toast(self, "Wrong old password", ERROR)
        else:
            Toast(self, update_password(self.identifier, new))

        self.clear_password()   # ✅ ALWAYS CLEAR

    def clear_password(self):
        self.old_entry.clear()
        self.new_entry.clear()
        self.strength_label.config(text="")

    def check_strength(self, e=None):
        pwd = self.new_entry.get()
        score = sum(bool(re.search(p, pwd)) for p in
                    [r"[A-Z]", r"[a-z]", r"[0-9]", r"[!@#$%^&*()]"])

        strength = "Weak" if score < 2 else "Medium" if score == 2 else "Strong"
        color = {"Weak": ERROR, "Medium": "#f59e0b", "Strong": SUCCESS}[strength]

        self.strength_label.config(text=f"Strength: {strength}", fg=color)

    # ---------------- DELETE ----------------
    def confirm_delete(self):
        ConfirmDialog(self, "Delete your account permanently?",
                      self.delete_account)

    def delete_account(self):
        Toast(self, delete_user(self.identifier))
        self.app.show_frame("LoginFrame")