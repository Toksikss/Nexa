from customtkinter import *
from tkinter import filedialog
from PIL import Image
import socket
import threading
import base64
import io
import time

server_ip = "127.0.0.1"
server_port = 8080


class App(CTk):
    def __init__(self):
        super().__init__()
        self.geometry('600x500')
        self.title('Nexa')
        self.username = None
        self.client_socket = None
        self.running = False
        self.reconnecting = False

        set_appearance_mode("dark")
        set_default_color_theme("blue")

        self.show_auth()

    def clear_window(self):
        for widget in self.winfo_children():
            widget.destroy()

    def show_auth(self):
        self.clear_window()
        try:
            image = Image.open("logo.png")
            ctk_image = CTkImage(light_image=image, dark_image=image, size=(300, 150))
            image_label = CTkLabel(self, image=ctk_image, text="")
            image_label.image = ctk_image
            image_label.pack(pady=(10, 10))
        except:
            CTkLabel(self, text="Nexa Chat", font=("Arial", 24)).pack(pady=(10, 10))

        self.name_entry = CTkEntry(self, placeholder_text="Ваш нік")
        self.name_entry.pack(pady=10, padx=20, fill="x")

        self.password_entry = CTkEntry(self, placeholder_text="Пароль", show="*")
        self.password_entry.pack(pady=10, padx=20, fill="x")

        CTkButton(self, text="Увійти", command=self.login).pack(pady=10)

    def connect_to_server(self):
        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((server_ip, server_port))
            self.client_socket.sendall(self.username.encode("utf-8"))
            self.running = True
            threading.Thread(target=self.receive_messages, daemon=True).start()
            return True
        except:
            return False

    def login(self):
        self.username = self.name_entry.get().strip() or "Гість"
        if not self.connect_to_server():
            self.show_auth()
            CTkLabel(self, text=f"Помилка підключення до сервера", text_color="red").pack()
            return
        self.show_chat()

    def show_chat(self):
        self.clear_window()


        self.chat_frame = CTkScrollableFrame(self)
        self.chat_frame.pack(padx=10, pady=10, fill="both", expand=True)

        bottom_frame = CTkFrame(self)
        bottom_frame.pack(padx=10, pady=5, fill="x")

        self.msg_entry = CTkEntry(bottom_frame, placeholder_text="Введіть повідомлення")
        self.msg_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        self.msg_entry.bind("<Return>", lambda e: self.send_message())

        CTkButton(bottom_frame, text="Фото", width=50, command=self.send_image).pack(side="right", padx=(5, 0))
        CTkButton(bottom_frame, text="▶", width=40, command=self.send_message).pack(side="right")

    def send_message(self):
        if not self.running:
            self.add_text_message("Система: Немає з'єднання з сервером!")
            return
        message = self.msg_entry.get().strip()
        if message:
            try:
                self.client_socket.sendall(message.encode("utf-8"))
                self.add_text_message(f"{self.username}: {message}")
            except:
                self.add_text_message("Система: Помилка відправки!")
        self.msg_entry.delete(0, "end")

    def send_image(self):
        file_path = filedialog.askopenfilename(filetypes=[("Зображення", "*.png;*.jpg;*.jpeg")])
        if not file_path:
            return
        try:
            with open(file_path, "rb") as f:
                encoded = base64.b64encode(f.read()).decode("utf-8")
            filename = os.path.basename(file_path)
            data = f"IMG::{self.username}::{filename}::{encoded}".encode("utf-8")
            self.client_socket.sendall(data)
            self.add_image_message(file_path)
        except Exception as e:
            self.add_text_message(f"Система: Помилка відправки фото ({e})")

    def add_text_message(self, text):
        CTkLabel(self.chat_frame, text=text, anchor="w", justify="left", wraplength=500).pack(fill="x", pady=2, anchor="w")

    def add_image_message(self, img_path_or_data):
        try:
            if isinstance(img_path_or_data, bytes):
                image = Image.open(io.BytesIO(img_path_or_data))
            else:
                image = Image.open(img_path_or_data)
            image.thumbnail((300, 300))
            ctk_img = CTkImage(light_image=image, dark_image=image, size=image.size)

            img_label = CTkLabel(self.chat_frame, image=ctk_img, text="", anchor="w")
            img_label.image = ctk_img
            img_label.pack(pady=3, anchor="w")
        except Exception as e:
            self.add_text_message(f"[Помилка відображення зображення: {e}]")

    def receive_messages(self):
        while self.running:
            try:
                data = self.client_socket.recv(65536)
                if not data:
                    break
                decoded = data.decode("utf-8", errors="ignore")
                if decoded.startswith("MSG::"):
                    msg = decoded.split("::", 1)[1]
                    self.after(0, self.add_text_message, msg)
                elif decoded.startswith("IMG::"):
                    _, sender, filename, b64data = decoded.split("::", 3)
                    img_data = base64.b64decode(b64data)
                    self.after(0, self.add_image_message, img_data)
            except:
                break
        self.running = False
        self.after(0, lambda: self.add_text_message("Система: З'єднання розірвано, пробую перепідключитися..."))
        self.after(1000, self.reconnect)

    def reconnect(self):
        if self.reconnecting:
            return
        self.reconnecting = True
        for i in range(10):
            if self.connect_to_server():
                self.add_text_message("Система: Підключення відновлено!")
                self.reconnecting = False
                return
            else:
                self.add_text_message(f"Система: Спроба підключення {i+1}/10...")
                time.sleep(2)
        self.add_text_message("Система: Не вдалося перепідключитися.")
        self.reconnecting = False

    def on_close(self):
        self.running = False
        if self.client_socket:
            try:
                self.client_socket.close()
            except:
                pass
        self.destroy()


if __name__ == "__main__":
    app = App()
    app.protocol("WM_DELETE_WINDOW", app.on_close)
    app.mainloop()
