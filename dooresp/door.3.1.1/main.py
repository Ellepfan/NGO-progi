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
import psutil
from datetime import datetime


class RelayControlApp:
    def __init__(self):
        # Инициализация основных атрибутов
        self.lock_file = "app.lock"
        self.status_file = "status.json"
        self.position_file = "window_position.json"  # Файл для хранения позиции

        # Проверка на уже запущенный экземпляр
        if self.is_already_running():
            self._log_error("Программа уже запущена!")
            messagebox.showwarning("Ошибка", "Программа уже запущена!")
            sys.exit(1)

        # Основная инициализация
        self.root = tk.Tk()
        self.lock_mode = False
        self.lock_message = ""
        self.server_available = False
        self._offset_x = 0
        self._offset_y = 0
        self.button_presses = 0
        self.start_time = time.time()
        self.has_images = False

        # Создание lock-файла
        self.create_lock_file()

        # Настройка шифрования
        self.encryption_key = b'N_l4-Y_Bze4MMJDQWj9uWdjQkOSQA8MC69kvZ6ANDzA='
        self.cipher = Fernet(self.encryption_key)
        self.encrypted_url = b'gAAAAABoY4ANHsTXlnkaJpzOP1Q8bCfJ4upuGS0me0Zu1yJ5FVqe3yaqCJ4_fCJLyTkUEP96E367EemqmKjGRyIstVlBbmLONYagw_alyLL2zd8XeliHhJv8oc3wSFm4Ofx8gESRp7_4'

        # Инициализация интерфейса
        self.setup_window()
        self.load_images()
        self.setup_ui()
        self.setup_tray_icon()

        # Загрузка состояния и проверка блокировки
        self.load_last_status()
        self.check_lock_status()

        # Настройка иконки
        try:
            self.root.iconbitmap(r'.\_internal\open.ico')
        except Exception as e:
            self._log_error(f"Не удалось загрузить иконку: {e}")

        # Таймеры
        self.root.after(60000, self.periodic_lock_check)
        self.root.after(60000, self.send_uptime)

    def _log_error(self, message):
        """Логирование ошибок в файл"""
        try:
            log_dir = os.path.join('._internal', 'log')
            if not os.path.exists(log_dir):
                os.makedirs(log_dir)

            with open(os.path.join(log_dir, 'errors.log'), 'a', encoding='utf-8') as f:
                f.write(f"{datetime.now()} - {message}\n")
        except Exception as e:
            print(f"Не удалось записать в лог: {e}")

    def is_already_running(self):
        """Проверяет, запущена ли уже программа."""
        # Проверка через процессы
        current_pid = os.getpid()
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                if "python" in proc.info['name'].lower() and proc.info['pid'] != current_pid:
                    cmdline = proc.cmdline()
                    if len(cmdline) > 1 and ("main.py" in cmdline[1] or "door" in cmdline[1]):
                        return True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        # Проверка через lock-файл
        if os.path.exists(self.lock_file):
            try:
                with open(self.lock_file, "r") as f:
                    pid = int(f.read().strip())
                    if psutil.pid_exists(pid):
                        return True
            except:
                pass

        return False

    def create_lock_file(self):
        """Создает файл блокировки с текущим PID."""
        try:
            with open(self.lock_file, "w") as f:
                f.write(str(os.getpid()))
        except Exception as e:
            self._log_error(f"Ошибка создания lock-файла: {e}")

    def remove_lock_file(self):
        """Удаляет файл блокировки при выходе."""
        try:
            if os.path.exists(self.lock_file):
                os.remove(self.lock_file)
        except Exception as e:
            self._log_error(f"Ошибка удаления lock-файла: {e}")

    def setup_window(self):
        """Настройка основного окна."""
        self.root.title("")

        # Загрузка сохраненной позиции окна
        default_x, default_y = 100, 100
        if os.path.exists(self.position_file):
            try:
                with open(self.position_file, 'r') as f:
                    pos = json.load(f)
                    default_x = pos.get('x', default_x)
                    default_y = pos.get('y', default_y)
            except Exception as e:
                self._log_error(f"Ошибка загрузки позиции окна: {e}")

        self.root.geometry(f"60x40+{default_x}+{default_y}")
        self.root.resizable(False, False)
        self.root.attributes("-alpha", 0.7)
        self.root.attributes("-topmost", True)
        self.root.overrideredirect(True)
        self.root.protocol("WM_DELETE_WINDOW", self.hide_to_tray)

        self.root.bind('<Button-1>', self.start_move)
        self.root.bind('<B1-Motion>', self.on_motion)
        self.root.bind('<ButtonRelease-1>', self.save_window_position)  # Сохраняем позицию при отпускании кнопки мыши

    def save_window_position(self, event=None):
        """Сохраняет текущую позицию окна."""
        try:
            x = self.root.winfo_x()
            y = self.root.winfo_y()
            with open(self.position_file, 'w') as f:
                json.dump({'x': x, 'y': y}, f)
        except Exception as e:
            self._log_error(f"Ошибка сохранения позиции окна: {e}")

    def start_move(self, event):
        self._offset_x = event.x
        self._offset_y = event.y

    def on_motion(self, event):
        x = self.root.winfo_pointerx() - self._offset_x
        y = self.root.winfo_pointery() - self._offset_y
        self.root.geometry(f"+{x}+{y}")

    def load_images(self):
        """Загрузка изображений для интерфейса."""
        try:
            self.python_logo_on = tk.PhotoImage(file=r'.\_internal\open.png')
            self.python_logo_off = tk.PhotoImage(file=r'.\_internal\of.png')
            self.lock_image = tk.PhotoImage(file=r'.\_internal\open.png')
            self.has_images = True
        except Exception as e:
            self._log_error(f"Ошибка загрузки изображений: {e}")
            self.python_logo_on = tk.PhotoImage(width=1, height=1)
            self.python_logo_off = tk.PhotoImage(width=1, height=1)
            self.lock_image = tk.PhotoImage(width=1, height=1)
            self.has_images = False

    def setup_ui(self):
        """Настройка пользовательского интерфейса."""
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
        """Обработчик нажатия кнопки."""
        if self.server_available and self.lock_mode:
            messagebox.showwarning("Заблокировано", self.lock_message)
            return

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

            if self.server_available:
                try:
                    requests.post("http://192.168.9.51:8001/api/button_press", timeout=3)
                except Exception as e:
                    self.server_available = False
                    self._log_error(f"Ошибка отправки нажатия кнопки: {e}")
        except Exception as e:
            self._log_error(f"Ошибка запроса: {e}")
            self.btn["image"] = self.python_logo_off

    def decrypt_url(self):
        """Расшифровывает URL для запросов."""
        try:
            return self.cipher.decrypt(self.encrypted_url).decode('utf-8')
        except Exception as e:
            self._log_error(f"Ошибка дешифровки: {e}")
            return None

    def send_uptime(self):
        """Отправляет время работы на сервер."""
        uptime_minutes = int((time.time() - self.start_time) / 60)
        if self.server_available:
            try:
                requests.post(
                    "http://192.168.9.51:8001/api/client_uptime",
                    json={"minutes": uptime_minutes},
                    timeout=3
                )
            except Exception as e:
                self.server_available = False
                self._log_error(f"Ошибка отправки uptime: {e}")

        self.root.after(60000, self.send_uptime)

    def setup_tray_icon(self):
        """Настройка иконки в трее."""
        try:
            if self.has_images:
                tray_image = Image.open(r".\_internal\open.png")
            else:
                tray_image = Image.new('RGB', (16, 16), 'white')

            menu = pystray.Menu(
                pystray.MenuItem("Закрыть", self.exit_app)
            )

            self.tray_icon = pystray.Icon("relay_control", tray_image, "Дверь NGO", menu)
            threading.Thread(target=self.tray_icon.run, daemon=True).start()
        except Exception as e:
            self._log_error(f"Ошибка создания иконки в трее: {e}")

    def hide_to_tray(self):
        """Скрывает окно в трей."""
        self.save_window_position()  # Сохраняем позицию перед скрытием
        self.root.withdraw()

    def exit_app(self, icon=None, item=None):
        """Завершает работу приложения."""
        self.save_last_status()
        self.save_window_position()  # Сохраняем позицию перед выходом
        self.remove_lock_file()
        if hasattr(self, 'tray_icon'):
            self.tray_icon.stop()
        self.root.destroy()
        sys.exit()

    def load_last_status(self):
        """Загружает последнее сохраненное состояние."""
        try:
            if os.path.exists(self.status_file):
                with open(self.status_file, 'r') as f:
                    data = json.load(f)
                    self.lock_mode = data.get('lock_mode', False)
                    self.lock_message = data.get('lock_message', "")

                    if self.lock_mode:
                        self.activate_lock(self.lock_message, save=False)
                    else:
                        self.deactivate_lock(save=False)
        except Exception as e:
            self._log_error(f"Ошибка загрузки статуса: {e}")

    def save_last_status(self):
        """Сохраняет текущее состояние."""
        try:
            with open(self.status_file, 'w') as f:
                json.dump({
                    'lock_mode': self.lock_mode,
                    'lock_message': self.lock_message
                }, f)
        except Exception as e:
            self._log_error(f"Ошибка сохранения статуса: {e}")

    def check_lock_status(self, icon=None, item=None):
        """Проверяет статус блокировки на сервере."""
        try:
            response = requests.get("http://192.168.9.51:8001/api/check_lock", timeout=5)
            data = response.json()
            self.server_available = True

            if data.get("locked", False):
                self.activate_lock(data.get("message", "Приложение заблокировано"))
            else:
                self.deactivate_lock()
        except Exception as e:
            self.server_available = False
            self._log_error(f"Ошибка проверки статуса блокировки: {e}")

    def periodic_lock_check(self):
        """Периодическая проверка статуса блокировки."""
        self.check_lock_status()
        self.root.after(60000, self.periodic_lock_check)

    def activate_lock(self, message, save=True):
        """Активирует режим блокировки."""
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
        """Деактивирует режим блокировки."""
        self.lock_mode = False
        self.lock_message = ""

        self.btn.config(state='normal')
        self.btn.config(image=self.python_logo_on)
        self.lock_label.lower()

        if save:
            self.save_last_status()


if __name__ == "__main__":
    try:
        app = RelayControlApp()
        app.root.mainloop()
    except Exception as e:
        error_msg = f"Критическая ошибка: {str(e)}"
        print(error_msg)
        try:
            log_dir = os.path.join('._internal', 'log')
            if not os.path.exists(log_dir):
                os.makedirs(log_dir)
            with open(os.path.join(log_dir, 'errors.log'), 'a', encoding='utf-8') as f:
                f.write(f"{datetime.now()} - {error_msg}\n")
        except:
            pass
        messagebox.showerror("Ошибка", error_msg)