---
applyTo: "**/*.py"
---

# Python Style

- Follow PEP 8: 4-space indent, max 88 chars per line, two blank lines between top-level definitions.
- Use Python 3.10+ native type hints: `list[str]`, `str | None` — never `List`, `Optional` from `typing`.
- Every public function and class must have a Google-style docstring with `Args`, `Returns`, and `Raises` sections.
- All function parameters and return types must be annotated.
- Use `f-strings` for string formatting; avoid `%` and `.format()`.
- Raise domain exceptions from `exceptions.py`; never raise raw `ValueError`, `KeyError`, or `Exception`.
