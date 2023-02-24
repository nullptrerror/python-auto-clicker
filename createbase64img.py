import tkinter as tk
from tkinter import filedialog, messagebox
import base64
import json
import os
import re


class ImageEncoder:
    def __init__(self):
        self.script_directory = os.path.abspath(os.path.dirname(__file__))
        self.filename_validator = FilenameValidator()

    def create_base64_image(self, image_path, script_filename, encoding='utf-8'):
        try:
            with open(image_path, 'rb') as f:
                image_data = f.read()
            base64_string = repr(base64.b64encode(image_data).decode(encoding))

            name, ext = self.sanitize_script_filename(script_filename)
            script_path = os.path.join(
                self.script_directory, 'assets', name + "." + ext)
            with open(script_path, 'w') as f:
                f.write(f"{name}_base64_string = {base64_string}")
        except FileNotFoundError as e:
            messagebox.showerror('Error', f'Error loading image: {e}')
        except Exception as e:
            messagebox.showerror('Error', f'Error encoding image: {e}')
        finally:
            f.close()

    def sanitize_script_filename(self, filename):
        # Remove any characters that are not letters, digits, or underscores
        filename = re.sub(r'[^\w\d_]', '', filename)

        # If the resulting string is empty, use a default name
        if not filename:
            filename = 'script'

        # Split the file name and extension
        name, ext = os.path.splitext(filename)

        # If the extension is not .py, add it
        if ext != '.py':
            ext = 'py'

        # Make sure the file name is a valid Python identifier
        if not re.match(r'^[a-zA-Z_]\w*$', name):
            name = f"_{name}"

        return name, ext

    def encode_image(self, image_path, script_filename):
        if not self.filename_validator.is_valid_script_filename(script_filename):
            messagebox.showerror(
                'Error', 'Invalid file name. Please enter a valid Python identifier and a valid Windows file name')
            return

        self.create_base64_image(image_path, script_filename)
        messagebox.showinfo(
            'Success', f'Image encoded and saved to {os.path.join(self.script_directory, "assets", script_filename)}')


class FilenameValidator:
    def is_valid_script_filename(self, filename):
        # Make sure the file name is a valid Python identifier
        if not re.match(r'^[a-zA-Z_]\w*$', filename.split('.')[0]):
            return False

        # Make sure the file name is a valid Windows file name
        try:
            os.path.basename(filename)
        except:
            return False

        return True


class ImageEncoderUI:
    def __init__(self, image_encoder):
        self.image_encoder = image_encoder
        self.image_path = None

        self.root = tk.Tk()
        self.root.title("Image Encoder")
        self.root.geometry("400x300")
        self.root.configure(bg="#424242")

        self.title_label = tk.Label(self.root, text="Select an image to encode", font=(
            "Roboto", 16), fg="#ffffff", bg="#424242")
        self.title_label.pack(pady=10)

        self.select_button = tk.Button(self.root, text="Select Image", font=(
            "Roboto", 12), fg="#ffffff", bg="#757575", command=self.select_image)
        self.select_button.pack(pady=10)

        self.filename_entry = tk.Entry(self.root, font=(
            "Roboto", 12), bg="#757575", fg="#ffffff", insertbackground="#ffffff")
        self.filename_entry.pack(pady=10)
        self.filename_entry.insert(0, "Enter a filename for the encoded image")
        self.filename_entry.bind("<FocusIn>", self.clear_filename_entry)

        self.encode_button = tk.Button(self.root, text="Encode Image", font=(
            "Roboto", 12), fg="#ffffff", bg="#757575", command=self.encode_image, state=tk.DISABLED)
        self.encode_button.pack(pady=10)

    def start(self):
        self.root.mainloop()

    def select_image(self):
        self.image_path = filedialog.askopenfilename(title="Select an Image", filetypes=(
            ("Image files", "*.jpg;*.jpeg;*.png;*.bmp;*.ico"), ("All files", "*.*")))
        if self.image_path:
            self.image_selected = True
            self.enable_filename_entry()

    def enable_filename_entry(self):
        self.filename_entry.config(state=tk.NORMAL)

    def encode_image(self):
        script_filename = self.filename_entry.get()
        self.image_encoder.encode_image(self.image_path, script_filename)

    def on_filename_entry_changed(self, *args):
        if self.filename_entry.get():
            self.enable_encode_button()
        else:
            self.disable_encode_button()

    def clear_filename_entry(self, event):
        self.filename_entry.delete(0, tk.END)

    def enable_encode_button(self):
        self.encode_button.config(state=tk.NORMAL)

    def disable_encode_button(self):
        self.encode_button.config(state=tk.DISABLED)


if __name__ == '__main__':
    encoder = ImageEncoder()
    ui = ImageEncoderUI(encoder)
    ui.filename_entry.bind("<KeyRelease>", ui.on_filename_entry_changed)
    ui.start()
