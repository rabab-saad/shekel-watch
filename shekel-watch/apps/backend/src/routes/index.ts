import { Router } from 'express';
import ratesRouter      from './rates';
import stocksRouter     from './stocks';
import arbitrageRouter  from './arbitrage';
import summaryRouter    from './summary';
import whatsappRouter   from './whatsapp';
import paperTradeRouter from './paperTrade';

export const router = Router();

router.use('/rates',       ratesRouter);
router.use('/stocks',      stocksRouter);
router.use('/arbitrage',   arbitrageRouter);
router.use('/summary',     summaryRouter);
router.use('/webhook',     whatsappRouter);   // POST /api/webhook/whatsapp
router.use('/paper-trade', paperTradeRouter); // POST /api/paper-trade
