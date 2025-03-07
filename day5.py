import tkinter as tk
from subprocess import Popen, CREATE_NEW_CONSOLE
from tkinter import Menu, simpledialog, messagebox, filedialog, ttk
import keyboard
import json
import os
import sys
import pystray
from PIL import Image, ImageTk
import customtkinter as ctk 
import psutil  # For getting running processes

# Set appearance mode and default color theme
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

opened_processes = []
app_shortcuts = {}
app_categories = {}
SHORTCUTS_FILE = "shortcuts.json"
APP_LIST_FILE = "app_list.json"
CATEGORIES_FILE = "categories.json"

def load_shortcuts():
    global app_shortcuts
    if os.path.exists(SHORTCUTS_FILE):
        with open(SHORTCUTS_FILE, "r") as f:
            app_shortcuts = json.load(f)
    else:
        app_shortcuts = {}

def save_shortcuts():
    with open(SHORTCUTS_FILE, "w") as f:
        json.dump(app_shortcuts, f, indent=4)

def load_app_list():
    if os.path.exists(APP_LIST_FILE):
        with open(APP_LIST_FILE, "r") as f:
            return json.load(f)
    return []

def save_app_list(app_list):
    with open(APP_LIST_FILE, "w") as f:
        json.dump(app_list, f, indent=4)

def load_categories():
    global app_categories
    if os.path.exists(CATEGORIES_FILE):
        with open(CATEGORIES_FILE, "r") as f:
            app_categories = json.load(f)
    else:
        # Default categories
        app_categories = {
            "Favorites": [],
            "Games": [],
            "Media": [],
            "Productivity": [],
            "Development": [],
            "Other": []
        }
        save_categories()

def save_categories():
    with open(CATEGORIES_FILE, "w") as f:
        json.dump(app_categories, f, indent=4)

def open_exe(exe_path, app_name):
    try:
        process = Popen(exe_path, creationflags=CREATE_NEW_CONSOLE)
        opened_processes.append({'process': process, 'app_name': app_name, 'exe_path': exe_path})
        print(f"Opened {exe_path}")
    except FileNotFoundError:
        print(f"Error: The specified executable file ({exe_path}) was not found.")
        messagebox.showerror("File Not Found", f"Executable file not found:\n{exe_path}")
    except Exception as e:
        print(f"An error occurred: {e}")
        messagebox.showerror("Error", f"Could not open application:\n{app_name}\nError: {e}")

def close_all_apps():
    global opened_processes
    for app_info in list(opened_processes):
        process = app_info['process']
        app_name = app_info['app_name']
        try:
            process.terminate()
            print(f"Closed process: {process.pid} ({app_name})")
        except Exception as e:
            print(f"An error occurred while closing the process: {e}")
        opened_processes.remove(app_info)

def close_app_instance(app_name, exe_path):
    global opened_processes
    for app_info in list(opened_processes):
        if app_info['app_name'] == app_name and app_info['exe_path'] == exe_path:
            process = app_info['process']
            try:
                process.terminate()
                print(f"Closed process: {process.pid} ({app_name})")
            except Exception as e:
                print(f"An error occurred while closing the process: {e}")
            opened_processes.remove(app_info)
            return

