import datetime
import json
import os
import tempfile
from contextlib import contextmanager
from dataclasses import dataclass, asdict
from typing import Generator, IO, List, Optional
from exceptions import ValidationError, BookNotFoundError, StorageError

DATA_FILE = "data.json"


@contextmanager
def _atomic_write(path: str) -> Generator[IO[str], None, None]:
    """Context manager for atomic file writes.

    Yields a writable file handle pointed at a temporary file in the same
    directory as ``path``. On clean exit, the temp file is renamed over
    ``path`` atomically via ``os.replace()``. On any ``OSError``, the temp
    file is cleaned up and a ``StorageError`` is raised.

    Args:
        path (str): The destination file path.

    Yields:
        IO[str]: A writable text-mode file handle.

    Raises:
        StorageError: If the temp file cannot be created or renamed (``OSError``).
            Non-I/O exceptions (e.g. serialisation errors from ``json.dump``)
            propagate unwrapped after temp file cleanup.

    Example:
        >>> with _atomic_write("data.json") as f:
        ...     json.dump(data, f)
    """
    data_dir = os.path.dirname(os.path.abspath(path))
    tmp_path = None
    try:
        tmp_fd, tmp_path = tempfile.mkstemp(dir=data_dir, suffix=".tmp")
        with os.fdopen(tmp_fd, "w") as f:
            yield f
        os.replace(tmp_path, path)
    except BaseException as e:
        if tmp_path is not None:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
        if isinstance(e, OSError):
            raise StorageError(f"Could not save to '{path}': {e}") from e
        raise


@dataclass
class Book:
    """A single book entry in the collection.

    Attributes:
        title (str): The book's title. Should be non-empty; use ``add_book()`` to enforce this.
        author (str): The author's full name. Should be non-empty; use ``add_book()`` to enforce this.
        year (int): Publication year; use 0 if unknown.
        read (bool): Whether the book has been marked as read. Defaults to False.

    Example:
        >>> book = Book(title="Dune", author="Frank Herbert", year=1965)
        >>> book.read
        False
        >>> book.year
        1965
    """
    title: str
    author: str
    year: int
    read: bool = False


