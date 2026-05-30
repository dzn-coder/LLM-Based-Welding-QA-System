import json
import os

SESSION_FILE = "./Session_List/sessions.json"
CHAT_HISTORY_DIR = "./Chat_History"

def load_sessions():
    if os.path.exists(SESSION_FILE):
        with open(SESSION_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return ["默认会话"]


def save_sessions(session_list):
    os.makedirs(os.path.dirname(SESSION_FILE), exist_ok=True)
    with open(SESSION_FILE, "w", encoding="utf-8") as f:
        json.dump(session_list, f, ensure_ascii=False, indent=2)
    
def delete_session(session_id, session_list):
    # 1️⃣ 从列表移除
    if session_id in session_list:
        session_list.remove(session_id)

    # 2️⃣ 删除文件
    file_path = os.path.join(CHAT_HISTORY_DIR, f"{session_id}.json")
    if os.path.exists(file_path):
        os.remove(file_path)

    return session_list