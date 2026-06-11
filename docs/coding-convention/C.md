# C Coding Convention

> **[Optional add-on]** Adopt only in firmware/native-interface projects. SW-only projects may ignore it.
> For the firmware target protocol, see [docs/coding-target/firmwareCodingProtocol.md](../coding-target/firmwareCodingProtocol.md).
>
> Reference standards: MISRA C:2025 / Linux Kernel Coding Style / NASA JPL Power of 10
> The canonical source for language-agnostic quality principles is [.clauderules](../../.clauderules).

---

## 1. Naming Conventions

| Target | Rule | Example |
|------|------|------|
| Variable | `snake_case` | `user_count`, `total_size` |
| Function | `snake_case` | `calculate_total()`, `get_user_id()` |
| Constant | `UPPER_SNAKE_CASE` | `MAX_SIZE`, `DEFAULT_TIMEOUT` |
| Macro | `UPPER_SNAKE_CASE` | `#define MAX_BUF_SIZE 256` |
| Struct / type | `snake_case_t` | `user_data_t`, `config_t` |
| Enum | `UPPER_SNAKE_CASE` | `STATUS_OK`, `STATUS_ERROR` |

- Minimize abbreviations; reflect domain terms clearly
- Single-character variables are allowed only for loop counters (`i`, `j`, `k`)

### Function Naming Rules

Write function names as **verb + object** to clearly express the action performed.

| Pattern | Use | Example |
|------|------|------|
| `get_` | Read a value (no side effects) | `get_user_name()`, `get_count()` |
| `set_` | Set a value | `set_timeout()`, `set_config()` |
| `init_` | Initialize | `init_module()`, `init_buffer()` |
| `create_` | Dynamic creation (includes memory allocation) | `create_session()` |
| `destroy_` | Free | `destroy_session()` |
| `is_` / `has_` | Return a boolean | `is_valid()`, `has_permission()` |
| `calculate_` / `compute_` | Compute | `calculate_checksum()` |
| `parse_` | Parse/convert | `parse_config()` |
| `handle_` | Handle an event/error | `handle_error()` |

```c
/* Examples of correct function names */
user_t    *create_user(const char *p_sName);
void       destroy_user(user_t *p_objUser);
bool       is_user_active(const user_t *p_objUser);
int        calculate_total_price(const int *p_arrPrices, int p_vCount);
```

---

## 2. Hybrid Naming Convention (Required)

Combine a variable's **origin (Scope)** and **data type (Type)** as a prefix so the name alone reveals both at a glance.

- **Format**: `[Scope]_[Type][Name]`
- **Scope**: `g_` (Global), `m_` (Member/Struct field), `p_` (Parameter); Local is omitted
- **Type**: `v` (Number/int/float), `s` (String/char*), `b` (Boolean/flag), `arr` (Array), `obj` (Struct pointer), `fn` (Function pointer)

| Example | Description |
|------|------|
| `g_vTotalCount` | Global numeric variable |
| `m_sUserName` | Struct member string |
| `p_objConfig` | Struct pointer passed as a parameter |
| `vLocalIdx` | Local numeric variable |
| `fnCalculate` | Function pointer |

```c
typedef struct {
    char  m_sName[32];
    int   m_vAge;
    bool  m_bIsActive;
} user_t;

int g_vUserCount = 0;

int process_user(user_t *p_objUser, int p_vLimit) {
    int vResult = 0;
    /* ... */
    return vResult;
}
```

---

## 3. Indentation and Formatting

- **Indentation**: 1 tab = 8 columns (Linux Kernel standard)
- **Max line length**: 80-100 chars
- **Braces**: always required on conditionals/loops (no exception even for single lines)
- **Formatting tool**: `clang-format` recommended

```c
/* Correct brace usage */
if (condition) {
        do_something();
}

/* Bad example - omitting braces is forbidden */
if (condition)
        do_something();
```

---

## 3-A. Comment Style

- Explain the **WHY (the rationale)**, avoid the WHAT (explaining the logic)
- State pre/post conditions for every function (NASA JPL)
- Clearly record hazards and assumptions

