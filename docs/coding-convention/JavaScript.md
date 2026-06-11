# JavaScript / TypeScript Coding Convention

> **[Optional add-on]** Adopt only in web/Node projects. Python-only projects may ignore it.
> When adopting, switch `.harness.toml [language].profile` to the relevant language and also replace the gate commands (test/lint/type).
>
> Reference standards: Airbnb JavaScript Style Guide / Google JS Style Guide / StandardJS
> The canonical source for language-agnostic quality principles is [.clauderules](../../.clauderules).

---

## 1. Naming Conventions

| Target | Rule | Example |
|------|------|------|
| Variable | `camelCase` | `userName`, `totalCount` |
| Function | `camelCase` | `calculateTotal()`, `getUserById()` |
| Class / constructor | `PascalCase` | `UserManager`, `DataProcessor` |
| Constant | `UPPER_SNAKE_CASE` | `MAX_SIZE`, `DEFAULT_TIMEOUT` |
| Private attribute | `_camelCase` | `_privateField`, `_internalState` |
| File name | `camelCase` / `PascalCase` | `userService.js`, `UserModel.js` |
| React component file | `PascalCase` | `UserCard.jsx`, `LoginForm.jsx` |

- No single-character variables (loop counters `i`, `j` excepted)
- Prefer clear words over abbreviations

### Function Naming Rules

Write function names as **verb + object** to clearly express the action performed.

| Pattern | Use | Example |
|------|------|------|
| `get` | Read a value (no side effects) | `getUser()`, `getTotalCount()` |
| `set` | Set a value | `setConfig()`, `setTimeout()` |
| `fetch` | Asynchronous data request | `fetchUser()`, `fetchOrders()` |
| `create` / `make` | Create an object | `createSession()`, `makeRequest()` |
| `update` | Modify | `updateUser()`, `updateStatus()` |
| `delete` / `remove` | Delete | `deleteUser()`, `removeItem()` |
| `is` / `has` / `can` | Return a boolean | `isValid()`, `hasPermission()` |
| `calculate` / `compute` | Compute | `calculateTotal()`, `computeHash()` |
| `handle` | Handle an event/error | `handleError()`, `handleSubmit()` |
| `parse` / `format` | Convert | `parseDate()`, `formatPrice()` |
| `on` | Event handler (callback) | `onClick()`, `onSubmit()` |

```javascript
// Examples of correct function names
async function fetchUserById(p_sUserId) { ... }
function calculateDiscountedPrice(p_vPrice, p_vRate) { ... }
function isEmailValid(p_sEmail) { ... }
function handlePaymentError(p_objError) { ... }
```

---

## 2. Hybrid Naming Convention (Required)

Combine a variable's **origin (Scope)** and **data type (Type)** as a prefix so the name alone reveals both at a glance.

- **Format**: `[Scope]_[Type][Name]`
- **Scope**: `g_` (Global), `m_` (Member/Class field), `p_` (Parameter); Local is omitted
- **Type**: `v` (Number), `s` (String), `b` (Boolean), `arr` (Array), `obj` (Object), `fn` (Function)

| Example | Description |
|------|------|
| `g_vTotalCount` | Global numeric variable |
| `m_sUserName` | Class member string |
| `p_objConfig` | Object passed as a parameter |
| `vLocalIdx` | Local numeric variable |
| `fnCalculate` | Function variable |

```javascript
const g_vMaxRetry = 3;

class UserService {
  constructor() {
    this.m_sBaseUrl = '/api/users';
    this.m_arrCache = [];
  }

  getUser(p_sUserId, p_objOptions = {}) {
    const vRetryCount = 0;
    const fnHandleError = (err) => console.error(err);
    // ...
  }
}
```

---

## 3. Indentation and Formatting

