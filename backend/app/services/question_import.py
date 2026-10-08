"""CSV → quiz questions (#31). Pure: no database access.

Columns: question_text, option_a, option_b, [option_c], [option_d],
correct_option (A-D or 1-4). Each row is validated with the same schema as a
question typed into the form (QuizQuestionCreate), plus the student-module
display limits (#49).
"""

from __future__ import annotations

from pydantic import ValidationError

from ..schemas import (DEVICE_MAX_OPTIONS, QuestionImportReport, QuestionImportRow, QuizQuestionCreate,
                       question_warnings)
from .csv_import import read_rows, text_key

REQUIRED = ["question_text", "option_a", "option_b", "correct_option"]
OPTIONAL = ["option_c", "option_d"]
ALIASES = {
    "question": "question_text", "text": "question_text",
    "a": "option_a", "b": "option_b", "c": "option_c", "d": "option_d",
    "option_1": "option_a", "option_2": "option_b", "option_3": "option_c", "option_4": "option_d",
    "correct": "correct_option", "correct_answer": "correct_option", "answer": "correct_option",
}
OPTION_COLUMNS = ["option_a", "option_b", "option_c", "option_d"][:DEVICE_MAX_OPTIONS]
MAX_QUESTION_CHARS = 1000
MAX_OPTION_CHARS = 200

TEMPLATE = (
    "question_text,option_a,option_b,option_c,option_d,correct_option\r\n"
    '"What is 2 + 2?",3,4,5,6,B\r\n'
    '"Which planet is closest to the Sun?",Mercury,Venus,,,A\r\n'
)


def _correct_index(value: str, n_options: int) -> tuple[int | None, str | None]:
    v = value.strip().upper()
    if len(v) == 1 and "A" <= v <= "D":
        idx = ord(v) - ord("A")
    elif v.isdigit() and 1 <= int(v) <= 4:
        idx = int(v) - 1
    else:
        return None, f"correct_option '{value}' must be a letter A–D or a number 1–4"
    if idx >= n_options:
        return None, f"correct_option {'ABCD'[idx]} points at an empty option"
    return idx, None


def parse_questions(raw: bytes, existing_texts: set[str] = frozenset()) -> QuestionImportReport:
    rows = read_rows(raw, REQUIRED, OPTIONAL, ALIASES)
    seen: dict[str, int] = {}
    out: list[QuestionImportRow] = []
    for line, r in rows:
        errors: list[str] = []
        if "__extra__" in r:
            errors.append(r.pop("__extra__"))
        text = r["question_text"]
        cells = [r.get(c, "") for c in OPTION_COLUMNS]
        last = max((i for i, c in enumerate(cells) if c), default=-1)
        options = cells[:last + 1]
        if any(not o for o in options):
            gaps = ", ".join("ABCD"[i] for i, o in enumerate(options) if not o)
            errors.append(f"option {gaps} is empty but a later option is filled")
        if len(text) > MAX_QUESTION_CHARS:
            errors.append(f"question_text is longer than {MAX_QUESTION_CHARS} characters")
        errors += [f"option {'ABCD'[i]} is longer than {MAX_OPTION_CHARS} characters"
                   for i, o in enumerate(options) if len(o) > MAX_OPTION_CHARS]
        correct, err = _correct_index(r["correct_option"], len(options)) if r["correct_option"] \
            else (None, "correct_option is empty")
        if err:
            errors.append(err)
        if not errors:
            try:
                QuizQuestionCreate(question_text=text, options=options, correct_option=correct)
            except ValidationError as e:
                errors += [f"{'.'.join(map(str, x['loc'])) or 'question'}: {x['msg']}" for x in e.errors()]

        row = QuestionImportRow(line=line, question_text=text, options=options, correct_option=correct,
                                status="invalid" if errors else "valid", errors=errors)
        key = text_key(text)
        if not errors:
            if key in existing_texts:
                row.status, row.duplicate_of = "duplicate", "already in this quiz"
            elif key in seen:
                row.status, row.duplicate_of = "duplicate", f"line {seen[key]}"
            else:
                seen[key] = line
                row.warnings = question_warnings(len(seen), text, options)
        out.append(row)

    count = {s: sum(r.status == s for r in out) for s in ("valid", "invalid", "duplicate")}
    return QuestionImportReport(total=len(out), valid=count["valid"], invalid=count["invalid"],
                                duplicate=count["duplicate"], imported=0, skipped=len(out), rows=out)
