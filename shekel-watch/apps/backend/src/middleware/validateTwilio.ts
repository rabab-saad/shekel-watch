import twilio from 'twilio';
import { Request, Response, NextFunction } from 'express';
import { config } from '../config';

export function validateTwilio(req: Request, res: Response, next: NextFunction): void {
  const signature = req.headers['x-twilio-signature'] as string;
  const url = `${req.protocol}://${req.get('host')}${req.originalUrl}`;

  const isValid = twilio.validateRequest(
    config.TWILIO_AUTH_TOKEN,
    signature,
    url,
    req.body
  );

  if (!isValid) {
    res.status(403).send('Forbidden: Invalid Twilio signature');
    return;
  }

  next();
}
