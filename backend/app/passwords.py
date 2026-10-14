"""Password policy for new and changed passwords (#153).

Existing passwords keep working; the rule applies when a password is set.
"""

from typing import Annotated

from pydantic import AfterValidator

MIN_LENGTH = 10

# The most common passwords and classroom-obvious ones; a guesser tries these first.
COMMON = frozenset("""
password password1 password12 password123 passw0rd passw0rd1 p@ssw0rd p@ssword 1234567890 0123456789
12345678910 1111111111 0000000000 1q2w3e4r5t qwertyuiop qwerty1234 qwerty12345 asdfghjkl1 iloveyou12
welcome123 welcome1234 letmein123 admin12345 administrator admin@1234 admin@123 changeme123 changeme1234
teacher123 teacher1234 student123 student1234 impress123 impress1234 classroom1 classroom123 school1234
abcdefghij abcd123456 abc1234567 1234abcd12 superadmin superadmin1 rootroot12 trustno1234
""".split())


SPECIAL = "!@#$%^&*()-_=+[]{};:,.<>?/|~"
POLICY_TEXT = "at least 8 characters, with lower and upper case letters, a number and a special character"


def complexity_problem(password: str) -> str | None:
    """The rule for administrators, faculty and TAs (v2.2): 8+ characters, lower and upper case, a number, a special character."""
    if len(password) < 8:
        return "must be at least 8 characters"
    if not any(c.islower() for c in password):
        return "needs a lower-case letter"
    if not any(c.isupper() for c in password):
        return "needs an upper-case letter"
    if not any(c.isdigit() for c in password):
        return "needs a number"
    if not any(not c.isalnum() for c in password):
        return "needs a special character (for example ! @ # $ %)"
    return None


def problem(password: str, username: str = "", role: str = "teacher") -> str | None:
    """Why `password` is not acceptable as a new password for an account of `role`, or None.

    Administrators, faculty and TAs follow the complexity rule above. A super admin keeps the
    longer rule (10+ characters, not a common password, enough variety); the complexity rule is not
    applied to them. Nobody may use a common password or their username."""
    lowered = password.lower()
    if lowered in COMMON:
        return "is too common"
    if username and lowered == username.strip().lower():
        return "must not be the username"
    if role == "super_admin":
        if len(password) < MIN_LENGTH:
            return f"must be at least {MIN_LENGTH} characters"
        if len(set(password)) < 4:
            return "uses too few different characters"
        return None
    return complexity_problem(password)


def strength(password: str, username: str = "") -> dict:
    """A score from 0 to 4 for the strength meter, a label, and what is missing. The web app's
    meter (passwordStrength in ui.js) uses the same rules."""
    checks = [("8 or more characters", len(password) >= 8),
              ("a lower-case letter", any(c.islower() for c in password)),
              ("an upper-case letter", any(c.isupper() for c in password)),
              ("a number", any(c.isdigit() for c in password)),
              ("a special character", any(not c.isalnum() for c in password))]
    missing = [name for name, ok in checks if not ok]
    bad = password.lower() in COMMON or bool(username and password.lower() == username.strip().lower())
    met = len(checks) - len(missing)
    if not password:
        score = 0
    elif bad:
        score = 0
    elif missing:
        score = 0 if met <= 2 else 1
    else:
        score = 2 + (len(password) >= 12) + (len(password) >= 16)
    return {"score": score, "label": ["Too weak", "Weak", "Fair", "Good", "Strong"][score], "missing": missing}


def generate(length: int = 12) -> str:
    """A random password with lower and upper case, digits and special characters (never fewer than 12 here)."""
    import secrets
    length = max(12, length)
    pools = ["abcdefghijkmnopqrstuvwxyz", "ABCDEFGHJKLMNPQRSTUVWXYZ", "23456789", "!@#$%^&*-_=+?"]   # no look-alikes
    chars = [secrets.choice(p) for p in pools] + [secrets.choice("".join(pools)) for _ in range(length - 4)]
    secrets.SystemRandom().shuffle(chars)
    return "".join(chars)


def _check(password: str) -> str:
    return password


NewPassword = Annotated[str, AfterValidator(_check)]   # shape only: the rule depends on the account's role, so routes call problem()
