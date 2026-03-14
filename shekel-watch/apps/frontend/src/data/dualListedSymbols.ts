export interface DualListedSymbol {
  symbol:     string;
  taseSymbol: string;
  name:       string;
}

export const DUAL_LISTED: DualListedSymbol[] = [
  { symbol: 'TEVA', taseSymbol: 'TEVA.TA', name: 'Teva Pharmaceuticals' },
  { symbol: 'CHKP', taseSymbol: 'CHKP.TA', name: 'Check Point Software' },
  { symbol: 'NICE', taseSymbol: 'NICE.TA', name: 'NICE Systems'         },
  { symbol: 'MNDY', taseSymbol: 'MNDY.TA', name: 'Monday.com'           },
  { symbol: 'WIX',  taseSymbol: 'WIX.TA',  name: 'Wix.com'              },
  { symbol: 'GLBE', taseSymbol: 'GLBE.TA', name: 'Global-E Online'      },
];
