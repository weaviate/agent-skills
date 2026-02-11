---
name: interface
description: Create interfaces to interact with Weaviate vector database collections and functions. Create endpoints (FastAPI) and frontends (Node & Nextjs) depending on the context.
---

# Interface Operations

This skill provides access to FastAPI and NextJS documentation to build an interface around a Weaviate vector database. It also offers a design guideline for both the FastAPI app and the NextJS frontend

## Prerequisites

All scripts require Node v25.3.0+.

```bash
node --version
```

If needed, we need the host of the backend.

**Required:**

```bash
NEXT_PUBLIC_BACKEND_HOST="localhost:8000"
```

## Documentation References

FastAPI Docs: https://fastapi.tiangolo.com/
FastAPI Github: https://github.com/fastapi/fastapi
NodeJS Docs: https://nodejs.org/en
NextJS Docs: https://nextjs.org/docs
TailwindCSS Docs: https://tailwindcss.com/docs/installation/framework-guides/nextjs
shadcn components: https://ui.shadcn.com/docs/components
react-icons: https://react-icons.github.io/react-icons
Framer Motion: https://motion.dev/

## Getting Started

### 1. Next.js setup

**Source:** [Next.js App Router Installation](https://nextjs.org/docs/app/getting-started/installation). Verify against current docs; do not rely on training data.

- **Command (repo root, current dir):** `npx create-next-app@latest . --yes`  
  Sandbox: may need `required_permissions: ["all"]` so CLI can write.
- **Defaults (--yes):** TypeScript, ESLint, Tailwind v4, App Router, Turbopack, `@/*` → `./*`, no `src/`. App in `app/`, static in `public/`.
- **Scripts:** `dev` | `build` | `start` | `lint`. Dev: http://localhost:3000.
- **Routes:** App Router. Root layout `app/layout.tsx`, home `app/page.tsx`. Imports: `@/` = project root.
- **Env:** `next build` needs network if using `next/font/google` (Geist). Multiple lockfiles → consider `turbopack.root` in next.config or remove extras.

---

### 2. shadcn/ui

**Source:** [Next.js – shadcn](https://ui.shadcn.com/docs/installation/next) | [CLI](https://ui.shadcn.com/docs/cli). **Requires:** §1 (Next + Tailwind v4 + App Router + `@/*`, no `src/`).

- **Init:** `npx shadcn@latest init -t next -y -b zinc --no-src-dir`  
  Flags: `-t next`, `-y` (skip prompt), `-b zinc` (base color; immutable after init), `--no-src-dir` (use root `components/`). Omit `--no-src-dir` if using `src/`.
- **Add component:** `npx shadcn@latest add button -y` (or `card dialog input`; `-o` overwrites).
- **Effect:** Creates `components.json`, `lib/utils.ts` (cn), updates `app/globals.css` (tw-animate, shadcn/tailwind.css, CSS vars), adds deps (clsx, tailwind-merge, cva, lucide-react, radix-ui, tw-animate-css). UI components in `components/ui/<name>.tsx`. Import: `import { Button } from "@/components/ui/button"`.
- **Check:** Use `<Button>Click me</Button>` on a page; `npm run lint`; `npm run build`.

---

## Design Guidelines

Follow these when building the Next.js frontend so the interface stays consistent and pleasant to use.

### Stack and structure

- **Layout and UI:** Use [shadcn components](https://ui.shadcn.com/docs/components) for all layout and interactive elements (buttons, cards, inputs, dialogs, etc.). Do not introduce another UI library.
- **Architecture:** Build a **Single Page Application (SPA)**—one main page that updates in place; avoid full-page navigations unless necessary.
- **Icons:** Use [react-icons](https://react-icons.github.io/react-icons) for all icons. Prefer a single icon set (e.g. `react-icons/fa` or `react-icons/hi`) for consistency.

### Visual style

- **Overall:** Keep the design **minimal, sleek, and clean**. Avoid clutter, heavy borders, and noisy backgrounds.
- **Aesthetic:** Take inspiration from **liquid glass**—frosted, translucent surfaces; soft blur; light borders and shadows; a sense of depth without heaviness. Use `backdrop-blur`, semi-transparent fills, and subtle gradients where they support this look.

### Motion and animation

- **Library:** Use [Framer Motion](https://motion.dev/) for all component and page animations. Do not add another animation library.
- **Character:** Animations should be **subtle, springy, and purposeful**—they add life and feedback (e.g. hover, enter/exit) without distracting. Prefer spring physics over linear or ease-out where it feels natural.
