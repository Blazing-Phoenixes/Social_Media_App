import tkinter as tk
from tkinter import ttk, filedialog, simpledialog
from PIL import Image, ImageTk
import os
import mimetypes

from Login_database import (
    search_users, send_friend_request, get_friend_requests, update_request_status,
    get_friends_list, get_user_details, unfriend_user,
    post_media, get_public_media, get_private_media_for_user, delete_media
)

# ================= MODERN ECOMMERCE THEME =================
BG = "#0f172a"              # Dark background
CARD = "#1e293b"           # Card background
PRIMARY = "#6366f1"        # Indigo
SECONDARY = "#22c55e"      # Green
TEXT = "#f8fafc"           # White text
SUBTEXT = "#94a3b8"        # Light gray
ERROR = "#ef4444"

FONT = ("Segoe UI", 11)

class HomeFrame(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=BG)
        self.app = app
        self.user = None

        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # ================= HEADER =================
        header = tk.Frame(self, bg="#1e293b", height=60)
        header.grid(row=0, column=0, sticky="ew")

        self.label = tk.Label(header, text="", bg="#1e293b",
                              fg=TEXT, font=("Segoe UI", 14, "bold"))
        self.label.pack(side="left", padx=15)

        tk.Button(header, text="Profile", bg=PRIMARY, fg="white",
                  relief="flat", padx=12,
                  command=lambda: self.app.show_frame("ProfileFrame", user=self.user)
        ).pack(side="right", padx=5, pady=10)

        tk.Button(header, text="Logout", bg=ERROR, fg="white",
                  relief="flat", padx=12,
                  command=lambda: self.app.show_frame("LoginSignupApp")
        ).pack(side="right", padx=5, pady=10)

        # ================= SEARCH BAR =================
        top = tk.Frame(self, bg=BG)
        top.grid(row=1, column=0, sticky="ew")

        self.search_var = tk.StringVar()

        self.search_entry = tk.Entry(
            top, textvariable=self.search_var,
            font=("Segoe UI", 11),
            bg="#1e293b", fg="white",
            insertbackground="white",
            relief="flat", width=40
        )
        self.search_entry.pack(side=tk.LEFT, padx=15, pady=10, ipady=5)

        # 🔥 NEW SEARCH BUTTON (without breaking existing search)
        tk.Button(top, text="Search",
                  bg=PRIMARY, fg="white", relief="flat",
                  command=self.render_search
                  ).pack(side=tk.LEFT, padx=5)

        # Live search still works
        self.search_entry.bind("<KeyRelease>", lambda e: self.render_search())

        # ================= TABS =================
        style = ttk.Style()
        style.theme_use("default")

        style.configure("TNotebook", background=BG)
        style.configure("TNotebook.Tab",
                        background="#1e293b",
                        foreground="white",
                        padding=10)

        self.tabs = ttk.Notebook(self)
        self.tabs.grid(row=2, column=0, sticky="nsew")

        self.tab_media = ttk.Frame(self.tabs)
        self.tab_search = ttk.Frame(self.tabs)
        self.tab_requests = ttk.Frame(self.tabs)
        self.tab_friends = ttk.Frame(self.tabs)

        self.tabs.add(self.tab_media, text="🏠 Home")
        self.tabs.add(self.tab_search, text="🔍 Search")
        self.tabs.add(self.tab_requests, text="📩 Requests")
        self.tabs.add(self.tab_friends, text="👥 Friends")

        # 🔥 DEFAULT HOME SCREEN = MEDIA
        self.tabs.select(self.tab_media)

        for name in ["search", "requests", "friends", "media"]:
            self.setup_scroll(getattr(self, f"tab_{name}"), name)

        tk.Button(self.tab_media, text="⬆ Upload Media",
                  bg=SECONDARY, fg="black", relief="flat",
                  command=self.upload_media).pack(pady=10)

        tk.Button(self.tab_requests, text="Refresh",
                  bg=PRIMARY, fg="white",
                  command=self.render_requests).pack(pady=5)

    # ================= TOAST =================
    def show_toast(self, msg, color=SECONDARY):
        toast = tk.Label(self, text=msg, bg=color, fg="black",
                         font=("Segoe UI", 10, "bold"))
        toast.place(relx=0.5, rely=0.95, anchor="center")
        self.after(2000, toast.destroy)

    # ================= LOAD =================
    def load_data(self, user):
        self.user = user
        details = get_user_details(user)

        self.label.config(text=f"Welcome, {details[0]}")

        self.search_var.set("")
        self.render_requests()
        self.render_friends()
        self.display_media_feed()

    # ================= SCROLL =================
    def setup_scroll(self, parent, name):
        frame = tk.Frame(parent, bg=BG)
        setattr(self, f"{name}_frame", frame)
        frame.pack(fill=tk.BOTH, expand=True)

        canvas = tk.Canvas(frame, bg=BG, highlightthickness=0)
        setattr(self, f"{name}_canvas", canvas)

        sb = ttk.Scrollbar(frame, orient="vertical", command=canvas.yview)

        scrollable = tk.Frame(canvas, bg=BG)
        setattr(self, f"{name}_scrollable", scrollable)

        scrollable.bind("<Configure>",
                        lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        canvas.create_window((0, 0), window=scrollable, anchor="nw")
        canvas.configure(yscrollcommand=sb.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.RIGHT, fill=tk.Y)

    def clear_children(self, frame):
        for child in frame.winfo_children():
            child.destroy()

    def show_message(self, parent, msg):
        self.clear_children(parent)
        tk.Label(parent, text=msg, fg=SUBTEXT, bg=BG,
                 font=("Segoe UI", 11)).pack(pady=20)

    # ================= SEARCH =================
    def render_search(self):
        self.clear_children(self.search_scrollable)
        query = self.search_var.get().strip()

        if not query:
            self.show_message(self.search_scrollable, "Start typing to search users")
            return

        results = search_users(query)

        for uname, _ in results:
            if uname.lower() == self.user.lower():
                continue

            card = tk.Frame(self.search_scrollable, bg=CARD, bd=0)
            card.pack(fill=tk.X, padx=12, pady=6)

            tk.Label(card, text=uname, bg=CARD, fg=TEXT,
                     font=("Segoe UI", 11)).pack(side=tk.LEFT, padx=10)

            tk.Button(card, text="Add Friend",
                      bg=PRIMARY, fg="white", relief="flat",
                      command=lambda u=uname: self.send_req(u)
                      ).pack(side=tk.RIGHT, padx=10, pady=5)

    def send_req(self, to):
        res = send_friend_request(self.user, to)
        self.show_toast(res)
        self.search_var.set("")
        self.render_search()

    # ================= REQUESTS =================
    def render_requests(self):
        self.clear_children(self.requests_scrollable)
        data = get_friend_requests(self.user)

        if not data:
            self.show_message(self.requests_scrollable, "No pending requests")
            return

        for sender, _ in data:
            card = tk.Frame(self.requests_scrollable, bg=CARD)
            card.pack(fill=tk.X, padx=10, pady=6)

            tk.Label(card, text=sender, bg=CARD, fg=TEXT).pack(side=tk.LEFT, padx=10)

            tk.Button(card, text="Accept", bg=SECONDARY,
                      command=lambda s=sender: self.respond(s, "accepted")
                      ).pack(side=tk.RIGHT, padx=5)

            tk.Button(card, text="Reject", bg=ERROR, fg="white",
                      command=lambda s=sender: self.respond(s, "rejected")
                      ).pack(side=tk.RIGHT, padx=5)

    def respond(self, sender, action):
        res = update_request_status(sender, self.user, action)
        self.show_toast(res)
        self.render_requests()
        self.render_friends()

    # ================= FRIENDS =================
    def render_friends(self):
        self.clear_children(self.friends_scrollable)
        friends = get_friends_list(self.user)

        if not friends:
            self.show_message(self.friends_scrollable, "No friends yet")
            return

        for f in friends:
            card = tk.Frame(self.friends_scrollable, bg=CARD)
            card.pack(fill=tk.X, padx=10, pady=6)

            tk.Label(card, text=f, bg=CARD, fg=TEXT).pack(side=tk.LEFT, padx=10)

            tk.Button(card, text="Chat", bg=PRIMARY, fg="white",
                      command=lambda u=f: self.app.show_frame(
                          "ChatFrame", sender=self.user, receiver=u)
                      ).pack(side=tk.RIGHT, padx=5)

            tk.Button(card, text="Remove", bg=ERROR, fg="white",
                      command=lambda u=f: self.remove_friend(u)
                      ).pack(side=tk.RIGHT, padx=5)

    def remove_friend(self, friend):
        if unfriend_user(self.user, friend):
            self.show_toast(f"{friend} removed", ERROR)
            self.render_friends()

    # ================= MEDIA =================
    def upload_media(self):
        file_path = filedialog.askopenfilename()
        if not file_path:
            return

        visibility = simpledialog.askstring("Visibility", "public/private")
        file_type = mimetypes.guess_type(file_path)[0] or 'unknown'

        post_media(self.user, self.user, file_path, file_type, visibility)
        self.show_toast("Uploaded successfully")
        self.display_media_feed()

    def display_media_feed(self):
        self.clear_children(self.media_scrollable)

        posts = get_public_media() + get_private_media_for_user(
            self.user, get_friends_list(self.user)
        )

        for media_id, uid, uname, path, ftype, vis, time in posts:
            card = tk.Frame(self.media_scrollable, bg=CARD)
            card.pack(fill="x", padx=12, pady=8)

            tk.Label(card, text=uname, bg=CARD, fg=TEXT,
                     font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=10)

            if ftype and "image" in ftype:
                try:
                    img = Image.open(path)
                    img.thumbnail((300, 300))
                    photo = ImageTk.PhotoImage(img)

                    lbl = tk.Label(card, image=photo, bg=CARD)
                    lbl.image = photo
                    lbl.pack(pady=5)
                except tk.TclError:
                    tk.Label(card, text="Preview failed", fg=SUBTEXT).pack()
            else:
                tk.Label(card, text=os.path.basename(path),
                         fg=SUBTEXT).pack(pady=5)

            btn_frame = tk.Frame(card, bg=CARD)
            btn_frame.pack(pady=5)

            tk.Button(btn_frame, text="Open",
                      bg=PRIMARY, fg="white",
                      command=lambda p=path: os.startfile(p)
                      ).pack(side="left", padx=5)

            if uid == self.user:
                tk.Button(btn_frame, text="Delete", bg=ERROR, fg="white",
                          command=lambda m=media_id: self.delete_post(m)
                          ).pack(side="left", padx=5)

    def delete_post(self, media_id):
        delete_media(media_id, self.user)
        self.show_toast("Deleted", ERROR)
        self.display_media_feed()
