# Web Application Coding Protocol

> **[Optional — default web protocol]** Adopt in projects that include a web frontend.
> Coding conventions for modern web frontend and architecture — based on {{WEB_FRAMEWORK}} (e.g. React / Vue) + {{LANG}} (e.g. TypeScript).
> For naming/language rules see [../coding-convention/JavaScript.md](../coding-convention/JavaScript.md);
> the canonical source for language-agnostic quality is [../../.clauderules](../../.clauderules).

---

## Table of Contents

1. [Project Architecture](#1-project-architecture)
2. [File and Folder Organization](#2-file-and-folder-organization)
3. [Naming Conventions](#3-naming-conventions)
4. [Type Definitions and Interfaces](#4-type-definitions-and-interfaces)
5. [Component Design Structure](#5-component-design-structure)
6. [State Management Paradigm](#6-state-management-paradigm)
7. [Error Handling and Boundaries](#7-error-handling-and-boundaries)
8. [Async and API Communication Structure](#8-async-and-api-communication-structure)
9. [Security and Defensive Coding](#9-security-and-defensive-coding)
10. [Performance and Rendering Optimization](#10-performance-and-rendering-optimization)
11. [Comment and Documentation Style](#11-comment-and-documentation-style)
12. [Code Formatting and Linting](#12-code-formatting-and-linting)

---

## 1. Project Architecture

Borrow concepts from FSD (Feature-Sliced Design), or follow a layered structure based on Domain-Driven Design (DDD).

```
src/
 ├── app/       → Application entry point, global setup (Router, Providers, Reset CSS)
 ├── pages/     → Page components at the routing level (Page composition)
 ├── widgets/   → Independent functional blocks that make up a page (e.g. Header, Sidebar, UserProfile)
 ├── features/  → Concrete user interactions with business value (e.g. form submission, authentication, payment)
 ├── entities/  → Business domain entities (domain models and pure logic such as User, Product)
 └── shared/    → UI, utilities, and API clients reused across the project
```

**Dependency direction:** `app → pages → widgets → features → entities → shared`

- Higher layers reference lower layers.
- Avoid references between the same layer where possible; a lower layer referencing a higher layer (a reverse dependency) is strictly forbidden.

---

## 2. File and Folder Organization

### Component Folder Pattern

Instead of putting everything in a single file, group highly cohesive files into a folder.

```
Button/
 ├── ui.tsx         // Actual UI rendering code
 ├── model.ts       // Component-related logic, state (optional)
 ├── lib.ts         // Component-specific helper functions (optional)
 ├── index.ts       // Public API export (Barrel file)
 └── style.css      // (or .module.css / styled)
```

**Role of `index.ts` (Barrel Pattern):**
```typescript
// Hide internal implementation and explicitly export only what is used externally
export { Button } from './ui';
export type { ButtonProps } from './ui';
```

---

## 3. Naming Conventions

Naming conventions follow the project's central rules.
For detailed naming rules, see the following document:
👉 [JavaScript Coding Convention (`../coding-convention/JavaScript.md`)](../coding-convention/JavaScript.md)

---

## 4. Type Definitions and Interfaces

### `type` vs `interface`

Separate their uses to maintain consistency within the project.

```typescript
// 1. Defining object structure (inheritance and extensibility) - use interface
interface User {
  id: string;
  email: string;
}

interface AdminUser extends User {
  role: 'admin';
}

// 2. Unions, tuples, primitive type aliases - use type
type Status = 'IDLE' | 'LOADING' | 'SUCCESS' | 'ERROR';
type Matrix = [number, number];
```

### Separating Global and Local Types
- **Local types**: Types used only within a given component/function file are declared at the top of that file (`Props`, etc.).
- **Global types**: Declared inside the `shared/types/` folder and shared via `index.ts`. Prefer explicit `import` over implicit `global.d.ts`.

---

## 5. Component Design Structure

### Single Responsibility Principle (SRP) and Function Nesting Limit
- A single component should focus only on UI rendering, or only on logic handling.
- **Ensuring visibility (required):** Defining another component function inside a component block (a Nested Function) is **strictly forbidden**. (Max nesting depth 0)

**❌ Bad example (nested component):**
```tsx
function ParentComponent() {
  // Redefining a component internally (causes unmount/remount on every render ➝ performance degradation and reduced readability)
  const ChildComponent = () => <div>Child component</div>;

  return (
    <div>
      <ChildComponent />
    </div>
  );
}
```

**✅ Good example (Lifting / extraction):**
```tsx
// Extract to the external sibling level
const ChildComponent = () => <div>Child component</div>;

function ParentComponent() {
  return (
    <div>
      <ChildComponent />
    </div>
  );
}
```

### Container / Presenter Pattern (or Custom Hook Separation)
Separate logic from view.

```tsx
// 1. The 'logic (Container)' that fetches user data
function useUserProfile(userId: string) {
  const { data, loading } = useQuery(`/api/user/${userId}`);
  return { user: data, loading };
}

// 2. The 'view (Presenter)' responsible purely for rendering
function UserProfileUI({ user }) {
  return <div>Welcome, {user.name}.</div>;
}

// 3. Composition
export function UserProfile({ userId }) {
  const { user, loading } = useUserProfile(userId);
  if (loading) return <Spinner />;
  return <UserProfileUI user={user} />;
}
```

---

## 6. State Management Paradigm

- **Server State:** State holding API data — use `React Query`, `SWR`, `RTK Query`, etc. to delegate caching and synchronization.
- **Global (client) State:** Store only state that must be shared across the whole application, such as theme and user session, in `Zustand`, `Redux`, or the `Context API`.
- **Local State:** Form input values, toggle parameters, etc. are not placed in the global store but resolved inside the component with `useState`.

---

## 7. Error Handling and Boundaries

### Declarative Error Handling (Error Boundary)

Set up an Error Boundary per layer to guard against crashes in the UI rendering tree.

```tsx
<ErrorBoundary fallback={<PageErrorFallback />}>
  <Suspense fallback={<PageSkeleton />}>
    <DashboardPage />
  </Suspense>
</ErrorBoundary>
```

### Fail-Fast & Early Return

Handle exceptional situations first at the top, without nesting conditionals.

```typescript
// ✅ Good example (Early Return)
function processPayment(user: User, amount: number) {
    if (!user) throw new Error("User not found");
    if (!user.hasValidCard) throw new Error("Invalid payment method");
    if (amount <= 0) throw new Error("Invalid amount");

    // Normal processing logic (no nesting)
    api.charge(user.id, amount);
}
```

---

## 8. Async and API Communication Structure

### API Client Abstraction (Axios / Fetch)
Instead of setting the URL and headers manually every time, use a centralized instance.

```typescript
// shared/api/client.ts
const apiClient = axios.create({
  baseURL: process.env.{{API_URL_ENV}},  // e.g. VITE_API_URL / NEXT_PUBLIC_API_URL
  timeout: 5000,
});

// Common handling via interceptors (token injection, etc.)
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});
```

### Enforce API Response Types
```typescript
interface ApiResponse<T> {
  data: T;
  message: string;
  code: number;
}

// Specify Promise in the function return type
export const getUser = async (id: string): Promise<ApiResponse<User>> => {
  const response = await apiClient.get(`/users/${id}`);
  return response.data;
};
```

---

## 9. Security and Defensive Coding (Web Security)

- **XSS (Cross-Site Scripting) prevention:**
  - As a rule, forbid the use of `innerHTML` and `dangerouslySetInnerHTML`.
  - When exposing external data, use the framework's own escaping features.
- **CSRF (Cross-Site Request Forgery):**
  - APIs that change sensitive state must use token-based authentication (header) or a lock (SameSite cookie).
- **Dependency integrity:**
  - Include `npm audit` in the CI/CD pipeline and force-update vulnerable old packages to the latest version.

---

## 10. Performance and Rendering Optimization

### Preventing Forced Re-renders (Memoization)
When an object, array, or callback function is passed as Props to a child component, consider memoization to prevent unnecessary renders.
- React: use `useMemo`, `useCallback`, `React.memo`
- However, avoid over-engineering (memoizing every variable); apply it appropriately only where there is a real load.

### Code Splitting & Lazy Loading
Dynamically load heavy libraries or split at the route level.
```tsx
const HeavyChartWidget = lazy(() => import('./widgets/HeavyChartWidget'));

function Dashboard() {
  return (
    <Suspense fallback={<Spinner />}>
      <HeavyChartWidget />
    </Suspense>
  );
}
```

---

## 11. Comment and Documentation Style

### JSDoc Usage Standard
Use the JSDoc format on externally exposed utility functions and shared components to get IDE IntelliSense support.

```typescript
/**
 * @brief  Takes a specific date format and returns a localized string
 * @param  date   Raw date string (ISO format specified)
 * @param  locale Locale string (default: 'ko-KR')
 * @retval Converted date string (e.g. "January 1, 2024")
 */
export function formatDate(date: string, locale: string = 'ko-KR'): string {
  // ...
}
```

- **Purpose of comments:** Explain not *how* it works, but **why** it was written this way — the business decision rationale or edge cases. The logic itself should be explained by variable and function names (self-documenting).

---

## 12. Code Formatting and Linting

### Enforcing Prettier & ESLint
Enforce conventions as code to prevent style debates between developers. (Auto-format on save.)

**Key ESLint policies:**
- `no-console`: forbid `console.log` in production builds (error logs excepted).
- `no-unused-vars`: treat unused variables as errors.
- `@typescript-eslint/no-explicit-any`: forbid explicit `any` type usage (when unavoidable, use `unknown` then apply a type guard).
- `react-hooks/exhaustive-deps`: prevent missing entries in a Hook's dependency array (strictly applied).

---
> This document is continuously updated (a Living Document) according to the maturity of the project and the framework version.
