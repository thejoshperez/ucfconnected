#!/usr/bin/env python3
"""
One-time interactive login that handles 2FA and saves a session file.
Run this once:
    python login.py

The scraper will automatically reuse the saved session on every
subsequent run — no 2FA prompt needed again unless the session expires.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

import instaloader

SESSION_DIR = os.path.join(os.path.dirname(__file__), ".sessions")
os.makedirs(SESSION_DIR, exist_ok=True)


def main() -> None:
    username = input("Instagram username: ").strip()
    if not username:
        print("No username entered — exiting.")
        sys.exit(1)

    loader = instaloader.Instaloader(quiet=True)

    try:
        loader.login(username, input("Password: ").strip())
        print("Logged in (no 2FA required).")
    except instaloader.exceptions.TwoFactorAuthRequiredException:
        code = input("2FA code: ").strip()
        loader.two_factor_login(code)
        print("2FA login successful.")
    except instaloader.exceptions.BadCredentialsException:
        print("Wrong username or password.")
        sys.exit(1)

    session_file = os.path.join(SESSION_DIR, username)
    loader.save_session_to_file(session_file)
    print(f"Session saved to {session_file}")
    print()
    print("Add this to backend/.env:")
    print(f"  INSTAGRAM_USERNAME={username}")
    print(f"  INSTAGRAM_SESSION_FILE={session_file}")


if __name__ == "__main__":
    main()
