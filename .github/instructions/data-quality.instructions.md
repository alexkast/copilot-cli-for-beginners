---
applyTo: "**/data.json"
---

# JSON Data Quality

- Every record must contain exactly these fields: `title`, `author`, `year`, `read`.
- `title` and `author` must be non-empty strings (not `""` or whitespace-only).
- `year` must be an integer between `1` and `current_year + 1`; use `0` only for unknown publication year.
- `read` must be a boolean (`true` or `false`).
- The top-level structure must be a JSON array `[...]`.
- No extra or unrecognised fields are allowed.
