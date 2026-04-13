# friend_requests.py
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import os

from Login_database import (
    get_friend_requests,
    update_request_status,
    get_profile_image_path
)

# ---------------- COLORS ----------------
BACKGROUND = "#0f172a"
CARD = "#1e293b"
INPUT = "#1f2937"
BUTTON = "#6366f1"
HOVER = "#4f46e5"
TEXT = "#e2e8f0"
SUBTEXT = "#94a3b8"
SUCCESS = "#22c55e"
ERROR = "#ef4444"


class FriendRequestsFrame(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)

        self.app = app
        self.current_user = None
        self.dark_mode = False

        # Responsive grid
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # ---------------- TOP BAR ----------------
        top = tk.Frame(self)
        top.grid(row=0, column=0, sticky="ew", pady=10, padx=10)

        self.title_label = tk.Label(
            top,
            text="📩 Friend Requests",
            font=("Segoe UI", 18, "bold")
        )
        self.title_label.pack(side=tk.LEFT)

        tk.Button(
            top,
            text="🌙 Toggle",
            command=self.toggle_dark,
            font=("Segoe UI", 10, "bold"),
            relief="flat"
        ).pack(side=tk.RIGHT)

        # ---------------- SCROLL AREA ----------------
        self.canvas = tk.Canvas(self, borderwidth=0, highlightthickness=0)
        self.canvas.grid(row=1, column=0, sticky="nsew")

        self.scrollbar = tk.Scrollbar(
            self,
            orient="vertical",
            command=self.canvas.yview
        )
        self.scrollbar.grid(row=1, column=1, sticky="ns")

        self.scrollable_frame = tk.Frame(self.canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(
                scrollregion=self.canvas.bbox("all")
            )
        )

        self.canvas.create_window(
            (0, 0),
            window=self.scrollable_frame,
            anchor="nw"
        )

        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        # ---------------- BOTTOM ----------------
        bottom = tk.Frame(self)
        bottom.grid(row=2, column=0, pady=10)

        tk.Button(
            bottom,
            text="🔄 Refresh",
            command=self.display_requests,
            bg=BUTTON,
            fg="white",
            font=("Segoe UI", 10, "bold"),
            relief="flat",
            padx=10,
            pady=5
        ).pack(side=tk.LEFT, padx=5)

        tk.Button(
            bottom,
            text="⬅ Back",
            command=lambda: self.app.show_frame(
                "HomeFrame",
                user=self.current_user
            ),
            font=("Segoe UI", 10),
            relief="flat",
            padx=10,
            pady=5
        ).pack(side=tk.LEFT, padx=5)

    # ---------------- LOAD DATA ----------------
    def load_data(self, user):
        self.current_user = user
        self.display_requests()
        self.auto_refresh()
        self.apply_theme()

    # ---------------- DISPLAY ----------------
    def display_requests(self):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        requests = get_friend_requests(self.current_user)

        if not requests:
            tk.Label(
                self.scrollable_frame,
                text="No friend requests found.",
                font=("Segoe UI", 12)
            ).pack(pady=20)
            return

        for sender, _ in requests:
            # Normalize for display ONLY
            display_name = sender.lower()

            card = tk.Frame(
                self.scrollable_frame,
                bg=CARD if self.dark_mode else "#f1f5f9",
                bd=0,
                relief="flat"
            )
            card.pack(fill=tk.X, padx=15, pady=8, ipadx=5, ipady=5)

            card.grid_columnconfigure(1, weight=1)

            # ---------------- AVATAR ----------------
            image_path = get_profile_image_path(sender)

            try:
                if image_path and os.path.exists(image_path):
                    img = Image.open(image_path).resize((45, 45))
                else:
                    img = Image.new("RGB", (45, 45), "#999")

                avatar = ImageTk.PhotoImage(img)

            except Exception:
                img = Image.new("RGB", (45, 45), "#999")
                avatar = ImageTk.PhotoImage(img)

            avatar_label = tk.Label(card, image=avatar, bg=card["bg"])
            avatar_label.image = avatar
            avatar_label.grid(row=0, column=0, padx=10)

            # ---------------- NAME ----------------
            tk.Label(
                card,
                text=display_name,
                font=("Segoe UI", 12, "bold"),
                bg=card["bg"],
                fg=TEXT if self.dark_mode else "#111"
            ).grid(row=0, column=1, sticky="w")

            # ---------------- BUTTONS ----------------
            btn_frame = tk.Frame(card, bg=card["bg"])
            btn_frame.grid(row=0, column=2, padx=10)

            accept_btn = tk.Button(
                btn_frame,
                text="✔ Accept",
                bg=SUCCESS,
                fg="white",
                relief="flat",
                command=lambda s=sender: self.respond(s, "accepted")
            )
            accept_btn.pack(side=tk.LEFT, padx=3)

            reject_btn = tk.Button(
                btn_frame,
                text="✖ Reject",
                bg=ERROR,
                fg="white",
                relief="flat",
                command=lambda s=sender: self.respond(s, "rejected")
            )
            reject_btn.pack(side=tk.LEFT, padx=3)

            # Hover effects
            for btn in (accept_btn, reject_btn):
                btn.bind("<Enter>", lambda e, b=btn: b.config(opacity=0.8))
                btn.bind("<Leave>", lambda e, b=btn: b.config(opacity=1))

        self.apply_theme()

    # ---------------- ACTION ----------------
    def respond(self, sender, action):
        # Normalize BOTH sides for consistency
        sender = sender.lower()
        receiver = self.current_user.lower()

        result = update_request_status(sender, receiver, action)

        messagebox.showinfo("Friend Request", result)
        self.display_requests()

    # ---------------- DARK MODE ----------------
    def toggle_dark(self):
        self.dark_mode = not self.dark_mode
        self.apply_theme()

    def apply_theme(self):
        bg = BACKGROUND if self.dark_mode else "#ffffff"
        fg = TEXT if self.dark_mode else "#000000"

        self.configure(bg=bg)
        self.canvas.configure(bg=bg)
        self.scrollable_frame.configure(bg=bg)

        for widget in self.scrollable_frame.winfo_children():
            try:
                widget.configure(bg=widget["bg"])
                for sub in widget.winfo_children():
                    if isinstance(sub, tk.Label):
                        sub.configure(bg=widget["bg"], fg=fg)
                    elif isinstance(sub, tk.Frame):
                        sub.configure(bg=widget["bg"])
            except Exception as e:
                print(f"Error occurred while applying theme: {e}")

    # ---------------- AUTO REFRESH ----------------
    def auto_refresh(self):
        if self.current_user:
            self.display_requests()
        self.after(30000, self.auto_refresh)