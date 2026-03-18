import cron from 'node-cron';
import { runMorningAlert }      from './morningAlert';
import { runRateSnapshot }      from './rateSnapshot';
import { runUpdateRiskScores }  from './updateRiskScores';
import { runArbitrageScan }     from './arbitrageScan';
import { runVolatilityMonitor } from './volatilityMonitor';
import { checkPendingOrders }   from './pendingOrderMonitor';
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

  // Risk score update: Mon–Fri 06:00 UTC (= 08:00 IST)
  cron.schedule('0 6 * * 1-5', async () => {
    logger.info('Running risk score update job');
    await runUpdateRiskScores();
  });

  // Arbitrage scan: every 5 min Mon–Fri (job itself checks 09:00–17:30 IST)
  cron.schedule('*/5 * * * 1-5', async () => {
    await runArbitrageScan();
  });

  // Volatility monitor: every 10 min Mon–Sun (job gates itself to 10:00–17:30 IST, Sun–Thu)
  cron.schedule('*/10 * * * *', async () => {
    await runVolatilityMonitor();
  });

  // Pending order monitor: every 60 seconds — checks limit/stop-loss/take-profit orders
  cron.schedule('* * * * *', async () => {
    try {
      await checkPendingOrders();
    } catch (err) {
      logger.error('Pending order monitor failed', err);
    }
  });

  logger.info('Cron scheduler started (morning alerts, hourly snapshots, daily risk scores, arbitrage scan, volatility monitor, pending order monitor)');
}