- **Indentation**: 2 spaces (Airbnb/Google standard)
- **Max line length**: 100 chars (Airbnb), 80 chars (Google)
- **Semicolons**: required (Airbnb/Google) — StandardJS omits them
- **Quotes**: prefer single quotes `'` (template literals use backticks `` ` ``)
- **Formatting tools**: ESLint + Prettier recommended

```javascript
// Good example
const userName = 'Alice';
const greeting = `Hello, ${userName}!`;

function calculateTotal(price, quantity) {
  const total = price * quantity;
  return total;
}

// Arrow function
const double = (num) => num * 2;
```

---

## 3-A. Comment Style

- Explain the **WHY (the rationale)**, avoid the WHAT (the logic)
- JSDoc is required on public functions/classes

```javascript
// Single-line comment

/**
 * Calculate the user's total.
 * @param {number} price - Unit price
 * @param {number} quantity - Quantity
 * @returns {number} Total amount
 * @throws {Error} If an input value is negative
 */
function calculateTotal(price, quantity) {}
```

---

## 4. File Organization

```javascript
// 1. External library imports
import React from 'react';
import axios from 'axios';

// 2. Internal module imports
import { formatDate } from './utils/dateHelper';
import UserModel from './models/UserModel';

// 3. Constant definitions
const MAX_RETRY_COUNT = 3;
const API_BASE_URL = process.env.API_URL;

// 4. Class or main functions
class UserService {
  constructor() {}

  async getUser(userId) {}
}

// 5. Utility functions

// 6. Exports
export default UserService;
export { MAX_RETRY_COUNT };
```

- Single responsibility per file
- File size 200-400 lines recommended, 800 lines max
- Group related imports (external → internal order)

---

## 5. Variable Declaration Rules

- No `var` — prefer `const`, use `let` when reassignment is needed
- Initialize at declaration
- Declare one variable per line

```javascript
// Good example
const MAX_SIZE = 100;
let currentIndex = 0;

// Bad example
var x = 1, y = 2;
```

---

## 6. Function Design Rules

- Function length: <= 50 lines; if the logic exceeds 30 lines, extract a helper function and place it at the sibling level
- A function performs exactly one role (Single Responsibility Principle)
- **Function nesting max 1 level** (aim for 0 where possible) — extract nested functions to the enclosing scope when possible
- When more than 3 parameters, group them into an object
- Prefer pure functions; minimize side effects
- **KISS principle**: no unnecessary design patterns or nested abstractions; keep the simplest structure

```javascript
// Use an object when there are many parameters
function createUser({ name, email, role = 'user' }) {
  return { name, email, role };
}

// Extract a sibling-level helper instead of a nested function
function validateEmail(p_sEmail) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(p_sEmail);
}

function registerUser(p_objData) {
  if (!validateEmail(p_objData.email)) {
    throw new Error('Invalid email');
  }
  // ...
}
```

---

## 7. Flow Control (Early Return / Guard Clauses)

> Principle definition: [.clauderules](../../.clauderules) § Code Quality — Stability and Flow Control

Instead of deep nesting, handle invalid conditions first at the top of the function and return immediately.

```javascript
// Bad example — deep nesting
function processOrder(order) {
  if (order) {
    if (order.items.length > 0) {
      if (order.isPaid) {
        // actual logic
      }
    }
  }
}

// Good example — Guard Clauses (Early Return)
function processOrder(p_objOrder) {
  if (!p_objOrder)                  { throw new Error('No order');     }
  if (p_objOrder.items.length === 0){ throw new Error('No items');     }
  if (!p_objOrder.isPaid)           { throw new Error('Not paid');     }

  // actual logic — clean, with no nesting
}
```

---

## 8. Immutability Principle

> Principle definition: [.clauderules](../../.clauderules) § Code Quality — Stability and Flow Control

Do not modify objects/arrays in place; always return a new copy to prevent side effects.

```javascript
// Bad example — in-place modification (mutation)
function addItem(arr, item) {
  arr.push(item); // modifies the original
  return arr;
}

// Good example — return a copy (immutability)
function addItem(p_arrItems, p_objItem) {
  return [...p_arrItems, p_objItem];
}

function updateUser(p_objUser, p_objChanges) {
  return { ...p_objUser, ...p_objChanges };
}
```

---

## 9. Security

> Principle definition: [.clauderules](../../.clauderules) § Security

- **Never hardcode** secrets, API keys, or passwords in source code — use `process.env`
- Validate all external input (user input, API responses)
- Prevent XSS when rendering HTML (use `textContent` instead of `innerHTML`)

```javascript
// Bad example — hardcoding
const API_KEY = 'sk-12345abcde';

// Good example — environment variable
const API_KEY = process.env.API_KEY;
if (!API_KEY) { throw new Error('The API_KEY environment variable is not set.'); }
```

---

## 10. Error Handling

```javascript
// async/await error handling
async function fetchUser(userId) {
  try {
    const response = await api.get(`/users/${userId}`);
    return response.data;
  } catch (error) {
    console.error('Failed to fetch user:', error.message);
    throw error;
  }
}
```

---

## References

- [Airbnb JavaScript Style Guide](https://github.com/airbnb/javascript)
- [Google JavaScript Style Guide](https://google.github.io/styleguide/jsguide.html)
- [StandardJS](https://standardjs.com/)
