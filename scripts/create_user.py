#!/usr/bin/env python
"""Utility script to create users in data/office_data.db.

Run from the project root (with .venv active):

    python scripts/create_user.py

This will prompt for username, full name, role and password,
then insert a new row into the `users` table with a bcrypt hash.
"""

import getpass
import sqlite3
from pathlib import Path

import bcrypt


# Base paths
ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "office_data.db"


def main() -> None:
    print(f"Using DB: {DB_PATH}")
    if not DB_PATH.exists():
        raise SystemExit("❌ office_data.db not found in data/ directory")

    username = input("Username: ").strip()
    if not username:
        raise SystemExit("❌ Username is required")

    full_name = input("Full name: ").strip() or username

    role = input("Role [viewer/editor/admin] (default: editor): ").strip() or "editor"
    if role not in {"viewer", "editor", "admin"}:
        raise SystemExit("❌ Role must be one of: viewer, editor, admin")

    password = getpass.getpass("Password: ")
    password2 = getpass.getpass("Repeat password: ")
    if not password:
        raise SystemExit("❌ Password is required")
    if password != password2:
        raise SystemExit("❌ Passwords do not match")

    # Hash password with bcrypt (12 rounds, matches existing style)
    password_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt(rounds=12)
    password_hash = bcrypt.hashpw(password_bytes, salt).decode("utf-8")

    conn = sqlite3.connect(str(DB_PATH))
    try:
        conn.execute(
            """
            INSERT INTO users (username, password_hash, full_name, role)
            VALUES (?, ?, ?, ?)
            """,
            (username, password_hash, full_name, role),
        )
        conn.commit()
        print(f"✅ User '{username}' created with role '{role}'")
    except sqlite3.IntegrityError as e:
        # In case username is unique and already exists
        raise SystemExit(f"❌ Could not create user (maybe username already exists?): {e}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
