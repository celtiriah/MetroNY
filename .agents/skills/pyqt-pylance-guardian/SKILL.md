---
name: pyqt-pylance-guardian
description: Enforce zero-error Pylance and Pyright typing rules, scoped enums, and safe type-narrowing patterns for PyQt (PyQt5, PyQt6, PySide) and PyQt-Fluent-Widgets (QFluentWidgets) desktop applications. Use whenever writing, refactoring, or diagnosing PyQt/QFluentWidgets code, fixing Pylance diagnostics (such as reportAttributeAccessIssue, reportOptionalMemberAccess, reportArgumentType), or running the 3-step verification loop.
---

# PyQt & Pylance Guardian Skill

This skill guides the construction, refactoring, and static validation of Python desktop applications built with **PyQt (PyQt5 / PyQt6 / PySide)** and **PyQt-Fluent-Widgets (QFluentWidgets)** to achieve **zero Pylance / Pyright diagnostics**.

---

## Core Problem: Why Pylance Flags PyQt Code

PyQt is a Python binding over native C++ code (via SIP). The Python type stubs (`.pyi` files) used by Pyright/Pylance strictly reflect native C++ semantics:
1. **Optional Return Types (`T | None`)**: Methods like `table.horizontalHeader()`, `table.item(row, col)`, or `table.currentItem()` can return `None` in C++ if uninitialized or out of range. Pylance flags any chained member access as `reportOptionalMemberAccess`.
2. **Modern Scoped Enums**: Modern PyQt stubs deprecate flat enum access. For example, `Qt.AlignRight` triggers `reportAttributeAccessIssue` because the stub defines `Qt.AlignmentFlag.AlignRight`.
3. **C++ Method Overloading**: Overloaded C++ signatures (e.g. `QComboBox.addItem(text)` vs `QComboBox.addItem(icon, text, userData)`) confuse type checkers when positional arguments are passed ambiguously, causing `reportArgumentType`.
4. **Disjoint Type Narrowing**: Pyright type narrowing strictly requires narrowing on the variable itself (`if value is not None:`). Setting or checking an auxiliary flag (e.g., `has_selection = True`) does **not** narrow `table.currentItem()`.

---

## The 6 Mandatory Rules

### Rule 1: Inspect Stubs & Signatures Before Touching Code
- Never assume an enum or method exists on a root class.
- Verify the exact attribute name in the library namespace or inspect with Python:
  ```python
  from PyQt5.QtCore import Qt
  hasattr(Qt.AlignmentFlag, 'AlignRight') # True
  ```

### Rule 2: Strict `T | None` Direct Variable Narrowing
Whenever interacting with Qt widgets that return optional elements, extract into a local variable and guard explicitly with `is not None`:

**Wrong (Chained / Unguarded):**
```python
# reportOptionalMemberAccess
table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
text = table.item(row, col).text()
```

**Wrong (Auxiliary flag narrowing):**
```python
# Pylance does NOT narrow table.item(row, col) through has_item!
has_item = table.item(row, col) is not None
if has_item:
    text = table.item(row, col).text() # ERROR
```

**Correct (Direct narrowing on local variable):**
```python
header = table.horizontalHeader()
if header is not None:
    header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

item = table.item(row, col)
if item is not None:
    text = item.text()
else:
    text = ""
```

---

### Rule 3: Use Scoped Qt Enums Exclusively
Always use the fully scoped enum namespace defined in modern Qt stubs:

| Legacy / Flat Access (Errors) | Modern Scoped Enum (Pylance-Safe) |
| :--- | :--- |
| `Qt.AlignRight`, `Qt.AlignCenter` | `Qt.AlignmentFlag.AlignRight`, `Qt.AlignmentFlag.AlignCenter` |
| `QHeaderView.Stretch`, `QHeaderView.ResizeToContents` | `QHeaderView.ResizeMode.Stretch`, `QHeaderView.ResizeMode.ResizeToContents` |
| `QAbstractItemView.SelectRows` | `QAbstractItemView.SelectionBehavior.SelectRows` |
| `QAbstractItemView.NoEditTriggers` | `QAbstractItemView.EditTrigger.NoEditTriggers` |
| `QTableWidgetItem.ItemIsEnabled` | `Qt.ItemFlag.ItemIsEnabled` |

---

### Rule 4: Disambiguate Overloads with Named Arguments
PyQt C++ bindings feature heavy function overloading. Disambiguate calls by explicitly naming optional keyword arguments:

**Wrong:**
```python
combo.addItem("Línea 1", 101)  # Ambiguous overload resolution
```

**Correct:**
```python
combo.addItem("Línea 1", userData=101)
```

For `userData` retrieval:
```python
data = combo.currentData()
line_id = int(data) if data is not None else None
```

---

### Rule 5: QFluentWidgets Safe Practices
1. **Valid Parent for `MessageBoxBase`**:
   `MessageBoxBase` modal subclasses require a valid `QWidget` parent (typically the main window) for geometry and shadow rendering. Pass `self.window()`:
   ```python
   dialog = CustomDialog(self.window())
   if dialog.exec():
       ...
   ```
2. **Strict FluentIcon (`FIF`) Member Usage**:
   Never invent or hallucinate icon names. Verify against the library's `FluentIcon` enum:
   - Available: `FIF.SYNC`, `FIF.PAUSE`, `FIF.PLAY`, `FIF.CLOSE`, `FIF.CANCEL`, `FIF.SEARCH`, `FIF.ADD`, `FIF.EDIT`, `FIF.DELETE`, `FIF.SETTING`, `FIF.INFO`.
   - Hallucinated: `FIF.POWER` does **not** exist (use `FIF.PAUSE` or `FIF.SYNC` instead).

---

### Rule 6: The 3-Step Verification Loop
Never claim a file is fixed or verified without running this exact 3-step sequence:

#### Step 1: Syntax Validation
Compile the file to bytecode to ensure zero syntax errors:
```bash
python -m py_compile path/to/file.py
```

#### Step 2: Deterministic Pattern Scan
Run the built-in scanner script bundled with this skill:
```bash
python <skill_path>/scripts/check_pyqt_pylance.py path/to/target_or_dir
```
*(Checks for chained header calls, chained `.item().text()`, flat `Qt.Align*`, and hallucinated `FIF.*` symbols).*

#### Step 3: Focused Runtime Smoke Test
Execute a quick non-interactive import or headless execution:
```bash
python -c "import sys; from PyQt5.QtWidgets import QApplication; app = QApplication(sys.argv); from prototypes.desktop.views.my_view import MyView; print('SUCCESS')"
```

---

## Scripts & Tools

This skill bundles a deterministic static analysis tool:
- **`scripts/check_pyqt_pylance.py`**:
  - Scans Python files or entire directories.
  - Verifies syntax with `py_compile`.
  - Runs regex patterns for unguarded headers, table items, unscoped enums, and known hallucinated icons.
  - Compatible with Windows console (handles UTF-8 and codepage 1252 gracefully).

Usage:
```powershell
python C:\Users\1999p\.gemini\config\skills\pyqt-pylance-guardian\scripts\check_pyqt_pylance.py c:\Projects\MetroNY\prototypes\desktop
```
