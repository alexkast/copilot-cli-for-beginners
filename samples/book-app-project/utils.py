import datetime

from books import Book
from exceptions import ValidationError


# --- Pure logic / validation helpers (no I/O) ---

def validate_menu_choice(choice: str) -> None:
    """Validate that a menu choice string is a number between 1 and 5.

    This is a pure function — it performs no I/O. Callers are responsible
    for printing any error messages.

    Args:
        choice (str): The raw string entered by the user.

    Raises:
        ValidationError: If ``choice`` is empty, non-numeric, or outside
            the range 1–5.

    Example:
        >>> validate_menu_choice("3")  # valid, no exception
        >>> validate_menu_choice("")   # raises ValidationError
        >>> validate_menu_choice("9")  # raises ValidationError
    """
    if not choice:
        raise ValidationError("Please enter a choice.")
    if not choice.isdigit() or not 1 <= int(choice) <= 5:
        raise ValidationError(f"Invalid choice '{choice}'. Please enter a number between 1 and 5.")


def parse_year(year_str: str) -> int:
    """Parse a publication year string into an integer.

    This is a pure function — it performs no I/O. An empty string is
    treated as "year unknown" and returns 0. Non-numeric input raises
    a ``ValidationError`` so the caller can decide how to handle it
    (e.g. default to 0 with a warning, or abort).

    Args:
        year_str (str): The raw year string entered by the user.
            Pass an empty string to indicate an unknown year.

    Returns:
        int: The parsed year as an integer, or 0 if ``year_str`` is empty.

    Raises:
        ValidationError: If ``year_str`` is non-empty but cannot be converted
            to an integer, or if the year falls outside the valid range
            (1 to the current year + 1). Year 0 bypasses the range check.

    Example:
        >>> parse_year("1984")
        1984
        >>> parse_year("")
        0
        >>> parse_year("abc")  # raises ValidationError
        >>> parse_year("-1")   # raises ValidationError
    """
    if not year_str:
        return 0
    try:
        year = int(year_str)
    except ValueError:
        raise ValidationError(f"Year must be a number, got '{year_str}'.")
    if year != 0:
        max_year = datetime.date.today().year + 1
        if year < 1 or year > max_year:
            raise ValidationError(
                f"Year must be between 1 and {max_year}, got {year}."
            )
    return year


# --- Display functions (output only, no logic) ---

def print_menu() -> None:
    """Print the interactive main menu to stdout.

    Displays the app title and the numbered list of available actions
    for the interactive menu mode (1–5).

    Example:
        >>> print_menu()
        📚 Book Collection App
        1. Add a book
        ...
    """
    print("\n📚 Book Collection App")
    print("1. Add a book")
    print("2. List books")
    print("3. Mark book as read")
    print("4. Remove a book")
    print("5. Exit")


def print_books(books: list[Book]) -> None:
    """Print a numbered book list with emoji read-status indicators.

    Used by the interactive menu mode. Each entry shows the book number,
    title, author, year, and a ✅/📖 status icon.

    Args:
        books (list[Book]): The list of books to display. If empty, prints
            a "no books" message instead.

    Example:
        >>> print_books([Book("Dune", "Frank Herbert", 1965, read=True)])
        Your Books:
        1. Dune by Frank Herbert (1965) - ✅ Read
    """
    if not books:
        print("No books in your collection.")
        return

    print("\nYour Books:")
    for index, book in enumerate(books, start=1):
        status = "✅ Read" if book.read else "📖 Unread"
        print(f"{index}. {book.title} by {book.author} ({book.year}) - {status}")


def show_books(books: list[Book]) -> None:
    """Print a numbered book list with bracketed read-status markers.

    Used by the CLI command mode (``list``, ``find``, ``search`` commands).
    Each entry shows a ``[✓]`` or ``[ ]`` read marker, title, author, and year.

    Args:
        books (list[Book]): The list of books to display. If empty, prints
            "No books found." and returns.

    Example:
        >>> show_books([Book("1984", "George Orwell", 1949)])
        Your Book Collection:
        1. [ ] 1984 by George Orwell (1949)
    """
    if not books:
        print("No books found.")
        return

    print("\nYour Book Collection:\n")

    for index, book in enumerate(books, start=1):
        status = "✓" if book.read else " "
        print(f"{index}. [{status}] {book.title} by {book.author} ({book.year})")

    print()


# --- Interaction helpers (I/O only; use logic helpers above) ---

def get_user_choice() -> str:
    """Prompt the user to choose a menu option and validate the input.

    Reads a line from stdin, strips whitespace, and validates it using
    ``validate_menu_choice``. If validation fails, the error message is
    printed and an empty string is returned so the caller can re-prompt.

    Returns:
        str: The valid choice string (``"1"``–``"5"``), or ``""`` if the
            input was invalid.

    Example:
        >>> # Assuming the user types "2" at the prompt:
        >>> choice = get_user_choice()
        >>> choice
        '2'
    """
    choice = input("Choose an option (1-5): ").strip()
    try:
        validate_menu_choice(choice)
    except ValidationError as e:
        print(str(e))
        return ""
    return choice


def get_book_details() -> tuple[str, str, int] | None:
    """Prompt the user for book details interactively.

    Prompts for title, author, and publication year in sequence.
    Returns None early if title or author is empty. Raises
    ``ValidationError`` if the year is non-numeric or out of range,
    so the caller can decide how to handle it (e.g. exit with an error
    message).

    Returns:
        A tuple of (title, author, year) on success, where:
            title (str): The book title, non-empty.
            author (str): The author's name, non-empty.
            year (int): The publication year, or 0 if left blank.
        None if title or author is empty.

    Raises:
        ValidationError: If the year input is non-numeric or outside
            the range 1..current_year+1.
    """
    title = input("Enter book title: ").strip()
    if not title:
        print("Error: Title cannot be empty.")
        return None

    author = input("Enter author: ").strip()
    if not author:
        print("Error: Author cannot be empty.")
        return None

    year_str = input("Enter publication year: ").strip()
    year = parse_year(year_str)  # raises ValidationError on bad input

    return title, author, year
