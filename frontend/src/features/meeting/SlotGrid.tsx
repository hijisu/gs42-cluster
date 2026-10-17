import { useMemo, useState } from 'react'
import { Button, Chip } from '../../components'
import { formatMonthDay, kstDate, kstTime, weekdayKo } from '../../lib/datetime'
import type { Slot } from './api'

const DAYS_PER_PAGE = 4

interface SlotGridProps {
  slots: Slot[]
  selected: string | null
  onSelect: (startAt: string) => void
}

// 날짜(열) × 시간(행) 격자. 가능/마감/선택됨을 보여준다.
export function SlotGrid({ slots, selected, onSelect }: SlotGridProps) {
  const [page, setPage] = useState(0)

  const { dates, times, byKey } = useMemo(() => {
    const dateSet = new Set<string>()
    const timeSet = new Set<string>()
    const map = new Map<string, Slot>()
    for (const s of slots) {
      const d = kstDate(s.start_at)
      const t = kstTime(s.start_at)
      dateSet.add(d)
      timeSet.add(t)
      map.set(`${d} ${t}`, s)
    }
    return { dates: [...dateSet].sort(), times: [...timeSet].sort(), byKey: map }
  }, [slots])

  if (slots.length === 0) {
    return <p className="muted">신청할 수 있는 시간이 아직 열려 있지 않습니다.</p>
  }

  const pageDates = dates.slice(page * DAYS_PER_PAGE, (page + 1) * DAYS_PER_PAGE)
  const maxPage = Math.ceil(dates.length / DAYS_PER_PAGE) - 1

  return (
    <div className="slot-wrap">
      <div className="row">
        <Button variant="ghost" size="sm" disabled={page === 0} onClick={() => setPage(page - 1)}>
          이전
        </Button>
        <Button variant="ghost" size="sm" disabled={page >= maxPage} onClick={() => setPage(page + 1)}>
          다음
        </Button>
      </div>
      <div className="slot-grid" role="group" aria-label="희망 시간 선택" style={{ gridTemplateColumns: `48px repeat(${pageDates.length}, minmax(44px, 1fr))` }}>
        <div />
        {pageDates.map((d) => (
          <div key={d} className="slot-head">
            <span className="mono" style={{ fontWeight: 700 }}>{formatMonthDay(d)}</span> <span className="muted" style={{ fontSize: 13 }}>{weekdayKo(d)}</span>
          </div>
        ))}
        {times.map((t) => (
          <SlotRow key={t} time={t} dates={pageDates} byKey={byKey} selected={selected} onSelect={onSelect} />
        ))}
      </div>
    </div>
  )
}

interface SlotRowProps {
  time: string
  dates: string[]
  byKey: Map<string, Slot>
  selected: string | null
  onSelect: (startAt: string) => void
}

function SlotRow({ time, dates, byKey, selected, onSelect }: SlotRowProps) {
  return (
    <>
      <div className="mono muted slot-time">{time}</div>
      {dates.map((d) => {
        const slot = byKey.get(`${d} ${time}`)
        if (!slot) {
          return (
            <div key={d} className="slot-off" aria-label={`${formatMonthDay(d)} ${time} 열리지 않음`}>
              -
            </div>
          )
        }
        if (!slot.available) {
          return (
            <div key={d} className="slot-off" aria-label={`${formatMonthDay(d)} ${time} 마감`}>
              마감
            </div>
          )
        }
        return (
          <Chip
            key={d}
            className="slot-btn"
            selected={selected === slot.start_at}
            aria-label={`${formatMonthDay(d)} ${time} 가능`}
            onClick={() => onSelect(slot.start_at)}
          >
            {selected === slot.start_at ? '선택됨' : '가능'}
          </Chip>
        )
      })}
    </>
  )
}
