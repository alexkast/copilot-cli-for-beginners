import sys
import os
import datetime
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import books
from books import BookCollection
from book_app import handle_remove, handle_mark_read, handle_add, handle_search
from utils import validate_menu_choice, parse_year
from exceptions import ValidationError, BookNotFoundError, StorageError


@pytest.fixture(autouse=True)
def use_temp_data_file(tmp_path, monkeypatch):
    """Use a temporary data file for each test."""
    temp_file = tmp_path / "data.json"
    temp_file.write_text("[]")
    monkeypatch.setattr(books, "DATA_FILE", str(temp_file))


def test_add_book():
    collection = BookCollection()
    initial_count = len(collection.books)
    collection.add_book("1984", "George Orwell", 1949)
    assert len(collection.books) == initial_count + 1
    book = collection.find_book_by_title("1984")
    assert book is not None
    assert book.author == "George Orwell"
    assert book.year == 1949
    assert book.read is False

def test_mark_book_as_read():
    collection = BookCollection()
    collection.add_book("Dune", "Frank Herbert", 1965)
    collection.mark_as_read("Dune")
    book = collection.find_book_by_title("Dune")
    assert book.read is True

def test_mark_book_as_read_invalid():
    collection = BookCollection()
    with pytest.raises(BookNotFoundError):
        collection.mark_as_read("Nonexistent Book")

def test_remove_book():
    collection = BookCollection()
    collection.add_book("The Hobbit", "J.R.R. Tolkien", 1937)
    collection.remove_book("The Hobbit")
    book = collection.find_book_by_title("The Hobbit")
    assert book is None

def test_remove_book_invalid():
    collection = BookCollection()
    with pytest.raises(BookNotFoundError):
        collection.remove_book("Nonexistent Book")


# Handler-level tests

def test_handle_remove_success(monkeypatch, capsys):
    collection = BookCollection()
    collection.add_book("Dune", "Frank Herbert", 1965)
    monkeypatch.setattr("builtins.input", lambda _: "Dune")
    handle_remove(collection)
    out = capsys.readouterr().out
    assert "removed successfully" in out
    assert collection.find_book_by_title("Dune") is None

def test_handle_remove_not_found(monkeypatch, capsys):
    collection = BookCollection()
    monkeypatch.setattr("builtins.input", lambda _: "Unknown Book")
    with pytest.raises(SystemExit):
        handle_remove(collection)
    out = capsys.readouterr().out
    assert "not found" in out

def test_handle_mark_read_success(monkeypatch, capsys):
    collection = BookCollection()
    collection.add_book("1984", "George Orwell", 1949)
    monkeypatch.setattr("builtins.input", lambda _: "1984")
    handle_mark_read(collection)
    out = capsys.readouterr().out
    assert "marked as read" in out
    assert collection.find_book_by_title("1984").read is True

def test_handle_mark_read_not_found(monkeypatch, capsys):
    collection = BookCollection()
    monkeypatch.setattr("builtins.input", lambda _: "Unknown Book")
    with pytest.raises(SystemExit):
        handle_mark_read(collection)
    out = capsys.readouterr().out
    assert "not found" in out

def test_handle_add_empty_title(monkeypatch, capsys):
    collection = BookCollection()
    inputs = iter(["", "Some Author"])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))
    with pytest.raises(SystemExit):
        handle_add(collection)
    out = capsys.readouterr().out
    assert "cannot be empty" in out


# Search tests

def test_search_by_title():
    collection = BookCollection()
    collection.add_book("1984", "George Orwell", 1949)
    collection.add_book("Dune", "Frank Herbert", 1965)
    results = collection.search("1984")
    assert len(results) == 1
    assert results[0].title == "1984"

def test_search_by_author():
    collection = BookCollection()
    collection.add_book("1984", "George Orwell", 1949)
    collection.add_book("Animal Farm", "George Orwell", 1945)
    collection.add_book("Dune", "Frank Herbert", 1965)
    results = collection.search("Orwell")
    assert len(results) == 2

def test_search_partial_match():
    collection = BookCollection()
    collection.add_book("The Hobbit", "J.R.R. Tolkien", 1937)
    collection.add_book("The Lord of the Rings", "J.R.R. Tolkien", 1954)
    results = collection.search("hobbit")
    assert len(results) == 1
    assert results[0].title == "The Hobbit"

