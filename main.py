import tkinter as tk
from tkinter import filedialog, scrolledtext, font, messagebox, ttk
import sys

# --- Try importing Pygments ---
try:
    from pygments import lex
    from pygments.lexers import get_lexer_by_name, guess_lexer, TextLexer
    from pygments.token import Token, Error # Import Token types
    PYGMENTS_AVAILABLE = True
except ImportError:
    PYGMENTS_AVAILABLE = False
    # You can keep the print statements here if you want console warnings
    # print("WARNING: Pygments library not found. Syntax highlighting will be disabled.")
    # print("Install it using: pip install Pygments")

# --- Helper Function (Place this outside the class) ---
def lighten_color(hex_color, factor=0.6):
    """
    Lightens a given hex color string by a specified factor.

    Args:
        hex_color (str): The color in hexadecimal format (e.g., '#FF0000').
        factor (float): The lightening factor (0.0 = no change, 1.0 = white).

    Returns:
        str: The lightened color in hexadecimal format, or a fallback color
             if the input is invalid.
    """
    try:
        # Remove '#' prefix if it exists
        hex_color = hex_color.lstrip('#')
        # Convert 3-digit hex to 6-digit
        if len(hex_color) == 3:
            hex_color = "".join([c*2 for c in hex_color])
        # Ensure it's a 6-digit hex color
        if len(hex_color) != 6:
            raise ValueError("Invalid hex color format")
        # Convert hex components to integer RGB values
        rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        # Calculate the new lightened RGB values
        new_rgb = tuple(min(255, int(color_component + (255 - color_component) * factor)) for color_component in rgb)
        # Convert the new RGB values back to a hex string
        return f"#{new_rgb[0]:02x}{new_rgb[1]:02x}{new_rgb[2]:02x}"
    except Exception:
        # Fallback to LightGray if any error occurs during conversion
        return "#D3D3D3"

