import tkinter as tk
from tkinter import ttk, messagebox
import requests
import pystray
from PIL import Image
import threading
import sys
import time
import os
import json
from cryptography.fernet import Fernet


class RelayControlApp:
    def __init__(self):
        self.root = tk.Tk()
        self.lock_mode = False
        self.lock_message = ""
        self.server_available = False  # Флаг доступности сервера
        self._offset_x = 0
        self._offset_y = 0
        self.button_presses = 0
        self.start_time = time.time()
        self.status_file = "status.json"  # Файл для хранения статуса

        # Настройка шифрования
        self.encryption_key = b'N_l4-Y_Bze4MMJDQWj9uWdjQkOSQA8MC69kvZ6ANDzA='  # Замените на свой ключ!
        self.cipher = Fernet(self.encryption_key)

        # Зашифрованный URL (генерируется заранее)
        self.encrypted_url = b'gAAAAABoY4ANHsTXlnkaJpzOP1Q8bCfJ4upuGS0me0Zu1yJ5FVqe3yaqCJ4_fCJLyTkUEP96E367EemqmKjGRyIstVlBbmLONYagw_alyLL2zd8XeliHhJv8oc3wSFm4Ofx8gESRp7_4'  # Инструкция ниже

        self.setup_window()
        self.load_images()
        self.setup_ui()
        self.setup_tray_icon()
        self.load_last_status()  # Загружаем последний статус при запуске
        self.check_lock_status()

        # Иконка приложения
        try:
            self.root.iconbitmap('.\_internal\open.ico')
        except:
            pass

        self.root.after(60000, self.periodic_lock_check)
        self.root.after(60000, self.send_uptime)

    def decrypt_url(self):
        """Расшифровывает URL для использования в запросах."""
        try:
            return self.cipher.decrypt(self.encrypted_url).decode('utf-8')
        except Exception as e:
            print(f"Ошибка дешифровки: {e}")
            return None

    def setup_window(self):
        self.root.title("")
        self.root.geometry("60x40+100+100")
        self.root.resizable(False, False)
        self.root.attributes("-alpha", 0.7)
        self.root.attributes("-topmost", True)
        self.root.overrideredirect(True)
        self.root.protocol("WM_DELETE_WINDOW", self.hide_to_tray)

        self.root.bind('<Button-1>', self.start_move)
        self.root.bind('<B1-Motion>', self.on_motion)

    def start_move(self, event):
        self._offset_x = event.x
        self._offset_y = event.y

    def on_motion(self, event):
        x = self.root.winfo_pointerx() - self._offset_x
        y = self.root.winfo_pointery() - self._offset_y
        self.root.geometry(f"+{x}+{y}")

    def load_images(self):
        try:
            self.python_logo_on = tk.PhotoImage(file='.\_internal\open.png')
            self.python_logo_off = tk.PhotoImage(file='.\_internal\of.png')
            self.lock_image = tk.PhotoImage(file='.\_internal\open.png')
            self.has_images = True
        except:
            self.python_logo_on = tk.PhotoImage(width=1, height=1)
            self.python_logo_off = tk.PhotoImage(width=1, height=1)
            self.lock_image = tk.PhotoImage(width=1, height=1)
            self.has_images = False

    def setup_ui(self):
        self.btn = ttk.Button(
            self.root,
            image=self.python_logo_on,
            command=self.click_button
        )
        self.btn.pack(fill=tk.BOTH, expand=True)

        self.lock_label = tk.Label(
            self.root,
            text="", bg='red', fg='white',
            wraplength=200, font=('Arial', 8)
        )
        self.lock_label.place(relx=0.5, rely=0.5, anchor='center')
        self.lock_label.lower()

    def click_button(self):
        # Если сервер доступен и включен режим блокировки
        if self.server_available and self.lock_mode:
            messagebox.showwarning("Заблокировано", self.lock_message)
            return

        # Если сервер недоступен, но локальный статус показывает блокировку
        if not self.server_available and self.lock_mode:
            messagebox.showwarning("Заблокировано", "Сервер недоступен. Приложение остается заблокированным.")
            return

        try:
            decrypted_url = self.decrypt_url()
            if not decrypted_url:
                raise ValueError("Не удалось расшифровать URL")

            requests.get(decrypted_url, timeout=3)
            self.btn["image"] = self.python_logo_on
            self.button_presses += 1

            # Отправляем информацию о нажатии только если сервер доступен
            if self.server_available:
                try:
                    requests.post("http://192.168.9.51:8001/api/button_press", timeout=3)
                except Exception:
                    self.server_available = False  # Сервер стал недоступен
        except Exception as e:
            print(f"Ошибка запроса: {e}")
            self.btn["image"] = self.python_logo_off

    def send_uptime(self):
        uptime_minutes = int((time.time() - self.start_time) / 60)
        if self.server_available:  # Отправляем только если сервер доступен
            try:
                requests.post(
                    "http://192.168.9.51:8001/api/client_uptime",
                    json={"minutes": uptime_minutes},
                    timeout=3
                )
            except Exception:
                self.server_available = False  # Сервер стал недоступен

        self.root.after(60000, self.send_uptime)

    def setup_tray_icon(self):
        try:
            if self.has_images:
                tray_image = Image.open(".\_internal\open.png")
            else:
                tray_image = Image.new('RGB', (16, 16), 'white')

            menu = pystray.Menu(
                pystray.MenuItem("Закрыть", self.exit_app)
            )

            self.tray_icon = pystray.Icon("relay_control", tray_image, "Дверь NGO", menu)
            threading.Thread(target=self.tray_icon.run, daemon=True).start()
        except Exception:
            pass

    def hide_to_tray(self):
        self.root.withdraw()

    def exit_app(self, icon=None, item=None):
        self.save_last_status()  # Сохраняем статус перед выходом
        if hasattr(self, 'tray_icon'):
            self.tray_icon.stop()
        self.root.destroy()
        sys.exit()

    def load_last_status(self):
        """Загружает последний сохраненный статус из файла."""
        try:
            if os.path.exists(self.status_file):
                with open(self.status_file, 'r') as f:
                    data = json.load(f)
                    self.lock_mode = data.get('lock_mode', False)
                    self.lock_message = data.get('lock_message', "")

                    # Применяем загруженный статус
                    if self.lock_mode:
                        self.activate_lock(self.lock_message, save=False)
                    else:
                        self.deactivate_lock(save=False)
        except Exception as e:
            print(f"Ошибка загрузки статуса: {e}")

    def save_last_status(self):
        """Сохраняет текущий статус в файл."""
        try:
            with open(self.status_file, 'w') as f:
                json.dump({
                    'lock_mode': self.lock_mode,
                    'lock_message': self.lock_message
                }, f)
        except Exception as e:
            print(f"Ошибка сохранения статуса: {e}")

    def check_lock_status(self, icon=None, item=None):
        try:
            response = requests.get("http://192.168.9.51:8001/api/check_lock", timeout=5)
            data = response.json()
            self.server_available = True  # Сервер доступен

            if data.get("locked", False):
                self.activate_lock(data.get("message", "Приложение заблокировано"))
            else:
                self.deactivate_lock()
        except Exception:
            self.server_available = False  # Сервер недоступен
            # Не изменяем статус блокировки, оставляем последний известный

    def periodic_lock_check(self):
        self.check_lock_status()
        self.root.after(60000, self.periodic_lock_check)

    def activate_lock(self, message, save=True):
        self.lock_mode = True
        self.lock_message = message

        self.btn.config(state='disabled')
        if self.lock_image:
            self.btn.config(image=self.lock_image)

        self.lock_label.config(text=message)
        self.lock_label.lift()
        self.root.deiconify()
        messagebox.showwarning("Блокировка", message)

        if save:
            self.save_last_status()

    def deactivate_lock(self, save=True):
        self.lock_mode = False
        self.lock_message = ""

        self.btn.config(state='normal')
        self.btn.config(image=self.python_logo_on)
        self.lock_label.lower()

        if save:
            self.save_last_status()


if __name__ == "__main__":
    app = RelayControlApp()
    app.root.mainloop()