import { formatMonthDay, kstDate, kstTime } from '../../lib/datetime'
import type { RoomBlock } from './api'

/** 0=월 … 6=일 */
export const WEEKDAY_LABELS = ['월', '화', '수', '목', '금', '토', '일']

export const repeatOptions = [
  { value: 'none', label: '반복 안 함' },
  { value: 'daily', label: '매일' },
  { value: 'weekly', label: '매주(요일 선택)' },
  { value: 'weekdays', label: '평일(월~금)' },
] as const

/** '매주 토 · ~10.31' 같은 반복 요약 */
export function repeatSummary(b: Pick<RoomBlock, 'repeat' | 'weekdays' | 'until'>): string {
  if (b.repeat === 'none') return '반복 없음'
  const until = b.until ? ` · ~${formatMonthDay(b.until)}` : ''
  if (b.repeat === 'daily') return `매일${until}`
  if (b.repeat === 'weekdays') return `평일${until}`
  return `매주 ${b.weekdays.map((d) => WEEKDAY_LABELS[d]).join('·')}${until}`
}

export const blockTime = (b: Pick<RoomBlock, 'start_at' | 'end_at'>) => `${kstTime(b.start_at)}–${kstTime(b.end_at)}`
export const blockFirstDay = (b: Pick<RoomBlock, 'start_at'>) => kstDate(b.start_at)

/** 30분 단위 시각 00:00 ~ 23:30 */
export const HALF_HOURS = Array.from({ length: 48 }, (_, i) => `${String(Math.floor(i / 2)).padStart(2, '0')}:${i % 2 ? '30' : '00'}`)
