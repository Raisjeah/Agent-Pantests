import os
from langgraph.checkpoint.sqlite import SqliteSaver

def get_checkpointer(db_path: str) -> SqliteSaver:
    db_path = os.path.expanduser(db_path)
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    return SqliteSaver.from_conn_string(db_path)
