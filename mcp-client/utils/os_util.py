# Copyright (C) 2025 AIDC-AI
# This project is licensed under the MIT License (SPDX-License-identifier: MIT).

import os


def get_root_path(*paths: str) -> str:
    root_path = os.path.dirname(os.path.abspath(__file__))
    if paths:
        return os.path.join(root_path, *paths)
    return root_path    

def get_temp_path(*paths: str) -> str:
    temp_path = get_root_path("temp")
    os.makedirs(temp_path, exist_ok=True)
    if paths:
        return os.path.join(temp_path, *paths)
    return temp_path

def get_data_path(*paths: str) -> str:
    data_path = get_root_path("data")
    os.makedirs(data_path, exist_ok=True)
    if paths:
        return os.path.join(data_path, *paths)
    return data_path

def belongs_to_chainlit_file_path(path: str) -> bool:
    if not path or not os.path.exists(path):
        return False
    
    chainlit_file_path = get_root_path(".files")
    return os.path.abspath(path).startswith(chainlit_file_path)

if __name__ == "__main__":
    print(get_data_path())