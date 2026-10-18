import { useEffect, useRef, useState } from 'react'
import { Button, Card } from '../../components'
import { ApiError } from '../../lib/api'
import { formatMonthDay, kstDateFromToday, weekdayKo } from '../../lib/datetime'
import { addDays, firstViewWeek, sameSet, slotKey, TIMES, toKeys, toSlots, weekStart } from './availabilityGrid'
import { useMyAvailability, useSaveAvailability } from './hooks'
import { errorLabel } from './labels'

/** 보고 바꿀 수 있는 범위: 오늘이 속한 주부터 4주(서버 규칙과 같다) */
const WEEKS = 4

/** 내 면담 가능 시간: 평일 5일 × 30분 칸. 칸을 누르거나 끌어서 열고 닫는다. */
export function AvailabilityPanel({ tabs }: { tabs: React.ReactNode }) {
  const today = kstDateFromToday(0)
  const firstWeek = firstViewWeek(today)
  const [from, setFrom] = useState(firstWeek)
  const [dirty, setDirty] = useState(false)
  const to = addDays(from, 6)
  const days = Array.from({ length: 5 }, (_, i) => addDays(from, i))
  const { data, isPending, isError } = useMyAvailability(from, to)
  const atStart = from <= firstWeek
  const atEnd = from >= addDays(weekStart(today), 7 * (WEEKS - 1))

  return (
    <Card className="stack" style={{ gap: 12 }}>
      {(isPending || isError) && <div className="row">{tabs}</div>}
      {isPending && <p className="muted" role="status">불러오는 중…</p>}
      {isError && <p role="alert">가능 시간을 불러오지 못했어요.</p>}
      {data && (
        <Editor
          key={`${from}-${data.slots.join()}`}
          from={from}
          days={days}
          today={today}
          slots={data.slots}
          tabs={tabs}
          onDirty={setDirty}
          nav={
            <div className="av-nav">
              <Button variant="secondary" size="sm" aria-label="이전 주" disabled={dirty || atStart} onClick={() => setFrom(addDays(from, -7))}>‹</Button>
              <span className="av-title" aria-live="polite">{formatMonthDay(days[0])} ~ {formatMonthDay(days[4])}</span>
              <Button variant="secondary" size="sm" aria-label="다음 주" disabled={dirty || atEnd} onClick={() => setFrom(addDays(from, 7))}>›</Button>
              <Button variant="secondary" size="sm" disabled={dirty || atStart} onClick={() => setFrom(firstWeek)}>오늘</Button>
            </div>
          }
        />
      )}
    </Card>
  )
}

interface EditorProps {
  from: string
  days: string[]
  today: string
  slots: string[]
  nav: React.ReactNode
  tabs: React.ReactNode
  onDirty: (dirty: boolean) => void
}

