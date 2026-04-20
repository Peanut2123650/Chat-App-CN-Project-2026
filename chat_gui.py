import socket
import threading
import sys
import tkinter as tk
from datetime import datetime

HOST = '127.0.0.1'
PORT = 12345

# ── Colour palette ───────────────────────────────────────────
BG_DARK       = "#0d1117"
BG_PANEL      = "#161b22"
BG_INPUT      = "#21262d"
BG_BUBBLE_ME  = "#1f6feb"
BG_BUBBLE_OT  = "#21262d"
BG_PRIVATE    = "#3d1f6f"

ACCENT        = "#1f6feb"
ACCENT_HOVER  = "#388bfd"
ACCENT_SEND   = "#238636"
ACCENT_SEND_H = "#2ea043"

TEXT_PRIMARY   = "#e6edf3"
TEXT_SECONDARY = "#8b949e"
TEXT_MUTED     = "#484f58"
TEXT_PRIVATE   = "#c9a7f0"
TEXT_SYSTEM    = "#6e7681"
TEXT_WHITE     = "#ffffff"

BORDER        = "#30363d"
ONLINE_DOT    = "#3fb950"

FONT_MAIN  = ("Segoe UI", 11)
FONT_BOLD  = ("Segoe UI", 11, "bold")
FONT_SMALL = ("Segoe UI", 9)
FONT_TITLE = ("Segoe UI", 13, "bold")
FONT_CODE  = ("Consolas", 10)
FONT_NAME  = ("Segoe UI", 10, "bold")
FONT_TIME  = ("Segoe UI", 8)


