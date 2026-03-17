import { Router } from 'express';
import ratesRouter      from './rates';
import stocksRouter     from './stocks';
import arbitrageRouter  from './arbitrage';
import summaryRouter    from './summary';
import whatsappRouter   from './whatsapp';
import paperTradeRouter from './paperTrade';
import inflationRouter  from './inflation';
import explainRouter    from './explain';
import crewRouter       from './crew';
import portfolioRouter  from './portfolio';

export const router = Router();

router.use('/rates',       ratesRouter);
router.use('/stocks',      stocksRouter);
router.use('/arbitrage',   arbitrageRouter);
router.use('/summary',     summaryRouter);
router.use('/webhook',     whatsappRouter);   // POST /api/webhook/whatsapp
router.use('/paper-trade', paperTradeRouter); // POST /api/paper-trade
router.use('/inflation',   inflationRouter);  // GET  /api/inflation
router.use('/explain',     explainRouter);    // POST /api/explain
router.use('/crew',        crewRouter);       // GET  /api/crew/summary|currency-arbitrage, POST /api/crew/compose-alert
router.use('/portfolio',   portfolioRouter);  // GET  /api/portfolio/analysis, POST /api/portfolio/suggestions
