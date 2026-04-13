# main.py - Entry point for the Social Media App
import tkinter as tk
from Login import LoginSignupApp
from home_screen import HomeFrame
from profile_screen import ProfileFrame
from chat_gui import ChatFrame


class MainApp(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Social Media App")
        self.state("zoomed")  # Fullscreen scalable
        self.configure(bg="#f0f0f0")

        self.current_user = None

        # Container
        self.container = tk.Frame(self)
        self.container.pack(fill="both", expand=True)

        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        self.frames = {}

        # 🔹 Initialize Frames
        for F in (LoginSignupApp, HomeFrame, ProfileFrame, ChatFrame):
            frame = F(self.container, self)
            self.frames[F.__name__] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        # ✅ FIX HERE
        self.show_frame("LoginSignupApp")

    def show_frame(self, name, **kwargs):
        if name not in self.frames:
            print("Available frames:", self.frames.keys())
            raise KeyError(f"{name} not found in frames")

        frame = self.frames[name]

        if hasattr(frame, "load_data"):
            frame.load_data(**kwargs)

        frame.tkraise()


if __name__ == "__main__":
    app = MainApp()
    app.mainloop()