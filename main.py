import tkinter as tk
from tkinter import filedialog, scrolledtext, font
from tkinter import messagebox # Import the messagebox module

class TypingTutorOverlayApp:
    def __init__(self, root_window):
        self.root = root_window
        self.root.title("Typing Practice - Overlay")
        self.root.geometry("800x600") # Set initial window size

        self.target_text_content = "" # Stores the text loaded from the file
        self.current_pos = 0 # Tracks the index of the next character the user should type

        # --- Configure Colors and Font ---
        self.faint_color = "lightgrey"      # Color for untyped text
        self.correct_color = "green"        # Color for correctly typed text
        self.incorrect_color = "#CC0000"    # A distinct red for incorrectly typed text
        # Use a monospaced font so all characters have the same width
        self.text_font = font.Font(family="Consolas", size=12)

        # --- User Interface Elements ---

        # Frame to hold the load button
        control_frame = tk.Frame(self.root, pady=10)
        control_frame.pack(fill=tk.X) # Make the frame fill the width

        # Button to load a text file
        self.load_button = tk.Button(control_frame, text="Load Text File", command=self.load_file)
        self.load_button.pack(side=tk.LEFT, padx=10)

        # The main text area where typing happens
        self.text_area = scrolledtext.ScrolledText(
            self.root,
            wrap=tk.WORD, # Wrap text by word (tk.NONE might be better for code)
            font=self.text_font,
            padx=5, # Padding inside the text area
            pady=5
        )
        # Make the text area expand to fill the window
        self.text_area.pack(expand=True, fill=tk.BOTH, padx=10, pady=(0, 10))

        # --- Configure Text Tags for Styling ---
        # A "tag" is a way to apply formatting to ranges of text
        self.text_area.tag_configure("faint", foreground=self.faint_color)
        self.text_area.tag_configure("correct", foreground=self.correct_color)
        self.text_area.tag_configure("incorrect", foreground=self.incorrect_color)
        # Optional: Make incorrect text bold for more emphasis
        # incorrect_font = font.Font(family="Consolas", size=12, weight='bold')
        # self.text_area.tag_configure("incorrect", foreground=self.incorrect_color, font=incorrect_font)

        # --- Bind Events ---
        # Bind the <KeyPress> event to our custom handler function.
        # This allows us to intercept keys before Tkinter processes them by default.
        self.text_area.bind('<KeyPress>', self.handle_keypress)

        # Prevent default behaviors that would interfere with our typing logic
        self.text_area.bind('<Button-1>', lambda event: "break") # Prevent mouse click moving cursor
        self.text_area.bind('<B1-Motion>', lambda event: "break")# Prevent mouse drag selection
        self.text_area.bind('<ButtonRelease-1>', lambda event: "break") # Prevent releasing click from doing anything
        self.text_area.bind('<Double-Button-1>', lambda event: "break") # Prevent double-click selection
        self.text_area.bind('<Triple-Button-1>', lambda event: "break") # Prevent triple-click selection
        self.text_area.bind('<Shift-Button-1>', lambda event: "break") # Prevent shift-click selection
        self.text_area.bind('<Control-Button-1>', lambda event: "break")# Prevent control-click actions

        # Prevent cutting and pasting into the widget
        self.text_area.bind("<<Cut>>", lambda event: "break")
        self.text_area.bind("<<Paste>>", lambda event: "break")

        # Prevent navigation keys from moving the cursor freely
        self.text_area.bind('<Left>', lambda event: "break")
        self.text_area.bind('<Right>', lambda event: "break")
        self.text_area.bind('<Up>', lambda event: "break")
        self.text_area.bind('<Down>', lambda event: "break")
        self.text_area.bind('<Home>', lambda event: "break")
        self.text_area.bind('<End>', lambda event: "break")
        self.text_area.bind('<Delete>', lambda event: "break") # Only allow BackSpace for deletion

        # Start the text area in a disabled state until a file is loaded
        self.text_area.config(state=tk.DISABLED)

    def load_file(self):
        """Opens a file dialog and loads text content into the text area."""
        filepath = filedialog.askopenfilename(
            title="Select Text File",
            filetypes=(("Text Files", "*.txt"),
                       ("Python Files", "*.py"),
                       ("All Files", "*.*"))
        )
        # If the user cancels the dialog, filepath will be empty
        if not filepath:
            return

        try:
            # Try reading with UTF-8 encoding first
            try:
                with open(filepath, 'r', encoding='utf-8') as file_handle:
                    # Read the file content and normalize different newline characters (\r\n, \r)
                    # to the standard Unix/Python newline (\n) for consistent handling.
                    self.target_text_content = file_handle.read().replace('\r\n', '\n').replace('\r', '\n')
            except UnicodeDecodeError:
                # If UTF-8 fails, try Latin-1 (another common encoding)
                 with open(filepath, 'r', encoding='latin-1') as file_handle:
                    self.target_text_content = file_handle.read().replace('\r\n', '\n').replace('\r', '\n')

            # Enable the text area for modification
            self.text_area.config(state=tk.NORMAL)
            # Delete any previous content
            self.text_area.delete("1.0", tk.END)

            # Insert the newly loaded text
            self.text_area.insert("1.0", self.target_text_content)

            # Apply the "faint" tag to all the text initially
            self.text_area.tag_add("faint", "1.0", tk.END)

            # Reset the typing position to the beginning
            self.current_pos = 0
            # Set the insertion cursor (caret) position to the beginning ("1.0")
            self.text_area.mark_set(tk.INSERT, "1.0")
            # Set the keyboard focus to the text area so the user can start typing
            self.text_area.focus_set()

            # Keep the text area state as NORMAL, but control input via key bindings

        except Exception as e:
            # Show an error message if the file cannot be read
            messagebox.showerror("Error Loading File", f"Could not read file:\n{e}")
            # Reset internal state on error
            self.target_text_content = ""
            self.text_area.config(state=tk.NORMAL)
            self.text_area.delete("1.0", tk.END)
            self.text_area.config(state=tk.DISABLED) # Disable if load failed

    def get_index(self, character_position):
        """Converts a flat character position (integer) into a Tkinter Text index ('line.column')."""
        # Example: position 0 -> "1.0", position 10 -> "1.10" (if on first line)
        # This automatically handles calculating line and column based on newlines in the text.
        return self.text_area.index(f"1.0 + {character_position} chars")

    def handle_keypress(self, event):
        """Handles user key presses to provide typing feedback and control input."""

        # If no text is loaded yet, ignore key presses
        if not self.target_text_content:
             return "break"

        # Get the symbolic name of the key pressed (e.g., 'BackSpace', 'Return', 'a', 'Shift_L')
        keysym = event.keysym
        # Get the actual character generated, if any (e.g., 'a', 'A', '\n', '\t')
        # Note: This might be empty for modifier keys like Shift, Ctrl, Alt
        char = event.char

        # --- Handle Backspace Key ---
        if keysym == 'BackSpace':
            # Only allow backspace if not at the very beginning
            if self.current_pos > 0:
                # Move the logical position back one step
                self.current_pos -= 1
                # Get the Tkinter indices for the character being reverted
                prev_index = self.get_index(self.current_pos)
                next_index = self.get_index(self.current_pos + 1)

                # Remove any 'correct' or 'incorrect' tags from that character position
                self.text_area.tag_remove("correct", prev_index, next_index)
                self.text_area.tag_remove("incorrect", prev_index, next_index)

                # Get the original character that should be at this position
                original_char = self.target_text_content[self.current_pos]

                # Delete the currently displayed character (might be correct/incorrect)
                self.text_area.delete(prev_index, next_index)
                # Insert the original character back, applying the 'faint' tag
                self.text_area.insert(prev_index, original_char, ("faint",))

                # Move the insertion cursor back to the corrected position
                self.text_area.mark_set(tk.INSERT, prev_index)
                # Ensure the cursor is visible (scrolls the text area if needed)
                self.text_area.see(tk.INSERT)

            # Crucially, return "break" to prevent Tkinter's default Backspace behavior
            return "break"

        # --- Ignore key presses if user has finished typing the text ---
        if self.current_pos >= len(self.target_text_content):
             return "break" # Don't allow typing past the end

        # --- Processing for typing keys (Enter, Tab, regular characters) ---

        # Get the character that the user is *supposed* to type at the current position
        target_char = self.target_text_content[self.current_pos]
        # Get the Tkinter indices for the current character position
        current_index = self.get_index(self.current_pos)
        next_index = self.get_index(self.current_pos + 1)

        is_correct = False # Flag to track if the typed key matches the target
        # Stores the character to display if the user types incorrectly (might be different from event.char)
        char_to_display_if_incorrect = None

        # --- Handle Enter Key (Tkinter keysym is 'Return') ---
        if keysym == 'Return':
            # Check if the target character is actually a newline
            if target_char == '\n':
                is_correct = True
            else:
                # User pressed Enter, but a newline was not expected
                is_correct = False
                # We don't want to display a visible character for an incorrect Enter press,
                # instead we will redisplay the character that *was* expected.
                char_to_display_if_incorrect = target_char

        # --- Handle Tab Key ---
        elif keysym == 'Tab':
             # Check if the target character is actually a tab
            if target_char == '\t':
                is_correct = True
            else:
                # User pressed Tab, but a tab was not expected
                is_correct = False
                # Display the character that was expected instead of the incorrect tab
                char_to_display_if_incorrect = target_char

        # --- Handle Regular Printable Characters ---
        # Check if event.char represents a single, printable character (or space)
        elif len(char) == 1 and (char.isprintable() or char == ' '):
            # Check if the typed character matches the target character
            if char == target_char:
                is_correct = True
            else:
                # User typed the wrong printable character
                is_correct = False
                # We want to display the character the user actually typed (their mistake)
                char_to_display_if_incorrect = char

        # --- Ignore other keys ---
        else:
             # This branch catches modifier keys (Shift, Ctrl, Alt), Function keys (F1-F12),
             # arrow keys, Home, End, Delete, etc., which were not handled above.
             # We ignore them by returning "break".
             return "break"

        # --- Apply Styling, Update Display, and Advance Position ---

        # Determine which tag ('correct' or 'incorrect') to apply based on correctness
        tag_to_apply = "correct" if is_correct else "incorrect"

        # Remove the 'faint' tag from the character position being typed
        self.text_area.tag_remove("faint", current_index, next_index)
        # Remove any pre-existing 'correct' or 'incorrect' tags (relevant after backspacing)
        self.text_area.tag_remove("correct", current_index, next_index)
        self.text_area.tag_remove("incorrect", current_index, next_index)

        # If the key press was incorrect, we need to update the displayed character
        if not is_correct:
            # Delete the original faint character currently at that position
            self.text_area.delete(current_index, next_index)
            # Insert the character we decided to display for the incorrect key press
            self.text_area.insert(current_index, char_to_display_if_incorrect)

        # Apply the 'correct' or 'incorrect' tag to the character at the current position
        # This primarily changes the foreground color.
        self.text_area.tag_add(tag_to_apply, current_index, next_index)

        # Advance the logical typing position to the next character
        self.current_pos += 1

        # Move the insertion cursor (caret) to the next position, if not at the end
        if self.current_pos < len(self.target_text_content):
            next_cursor_index = self.get_index(self.current_pos)
            self.text_area.mark_set(tk.INSERT, next_cursor_index)
        else:
            # If we've reached the end, place the cursor just after the last character
             self.text_area.mark_set(tk.INSERT, tk.END + "-1c") # Or just tk.END

        # Ensure the cursor position is visible by scrolling the text area if necessary
        self.text_area.see(tk.INSERT)

        # VERY IMPORTANT: Return "break" to prevent Tkinter's default action
        # for the key press (e.g., inserting the character again, moving the cursor).
        return "break"

# --- Main Execution Block ---
if __name__ == "__main__":
    # Create the main application window
    main_window = tk.Tk()
    # Create an instance of our application class
    app = TypingTutorOverlayApp(main_window)
    # Start the Tkinter event loop (waits for user input and runs the application)
    main_window.mainloop()