def test_search_case_insensitive():
    collection = BookCollection()
    collection.add_book("1984", "George Orwell", 1949)
    assert len(collection.search("GEORGE")) == 1
    assert len(collection.search("orwell")) == 1
    assert len(collection.search("1984")) == 1

def test_search_no_results():
    collection = BookCollection()
    collection.add_book("1984", "George Orwell", 1949)
    results = collection.search("tolkien")
    assert results == []

def test_handle_search_shows_results(monkeypatch, capsys):
    collection = BookCollection()
    collection.add_book("1984", "George Orwell", 1949)
    monkeypatch.setattr("builtins.input", lambda _: "orwell")
    handle_search(collection)
    out = capsys.readouterr().out
    assert "1984" in out

def test_handle_search_no_results(monkeypatch, capsys):
    collection = BookCollection()
    collection.add_book("1984", "George Orwell", 1949)
    monkeypatch.setattr("builtins.input", lambda _: "tolkien")
    handle_search(collection)
    out = capsys.readouterr().out
    assert "No books found" in out


# validate_menu_choice tests

def test_validate_menu_choice_valid():
    assert validate_menu_choice("1") is None
    assert validate_menu_choice("5") is None
    assert validate_menu_choice("3") is None

def test_validate_menu_choice_empty():
    with pytest.raises(ValidationError, match="enter a choice"):
        validate_menu_choice("")

def test_validate_menu_choice_non_numeric():
    with pytest.raises(ValidationError):
        validate_menu_choice("abc")

def test_validate_menu_choice_out_of_range():
    with pytest.raises(ValidationError):
        validate_menu_choice("0")
    with pytest.raises(ValidationError):
        validate_menu_choice("6")


# ── BookCollection: load_books edge cases ─────────────────────────────────────

def test_load_books_missing_file(tmp_path, monkeypatch):
    """Missing data file → empty collection, no exception."""
    monkeypatch.setattr(books, "DATA_FILE", str(tmp_path / "nonexistent.json"))
    collection = BookCollection()
    assert collection.books == []

def test_load_books_invalid_json(tmp_path, monkeypatch):
    """File with invalid JSON → StorageError."""
    data_file = tmp_path / "data.json"
    data_file.write_text("not valid json {{{")
    monkeypatch.setattr(books, "DATA_FILE", str(data_file))
    with pytest.raises(StorageError, match="invalid JSON"):
        BookCollection()

def test_load_books_not_array(tmp_path, monkeypatch):
    """JSON that is not an array → StorageError."""
    data_file = tmp_path / "data.json"
    data_file.write_text('{"title": "1984"}')
    monkeypatch.setattr(books, "DATA_FILE", str(data_file))
    with pytest.raises(StorageError, match="JSON array"):
        BookCollection()

def test_load_books_invalid_records(tmp_path, monkeypatch):
    """Array with records missing required Book fields → StorageError."""
    data_file = tmp_path / "data.json"
    data_file.write_text('[{"bad_field": "value"}]')
    monkeypatch.setattr(books, "DATA_FILE", str(data_file))
    with pytest.raises(StorageError, match="invalid book records"):
        BookCollection()


# ── BookCollection: persistence ───────────────────────────────────────────────

def test_data_persists_across_instances():
    """Books added in one instance are available when reloading from disk."""
    c1 = BookCollection()
    c1.add_book("Dune", "Frank Herbert", 1965)
    c2 = BookCollection()
    book = c2.find_book_by_title("Dune")
    assert book is not None
    assert book.author == "Frank Herbert"
    assert book.year == 1965

def test_read_flag_persists():
    """mark_as_read change persists across a reload."""
    c1 = BookCollection()
    c1.add_book("1984", "George Orwell", 1949)
    c1.mark_as_read("1984")
    c2 = BookCollection()
    assert c2.find_book_by_title("1984").read is True

def test_remove_persists():
    """remove_book change persists across a reload."""
    c1 = BookCollection()
    c1.add_book("1984", "George Orwell", 1949)
    c1.remove_book("1984")
    c2 = BookCollection()
    assert c2.find_book_by_title("1984") is None


