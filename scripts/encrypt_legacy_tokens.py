"""One-time migration: encrypt legacy plaintext GitLab tokens.

Iterates all User records and encrypts any plaintext tokens still stored
in `gitlab_access_token` / `gitlab_refresh_token` columns.

Usage:
    python -m scripts.encrypt_legacy_tokens

Requires DATABASE_URL, SECRET_KEY env vars to be set.
"""

import asyncio
import logging
import os
import sys

logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


async def migrate() -> int:
    """Encrypt all plaintext tokens in the users table."""
    # Add src to path so app imports work
    src_dir = os.path.join(os.path.dirname(__file__), "..", "src")
    sys.path.insert(0, os.path.abspath(src_dir))

    from sqlalchemy import select
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

    from app.config import get_settings
    from app.models.user import User
    from app.security.token_encryption import encrypt_token, is_encrypted

    settings = get_settings()
    engine = create_async_engine(str(settings.database_url), echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    migrated = 0
    skipped = 0

    async with async_session() as session:
        result = await session.execute(select(User))
        users = list(result.scalars().all())

        for user in users:
            changed = False

            # Encrypt access token if plaintext
            if user.gitlab_access_token and not is_encrypted(user.gitlab_access_token):
                user.gitlab_access_token = encrypt_token(
                    user.gitlab_access_token, settings.secret_key
                )
                changed = True

            # Encrypt refresh token if plaintext
            if user.gitlab_refresh_token and not is_encrypted(user.gitlab_refresh_token):
                user.gitlab_refresh_token = encrypt_token(
                    user.gitlab_refresh_token, settings.secret_key
                )
                changed = True

            if changed:
                await session.merge(user)
                migrated += 1
                logger.info("Encrypted tokens for user: %s", user.username)
            else:
                skipped += 1

        await session.commit()

    await engine.dispose()
    logger.info("Migration complete: %d encrypted, %d already encrypted/empty", migrated, skipped)
    return migrated


if __name__ == "__main__":
    count = asyncio.run(migrate())
    sys.exit(0 if count >= 0 else 1)
