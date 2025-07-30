import tkinter as tk
from tkinter import scrolledtext, messagebox, filedialog
from datetime import datetime
import os
from Login_database import send_message, get_conversation, mark_messages_as_read

class ChatWindow:
    def __init__(self, master, sender, receiver):
        self.master = master
        self.sender = sender
        self.receiver = receiver
        self.master.title(f"Chat with {receiver}")
        self.master.geometry("738x1705")

        # Chat display area
        self.chat_area = scrolledtext.ScrolledText(master, wrap=tk.WORD, font=('Arial', 11))
        self.chat_area.pack(fill="both", expand=False)
        self.chat_area.config(state=tk.DISABLED)

        # Typing label
        self.typing_label = tk.Label(master, text="", font=('Arial', 8), fg='grey')
        self.typing_label.pack()

        # Entry box for typing
        self.entry = tk.Entry(master, font=('Arial', 12))
        self.entry.pack(padx=10, pady=5, fill=tk.X)
        self.entry.bind("<Return>", self.send_msg)
        self.entry.bind("<Key>", lambda e: self.show_typing())

        # Buttons Frame
        btn_frame = tk.Frame(master)
        btn_frame.pack(pady=5)

        tk.Button(btn_frame, text="Send", width=10, command=self.send_msg).grid(row=0, column=0, padx=5)
        tk.Button(btn_frame, text="Send File", width=10, command=self.send_file).grid(row=0, column=1, padx=5)

        # Load past messages
        self.load_messages()

        # Auto-refresh every 5 seconds
        self.refresh_interval_ms = 5000
        self.master.after(self.refresh_interval_ms, self.auto_refresh)

    def load_messages(self):
        mark_messages_as_read(self.receiver, self.sender)  # Mark unread messages as read

        messages = get_conversation(self.sender, self.receiver)  # Load conversation history

        self.chat_area.config(state=tk.NORMAL)
        self.chat_area.delete(1.0, tk.END)  # Clear previous chat

        for msg in messages:  # Display each message with formatting
            sender, message, time = msg
            formatted_time = datetime.strptime(time, "%Y-%m-%d %H:%M:%S").strftime("%b %d, %I:%M %p")
            formatted = f"[{formatted_time}] {sender}: {message}\n"

            tag = "me" if sender == self.sender else "them"  # Apply tag styling
            self.chat_area.insert(tk.END, formatted, tag)

        # Chat color tags
        self.chat_area.tag_config("me", foreground="blue")
        self.chat_area.tag_config("them", foreground="green")

        self.chat_area.config(state=tk.DISABLED)
        self.chat_area.yview(tk.END)  # Auto-scroll to bottom

    def send_msg(self, event=None):
        msg = self.entry.get().strip()
        if msg:
            msg = self.parse_emojis(msg)
            send_message(self.sender, self.receiver, msg)
            self.entry.delete(0, tk.END)
            self.load_messages()

    def show_typing(self):
        self.typing_label.config(text=f"{self.sender} is typing...")
        self.master.after(1000, lambda: self.typing_label.config(text=""))

    def auto_refresh(self):
        self.load_messages()
        self.master.after(self.refresh_interval_ms, self.auto_refresh)

    def parse_emojis(self, msg):
        emoji_map = {":)": "😊", ":(": "😢", ":D": "😄"}
        for key, val in emoji_map.items():
            msg = msg.replace(key, val)
        return msg

    def send_file(self):
        file_path = filedialog.askopenfilename()
        if file_path:
            file_name = os.path.basename(file_path)
            file_msg = f"[File] {file_name} | Path: {file_path}"
            send_message(self.sender, self.receiver, file_msg)
            self.load_messages()

def start_chat(root, user, friend_username):
    try:
        win = tk.Toplevel(root)
        ChatWindow(win, user, friend_username)
    except Exception as e:
        messagebox.showerror("Chat Error", f"Cannot open chat: {e}")
