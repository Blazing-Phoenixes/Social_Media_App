# home_screen.py

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
from PIL import Image, ImageTk
import os
import mimetypes
import subprocess
import platform
import webbrowser

from chat_gui import ChatWindow
from Login_database import (
    search_users, send_friend_request, get_friend_requests, update_request_status,
    get_friends_list, get_user_details, get_profile_image_path, unfriend_user,
    post_media, get_public_media, get_private_media_for_user, delete_media
)
from profile_screen import ProfileScreen

class HomeScreen:
    def __init__(self, user):
        self.user = user
        self.is_dark = False

        self.root = tk.Tk()
        self.root.title("Home / Feed")
        w, h = 1000, 700
        x = (self.root.winfo_screenwidth() - w) // 2
        y = (self.root.winfo_screenheight() - h) // 2
        self.root.geometry(f"{w}x{h}+{x}+{y}")
        self.root.configure(bg="#f9f9f9")

        self.top = tk.Frame(self.root, bg="#f9f9f9")
        self.top.pack(fill=tk.X, pady=5)

        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(self.top, textvariable=self.search_var, width=30)
        self.search_entry.pack(side=tk.LEFT, padx=10)
        self.search_entry.bind("<KeyRelease>", lambda e: self.render_search())

        ttk.Button(self.top, text="Settings", command=self.open_profile).pack(side=tk.RIGHT, padx=5)
        ttk.Button(self.top, text="Dark Mode", command=self.toggle_dark).pack(side=tk.RIGHT, padx=5)

        self.header = tk.Frame(self.root, bg="#f9f9f9")
        self.header.pack(pady=5)
        details = get_user_details(self.user)
        img_path = get_profile_image_path(self.user)
        if img_path and os.path.exists(img_path):
            img = Image.open(img_path).resize((50, 50))
            self.img_tk = ImageTk.PhotoImage(img)
            tk.Label(self.header, image=self.img_tk, bg="#f9f9f9").pack(side=tk.LEFT, padx=10)

        tk.Label(self.header, text=f"Welcome, {details[0]}\nEmail: {details[2] or 'N/A'}",
                 font=("Arial", 12), bg="#f9f9f9").pack(side=tk.LEFT)

        self.tabs = ttk.Notebook(self.root)
        self.tab_search = ttk.Frame(self.tabs)
        self.tab_requests = ttk.Frame(self.tabs)
        self.tab_friends = ttk.Frame(self.tabs)
        self.tab_media = ttk.Frame(self.tabs)
        self.tabs.add(self.tab_search, text="Search")
        self.tabs.add(self.tab_requests, text="Requests")
        self.tabs.add(self.tab_friends, text="Friends")
        self.tabs.add(self.tab_media, text="Media Feed")
        self.tabs.pack(fill=tk.BOTH, expand=True)

        for name in ["search", "requests", "friends", "media"]:
            self.setup_scroll(getattr(self, f"tab_{name}"), name)

        self.file_type_var = tk.StringVar(value="all")
        self.show_message(self.search_scrollable, "(Type above to search users)")
        tk.Button(self.tab_requests, text="Refresh", command=self.render_requests).pack(pady=5)

        self.render_requests()
        self.render_friends()
        self.display_media_feed()

        tk.Button(self.root, text="Logout", command=self.root.destroy).pack(pady=5)
        self.auto_refresh()
        self.root.mainloop()

    def setup_scroll(self, parent, name):
        frame = tk.Frame(parent)
        setattr(self, f"{name}_frame", frame)
        frame.pack(fill=tk.BOTH, expand=True)

        canvas = tk.Canvas(frame, highlightthickness=0, bg="#f9f9f9")
        setattr(self, f"{name}_canvas", canvas)

        sb = ttk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        setattr(self, f"{name}_sb", sb)

        scrollable = tk.Frame(canvas, bg="#f9f9f9")
        setattr(self, f"{name}_scrollable", scrollable)

        scrollable.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable, anchor="nw")
        canvas.configure(yscrollcommand=sb.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.RIGHT, fill=tk.Y)

    def show_message(self, parent_frame, msg):
        self.clear_children(parent_frame)
        tk.Label(parent_frame, text=msg, fg="#777", bg=parent_frame["bg"]).pack(pady=20)

    def clear_children(self, frame):
        for child in frame.winfo_children():
            child.destroy()

    def render_search(self):
        self.clear_children(self.search_scrollable)
        query = self.search_var.get().strip()
        if not query:
            self.show_message(self.search_scrollable, "(Type above to search users)")
            return
        results = search_users(query)
        for uname, _ in results:
            if uname.lower() == self.user.lower():
                continue
            f = tk.Frame(self.search_scrollable, bg="#f9f9f9", bd=1, relief=tk.SOLID)
            f.pack(fill=tk.X, padx=5, pady=3)
            tk.Label(f, text=uname, bg="#f9f9f9", anchor="w").pack(side=tk.LEFT, padx=10)
            ttk.Button(f, text="Send Request", command=lambda u=uname: self.send_req(u)).pack(side=tk.RIGHT, padx=5)

    def send_req(self, to):
        res = send_friend_request(self.user, to)
        messagebox.showinfo("Request Status", res)

    def render_requests(self):
        self.clear_children(self.requests_scrollable)
        data = get_friend_requests(self.user)
        if not data:
            self.show_message(self.requests_scrollable, "No pending requests.")
            return
        for sender, _ in data:
            f = tk.Frame(self.requests_scrollable, bg="#f9f9f9", bd=1, relief=tk.SOLID)
            f.pack(fill=tk.X, padx=5, pady=3)
            tk.Label(f, text=sender, bg="#f9f9f9").pack(side=tk.LEFT, padx=10)
            ttk.Button(f, text="Accept", command=lambda s=sender: self.respond(s, "accepted")).pack(side=tk.RIGHT, padx=2)
            ttk.Button(f, text="Reject", command=lambda s=sender: self.respond(s, "rejected")).pack(side=tk.RIGHT, padx=2)

    def respond(self, sender, action):
        res = update_request_status(sender, self.user, action)
        messagebox.showinfo("Request", res)
        self.render_requests()
        self.render_friends()

    def render_friends(self):
        self.clear_children(self.friends_scrollable)
        friends = get_friends_list(self.user)
        if not friends:
            self.show_message(self.friends_scrollable, "No friends yet.")
            return
        for f in friends:
            f_frame = tk.Frame(self.friends_scrollable, bg="#f9f9f9", bd=1, relief=tk.SOLID)
            f_frame.pack(fill=tk.X, padx=5, pady=3)
            tk.Label(f_frame, text=f, bg="#f9f9f9").pack(side=tk.LEFT, padx=10)
            ttk.Button(f_frame, text="Chat", command=lambda u=f: self.open_chat(u)).pack(side=tk.RIGHT, padx=2)
            ttk.Button(f_frame, text="Unfriend", command=lambda u=f: self.remove_friend(u)).pack(side=tk.RIGHT, padx=2)

    def open_chat(self, friend):
        ChatWindow(tk.Toplevel(self.root), self.user, friend)

    def remove_friend(self, friend):
        if messagebox.askyesno("Confirm", f"Remove {friend}?"):
            if unfriend_user(self.user, friend):
                messagebox.showinfo("Removed", f"{friend} unfriended.")
                self.render_friends()

    def upload_media(self):
        file_path = filedialog.askopenfilename(title="Select File (Max 500MB)")
        if not file_path:
            return
        if os.path.getsize(file_path) > 500 * 1024 * 1024:
            messagebox.showerror("File Too Large", "Max 500MB allowed.")
            return
        visibility = simpledialog.askstring("Visibility", "Enter 'public' or 'private':")
        if visibility not in ['public', 'private']:
            messagebox.showerror("Invalid", "Choose 'public' or 'private'")
            return
        file_type = mimetypes.guess_type(file_path)[0] or 'unknown'
        result = post_media(self.user, self.user, file_path, file_type, visibility)
        messagebox.showinfo("Upload Status", result)
        self.display_media_feed()

    def display_media_feed(self):
        self.clear_children(self.media_scrollable)

        filter_frame = tk.Frame(self.media_scrollable, bg="#f9f9f9")
        filter_frame.pack(fill=tk.X, pady=5)
        tk.Label(filter_frame, text="Filter by Type:", bg="#f9f9f9").pack(side=tk.LEFT, padx=5)
        options = ["all", "image", "audio", "video", "document"]
        tk.OptionMenu(filter_frame, self.file_type_var, *options, command=lambda e: self.display_media_feed()).pack(side=tk.LEFT)
        tk.Button(filter_frame, text="Upload Media", bg="#28a745", fg="white", command=self.upload_media).pack(side=tk.RIGHT, padx=10)

        posts = get_public_media() + get_private_media_for_user(self.user, get_friends_list(self.user))
        posts.sort(key=lambda x: x[6], reverse=True)
        selected_type = self.file_type_var.get()

        for media_id, uid, uname, path, ftype, vis, time in posts:
            if selected_type != "all":
                if selected_type == "image" and not ftype.startswith("image"):
                    continue
                if selected_type == "audio" and not ftype.startswith("audio"):
                    continue
                if selected_type == "video" and not ftype.startswith("video"):
                    continue
                if selected_type == "document" and not ("pdf" in ftype or "text" in ftype):
                    continue

            card = tk.Frame(self.media_scrollable, bd=2, relief="ridge", padx=10, pady=5, bg="#f7f7f7")
            card.pack(fill="x", padx=10, pady=5)

            tk.Label(card, text=f"{uname} • {os.path.basename(path)} • {vis} • {time}",
                     bg="#f7f7f7", font=("Arial", 10, "bold")).pack(anchor="w")

            if ftype.startswith("image"):
                try:
                    img = Image.open(path)
                    img.thumbnail((120, 120))
                    img = ImageTk.PhotoImage(img)
                    img_label = tk.Label(card, image=img, bg="#f7f7f7")
                    img_label.image = img
                    img_label.pack(anchor="w")
                except:
                    tk.Label(card, text="[Image can't be loaded]", fg="red", bg="#f7f7f7").pack(anchor="w")
            else:
                tk.Label(card, text=ftype, fg="blue", bg="#f7f7f7").pack(anchor="w")

            btns = tk.Frame(card, bg="#f7f7f7")
            btns.pack(anchor="e")
            tk.Button(btns, text="Open", command=lambda p=path: self.open_file(p)).pack(side="left", padx=5)
            if uid == self.user:
                tk.Button(btns, text="Delete", command=lambda m=media_id: self.delete_post(m)).pack(side="left", padx=5)

    def open_file(self, path):
        try:
            if not os.path.exists(path):
                messagebox.showerror("File Not Found", f"The file does not exist:\n{path}")
                return
            sys_platform = platform.system()
            if sys_platform == "Windows":
                os.startfile(path)
            elif sys_platform == "Darwin":
                subprocess.call(["open", path])
            elif sys_platform == "Linux":
                if "ANDROID_STORAGE" in os.environ:
                    os.system(f'am start -a android.intent.action.VIEW -d "file://{path}"')
                else:
                    try:
                        subprocess.call(["xdg-open", path])
                    except FileNotFoundError:
                        webbrowser.open(f"file://{path}")
            else:
                webbrowser.open(f"file://{path}")
        except Exception as e:
            messagebox.showerror("Open File Error", f"Unable to open file:\n{e}")

    def delete_post(self, media_id):
        if messagebox.askyesno("Confirm", "Delete this media?"):
            delete_media(media_id, self.user)
            self.display_media_feed()

    def toggle_dark(self):
        self.is_dark = not self.is_dark
        bg = "#222" if self.is_dark else "#f9f9f9"
        fg = "white" if self.is_dark else "black"
        self.apply_theme(self.root, bg, fg)

    def apply_theme(self, widget, bg, fg):
        try:
            widget.configure(bg=bg, fg=fg)
        except:
            pass
        for child in widget.winfo_children():
            self.apply_theme(child, bg, fg)

    def open_profile(self):
        ProfileScreen(self.user)

    def auto_refresh(self):
        self.render_requests()
        self.render_friends()
        self.root.after(30000, self.auto_refresh)