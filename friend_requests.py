import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import os

from Login_database import (
    get_friend_requests,
    update_request_status,
    get_profile_image
)

class FriendRequestsWindow:
    def __init__(self, current_user):
        self.current_user = current_user
        self.dark_mode = False

        self.window = tk.Toplevel()
        self.window.title("Friend Requests")
        self.window.geometry("420x460")
        self.window.resizable(False, False)

        # Top Bar
        top = tk.Frame(self.window)
        top.pack(fill=tk.X, pady=5)
        tk.Label(top, text="Incoming Friend Requests", font=("Arial", 16, "bold")).pack(side=tk.LEFT, padx=10)
        tk.Button(top, text="Toggle Dark Mode", command=self.toggle_dark).pack(side=tk.RIGHT, padx=10)

        # Scrollable Frame
        self.canvas = tk.Canvas(self.window, borderwidth=0, highlightthickness=0)
        self.scrollbar = tk.Scrollbar(self.window, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        # Refresh Button
        tk.Button(self.window, text="Refresh", command=self.display_requests,
                  bg="#2196F3", fg="white", font=("Arial", 10)).pack(pady=5)

        self.display_requests()
        self.auto_refresh()
        self.apply_theme()

    def display_requests(self):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        requests = get_friend_requests(self.current_user)

        if not requests:
            tk.Label(self.scrollable_frame, text="No friend requests found.", font=("Arial", 12)).pack(pady=10)
            return

        for sender, _ in requests:
            frame = tk.Frame(self.scrollable_frame, pady=5, padx=5, bd=1, relief=tk.RIDGE)
            frame.pack(fill=tk.X, padx=10, pady=5)

            # Profile image
            image_path = get_profile_image_path(sender)
            try:
                if image_path and os.path.exists(image_path):
                    img = Image.open(image_path).resize((40, 40))
                else:
                    img = Image.new("RGB", (40, 40), "#aaa")
                avatar = ImageTk.PhotoImage(img)
            except Exception as e:
                print("Image error:", e)
                img = Image.new("RGB", (40, 40), "#aaa")
                avatar = ImageTk.PhotoImage(img)

            avatar_label = tk.Label(frame, image=avatar)
            avatar_label.image = avatar
            avatar_label.pack(side=tk.LEFT, padx=5)

            # Name and buttons
            tk.Label(frame, text=sender, width=18, anchor="w", font=("Arial", 12)).pack(side=tk.LEFT, padx=5)
            tk.Button(frame, text="Accept", bg="#4CAF50", fg="white",
                      command=lambda s=sender: self.respond(s, "accepted")).pack(side=tk.RIGHT, padx=2)
            tk.Button(frame, text="Reject", bg="#f44336", fg="white",
                      command=lambda s=sender: self.respond(s, "rejected")).pack(side=tk.RIGHT, padx=2)

        self.apply_theme()  # Re-apply theme for new widgets

    def respond(self, sender, action):
        result = update_request_status(sender, self.current_user, action)
        messagebox.showinfo("Friend Request", result)
        self.display_requests()

    def toggle_dark(self):
        self.dark_mode = not self.dark_mode
        self.apply_theme()

    def apply_theme(self):
        bg = "#121212" if self.dark_mode else "#ffffff"
        fg = "#ffffff" if self.dark_mode else "#000000"
        self.window.configure(bg=bg)
        self.canvas.configure(bg=bg)
        self.scrollable_frame.configure(bg=bg)

        for widget in self.scrollable_frame.winfo_children():
            try:
                widget.configure(bg=bg, fg=fg)
                for sub in widget.winfo_children():
                    sub.configure(bg=bg, fg=fg)
            except:
                pass

    def auto_refresh(self):
        self.window.after(30000, self.auto_refresh)
        self.display_requests()
