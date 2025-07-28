# Copyright (C) 2025 AIDC-AI
# This project is licensed under the MIT License (SPDX-License-identifier: MIT).

import chainlit as cl

@cl.password_auth_callback
def auth_callback(username: str, password: str):
    if (username, password) == ("dev", "dev"):
        return cl.User(
            identifier="dev", metadata={"role": "user", "provider": "credentials"}
        )
    else:
        return None