# App button with hover animation and modern styling
class AppButton(ctk.CTkButton):
    def __init__(self, master, app_info, category_frame, **kwargs):
        self.app_info = app_info
        self.category_frame = category_frame
        self.master = master
        self.exe_path = app_info['exe_path']
        self.app_name = app_info['app_name']

        # Load icon if available
        self.icon_image = None
        icon_path = app_shortcuts.get(self.app_name, {}).get('icon_path')
        if icon_path and os.path.exists(icon_path):
            try:
                img = Image.open(icon_path)
                img = img.resize((32, 32), Image.Resampling.LANCZOS)
                self.icon_image = ImageTk.PhotoImage(img)
            except Exception as e:
                print(f"Error loading icon for {self.app_name}: {e}")

        # Create button with gradient effect
        super().__init__(
            master=master,
            text=self.app_name,
            image=self.icon_image if self.icon_image else None,
            compound="left",
            corner_radius=8,
            fg_color=("#2B2B2B", "#2B2B2B"),  # Normal state color
            hover_color=("#3E3E3E", "#3E3E3E"),  # Hover state color
            text_color=("#FFFFFF", "#FFFFFF"),
            command=self.open_app,
            **kwargs
        )

        # Bind right-click event
        self.bind("<Button-3>", self.on_right_click)

        # Hover animation
        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)

    def open_app(self):
        open_exe(self.exe_path, self.app_name)

    def on_enter(self, event):
        # Scale up slightly on hover
        self.configure(fg_color=("#3E3E3E", "#3E3E3E"))

    def on_leave(self, event):
        # Return to normal size
        self.configure(fg_color=("#2B2B2B", "#2B2B2B"))

    def on_right_click(self, event):
        menu = Menu(self.master, tearoff=0, background='#2B2B2B', foreground='#FFFFFF', bd=0)
        menu.add_command(label=f"Open {self.app_name}", command=self.open_app)
        menu.add_command(label=f"Close Instance", command=lambda: close_app_instance(self.app_name, self.exe_path))
        menu.add_command(label="Settings", command=self.open_settings)

        # Category submenu
        category_menu = Menu(menu, tearoff=0, background='#2B2B2B', foreground='#FFFFFF', bd=0)
        for category in app_categories.keys():
            category_menu.add_command(
                label=category,
                command=lambda cat=category: self.change_category(cat)
            )
        menu.add_cascade(label="Move to Category", menu=category_menu)

        menu.add_command(label="Remove App", command=self.remove_app)
        menu.post(event.x_root, event.y_root)

    def open_settings(self):
        SettingsDialog(self.master, self.app_info, self)

    def change_category(self, new_category):
        # Remove from current category
        for category, apps in app_categories.items():
            if self.exe_path in apps:
                app_categories[category].remove(self.exe_path)

        # Add to new category
        app_categories[new_category].append(self.exe_path)
        save_categories()

        # Refresh UI
        refresh_category_view()
        messagebox.showinfo("Category Changed", f"{self.app_name} moved to {new_category}")

    def remove_app(self):
        global app_list_data
        # Remove from app list
        app_list_data = [app for app in app_list_data if app['exe_path'] != self.exe_path]
        save_app_list(app_list_data)

        # Remove from categories
        for category, apps in app_categories.items():
            if self.exe_path in apps:
                app_categories[category].remove(self.exe_path)
        save_categories()

        # Remove button
        self.destroy()
        messagebox.showinfo("App Removed", f"{self.app_name} removed from launcher.")

