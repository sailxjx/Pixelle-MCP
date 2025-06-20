from pathlib import Path
import base64
import os

def get_root_path() -> str:
    return str(Path(__file__).parent.parent)

def get_data_path(*paths: str) -> str:
    return os.path.join(get_root_path(), "data", *paths)

def save_base64_to_file(base64_str, file_path):
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "wb") as f:
        f.write(base64.b64decode(base64_str))

