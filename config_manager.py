import os
import json

# Saves config to the user's home directory so it isn't deleted if the .exe is moved
CONFIG_FILE = os.path.join(os.path.expanduser("~"), ".granthex_config.json")

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_config(api_key, workspace_path):
    os.makedirs(workspace_path, exist_ok=True)
    config_data = {
        "api_key": api_key,
        "workspace_path": workspace_path
    }
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config_data, f)

def is_setup_complete():
    config = load_config()
    return bool(config.get("api_key")) and bool(config.get("workspace_path"))

def get_api_key():
    return load_config().get("api_key")

def get_workspace_base():
    # Defaults to a "GrantheX_Workspaces" folder in the user's Documents
    default_path = os.path.join(os.path.expanduser("~"), "Documents", "GrantheX_Workspaces")
    return load_config().get("workspace_path", default_path)