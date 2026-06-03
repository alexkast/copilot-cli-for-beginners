---
applyTo: "**/tests/**/*.py"
---

# Pytest Standards

- Name tests `test_<what>_<condition>_<expected>` (e.g. `test_add_book_empty_title_raises`).
- Use `pytest.raises(ExceptionType)` to assert exceptions — never `try/except` in tests.
- Isolate file I/O with `monkeypatch.setattr(books, "DATA_FILE", str(tmp_path / "data.json"))`.
- One logical assertion per test; use separate tests for each edge case.
- Cover three cases for every feature: happy path, validation error, not-found / edge case.
- Never import or test private functions (prefixed with `_`).