# ── BookCollection: add_book validation ───────────────────────────────────────

def test_add_book_empty_title():
    collection = BookCollection()
    with pytest.raises(ValidationError, match="Title"):
        collection.add_book("", "Frank Herbert", 1965)

def test_add_book_empty_author():
    collection = BookCollection()
    with pytest.raises(ValidationError, match="Author"):
        collection.add_book("Dune", "", 1965)

def test_add_book_whitespace_only_title():
    collection = BookCollection()
    with pytest.raises(ValidationError, match="Title"):
        collection.add_book("   ", "Frank Herbert", 1965)

def test_add_book_returns_book_instance():
    collection = BookCollection()
    book = collection.add_book("Dune", "Frank Herbert", 1965)
    assert book.title == "Dune"
    assert book.author == "Frank Herbert"
    assert book.year == 1965
    assert book.read is False


# ── BookCollection: list_books / find_book_by_title ───────────────────────────

def test_list_books_empty():
    collection = BookCollection()
    assert collection.list_books() == []

def test_list_books_insertion_order():
    collection = BookCollection()
    collection.add_book("1984", "George Orwell", 1949)
    collection.add_book("Dune", "Frank Herbert", 1965)
    result = collection.list_books()
    assert result[0].title == "1984"
    assert result[1].title == "Dune"

def test_find_book_by_title_case_insensitive():
    collection = BookCollection()
    collection.add_book("Dune", "Frank Herbert", 1965)
    assert collection.find_book_by_title("DUNE") is not None
    assert collection.find_book_by_title("dune") is not None

def test_find_book_by_title_not_found():
    collection = BookCollection()
    assert collection.find_book_by_title("Unknown Title") is None


# ── BookCollection: find_by_author ────────────────────────────────────────────

def test_find_by_author_basic():
    collection = BookCollection()
    collection.add_book("1984", "George Orwell", 1949)
    collection.add_book("Animal Farm", "George Orwell", 1945)
    collection.add_book("Dune", "Frank Herbert", 1965)
    assert len(collection.find_by_author("George Orwell")) == 2

def test_find_by_author_case_insensitive():
    collection = BookCollection()
    collection.add_book("1984", "George Orwell", 1949)
    assert len(collection.find_by_author("george orwell")) == 1
    assert len(collection.find_by_author("GEORGE ORWELL")) == 1

def test_find_by_author_no_results():
    collection = BookCollection()
    collection.add_book("1984", "George Orwell", 1949)
    assert collection.find_by_author("Frank Herbert") == []


# ── Year validation: parse_year ───────────────────────────────────────────────

def test_parse_year_valid():
    assert parse_year("1984") == 1984

def test_parse_year_empty_returns_zero():
    assert parse_year("") == 0

def test_parse_year_zero_is_valid():
    assert parse_year("0") == 0

def test_parse_year_current_year_valid():
    current_year = datetime.date.today().year
    assert parse_year(str(current_year)) == current_year

def test_parse_year_next_year_valid():
    next_year = datetime.date.today().year + 1
    assert parse_year(str(next_year)) == next_year

def test_parse_year_year_after_next_invalid():
    too_far = datetime.date.today().year + 2
    with pytest.raises(ValidationError, match="between 1"):
        parse_year(str(too_far))

def test_parse_year_negative_invalid():
    with pytest.raises(ValidationError, match="between 1"):
        parse_year("-1")

def test_parse_year_very_large_invalid():
    with pytest.raises(ValidationError, match="between 1"):
        parse_year("99999")

def test_parse_year_non_numeric():
    with pytest.raises(ValidationError, match="must be a number"):
        parse_year("abc")


# ── Year validation: add_book ─────────────────────────────────────────────────

def test_add_book_year_zero_allowed():
    """Year 0 (unknown) is always accepted."""
    collection = BookCollection()
    book = collection.add_book("Unknown Year Book", "Author", 0)
    assert book.year == 0

def test_add_book_year_one_allowed():
    """Year 1 is the minimum accepted non-zero year."""
    collection = BookCollection()
    book = collection.add_book("Ancient Text", "Author", 1)
    assert book.year == 1

