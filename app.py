import os
import sys
import threading
from flask import Flask, render_template, request, jsonify, send_file, send_from_directory
import webview 
from werkzeug.utils import secure_filename

import engine
import gex_manager
import config_manager

# --- PyInstaller Resource Helper ---
def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# Initialize Flask with PyInstaller-compatible paths
app = Flask(__name__, 
            template_folder=resource_path('templates'),
            static_folder=resource_path('static'))
            
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024 

# --- ROUTES ---
@app.route('/favicon.ico')
def favicon():
    return send_file(resource_path('icon.ico'), mimetype='image/vnd.microsoft.icon')

@app.route('/')
def index():
    # SETUP CHECK: If the user hasn't set up the app, intercept them!
    if not config_manager.is_setup_complete():
        return render_template('setup.html', default_path=config_manager.get_workspace_base())
    
    # Load Main App
    workspace_base = config_manager.get_workspace_base()
    os.makedirs(workspace_base, exist_ok=True)
    os.makedirs(os.path.join(workspace_base, 'exports'), exist_ok=True)
    
    notebooks = [d for d in os.listdir(workspace_base) if os.path.isdir(os.path.join(workspace_base, d)) and d != "exports"]
    return render_template('index.html', notebooks=notebooks)

@app.route('/api/setup', methods=['POST'])
def setup_app():
    data = request.json
    config_manager.save_config(data.get("api_key"), data.get("workspace_path"))
    return jsonify({"status": "success"})

@app.route('/api/select_folder')
def select_folder():
    """Triggers the native Windows folder selection dialog."""
    try:
        # Grab the active PyWebview window
        if webview.windows:
            window = webview.windows[0]
            # Open the native folder dialog
            result = window.create_file_dialog(webview.FOLDER_DIALOG)
            
            # If the user selected a folder, return it
            if result and len(result) > 0:
                return jsonify({"path": result[0]})
    except Exception as e:
        print(f"Dialog error: {e}")
        
    # If the user clicked 'Cancel' or closed the dialog, return empty
    return jsonify({"path": ""})

# --- (KEEP ALL YOUR OTHER FLASK ROUTES THE SAME AS BEFORE, BUT UPDATE PATHS) ---
# Example: Change os.path.join('workspaces', notebook_id) 
# To: os.path.join(config_manager.get_workspace_base(), notebook_id)
# Apply this change to upload_file, chat, export_gex, get_guide, generate_podcast, serve_audio, get_history, handle_notes.

# --- LAUNCHER & AUTO-REGISTRY ---
def run_flask():
    app.run(host='127.0.0.1', port=5000, debug=False, use_reloader=False)

def on_closed():
    print("Shutting down GrantheX...")
    os._exit(0) 

def auto_register_exe():
    """Automatically registers the .gex extension to the compiled .exe file"""
    if getattr(sys, 'frozen', False): 
        try:
            import winreg
            exe_path = os.path.abspath(sys.executable)
            command = f'"{exe_path}" "%1"'
            
            key_ext = winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Software\Classes\.gex")
            winreg.SetValue(key_ext, "", winreg.REG_SZ, "GrantheX.Notebook")
            winreg.CloseKey(key_ext)

            key_class = winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Software\Classes\GrantheX.Notebook")
            winreg.SetValue(key_class, "", winreg.REG_SZ, "GrantheX AI Notebook File")
            
            key_command = winreg.CreateKey(key_class, r"shell\open\command")
            winreg.SetValue(key_command, "", winreg.REG_SZ, command)
        except Exception:
            pass # Fails silently if user lacks permissions, no big deal.

if __name__ == '__main__':
    # Auto-register .exe on launch
    auto_register_exe()

    # Intercept double-clicked .gex files
    if len(sys.argv) > 1 and sys.argv[1].endswith('.gex'):
        if config_manager.is_setup_complete():
            gex_filepath = sys.argv[1]
            base_name = os.path.basename(gex_filepath).replace('.gex', '')
            workspace_base = config_manager.get_workspace_base()
            if not os.path.exists(os.path.join(workspace_base, base_name)):
                gex_manager.unpack_gex(gex_filepath, base_name)
    
    t = threading.Thread(target=run_flask)
    t.daemon = True
    t.start()
    
    window = webview.create_window(
        title='GrantheX - AI Notebook', 
        url='http://127.0.0.1:5000', 
        width=1200, 
        height=800
    )
    window.events.closed += on_closed
    webview.start(icon=resource_path('icon.ico'))