class ChatApp:
    def __init__(self, root):
        self.root = root
        self.client = None
        self.username = None
        self.stop_event = threading.Event()
        self.online_users = []

        self.root.title("TCP Chat")
        self.root.geometry("900x620")
        self.root.minsize(680, 480)
        self.root.configure(bg=BG_DARK)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        self._build_login()

    # ── LOGIN ────────────────────────────────────────────────
    def _build_login(self):
        self.login_frame = tk.Frame(self.root, bg=BG_DARK)
        self.login_frame.place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(self.login_frame, text="💬", font=("Segoe UI Emoji", 36),
                 bg=BG_DARK, fg=TEXT_PRIMARY).pack(pady=(0, 6))
        tk.Label(self.login_frame, text="TCP Chat", font=("Segoe UI", 24, "bold"),
                 bg=BG_DARK, fg=TEXT_PRIMARY).pack()
        tk.Label(self.login_frame, text="Connect to a chat server",
                 font=FONT_MAIN, bg=BG_DARK, fg=TEXT_SECONDARY).pack(pady=(4, 24))

        card = tk.Frame(self.login_frame, bg=BG_PANEL, padx=28, pady=24,
                        highlightbackground=BORDER, highlightthickness=1)
        card.pack()

        def field(label, var):
            tk.Label(card, text=label, font=("Segoe UI", 9, "bold"),
                     bg=BG_PANEL, fg=TEXT_SECONDARY).pack(anchor="w")
            e = tk.Entry(card, textvariable=var, font=FONT_MAIN,
                         bg=BG_INPUT, fg=TEXT_PRIMARY, insertbackground=TEXT_PRIMARY,
                         relief=tk.FLAT, width=26,
                         highlightbackground=BORDER, highlightthickness=1)
            e.pack(fill=tk.X, ipady=7, pady=(3, 12))
            return e

        self.host_var     = tk.StringVar(value=HOST)
        self.port_var     = tk.StringVar(value=str(PORT))
        self.username_var = tk.StringVar()

        field("Server Host", self.host_var)
        field("Port", self.port_var)
        self.username_entry = field("Username", self.username_var)

        self.login_error = tk.Label(card, text="", font=FONT_SMALL,
                                    bg=BG_PANEL, fg="#f85149")
        self.login_error.pack(anchor="w", pady=(0, 12))

        self.connect_btn = tk.Button(card, text="Connect →",
                                     font=("Segoe UI", 11, "bold"),
                                     bg=ACCENT, fg=TEXT_WHITE, relief=tk.FLAT,
                                     activebackground=ACCENT_HOVER,
                                     activeforeground=TEXT_WHITE,
                                     cursor="hand2", command=self._connect,
                                     padx=20, pady=8)
        self.connect_btn.pack(fill=tk.X)

        self.username_entry.bind("<Return>", lambda e: self._connect())
        self.username_entry.focus_set()

    # ── CONNECT ──────────────────────────────────────────────
    def _connect(self):
        host     = self.host_var.get().strip()
        username = self.username_var.get().strip()
        try:
            port = int(self.port_var.get().strip())
        except ValueError:
            self.login_error.config(text="Invalid port number.")
            return
        if not username:
            self.login_error.config(text="Username cannot be empty.")
            return
        if len(username) > 20:
            self.login_error.config(text="Username too long (max 20 chars).")
            return
        if " " in username:
            self.login_error.config(text="No spaces in username.")
            return

        self.connect_btn.config(text="Connecting...", state=tk.DISABLED)
        self.login_error.config(text="")
        threading.Thread(target=self._do_connect,
                         args=(host, port, username), daemon=True).start()

    def _do_connect(self, host, port, username):
        try:
            self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client.connect((host, port))
        except Exception as e:
            self.root.after(0, lambda: self._login_err(f"Cannot connect: {e}"))
            return

        try:
            while True:
                msg = self.client.recv(1024).decode()
                if msg == "USERNAME":
                    self.client.send(username.encode())
                elif msg.startswith("USERNAME_ERR:"):
                    err = msg[len("USERNAME_ERR:"):]
                    self.root.after(0, lambda e=err: self._login_err(e))
                    self.client.close()
                    return
                else:
                    break
        except Exception as e:
            self.root.after(0, lambda: self._login_err(f"Handshake failed: {e}"))
            return

        self.username = username
        self.root.after(0, self._launch_chat)

    def _login_err(self, msg):
        self.login_error.config(text=msg)
        self.connect_btn.config(text="Connect →", state=tk.NORMAL)
        if self.client:
            try:
                self.client.close()
            except:
                pass
            self.client = None

    # ── CHAT UI ──────────────────────────────────────────────
    def _launch_chat(self):
        self.login_frame.destroy()
        self.root.title(f"TCP Chat — {self.username}")
        self._build_chat_ui()
        threading.Thread(target=self._receive_loop, daemon=True).start()
        self.root.after(300, self._request_user_list)
        self._system_message(
            f"Connected as {self.username}. Type /help for commands.")
        self.msg_entry.focus_set()

    def _build_chat_ui(self):
        # Top bar
        topbar = tk.Frame(self.root, bg=BG_PANEL, height=50,
                          highlightbackground=BORDER, highlightthickness=1)
        topbar.pack(fill=tk.X, side=tk.TOP)
        topbar.pack_propagate(False)

        tk.Label(topbar, text="💬  TCP Chat", font=FONT_TITLE,
                 bg=BG_PANEL, fg=TEXT_PRIMARY).pack(
                     side=tk.LEFT, padx=18, pady=12)

        sf = tk.Frame(topbar, bg=BG_PANEL)
        sf.pack(side=tk.RIGHT, padx=18)
        tk.Label(sf, text="●", font=("Segoe UI", 10),
                 bg=BG_PANEL, fg=ONLINE_DOT).pack(side=tk.LEFT)
        tk.Label(sf, text=f"  {self.username}",
                 font=FONT_BOLD, bg=BG_PANEL,
                 fg=TEXT_PRIMARY).pack(side=tk.LEFT)

        # Body: sidebar on left, chat column on right
        # Use grid so the input bar is pinned to the bottom of the chat column
        body = tk.Frame(self.root, bg=BG_DARK)
        body.pack(fill=tk.BOTH, expand=True)
        body.grid_columnconfigure(1, weight=1)
        body.grid_rowconfigure(0, weight=1)

        # ── Sidebar ──────────────────────────────────────────
        sidebar = tk.Frame(body, bg=BG_PANEL, width=185,
                           highlightbackground=BORDER, highlightthickness=1)
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.pack_propagate(False)

        tk.Label(sidebar, text="ONLINE",
                 font=("Segoe UI", 8, "bold"),
                 bg=BG_PANEL, fg=TEXT_MUTED).pack(
                     anchor="w", padx=14, pady=(14, 4))

        self.users_frame = tk.Frame(sidebar, bg=BG_PANEL)
        self.users_frame.pack(fill=tk.X, padx=6)

        tk.Frame(sidebar, bg=BORDER, height=1).pack(
            fill=tk.X, padx=14, pady=10)

        tk.Label(sidebar, text="COMMANDS",
                 font=("Segoe UI", 8, "bold"),
                 bg=BG_PANEL, fg=TEXT_MUTED).pack(
                     anchor="w", padx=14, pady=(0, 6))

        for cmd, desc in [
            ("/list",              "show users"),
            ("/msg <user> <msg>",  "private"),
            ("/help",              "all commands"),
            ("/exit",              "disconnect"),
        ]:
            f = tk.Frame(sidebar, bg=BG_PANEL)
            f.pack(fill=tk.X, padx=14, pady=2)
            tk.Label(f, text=cmd, font=FONT_CODE,
                     bg=BG_PANEL, fg=ACCENT, anchor="w").pack(anchor="w")
            tk.Label(f, text=desc, font=("Segoe UI", 8),
                     bg=BG_PANEL, fg=TEXT_MUTED, anchor="w").pack(anchor="w")

        # ── Chat column ───────────────────────────────────────
        chat_col = tk.Frame(body, bg=BG_DARK)
        chat_col.grid(row=0, column=1, sticky="nsew")

        # grid inside chat_col: row 0 = messages (expands), row 1 = input (fixed)
        chat_col.grid_rowconfigure(0, weight=1)
        chat_col.grid_rowconfigure(1, weight=0)
        chat_col.grid_columnconfigure(0, weight=1)

        # Messages canvas
        msg_area = tk.Frame(chat_col, bg=BG_DARK)
        msg_area.grid(row=0, column=0, sticky="nsew")

        self.chat_canvas = tk.Canvas(msg_area, bg=BG_DARK,
                                     highlightthickness=0, bd=0)
        sb = tk.Scrollbar(msg_area, orient=tk.VERTICAL,
                          command=self.chat_canvas.yview,
                          bg=BG_PANEL, troughcolor=BG_DARK, width=8)
        self.chat_canvas.configure(yscrollcommand=sb.set)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        self.chat_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.messages_frame = tk.Frame(self.chat_canvas, bg=BG_DARK)
        self.canvas_window = self.chat_canvas.create_window(
            (0, 0), window=self.messages_frame, anchor="nw")

        self.messages_frame.bind("<Configure>", self._on_frame_configure)
        self.chat_canvas.bind("<Configure>", self._on_canvas_configure)
        self.chat_canvas.bind("<MouseWheel>", self._on_mousewheel)
        self.messages_frame.bind("<MouseWheel>", self._on_mousewheel)

        # Input bar — pinned to bottom via grid row 1
        input_bar = tk.Frame(chat_col, bg=BG_PANEL, height=58,
                             highlightbackground=BORDER, highlightthickness=1)
        input_bar.grid(row=1, column=0, sticky="ew")
        input_bar.pack_propagate(False)

        inner = tk.Frame(input_bar, bg=BG_INPUT,
                         highlightbackground=BORDER, highlightthickness=1)
        inner.pack(fill=tk.X, padx=14, pady=10)

        self.msg_entry = tk.Entry(inner, font=FONT_MAIN, bg=BG_INPUT,
                                  fg=TEXT_PRIMARY,
                                  insertbackground=TEXT_PRIMARY,
                                  relief=tk.FLAT, bd=0)
        self.msg_entry.pack(side=tk.LEFT, fill=tk.BOTH,
                            expand=True, ipady=7, padx=(10, 6))
        self.msg_entry.bind("<Return>", lambda e: self._send())

        self.send_btn = tk.Button(inner, text="Send",
                                  font=("Segoe UI", 10, "bold"),
                                  bg=ACCENT_SEND, fg=TEXT_WHITE,
                                  relief=tk.FLAT,
                                  activebackground=ACCENT_SEND_H,
                                  activeforeground=TEXT_WHITE,
                                  cursor="hand2", command=self._send,
                                  padx=14, pady=5)
        self.send_btn.pack(side=tk.RIGHT, padx=(0, 4))

    # ── SIDEBAR ──────────────────────────────────────────────
    def _update_users_sidebar(self, users):
        for w in self.users_frame.winfo_children():
            w.destroy()
        for u in users:
            row = tk.Frame(self.users_frame, bg=BG_PANEL)
            row.pack(fill=tk.X, pady=2)
            tk.Label(row, text="●", font=("Segoe UI", 8),
                     bg=BG_PANEL, fg=ONLINE_DOT).pack(side=tk.LEFT, padx=(6, 4))
            col = ACCENT if u == self.username else TEXT_PRIMARY
            tk.Label(row, text=u, font=FONT_MAIN,
                     bg=BG_PANEL, fg=col).pack(side=tk.LEFT)
            if u == self.username:
                tk.Label(row, text=" (you)", font=FONT_SMALL,
                         bg=BG_PANEL, fg=TEXT_MUTED).pack(side=tk.LEFT)

    # ── MESSAGE RENDERING ────────────────────────────────────
    def _add_message(self, sender, time_str, body, kind="other"):
        if kind == "system":
            self._system_message(body)
            return

        is_right = kind in ("me", "private_out")
        row = tk.Frame(self.messages_frame, bg=BG_DARK)
        row.pack(fill=tk.X, padx=12, pady=3,
                 anchor="e" if is_right else "w")

        if kind == "me":
            bbg, ncol, bcol, tcol = (BG_BUBBLE_ME, TEXT_WHITE,
                                     TEXT_WHITE, "#a8c9f8")
        elif kind in ("private_in", "private_out"):
            bbg, ncol, bcol, tcol = (BG_PRIVATE, TEXT_PRIVATE,
                                     TEXT_PRIMARY, "#9d71c8")
        else:
            bbg, ncol, bcol, tcol = (BG_BUBBLE_OT, ACCENT_HOVER,
                                     TEXT_PRIMARY, TEXT_MUTED)

        bubble = tk.Frame(row, bg=bbg,
                          highlightbackground=BORDER, highlightthickness=1)
        bubble.pack(side=tk.RIGHT if is_right else tk.LEFT, padx=4)

        header = tk.Frame(bubble, bg=bbg)
        header.pack(fill=tk.X, padx=10, pady=(6, 2))
        if sender:
            tk.Label(header, text=sender, font=FONT_NAME,
                     bg=bbg, fg=ncol).pack(side=tk.LEFT)
        if time_str:
            tk.Label(header, text=time_str, font=FONT_TIME,
                     bg=bbg, fg=tcol).pack(side=tk.RIGHT, padx=(8, 0))

        tk.Label(bubble, text=body, font=FONT_MAIN, bg=bbg, fg=bcol,
                 wraplength=400, justify=tk.LEFT,
                 anchor="w").pack(padx=10, pady=(0, 8), anchor="w")

        self._scroll_to_bottom()

    def _system_message(self, text):
        row = tk.Frame(self.messages_frame, bg=BG_DARK)
        row.pack(fill=tk.X, padx=20, pady=4)
        tk.Label(row, text=text, font=("Segoe UI", 9, "italic"),
                 bg=BG_DARK, fg=TEXT_SYSTEM).pack()
        self._scroll_to_bottom()

    def _parse_and_display(self, raw):
        # /list response
        if raw.startswith("Active users:"):
            users = [u.strip()
                     for u in raw[len("Active users:"):].split(",")
                     if u.strip()]
            self.online_users = users
            self._update_users_sidebar(users)
            return

        # Private received: [HH:MM] [Private] sender: body
        if "[Private]" in raw and "[Private to" not in raw:
            try:
                time_part = raw[1:6]
                rest = raw[9:].replace("[Private] ", "", 1)
                sender, body = rest.split(": ", 1)
                self._add_message(f"🔒 {sender}", time_part,
                                  body, kind="private_in")
            except:
                self._system_message(raw)
            return

        # Private confirmation: [HH:MM] [Private to user]: body
        if "[Private to" in raw:
            try:
                time_part = raw[1:6]
                rest = raw[9:]
                header, body = rest.split("]: ", 1)
                self._add_message(f"🔒 {header}]", time_part,
                                  body, kind="private_out")
            except:
                self._system_message(raw)
            return

        # Normal message: [HH:MM] username: body
        if raw.startswith("[") and ": " in raw:
            try:
                time_part = raw[1:6]
                rest = raw[8:]
                sender, body = rest.split(": ", 1)
                kind = "me" if sender == self.username else "other"
                self._add_message(sender, time_part, body, kind=kind)
                return
            except:
                pass

        self._system_message(raw)

    # ── RECEIVE LOOP ─────────────────────────────────────────
    def _receive_loop(self):
        while not self.stop_event.is_set():
            try:
                message = self.client.recv(1024).decode()
                if not message:
                    break
                if message == "Disconnecting...":
                    self.root.after(0, lambda: self._system_message(
                        "Disconnected from server."))
                    self.stop_event.set()
                    break
                if ("joined the chat" in message
                        or "left the chat" in message):
                    self.root.after(200, self._request_user_list)
                self.root.after(0, lambda m=message: self._parse_and_display(m))
            except:
                if not self.stop_event.is_set():
                    self.root.after(0, lambda: self._system_message(
                        "Connection lost."))
                self.stop_event.set()
                break

    def _request_user_list(self):
        try:
            self.client.send("/list".encode())
        except:
            pass

    # ── SEND ─────────────────────────────────────────────────
    def _send(self):
        msg = self.msg_entry.get().strip()
        if not msg:
            return
        self.msg_entry.delete(0, tk.END)
        try:
            self.client.send(msg.encode())
        except:
            self._system_message("Failed to send message.")
            return

        if not msg.startswith("/"):
            time_str = datetime.now().strftime("%H:%M")
            self._add_message(self.username, time_str, msg, kind="me")
        elif msg == "/exit":
            self.stop_event.set()
            self.root.after(500, self.root.destroy)

    # ── CANVAS HELPERS ───────────────────────────────────────
    def _on_frame_configure(self, event):
        self.chat_canvas.configure(
            scrollregion=self.chat_canvas.bbox("all"))

    def _on_canvas_configure(self, event):
        self.chat_canvas.itemconfig(
            self.canvas_window, width=event.width)

    def _on_mousewheel(self, event):
        self.chat_canvas.yview_scroll(
            int(-1 * (event.delta / 120)), "units")

    def _scroll_to_bottom(self):
        self.root.after(50, lambda: self.chat_canvas.yview_moveto(1.0))

    # ── CLOSE ────────────────────────────────────────────────
    def _on_close(self):
        if self.client and not self.stop_event.is_set():
            try:
                self.client.send("/exit".encode())
            except:
                pass
        self.stop_event.set()
        if self.client:
            try:
                self.client.close()
            except:
                pass
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = ChatApp(root)
    root.mainloop()