class TypingTutorOverlayApp:
    """
    A Tkinter application for practicing typing code or text with syntax highlighting.
    Untyped text appears faint, correctly typed text appears in normal syntax colors,
    and incorrectly typed text appears bright red.
    """
    def __init__(self, root_window):
        """
        Initializes the Typing Tutor application window and its components.

        Args:
            root_window (tk.Tk): The main Tkinter window instance.
        """
        self.root = root_window
        self.root.title("Typing Practice - Faint Syntax Highlighting")
        self.root.geometry("900x700") # Set initial window dimensions

        # --- Application State Variables ---
        self.target_text_content = "" # Stores the full text to be typed
        self.current_pos = 0          # Index of the next character the user should type
        # Stores token information for syntax highlighting and backspace handling:
        # list of {"start": int, "end": int, "type": pygments.token.Token}
        self.token_map = []

        # --- Configure Colors and Font ---
        # Colors defined here are primarily for feedback
        self.incorrect_color = "#FF0000" # Bright Red for errors
        # Font settings (monospaced recommended for code)
        self.text_font = font.Font(family="Consolas", size=12) # Common monospaced font

        # --- Syntax Highlighting Colors (Customize as desired) ---
        # Maps Pygments token types to their desired *normal* (non-faint) colors
        self.syntax_colors = {
            Token.Keyword: '#0000FF',             # Blue
            Token.Keyword.Constant: '#0000FF',
            Token.Keyword.Declaration: '#0000FF',
            Token.Keyword.Namespace: '#0000FF',
            Token.Keyword.Pseudo: '#0000FF',
            Token.Keyword.Reserved: '#0000FF',
            Token.Keyword.Type: '#2B91AF',        # Teal
            Token.Name.Class: '#2B91AF',
            Token.Name.Function: '#2B91AF',
            Token.Name.Builtin: '#2B91AF',
            Token.Name.Builtin.Pseudo: '#2B91AF',
            Token.Name.Variable: '#000000',       # Black (or default)
            Token.Name.Constant: '#880000',       # Dark red
            Token.Name.Tag: '#000080',            # Navy (HTML/XML tags)
            Token.Name.Attribute: '#FF8000',      # Orange (HTML/XML attributes)
            Token.Name.Decorator: '#AA22FF',      # Purple (Python decorators)
            Token.Literal.String: '#A31515',      # Reddish-brown (Strings)
            Token.Literal.String.Doc: '#A31515',
            Token.Literal.String.Interpol: '#A31515',
            Token.Literal.String.Escape: '#A31515',
            Token.Literal.String.Regex: '#A31515',
            Token.Literal.String.Symbol: '#A31515',
            Token.Literal.String.Other: '#A31515',
            Token.Literal.Number: '#098658',      # Greenish (Numbers)
            Token.Operator: '#000000',            # Black (Operators)
            Token.Operator.Word: '#0000FF',       # Blue (Word operators like 'in', 'is')
            Token.Punctuation: '#000000',          # Black (Punctuation)
            Token.Comment: '#008000',             # Green (Comments)
            Token.Comment.Multiline: '#008000',
            Token.Comment.Single: '#008000',
            Token.Comment.Special: '#008000',
            Token.Comment.Preproc: '#0000FF',     # Blue (Preprocessor directives)
            Token.Generic.Heading: '#000080',     # Navy (Markdown etc.)
            Token.Generic.Subheading: '#000080',
            Token.Generic.Deleted: '#A31515',
            Token.Generic.Inserted: '#008000',
            Token.Generic.Error: '#FF0000',       # Red (Generic errors)
            Token.Error: '#FF0000',               # Red (Lexer errors)
            # Add more token types and colors as needed from Pygments documentation
        }


        # --- User Interface Elements ---

        # Top frame for control buttons and language selection
        control_frame = tk.Frame(self.root, pady=10)
        control_frame.pack(fill=tk.X) # Make frame fill window width

        # Button to load text from a file
        self.load_button = tk.Button(control_frame, text="Load File", command=self.load_file)
        self.load_button.pack(side=tk.LEFT, padx=(10, 5)) # Padding (left, right)

        # Button to paste text from clipboard
        self.paste_button = tk.Button(control_frame, text="Paste Text", command=self.paste_text)
        self.paste_button.pack(side=tk.LEFT, padx=5)

        # Label for the language selection dropdown
        language_label = tk.Label(control_frame, text="Language:")
        language_label.pack(side=tk.LEFT, padx=(10, 2))

        # Language selection dropdown (Combobox)
        self.language_var = tk.StringVar(self.root)
        # List of supported languages for explicit selection
        languages = ["Plain Text", "Python", "JavaScript", "HTML", "CSS"]
        # You can add more languages supported by Pygments here
        self.language_menu = ttk.Combobox(
            control_frame,
            textvariable=self.language_var,
            values=languages,
            state="readonly" # User must select from the list
        )
        self.language_menu.pack(side=tk.LEFT, padx=5)
        self.language_menu.set("Plain Text") # Set default selection
        # Call on_language_change when the user selects a different language
        self.language_menu.bind("<<ComboboxSelected>>", self.on_language_change)

        # The main text area widget with scrolling capabilities
        self.text_area = scrolledtext.ScrolledText(
            self.root,
            wrap=tk.NONE, # Disable automatic line wrapping (best for code)
            font=self.text_font,
            padx=5, # Internal horizontal padding
            pady=5, # Internal vertical padding
            # Enable Tkinter's built-in undo/redo stack
            undo=True,
            autoseparators=True,
            maxundo=-1 # Set unlimited undo history
        )
        # Make the text area expand to fill available space
        self.text_area.pack(expand=True, fill=tk.BOTH, padx=10, pady=(0, 10))

        # --- Configure Text Tags ---
        # Sets up tags for feedback and syntax highlighting (normal and faint)
        self._configure_tags()

        # --- Bind Events ---
        # Connects user actions (like key presses, clicks) to handler methods
        self._bind_events()

        # Start the text area in a disabled state; enable after loading/pasting
        self.text_area.config(state=tk.DISABLED)

    def _generate_tag_name(self, token_type, faint=False):
        """
        Generates a consistent tag name string from a Pygments token type.
        Prepends 'faint_hl_' for faint tags, 'hl_' for normal syntax tags.

        Args:
            token_type (pygments.token.Token): The Pygments token type.
            faint (bool): If True, generates the name for the faint version tag.

        Returns:
            str: The generated tag name (e.g., 'hl_Keyword_Type', 'faint_hl_Literal_String').
        """
        prefix = "faint_hl_" if faint else "hl_"
        # Replace dots in token type string with underscores for valid tag names
        return f"{prefix}{str(token_type).replace('.', '_')}"

    def _configure_tags(self):
        """
        Configures all necessary text tags in the ScrolledText widget.
        This includes feedback tags (incorrect) and dual syntax tags (normal, faint).
        """
        # --- Typing Feedback Tags ---
        # Tag to apply when user types incorrectly (overrides syntax colors with red)
        self.text_area.tag_configure("incorrect", foreground=self.incorrect_color)
        # Note: A "correct" tag is not explicitly styled, as correctness is indicated
        # by revealing the normal syntax color.

        # --- Syntax Highlighting Tags (Normal and Faint) ---
        if PYGMENTS_AVAILABLE:
            # Configure default text tags (for text not matched by other tokens)
            try:
                 # Get the default foreground color of the text widget
                default_fg = self.text_area.cget("foreground")
            except tk.TclError:
                 default_fg = "#000000" # Fallback to black if getting default fails

            faint_default_fg = lighten_color(default_fg, 0.6)
            # Tag for normal default text
            self.text_area.tag_configure(self._generate_tag_name(Token.Text), foreground=default_fg)
            # Tag for faint default text
            self.text_area.tag_configure(self._generate_tag_name(Token.Text, faint=True), foreground=faint_default_fg)

            # Configure tags for each token type defined in self.syntax_colors
            for token_type, color in self.syntax_colors.items():
                # Configure the tag for the normal syntax color
                normal_tag_name = self._generate_tag_name(token_type)
                try:
                    self.text_area.tag_configure(normal_tag_name, foreground=color)
                except tk.TclError as error:
                    print(f"Warning: Could not configure tag '{normal_tag_name}' ({color}): {error}")

                # Configure the tag for the faint version of the syntax color
                faint_tag_name = self._generate_tag_name(token_type, faint=True)
                faint_color = lighten_color(color, 0.6) # Use the helper function
                try:
                    self.text_area.tag_configure(faint_tag_name, foreground=faint_color)
                except tk.TclError as error:
                    print(f"Warning: Could not configure faint tag '{faint_tag_name}' ({faint_color}): {error}")

    def _bind_events(self):
        """
        Binds all necessary event handlers to the text area widget.
        Primarily intercepts key presses and prevents unwanted default actions.
        """
        # Bind the primary key press event to our custom handler
        self.text_area.bind('<KeyPress>', self.handle_keypress)

        # Prevent default actions that interfere with the typing tutor logic
        # Mouse actions: Prevent clicking to move cursor or select text
        self.text_area.bind('<Button-1>', lambda event: "break") # Left click
        self.text_area.bind('<B1-Motion>', lambda event: "break")# Left click + drag
        self.text_area.bind('<ButtonRelease-1>', lambda event: "break") # Left click release
        self.text_area.bind('<Double-Button-1>', lambda event: "break") # Double click
        self.text_area.bind('<Triple-Button-1>', lambda event: "break") # Triple click
        self.text_area.bind('<Shift-Button-1>', lambda event: "break") # Shift + click
        self.text_area.bind('<Control-Button-1>', lambda event: "break")# Control + click (may vary by OS)

        # Prevent clipboard operations via standard shortcuts/menus
        self.text_area.bind("<<Cut>>", lambda event: "break")
        self.text_area.bind("<<Paste>>", lambda event: "break") # Use our button instead

        # Prevent cursor navigation keys
        self.text_area.bind('<Left>', lambda event: "break")
        self.text_area.bind('<Right>', lambda event: "break")
        self.text_area.bind('<Up>', lambda event: "break")
        self.text_area.bind('<Down>', lambda event: "break")
        self.text_area.bind('<Home>', lambda event: "break")
        self.text_area.bind('<End>', lambda event: "break")

        # Prevent the Delete key (only allow Backspace for correction)
        self.text_area.bind('<Delete>', lambda event: "break")

    def on_language_change(self, event=None):
        """
        Event handler called when the user selects a different language
        from the Combobox. Reloads syntax highlighting.
        """
        # Check if there is text currently loaded in the target variable
        if self.target_text_content and self.text_area.get("1.0", tk.END).strip():
            # Re-apply syntax highlighting using the newly selected language
            self._apply_syntax_highlighting(self.language_var.get())
            # Re-apply faint/incorrect tags based on the current typing position
            self._reapply_faint_and_feedback()

    def _set_new_target_text(self, text_content):
        """
        Helper function to update the application state and text area
        when new text is loaded or pasted.

        Args:
            text_content (str): The new text to be used for practice.
        """
        try:
            # Normalize newline characters for cross-platform consistency
            self.target_text_content = text_content.replace('\r\n', '\n').replace('\r', '\n')
            self.token_map = [] # Clear the previous token map

            # Enable the text area for modification
            self.text_area.config(state=tk.NORMAL)
            # Clear any existing content
            self.text_area.delete("1.0", tk.END)
            # Insert the new target text
            self.text_area.insert("1.0", self.target_text_content)

            # Apply syntax highlighting (both normal and faint tags)
            selected_language = self.language_var.get()
            self._apply_syntax_highlighting(selected_language)

            # Reset the typing progress
            self.current_pos = 0
            # Set the insertion cursor position to the beginning
            self.text_area.mark_set(tk.INSERT, "1.0")
            # Give the text area keyboard focus
            self.text_area.focus_set()

        except Exception as error:
            messagebox.showerror("Error Setting Text", f"An error occurred while setting the text:\n{error}")
            # Reset state completely on error
            self.target_text_content = ""
            self.token_map = []
            self.text_area.config(state=tk.NORMAL)
            self.text_area.delete("1.0", tk.END)
            self.text_area.config(state=tk.DISABLED) # Disable if setting failed

    def _apply_syntax_highlighting(self, language_name):
        """
        Applies syntax highlighting using Pygments. It adds *both* the normal
        syntax tag (e.g., 'hl_Keyword') and the faint syntax tag (e.g., 'faint_hl_Keyword')
        to each token's range. Populates self.token_map.

        Args:
            language_name (str): The name of the language (e.g., 'Python', 'HTML').
        """
        if not PYGMENTS_AVAILABLE or not self.target_text_content:
            self.token_map = [] # Ensure map is empty if no highlighting
            return

        # --- Clear existing highlighting and feedback tags ---
        all_tags = self.text_area.tag_names()
        for tag in all_tags:
            if tag.startswith("hl_") or tag.startswith("faint_hl_") or tag == "incorrect":
                self.text_area.tag_remove(tag, "1.0", tk.END)

        # --- Reset the token map ---
        self.token_map = []

        # --- Get the appropriate Pygments Lexer ---
        try:
            # Handle 'Plain Text' explicitly to avoid Pygments errors
            if language_name == "Plain Text":
                lexer = TextLexer()
            else:
                # Get lexer by name (case-insensitive alias matching)
                lexer = get_lexer_by_name(language_name.lower())
        except Exception: # Catches pygments.util.ClassNotFound
            # If specific language fails, try guessing
            try:
                lexer = guess_lexer(self.target_text_content)
                # Optionally update the combobox here if guessing succeeds
                # self.language_var.set(lexer.name) # Could be slightly annoying for user
            except Exception:
                # If guessing also fails, fallback to plain text
                lexer = TextLexer()

        # --- Apply tags token by token ---
        start_index = "1.0"       # Tkinter index for the start of the current token
        current_char_pos = 0    # Flat character position counter

        # Process the text using the chosen lexer
        for token_type, value in lex(self.target_text_content, lexer):
            # Calculate end position/index for the current token
            end_index = self.text_area.index(f"{start_index} + {len(value)} chars")
            end_char_pos = current_char_pos + len(value)

            # Store token info (start pos, end pos, type) in the map
            self.token_map.append({"start": current_char_pos, "end": end_char_pos, "type": token_type})

            # Generate tag names for this token type
            normal_tag = self._generate_tag_name(token_type)
            faint_tag = self._generate_tag_name(token_type, faint=True)

            # Apply the normal syntax tag (might be hidden by faint initially)
            # Use default 'Text' tag if a specific one wasn't configured
            tag_to_apply_normal = normal_tag if normal_tag in self.text_area.tag_names() else self._generate_tag_name(Token.Text)
            self.text_area.tag_add(tag_to_apply_normal, start_index, end_index)

            # Apply the faint syntax tag (this will be visible initially)
            # Use default faint 'Text' tag if a specific one wasn't configured
            tag_to_apply_faint = faint_tag if faint_tag in self.text_area.tag_names() else self._generate_tag_name(Token.Text, faint=True)
            self.text_area.tag_add(tag_to_apply_faint, start_index, end_index)

            # Update start position for the next token
            start_index = end_index
            current_char_pos = end_char_pos

    def _reapply_faint_and_feedback(self):
        """
        Called after a language change on existing text. Attempts to restore
        the faintness for untyped portions. Does NOT perfectly restore 'incorrect'
        state as that state isn't stored persistently.
        """
        if not self.target_text_content: return

        # Remove all faint and incorrect tags first to reset
        all_tags = self.text_area.tag_names()
        for tag in all_tags:
            if tag.startswith("faint_hl_") or tag == "incorrect":
                self.text_area.tag_remove(tag, "1.0", tk.END)

        # Iterate through the text character by character
        for i in range(len(self.target_text_content)):
            index = self.get_index(i)
            next_index = self.get_index(i + 1)
            if not index or not next_index: continue # Skip if index calculation fails

            # Check if this character position is before the user's current typing position
            if i < self.current_pos:
                # This part has been typed. Assume it's correct after language change.
                # Ensure no faint tag is applied (already handled by the removal above).
                pass
            else:
                # This part is untyped. Re-apply the appropriate faint tag.
                token_info = self._find_token_for_pos(i)
                # Determine the correct faint tag (specific or default)
                faint_tag_to_apply = self._generate_tag_name(Token.Text, faint=True) # Default
                if token_info:
                    potential_tag = self._generate_tag_name(token_info["type"], faint=True)
                    if potential_tag in self.text_area.tag_names():
                        faint_tag_to_apply = potential_tag
                # Apply the determined faint tag
                self.text_area.tag_add(faint_tag_to_apply, index, next_index)


    def _find_token_for_pos(self, char_pos):
        """
        Finds the token information dictionary from self.token_map that covers
        a specific flat character position.

        Args:
            char_pos (int): The flat character position (0-based index).

        Returns:
            dict or None: The token dictionary {'start', 'end', 'type'} if found,
                          otherwise None.
        """
        for token_info in self.token_map:
            # Check if the position falls within the token's range [start, end)
            if token_info["start"] <= char_pos < token_info["end"]:
                return token_info
        return None # Position not found in any token range

    def load_file(self):
        """
        Opens a file dialog for the user to select a text file,
        reads the content, attempts to guess the language, and loads it
        into the application using _set_new_target_text.
        """
        filepath = filedialog.askopenfilename(
            title="Select Text File",
            # Define allowed file types for the dialog
            filetypes=(("Text Files", "*.txt"), ("Python Files", "*.py"), ("JavaScript Files", "*.js"),
                       ("HTML Files", "*.html;*.htm"), ("CSS Files", "*.css"), ("All Files", "*.*"))
        )
        # If the user cancels the dialog, filepath will be empty
        if not filepath:
            return

        # Attempt to automatically set language based on file extension
        if filepath.lower().endswith(".py"): self.language_var.set("Python")
        elif filepath.lower().endswith(".js"): self.language_var.set("JavaScript")
        elif filepath.lower().endswith((".html", ".htm")): self.language_var.set("HTML")
        elif filepath.lower().endswith(".css"): self.language_var.set("CSS")
        # Keep previous selection if extension doesn't match common types

        try:
            content = ""
            # Try multiple common encodings to read the file
            encodings_to_try = ['utf-8', 'latin-1', 'cp1252']
            file_opened_successfully = False
            last_exception = None
            for enc in encodings_to_try:
                try:
                    with open(filepath, 'r', encoding=enc) as file_handle:
                        content = file_handle.read()
                    file_opened_successfully = True
                    break # Exit loop on successful read
                except UnicodeDecodeError:
                    last_exception = UnicodeDecodeError # Keep track of decoding error
                    continue # Try the next encoding
                except Exception as e: # Catch other file I/O errors
                     last_exception = e
                     # Don't continue if it's not a decoding error (e.g., permission denied)
                     break

            if not file_opened_successfully:
                # If loop finishes without success, raise the last encountered error
                if last_exception:
                    raise last_exception
                else: # Should not happen unless encodings_to_try is empty
                    raise IOError(f"Could not open or decode file '{filepath}'")

            # Load the successfully read content into the application
            self._set_new_target_text(content)

        except Exception as error:
            # Show error message to the user if loading fails
            messagebox.showerror("Error Loading File", f"Could not read file:\n{error}")
            # Clear the application state if loading failed
            self._set_new_target_text("")

    def paste_text(self):
        """
        Pastes text from the system clipboard into the application,
        attempts to guess the language, and loads it using _set_new_target_text.
        """
        try:
            # Attempt to get text content from the clipboard
            clipboard_content = self.root.clipboard_get()
            if clipboard_content:
                # If Pygments is available, try to guess the language
                if PYGMENTS_AVAILABLE:
                    try:
                        lexer = guess_lexer(clipboard_content)
                        # Map common Pygments lexer aliases to our Combobox values
                        lang_map = {'python': 'Python', 'py': 'Python', 'javascript': 'JavaScript',
                                    'js': 'JavaScript', 'html': 'HTML', 'css': 'CSS'}
                        guessed_language = "Plain Text" # Default guess
                        if lexer.aliases: # Check if the lexer has defined aliases
                            # Use the first alias for mapping
                            guessed_language = lang_map.get(lexer.aliases[0], "Plain Text")
                        self.language_var.set(guessed_language) # Update the Combobox
                    except Exception: # Catch pygments.util.ClassNotFound if guess fails
                        self.language_var.set("Plain Text") # Fallback on error
                else:
                     # If Pygments is not available, default to Plain Text
                     self.language_var.set("Plain Text")

                # Load the pasted content into the application
                self._set_new_target_text(clipboard_content)
            else:
                # Inform user if the clipboard was empty
                messagebox.showwarning("Paste Text", "Clipboard is empty.")
        except tk.TclError:
            # Handle error if clipboard access fails (e.g., no text content)
            messagebox.showwarning("Paste Text", "Could not get text from clipboard.")
        except Exception as error:
            # Handle any other unexpected errors during the paste operation
            messagebox.showerror("Paste Error", f"An error occurred during paste:\n{error}")

    def get_index(self, character_position):
        """
        Converts a flat character position (integer) into a Tkinter Text
        widget index string (e.g., 'line.column'). Includes basic error handling.

        Args:
            character_position (int): The 0-based flat character index.

        Returns:
            str or None: The Tkinter index string, or None if an error occurs
                         or the position is invalid.
        """
        try:
            # Prevent errors if position becomes negative during rapid operations
            if character_position < 0:
                return "1.0" # Return start index if position is negative
            # Use Tkinter's index method to calculate the line.column position
            return self.text_area.index(f"1.0 + {character_position} chars")
        except tk.TclError:
            # Return None if Tkinter fails to calculate the index (e.g., widget destroyed)
            return None

          
    def handle_keypress(self, event):
        """
        The core event handler for key presses within the text area.
        It compares the typed key with the target text, applies appropriate
        styling (revealing syntax color or showing red error), and prevents
        default Tkinter key actions.

        Args:
            event (tk.Event): The key press event object.

        Returns:
            str: Always returns "break" to prevent default Tkinter actions.
        """
        # Ignore key presses if no text is loaded
        if not self.target_text_content:
            return "break"

        keysym = event.keysym # Symbolic name (e.g., 'BackSpace', 'a', 'Return')
        char = event.char    # Actual character produced (e.g., 'a', '\n', '')

        # --- Handle Backspace Key ---
        if keysym == 'BackSpace':
            # Check if we can move back (not at the beginning)
            if self.current_pos > 0:
                # Decrement the current typing position
                self.current_pos -= 1
                # Get Tkinter indices for the character being reverted
                prev_index = self.get_index(self.current_pos)
                next_index = self.get_index(self.current_pos + 1)
                # Safety check if index calculation failed
                if not prev_index or not next_index: return "break"

                # Remove feedback tags ('incorrect') from this position
                self.text_area.tag_remove("incorrect", prev_index, next_index)

                # --- Find original token info for this position ---
                token_info = self._find_token_for_pos(self.current_pos)

                # --- Determine BOTH normal and faint tags to re-apply ---
                # Default tags (for text not otherwise tokenized)
                normal_tag_to_apply = self._generate_tag_name(Token.Text)
                faint_tag_to_apply = self._generate_tag_name(Token.Text, faint=True)

                if token_info:
                    # Get specific token tags if found
                    potential_normal_tag = self._generate_tag_name(token_info["type"])
                    potential_faint_tag = self._generate_tag_name(token_info["type"], faint=True)
                    # Check if these specific tags actually exist/were configured
                    if potential_normal_tag in self.text_area.tag_names():
                        normal_tag_to_apply = potential_normal_tag
                    if potential_faint_tag in self.text_area.tag_names():
                        faint_tag_to_apply = potential_faint_tag

                # --- Restore original character and apply BOTH tags ---
                original_char = self.target_text_content[self.current_pos]
                # Delete the character currently displayed at that position
                self.text_area.delete(prev_index, next_index)

                # **CORRECTION HERE:** Insert char and apply BOTH the normal and faint tags.
                # The faint tag's color will visually take precedence.
                tags_to_apply_on_backspace = (normal_tag_to_apply, faint_tag_to_apply)
                self.text_area.insert(prev_index, original_char, tags_to_apply_on_backspace)

                # Move the insertion cursor (caret) back
                self.text_area.mark_set(tk.INSERT, prev_index)
                # Ensure the cursor is visible (scroll if necessary)
                self.text_area.see(tk.INSERT)
            # Prevent Tkinter's default backspace behavior
            return "break"

        # --- Ignore key presses if user has already typed the whole text ---
        if self.current_pos >= len(self.target_text_content):
            return "break"

        # --- Processing for Typing Keys (Enter, Tab, Printable Chars) ---
        # Get the character expected at the current position
        target_char = self.target_text_content[self.current_pos]
        # Get Tkinter indices for the current character position
        current_index = self.get_index(self.current_pos)
        next_index = self.get_index(self.current_pos + 1)
        # Safety check if index calculation failed
        if not current_index or not next_index: return "break"

        # Find the token information for the current character position
        token_info = self._find_token_for_pos(self.current_pos)
        # Determine the faint tag associated with this position (specific or default)
        faint_tag_to_remove = self._generate_tag_name(Token.Text, faint=True) # Default
        if token_info:
            potential_faint_tag = self._generate_tag_name(token_info["type"], faint=True)
            if potential_faint_tag in self.text_area.tag_names():
                faint_tag_to_remove = potential_faint_tag


        # --- Determine Correctness ---
        is_correct = False # Flag to track if the key press matches the target
        # Stores character to display if incorrect (might be target char or typed char)
        char_to_display_if_incorrect = None

        # Check specific keys first
        if keysym == 'Return': # Enter key
            is_correct = (target_char == '\n')
            # If Enter was pressed incorrectly, show the char that *was* expected
            if not is_correct: char_to_display_if_incorrect = target_char
        elif keysym == 'Tab': # Tab key
            is_correct = (target_char == '\t')
            # If Tab was pressed incorrectly, show the char that *was* expected
            if not is_correct: char_to_display_if_incorrect = target_char
        # Check for regular printable characters (including space)
        elif len(char) == 1 and (char.isprintable() or char == ' '):
            is_correct = (char == target_char)
            # If incorrect, show the character the user actually typed (their mistake)
            if not is_correct: char_to_display_if_incorrect = char
        else:
            # Ignore all other keys (modifiers, function keys, arrows, etc.)
            return "break"

        # --- Apply Styling and Advance ---

        # Remove the faint tag for the current position, revealing normal syntax color underneath
        self.text_area.tag_remove(faint_tag_to_remove, current_index, next_index)
        # Remove the 'incorrect' tag (in case user is correcting a previous mistake)
        self.text_area.tag_remove("incorrect", current_index, next_index)

        if is_correct:
            # --- Correct Key Press ---
            # Faint tag removed, normal syntax color shows. Ensure correct char is displayed.
            # Check if the currently displayed character is already the correct one
            # (it might be wrong if the user just corrected a mistake).
            if self.text_area.get(current_index, next_index) != target_char:
                 # If not, delete the wrong char and insert the correct one
                 self.text_area.delete(current_index, next_index)
                 self.text_area.insert(current_index, target_char)
            # No additional styling needed; normal syntax color is the indicator.

        else: # --- Incorrect Key Press ---
            # Determine the character to actually display (user's mistake or expected char)
            display_char = char_to_display_if_incorrect if char_to_display_if_incorrect is not None else target_char
            # Update the displayed character in the text widget if it's not already showing the error/target
            if self.text_area.get(current_index, next_index) != display_char:
                self.text_area.delete(current_index, next_index)
                self.text_area.insert(current_index, display_char)
            # Apply the 'incorrect' tag, making the character bright red.
            # This overrides the normal syntax color.
            self.text_area.tag_add("incorrect", current_index, next_index)

        # Advance the logical typing position
        self.current_pos += 1

        # Move the insertion cursor (caret) to the next position
        if self.current_pos < len(self.target_text_content):
            next_cursor_index = self.get_index(self.current_pos)
            # Only move cursor if index calculation was successful
            if next_cursor_index: self.text_area.mark_set(tk.INSERT, next_cursor_index)
        else:
            # If at the end, place cursor just after the last character
             self.text_area.mark_set(tk.INSERT, tk.END + "-1c") # Safest way to position at end

        # Ensure the new cursor position is visible (scrolls if needed)
        self.text_area.see(tk.INSERT)

        # Crucial: Prevent Tkinter's default action for the key press
        return "break"

    

# --- Main Execution Block ---
if __name__ == "__main__":
    # Create the main Tkinter window
    main_window = tk.Tk()
    # Create an instance of our application class
    app = TypingTutorOverlayApp(main_window)
    # Display a note if Pygments is not available (syntax highlighting disabled)
    if not PYGMENTS_AVAILABLE:
        # You could also display this message in the GUI status bar if you add one
        print("\nNOTE: Pygments library not found. Syntax highlighting disabled.")
        print("      Install using: pip install Pygments\n")
    # Start the Tkinter event loop (this keeps the window open and responsive)
    main_window.mainloop()