import tkinter as tk
from tkinter import filedialog, scrolledtext, font
from tkinter import messagebox 

class TypingTutorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Typing Practice")
        self.root.geometry("800x600")

        self.target_text_content = ""

        self.correct_bg = "light green"
        self.incorrect_bg = "light coral"
        self.text_font = font.Font(family="Consolas", size=11)

        # --- UI Elements ---
        control_frame = tk.Frame(root, pady=10)
        control_frame.pack(fill=tk.X)

        self.load_button = tk.Button(control_frame, text="Load Text File", command=self.load_file)
        self.load_button.pack(side=tk.LEFT, padx=10)

        text_frame = tk.Frame(root)
        text_frame.pack(expand=True, fill=tk.BOTH, padx=10, pady=(0, 10))

        target_label = tk.Label(text_frame, text="Target Text:")
        target_label.pack(anchor=tk.W)
        self.target_text = scrolledtext.ScrolledText(
            text_frame,
            wrap=tk.WORD,
            height=10,
            font=self.text_font,
            state=tk.DISABLED
        )
        self.target_text.pack(expand=True, fill=tk.BOTH, pady=(0, 10))

        input_label = tk.Label(text_frame, text="Your Input:")
        input_label.pack(anchor=tk.W)
        self.input_text = scrolledtext.ScrolledText(
            text_frame,
            wrap=tk.WORD,
            height=10,
            font=self.text_font
        )
        self.input_text.pack(expand=True, fill=tk.BOTH)
        self.input_text.focus()

        # --- Configure Highlighting Tags ---
        self.input_text.tag_configure("correct", background=self.correct_bg)
        self.input_text.tag_configure("incorrect", background=self.incorrect_bg)

        # --- Bind Events ---
        self.input_text.bind('<KeyRelease>', self.check_text)

    def load_file(self):
        filepath = filedialog.askopenfilename(
            title="Select Text File",
            filetypes=(("Text Files", "*.txt"),
                       ("Python Files", "*.py"),
                       ("All Files", "*.*"))
        )
        if not filepath:
            return

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                self.target_text_content = f.read()

            self.target_text.config(state=tk.NORMAL)
            self.target_text.delete("1.0", tk.END)
            self.target_text.insert("1.0", self.target_text_content)
            self.target_text.config(state=tk.DISABLED)

            self.input_text.delete("1.0", tk.END)
            self.input_text.focus()
            self.check_text()

        except Exception as e:
            # Use messagebox directly now
            messagebox.showerror("Error Loading File", f"Could not read file:\n{e}")
            self.target_text_content = ""
            self.target_text.config(state=tk.NORMAL)
            self.target_text.delete("1.0", tk.END)
            self.target_text.config(state=tk.DISABLED)
            self.input_text.delete("1.0", tk.END)


    def check_text(self, event=None):
        self.input_text.tag_remove("correct", "1.0", tk.END)
        self.input_text.tag_remove("incorrect", "1.0", tk.END)

        input_content = self.input_text.get("1.0", "end-1c")
        target_len = len(self.target_text_content)
        input_len = len(input_content)

        compare_len = min(target_len, input_len)

        for i in range(compare_len):
            start_index = f"1.0 + {i} chars"
            end_index = f"1.0 + {i+1} chars"

            if input_content[i] == self.target_text_content[i]:
                self.input_text.tag_add("correct", start_index, end_index)
            else:
                self.input_text.tag_add("incorrect", start_index, end_index)

        if input_len > target_len:
            start_index = f"1.0 + {target_len} chars"
            end_index = tk.END
            self.input_text.tag_add("incorrect", start_index, end_index)

# --- Main Execution ---
if __name__ == "__main__":
    root = tk.Tk()
    app = TypingTutorApp(root)
    root.mainloop()