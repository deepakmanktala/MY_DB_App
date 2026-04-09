# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## ⚠️ Important: Next.js Version Warning

This project uses **Next.js 16.2.2** and **React 19.2.4** — versions that may differ significantly from training data. Before writing any Next.js-specific code, read the relevant guide in:

```
node_modules/next/dist/docs/
```

Pay attention to deprecation notices and breaking changes.

## Commands

```bash
# Development server (http://localhost:3000)
npm run dev

# Production build
npm run build

# Start production server
npm start

# Lint
npm run lint
```

## Stack

- **Next.js 16** with App Router (`src/app/`)
- **React 19**
- **TypeScript 5**
- **Tailwind CSS 4** (via `@tailwindcss/postcss`)

## Architecture

- `src/app/layout.tsx` — root layout; sets up Geist fonts and `<html>`/`<body>` structure
- `src/app/page.tsx` — home page (currently the default scaffold)
- `src/app/globals.css` — global styles

All new routes go under `src/app/` following Next.js App Router conventions. There are currently no API routes, components, or data-fetching layers — the app is at its initial scaffold state.