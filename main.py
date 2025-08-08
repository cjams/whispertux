#!/usr/bin/env python3
"""
WhisperTux - Voice dictation application for Linux
"""

import tkinter as tk
from tkinter import ttk, messagebox
import ttkbootstrap as ttk_style
from ttkbootstrap.constants import *
import threading
import time
import os
import sys
from pathlib import Path

# Import our custom modules
from src.audio_capture import AudioCapture
from src.whisper_manager import WhisperManager
from src.text_injector import TextInjector
from src.config_manager import ConfigManager
from src.global_shortcuts import GlobalShortcuts
from src.waveform_visualizer import WaveformVisualizer


class SettingsDialog:
    """Settings configuration dialog for WhisperTux"""

    def __init__(self, parent, config, global_shortcuts, update_callback, text_injector=None, app_instance=None):
        self.parent = parent
        self.config = config
        self.global_shortcuts = global_shortcuts
        self.update_callback = update_callback
        self.text_injector = text_injector
        self.app_instance = app_instance

        # Dialog window
        self.dialog = None
        self.shortcut_var = None
        self.shortcut_combo = None
        self.test_button = None
        self.apply_button = None
        self.current_shortcut_label = None

        self._create_dialog()

    def _create_dialog(self):
        """Create the settings dialog window"""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("WhisperTux Settings")
        self.dialog.geometry("520x600")
        self.dialog.resizable(True, True)
        self.dialog.minsize(520, 400)
        self.dialog.transient(self.parent)
        self.dialog.grab_set()

        # Center the dialog on parent window
        self._center_dialog()

        # Create scrollable container
        self._create_scrollable_dialog_frame()


        # Global Shortcuts Section
        self._create_shortcuts_section(self.scrollable_dialog_frame)

        # Model Settings Section
        self._create_model_section(self.scrollable_dialog_frame)

        # Additional Settings Section
        self._create_general_section(self.scrollable_dialog_frame)

        # Word Overrides Section
        self._create_word_overrides_section(self.scrollable_dialog_frame)

        # Buttons
        self._create_buttons(self.scrollable_dialog_frame)

    def _create_scrollable_dialog_frame(self):
        """Create a scrollable frame for the settings dialog"""
        # Create canvas and scrollbar
        self.dialog_canvas = tk.Canvas(self.dialog, highlightthickness=0)
        self.dialog_scrollbar = ttk.Scrollbar(self.dialog, orient="vertical", command=self.dialog_canvas.yview)
        self.scrollable_dialog_frame = ttk.Frame(self.dialog_canvas)

        # Configure scrolling
        self.scrollable_dialog_frame.bind(
            "<Configure>",
            lambda e: self.dialog_canvas.configure(scrollregion=self.dialog_canvas.bbox("all"))
        )

        # Create window in canvas
        self.dialog_canvas_window = self.dialog_canvas.create_window((0, 0), window=self.scrollable_dialog_frame, anchor="nw")
        self.dialog_canvas.configure(yscrollcommand=self.dialog_scrollbar.set)

        # Bind canvas resize to update scroll region
        def on_dialog_canvas_configure(event):
            self.dialog_canvas.itemconfig(self.dialog_canvas_window, width=event.width)
        self.dialog_canvas.bind('<Configure>', on_dialog_canvas_configure)

        # Bind mousewheel to scroll
        def on_dialog_mousewheel(event):
            self.dialog_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        def bind_dialog_mousewheel(event):
            self.dialog_canvas.bind_all("<MouseWheel>", on_dialog_mousewheel)

        def unbind_dialog_mousewheel(event):
            self.dialog_canvas.unbind_all("<MouseWheel>")

        self.dialog_canvas.bind('<Enter>', bind_dialog_mousewheel)
        self.dialog_canvas.bind('<Leave>', unbind_dialog_mousewheel)

        # Pack canvas and scrollbar with proper spacing
        self.dialog_canvas.pack(side="left", fill="both", expand=True, padx=(20, 10), pady=20)
        self.dialog_scrollbar.pack(side="right", fill="y", padx=(10, 20), pady=20)

    def _center_dialog(self):
        """Center the dialog on the parent window"""
        self.dialog.update_idletasks()

        parent_x = self.parent.winfo_rootx()
        parent_y = self.parent.winfo_rooty()
        parent_width = self.parent.winfo_width()
        parent_height = self.parent.winfo_height()

        dialog_width = self.dialog.winfo_reqwidth()
        dialog_height = self.dialog.winfo_reqheight()

        x = parent_x + (parent_width - dialog_width) // 2
        y = parent_y + (parent_height - dialog_height) // 2

        self.dialog.geometry(f"+{x}+{y}")

    def _create_shortcuts_section(self, parent):
        """Create the global shortcuts configuration section"""
        shortcuts_frame = ttk.LabelFrame(parent, text="Global Shortcuts", padding=15)
        shortcuts_frame.pack(fill=X, pady=(0, 15))

        # Instructions
        info_label = ttk.Label(
            shortcuts_frame,
            text="Select a global shortcut key for voice recording:",
            font=("Arial", 10),
            bootstyle=INFO
        )
        info_label.pack(anchor=W, pady=(0, 10))

        # Current shortcut display
        current_frame = ttk.Frame(shortcuts_frame)
        current_frame.pack(fill=X, pady=(0, 10))

        ttk.Label(current_frame, text="Current Shortcut:").pack(side=LEFT)
        self.current_shortcut_label = ttk.Label(
            current_frame,
            text=self.config.get_setting('primary_shortcut', 'F12'),
            font=("Arial", 10, "bold"),
            bootstyle=SUCCESS
        )
        self.current_shortcut_label.pack(side=RIGHT)

        # New shortcut selection
        selection_frame = ttk.Frame(shortcuts_frame)
        selection_frame.pack(fill=X, pady=(0, 10))

        ttk.Label(selection_frame, text="New Shortcut:").pack(side=LEFT)

        # Available shortcut options
        shortcut_options = [
            'F1', 'F2', 'F3', 'F4', 'F5', 'F6',
            'F7', 'F8', 'F9', 'F10', 'F11', 'F12',
            'Ctrl+X',
            'Ctrl+F1', 'Ctrl+F2', 'Ctrl+F3', 'Ctrl+F4',
            'Ctrl+F5', 'Ctrl+F6', 'Ctrl+F7', 'Ctrl+F8',
            'Ctrl+F9', 'Ctrl+F10', 'Ctrl+F11', 'Ctrl+F12',
            'Alt+F1', 'Alt+F2', 'Alt+F3', 'Alt+F4',
            'Alt+F5', 'Alt+F6', 'Alt+F7', 'Alt+F8',
            'Alt+F9', 'Alt+F10', 'Alt+F11', 'Alt+F12',
            'Shift+F1', 'Shift+F2', 'Shift+F3', 'Shift+F4',
            'Shift+F5', 'Shift+F6', 'Shift+F7', 'Shift+F8',
            'Shift+F9', 'Shift+F10', 'Shift+F11', 'Shift+F12',
            'Super+F1', 'Super+F2', 'Super+F3', 'Super+F4',
            'Super+F5', 'Super+F6', 'Super+F7', 'Super+F8',
            'Super+F9', 'Super+F10', 'Super+F11', 'Super+F12',
            'Super+X'
        ]

        # Add Ctrl + letter combinations
        for letter in 'abcdefghijklmnopqrstuvwxyz':
            shortcut_options.append(f'Ctrl+{letter.upper()}')

        # Add Ctrl + Shift + letter combinations
        for letter in 'abcdefghijklmnopqrstuvwxyz':
            shortcut_options.append(f'Ctrl+Shift+{letter.upper()}')

        # Add Super + letter combinations
        for letter in 'abcdefghijklmnopqrstuvwxyz':
            shortcut_options.append(f'Super+{letter.upper()}')

        # Add Ctrl + Super + letter combinations
        for letter in 'abcdefghijklmnopqrstuvwxyz':
            shortcut_options.append(f'Ctrl+Super+{letter.upper()}')

        # Add Super + Alt + letter combinations
        for letter in 'abcdefghijklmnopqrstuvwxyz':
            shortcut_options.append(f'Super+Alt+{letter.upper()}')

        # Add Ctrl + Alt + letter combinations
        for letter in 'abcdefghijklmnopqrstuvwxyz':
            shortcut_options.append(f'Ctrl+Alt+{letter.upper()}')

        self.shortcut_var = tk.StringVar(value=self.config.get_setting('primary_shortcut', 'F12'))
        self.shortcut_combo = ttk.Combobox(
            selection_frame,
            textvariable=self.shortcut_var,
            values=shortcut_options,
            state="readonly",
            width=15
        )
        self.shortcut_combo.pack(side=RIGHT)

        # Test shortcut button
        test_frame = ttk.Frame(shortcuts_frame)
        test_frame.pack(fill=X, pady=(10, 0))

        self.test_button = ttk.Button(
            test_frame,
            text="Test Shortcut",
            command=self._test_shortcut,
            bootstyle=INFO,
            width=15
        )
        self.test_button.pack(side=LEFT)

        # Status label for test results
        self.test_status_label = ttk.Label(
            test_frame,
            text="",
            font=("Arial", 9),
        )
        self.test_status_label.pack(side=RIGHT, padx=(10, 0))

    def _create_model_section(self, parent):
        """Create the model configuration section"""
        model_frame = ttk.LabelFrame(parent, text="Model", padding=15)
        model_frame.pack(fill=X, pady=(0, 15))

        # Model selection
        model_selection_frame = ttk.Frame(model_frame)
        model_selection_frame.pack(fill=X, pady=(0, 10))

        ttk.Label(model_selection_frame, text="Whisper Model:").pack(side=LEFT)

        # Get available models from whisper manager
        try:
            # Access the parent's whisper manager through the parent window
            available_models = []
            if hasattr(self.parent, 'whisper_manager'):
                available_models = self.parent.whisper_manager.get_available_models()
            if not available_models:
                available_models = ["No models found"]
        except:
            available_models = ["No models found"]

        self.model_var = tk.StringVar(value=self.config.get_setting('model', 'base'))
        self.model_combo_dialog = ttk.Combobox(
            model_selection_frame,
            textvariable=self.model_var,
            values=available_models,
            state="readonly",
            width=15
        )
        self.model_combo_dialog.pack(side=RIGHT)

        # Set current model if it exists
        current_model = self.config.get_setting('model', 'base')
        if current_model in available_models:
            self.model_var.set(current_model)
        elif available_models and available_models[0] != "No models found":
            self.model_var.set(available_models[0])

        # Download Models button
        download_frame = ttk.Frame(model_frame)
        download_frame.pack(fill=X, pady=(10, 0))

        download_button = ttk.Button(
            download_frame,
            text="Download Models",
            command=self._show_model_download_from_settings,
            bootstyle=INFO,
            width=15
        )
        download_button.pack(side=RIGHT)

    def _create_general_section(self, parent):
        """Create the general settings section"""
        general_frame = ttk.LabelFrame(parent, text="General Settings", padding=15)
        general_frame.pack(fill=X, pady=(0, 15))

        # Always on top setting
        always_on_top_frame = ttk.Frame(general_frame)
        always_on_top_frame.pack(fill=X, pady=(0, 5))

        self.always_on_top_var = tk.BooleanVar(value=self.config.get_setting('always_on_top', True))
        always_on_top_check = ttk.Checkbutton(
            always_on_top_frame,
            text="Keep window always on top",
            variable=self.always_on_top_var,
            bootstyle="round-toggle"
        )
        always_on_top_check.pack(anchor=W)

        # Use clipboard option (moved above typing speed)
        clipboard_frame = ttk.Frame(general_frame)
        clipboard_frame.pack(fill=X, pady=(5, 5))

        self.use_clipboard_var = tk.BooleanVar(value=self.config.get_setting('use_clipboard', False))
        clipboard_check = ttk.Checkbutton(
            clipboard_frame,
            text="Use clipboard for text injection (alternative method)",
            variable=self.use_clipboard_var,
            bootstyle="round-toggle"
        )
        clipboard_check.pack(anchor=W)

        # Typing speed setting
        typing_frame = ttk.Frame(general_frame)
        typing_frame.pack(fill=X, pady=(5, 5))

        ttk.Label(typing_frame, text="Typing Speed (chars/min):").pack(side=LEFT)

        self.typing_speed_var = tk.IntVar(value=self.config.get_setting('typing_speed', 150))
        typing_spin = ttk.Spinbox(
            typing_frame,
            from_=50,
            to=500,
            increment=25,
            textvariable=self.typing_speed_var,
            width=10
        )
        typing_spin.pack(side=RIGHT)

        # Keyboard device selection
        keyboard_frame = ttk.Frame(general_frame)
        keyboard_frame.pack(fill=X, pady=(5, 0))

        ttk.Label(keyboard_frame, text="Keyboard Device:").pack(side=LEFT)

        # Get available keyboards
        try:
            from src.global_shortcuts import get_available_keyboards
            available_keyboards = get_available_keyboards()

            keyboard_options = ["Auto-detect (All Keyboards)"]
            keyboard_values = [""]

            for kb in available_keyboards:
                keyboard_options.append(kb['display_name'])
                keyboard_values.append(kb['path'])

            self.keyboard_options = keyboard_options
            self.keyboard_values = keyboard_values

        except Exception as e:
            print(f"Error getting keyboard devices: {e}")
            keyboard_options = ["Auto-detect (All Keyboards)"]
            keyboard_values = [""]
            self.keyboard_options = keyboard_options
            self.keyboard_values = keyboard_values

        # Find current selection
        current_device = self.config.get_setting('keyboard_device', '')
        current_index = 0
        if current_device in keyboard_values:
            current_index = keyboard_values.index(current_device)

        self.keyboard_device_var = tk.StringVar(value=keyboard_options[current_index])
        keyboard_combo = ttk.Combobox(
            keyboard_frame,
            textvariable=self.keyboard_device_var,
            values=keyboard_options,
            state="readonly",
            width=35
        )
        keyboard_combo.pack(side=RIGHT)

    def _create_word_overrides_section(self, parent):
        """Create the word overrides configuration section"""
        overrides_frame = ttk.LabelFrame(parent, text="Word Overrides", padding=15)
        overrides_frame.pack(fill=X, pady=(0, 15))

        # Instructions
        info_label = ttk.Label(
            overrides_frame,
            text="Configure word replacements (e.g., 'tech' → 'tek'):",
            font=("Arial", 10),
            bootstyle=INFO
        )
        info_label.pack(anchor=W, pady=(0, 10))

        # Current overrides list
        list_frame = ttk.Frame(overrides_frame)
        list_frame.pack(fill=X, pady=(0, 10))

        # Create treeview for overrides list
        columns = ('original', 'replacement')
        self.overrides_tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=4)
        self.overrides_tree.heading('original', text='Original')
        self.overrides_tree.heading('replacement', text='Replacement')
        self.overrides_tree.column('original', width=120)
        self.overrides_tree.column('replacement', width=120)

        # Scrollbar for treeview
        tree_scrollbar = ttk.Scrollbar(list_frame, orient=VERTICAL, command=self.overrides_tree.yview)
        self.overrides_tree.configure(yscrollcommand=tree_scrollbar.set)

        self.overrides_tree.pack(side=LEFT, fill=BOTH, expand=True)
        tree_scrollbar.pack(side=RIGHT, fill=Y)

        # Load current overrides
        self._refresh_overrides_list()

        # Add new override section
        add_frame = ttk.Frame(overrides_frame)
        add_frame.pack(fill=X, pady=(10, 10))

        # Entry fields for new override
        ttk.Label(add_frame, text="Add Override:", font=("Arial", 9, "bold")).pack(anchor=W)

        input_frame = ttk.Frame(add_frame)
        input_frame.pack(fill=X, pady=(5, 0))

        ttk.Label(input_frame, text="Original:").pack(side=LEFT)
        self.original_entry = ttk.Entry(input_frame, width=15)
        self.original_entry.pack(side=LEFT, padx=(5, 10))

        ttk.Label(input_frame, text="→").pack(side=LEFT)

        ttk.Label(input_frame, text="Replacement:").pack(side=LEFT, padx=(10, 5))
        self.replacement_entry = ttk.Entry(input_frame, width=15)
        self.replacement_entry.pack(side=LEFT, padx=(5, 10))

        # Buttons for managing overrides
        buttons_frame = ttk.Frame(overrides_frame)
        buttons_frame.pack(fill=X, pady=(10, 0))

        add_button = ttk.Button(
            buttons_frame,
            text="Add",
            command=self._add_word_override,
            bootstyle=SUCCESS,
            width=8
        )
        add_button.pack(side=LEFT)

        edit_button = ttk.Button(
            buttons_frame,
            text="Edit",
            command=self._edit_word_override,
            bootstyle=INFO,
            width=8
        )
        edit_button.pack(side=LEFT, padx=(5, 0))

        delete_button = ttk.Button(
            buttons_frame,
            text="Delete",
            command=self._delete_word_override,
            bootstyle=WARNING,
            width=8
        )
        delete_button.pack(side=LEFT, padx=(5, 0))

        clear_all_button = ttk.Button(
            buttons_frame,
            text="Clear All",
            command=self._clear_all_overrides,
            bootstyle=DANGER,
            width=8
        )
        clear_all_button.pack(side=RIGHT)

        # Bind double-click to edit
        self.overrides_tree.bind('<Double-1>', lambda e: self._edit_word_override())

    def _refresh_overrides_list(self):
        """Refresh the word overrides list display"""
        # Clear current items
        for item in self.overrides_tree.get_children():
            self.overrides_tree.delete(item)

        # Load overrides from config
        word_overrides = self.config.get_word_overrides()

        # Add items to tree
        for original, replacement in word_overrides.items():
            self.overrides_tree.insert('', 'end', values=(original, replacement))

    def _add_word_override(self):
        """Add a new word override"""
        original = self.original_entry.get().strip()
        replacement = self.replacement_entry.get().strip()

        if not original or not replacement:
            messagebox.showwarning("Invalid Input", "Both original and replacement words are required.")
            return

        # Add/update override
        self.config.add_word_override(original, replacement)
        self._refresh_overrides_list()

        # Clear entry fields
        self.original_entry.delete(0, tk.END)
        self.replacement_entry.delete(0, tk.END)

    def _edit_word_override(self):
        """Edit the selected word override"""
        selection = self.overrides_tree.selection()
        if not selection:
            return

        # Get selected item values
        item = selection[0]
        values = self.overrides_tree.item(item, 'values')
        original, replacement = values

        # Populate entry fields with current values
        self.original_entry.delete(0, tk.END)
        self.original_entry.insert(0, original)
        self.replacement_entry.delete(0, tk.END)
        self.replacement_entry.insert(0, replacement)

        # Remove the old override (we'll add the new one when user clicks Add)
        self.config.remove_word_override(original)
        self._refresh_overrides_list()

    def _delete_word_override(self):
        """Delete the selected word override"""
        selection = self.overrides_tree.selection()
        if not selection:
            return

        # Get selected item values
        item = selection[0]
        values = self.overrides_tree.item(item, 'values')
        original = values[0]

        self.config.remove_word_override(original)
        self._refresh_overrides_list()

    def _clear_all_overrides(self):
        """Clear all word overrides"""
        self.config.clear_word_overrides()
        self._refresh_overrides_list()

    def _create_buttons(self, parent):
        """Create dialog action buttons"""
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill=X, pady=(20, 0))

        # Cancel button
        cancel_button = ttk.Button(
            button_frame,
            text="✖️ Cancel",
            command=self._cancel,
            bootstyle=SECONDARY,
            width=12
        )
        cancel_button.pack(side=LEFT)

        # Reset to defaults button
        reset_button = ttk.Button(
            button_frame,
            text="Reset to Defaults",
            command=self._reset_defaults,
            bootstyle=WARNING,
            width=15
        )
        reset_button.pack(side=LEFT, padx=(10, 0))

        # Save Settings button
        self.save_button = ttk.Button(
            button_frame,
            text="Save Settings",
            command=self._save_settings,
            bootstyle=SUCCESS,
            width=15
        )
        self.save_button.pack(side=RIGHT)

    def _test_shortcut(self):
        """Test the selected shortcut"""
        selected_shortcut = self.shortcut_var.get()

        if not selected_shortcut:
            self.test_status_label.config(text="ERROR: No shortcut selected", bootstyle=DANGER)
            return

        self.test_status_label.config(text="🔄 Testing...", bootstyle=WARNING)
        self.test_button.config(state=DISABLED)
        self.dialog.update()

        def test_shortcut_thread():
            try:
                # Create a temporary global shortcuts instance for testing
                test_triggered = threading.Event()

                def test_callback():
                    test_triggered.set()

                # Create test shortcuts instance
                from src.global_shortcuts import GlobalShortcuts
                test_shortcuts = GlobalShortcuts(selected_shortcut, test_callback)

                if test_shortcuts.start():
                    # Wait for test trigger
                    self.dialog.after(100, lambda: self.test_status_label.config(
                        text=f"Press {selected_shortcut} within 5 seconds...",
                        bootstyle=INFO
                    ))

                    if test_triggered.wait(timeout=5):
                        self.dialog.after(100, lambda: self.test_status_label.config(
                            text="✅ Test successful!",
                            bootstyle=SUCCESS
                        ))
                        result = True
                    else:
                        self.dialog.after(100, lambda: self.test_status_label.config(
                            text="❌ Test failed - no response",
                            bootstyle=DANGER
                        ))
                        result = False

                    test_shortcuts.stop()
                else:
                    self.dialog.after(100, lambda: self.test_status_label.config(
                        text="❌ Could not start test",
                        bootstyle=DANGER
                    ))
                    result = False

            except Exception as e:
                self.dialog.after(100, lambda: self.test_status_label.config(
                    text=f"❌ Test error: {str(e)[:20]}...",
                    bootstyle=DANGER
                ))
            finally:
                self.dialog.after(100, lambda: self.test_button.config(state=NORMAL))

        # Run test in background thread
        test_thread = threading.Thread(target=test_shortcut_thread, daemon=True)
        test_thread.start()

    def _save_settings(self):
        """Save all settings and apply them"""
        try:
            # Get current values from dialog
            new_shortcut = self.shortcut_var.get()
            old_shortcut = self.config.get_setting('primary_shortcut')

            # Get keyboard device selection
            selected_keyboard_index = self.keyboard_options.index(self.keyboard_device_var.get())
            selected_keyboard_path = self.keyboard_values[selected_keyboard_index]

            # Update all settings in config
            self.config.set_setting('primary_shortcut', new_shortcut)
            self.config.set_setting('always_on_top', self.always_on_top_var.get())
            self.config.set_setting('typing_speed', self.typing_speed_var.get())
            self.config.set_setting('use_clipboard', self.use_clipboard_var.get())
            self.config.set_setting('keyboard_device', selected_keyboard_path)

            # Update model setting if changed
            new_model = self.model_var.get()
            if new_model != "No models found":
                self.config.set_setting('model', new_model)
                # Update the parent's whisper manager
                if hasattr(self.parent, 'whisper_manager'):
                    try:
                        self.parent.whisper_manager.set_model(new_model)
                    except Exception as e:
                        print(f"Failed to update model: {e}")

            # Save configuration to file
            if not self.config.save_config():
                messagebox.showerror("Error", "Failed to save settings to file!")
                return

            # Update parent window's always on top setting
            self.parent.attributes('-topmost', self.always_on_top_var.get())

            # Handle shortcut changes
            shortcut_update_success = True
            if new_shortcut != old_shortcut:
                if self.global_shortcuts:
                    print(f"Updating global shortcut from {old_shortcut} to {new_shortcut}")
                    # Stop the current shortcuts listener
                    self.global_shortcuts.stop()

                    # Update the shortcut key
                    self.global_shortcuts.update_shortcut(new_shortcut)

                    # Start the listener with the new shortcut
                    if not self.global_shortcuts.start():
                        print("Failed to restart global shortcuts")
                        messagebox.showwarning("Warning",
                            f"Settings saved successfully, but failed to activate shortcut '{new_shortcut}'. "
                            f"The shortcut may not work until application restart.")
                        shortcut_update_success = False
                    else:
                        print(f"Successfully activated new shortcut: {new_shortcut}")
                        shortcut_update_success = True

            # Update the current shortcut display in the dialog
            if self.current_shortcut_label:
                self.current_shortcut_label.config(text=new_shortcut)

            # Call the update callback to refresh main window display
            if self.update_callback:
                self.update_callback()

            # Close the dialog (settings saved successfully)
            self._close_dialog()

        except Exception as e:
            messagebox.showerror("Error", f"Failed to save settings: {e}")
            print(f"Settings save error: {e}")

    def _apply_settings(self):
        """Apply the settings changes"""
        try:
            # Update shortcut configuration
            new_shortcut = self.shortcut_var.get()
            old_shortcut = self.config.get_setting('primary_shortcut')

            if new_shortcut != old_shortcut:
                self.config.set_setting('primary_shortcut', new_shortcut)

                # Restart global shortcuts with new key
                if self.global_shortcuts:
                    print(f"Updating global shortcut from {old_shortcut} to {new_shortcut}")
                    self.global_shortcuts.stop()
                    self.global_shortcuts.update_shortcut(new_shortcut)
                    if not self.global_shortcuts.start():
                        print("Failed to restart global shortcuts")
                        messagebox.showwarning("Warning", f"Failed to activate shortcut '{new_shortcut}'. The shortcut has been saved but may not work until application restart.")
                    else:
                        print(f"Successfully activated new shortcut: {new_shortcut}")

            # Update other settings
            self.config.set_setting('always_on_top', self.always_on_top_var.get())
            self.config.set_setting('typing_speed', self.typing_speed_var.get())
            self.config.set_setting('use_clipboard', self.use_clipboard_var.get())

            # Save configuration
            if self.config.save_config():
                # Update parent window's always on top setting
                self.parent.attributes('-topmost', self.always_on_top_var.get())

                # Update the current shortcut display in the dialog
                if self.current_shortcut_label and new_shortcut:
                    self.current_shortcut_label.config(text=new_shortcut)

                # Call the update callback to refresh main window display
                if self.update_callback:
                    self.update_callback()

                messagebox.showinfo("Settings", "Settings applied successfully!")
                self._close_dialog()
            else:
                messagebox.showerror("Error", "Failed to save settings!")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to apply settings: {e}")

    def _reset_defaults(self):
        """Reset settings to defaults"""
        if messagebox.askyesno("Reset Settings", "Are you sure you want to reset all settings to defaults?"):
            try:
                # Reset config to defaults
                self.config.reset_to_defaults()

                # Update dialog controls
                new_shortcut = self.config.get_setting('primary_shortcut')
                self.shortcut_var.set(new_shortcut)
                self.always_on_top_var.set(self.config.get_setting('always_on_top'))
                self.typing_speed_var.set(self.config.get_setting('typing_speed'))
                self.use_clipboard_var.set(self.config.get_setting('use_clipboard'))

                # Update the current shortcut display in the dialog
                if self.current_shortcut_label:
                    self.current_shortcut_label.config(text=new_shortcut)

                # Refresh word overrides list (will be empty after reset)
                if hasattr(self, '_refresh_overrides_list'):
                    self._refresh_overrides_list()

                # Clear override entry fields
                if hasattr(self, 'original_entry') and hasattr(self, 'replacement_entry'):
                    self.original_entry.delete(0, tk.END)
                    self.replacement_entry.delete(0, tk.END)

                self.test_status_label.config(text="Settings reset to defaults", bootstyle=INFO)

            except Exception as e:
                messagebox.showerror("Error", f"Failed to reset settings: {e}")

    def _show_model_download_from_settings(self):
        """Show model download dialog from settings"""
        # Just delegate to the app instance's method
        if self.app_instance and hasattr(self.app_instance, '_show_model_download'):
            # Pass a callback to refresh this dialog's model combo after download
            self.app_instance._show_model_download(callback=self._refresh_model_combo_dialog)

    def _refresh_model_combo_dialog(self):
        """Refresh the model combo box in this settings dialog"""
        try:
            # Get updated available models
            available_models = []
            if self.app_instance and hasattr(self.app_instance, 'whisper_manager'):
                available_models = self.app_instance.whisper_manager.get_available_models()
            if not available_models:
                available_models = ["No models found"]

            # Update the combo box values
            if hasattr(self, 'model_combo_dialog') and self.model_combo_dialog:
                self.model_combo_dialog['values'] = available_models

                # Update current selection if needed
                current_model = self.config.get_setting('model', 'base')
                if current_model in available_models:
                    self.model_var.set(current_model)
                elif available_models and available_models[0] != "No models found":
                    self.model_var.set(available_models[0])

                print(f"Refreshed settings dialog model combo with: {available_models}")
        except Exception as e:
            print(f"Error refreshing settings dialog model combo: {e}")

    def _cancel(self):
        """Cancel settings dialog"""
        self._close_dialog()

    def _close_dialog(self):
        """Close the settings dialog"""
        if self.dialog:
            self.dialog.grab_release()
            self.dialog.destroy()

