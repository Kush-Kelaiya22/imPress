"""Server-side maintenance commands, run on the host that has the database (#120).

    cd backend && python -m app.manage restore-super-admin --username admin
    docker exec -w /app/backend impress python -m app.manage restore-super-admin --username admin
    python -m app.manage audit-verify /var/log/impress/audit.jsonl

restore-super-admin recovers an installation where no one can manage users
any more (for example a database locked out before #116): it makes the named
account an active super admin with a new one-time password, signs out its old
sessions and records the action in the activity log. There is deliberately no
HTTP equivalent: running it needs the same access as reading the database file.
"""

import argparse
import asyncio
import secrets
import sys

from sqlalchemy import select


async def restore_super_admin(username: str, create: bool = False) -> str:
    """Returns the new password. Raises LookupError for an unknown username."""
    from .activity import log_activity
    from .auth import hash_password, revoke_user_sessions
    from .database import async_session, engine, init_db
    from .models import User

    await init_db()                                   # same schema as the server would use
    password = secrets.token_urlsafe(12)
    async with async_session() as db:
        user = (await db.execute(select(User).where(User.username == username))).scalar_one_or_none()
        created = user is None
        if created:
            if not create:
                raise LookupError(username)
            user = User(username=username, email=f"{username}@impress.local", full_name="Recovered admin",
                        hashed_password="", role="super_admin")
            db.add(user)
            await db.flush()
        before = None if created else {"role": user.role, "is_active": user.is_active}
        user.role, user.is_active = "super_admin", True
        user.hashed_password = hash_password(password)
        await revoke_user_sessions(db, user.id)
        await log_activity(db, "user.recovery", None, "user", user.id,
                           {"via": "cli", "username": username, "before": before, "created": created})
        await db.commit()
    await engine.dispose()
    return password


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="python -m app.manage", description=__doc__.split("\n\n")[0])
    sub = parser.add_subparsers(dest="command", required=True)
    r = sub.add_parser("restore-super-admin", help="make an account an active super admin with a new password")
    r.add_argument("--username", required=True)
    r.add_argument("--create", action="store_true", help="create the account if it does not exist")
    v = sub.add_parser("audit-verify", help="check an external audit file's hash chain (policy audit.sink_path)")
    v.add_argument("file")
    args = parser.parse_args(argv)

    if args.command == "audit-verify":
        from pathlib import Path

        from .services import auditsink
        problems = auditsink.verify_file(Path(args.file))
        print("\n".join(problems) if problems else "the audit chain is intact")
        return 1 if problems else 0

    try:
        password = asyncio.run(restore_super_admin(args.username, args.create))
    except LookupError:
        print(f"No user named {args.username!r}. Check the name, or add --create.", file=sys.stderr)
        return 2
    print(f"{args.username} is an active super admin. One-time password (change it after logging in):")
    print(password)
    return 0


if __name__ == "__main__":
    sys.exit(main())
