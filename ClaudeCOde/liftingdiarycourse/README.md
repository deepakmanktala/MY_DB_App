This is a [Next.js](https://nextjs.org) project bootstrapped with [`create-next-app`](https://nextjs.org/docs/app/api-reference/cli/create-next-app).

## Tech Stack

| Layer | Technology |
|---|---|
| Authentication | [Clerk](https://clerk.com) — user identity and session management. All database records are scoped to a `clerk_user_id` (e.g. `user_3CFJkRKMROlqhdcdBc5qfcQOo1J`) |
| Database | [Neon](https://neon.tech) — serverless PostgreSQL. Hosts all app tables: `workouts`, `exercises`, `workout_exercises`, `sets` |
| ORM | [Drizzle ORM](https://orm.drizzle.team) — type-safe SQL query builder and schema manager. Schema lives in `src/db/schema.ts`, DB client in `src/db/index.ts` |
| UI Components | [shadcn/ui](https://ui.shadcn.com) — copy-paste React component library built on Radix UI and Tailwind CSS. Components live in `src/components/ui/` |

### How user identity flows
Clerk authenticates the user and provides a `userId`. This ID is stored as `clerk_user_id` on the `workouts` and `exercises` tables to scope all data per user — no separate `users` table is needed in the app database.

## Getting Started

First, run the development server:

```bash
npm run dev
# or
yarn dev
# or
pnpm dev
# or
bun dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

You can start editing the page by modifying `app/page.tsx`. The page auto-updates as you edit the file.

This project uses [`next/font`](https://nextjs.org/docs/app/building-your-application/optimizing/fonts) to automatically optimize and load [Geist](https://vercel.com/font), a new font family for Vercel.

## Learn More

To learn more about Next.js, take a look at the following resources:

- [Next.js Documentation](https://nextjs.org/docs) - learn about Next.js features and API.
- [Learn Next.js](https://nextjs.org/learn) - an interactive Next.js tutorial.

You can check out [the Next.js GitHub repository](https://github.com/vercel/next.js) - your feedback and contributions are welcome!

## Deploy on Vercel

The easiest way to deploy your Next.js app is to use the [Vercel Platform](https://vercel.com/new?utm_medium=default-template&filter=next.js&utm_source=create-next-app&utm_campaign=create-next-app-readme) from the creators of Next.js.

Check out our [Next.js deployment documentation](https://nextjs.org/docs/app/building-your-application/deploying) for more details.
