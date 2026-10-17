import { useState } from 'react'
import { Chip } from '../../components'
import { kstDateFromToday } from '../../lib/datetime'

const WEEK = ['일', '월', '화', '수', '목', '금', '토']
const pad = (n: number) => String(n).padStart(2, '0')

interface CalendarProps {
  selected: string
  onSelect: (date: string) => void
}

// 월간 캘린더. 오늘(KST) 이전 날짜는 선택할 수 없다.
export function Calendar({ selected, onSelect }: CalendarProps) {
  const today = kstDateFromToday(0)
  const [ym, setYm] = useState(() => ({ y: Number(selected.slice(0, 4)), m: Number(selected.slice(5, 7)) }))

  const first = new Date(Date.UTC(ym.y, ym.m - 1, 1))
  const lead = first.getUTCDay()
  const count = new Date(Date.UTC(ym.y, ym.m, 0)).getUTCDate()
  const monthStart = `${ym.y}-${pad(ym.m)}-01`
  const atCurrentMonth = monthStart <= `${today.slice(0, 7)}-01`

  const move = (delta: number) => {
    const d = new Date(Date.UTC(ym.y, ym.m - 1 + delta, 1))
    setYm({ y: d.getUTCFullYear(), m: d.getUTCMonth() + 1 })
  }

  return (
    <div className="stack" style={{ gap: 10 }}>
      <div className="row">
        <Chip aria-label="이전 달" disabled={atCurrentMonth} onClick={() => move(-1)} style={{ minHeight: 44, minWidth: 44, padding: '0 12px' }}>
          ‹
        </Chip>
        <span style={{ fontWeight: 700 }}>
          {ym.y}년 {ym.m}월
        </span>
        <Chip aria-label="다음 달" onClick={() => move(1)} style={{ minHeight: 44, minWidth: 44, padding: '0 12px' }}>
          ›
        </Chip>
      </div>
      <div className="cal" role="group" aria-label="날짜 선택">
        {WEEK.map((w) => (
          <span key={w}>{w}</span>
        ))}
        {Array.from({ length: lead }, (_, i) => (
          <span key={`b${i}`} />
        ))}
        {Array.from({ length: count }, (_, i) => {
          const date = `${ym.y}-${pad(ym.m)}-${pad(i + 1)}`
          const past = date < today
          const cls = [past ? 'off' : '', date === today ? 'today' : '', date === selected ? 'sel' : ''].filter(Boolean).join(' ')
          return (
            <button key={date} type="button" className={cls} disabled={past} aria-pressed={date === selected} aria-label={`${ym.m}월 ${i + 1}일`} onClick={() => onSelect(date)}>
              {i + 1}
            </button>
          )
        })}
      </div>
    </div>
  )
}