# Modern settings dialog with gradient background
class SettingsDialog(ctk.CTkToplevel):
    def __init__(self, parent, app_info, app_button):
        super().__init__(parent)
        self.app_info = app_info
        self.app_button = app_button
        self.title(f"Settings - {app_info['app_name']}")

        # Center the dialog
        window_width = 400
        window_height = 300
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x_pos = (screen_width - window_width) // 2
        y_pos = (screen_height - window_height) // 2
        self.geometry(f"{window_width}x{window_height}+{x_pos}+{y_pos}")

        # Make it modal
        self.transient(parent)
        self.grab_set()

        # Variables
        self.icon_path_var = tk.StringVar(value=app_shortcuts.get(app_info['app_name'], {}).get('icon_path', ''))
        self.shortcut_var = tk.StringVar(value=app_shortcuts.get(app_info['app_name'], {}).get('shortcut', ''))

        self.create_widgets()

    def create_widgets(self):
        # Header with app name
        header_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        header_frame.pack(fill="x", pady=(20, 10))

        app_label = ctk.CTkLabel(
            header_frame,
            text=self.app_info['app_name'],
            font=ctk.CTkFont(size=18, weight="bold")
        )
        app_label.pack()

        # Content frame
        content_frame = ctk.CTkFrame(self, corner_radius=10)
        content_frame.pack(fill="both", expand=True, padx=20, pady=10)

        # Executable path
        path_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        path_frame.pack(fill="x", padx=10, pady=(10, 5))

        path_label = ctk.CTkLabel(path_frame, text="Executable:", anchor="w")
        path_label.pack(side="left")

        path_value = ctk.CTkLabel(
            path_frame,
            text=self.app_info['exe_path'],
            anchor="w",
            fg_color="#2B2B2B",
            corner_radius=5
        )
        path_value.pack(side="left", fill="x", expand=True, padx=(10, 0))

        # Icon path
        icon_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        icon_frame.pack(fill="x", padx=10, pady=5)

        icon_label = ctk.CTkLabel(icon_frame, text="Icon Path:", anchor="w")
        icon_label.pack(side="left")

        icon_entry = ctk.CTkEntry(icon_frame, textvariable=self.icon_path_var)
        icon_entry.pack(side="left", fill="x", expand=True, padx=(10, 10))

        browse_button = ctk.CTkButton(
            icon_frame,
            text="Browse",
            width=80,
            command=self.browse_icon
        )
        browse_button.pack(side="right")

        # Shortcut
        shortcut_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        shortcut_frame.pack(fill="x", padx=10, pady=5)

        shortcut_label = ctk.CTkLabel(shortcut_frame, text="Shortcut:", anchor="w")
        shortcut_label.pack(side="left")

        shortcut_entry = ctk.CTkEntry(shortcut_frame, textvariable=self.shortcut_var)
        shortcut_entry.pack(side="left", fill="x", expand=True, padx=(10, 0))

        # Buttons
        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.pack(fill="x", padx=20, pady=(10, 20))

        cancel_button = ctk.CTkButton(
            button_frame,
            text="Cancel",
            fg_color="#555555",
            hover_color="#777777",
            command=self.destroy
        )
        cancel_button.pack(side="left", padx=(0, 10))

        save_button = ctk.CTkButton(
            button_frame,
            text="Save",
            command=self.save_settings
        )
        save_button.pack(side="right")

    def browse_icon(self):
        filename = filedialog.askopenfilename(
            initialdir=".",
            title="Select Icon File",
            filetypes=(("PNG files", "*.png"), ("JPEG files", "*.jpg *.jpeg"), ("ICO files", "*.ico"), ("All files", "*.*"))
        )
        if filename:
            self.icon_path_var.set(filename)

    def save_settings(self):
        app_name = self.app_info['app_name']
        icon_path = self.icon_path_var.get()
        shortcut = self.shortcut_var.get()

        app_shortcuts[app_name] = {'icon_path': icon_path, 'shortcut': shortcut}
        save_shortcuts()

        try:
            keyboard.remove_hotkey(app_shortcuts.get(app_name, {}).get('shortcut'))
        except:
            pass

        if shortcut:
            try:
                keyboard.add_hotkey(shortcut, lambda path=self.app_info['exe_path'], name=app_name: open_exe(path, name))
            except Exception as hotkey_err:
                messagebox.showerror("Hotkey Error", f"Could not set hotkey '{shortcut}'. It might be invalid or already in use.")

        # Update button icon
        if icon_path and os.path.exists(icon_path):
            try:
                img = Image.open(icon_path)
                img = img.resize((32, 32), Image.Resampling.LANCZOS)
                icon_image = ImageTk.PhotoImage(img)
                self.app_button.configure(image=icon_image)
                self.app_button.image = icon_image
            except Exception as e:
                print(f"Error loading icon after settings change: {e}")

        messagebox.showinfo("Settings Saved", f"Settings for {app_name} saved.")
        self.destroy()

# Dialog to create a new category
class CategoryDialog(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Create New Category")
        self.geometry("300x150")
        self.transient(parent)
        self.grab_set()

        # Category name variable
        self.category_name = tk.StringVar()

        # UI Elements
        ctk.CTkLabel(self, text="Category Name:").pack(pady=(20, 5))
        ctk.CTkEntry(self, textvariable=self.category_name, width=200).pack(pady=5)

        # Buttons
        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.pack(fill="x", padx=20, pady=(10, 20))

        ctk.CTkButton(
            button_frame,
            text="Cancel",
            fg_color="#555555",
            hover_color="#777777",
            command=self.destroy
        ).pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            button_frame,
            text="Create",
            command=self.create_category
        ).pack(side="right")

    def create_category(self):
        name = self.category_name.get().strip()
        if not name:
            messagebox.showerror("Error", "Category name cannot be empty")
            return

        if name in app_categories:
            messagebox.showerror("Error", f"Category '{name}' already exists")
            return

        # Add new category
        app_categories[name] = []
        save_categories()

        # Refresh UI
        refresh_category_view()
        messagebox.showinfo("Category Created", f"Category '{name}' created successfully")
        self.destroy()

