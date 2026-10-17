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

/** KST 날짜(YYYY-MM-DD)와 시각(HH:mm)을 서버로 보낼 UTC ISO로 바꾼다. */
export function kstToIso(date: string, time: string): string {
  return new Date(`${date}T${time}:00+09:00`).toISOString()
}

/** '15:00–18:00' */
export function formatTimeRange(startIso: string, endIso: string): string {
  return `${kstTime(startIso)}–${kstTime(endIso)}`
}

/** 'YYYY-MM-DD' → '10.16 (금)' */
export function formatDayLabel(date: string): string {
  return `${formatMonthDay(date)} (${weekdayKo(date)})`
}

/** '방금 전' / 'N분 전' / 'N시간 전' / 'N일 전' */
export function timeAgo(iso: string, now: Date = new Date()): string {
  const min = Math.max(0, Math.floor((now.getTime() - new Date(iso).getTime()) / 60000))
  if (min < 1) return '방금 전'
  if (min < 60) return `${min}분 전`
  if (min < 60 * 24) return `${Math.floor(min / 60)}시간 전`
  return `${Math.floor(min / 1440)}일 전`
}

const EN_WEEKDAYS = ['SUN', 'MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT']

/** '2026.10.09 FRI' (KST 기준 오늘) */
export function kstTodayLabel(now: Date = new Date()): string {
  const d = kstDate(now.toISOString())
  const day = EN_WEEKDAYS[new Date(`${d}T00:00:00Z`).getUTCDay()]
  return `${d.replaceAll('-', '.')} ${day}`
}

/** YYYY-MM-DD에 days일을 더한다(날짜만 다루므로 시간대 영향 없음) */
export function addDays(date: string, days: number): string {
  const d = new Date(`${date}T00:00:00Z`)
  d.setUTCDate(d.getUTCDate() + days)
  return d.toISOString().slice(0, 10)
}

/** 그 날짜가 속한 주의 월요일 */
export function weekStart(date: string): string {
  const dow = new Date(`${date}T00:00:00Z`).getUTCDay()
  return addDays(date, dow === 0 ? -6 : 1 - dow)
}

export const isWeekday = (date: string): boolean => ![0, 6].includes(new Date(`${date}T00:00:00Z`).getUTCDay())

/** 처음 보여줄 주의 월요일: 주말에는 이번 주가 모두 지난 뒤라 다음 주를 보여준다 */
export const firstViewWeek = (today: string): string => (isWeekday(today) ? weekStart(today) : addDays(weekStart(today), 7))