class WhisperTuxApp:
    """Main application class for WhisperTux voice dictation"""

    def __init__(self):
        # Initialize core components first
        self.config = ConfigManager()

        # Initialize audio capture with configured device
        audio_device_id = self.config.get_setting('audio_device', None)
        self.audio_capture = AudioCapture(device_id=audio_device_id)

        self.whisper_manager = WhisperManager()
        self.text_injector = TextInjector(self.config)
        self.global_shortcuts = None

        # Application state
        self.is_recording = False
        self.is_processing = False
        self.current_transcription = ""

        # GUI components
        self.root = None
        self.main_frame = None
        self.status_label = None
        self.record_button = None
        self.transcription_text = None
        self.waveform_visualizer = None
        self.model_combo = None
        self.shortcut_display_label = None

        # Initialize GUI
        self._setup_gui()
        self._setup_global_shortcuts()

    def _setup_gui(self):
        """Initialize the main GUI window with ttkbootstrap styling"""

        # Create main window with ttkbootstrap
        self.root = ttk_style.Window(
            title="WhisperTux - Voice Dictation",
            themename="darkly",
            size=(480, 600),
            resizable=(True, True),
            minsize=(480, 500)
        )

        # Configure window properties to match the electron version
        self.root.attributes('-topmost', True)  # Always on top
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)

        # Position window in top-right corner (similar to electron version)
        self._position_window()

        # Create scrollable main container
        self._create_scrollable_main_frame()

        # Create GUI sections
        self._create_header()
        self._create_status_section()
        self._create_audio_section()
        self._create_transcription_section()
        self._create_control_buttons()


    def _create_scrollable_main_frame(self):
        """Create a scrollable main frame for the application"""
        # Create canvas and scrollbar
        self.canvas = tk.Canvas(self.root, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self.root, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)

        # Configure scrolling
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        # Create window in canvas
        self.canvas_window = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        # Bind canvas resize to update scroll region
        def on_canvas_configure(event):
            self.canvas.itemconfig(self.canvas_window, width=event.width)
        self.canvas.bind('<Configure>', on_canvas_configure)

        # Bind mousewheel to scroll
        def on_mousewheel(event):
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        def bind_mousewheel(event):
            self.canvas.bind_all("<MouseWheel>", on_mousewheel)

        def unbind_mousewheel(event):
            self.canvas.unbind_all("<MouseWheel>")

        self.canvas.bind('<Enter>', bind_mousewheel)
        self.canvas.bind('<Leave>', unbind_mousewheel)

        # Pack canvas and scrollbar with proper spacing
        self.canvas.pack(side="left", fill="both", expand=True, padx=(20, 10), pady=20)
        self.scrollbar.pack(side="right", fill="y", padx=(10, 20), pady=20)

        # Set main_frame to scrollable_frame for compatibility
        self.main_frame = self.scrollable_frame

    def _position_window(self):
        """Position window in bottom-left corner of the screen"""
        self.root.update_idletasks()
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        window_width = 480
        window_height = 600
        x_position = 20  # 20px margin from left
        y_position = screen_height - window_height - 20  # 20px margin from bottom

        self.root.geometry(f"{window_width}x{window_height}+{x_position}+{y_position}")

    def _create_header(self):
        """Create the application header"""
        header_frame = ttk.Frame(self.main_frame)
        header_frame.pack(fill=X, pady=(0, 20))

        # Create left and right sections - logo on left, text on right
        logo_frame = ttk.Frame(header_frame)
        logo_frame.pack(side=tk.LEFT, pady=(0, 0))

        text_frame = ttk.Frame(header_frame)
        text_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(8, 0), pady=(16, 0))

        # Logo image on the left
        try:
            # Load the whispertux.png image
            from PIL import Image, ImageTk

            # Open and resize the image to be wider
            img = Image.open("assets/whispertux.png")
            # Resize to 60x45 for wider appearance and better centering
            img = img.resize((80, 65), Image.Resampling.LANCZOS)
            self.logo_image = ImageTk.PhotoImage(img)

            logo_label = ttk.Label(
                logo_frame,
                image=self.logo_image
            )
            # Add bottom margin to better center with the two text lines
            logo_label.pack(pady=(0, 0))

        except Exception as e:
            print(f"Failed to load whispertux.png: {e}")
            # Fallback: show a simple text logo
            logo_label = ttk.Label(
                logo_frame,
                text="🎤",
                font=("Arial", 22)
            )
            logo_label.pack(pady=(0, 8))

        # Title and subtitle on the right of the logo
        title_label = ttk.Label(
            text_frame,
            text="whispertux",
            font=("Arial", 18, "bold"),
            bootstyle=INFO  # Brighter blue color
        )
        title_label.pack(anchor=tk.W)

        subtitle_label = ttk.Label(
            text_frame,
            text="Voice Dictation for Linux",
            font=("Arial", 10, "bold"),
            bootstyle=PRIMARY # Brighter color instead of SECONDARY
        )
        subtitle_label.pack(anchor=tk.W)

    def _create_status_section(self):
        """Create the status display section"""
        status_frame = ttk.LabelFrame(self.main_frame, text="Status", padding=10)
        status_frame.pack(fill=X, pady=(0, 10))

        # Main status on the right
        status_main_frame = ttk.Frame(status_frame)
        status_main_frame.pack(fill=X)

        self.status_label = ttk.Label(
            status_main_frame,
            text="Ready",
            font=("Arial", 12, "bold"),
            bootstyle=SUCCESS
        )
        self.status_label.pack(side=RIGHT)

        # Settings info on the left - vertical layout
        settings_info_frame = ttk.Frame(status_main_frame)
        settings_info_frame.pack(side=LEFT, fill=X, expand=True)

        # Model info
        model_info_frame = ttk.Frame(settings_info_frame)
        model_info_frame.pack(fill=X, pady=1)

        ttk.Label(model_info_frame, text="Model:", font=("Arial", 9)).pack(side=LEFT)
        self.model_display_label = ttk.Label(
            model_info_frame,
            text=self.config.get_setting('model', 'base'),
            font=("Arial", 9, "bold"),
            bootstyle=INFO
        )
        self.model_display_label.pack(side=LEFT, padx=(5, 0))

        # Shortcut info
        shortcut_info_frame = ttk.Frame(settings_info_frame)
        shortcut_info_frame.pack(fill=X, pady=1)

        ttk.Label(shortcut_info_frame, text="Shortcut:", font=("Arial", 9)).pack(side=LEFT)
        self.shortcut_display_label = ttk.Label(
            shortcut_info_frame,
            text=self.config.get_setting('primary_shortcut', 'F12'),
            font=("Arial", 9, "bold"),
            bootstyle=INFO
        )
        self.shortcut_display_label.pack(side=LEFT, padx=(5, 0))

        # Typing speed info
        typing_info_frame = ttk.Frame(settings_info_frame)
        typing_info_frame.pack(fill=X, pady=1)

        ttk.Label(typing_info_frame, text="Speed:", font=("Arial", 9)).pack(side=LEFT)
        self.typing_speed_display_label = ttk.Label(
            typing_info_frame,
            text=f"{self.config.get_setting('typing_speed', 150)} cpm",
            font=("Arial", 9, "bold"),
            bootstyle=INFO
        )
        self.typing_speed_display_label.pack(side=LEFT, padx=(5, 0))


    def _create_audio_section(self):
        """Create the audio monitoring section with waveform visualizer"""
        audio_frame = ttk.LabelFrame(self.main_frame, text="Audio Level", padding=10)
        audio_frame.pack(fill=X, pady=(0, 10))

        # Waveform visualizer widget
        self.waveform_visualizer = WaveformVisualizer(
            audio_frame,
            width=420,
            height=120
        )
        self.waveform_visualizer.pack(fill=X, pady=5, expand=True)

    def _create_transcription_section(self):
        """Create the transcription display section"""
        trans_frame = ttk.LabelFrame(self.main_frame, text="Transcription", padding=10)
        trans_frame.pack(fill=BOTH, expand=True, pady=(0, 10))

        # Scrollable text widget for transcription
        text_frame = ttk.Frame(trans_frame)
        text_frame.pack(fill=BOTH, expand=True)

        self.transcription_text = tk.Text(
            text_frame,
            height=8,
            wrap=tk.WORD,
            font=("Arial", 10),
            bg="#2b2b2b",  # Dark background to match theme
            fg="#ffffff",  # White text
            insertbackground="#ffffff",  # White cursor
            selectbackground="#404040"  # Selection color
        )

        # Add scrollbar
        scrollbar = ttk.Scrollbar(text_frame, orient=VERTICAL)
        scrollbar.pack(side=RIGHT, fill=Y)

        self.transcription_text.pack(side=LEFT, fill=BOTH, expand=True)
        self.transcription_text.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.transcription_text.yview)

        # Add buttons
        buttons_frame = ttk.Frame(trans_frame)
        buttons_frame.pack(pady=(5, 0))

        copy_button = ttk.Button(
            buttons_frame,
            text="Copy",
            command=self._copy_all_transcription,
            bootstyle="info",
            width=8
        )
        copy_button.pack(side=LEFT, padx=(0, 5))

        clear_button = ttk.Button(
            buttons_frame,
            text="Clear",
            command=self._clear_transcription,
            bootstyle="secondary",
            width=8
        )
        clear_button.pack(side=LEFT)


    def _create_control_buttons(self):
        """Create the main control buttons"""
        button_frame = ttk.Frame(self.main_frame)
        button_frame.pack(fill=X, pady=(10, 0))

        # Quit button (far left)
        quit_button = ttk.Button(
            button_frame,
            text="Quit",
            command=self._on_closing,
            bootstyle=DANGER,
            width=10
        )
        quit_button.pack(side=LEFT)

        # Settings button (center-left)
        settings_button = ttk.Button(
            button_frame,
            text="Settings",
            command=self._show_settings,
            bootstyle=SECONDARY,
            width=12
        )
        settings_button.pack(side=LEFT, padx=(10, 0))

        # Main record/stop button (right)
        self.record_button = ttk.Button(
            button_frame,
            text="Record",
            command=self._toggle_recording,
            bootstyle=SUCCESS,
            width=15
        )
        self.record_button.pack(side=RIGHT)

    def _setup_global_shortcuts(self):
        """Set up global keyboard shortcuts"""
        try:
            from src.global_shortcuts import GlobalShortcuts
            keyboard_device = self.config.get_setting('keyboard_device', '')
            device_path = keyboard_device if keyboard_device else None

            self.global_shortcuts = GlobalShortcuts(
                primary_key=self.config.get_setting('primary_shortcut', 'F12'),
                callback=self._toggle_recording,
                device_path=device_path
            )
            self.global_shortcuts.start()
            print(f"Global shortcuts initialized")
        except Exception as e:
            print(f"ERROR: Failed to setup global shortcuts: {e}")
            # Still allow the app to run without global shortcuts

    def _start_audio_monitor(self):
        """Start the audio level monitoring thread"""
        def monitor_audio():
            while hasattr(self, 'root') and self.root:
                try:
                    # Get audio level from capture device
                    level = self.audio_capture.get_audio_level()

                    # Update progress bar on main thread
                    if self.root:
                        self.root.after_idle(self._update_audio_level, level)

                    time.sleep(0.05)  # Update ~20 times per second
                except:
                    break

        self.monitor_thread = threading.Thread(target=monitor_audio, daemon=True)
        self.monitor_thread.start()

    def _stop_audio_monitor(self):
        """Stop the audio level monitoring thread"""
        if hasattr(self, 'monitor_thread') and self.monitor_thread and self.monitor_thread.is_alive():
            # The monitor_audio function checks for self.root existence, so setting it to None will stop the loop
            pass  # Thread will stop automatically when recording ends

    def _update_audio_level(self, level):
        """Update the waveform visualizer with audio level data (called from main thread)"""
        if self.waveform_visualizer:
            # Always update the visualizer with live audio data
            # The visualizer will handle different display modes based on recording state
            self.waveform_visualizer.update_audio_data(level)

    def _reset_audio_level(self):
        """Reset the waveform visualizer"""
        if self.waveform_visualizer:
            self.waveform_visualizer.clear_waveform()

    def _clear_transcription(self):
        """Clear the transcription text area"""
        if self.transcription_text:
            self.transcription_text.delete(1.0, tk.END)

    def _copy_all_transcription(self):
        """Copy all transcription text to clipboard"""
        if self.transcription_text:
            text_content = self.transcription_text.get(1.0, tk.END).strip()
            if text_content:
                self.transcription_text.clipboard_clear()
                self.transcription_text.clipboard_append(text_content)

    def _toggle_recording(self):
        """Toggle recording state - main entry point for recording control"""
        if self.is_recording:
            self._stop_recording()
        else:
            self._start_recording()

    def _start_recording(self):
        """Start audio recording"""
        if self.is_recording or self.is_processing:
            return

        try:
            self.is_recording = True
            self._update_ui_recording_state()

            # Start audio monitoring and waveform animation for live visualization
            self._start_audio_monitor()
            if self.waveform_visualizer:
                self.waveform_visualizer.start_animation()

            # Start audio capture in a separate thread
            def record_audio():
                try:
                    self.audio_capture.start_recording()
                except Exception as e:
                    self.root.after_idle(self._show_error, f"Failed to start recording: {e}")
                    self.root.after_idle(self._stop_recording)

            record_thread = threading.Thread(target=record_audio, daemon=True)
            record_thread.start()

        except Exception as e:
            self._show_error(f"Failed to start recording: {e}")
            self.is_recording = False
            self._update_ui_recording_state()

    def _stop_recording(self):
        """Stop audio recording and process transcription"""
        if not self.is_recording:
            return

        self.is_recording = False
        self.is_processing = True
        self._update_ui_recording_state()

        # Stop recording and process in background thread
        def process_recording():
            try:
                # Stop audio capture and get the recorded data
                audio_data = self.audio_capture.stop_recording()

                if audio_data is not None and len(audio_data) > 0:
                    # Transcribe the audio
                    transcription = self.whisper_manager.transcribe_audio(audio_data)

                    # Update UI and inject text on main thread (only if root still exists)
                    if hasattr(self, 'root') and self.root:
                        self.root.after_idle(self._handle_transcription, transcription)
                else:
                    if hasattr(self, 'root') and self.root:
                        self.root.after_idle(self._handle_transcription, None)

            except Exception as e:
                if hasattr(self, 'root') and self.root:
                    self.root.after_idle(self._show_error, f"Transcription failed: {e}")
                else:
                    print(f"Transcription failed: {e}")
            finally:
                self.is_processing = False
                if hasattr(self, 'root') and self.root:
                    self.root.after_idle(self._update_ui_recording_state)

        process_thread = threading.Thread(target=process_recording, daemon=True)
        process_thread.start()

    def _handle_transcription(self, transcription):
        """Handle completed transcription"""
        # Stop audio monitoring, animation, and reset audio level bar after recording
        self._stop_audio_monitor()
        if self.waveform_visualizer:
            self.waveform_visualizer.stop_animation()
        self._reset_audio_level()

        if transcription and transcription.strip():
            # Filter out blank audio responses from whisper
            cleaned_transcription = transcription.strip()

            # Check for various blank audio indicators that should not be injected
            blank_indicators = ["[BLANK_AUDIO]", "[blank_audio]", "(blank)", "(silence)", "[silence]", ""]
            is_blank = any(indicator in cleaned_transcription.lower() for indicator in ["[blank_audio]", "(blank)", "(silence)", "[silence]"]) or cleaned_transcription == "[BLANK_AUDIO]"

            if not is_blank and cleaned_transcription:
                # Display in UI
                self.transcription_text.insert(tk.END, f"{cleaned_transcription}\n")
                self.transcription_text.see(tk.END)

                # Inject text into focused application
                try:
                    self.text_injector.inject_text(cleaned_transcription)
                except Exception as e:
                    self.status_label.config(text="❌ Text injection failed", bootstyle="danger")
        else:
            # Don't show popup for no speech detected, just update status
            print("No speech detected")
            self.status_label.config(text="⚪ No speech detected", bootstyle="secondary")
            self.transcription_text.insert(tk.END, "[No speech detected]\n")
            self.transcription_text.see(tk.END)

    def _update_ui_recording_state(self):
        """Update UI elements based on recording state"""
        if self.is_recording:
            self.status_label.config(text="🔴 Recording...", bootstyle=DANGER)
            self.record_button.config(text="Stop Recording", bootstyle=DANGER)
            # Update waveform visualizer recording state
            if self.waveform_visualizer:
                self.waveform_visualizer.set_recording_state(True)
        elif self.is_processing:
            self.status_label.config(text="🔄 Processing...", bootstyle=WARNING)
            self.record_button.config(text="Processing...", bootstyle=WARNING, state=DISABLED)
            # Stop recording state in visualizer
            if self.waveform_visualizer:
                self.waveform_visualizer.set_recording_state(False)
        else:
            self.status_label.config(text="✅ Ready", bootstyle=SUCCESS)
            self.record_button.config(text="Record", bootstyle=SUCCESS, state=NORMAL)
            # Stop recording state in visualizer
            if self.waveform_visualizer:
                self.waveform_visualizer.set_recording_state(False)

    def _on_model_changed(self, event=None):
        """Handle model selection change"""
        new_model = self.model_combo.get()
        self.config.set_setting('model', new_model)
        self.config.save_config()

        # Update whisper manager with new model
        try:
            self.whisper_manager.set_model(new_model)
        except Exception as e:
            self._show_error(f"Failed to change model: {e}")

    def _show_settings(self):
        """Show settings dialog"""
        SettingsDialog(self.root, self.config, self.global_shortcuts, self._update_shortcut_display, self.text_injector, self)

    def _get_current_audio_device_name(self):
        """Get the display name of the current audio device"""
        try:
            configured_device_id = self.config.get_setting('audio_device', None)

            if configured_device_id is None:
                return "System Default"

            # Get the current device info from audio capture
            current_device_info = self.audio_capture.get_current_device_info()
            if current_device_info:
                # Allow longer device names for display
                name = current_device_info['name']
                if len(name) > 32:
                    name = name[:29] + "..."
                return name

            return "Unknown Device"
        except:
            return "Error"

    def _update_shortcut_display(self):
        """Update all status displays in the main window"""
        # Update shortcut display
        if self.shortcut_display_label:
            current_shortcut = self.config.get_setting('primary_shortcut', 'F12')
            self.shortcut_display_label.config(text=current_shortcut)
            print(f"Updated shortcut display to: {current_shortcut}")

        # Update model display
        if self.model_display_label:
            current_model = self.config.get_setting('model', 'base')
            self.model_display_label.config(text=current_model)
            print(f"Updated model display to: {current_model}")

        # Update typing speed display
        if self.typing_speed_display_label:
            typing_speed = self.config.get_setting('typing_speed', 150)
            self.typing_speed_display_label.config(text=f"{typing_speed} cpm")
            print(f"Updated typing speed display to: {typing_speed}")

    def _show_error(self, message):
        """Show error message"""
        messagebox.showerror("Error", message)

    def _show_info(self, message):
        """Show info message"""
        messagebox.showinfo("Info", message)

    def _show_model_download(self, callback=None):
        """Show model download dialog"""
        from tkinter import simpledialog

        # List of available models to download
        available_models = [
            "base.en", "small.en", "medium.en", "large-v3",
            "base", "small", "medium", "large"
        ]

        # Create a custom dialog for model selection
        dialog = tk.Toplevel(self.root)
        dialog.title("Download Whisper Models")
        dialog.geometry("400x300")
        dialog.transient(self.root)
        dialog.grab_set()

        # Center dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() - dialog.winfo_reqwidth()) // 2
        y = (dialog.winfo_screenheight() - dialog.winfo_reqheight()) // 2
        dialog.geometry(f"+{x}+{y}")

        # Title
        title_label = ttk.Label(
            dialog,
            text="Download Whisper Models",
            font=("Arial", 14, "bold")
        )
        title_label.pack(pady=10)

        # Instructions
        info_label = ttk.Label(
            dialog,
            text="Select a model to download:",
            font=("Arial", 10)
        )
        info_label.pack(pady=5)

        # Model selection
        model_var = tk.StringVar(value=available_models[0])
        model_combo = ttk.Combobox(
            dialog,
            textvariable=model_var,
            values=available_models,
            state="readonly",
            width=20
        )
        model_combo.pack(pady=10)

        # Progress bar
        progress = ttk.Progressbar(dialog, mode='indeterminate')
        progress.pack(pady=10, fill=X, padx=20)

        # Status label
        status_label = ttk.Label(dialog, text="", font=("Arial", 9))
        status_label.pack(pady=5)

        # Buttons
        button_frame = ttk.Frame(dialog)
        button_frame.pack(pady=10)

        def download_model():
            selected_model = model_var.get()
            status_label.config(text=f"Downloading {selected_model}...")
            progress.start()

            def download_thread():
                try:
                    project_root = Path(__file__).parent
                    models_dir = project_root / "whisper.cpp" / "models"

                    # Use the download script
                    import subprocess
                    result = subprocess.run([
                        "bash",
                        str(models_dir / "download-ggml-model.sh"),
                        selected_model
                    ], cwd=str(models_dir), capture_output=True, text=True)

                    if result.returncode == 0:
                        dialog.after(100, lambda: status_label.config(text=f"✅ {selected_model} downloaded successfully!"))
                        dialog.after(100, lambda: progress.stop())
                        # Refresh model combo in main window
                        dialog.after(2000, lambda: self._refresh_model_combo())
                        # Call the callback to refresh settings dialog if provided
                        if callback:
                            dialog.after(2000, callback)
                        dialog.after(2000, lambda: dialog.destroy())
                    else:
                        dialog.after(100, lambda: status_label.config(text=f"❌ Download failed: {result.stderr[:50]}..."))
                        dialog.after(100, lambda: progress.stop())

                except Exception as e:
                    dialog.after(100, lambda: status_label.config(text=f"❌ Error: {str(e)[:50]}..."))
                    dialog.after(100, lambda: progress.stop())

            threading.Thread(target=download_thread, daemon=True).start()

        download_button = ttk.Button(
            button_frame,
            text="Download",
            command=download_model,
            bootstyle=SUCCESS
        )
        download_button.pack(side=LEFT, padx=5)

        cancel_button = ttk.Button(
            button_frame,
            text="Cancel",
            command=dialog.destroy,
            bootstyle=SECONDARY
        )
        cancel_button.pack(side=LEFT, padx=5)

    def _refresh_model_combo(self):
        """Refresh the model settings after downloading new models"""
        try:
            available_models = self.whisper_manager.get_available_models()
            if available_models:
                print(f"Available models after refresh: {available_models}")
                # The model combo is now in the settings dialog, not main window
                # This method is mainly for updating the current model display
                current_model = self.config.get_setting('model', 'base')
                if current_model not in available_models and available_models:
                    # Update to first available model if current one doesn't exist
                    self.config.set_setting('model', available_models[0])
                    self.config.save_config()
                    self._update_shortcut_display()  # This will update all displays
        except Exception as e:
            print(f"Error refreshing model settings: {e}")

    def _on_closing(self):
        """Handle application closing"""
        try:
            # Stop global shortcuts
            if self.global_shortcuts:
                self.global_shortcuts.stop()

            # Stop audio capture
            if self.is_recording:
                self.audio_capture.stop_recording()

            # Stop waveform visualizer animation
            if self.waveform_visualizer:
                self.waveform_visualizer.stop_animation()

            # Save configuration
            self.config.save_config()

        except Exception as e:
            print(f"Error during cleanup: {e}")
        finally:
            self.root.destroy()

    def run(self):
        """Start the application"""
        print("Starting WhisperTux...")

        # Initialize whisper manager
        if not self.whisper_manager.initialize():
            messagebox.showerror(
                "Initialization Error",
                "Failed to initialize Whisper. Please ensure whisper.cpp is built.\n"
                "Run the build scripts first."
            )
            return False

        # Start the GUI main loop
        self.root.mainloop()
        return True


def main():
    """Main entry point"""
    # Ensure we're running on Linux (since this uses ydotool)
    if not sys.platform.startswith('linux'):
        try:
            from src.logger import log_warning
            log_warning("This application is designed for Linux systems", "MAIN")
        except ImportError:
            print("Warning: This application is designed for Linux systems")

    # Create and run the application
    app = WhisperTuxApp()
    success = app.run()

    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
