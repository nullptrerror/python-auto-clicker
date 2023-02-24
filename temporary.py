from datetime import datetime
import time
import tkinter as tk
from rx import interval
from rx.operators import throttle_first


class AutoClickerFrame(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.TK: tk.Tk = master
        self.INTERVAL_VALUE_SECONDS: float = 0.0842069420420420
        self.throttled_observable_subscription = self.update_throttled_observable_subscription_interval(
            self.INTERVAL_VALUE_SECONDS)
        self.create_widgets()

    def create_widgets(self):
        self.hi_there = tk.Button(self)
        self.hi_there["text"] = "Hello World (click me)"
        self.hi_there["command"] = self.say_hi
        self.hi_there.pack(side="top")

        self.quit = tk.Button(self, text="QUIT", fg="red",
                              command=self.master.destroy)
        self.quit.pack(side="bottom")
        self.pack()

    def say_hi(self):
        print("hi there, everyone!")

    def update_throttled_observable_subscription_interval(self, new_interval):
        # Unsubscribe from the previous subscription if it exists
        if hasattr(self, "throttled_observable_subscription"):
            self.throttled_observable_subscription.dispose()
        return interval(new_interval).subscribe(lambda x: self.log(f"x: {x}"))

    def log(self, message):
        colors = [
            "\033[1;31m",   # red
            "\033[1;33m",   # yellow
            "\033[1;32m",   # green
            "\033[1;34m",   # blue
            "\033[1;35m",   # purple
            "\033[1;36m",   # cyan
        ]

        ts = datetime.now().time()
        ts_str = ts.strftime("%H:%M:%S.%f")

        # Print the message in the console in rainbow colors each line (lol)
        print(
            f"{colors[int(ts) % len(colors)]}{ts_str} {message}\033[0m")


if __name__ == "__main__":
    root = tk.Tk()
    app = AutoClickerFrame(master=root)
    app.mainloop()