# Scan for applications with progress bar
def scan_for_apps(root):
    program_files_dirs = [
        os.environ.get("ProgramFiles"),
        os.environ.get("ProgramFiles(x86)")
    ]

    # Create loading dialog
    loading_dialog = ctk.CTkToplevel(root)
    loading_dialog.title("Scanning for Apps")
    loading_dialog.geometry("400x150")
    loading_dialog.transient(root)
    loading_dialog.grab_set()

    # Center the dialog
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x_pos = (screen_width - 400) // 2
    y_pos = (screen_height - 150) // 2
    loading_dialog.geometry(f"400x150+{x_pos}+{y_pos}")

    # Progress UI
    ctk.CTkLabel(loading_dialog, text="Scanning for applications...").pack(pady=(20, 10))
    progress = ctk.CTkProgressBar(loading_dialog, width=300, mode="indeterminate")
    progress.pack(pady=10)
    progress.start()

    status_label = ctk.CTkLabel(loading_dialog, text="Please wait...")
    status_label.pack(pady=10)

    def find_apps_in_dir(directories):
        found_apps = []
        for program_dir in directories:
            if program_dir:
                for root_dir, _, files in os.walk(program_dir):
                    for file in files:
                        if file.lower().endswith(".exe"):
                            exe_path = os.path.join(root_dir, file)
                            app_name = file[:-4]
                            found_apps.append({'exe_path': exe_path, 'app_name': app_name})
        return found_apps

    def update_app_display(found_apps):
        global app_list_data
        app_list_data.extend(found_apps)
        # Remove duplicates based on exe_path
        app_list_data = list({v['exe_path']:v for v in app_list_data}.values())

        # Add all apps to "Other" category if not already in a category
        for app_info in app_list_data:
            exe_path = app_info['exe_path']
            # Check if app is in any category
            in_category = False
            for category, apps in app_categories.items():
                if exe_path in apps:
                    in_category = True
                    break

            if not in_category:
                app_categories["Other"].append(exe_path)

        save_app_list(app_list_data)
        save_categories()

        # Set up keyboard shortcuts
        for app_info in app_list_data:
            if app_info['app_name'] in app_shortcuts and 'shortcut' in app_shortcuts[app_info['app_name']]:
                try:
                    keyboard.add_hotkey(
                        app_shortcuts[app_info['app_name']]['shortcut'],
                        lambda path=app_info['exe_path'], name=app_info['app_name']: open_exe(path, name)
                    )
                except Exception as hotkey_err:
                    print(f"Error setting hotkey for {app_info['app_name']}: {hotkey_err}")

        # Refresh UI
        refresh_category_view()

        # Close loading dialog
        status_label.configure(text=f"Scan complete. Found {len(found_apps)} new apps.")
        progress.stop()
        loading_dialog.after(2000, loading_dialog.destroy)

    # Run scan in a separate thread
    import threading
    scan_thread = threading.Thread(target=lambda: update_app_display(find_apps_in_dir(program_files_dirs)))
    scan_thread.daemon = True
    scan_thread.start()

def refresh_category_view(search_term=None):
    # Clear existing tabs content
    for tab in category_tabs.values():
        for widget in tab.winfo_children():
            widget.destroy()

    # Populate tabs with apps
    for category, exe_paths in app_categories.items():
        if category in category_tabs:
            tab = category_tabs[category]

            # Create scrollable frame
            scrollable_frame = ctk.CTkScrollableFrame(tab, fg_color="transparent")
            scrollable_frame.pack(fill="both", expand=True, padx=10, pady=10)

            # Find apps for this category
            category_apps = []
            for exe_path in exe_paths:
                for app in app_list_data:
                    if app['exe_path'] == exe_path:
                        category_apps.append(app)
                        break

            # Apply search filter if search_term is provided
            if search_term:
                search_term = search_term.lower()
                category_apps = [
                    app for app in category_apps
                    if search_term in app['app_name'].lower()
                ]

            # No apps message
            if not category_apps:
                no_apps_label = ctk.CTkLabel(
                    scrollable_frame,
                    text=f"No apps in {category}{' matching search' if search_term else ''}",
                    font=ctk.CTkFont(size=14),
                    text_color="#888888"
                )
                no_apps_label.pack(pady=20)
                continue

            # Create app grid (3 columns)
            row = 0
            col = 0
            max_cols = 3

            # Create a frame grid
            for i, app_info in enumerate(category_apps):
                # Create frame for the app
                app_frame = ctk.CTkFrame(scrollable_frame, fg_color="transparent")
                app_frame.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")

                # Create app button in the frame
                app_button = AppButton(
                    app_frame,
                    app_info,
                    category,
                    width=120,
                    height=120
                )
                app_button.pack(fill="both", expand=True)

                # Update grid position
                col += 1
                if col >= max_cols:
                    col = 0
                    row += 1

            # Configure grid weights
            for i in range(max_cols):
                scrollable_frame.grid_columnconfigure(i, weight=1)

