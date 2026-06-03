import sys
from books import Book, BookCollection
from exceptions import BookNotFoundError, StorageError, ValidationError
from utils import show_books


def handle_list(collection: BookCollection) -> None:
    """Display all books in the collection.

    Args:
        collection (BookCollection): The loaded book collection to display.

    Example:
        >>> handle_list(collection)  # prints all books, or "No books found."
    """
    books = collection.list_books()
    show_books(books)


def handle_add(collection: BookCollection) -> None:
    """Prompt the user for book details and add the book to the collection.

    Reads title, author, and year interactively from stdin. Exits with
    code 1 if any required field is empty, if year is not a number, or
    if the book cannot be saved.

    Args:
        collection (BookCollection): The loaded book collection to add to.

    Raises:
        SystemExit: With code 1 on validation failure or storage error.

    Example:
        >>> # Run: python book_app.py add
        >>> # Prompts: Title, Author, Year
    """
    print("\nAdd a New Book\n")

    title = input("Title: ").strip()
    if not title:
        print("\nError: Title cannot be empty.\n")
        sys.exit(1)

    author = input("Author: ").strip()
    if not author:
        print("\nError: Author cannot be empty.\n")
        sys.exit(1)

    year_str = input("Year: ").strip()

    try:
        year = int(year_str) if year_str else 0
    except ValueError:
        print("\nError: Year must be a number.\n")
        sys.exit(1)

    try:
        collection.add_book(title, author, year)
        print("\nBook added successfully.\n")
    except ValidationError as e:
        print(f"\nError: {e}\n")
        sys.exit(1)
    except StorageError as e:
        print(f"\nError: Could not save book ({e}).\n")
        sys.exit(1)


def handle_remove(collection: BookCollection) -> None:
    """Prompt for a book title and remove it from the collection.

    Matching is case-insensitive. Exits with code 1 if the title is
    empty, the book is not found, or the collection cannot be saved.

    Args:
        collection (BookCollection): The loaded book collection to remove from.

    Raises:
        SystemExit: With code 1 if the title is empty, not found, or on storage error.

    Example:
        >>> # Run: python book_app.py remove
        >>> # Prompts: title to remove
    """
    print("\nRemove a Book\n")

    title = input("Enter the title of the book to remove: ").strip()
    if not title:
        print("\nError: Title cannot be empty.\n")
        sys.exit(1)

    try:
        collection.remove_book(title)
        print(f"\n'{title}' removed successfully.\n")
    except BookNotFoundError:
        print(f"\nBook '{title}' not found.\n")
        sys.exit(1)
    except StorageError as e:
        print(f"\nError: Could not save changes ({e}).\n")
        sys.exit(1)


def handle_mark_read(collection: BookCollection) -> None:
    """Prompt for a book title and mark it as read.

    Matching is case-insensitive. Exits with code 1 if the title is
    empty, the book is not found, or the collection cannot be saved.

    Args:
        collection (BookCollection): The loaded book collection to update.

    Raises:
        SystemExit: With code 1 if the title is empty, not found, or on storage error.

    Example:
        >>> # Run: python book_app.py mark
        >>> # Prompts: title to mark as read
    """
    print("\nMark a Book as Read\n")

    title = input("Enter the title of the book to mark as read: ").strip()
    if not title:
        print("\nError: Title cannot be empty.\n")
        sys.exit(1)

    try:
        collection.mark_as_read(title)
        print(f"\n'{title}' marked as read.\n")
    except BookNotFoundError:
        print(f"\nBook '{title}' not found.\n")
        sys.exit(1)
    except StorageError as e:
        print(f"\nError: Could not save changes ({e}).\n")
        sys.exit(1)


def handle_list_unread(collection: BookCollection) -> None:
    """Display all books that have not been marked as read.

    Args:
        collection (BookCollection): The loaded book collection to filter.

    Example:
        >>> handle_list_unread(collection)  # prints unread books, or "No books found."
    """
    books = collection.get_unread_books()
    show_books(books)


def handle_find(collection: BookCollection) -> None:
    """Prompt for an author name and display all their books.

    Performs a case-insensitive exact match on the author field. Exits
    with code 1 if the author name is empty.

    Args:
        collection (BookCollection): The loaded book collection to search.

    Raises:
        SystemExit: With code 1 if the author name is empty.

    Example:
        >>> # Run: python book_app.py find
        >>> # Prompts: author name
        >>> # Prints all books by that author, or "No books found."
    """
    print("\nFind Books by Author\n")

    author = input("Author name: ").strip()
    if not author:
        print("\nError: Author name cannot be empty.\n")
        sys.exit(1)

    books = collection.find_by_author(author)
    show_books(books)


def handle_search(collection: BookCollection) -> None:
    """Prompt for a search query and display matching books.

    Searches both the title and author fields using a case-insensitive
    substring match. Exits with code 1 if the query is empty.

    Args:
        collection (BookCollection): The loaded book collection to search.

    Raises:
        SystemExit: With code 1 if the query is empty.

    Example:
        >>> # Run: python book_app.py search
        >>> # Prompts: search query
        >>> # "orwell" matches books by George Orwell; "1984" matches by title
    """
    print("\nSearch Books\n")

    query = input("Search by title or author: ").strip()
    if not query:
        print("\nError: Search query cannot be empty.\n")
        sys.exit(1)

    books = collection.search(query)
    show_books(books)


def show_help() -> None:
    """Print the CLI help text listing all available commands.

    Example:
        >>> show_help()
        Book Collection Helper
        Commands:
          list     - Show all books
          ...
    """
    print("""
Book Collection Helper

Commands:
  list     - Show all books
  unread   - Show only unread books
  add      - Add a new book
  remove   - Remove a book by title
  mark     - Mark a book as read
  find     - Find books by author
  search   - Search books by title or author
  help     - Show this help message
""")


COMMANDS: dict = {
    "list": handle_list,
    "unread": handle_list_unread,
    "add": handle_add,
    "remove": handle_remove,
    "mark": handle_mark_read,
    "find": handle_find,
    "search": handle_search,
}


def main() -> None:
    """Entry point for the Book Collection CLI.

    Reads the command from ``sys.argv[1]``, loads the book collection,
    and dispatches to the appropriate handler via the ``COMMANDS`` registry.
    Prints help and exits cleanly if no command is given.

    Raises:
        SystemExit: With code 1 if the command is unknown or if loading
            the collection fails.

    Example:
        >>> # python book_app.py list
        >>> # python book_app.py add
        >>> # python book_app.py help
    """
    if len(sys.argv) < 2:
        show_help()
        return

    command = sys.argv[1].lower()

    if command == "help":
        show_help()
        return

    if command not in COMMANDS:
        print("Unknown command.\n")
        show_help()
        sys.exit(1)

    try:
        collection = BookCollection()
    except StorageError as e:
        print(f"\nError: Could not load book collection ({e}).\n")
        sys.exit(1)

    COMMANDS[command](collection)


if __name__ == "__main__":
    main()
