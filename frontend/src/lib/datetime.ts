// 서버는 UTC ISO(...Z)로 내려준다. 화면 표시와 날짜 기준은 항상 KST(Asia/Seoul).
const TZ = 'Asia/Seoul'
const WEEKDAYS = ['일', '월', '화', '수', '목', '금', '토']

function parts(iso: string) {
  const fmt = new Intl.DateTimeFormat('en-GB', {
    timeZone: TZ,
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    weekday: 'short',
    hourCycle: 'h23',
  })
  const p = Object.fromEntries(fmt.formatToParts(new Date(iso)).map((x) => [x.type, x.value]))
  return p as Record<'year' | 'month' | 'day' | 'hour' | 'minute' | 'weekday', string>
}

/** KST 기준 YYYY-MM-DD */
export function kstDate(iso: string): string {
  const p = parts(iso)
  return `${p.year}-${p.month}-${p.day}`
}

/** KST 기준 HH:mm */
export function kstTime(iso: string): string {
  const p = parts(iso)
  return `${p.hour}:${p.minute}`
}

/** 'MM.DD' */
export function formatMonthDay(date: string): string {
  return `${date.slice(5, 7)}.${date.slice(8, 10)}`
}

/** 'YYYY-MM-DD' → '월' */
export function weekdayKo(date: string): string {
  return WEEKDAYS[new Date(`${date}T00:00:00Z`).getUTCDay()]
}

/** '10.13 15:00' */
export function formatDateTime(iso: string): string {
  return `${formatMonthDay(kstDate(iso))} ${kstTime(iso)}`
}

/** '10.13 (화) 15:00' */
export function formatDateTimeLong(iso: string): string {
  const d = kstDate(iso)
  return `${formatMonthDay(d)} (${weekdayKo(d)}) ${kstTime(iso)}`
}

/** 오늘(KST) 기준으로 days일 뒤의 YYYY-MM-DD */
export function kstDateFromToday(days: number, now: Date = new Date()): string {
  const d = new Date(kstDate(now.toISOString()) + 'T00:00:00Z')
  d.setUTCDate(d.getUTCDate() + days)
  return d.toISOString().slice(0, 10)
}