class BookCollection:
    """Manages a persistent collection of books backed by a JSON file.

    All mutating operations (add, remove, mark as read) save the collection
    to disk immediately so no changes are lost between runs.

    Example:
        >>> collection = BookCollection()
        >>> book = collection.add_book("1984", "George Orwell", 1949)
        >>> len(collection.list_books())
        1
    """

    def __init__(self) -> None:
        """Initialize an empty collection and load any saved books from disk.

        Raises:
            StorageError: If the data file exists but cannot be read or is corrupt.

        Example:
            >>> collection = BookCollection()
            >>> isinstance(collection.books, list)
            True
        """
        self.books: List[Book] = []
        self.load_books()

    def load_books(self) -> None:
        """Load books from the JSON data file into ``self.books``.

        If the file does not exist, the collection starts empty (expected
        on first run). Any other read or parse failure raises ``StorageError``
        so the caller can decide how to handle corrupt data.

        Raises:
            StorageError: If the file cannot be opened (permissions, disk error),
                contains invalid JSON, is not a top-level array, or contains
                records that do not match the ``Book`` dataclass fields.

        Example:
            >>> collection = BookCollection()  # loads from DATA_FILE if present
            >>> isinstance(collection.books, list)
            True
        """
        try:
            with open(DATA_FILE, "r") as f:
                data = json.load(f)
        except FileNotFoundError:
            self.books = []
            return
        except OSError as e:
            raise StorageError(f"Could not read data file: {e}") from e
        except json.JSONDecodeError as e:
            raise StorageError(f"data.json is corrupt (invalid JSON): {e}") from e

        if not isinstance(data, list):
            raise StorageError("data.json is corrupt: expected a JSON array at the top level.")

        try:
            self.books = [Book(**b) for b in data]
        except (TypeError, KeyError) as e:
            raise StorageError(f"data.json contains invalid book records: {e}") from e

    def save_books(self) -> None:
        """Persist the current collection to the JSON data file atomically.

        Uses the ``_atomic_write`` context manager to write to a temporary
        file first, then rename it over the target — so a failed write never
        leaves the data file truncated or corrupt.

        Raises:
            StorageError: If the file cannot be written (e.g. permission denied,
                disk full).

        Example:
            >>> collection = BookCollection()
            >>> collection.add_book("Dune", "Frank Herbert", 1965)  # calls save_books internally
            Book(title='Dune', author='Frank Herbert', year=1965, read=False)
        """
        with _atomic_write(DATA_FILE) as f:
            json.dump([asdict(b) for b in self.books], f, indent=2)

    def add_book(self, title: str, author: str, year: int) -> Book:
        """Add a new book to the collection and save it to disk.

        Args:
            title (str): The book's title. Must be non-empty after stripping whitespace.
            author (str): The author's name. Must be non-empty after stripping whitespace.
            year (int): Publication year. Pass 0 if unknown. Otherwise must be
                between 1 and the current calendar year + 1 (to allow upcoming books).

        Returns:
            Book: The newly created ``Book`` instance that was added.

        Raises:
            ValidationError: If ``title`` or ``author`` is empty or whitespace-only,
                or if ``year`` is non-zero and outside the range 1..current_year+1.
            StorageError: If the updated collection cannot be saved to disk.

        Example:
            >>> collection = BookCollection()
            >>> book = collection.add_book("1984", "George Orwell", 1949)
            >>> book.title
            '1984'
            >>> book.read
            False
        """
        if not title or not title.strip():
            raise ValidationError("Title cannot be empty.")
        if not author or not author.strip():
            raise ValidationError("Author cannot be empty.")
        if year != 0:
            max_year = datetime.date.today().year + 1
            if year < 1 or year > max_year:
                raise ValidationError(
                    f"Year must be between 1 and {max_year}, got {year}."
                )
        book = Book(title=title, author=author, year=year)
        self.books.append(book)
        self.save_books()
        return book

    def list_books(self) -> List[Book]:
        """Return all books in the collection.

        Returns:
            list[Book]: A list of all ``Book`` objects, in insertion order.
                Returns an empty list if the collection is empty.

        Example:
            >>> collection = BookCollection()
            >>> _ = collection.add_book("Dune", "Frank Herbert", 1965)
            >>> len(collection.list_books())
            1
        """
        return self.books

    def find_book_by_title(self, title: str) -> Optional[Book]:
        """Find a book by its exact title (case-insensitive).

        Args:
            title (str): The title to search for. Matching is case-insensitive.

        Returns:
            Optional[Book]: The matching ``Book`` if found, or ``None`` if no
                book with that title exists.

        Example:
            >>> collection = BookCollection()
            >>> _ = collection.add_book("Dune", "Frank Herbert", 1965)
            >>> collection.find_book_by_title("dune").author
            'Frank Herbert'
            >>> collection.find_book_by_title("Unknown") is None
            True
        """
        for book in self.books:
            if book.title.lower() == title.lower():
                return book
        return None

    def mark_as_read(self, title: str) -> None:
        """Mark a book as read and save the change to disk.

        Args:
            title (str): The title of the book to mark. Matching is case-insensitive.

        Raises:
            BookNotFoundError: If no book with the given title exists in the collection.
            StorageError: If the updated collection cannot be saved to disk.

        Example:
            >>> collection = BookCollection()
            >>> _ = collection.add_book("Dune", "Frank Herbert", 1965)
            >>> collection.mark_as_read("Dune")
            >>> collection.find_book_by_title("Dune").read
            True
        """
        book = self.find_book_by_title(title)
        if not book:
            raise BookNotFoundError(f"Book '{title}' not found.")
        book.read = True
        self.save_books()

    def remove_book(self, title: str) -> None:
        """Remove a book from the collection and save the change to disk.

        Args:
            title (str): The title of the book to remove. Matching is case-insensitive.

        Raises:
            BookNotFoundError: If no book with the given title exists in the collection.
            StorageError: If the updated collection cannot be saved to disk.

        Example:
            >>> collection = BookCollection()
            >>> _ = collection.add_book("Dune", "Frank Herbert", 1965)
            >>> collection.remove_book("Dune")
            >>> collection.find_book_by_title("Dune") is None
            True
        """
        book = self.find_book_by_title(title)
        if not book:
            raise BookNotFoundError(f"Book '{title}' not found.")
        self.books.remove(book)
        self.save_books()

    def get_unread_books(self) -> list[Book]:
        """Return all books that have not been marked as read.

        Returns:
            list[Book]: All ``Book`` objects where ``read`` is ``False``,
                in insertion order. Returns an empty list if all books
                are read or the collection is empty.

        Example:
            >>> collection = BookCollection()
            >>> _ = collection.add_book("Dune", "Frank Herbert", 1965)
            >>> _ = collection.add_book("1984", "George Orwell", 1949)
            >>> collection.mark_as_read("1984")
            >>> unread = collection.get_unread_books()
            >>> len(unread)
            1
            >>> unread[0].title
            'Dune'
        """
        return [b for b in self.books if not b.read]

    def find_by_author(self, author: str) -> List[Book]:
        """Find all books by a given author (case-insensitive exact match).

        Args:
            author (str): The author name to search for. Matching is case-insensitive
                but must match the full author field exactly.

        Returns:
            list[Book]: All books whose author matches. Returns an empty list
                if no books are found.

        Example:
            >>> collection = BookCollection()
            >>> _ = collection.add_book("1984", "George Orwell", 1949)
            >>> _ = collection.add_book("Animal Farm", "George Orwell", 1945)
            >>> len(collection.find_by_author("george orwell"))
            2
        """
        return [b for b in self.books if b.author.lower() == author.lower()]

    def search(self, query: str) -> List[Book]:
        """Search for books whose title or author contains the query string.

        The search is case-insensitive and matches partial substrings in either
        the title or the author field.

        Args:
            query (str): The search term. Matched as a substring against both
                ``title`` and ``author`` fields, case-insensitively.

        Returns:
            list[Book]: All books that contain the query in their title or author.
                Returns an empty list if no books match.

        Example:
            >>> collection = BookCollection()
            >>> _ = collection.add_book("The Hobbit", "J.R.R. Tolkien", 1937)
            >>> _ = collection.add_book("1984", "George Orwell", 1949)
            >>> len(collection.search("tolkien"))
            1
            >>> len(collection.search("the"))  # matches "The Hobbit"
            1
        """
        q = query.lower()
        return [b for b in self.books if q in b.title.lower() or q in b.author.lower()]
