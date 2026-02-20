
import { drizzle } from "drizzle-orm/better-sqlite3";
import { Database } from "better-sqlite3";
import path from "path";

// Use SQLite for local development
const dbPath = path.resolve(process.cwd(), "sqlite.db");
const client = new Database(dbPath);
export const db = drizzle(client);
export default client;