def test_add_book_year_current_year_valid():
    current_year = datetime.date.today().year
    collection = BookCollection()
    book = collection.add_book("Recent Book", "Author", current_year)
    assert book.year == current_year

def test_add_book_year_next_year_valid():
    next_year = datetime.date.today().year + 1
    collection = BookCollection()
    book = collection.add_book("Upcoming Book", "Author", next_year)
    assert book.year == next_year

def test_add_book_year_too_far_future_invalid():
    too_far = datetime.date.today().year + 2
    collection = BookCollection()
    with pytest.raises(ValidationError, match="between 1"):
        collection.add_book("Far Future", "Author", too_far)

def test_add_book_year_negative_invalid():
    collection = BookCollection()
    with pytest.raises(ValidationError, match="between 1"):
        collection.add_book("BC Book", "Author", -500)


# ── BookCollection: get_unread_books ─────────────────────────────────────────

def test_get_unread_books_empty_collection():
    """Empty collection → returns empty list."""
    collection = BookCollection()
    assert collection.get_unread_books() == []

def test_get_unread_books_all_unread():
    """All books unread → returns all books."""
    collection = BookCollection()
    collection.add_book("Dune", "Frank Herbert", 1965)
    collection.add_book("1984", "George Orwell", 1949)
    assert len(collection.get_unread_books()) == 2

def test_get_unread_books_all_read_returns_empty():
    """All books marked read → returns empty list."""
    collection = BookCollection()
    collection.add_book("Dune", "Frank Herbert", 1965)
    collection.add_book("1984", "George Orwell", 1949)
    collection.mark_as_read("Dune")
    collection.mark_as_read("1984")
    assert collection.get_unread_books() == []

def test_get_unread_books_filters_read_books():
    """Mixed collection → only unread books returned."""
    collection = BookCollection()
    collection.add_book("Dune", "Frank Herbert", 1965)
    collection.add_book("1984", "George Orwell", 1949)
    collection.add_book("The Hobbit", "J.R.R. Tolkien", 1937)
    collection.mark_as_read("1984")
    unread = collection.get_unread_books()
    titles = [b.title for b in unread]
    assert "1984" not in titles

def test_get_unread_books_filters_read_books_count():
    """Mixed collection → correct count of unread books."""
    collection = BookCollection()
    collection.add_book("Dune", "Frank Herbert", 1965)
    collection.add_book("1984", "George Orwell", 1949)
    collection.add_book("The Hobbit", "J.R.R. Tolkien", 1937)
    collection.mark_as_read("1984")
    assert len(collection.get_unread_books()) == 2

def test_get_unread_books_single_unread():
    """Single unread book → returned in list."""
    collection = BookCollection()
    collection.add_book("Dune", "Frank Herbert", 1965)
    unread = collection.get_unread_books()
    assert len(unread) == 1
    assert unread[0].title == "Dune"

def test_get_unread_books_excludes_read_book():
    """Single book marked read → not in unread results."""
    collection = BookCollection()
    collection.add_book("1984", "George Orwell", 1949)
    collection.mark_as_read("1984")
    assert collection.get_unread_books() == []

def test_get_unread_books_preserves_insertion_order():
    """Unread books returned in insertion order."""
    collection = BookCollection()
    collection.add_book("Dune", "Frank Herbert", 1965)
    collection.add_book("1984", "George Orwell", 1949)
    collection.add_book("The Hobbit", "J.R.R. Tolkien", 1937)
    collection.mark_as_read("1984")
    unread = collection.get_unread_books()
    assert unread[0].title == "Dune"
    assert unread[1].title == "The Hobbit"

def test_get_unread_books_reflects_mark_as_read():
    """After mark_as_read, count drops by one."""
    collection = BookCollection()
    collection.add_book("Dune", "Frank Herbert", 1965)
    collection.add_book("1984", "George Orwell", 1949)
    assert len(collection.get_unread_books()) == 2
    collection.mark_as_read("Dune")
    assert len(collection.get_unread_books()) == 1

def test_get_unread_books_returns_new_list():
    """Returned list is a copy — mutating it doesn't affect the collection."""
    collection = BookCollection()
    collection.add_book("Dune", "Frank Herbert", 1965)
    unread = collection.get_unread_books()
    unread.clear()
    assert len(collection.get_unread_books()) == 1
