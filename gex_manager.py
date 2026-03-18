import os
import zipfile
import config_manager

def create_workspace(notebook_id):
    base = config_manager.get_workspace_base()
    workspace_path = os.path.join(base, notebook_id)
    os.makedirs(os.path.join(workspace_path, "sources"), exist_ok=True)
    return workspace_path

def pack_gex(notebook_id, export_path):
    base = config_manager.get_workspace_base()
    workspace_path = os.path.join(base, notebook_id)
    
    with zipfile.ZipFile(export_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(workspace_path):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, workspace_path)
                zipf.write(file_path, arcname)
    return export_path

def unpack_gex(gex_filepath, notebook_id):
    workspace_path = create_workspace(notebook_id)
    with zipfile.ZipFile(gex_filepath, 'r') as zipf:
        zipf.extractall(workspace_path)
    return workspace_path