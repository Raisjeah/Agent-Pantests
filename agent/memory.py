import os
import sqlite3
from langgraph.checkpoint.sqlite import SqliteSaver

def get_checkpointer(db_path: str) -> SqliteSaver:
    db_path = os.path.expanduser(db_path)
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path, check_same_thread=False)
    return SqliteSaver(conn)
