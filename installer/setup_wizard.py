import os
import sys
import zipfile
import threading
import requests
import tkinter as tk
from tkinter import ttk, messagebox

# --- CONFIGURATION ---
APP_NAME = "GrantheX"
# You will update this URL later once you upload your zip to GitHub Releases
DOWNLOAD_URL = "https://github.com/electrollminux/GrantheX/releases/download/v1.0/GrantheX_App.zip" 

# Install to AppData/Local so we don't need Admin permissions!
INSTALL_DIR = os.path.join(os.environ.get('LOCALAPPDATA'), APP_NAME)
ZIP_PATH = os.path.join(os.environ.get('TEMP'), f"{APP_NAME}_download.zip")

class InstallerApp:
    def __init__(self, root):
        self.root = root
        self.root.title(f"{APP_NAME} Setup")
        self.root.geometry("450x250")
        self.root.resizable(False, False)
        
        # UI Elements
        self.title_label = tk.Label(root, text=f"Installing {APP_NAME}", font=("Helvetica", 16, "bold"))
        self.title_label.pack(pady=20)
        
        self.status_label = tk.Label(root, text="Click 'Install' to begin downloading.", font=("Helvetica", 10))
        self.status_label.pack(pady=5)
        
        self.progress = ttk.Progressbar(root, orient="horizontal", length=350, mode="determinate")
        self.progress.pack(pady=10)
        
        self.install_btn = tk.Button(root, text="Install", command=self.start_installation, width=15, bg="#0d6efd", fg="white", font=("Helvetica", 10, "bold"))
        self.install_btn.pack(pady=10)

    def start_installation(self):
        self.install_btn.config(state=tk.DISABLED)
        self.progress['value'] = 0
        threading.Thread(target=self.download_and_extract, daemon=True).start()

    def download_and_extract(self):
        try:
            # 1. Download the Zip
            self.status_label.config(text="Downloading GrantheX... (This may take a while)")
            response = requests.get(DOWNLOAD_URL, stream=True)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(ZIP_PATH, 'wb') as file:
                for data in response.iter_content(chunk_size=4096):
                    downloaded += len(data)
                    file.write(data)
                    if total_size > 0:
                        percent = int((downloaded / total_size) * 100)
                        self.progress['value'] = percent
                        self.root.update_idletasks()

            # 2. Extract the Zip
            self.status_label.config(text="Extracting files...")
            self.progress.config(mode="indeterminate")
            self.progress.start()
            
            os.makedirs(INSTALL_DIR, exist_ok=True)
            with zipfile.ZipFile(ZIP_PATH, 'r') as zip_ref:
                zip_ref.extractall(INSTALL_DIR)
                
            # Clean up temp zip
            os.remove(ZIP_PATH)

            # 3. Create Desktop Shortcut
            self.status_label.config(text="Creating shortcuts...")
            self.create_desktop_shortcut()

            self.progress.stop()
            self.progress.config(mode="determinate")
            self.progress['value'] = 100
            self.status_label.config(text="Installation Complete!")
            
            messagebox.showinfo("Success", f"{APP_NAME} has been installed to your Desktop!")
            self.root.quit()

        except Exception as e:
            self.progress.stop()
            self.status_label.config(text="Installation Failed.")
            messagebox.showerror("Error", f"An error occurred: {str(e)}")
            self.install_btn.config(state=tk.NORMAL)

    def create_desktop_shortcut(self):
        """Uses a dynamic VBScript to create a shortcut without needing extra pip libraries"""
        desktop = os.path.join(os.environ.get('USERPROFILE'), 'Desktop')
        shortcut_path = os.path.join(desktop, f"{APP_NAME}.lnk")
        target_path = os.path.join(INSTALL_DIR, "app", "app.exe") # PyInstaller's output folder
        icon_path = os.path.join(INSTALL_DIR, "app", "icon.ico")
        
        vbs_script = f"""
        Set oWS = WScript.CreateObject("WScript.Shell")
        sLinkFile = "{shortcut_path}"
        Set oLink = oWS.CreateShortcut(sLinkFile)
        oLink.TargetPath = "{target_path}"
        oLink.IconLocation = "{icon_path}"
        oLink.WorkingDirectory = "{os.path.join(INSTALL_DIR, 'app')}"
        oLink.Save
        """
        
        vbs_path = os.path.join(os.environ.get('TEMP'), "create_shortcut.vbs")
        with open(vbs_path, 'w') as f:
            f.write(vbs_script)
        
        os.system(f'cscript //nologo "{vbs_path}"')
        os.remove(vbs_path)

if __name__ == "__main__":
    root = tk.Tk()
    app = InstallerApp(root)
    root.mainloop()