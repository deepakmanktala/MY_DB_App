// Initialises the Drizzle client connected to Neon via HTTP transport, exported as `db` for use across the app.
import { drizzle } from 'drizzle-orm/neon-http';

const db = drizzle(process.env.DATABASE_URL!);

export { db };
