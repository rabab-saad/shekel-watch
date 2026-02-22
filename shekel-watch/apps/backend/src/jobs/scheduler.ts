import cron from 'node-cron';
import { runMorningAlert } from './morningAlert';
import { runRateSnapshot } from './rateSnapshot';
import { logger } from '../utils/logger';

export function startScheduler(): void {
  // Morning alert: Mon–Fri 06:00 UTC (= 08:00 IST in winter)
  // Handler checks Israel time internally to handle DST correctly
  cron.schedule('0 5,6 * * 1-5', async () => {
    logger.info('Running morning alert job');
    await runMorningAlert();
  });

  // Hourly rate snapshot
  cron.schedule('0 * * * *', async () => {
    logger.info('Running hourly rate snapshot');
    await runRateSnapshot();
  });

  logger.info('Cron scheduler started (morning alerts Mon–Fri, hourly snapshots)');
}