# Function to add a single app manually
def add_individual_app():
    global app_list_data, app_categories
    file_path = filedialog.askopenfilename(
        title="Select Application Executable",
        filetypes=[("Executable files", "*.exe")]
    )
    if file_path:
        app_name = os.path.basename(file_path)[:-4] # Remove ".exe"
        new_app = {'exe_path': file_path, 'app_name': app_name}

        # Remove duplicates
        current_exe_paths = [app['exe_path'] for app in app_list_data]
        if file_path not in current_exe_paths:
            app_list_data.append(new_app)
            save_app_list(app_list_data)

            # Add to "Other" category if not already categorized
            in_category = False
            for category_apps in app_categories.values():
                if file_path in category_apps:
                    in_category = True
                    break
            if not in_category:
                app_categories["Other"].append(file_path)
                save_categories()

            refresh_category_view()
            messagebox.showinfo("App Added", f"{app_name} added to launcher.")
        else:
            messagebox.showinfo("Duplicate App", f"{app_name} is already in the launcher.")

# Function to add apps from currently running processes
def add_apps_from_running_processes():
    global app_list_data, app_categories
    added_count = 0
    processes = psutil.process_iter(['pid', 'name', 'exe'])
    running_apps = []

    for process in processes:
        try:
            exe_path = process.info['exe']
            app_name = process.info['name']
            if exe_path and exe_path.lower().endswith(".exe"): # Ensure it's an exe and has a path
                running_apps.append({'exe_path': exe_path, 'app_name': app_name})
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue # Ignore processes we can't get info from

    current_exe_paths = [app['exe_path'] for app in app_list_data]
    newly_added_apps = []

    for app_info in running_apps:
        if app_info['exe_path'] not in current_exe_paths:
            app_list_data.append(app_info)
            newly_added_apps.append(app_info['app_name'])
            added_count += 1
            current_exe_paths.append(app_info['exe_path']) # To avoid dupes within this function call

            # Add to "Other" category if not already categorized
            in_category = False
            for category_apps in app_categories.values():
                if app_info['exe_path'] in category_apps:
                    in_category = True
                    break
            if not in_category:
                app_categories["Other"].append(app_info['exe_path'])


    save_app_list(app_list_data)
    save_categories()
    refresh_category_view()

    if added_count > 0:
        messagebox.showinfo("Apps Added", f"{added_count} apps from running processes added: {', '.join(newly_added_apps)}")
    else:
        messagebox.showinfo("No New Apps Added", "No new apps from running processes were added.")

def search_apps():
    search_term = search_entry.get()
    refresh_category_view(search_term)

# Create tray icon
def create_tray_icon(root):
    # Try to load the icon, use a default if not found
    try:
        image = Image.open("its.png")
    except:
        # Create a simple icon as fallback
        image = Image.new('RGB', (64, 64), color='blue')

    menu = pystray.Menu(
        pystray.MenuItem("Open App Manager", lambda icon, item: show_window(root, icon)),
        pystray.MenuItem("Exit", lambda icon, item: quit_app(root, icon))
    )
    icon = pystray.Icon("AppManager", image, "App Manager", menu)
    return icon

def show_window(root, icon=None):
    root.deiconify()
    root.lift()
    root.focus_force()
    if icon:
        icon.stop()

def hide_window(root, icon):
    root.withdraw()
    icon.run()

def quit_app(root, icon=None):
    close_all_apps()
    root.destroy()
    if icon:
        icon.stop()

