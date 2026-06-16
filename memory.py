import os
import json
from datetime import datetime
from git import Repo

MEMORY_DIR = "./pnsv_chat_history"
MAX_HISTORY_ENTRIES = 50  

def get_current_repo_name(workspace_path: str = "./repo_workspace") -> str:
    """Detects the folder name or Git remote identifier of the active repo."""
    try:
        if os.path.exists(os.path.join(workspace_path, ".git")):
            repo = Repo(workspace_path)
            remote_url = repo.remotes.origin.url
            # Extracts 'repo_name' from 'https://github.com/user/repo_name.git'
            repo_name = remote_url.split("/")[-1].replace(".git", "").strip()
            if repo_name:
                return repo_name
    except Exception:
        pass
    
    # Fallback: if Git parsing fails, use the folder name layout
    if os.path.exists(workspace_path):
        return os.path.basename(os.path.abspath(workspace_path))
    return "default_repo"

def save_chat_turn(interface: str, user_query: str, ai_response: str):
    """Saves a chat turn into an isolated history partition, keeping a max of 20 entries."""
    os.makedirs(MEMORY_DIR, exist_ok=True)
    repo_name = get_current_repo_name()
    file_path = os.path.join(MEMORY_DIR, f"{repo_name}_history.json")
    
    history = []
    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                history = json.load(f)
        except Exception:
            history = []

    # 1. Append the new chat turn
    history.append({
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "interface": interface,
        "user": user_query,
        "assistant": ai_response
    })

    # 2. Apply sliding window: keep only the most recent 'MAX_HISTORY_ENTRIES'
    if len(history) > MAX_HISTORY_ENTRIES:
        history = history[-MAX_HISTORY_ENTRIES:]

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=4, ensure_ascii=False)

def get_chat_history() -> list:
    """Retrieves past logs linked exclusively to the active codebase."""
    repo_name = get_current_repo_name()
    file_path = os.path.join(MEMORY_DIR, f"{repo_name}_history.json")
    if not os.path.exists(file_path):
        return []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def clear_repo_history():
    """Wipes the history file for the active repository partition."""
    repo_name = get_current_repo_name()
    file_path = os.path.join(MEMORY_DIR, f"{repo_name}_history.json")
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
        except Exception:
            pass