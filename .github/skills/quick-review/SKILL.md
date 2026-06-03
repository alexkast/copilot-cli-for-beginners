---
name: quick-review
description: Fast 3-point Python code review - checks for bare except clauses, missing type hints, and unclear variable names
---

# Quick Review Skill

Perform a fast focused review of Python code checking exactly three things.

## Checklist

### 1. Bare Except Clauses
Scan for any `except:` or `except Exception:` without a re-raise.
These silently swallow errors and hide bugs.

Flag:
```python
except:          # bare — always flag
except Exception: pass  # silent swallow — always flag
```

Do NOT flag:
```python
except OSError as e:          # specific — OK
except (TypeError, KeyError): # specific tuple — OK
except BaseException as e: ... raise  # re-raises — OK
```

### 2. Missing Type Hints
Check every function and method signature.
Flag any parameter or return value without a type annotation.

Flag:
```python
def add_book(self, title, author, year):   # no hints
def load():                                 # no return hint
```

Do NOT flag:
```python
def add_book(self, title: str, author: str, year: int) -> Book:  # fully annotated
```

### 3. Unclear Variable Names
Flag single-letter names (except `i`, `j`, `k` in loops and `f` for file handles), abbreviations that need decoding, and names that don't describe what they hold.

Flag:
```python
x = collection.list_books()   # what is x?
d = json.load(f)              # d = data? dict?
tmp = title.strip()           # tmp tells nothing
```

Do NOT flag:
```python
books = collection.list_books()
data = json.load(f)
q = query.lower()             # acceptable single-letter for local query shorthand
```

## Output Format

```
## Quick Review: [filename]

### 1. Bare Except Clauses
- [PASS/FAIL] line X — description

### 2. Missing Type Hints
- [PASS/FAIL] function_name() — description

### 3. Unclear Variable Names
- [PASS/FAIL] line X — description

### Result: X issue(s) found
```

Use `[PASS]` when the file is clean on that check. List every individual finding — don't summarise multiple issues into one line.
