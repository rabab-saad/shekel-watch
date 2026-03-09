import { Request, Response, NextFunction } from 'express';
import { config } from '../config';

export function validateGreenApi(req: Request, res: Response, next: NextFunction): void {
  const token = req.query.token as string;

  if (!token || token !== config.GREENAPI_WEBHOOK_TOKEN) {
    res.status(403).send('Forbidden: Invalid webhook token');
    return;
  }

  next();
}