function Editor({ from, days, today, slots, nav, tabs, onDirty }: EditorProps) {
  const save = useSaveAvailability()
  const initial = toKeys(slots)
  const [picked, setPicked] = useState<Set<string>>(initial)
  const dirty = !sameSet(picked, initial)
  useEffect(() => {
    onDirty(dirty)
    return () => onDirty(false)
  }, [dirty, onDirty])

  const paint = (key: string, on: boolean) =>
    setPicked((prev) => {
      if (prev.has(key) === on) return prev
      const next = new Set(prev)
      if (on) next.add(key)
      else next.delete(key)
      return next
    })

  // 끌기(마우스·터치 공통): 누른 칸의 반대 상태로, 포인터가 지나가는 칸을 모두 칠한다.
  // 터치는 포인터가 처음 누른 칸에 묶이므로 enter 이벤트 대신 좌표로 칸을 찾는다.
  const painting = useRef<boolean | null>(null)
  const cellAt = (x: number, y: number) => (document.elementFromPoint(x, y) as HTMLElement | null)?.closest<HTMLElement>('[data-slot]')
  useEffect(() => {
    const move = (e: PointerEvent) => {
      if (painting.current === null) return
      const key = cellAt(e.clientX, e.clientY)?.dataset.slot
      if (key) paint(key, painting.current)
    }
    const end = () => {
      painting.current = null
    }
    window.addEventListener('pointermove', move)
    window.addEventListener('pointerup', end)
    window.addEventListener('pointercancel', end)
    return () => {
      window.removeEventListener('pointermove', move)
      window.removeEventListener('pointerup', end)
      window.removeEventListener('pointercancel', end)
    }
  }, [])

  // 서버는 지난 날짜 저장을 거절하므로 오늘 이후의 평일만 보낸다
  const saveFrom = from > today ? from : today
  const saveTo = days[4]
  const error = save.error
  const message = error instanceof ApiError ? (errorLabel[error.code ?? ''] ?? '저장하지 못했어요. 잠시 후 다시 시도해 주세요.') : error ? '저장하지 못했어요.' : null

  return (
    <div className="av-editor">
      <div className="row av-head-row">
        {tabs}
        <div style={{ display: 'flex', gap: 6 }}>
          <Button variant="secondary" size="sm" disabled={save.isPending || !dirty} onClick={() => setPicked(initial)}>
            변경 취소
          </Button>
          <Button size="sm" disabled={save.isPending || !dirty} onClick={() => save.mutate({ from: saveFrom, to: saveTo, slots: toSlots(picked, saveFrom, saveTo) })}>
            {save.isPending ? '저장 중…' : '저장'}
          </Button>
        </div>
      </div>
      {/* 안내는 전문을 그대로 보여준다. 데스크톱: 변경 취소·저장 버튼 바로 아래 오른쪽(높이 고정). 모바일: 날짜 이동 아래(높이 고정). */}
      <p className="av-status" role="status" title={message ?? undefined}>
        {message ?? (dirty ? '저장하지 않은 변경이 있어요. 저장하거나 취소해야 다른 주로 이동할 수 있어요.' : '')}
      </p>
      <div className="av-toolbar">{nav}</div>
      <div className="av-grid" role="group" aria-label="가능 시간 선택">
        <span />
        {days.map((d) => (
          <span key={d} className={`av-head${d === today ? ' today' : ''}${d < today ? ' pastcol' : ''}`}>
            <span>{formatMonthDay(d)} ({weekdayKo(d)})</span>
          </span>
        ))}
        {TIMES.map((t) => (
          <Row key={t} time={t}>
            {days.map((d) => {
              const key = slotKey(d, t)
              if (d < today) return <span key={key} className="av-cell past" aria-hidden="true" />
              const on = picked.has(key)
              return (
                <button
                  key={key}
                  type="button"
                  className={`av-cell${on ? ' on' : ''}`}
                  data-slot={key}
                  data-tip={`${weekdayKo(d)} ${t}`}
                  aria-pressed={on}
                  aria-label={`${formatMonthDay(d)} (${weekdayKo(d)}) ${t}`}
                  onPointerDown={(e) => {
                    if (e.pointerType === 'mouse' && e.button !== 0) return
                    e.preventDefault()
                    painting.current = !on
                    paint(key, !on)
                  }}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                      e.preventDefault()
                      paint(key, !on)
                    }
                  }}
                />
              )
            })}
          </Row>
        ))}
      </div>
      <p className="muted small av-note">오늘부터 4주 안에서 설정할 수 있어요. 칸을 누르거나 끌어서 열고 닫아요.</p>
    </div>
  )
}

/** 1시간(2칸)마다 전체 열에 걸친 구분선을 넣고, 시각 라벨 + 날짜별 칸을 한 줄로 이어 붙인다. */
function Row({ time, children }: { time: string; children: React.ReactNode }) {
  const hour = time.endsWith(':00')
  return (
    <>
      {hour && time !== TIMES[0] && <div className="av-sep" aria-hidden="true" />}
      <span className="av-time">{hour ? time : ''}</span>
      {children}
    </>
  )
}
