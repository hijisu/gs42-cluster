import { kstDate, kstTime, kstToIso } from '../../lib/datetime'

/** 30분 단위 시작 시각 09:00 ~ 18:30 */
export const TIMES = Array.from({ length: 20 }, (_, i) => `${String(9 + Math.floor(i / 2)).padStart(2, '0')}:${i % 2 ? '30' : '00'}`)
/** 종료 선택지: 첫 시작 + 30분 ~ 19:00 */
export const END_TIMES = [...TIMES.slice(1), '19:00']

export const addDays = (date: string, days: number): string => {
  const d = new Date(`${date}T00:00:00Z`)
  d.setUTCDate(d.getUTCDate() + days)
  return d.toISOString().slice(0, 10)
}

/** 그 날짜가 속한 주의 월요일 */
export const weekStart = (date: string): string => {
  const dow = new Date(`${date}T00:00:00Z`).getUTCDay()
  return addDays(date, dow === 0 ? -6 : 1 - dow)
}

export const slotKey = (date: string, time: string) => `${date} ${time}`
export const isWeekday = (date: string) => ![0, 6].includes(new Date(`${date}T00:00:00Z`).getUTCDay())

/** 서버가 준 ISO 시각들 → 화면용 키 집합 */
export const toKeys = (slots: string[]): Set<string> => new Set(slots.map((iso) => slotKey(kstDate(iso), kstTime(iso))))

/** 화면 키 집합 → 서버로 보낼 ISO(정렬) */
export const toSlots = (keys: Set<string>): string[] =>
  [...keys].sort().map((k) => {
    const [date, time] = k.split(' ')
    return kstToIso(date, time)
  })

/** [start, end) 구간에 걸치는 30분 칸 */
export const timesBetween = (start: string, end: string): string[] => TIMES.filter((t) => t >= start && t < end)

export const sameSet = (a: Set<string>, b: Set<string>) => a.size === b.size && [...a].every((k) => b.has(k))
