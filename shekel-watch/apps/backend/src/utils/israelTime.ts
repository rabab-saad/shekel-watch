import dayjs from 'dayjs';
import utc from 'dayjs/plugin/utc';
import timezone from 'dayjs/plugin/timezone';

dayjs.extend(utc);
dayjs.extend(timezone);

export function toIsraelTime(date: Date): dayjs.Dayjs {
  return dayjs(date).tz('Asia/Jerusalem');
}

export function nowInIsrael(): dayjs.Dayjs {
  return dayjs().tz('Asia/Jerusalem');
}