if __name__ == "__main__":
    # Initialize the app
    ctk.set_appearance_mode("dark")  # Options: "Light", "Dark", "System"
    ctk.set_default_color_theme("blue")  # Options: "blue", "green", "dark-blue"

    root = ctk.CTk()
    root.title("cold's app launcher")

    # Set window size and position
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    window_width = 900
    window_height = 700
    x_pos = (screen_width - window_width) // 2
    y_pos = (screen_height - window_height) // 2
    root.geometry(f"{window_width}x{window_height}+{x_pos}+{y_pos}")

    # Load data
    load_shortcuts()
    load_categories()
    app_list_data = load_app_list()

    # Main UI
    root.protocol("WM_DELETE_WINDOW", lambda: hide_window(root, tray_icon))

    # Create main content frame
    main_frame = ctk.CTkFrame(root, fg_color="transparent")
    main_frame.pack(fill="both", expand=True)

    # Header
    header_frame = ctk.CTkFrame(main_frame, height=60, corner_radius=0)
    header_frame.pack(fill="x")

    title_label = ctk.CTkLabel(
        header_frame,
        text="cold's app launcher",
        font=ctk.CTkFont(size=24, weight="bold"),
        text_color="#00BFFF"
    )
    title_label.pack(side="left", padx=20, pady=10)

    # Action buttons in header
    action_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
    action_frame.pack(side="right", padx=20, pady=10)

    # Search functionality
    search_frame = ctk.CTkFrame(action_frame, fg_color="transparent")
    search_frame.pack(side="left", padx=(0, 10))

    search_entry = ctk.CTkEntry(search_frame, width=150, placeholder_text="Search apps...")
    search_entry.pack(side="left")

    search_button = ctk.CTkButton(
        search_frame,
        text="Search",
        width=70,
        command=search_apps
    )
    search_button.pack(side="left", padx=(5, 0))


    scan_button = ctk.CTkButton(
        action_frame,
        text="Scan for Apps",
        command=lambda: scan_for_apps(root),
        width=120
    )
    scan_button.pack(side="left", padx=(0, 10))

    add_app_button = ctk.CTkButton(
        action_frame,
        text="Add App",
        command=add_individual_app,
        width=120
    )
    add_app_button.pack(side="left", padx=(0, 10))

    add_taskbar_apps_button = ctk.CTkButton(
        action_frame,
        text="Add Running Apps",
        command=add_apps_from_running_processes,
        width=150
    )
    add_taskbar_apps_button.pack(side="left", padx=(0, 10))

    close_all_button = ctk.CTkButton(
        action_frame,
        text="Close All Apps",
        command=close_all_apps,
        fg_color="#DC3545",
        hover_color="#B02A37",
        width=120
    )
    close_all_button.pack(side="left")

    # Content area with tabview for categories
    content_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
    content_frame.pack(fill="both", expand=True, padx=20, pady=20)

    # Tab view for categories
    tabview = ctk.CTkTabview(content_frame, fg_color="#2B2B2B")
    tabview.pack(fill="both", expand=True)

    # Create tabs for each category
    category_tabs = {}
    for category in app_categories.keys():
        tab = tabview.add(category)
        category_tabs[category] = tab

    # Set active tab to Favorites
    tabview.set("Favorites")

    # Bottom bar
    bottom_frame = ctk.CTkFrame(main_frame, height=50, corner_radius=0)
    bottom_frame.pack(fill="x")

    # Add category button
    add_category_button = ctk.CTkButton(
        bottom_frame,
        text="+ Add Category",
        command=lambda: CategoryDialog(root),
        width=120,
        fg_color="#555555",
        hover_color="#777777"
    )
    add_category_button.pack(side="left", padx=20, pady=10)

    # Close all shortcut
    shortcut_frame = ctk.CTkFrame(bottom_frame, fg_color="transparent")
    shortcut_frame.pack(side="right", padx=20, pady=10)

    shortcut_label = ctk.CTkLabel(shortcut_frame, text="Close All Shortcut:")
    shortcut_label.pack(side="left", padx=(0, 10))

    close_all_shortcut_var = tk.StringVar(value=app_shortcuts.get('close_all_shortcut', ''))
    shortcut_entry = ctk.CTkEntry(shortcut_frame, textvariable=close_all_shortcut_var, width=120)
    shortcut_entry.pack(side="left", padx=(0, 10))

    def set_close_all_shortcut():
        shortcut = close_all_shortcut_var.get()
        app_shortcuts['close_all_shortcut'] = shortcut
        save_shortcuts()
        try:
            keyboard.remove_hotkey(app_shortcuts.get('close_all_shortcut'))
        except:
            pass
        if shortcut:
            try:
                keyboard.add_hotkey(shortcut, close_all_apps)
                messagebox.showinfo("Shortcut Set", f"Close All Apps shortcut set to '{shortcut}'")
            except Exception as e:
                messagebox.showerror("Hotkey Error", f"Could not set hotkey '{shortcut}'. It might be invalid or already in use.")

    set_button = ctk.CTkButton(
        shortcut_frame,
        text="Set",
        command=set_close_all_shortcut,
        width=60
    )
    set_button.pack(side="left")

    # Populate the UI with apps
    refresh_category_view()

    # Create system tray icon
    tray_icon = create_tray_icon(root)

    # Start app
    root.mainloop()