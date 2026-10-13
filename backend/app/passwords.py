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


def problem(password: str, username: str = "") -> str | None:
    """Why `password` is not acceptable as a new password, or None."""
    if len(password) < MIN_LENGTH:
        return f"must be at least {MIN_LENGTH} characters"
    lowered = password.lower()
    if lowered in COMMON:
        return "is too common"
    if username and lowered == username.strip().lower():
        return "must not be the username"
    if len(set(password)) < 4:
        return "uses too few different characters"
    return None


def _check(password: str) -> str:
    why = problem(password)
    if why:
        raise ValueError(f"Password {why}")
    return password


NewPassword = Annotated[str, AfterValidator(_check)]
