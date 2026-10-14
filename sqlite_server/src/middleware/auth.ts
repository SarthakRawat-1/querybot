import { Request, Response, NextFunction } from 'express';
import crypto from 'crypto';
import { config } from '../config';
import { logger } from '../utils/logger';

/** Constant-time comparison so a token cannot be recovered by timing the response. */
const tokensMatch = (provided: string, expected: string): boolean => {
  const a = Buffer.from(provided);
  const b = Buffer.from(expected);
  if (a.length !== b.length) return false;
  return crypto.timingSafeEqual(a, b);
};

/**
 * Requires the shared service token on data endpoints.
 *
 * The FastAPI server is the only browser-facing entry point. With no token configured the
 * check is skipped and a warning is logged, which keeps native local development
 * convenient when the shared token has not been configured yet.
 */
export const requireServiceToken = (req: Request, res: Response, next: NextFunction): void => {
  if (!config.serviceToken) {
    logger.warn('SERVICE_TOKEN is not set - data endpoints are unauthenticated', {
      path: req.originalUrl,
    });
    next();
    return;
  }

  const header = req.get('authorization') ?? '';
  const provided = header.startsWith('Bearer ') ? header.slice(7) : (req.get('x-service-token') ?? '');

  if (!provided || !tokensMatch(provided, config.serviceToken)) {
    logger.warn('Rejected request with missing or invalid service token', {
      path: req.originalUrl,
      ip: req.ip,
    });
    res.status(401).json({
      success: false,
      message: 'Unauthorized',
      data: null,
      timestamp: new Date().toISOString(),
    });
    return;
  }

  next();
};
