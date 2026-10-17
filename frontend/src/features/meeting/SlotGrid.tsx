import { useMemo, useState } from 'react'
import { Button, Chip } from '../../components'
import { addDays, firstViewWeek, formatMonthDay, kstDate, kstDateFromToday, kstTime, weekdayKo } from '../../lib/datetime'
import type { Slot } from './api'
import { SLOT_WEEKS } from './hooks'

interface SlotGridProps {
  slots: Slot[]
  selected: string | null
  onSelect: (startAt: string) => void
}

// 월~금 5열 × 운영 시간 행 격자. 가능은 선택, 불가·마감은 회색 라벨로 보여준다. 주 단위로 이동한다.
export function SlotGrid({ slots, selected, onSelect }: SlotGridProps) {
  const [week, setWeek] = useState(0)
  const first = firstViewWeek(kstDateFromToday(0))

  const { times, byKey } = useMemo(() => {
    const timeSet = new Set<string>()
    const map = new Map<string, Slot>()
    for (const s of slots) {
      const t = kstTime(s.start_at)
      timeSet.add(t)
      map.set(`${kstDate(s.start_at)} ${t}`, s)
    }
    return { times: [...timeSet].sort(), byKey: map }
  }, [slots])

  if (slots.length === 0) {
    return <p className="muted">신청할 수 있는 시간이 아직 열려 있지 않습니다.</p>
  }

  const monday = addDays(first, week * 7)
  const dates = Array.from({ length: 5 }, (_, i) => addDays(monday, i))

  return (
    <div className="slot-wrap">
      <div className="row">
        <Button variant="ghost" size="sm" disabled={week === 0} onClick={() => setWeek(week - 1)}>
          이전 주
        </Button>
        <b className="mono" aria-live="polite">{formatMonthDay(dates[0])} ~ {formatMonthDay(dates[4])}</b>
        <Button variant="ghost" size="sm" disabled={week >= SLOT_WEEKS - 1} onClick={() => setWeek(week + 1)}>
          다음 주
        </Button>
      </div>
      <div className="slot-scroll">
        <div className="slot-grid" role="group" aria-label="희망 시간 선택">
          <div />
          {dates.map((d) => (
            <div key={d} className="slot-head">
              <span className="mono" style={{ fontWeight: 700 }}>{formatMonthDay(d)}</span> <span className="muted" style={{ fontSize: 13 }}>{weekdayKo(d)}</span>
            </div>
          ))}
          {times.map((t) => (
            <SlotRow key={t} time={t} dates={dates} byKey={byKey} selected={selected} onSelect={onSelect} />
          ))}
        </div>
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
        const label = `${formatMonthDay(d)} ${time}`
        if (!slot || slot.state === 'unavailable') {
          return (
            <div key={d} className="slot-off" aria-label={`${label} 불가`}>
              불가
            </div>
          )
        }
        if (slot.state === 'full' || !slot.available) {
          return (
            <div key={d} className="slot-off" aria-label={`${label} 마감`}>
              마감
            </div>
          )
        }
        return (
          <Chip key={d} className="slot-btn" selected={selected === slot.start_at} aria-label={`${label} 가능`} onClick={() => onSelect(slot.start_at)}>
            {selected === slot.start_at ? '선택됨' : '가능'}
          </Chip>
        )
      })}
    </>
  )
}
