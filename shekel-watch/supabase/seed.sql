insert into public.dual_listed (name, ticker_tase, ticker_nyse, sector) values
  ('Teva Pharmaceutical',  'TEVA.TA', 'TEVA', 'Healthcare'),
  ('Elbit Systems',        'ESLT.TA', 'ESLT', 'Defense'),
  ('Check Point Software', 'CHKP.TA', 'CHKP', 'Technology'),
  ('Nice Systems',         'NICE.TA', 'NICE', 'Technology'),
  ('Amdocs',               'DOX.TA',  'DOX',  'Technology'),
  ('Tower Semiconductor',  'TSEM.TA', 'TSEM', 'Semiconductors')
on conflict do nothing;