```c
/* Block comment: keep it concise */

int foo; /* Inline comment */

/**
 * Function description
 * @pre  The input value must be >= 0
 * @post The return value is not NULL
 * @param p_nSize Buffer size
 * @return Pointer to the result
 */
void *allocate_buffer(int p_nSize);
```

---

## 4. File Organization

```c
/* 1. Header guard */
#ifndef MODULE_NAME_H
#define MODULE_NAME_H

/* 2. System header includes */
#include <stdio.h>
#include <stdlib.h>

/* 3. Local header includes */
#include "local_module.h"

/* 4. Macro definitions */
#define MAX_SIZE 100

/* 5. Type definitions */
typedef struct {
        int  field_one;
        char field_two[32];
} my_struct_t;

/* 6. Function declarations */
int  process_data(my_struct_t *p_objData);
void cleanup(void);

#endif /* MODULE_NAME_H */
```

- Single responsibility per file
- File size 200-400 lines recommended, 800 lines max
- Declare the public API only in header files

---

## 5. Function Design Rules

- Function length: <= 50 lines (NASA JPL); if the logic exceeds 30 lines, extract a helper function and place it at the sibling level
- A function performs exactly one role (Single Responsibility Principle)
- **Control Flow Nesting**: limit if/else/loop nesting to **3 levels max**; beyond that, split the function or apply a Guard Clause (C does not support nested functions)
- All code must compile with no warnings
- Must pass static analyzers (Lint, clang-tidy)
- No recursion (MISRA C, NASA JPL)
- **KISS principle**: no unnecessary abstractions or nested macros; keep the simplest structure

---

## 6. Flow Control (Early Return / Guard Clauses)

> Principle definition: [.clauderules](../../.clauderules) § Code Quality — Stability and Flow Control

Instead of deep nesting, handle invalid conditions first at the top of the function and return immediately.

```c
/* Bad example — deep nesting */
int process(user_t *p_objUser) {
    if (p_objUser != NULL) {
        if (p_objUser->m_bIsActive) {
            if (p_objUser->m_vAge >= 0) {
                /* actual logic */
            }
        }
    }
    return -1;
}

/* Good example — Guard Clauses (Early Return) */
int process(user_t *p_objUser) {
    if (p_objUser == NULL)      { return ERROR_NULL;     }
    if (!p_objUser->m_bIsActive){ return ERROR_INACTIVE; }
    if (p_objUser->m_vAge < 0)  { return ERROR_INVALID;  }

    /* actual logic — clean, with no nesting */
    return OK;
}
```

---

## 7. Immutability Principle

> Principle definition: [.clauderules](../../.clauderules) § Code Quality — Stability and Flow Control

Do not modify objects/data in place; make active use of `const` to prevent unintended changes.

```c
/* Declare parameters const where possible */
int calculate_total(const int *p_arrPrices, int p_vCount);

/* Read-only pointer */
const char *get_name(const user_t *p_objUser) {
    return p_objUser->m_sName;
}

/* Struct update — return a copy instead of modifying the original */
user_t update_age(user_t p_objUser, int p_vNewAge) {
    user_t vUpdated = p_objUser;  /* copy */
    vUpdated.m_vAge = p_vNewAge;
    return vUpdated;
}
```

---

## 8. Security

> Principle definition: [.clauderules](../../.clauderules) § Security

- **Never hardcode** secrets, API keys, or passwords in source code — use environment variables or a config file
- Validate all external input (user input, data received over the network)
- Always pass buffer sizes explicitly; use `strncpy` instead of `strcpy`
- Always consider the possibility of integer overflow

```c
/* Bad example — hardcoding */
#define API_KEY "sk-12345abcde"

/* Good example — environment variable */
const char *p_sApiKey = getenv("API_KEY");
if (p_sApiKey == NULL) { return ERROR_CONFIG; }
```

---

## 9. Safe Coding Rules (MISRA C / NASA JPL)

- Minimize dynamic memory allocation (`malloc`)
- Always NULL-check before dereferencing a pointer
- Check all return values (do not ignore them)
- No `goto`
- Minimize use of global variables

---

## References

- [MISRA C:2025](https://misra.org.uk/)
- [Linux Kernel Coding Style](https://docs.kernel.org/process/coding-style.html)
- [NASA JPL Power of 10](https://spinroot.com/gerard/pdf/P10.pdf)
