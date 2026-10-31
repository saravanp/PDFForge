"""
Desktop GUI for PDF Merger using Tkinter with drag-and-drop support.

Supports:
- Dragging files from the file system directly to the file list (requires tkinterdnd2)
- Drag-and-drop reordering within the list
- Keyboard shortcuts (Delete/Backspace to remove selected files)
"""
try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    _dnd_available = True
except ImportError:
    # Fallback if tkinterdnd2 is not installed
    _dnd_available = False
    TkinterDnD = object  # Dummy class for type hinting
    DND_FILES = None

import os
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from pdf_merger import merge_pdfs


def get_file_type(filename: str) -> str:
    """Determine if file is PDF or image."""
    ext = Path(filename).suffix.lower()
    return "pdf" if ext == ".pdf" else "image"


class PDFMergerApp:
    """Main GUI application for PDF merging with drag-and-drop reordering."""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("PDF Merger")
        self.root.geometry("900x700")
        self.root.minsize(700, 500)

        # Ensure proper font on all platforms
        default_font = ("Segoe UI", 10) if os.name == "nt" else ("Helvetica Neue", 10)
        title_font = ("Segoe UI", 14, "bold") if os.name == "nt" else ("Helvetica", 14, "bold")

        # Drag state for reordering
        self.drag_start_index = None
        self.drag_data = {"index": None, "item": None}

        # State
        self.input_files: list[Path] = []
        self.output_path = tk.StringVar(value="merged.pdf")

        # UI Elements
        self.merge_btn = None
        self.progress_label = None
        self.status_var = None
        self.file_listbox = None

        # Configure ttk style for cross-platform button consistency
        style = ttk.Style()
        # Use 'alt' theme on macOS for better color support, otherwise use default
        if os.name == "darwin":
            style.theme_use("alt")  # Better color support on macOS
        else:
            style.theme_use("default")
        # Configure custom button style with explicit colors
        # Use 'alt' theme on macOS for better color support, otherwise use default
        # Configure custom button style with explicit colors
        style.configure("Dark.TButton", background="#2196F3", foreground="white", font=("Segoe UI", 9, "bold"), focuscolor="none")
        style.configure("DarkAccent.TButton", background="#4CAF50", foreground="white", font=("Segoe UI", 9, "bold"), focuscolor="none")
        style.configure("MoveBtn.TButton", background="#9C27B0", foreground="white", font=("Segoe UI", 9, "bold"), focuscolor="none")
        style.configure("RemoveBtn.TButton", background="#F44336", foreground="white", font=("Segoe UI", 9, "bold"), focuscolor="none")
        style.configure("ClearBtn.TButton", background="#607D8B", foreground="white", font=("Segoe UI", 9, "bold"), focuscolor="none")
        style.configure("Browse.TButton", background="#673AB7", foreground="white", font=default_font, focuscolor="none")
        style.configure("Merge.TButton", background="#1B5E20", foreground="white", font=("Segoe UI", 16, "bold"), focuscolor="none", padding=20, relief=tk.RAISED)
        # Configure active/hover states to keep colors consistent
        style.map("Dark.TButton", background=[("active", "#1565C0"), ("disabled", "#B0BEC5")], foreground=[("active", "white"), ("disabled", "#ECEFF1")])
        style.map("DarkAccent.TButton", background=[("active", "#2E7D32"), ("disabled", "#B0BEC5")], foreground=[("active", "white"), ("disabled", "#ECEFF1")])
        style.map("MoveBtn.TButton", background=[("active", "#6A1B9A"), ("disabled", "#B0BEC5")], foreground=[("active", "white"), ("disabled", "#ECEFF1")])
        style.map("RemoveBtn.TButton", background=[("active", "#C62828"), ("disabled", "#B0BEC5")], foreground=[("active", "white"), ("disabled", "#ECEFF1")])
        style.map("ClearBtn.TButton", background=[("active", "#455A64"), ("disabled", "#B0BEC5")], foreground=[("active", "white"), ("disabled", "#ECEFF1")])
        style.map("Browse.TButton", background=[("active", "#4A148C"), ("disabled", "#B0BEC5")], foreground=[("active", "white"), ("disabled", "#ECEFF1")])
        style.map("Merge.TButton", background=[("active", "#2E7D32"), ("disabled", "#A5D6A7"), ("pressed", "#1B5E20")], foreground=[("active", "white"), ("disabled", "#ECEFF1"), ("pressed", "white")])

        self._build_ui(default_font, title_font)

    def _build_ui(self, default_font, title_font):
        """Construct the GUI layout."""
        # --- Title Bar ---
        title_bar = tk.Frame(self.root, bg="#2c3e50", height=60)
        title_bar.pack(fill=tk.X)
        title_bar.pack_propagate(False)

        tk.Label(
            title_bar,
            text="PDF Merger",
            font=("Segoe UI", 22, "bold") if os.name == "nt" else ("Helvetica", 22, "bold"),
            bg="#2c3e50",
            fg="white",
        ).pack(side=tk.LEFT, padx=20)

        tk.Label(
            title_bar,
            text="Merge images and PDFs into a single PDF",
            bg="#2c3e50",
            fg="#bdc3c7",
            font=("Segoe UI", 10) if os.name == "nt" else ("Helvetica", 10),
        ).pack(side=tk.LEFT, padx=(5, 0), pady=(0, 2))

        # --- Main Content ---
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(10, 20))

        # Instructions
        tk.Label(
            main_frame,
            text="Drag & drop files from your desktop to add them, then drag to reorder.",
            font=("Segoe UI", 9, "italic") if os.name == "nt" else ("Helvetica", 9, "italic"),
            fg="#7f8c8d",
            anchor="w",
        ).pack(fill=tk.X, pady=(0, 5))

        # File list section with Listbox
        file_frame = tk.LabelFrame(main_frame, text=" Files to Merge ", font=title_font)
        file_frame.pack(fill=tk.BOTH, expand=True, pady=(5, 10))

        # Listbox with scrollbar
        list_frame = tk.Frame(file_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        scrollbar = tk.Scrollbar(list_frame, orient=tk.VERTICAL)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.file_listbox = tk.Listbox(
            list_frame,
            yscrollcommand=scrollbar.set,
            selectmode=tk.EXTENDED,
            font=default_font,
            activestyle="dotbox",
            bd=2,
            highlightthickness=1,
            selectbackground="#2196F3",
            selectforeground="white",
        )
        self.file_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.file_listbox.yview)

        # Drag and drop bindings for Listbox
        self.file_listbox.bind("<Button-1>", self._on_drag_start)
        self.file_listbox.bind("<B1-Motion>", self._on_drag_motion)
        self.file_listbox.bind("<ButtonRelease-1>", self._on_drag_drop)
        # Keyboard bindings for removing files
        self.file_listbox.bind("<Delete>", self._on_delete_key)
        self.file_listbox.bind("<BackSpace>", self._on_delete_key)
        if _dnd_available:
            self.file_listbox.drop_target_register(DND_FILES)
            self.file_listbox.dnd_bind("<<Drop>>", self._on_external_drop)
            self.file_listbox.dnd_bind("<<DropEnter>>", self._on_drop_enter)
            self.file_listbox.dnd_bind("<<DropLeave>>", self._on_drop_leave)

        # Buttons for file operations
        btn_frame = tk.Frame(file_frame)
        btn_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        ttk.Button(
            btn_frame, text="Add Files", command=self.add_files, style="Dark.TButton"
        ).pack(side=tk.LEFT, padx=3)

        ttk.Button(
            btn_frame, text="Add Folder", command=self.add_folder, style="DarkAccent.TButton"
        ).pack(side=tk.LEFT, padx=3)

        ttk.Button(
            btn_frame, text="Remove Selected", command=self.remove_selected, style="RemoveBtn.TButton"
        ).pack(side=tk.LEFT, padx=3)

        ttk.Button(
            btn_frame, text="Clear All", command=self.clear_all, style="ClearBtn.TButton"
        ).pack(side=tk.LEFT, padx=3)

        # Output section
        output_frame = tk.LabelFrame(main_frame, text=" Output ", font=title_font)
        output_frame.pack(fill=tk.X, pady=(0, 10))

        output_inner = tk.Frame(output_frame)
        output_inner.pack(fill=tk.X, padx=10, pady=10)

        tk.Label(output_inner, text="Output file:", font=default_font).pack(side=tk.LEFT)
        tk.Entry(
            output_inner,
            textvariable=self.output_path,
            width=35,
            font=default_font,
            bd=2,
            highlightthickness=1,
        ).pack(side=tk.LEFT, padx=10, expand=True, fill=tk.X)
        ttk.Button(
            output_inner, text="Browse", command=self.browse_output, style="Browse.TButton"
        ).pack(side=tk.LEFT, padx=3)

        # Progress section
        progress_frame = tk.Frame(main_frame)
        progress_frame.pack(fill=tk.X, pady=(0, 10))

        self.progress_label = tk.Label(
            progress_frame, text="Ready to merge", font=default_font, fg="#7f8c8d"
        )
        self.progress_label.pack(side=tk.LEFT)

        # Merge button
        self.merge_btn = ttk.Button(
            main_frame, text="MERGE FILES", command=self.merge_files, style="Merge.TButton"
        )
        self.merge_btn.pack(fill=tk.X, pady=(5, 5))

        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        status_bar = tk.Label(
            self.root, textvariable=self.status_var,
            relief=tk.SUNKEN, anchor=tk.W,
            font=("Segoe UI", 9) if os.name == "nt" else ("Helvetica", 9),
            bg="#ecf0f1",
        )
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    # --- File Operations ---

    def add_files(self):
        """Add individual files via file dialog."""
        files = filedialog.askopenfilenames(
            title="Select files to merge",
            filetypes=[
                ("PDF files", "*.pdf"),
                ("Image files", "*.jpg *.jpeg *.png *.gif *.bmp *.tiff *.webp"),
                ("All files", "*.*"),
            ],
        )
        if files:
            for file_path in files:
                self.add_file_to_list(Path(file_path))

    def add_folder(self):
        """Add all supported files from a folder."""
        folder = filedialog.askdirectory(title="Select folder containing files")
        if folder:
            folder_path = Path(folder)
            for ext in [".pdf", ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".webp"]:
                for p in list(folder_path.glob(f"*{ext}")) + list(folder_path.glob(f"*{ext.upper()}")):
                    self.add_file_to_list(p)

    def add_file_to_list(self, file_path: Path):
        """Add a file to the list if not already present."""
        if file_path not in self.input_files:
            self.input_files.append(file_path)
            file_type = get_file_type(file_path.name)
            try:
                size = file_path.stat().st_size
            except OSError:
                size = 0
            self.file_listbox.insert(tk.END, f"{file_path.name} ({file_type}, {size} bytes)")
            self.update_status()

    def remove_selected(self):
        """Remove selected files from list."""
        selected = self.file_listbox.curselection()
        if not selected:
            return
        # Remove from model (in reverse order to preserve indices)
        for idx in sorted(selected, reverse=True):
            if 0 <= idx < len(self.input_files):
                del self.input_files[idx]
        # Remove from listbox (in reverse order)
        for idx in sorted(selected, reverse=True):
            self.file_listbox.delete(idx)
        self.update_status()

    def clear_all(self):
        """Clear all files from list."""
        self.file_listbox.delete(0, tk.END)
        self.input_files.clear()
        self.update_status()

    def browse_output(self):
        """Browse for output file location."""
        file = filedialog.asksaveasfilename(
            title="Save merged PDF as",
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
        )
        if file:
            self.output_path.set(file)

    def update_status(self):
        """Update status with file count."""
        count = len(self.input_files)
        if self.progress_label:
            self.progress_label.config(text=f"{count} file(s) selected for merging")
        if self.status_var:
            if count == 0:
                self.status_var.set("Ready")
            else:
                self.status_var.set(f"{count} file(s) ready to merge")

    def move_up(self):
        """Move selected items up in the list."""
        selected = self.file_listbox.curselection()
        if not selected:
            return
        first = selected[0]
        if first == 0:
            return
        # Swap in model
        self.input_files[first], self.input_files[first - 1] = self.input_files[first - 1], self.input_files[first]
        # Swap in listbox
        text_above = self.file_listbox.get(first - 1)
        text_current = self.file_listbox.get(first)
        self.file_listbox.delete(first)
        self.file_listbox.delete(first - 1)
        self.file_listbox.insert(first - 1, text_current)
        self.file_listbox.insert(first, text_above)
        # Re-select
        self.file_listbox.selection_clear(0, tk.END)
        self.file_listbox.selection_set(first - 1)
        self.file_listbox.see(first - 1)
        self.update_status()

    def move_down(self):
        """Move selected items down in the list."""
        selected = self.file_listbox.curselection()
        if not selected:
            return
        last = selected[-1]
        if last == len(self.input_files) - 1:
            return
        # Swap in model
        self.input_files[last], self.input_files[last + 1] = self.input_files[last + 1], self.input_files[last]
        # Swap in listbox
        text_below = self.file_listbox.get(last + 1)
        text_current = self.file_listbox.get(last)
        self.file_listbox.delete(last + 1)
        self.file_listbox.delete(last)
        self.file_listbox.insert(last, text_below)
        self.file_listbox.insert(last + 1, text_current)
        # Re-select
        self.file_listbox.selection_clear(0, tk.END)
        self.file_listbox.selection_set(last + 1)
        self.file_listbox.see(last + 1)
        self.update_status()

    # --- Drag and Drop ---

    def _on_drag_start(self, event):
        """Handle drag start - record the item being dragged."""
        index = self.file_listbox.nearest(event.y)
        bbox = self.file_listbox.bbox(index)
        if bbox is not None:
            self.drag_start_index = index
            self.drag_data["index"] = index
            self.drag_data["item"] = self.file_listbox.get(index)
            self.file_listbox.selection_clear(0, tk.END)
            self.file_listbox.selection_set(index)
            self.file_listbox.activate(index)
            # Store initial Y position for detecting drag vs click
            self.drag_data["start_y"] = event.y
            self.drag_data["is_dragging"] = False

    def _on_drag_motion(self, event):
        """Handle drag motion - detect drag and show visual feedback."""
        if self.drag_data["index"] is None:
            return
        # Auto-scroll when dragging near edges
        y = event.y
        top_margin = 30
        bottom_margin = self.file_listbox.winfo_height() - 30
        if y < top_margin:
            self.file_listbox.yview_scroll(-1, "unit")
        elif y > bottom_margin:
            self.file_listbox.yview_scroll(1, "unit")
        # Highlight the item under cursor as potential drop target
        target = self.file_listbox.nearest(event.y)
        if target != self.drag_data["index"]:
            self.file_listbox.selection_clear(0, tk.END)
            self.file_listbox.selection_set(target)

    def _on_drag_drop(self, event):
        """Handle drop - reorder files."""
        if self.drag_data["index"] is None:
            self.drag_data = {"index": None, "item": None}
            self.drag_start_index = None
            return

        # Only reorder if we actually dragged (moved more than 5 pixels)
        start_y = self.drag_data.get("start_y", 0)
        if abs(event.y - start_y) < 5:
            # Just a click, not a drag
            self.drag_data = {"index": None, "item": None}
            self.drag_start_index = None
            return

        target_index = self.file_listbox.nearest(event.y)
        start_index = self.drag_data["index"]

        if target_index != start_index:
            # Swap in the model
            self.input_files[start_index], self.input_files[target_index] = \
                self.input_files[target_index], self.input_files[start_index]
            # Swap in listbox
            self.file_listbox.delete(start_index)
            self.file_listbox.insert(target_index, self.drag_data["item"])
            # Re-select the moved item
            self.file_listbox.selection_clear(0, tk.END)
            self.file_listbox.selection_set(target_index)

        self.update_status()
        self.drag_data = {"index": None, "item": None}
        self.drag_start_index = None

    def _on_delete_key(self, event):
        """Handle Delete/BackSpace key to remove selected files."""
        self.remove_selected()

    def _on_drop_enter(self, event):
        """Visual feedback when a file enters the drop area."""
        self.file_listbox.configure(highlightbackground="#2196F3", highlightthickness=3)

    def _on_drop_leave(self, event):
        """Visual feedback when a file leaves the drop area."""
        self.file_listbox.configure(highlightbackground="#BDC3C7", highlightthickness=1)

    def _on_external_drop(self, event):
        """Handle dropping files from the file system."""
        # Get the dropped file paths
        files = self.root.tk.splitlist(event.data)
        if not files:
            return
        # Add only .pdf and image files
        valid_extensions = {".pdf", ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff", ".webp"}
        for f in files:
            # Files from drag-and-drop may come as file:// URLs or plain paths
            # Normalize to a Path object
            if f.startswith("file://"):
                # Remove file:// prefix and handle URL encoding
                from urllib.parse import unquote
                f = unquote(f[len("file://"):])
            file_path = Path(f)
            # Skip if file doesn't exist
            if not file_path.exists():
                continue
            if (
                file_path.suffix.lower() in valid_extensions
                and file_path not in self.input_files
            ):
                self.add_file_to_list(file_path)
        # Visual feedback - reset after a moment
        self.file_listbox.configure(highlightbackground="#2196F3", highlightthickness=3)
        self.root.after(500, lambda: self.file_listbox.configure(highlightbackground="#BDC3C7", highlightthickness=1))

    # --- Merge ---

    def merge_files(self):
        """Trigger the merge operation."""
        if not self.input_files:
            messagebox.showwarning("No files", "Please add files to merge first.")
            return

        self.merge_btn.config(state=tk.DISABLED)
        self.status_var.set("Merging files...")
        self.progress_label.config(text="Merging in progress...", fg="#e67e22")

        merge_thread = threading.Thread(target=self._do_merge)
        merge_thread.daemon = True
        merge_thread.start()

    def _do_merge(self):
        """Perform the actual merge operation."""
        try:
            output_file = Path(self.output_path.get())
            if not output_file.suffix.lower():
                output_file = output_file.with_suffix(".pdf")

            merge_pdfs(self.input_files, output_file)

            self.root.after(0, lambda: [
                self.merge_btn.config(state=tk.NORMAL),
                self.progress_label.config(
                    text=f"Merged {len(self.input_files)} file(s) into {output_file.name}",
                    fg="#2E7D32"
                ),
                messagebox.showinfo(
                    "Success",
                    f"Successfully merged {len(self.input_files)} file(s)!\n\nOutput: {output_file}"
                ),
            ])

        except Exception as e:  # noqa: BLE001 - report any merge failure in the GUI
            error_message = str(e)
            self.root.after(0, lambda: [
                self.merge_btn.config(state=tk.NORMAL),
                self.status_var.set("Error occurred"),
                self.progress_label.config(text=f"Error: {error_message}", fg="#e74c3c"),
                messagebox.showerror(
                    "Merge Error",
                    f"An error occurred during merging:\n\n{error_message}"
                ),
            ])


def run_gui():
    """Launch the PDF Merger GUI."""
    if _dnd_available:
        root = TkinterDnD.Tk()
    else:
        root = tk.Tk()
    PDFMergerApp(root)
    root.mainloop()


if __name__ == "__main__":
    run_gui()
