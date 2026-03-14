/**
 * TASE 2025 holiday schedule (Asia/Jerusalem).
 * Sources: TASE official calendar + Hebrew calendar 5785/5786.
 */

/** Full-day closures — TASE does not open */
export const TASE_HOLIDAYS: string[] = [
  // Purim (14 Adar II, 5785)
  '2025-03-13',

  // Passover / Pesach  (15 Nisan + 21 Nisan, 5785)
  '2025-04-13', // Day 1
  '2025-04-19', // Day 7

  // Yom HaAtzmaut — Independence Day
  // 5 Iyar 5785 falls on Shabbat → moved to Thursday 1 May
  '2025-05-01',

  // Shavuot (6 Sivan, 5785)
  '2025-06-02',

  // Tisha B'Av (9 Av, 5785)
  // 9 Av falls on Sunday in 2025 → observed same day
  '2025-08-03',

  // Rosh Hashana 5786 (1-2 Tishrei)
  '2025-09-22', // Day 1
  '2025-09-23', // Day 2

  // Yom Kippur (10 Tishrei, 5786)
  '2025-10-02',

  // Sukkot — first day (15 Tishrei, 5786)
  '2025-10-06',

  // Shmini Atzeret / Simchat Torah (22 Tishrei, 5786)
  '2025-10-13',
];

/**
 * Days where TASE closes early at 13:30 IST (holiday eves).
 * Regular Fridays (early close for Shabbat) are handled separately
 * by the component — do NOT duplicate them here.
 */
export const EARLY_CLOSE_DATES: string[] = [
  // Erev Purim
  '2025-03-12',

  // Erev Pesach (14 Nisan)
  '2025-04-12',

  // Yom HaZikaron — Memorial Day (eve of Independence Day)
  '2025-04-30',

  // Erev Shavuot (5 Sivan)
  '2025-06-01',

  // Erev Rosh Hashana (29 Elul)
  '2025-09-21',

  // Erev Yom Kippur (9 Tishrei)
  '2025-10-01',

  // Erev Sukkot (14 Tishrei)
  '2025-10-05',

  // Hoshana Raba / Erev Shmini Atzeret (21 Tishrei)
  '2025-10-12',
];
