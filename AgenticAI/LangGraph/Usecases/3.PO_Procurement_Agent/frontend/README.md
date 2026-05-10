# Frontend — Purchase Order Agent

Professional UI for the PO Agent, built with **React 18 + Vite + TypeScript + Tailwind CSS**. No heavy UI library — every component is hand-written so students can read every line.

## Why this stack

| Choice | Reason |
|---|---|
| **React** | Most widely used UI library (~40% of frontend jobs). Marketable skill. |
| **Vite** | Fastest dev experience available. `npm run dev` is instant. |
| **TypeScript** | Catches API mismatch bugs at compile time. |
| **Tailwind CSS** | Utility-first styling, no separate CSS files to manage. |
| **Lucide icons** | Single icon package; tree-shaken on build. |
| **No shadcn/MUI/Antd** | Keeps the code readable. Students see exactly how each component is built. |

## Folder structure

```
frontend/
├── src/
│   ├── components/         ← Reusable UI bits
│   │   ├── PageHeader.tsx
│   │   └── StatusBadge.tsx
│   │
│   ├── pages/              ← One file per route
│   │   ├── ChatPage.tsx        — submit a PO, see live trace
│   │   ├── OrdersPage.tsx      — list of all POs
│   │   ├── OrderDetailPage.tsx — single PO with audit timeline
│   │   ├── ProductsPage.tsx    — catalog browser
│   │   ├── VendorsPage.tsx     — vendor master cards
│   │   └── BudgetsPage.tsx     — budget utilization
│   │
│   ├── lib/                ← API client + helpers
│   │   ├── api.ts              — typed fetch wrapper
│   │   └── format.ts           — INR / date formatters
│   │
│   ├── types/
│   │   └── api.ts              — types matching backend responses
│   │
│   ├── App.tsx             — sidebar layout + routes
│   ├── main.tsx            — entry point
│   └── index.css           — Tailwind directives + a few custom classes
│
├── index.html
├── package.json
├── vite.config.ts
├── tailwind.config.js
├── tsconfig.json
└── README.md               ← (this file)
```

## Setup

### Prerequisites

- **Node.js 18+** — check with `node --version`. If you don't have it, install from [nodejs.org](https://nodejs.org/) or use [nvm](https://github.com/nvm-sh/nvm).
- The **backend running** on port 8000 (see `../backend/README.md`).

### Install

```bash
cd frontend
npm install
```

This installs dependencies from `package.json` into `node_modules/`. Takes ~30 seconds the first time.

### Configure

The frontend reads `VITE_API_URL` from the project root `.env`. Default is `http://localhost:8000`. Vite also has a built-in proxy from `/api` → `http://localhost:8000` configured in `vite.config.ts`, so no additional CORS config is needed in dev.

### Run

```bash
npm run dev
```

Frontend live at [http://localhost:5173](http://localhost:5173). Vite hot-reloads on file save.

### Production build

```bash
npm run build      # produces dist/
npm run preview    # serves dist/ locally to verify
```

The `dist/` folder is a static site you can deploy anywhere (Vercel, Netlify, S3, nginx).

## Pages overview

| Route | What it shows |
|---|---|
| `/` | Chat-style interface to submit PO requests; right panel streams the agent verdict, findings, and final PO. |
| `/orders` | Sortable list of all POs with status badges and finding counts. |
| `/orders/:po_number` | Drill-down view of one PO with its audit timeline. |
| `/products` | Searchable catalog with stock levels — the source of truth the Auditor uses. |
| `/vendors` | Approved vendor cards with category coverage. |
| `/budgets` | Budget utilization with progress bars. |

## Extending the UI

To add a new page:

1. Create `src/pages/NewPage.tsx`
2. Add it to the routes in `App.tsx`
3. Add a nav entry in `App.tsx`'s `NAV` array

To call a new backend endpoint:

1. Add the type to `src/types/api.ts`
2. Add the fetch call to `src/lib/api.ts`
3. Use it in your page with a `useEffect`

## Common issues

### "Failed to fetch" or CORS errors

Make sure the backend is running on port 8000. The frontend's Vite dev server proxies `/api/*` to the backend automatically.

### Port 5173 already in use

```bash
npm run dev -- --port 3000
```

### Tailwind classes not applying

Make sure `index.css` is imported in `main.tsx` (it is by default). Restart `npm run dev`.

### Type errors after backend changes

Update `src/types/api.ts` to match the backend's new response shape, then `npm run lint` to catch any lingering mismatches.
