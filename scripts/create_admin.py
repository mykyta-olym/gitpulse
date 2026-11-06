#!/usr/bin/env python3
"""Create or promote an admin user in the database.

OAuth-only mode: This script creates a user record that will be linked
to a GitLab account when the user logs in via OAuth.

Usage:
    python scripts/create_admin.py --username gitlab_username [--email admin@example.com]

Requires DATABASE_URL environment variable (synchronous psycopg2).
"""

import argparse
import os
import secrets
import sys

import psycopg2  # type: ignore[import-untyped]


def main() -> None:
    parser = argparse.ArgumentParser(description="Create/promote admin user for OAuth")
    parser.add_argument("--username", required=True, help="GitLab username")
    parser.add_argument("--email", default=None, help="Email address (optional)")
    args = parser.parse_args()

    db_url = os.environ.get("DATABASE_URL", "")
    if not db_url:
        print("ERROR: DATABASE_URL not set", file=sys.stderr)
        sys.exit(1)

    # Convert asyncpg URL to psycopg2
    db_url = db_url.replace("+asyncpg", "").replace("postgresql+psycopg2", "postgresql")

    # OAuth placeholder - not a real password, user must login via GitLab
    oauth_placeholder = f"oauth:{secrets.token_hex(32)}"

    conn = psycopg2.connect(db_url)
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO users (username, email, password_hash, role, is_active, gitlab_username)
                VALUES (%s, %s, %s, 'admin', true, %s)
                ON CONFLICT (username) DO UPDATE
                SET email = COALESCE(EXCLUDED.email, users.email),
                    role = 'admin',
                    is_active = true,
                    gitlab_username = COALESCE(users.gitlab_username, EXCLUDED.gitlab_username)
                """,
                (args.username, args.email, oauth_placeholder, args.username),
            )
            conn.commit()
            print(f"Admin user '{args.username}' created/promoted successfully.")
            print("User must login via GitLab OAuth to activate the account.")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
