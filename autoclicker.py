import random
import time
import win32api
import win32con
import tkinter as tk
import pystray
from tkinter import Tk, ttk
from datetime import datetime
import base64
import queue
import threading
import os
from PIL import Image, ImageTk
from pynput import keyboard
import assets.base64_resource_strings as brs


class AutoClickerGUI(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.master: Tk = master
        self.master.title('Auto Clicker')
        self.SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
        self.ICON_PATH = os.path.join(
            self.SCRIPT_DIR, 'assets', 'icon.ico')
        self.ICON_BYTES = base64.b64decode(brs.icon_base64_string)
        self.initialize_dependencies()
        master.protocol("WM_DELETE_WINDOW", self.stop_and_close)
        self.log_text_queue = queue.Queue()
        self.message_timer = None
        self.message_lock = threading.Lock()
        self.MESSAGE_FLUSH_INTERVAL = 1
        self.MAX_LOG_LINES = 1000
        self.DEFAULT_HOTKEY_COMBINATION = {keyboard.Key.ctrl_l,
                                           keyboard.Key.shift, keyboard.KeyCode(char='`')}
        self.running = False
        self.interval = 87.00
        self.create_widgets()
        self.pack()
        self.autoclick_thread = threading.Thread(target=self.autoclick_loop)
        self.autoclick_thread.start()
        self.log_text_thread = threading.Thread(
            target=self.log_text_update_loop)
        self.log_text_thread.daemon = True
        self.log_text_thread.start()
        self.after(self.MESSAGE_FLUSH_INTERVAL * 1000, self.flush_messages)

    def initialize_dependencies(self):
        try:
            with open(self.ICON_PATH, 'wb') as f:
                f.write(self.ICON_BYTES)

            # Load the icon file using PIL's ImageTk.PhotoImage
            self.icon_image = Image.open(self.ICON_PATH)
            self.icon_photo = ImageTk.PhotoImage(self.icon_image)

            self.menu = pystray.Menu(
                pystray.MenuItem('Quit', self.on_menu_quit))
            self.icon = pystray.Icon(
                'Auto Clicker', icon=self.icon_image, menu=self.menu)
            self.tray_icon_thread = threading.Thread(
                target=self.run_tray_icon)
            self.tray_icon_thread.start()

            self.master.iconphoto(True, self.icon_photo)
            self.master.iconbitmap(self.ICON_PATH)
        except Exception as e:
            print(f"Error setting icon: {e}")

    def on_menu_quit(valueA, valueB, valueC, *args, **kwargs):
        print(f"on_menu_quit({valueA}, {valueB}, {valueC}, {args}, {kwargs})")
        # on_menu_quit(.!autoclickergui, <pystray._win32.Icon object at 0x00000222B6638F90>, Quit, (), {})

    def create_widgets(self):
        style = ttk.Style()
        style.theme_use('clam')
        self.configure(background='#202123')
        style.configure('TLabel', font=('Roboto', 10),
                        foreground='#ffffff', background='#202123', borderwidth=0)
        style.configure('TButton', font=('Roboto', 10),
                        foreground='#ffffff', background='#343541', borderwidth=0)
        style.configure('TScale', font=('Roboto', 10),
                        foreground='#ffffff', background='#343541', borderwidth=0)
        style.map('TButton', background=[('active', '#565869')])
        style.map('TScale', background=[('active', '#565869')])
        self.log_text = tk.Text(self, height=10, width=50, wrap='none', background='#444654', foreground='#ffffff', font=(
            'Roboto', 10), borderwidth=0, highlightthickness=0, padx=10, pady=10)
        self.log_text.tag_configure(
            'green', background='green', foreground='#333333')
        self.log_text.tag_configure(
            'red', background='red', foreground='#333333')
        self.log_text.tag_configure(
            'orange', background='orange', foreground='#333333')
        self.log_text.tag_configure(
            'blue', background='blue', foreground='#333333')
        self.log_text.tag_configure(
            'yellow', background='yellow', foreground='#333333')
        self.log_text.tag_configure(
            'white', background='white', foreground='#333333')
        self.log_text.bind("<Key>", lambda event: "break")
        self.log_text_insert('end', "Auto Clicker", 'white')
        self.log_scrollbar = ttk.Scrollbar(self, orient='vertical')
        self.log_text.configure(
            yscrollcommand=self.log_scrollbar.set, background='#444654')
        self.log_scrollbar.config(command=self.log_text.yview)
        self.current_hotkey_label = ttk.Label(
            self, text=f"Current hotkey: {'+'.join([str(key).replace('Key.', '').replace('_', ' ').title() if not hasattr(key, 'char') else key.char.upper() for key in self.DEFAULT_HOTKEY_COMBINATION])}")
        self.interval_label = ttk.Label(
            self, text=f"Clicks per second: {1000 / self.interval:.2f} / 11.60", width=30, anchor="center")
        self.click_rate_scale = ttk.Scale(
            self, from_=870, to=87, orient='horizontal', length=200, command=self.on_scale_move)
        self.hotkey_button = ttk.Button(
            self, text='Set Hotkey', command=self.set_hotkey)
        self.toggle_button = ttk.Button(
            self, text='Start', command=self.toggle_autoclicker)
        self.log_scrollbar.pack(side='right', fill='y')
        self.log_text.pack(side='right', fill='both', expand=True)
        self.current_hotkey_label.pack(side='top', pady=5)
        self.hotkey_button.pack(side='top', pady=5, padx=5)
        self.interval_label.pack(side='top', pady=10)
        self.click_rate_scale.pack(side='top')
        self.toggle_button.pack(side='bottom', padx=10, pady=10)
        self.click_rate_scale.set(87)

    def on_scale_move(self, value):
        self.interval = float(value)
        clicks_per_second = 1000 / self.interval
        self.interval_label.config(
            text=f"Clicks per second: {clicks_per_second:.2f} / 11.60",
            foreground=('red' if clicks_per_second >
                        11.48 else 'orange' if clicks_per_second > 2 else 'green')
        )
        # Cancel the previous timer
        if hasattr(self, 'scale_timer'):
            self.master.after_cancel(self.scale_timer)
        # Set a new timer to update the log text after 250ms
        self.scale_timer = self.master.after(
            250, self.update_log_text, clicks_per_second)

    def update_log_text(self, clicks_per_second):
        self.log_text_insert('end', f"Clicks per second: {clicks_per_second:.2f} / 11.60",
                             'red' if clicks_per_second > 11.48 else 'orange' if clicks_per_second > 2 else 'green')

    def run_tray_icon(self):
        try:
            self.icon.run()
        except Exception as e:
            print(f"Error running tray icon: {e}")

    def stop_and_close(self):
        self._stop_autoclick_thread()  # Stop the auto-clicking loop
        self.master.destroy()    # Close the window

    def set_hotkey(self):
        self.log_text_insert(
            'end', 'HOTKEYS DON\'T WORK, SORRY BOYOS. TODO', 'white')

    def on_hotkey_pressed(self):
        self.toggle_autoclicker()
        self.log_text_insert(
            'end', f"Hotkey pressed: {'+'.join(self.DEFAULT_HOTKEY_COMBINATION)}", 'white')

    def toggle_autoclicker(self):
        self.running = not self.running
        self.toggle_button["state"] = "disabled"
        self.toggle_button.config(text='Stop' if self.running else 'Start')
        if self.running:
            self.toggle_button["state"] = "disabled"
            self.toggle_button.configure(text='Action in progress')
            self.log_text_insert('end', 'Starting countdown', 'green')
            self.autoclick_thread = threading.Thread(
                target=self.countdown_and_start_autoclick)
            self.autoclick_thread.start()
        else:
            self._stop_autoclick_thread()
            self.log_text_insert('end', 'Auto-clicking stopped', 'red')

    def countdown_and_start_autoclick(self):

        for i in range(5, 0, -1):
            self.log_text_insert('end', f'Starting in {i}', 'green')
            time.sleep(1)
            if not self.running:
                self.log_text_insert('end', 'Countdown cancelled', 'red')
                return
        self.toggle_button["state"] = "normal"
        self.log_text_insert('end', 'Auto-clicking started', 'green')
        try:
            self.autoclick_thread = threading.Thread(
                target=self.autoclick_loop)
            self.autoclick_thread.start()
        except Exception as e:
            self.log_text_insert(
                'end', f'Error starting auto-clicking loop: {e}', 'red')

    def _stop_autoclick_thread(self):
        try:
            if self.autoclick_thread and self.autoclick_thread.is_alive():
                self.autoclick_thread.join()
                self.autoclick_thread = None
        except Exception as e:
            self.log_text_insert(
                'end',  f'_stop_autoclick_thread except Exception as e: {e}', 'red')

    def autoclick_loop(self):
        if (self.running == False):
            return

        if (self.running == True):
            return

        start_time = time.perf_counter()
        clicks = 0

        while self.running:
            # Get the current mouse position
            x, y = win32api.GetCursorPos()
            local_interval = self.interval / 1000
            human_interval = self.get_random_human_seconds()
            full_interval = local_interval + human_interval
            clicks_per_second = clicks / (time.perf_counter() - start_time)
            self.log_text_insert(
                'end', f'[Click](x={x},y={y})(c={clicks_per_second:.2f}/11.60)(ms={full_interval})', 'blue')
            # Perform a left mouse button down click
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, x, y, 0, 0)
            time.sleep(human_interval)
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, x, y, 0, 0)
            time.sleep(local_interval)
            clicks += 1

    def get_random_human_seconds(self, maximum=00.03, minimum=0.01):
        minimum = max(minimum, 00.01)
        maximum = max(maximum, 00.03)
        if minimum > maximum:
            minimum, maximum = maximum, minimum
        random_seconds = random.uniform(minimum, maximum)
        return random_seconds

    def log_text_insert(self, index, chars, tagName=None):
        self.log_text_queue.put((index, chars, tagName))

    def log_text_update_loop(self):
        while True:
            # Wait for a new message to arrive on the queue.
            index, chars, tagName = self.log_text_queue.get()
            self.log_text_insert_unsafe(index, chars, tagName)
            self.schedule_message_flush()

    def schedule_message_flush(self):
        with self.message_lock:
            if self.message_timer is None:
                self.message_timer = threading.Timer(
                    self.MESSAGE_FLUSH_INTERVAL, self.flush_messages)
                self.message_timer.start()

    def flush_messages(self):
        messages = []
        while not self.log_text_queue.empty():
            messages.append(self.log_text_queue.get())

        if len(messages) > 0:
            self.log_text.configure(state='normal')
            for index, chars, tagName in messages:
                self.log_text_insert_unsafe(index, chars, tagName)
            self.log_text.configure(state='disabled')

        # Schedule the next message flush.
        self.after(self.MESSAGE_FLUSH_INTERVAL * 1000, self.flush_messages)

    def log_text_insert_unsafe(self, index, chars, tagName=None):
        try:
            lines = chars.split('\n')
            for i, line in enumerate(lines):
                self.log_text.insert(
                    index, datetime.now().strftime('[%H:%M:%S.%f]'), tagName)
                self.log_text.insert(index, ' ')
                self.log_text.insert(index, line)
                self.log_text.insert(index, '\n')
        except Exception as e:
            print(f"Error inserting text: {e}")

        num_lines = float(self.log_text.index('end-1c').split('.')[0])
        if num_lines > self.MAX_LOG_LINES:
            max_index = f'{num_lines - self.MAX_LOG_LINES}.0'
            self.log_text.delete('1.0', max_index)
        elif num_lines == self.MAX_LOG_LINES:
            self.log_text.delete('1.0', 'end-1l')

        self.log_text.see('end')


def main():
    root = tk.Tk()
    app = AutoClickerGUI(master=root)
    app.mainloop()


if __name__ == '__main__':
    main()
