import path from 'path';
import dotenv from 'dotenv';

dotenv.config();

/** Parse an integer environment variable, falling back when absent or malformed. */
const int = (value: string | undefined, fallback: number): number => {
  const parsed = Number.parseInt(value ?? '', 10);
  return Number.isFinite(parsed) && parsed > 0 ? parsed : fallback;
};

/** Parse a comma-separated list into trimmed, non-empty entries. */
const list = (value: string | undefined): string[] =>
  (value ?? '')
    .split(',')
    .map((entry) => entry.trim())
    .filter(Boolean);

const corsOrigins = list(process.env.CORS_ORIGINS);

export const config = {
  port: int(process.env.PORT, 3001),

  /** Allowed browser origins for the local development server. */
  corsOrigins: corsOrigins.length > 0 ? corsOrigins : ['http://localhost:5173', 'http://127.0.0.1:5173'],

  /**
  * Shared secret required on every data endpoint. Only the FastAPI server and
  * LangGraph agent are meant to reach this service directly.
   */
  serviceToken: process.env.SERVICE_TOKEN ?? '',

  uploadDir: process.env.UPLOAD_DIR
    ? path.resolve(process.env.UPLOAD_DIR)
    : path.join(process.cwd(), 'uploads'),

  maxFileSizeBytes: int(process.env.MAX_FILE_SIZE, 100 * 1024 * 1024),
  cleanupIntervalMs: int(process.env.DB_CLEANUP_INTERVAL, 60 * 60 * 1000),
  fileRetentionMs: int(process.env.DB_FILE_RETENTION, 4 * 60 * 60 * 1000),

  /** Hard ceiling on rows returned by a single query, protecting memory. */
  maxQueryRows: int(process.env.MAX_QUERY_ROWS, 5000),
  /** Rows returned by the dataset preview endpoint. */
  previewRowLimit: int(process.env.PREVIEW_ROW_LIMIT, 50),
  /** Milliseconds a single query may run before SQLite interrupts it. */
  queryTimeoutMs: int(process.env.QUERY_TIMEOUT_MS, 15_000),

  logLevel: process.env.LOG_LEVEL ?? 'info',
} as const;

