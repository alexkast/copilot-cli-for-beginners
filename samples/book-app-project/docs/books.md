# `books.py` — Module Documentation

Manages the data model and persistence layer for the book collection app. All book data is stored in a local JSON file and loaded automatically on startup.

---

## Overview

This module provides two public objects:

| Name | Type | Purpose |
|---|---|---|
| `Book` | dataclass | Represents a single book entry |
| `BookCollection` | class | Manages the full collection (CRUD + persistence) |

All exceptions are defined in `exceptions.py` and imported here.

---

## `Book` — Data Model

A plain dataclass representing one book. Instances are created by `BookCollection.add_book()` and returned by most query methods.

```python
from books import Book

book = Book(title="Dune", author="Frank Herbert", year=1965)
book.read       # False (default)
book.year       # 1965
```

### Fields

| Field | Type | Required | Description |
|---|---|---|---|
| `title` | `str` | ✅ | Book title |
| `author` | `str` | ✅ | Author's full name |
| `year` | `int` | ✅ | Publication year. Use `0` for unknown |
| `read` | `bool` | ❌ | Whether the book has been read. Defaults to `False` |

> **Gotcha:** `Book` is a plain dataclass — it performs no validation. Always create books through `BookCollection.add_book()`, which enforces input rules.

---

## `BookCollection` — Collection Manager

Loads books from `data.json` on init and writes back to disk after every mutation.

```python
from books import BookCollection

collection = BookCollection()              # loads data.json (or starts empty)
book = collection.add_book("1984", "George Orwell", 1949)
collection.mark_as_read("1984")
collection.remove_book("1984")
```

### Constructor

```python
BookCollection()
```

- Reads `DATA_FILE` (`data.json`) from the current working directory.
- If the file does not exist, starts with an empty list (normal first-run behaviour).
- Raises `StorageError` if the file exists but is corrupt or unreadable.

---

### Methods

#### `add_book(title, author, year) → Book`

Adds a new book and saves to disk immediately.

```python
book = collection.add_book("The Hobbit", "J.R.R. Tolkien", 1937)
book_unknown_year = collection.add_book("Draft", "Someone", 0)  # year=0 = unknown
```

| Parameter | Type | Rules |
|---|---|---|
| `title` | `str` | Non-empty, non-whitespace |
| `author` | `str` | Non-empty, non-whitespace |
| `year` | `int` | `0` (unknown) or `1` to `current_year + 1` |

**Raises:**
- `ValidationError` — empty title/author, or year outside valid range
- `StorageError` — disk write failure

---

#### `list_books() → List[Book]`

Returns all books in insertion order.

```python
books = collection.list_books()   # [] if empty
for book in books:
    print(book.title)
```

> **Gotcha:** Returns a direct reference to the internal list. Do not mutate the returned value.

---

#### `find_book_by_title(title) → Optional[Book]`

Case-insensitive exact title match. Returns `None` if not found.

```python
book = collection.find_book_by_title("dune")   # matches "Dune"
if book is None:
    print("Not found")
```

---

#### `find_by_author(author) → List[Book]`

Case-insensitive exact author match. Returns all matching books (empty list if none).

```python
orwell_books = collection.find_by_author("george orwell")
```

> **Gotcha:** Exact full-name match only. `"Orwell"` will not match `"George Orwell"`. Use `search()` for partial matching.

---

#### `search(query) → List[Book]`

Case-insensitive **partial** substring search across both title and author fields.

```python
results = collection.search("orwell")   # matches title OR author
results = collection.search("the")      # matches "The Hobbit", "The Great Gatsby", etc.
```

---

#### `mark_as_read(title) → None`

Marks a book as read and saves to disk.

```python
collection.mark_as_read("Dune")
```

**Raises:** `BookNotFoundError` if no book with that title exists (case-insensitive).

---

#### `remove_book(title) → None`

Removes a book from the collection and saves to disk.

```python
collection.remove_book("Dune")
```

**Raises:** `BookNotFoundError` if no book with that title exists (case-insensitive).

---

## Data File (`data.json`)

Books are stored as a JSON array. Each entry maps directly to `Book` fields:

```json
[
  {
    "title": "1984",
    "author": "George Orwell",
    "year": 1949,
    "read": true
  }
]
```

> **Gotcha:** `data.json` is resolved relative to the **current working directory**, not the script's location. Always run the app from the `samples/book-app-project/` directory.

---

## Exception Reference

All exceptions inherit from `BookAppError` (defined in `exceptions.py`).

| Exception | Raised when |
|---|---|
| `ValidationError` | Invalid input (empty title/author, bad year) |
| `BookNotFoundError` | Title not found in `mark_as_read` or `remove_book` |
| `StorageError` | `data.json` cannot be read, parsed, or written |

```python
from exceptions import BookNotFoundError, StorageError, ValidationError

try:
    collection.add_book("", "Author", 1984)
except ValidationError as e:
    print(f"Bad input: {e}")

try:
    collection.remove_book("Unknown Title")
except BookNotFoundError as e:
    print(f"Not found: {e}")
```

---

## Internal: `_atomic_write(path)` — Context Manager

Private helper used by `save_books()`. Writes to a temp file in the same directory, then atomically renames it over the target path via `os.replace()`. A failed write never leaves the data file truncated.

```python
# Internal use only — not part of the public API
with _atomic_write("data.json") as f:
    json.dump(data, f)
```
