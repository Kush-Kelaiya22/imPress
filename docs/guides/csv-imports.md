# CSV imports

Bulk-create content from a spreadsheet instead of typing it into forms. Every import is checked on the server first and shows a preview. **Nothing is stored until you confirm, and a file with any invalid row stores nothing at all.**

| Import | Where | Who |
|---|---|---|
| [Quiz questions](#quiz-questions) | Create Quiz page → *Import questions from CSV* | teachers (for their classes) and admins |

Common rules for every import:
- **UTF-8.** In Excel use *Save As → CSV UTF-8 (Comma delimited)*. A byte-order mark is fine; other encodings are refused with that hint.
- **The first row is the header.** Column names are case-insensitive and may be in any order. **Unknown columns are refused**, so a column you expect to be imported is never silently ignored.
- **At most 1 MB and 500 rows** per file.
- Quoted values may contain commas, quotes (`""`) and line breaks.
- Re-uploading the same file is safe: rows that already exist are reported as duplicates and skipped.

## Quiz questions

1. Open a class → **New Quiz**.
2. In *Import questions from CSV*, click **Download template** to get an example, or drop your file on the box.
3. Read the preview. Each row is **valid**, **invalid** (with the reason), or **duplicate** (of an earlier line, or of a question already in the quiz). A note warns when text is longer than a student module can display (it will be cut off on the device).
4. If every row is valid, click **Add N questions to this quiz**. They appear in the form below, where you can still edit or delete them. Then click **Create Quiz**.

![Preview with an invalid row: nothing can be added until it is fixed](../assets/ui/csv-questions-invalid.png)

| Column | Required | What to put in it |
|---|---|---|
| `question_text` | yes | the question, up to 1000 characters |
| `option_a`, `option_b` | yes | the first two answers, up to 200 characters each |
| `option_c`, `option_d` | no | more answers; leave the rest empty (no gaps: D needs C) |
| `correct_option` | yes | `A`–`D` (or `1`–`4`) |

Student modules have four buttons, so a question has **2–4 options**. They show about 139 bytes of a question and 14 bytes of an option (non-Latin scripts use 2–3 bytes per letter). Longer text is accepted with a warning.

```csv
question_text,option_a,option_b,option_c,option_d,correct_option
"What is 2 + 2?",3,4,5,6,B
"Which planet is closest to the Sun?",Mercury,Venus,,,A
```

![A valid file: the questions are ready to add](../assets/ui/csv-questions-preview.png)

To add questions to an **existing draft quiz** from a script, use `POST /api/quizzes/{id}/questions/import` ([REST API](../api/rest-api.md#importing-questions-from-csv-31)).
