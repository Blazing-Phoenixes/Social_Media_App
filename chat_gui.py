import tkinter as tk
from tkinter import scrolledtext, filedialog, Menu
from datetime import datetime
import os
from PIL import Image, ImageTk

from Login_database import send_message, get_conversation, mark_messages_as_read

# ---------------- COLORS ----------------
BG_MAIN = "#0f172a"
CARD = "#111827"
PRIMARY = "#6366f1"
PRIMARY_HOVER = "#4f46e5"
TEXT = "#e5e7eb"
SUBTEXT = "#9ca3af"
INPUT_BG = "#1f2937"
INPUT_BORDER = "#374151"

MY_MSG = "#4f46e5"
OTHER_MSG = "#374151"

# ---------------- FONTS ----------------
TITLE_FONT = ("Segoe UI", 15, "bold")
TEXT_FONT = ("Segoe UI", 11)
ENTRY_FONT = ("Segoe UI", 12)


# ---------------- CHAT FRAME ----------------
class ChatFrame(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=BG_MAIN)
        self.app = app

        self.sender = None
        self.receiver = None
        self.refresh_interval_ms = 3000

        self.images_cache = {}  # keep image references

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # ---------------- HEADER ----------------
        header = tk.Frame(self, bg="#020617", height=60)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_columnconfigure(1, weight=1)

        self.avatar = tk.Label(header, text="👤",
                               bg="#020617", fg="white",
                               font=("Segoe UI", 18, "bold"))
        self.avatar.grid(row=0, column=0, padx=10)

        self.title_label = tk.Label(header, text="",
                                   font=TITLE_FONT,
                                   bg="#020617", fg=TEXT)
        self.title_label.grid(row=0, column=1, sticky="w")

        back_btn = tk.Button(header, text="←",
                             bg=PRIMARY, fg="white",
                             font=("Segoe UI", 11, "bold"),
                             relief="flat",
                             command=lambda: self.app.show_frame("HomeFrame", user=self.sender))
        back_btn.grid(row=0, column=2, padx=10)

        # ---------------- CHAT AREA ----------------
        container = tk.Frame(self, bg=BG_MAIN)
        container.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)

        self.chat_area = scrolledtext.ScrolledText(
            container,
            wrap=tk.WORD,
            font=TEXT_FONT,
            bg=CARD,
            fg=TEXT,
            relief="flat",
            padx=15,
            pady=10,
            insertbackground="white"
        )
        self.chat_area.pack(fill="both", expand=True)
        self.chat_area.config(state=tk.DISABLED)

        # Right click menu
        self.menu = Menu(self, tearoff=0)
        self.menu.add_command(label="❤️ React", command=lambda: self.react("❤️"))
        self.menu.add_command(label="👍 React", command=lambda: self.react("👍"))
        self.menu.add_command(label="😂 React", command=lambda: self.react("😂"))
        self.menu.add_separator()
        self.menu.add_command(label="🗑 Delete", command=self.delete_message)

        self.chat_area.bind("<Button-3>", self.show_menu)

        # ---------------- TYPING ----------------
        self.typing_label = tk.Label(self,
                                     text="",
                                     font=("Segoe UI", 9),
                                     fg=SUBTEXT,
                                     bg=BG_MAIN)
        self.typing_label.grid(row=2, column=0)

        # ---------------- INPUT ----------------
        bottom = tk.Frame(self, bg=BG_MAIN)
        bottom.grid(row=3, column=0, sticky="ew", padx=10, pady=10)
        bottom.grid_columnconfigure(0, weight=1)

        self.entry = tk.Entry(bottom,
                              font=ENTRY_FONT,
                              bg=INPUT_BG,
                              fg="white",
                              insertbackground="white",
                              relief="flat",
                              highlightthickness=2,
                              highlightbackground=INPUT_BORDER,
                              highlightcolor=PRIMARY)
        self.entry.grid(row=0, column=0, sticky="ew", padx=5, ipady=10)

        self.entry.bind("<Return>", self.send_msg)
        self.entry.bind("<Key>", lambda e: self.show_typing())

        send_btn = tk.Button(bottom, text="Send",
                             bg=PRIMARY, fg="white",
                             font=("Segoe UI", 10, "bold"),
                             relief="flat",
                             command=self.send_msg)
        send_btn.grid(row=0, column=1, padx=5, ipadx=10)

        file_btn = tk.Button(bottom, text="📎",
                             bg="#020617", fg="white",
                             relief="flat",
                             command=self.send_file)
        file_btn.grid(row=0, column=2, padx=5)

    # ---------------- LOAD ----------------
    def load_data(self, sender=None, receiver=None):
        self.sender = sender
        self.receiver = receiver

        self.title_label.config(text=receiver)
        self.avatar.config(text=receiver[0].upper())

        self.load_messages()
        self.auto_refresh()

    # ---------------- LOAD MESSAGES ----------------
    def load_messages(self):
        if not self.sender or not self.receiver:
            return

        mark_messages_as_read(self.receiver, self.sender)
        messages = get_conversation(self.sender, self.receiver)

        self.chat_area.config(state=tk.NORMAL)
        self.chat_area.delete(1.0, tk.END)

        for msg in messages:
            sender, message, time = msg
            time_fmt = datetime.strptime(time, "%Y-%m-%d %H:%M:%S").strftime("%I:%M %p")

            is_me = sender == self.sender

            # ---------- IMAGE PREVIEW ----------
            if "[File]" in message:
                file_name = message.replace("[File] ", "").split("|")[0].strip()
                self.insert_image(file_name, is_me)
                continue

            bubble = f"{message}\n{time_fmt}"

            if is_me:
                bubble += " ✓✓"

            self.insert_bubble(bubble, is_me)

        self.chat_area.config(state=tk.DISABLED)
        self.chat_area.yview(tk.END)

    # ---------------- IMAGE ----------------
    def insert_image(self, file_name, is_me):
        path = f"C:/Users/ELCOT/Downloads/{file_name}"

        if not os.path.exists(path):
            self.insert_bubble("[Image not found]", is_me)
            return

        img = Image.open(path)
        img.thumbnail((200, 200))
        img_tk = ImageTk.PhotoImage(img)

        self.images_cache[file_name] = img_tk

        self.chat_area.image_create(tk.END, image=img_tk)
        self.chat_area.insert(tk.END, "\n")

    # ---------------- BUBBLE ----------------
    def insert_bubble(self, text, is_me):
        tag = "me" if is_me else "them"

        self.chat_area.insert(tk.END, "\n")

        start = self.chat_area.index(tk.END)
        self.chat_area.insert(tk.END, text + "\n")
        end = self.chat_area.index(tk.END)

        self.chat_area.tag_add(tag, start, end)

        if is_me:
            self.chat_area.tag_config(tag,
                                     background=MY_MSG,
                                     lmargin1=120,
                                     lmargin2=120,
                                     rmargin=10,
                                     spacing3=8)
        else:
            self.chat_area.tag_config(tag,
                                     background=OTHER_MSG,
                                     lmargin1=10,
                                     lmargin2=10,
                                     rmargin=120,
                                     spacing3=8)

    # ---------------- SEND ----------------
    def send_msg(self, event=None):
        msg = self.entry.get().strip()
        if msg:
            send_message(self.sender, self.receiver, msg)
            self.entry.delete(0, tk.END)
            self.load_messages()

    # ---------------- FILE ----------------
    def send_file(self):
        file_path = filedialog.askopenfilename()
        if file_path:
            file_name = os.path.basename(file_path)
            msg = f"[File] {file_name}"
            send_message(self.sender, self.receiver, msg)
            self.load_messages()

    # ---------------- MENU ----------------
    def show_menu(self, event):
        try:
            self.menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.menu.grab_release()

    def react(self, emoji):
        self.chat_area.insert(tk.END, f" {emoji}")

    def delete_message(self):
        self.chat_area.insert(tk.END, "\n[Message deleted]\n")

    # ---------------- TYPING ----------------
    def show_typing(self):
        self.typing_label.config(text="Typing...")
        self.after(800, lambda: self.typing_label.config(text=""))

    # ---------------- AUTO REFRESH ----------------
    def auto_refresh(self):
        self.load_messages()
        self.after(self.refresh_interval_ms, self.auto_refresh)