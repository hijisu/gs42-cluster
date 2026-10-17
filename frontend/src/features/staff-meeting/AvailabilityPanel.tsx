import { useEffect, useRef, useState } from 'react'
import { Button, Card, Chip } from '../../components'
import { ApiError } from '../../lib/api'
import { formatMonthDay, kstDateFromToday, weekdayKo } from '../../lib/datetime'
import { MOBILE_QUERY, useMediaQuery } from '../../lib/useMediaQuery'
import { addDays, END_TIMES, isWeekday, sameSet, slotKey, TIMES, timesBetween, toKeys, toSlots, weekStart } from './availabilityGrid'
import { useMyAvailability, useResetAvailability, useSaveAvailability } from './hooks'
import { errorLabel } from './labels'

type View = 'week' | 'day'

/** 내 면담 가능 시간: 주/일 단위 칸 선택(드래그·탭) 또는 시작~종료 입력으로 설정 */
export function AvailabilityPanel() {
  const mobile = useMediaQuery(MOBILE_QUERY)
  const [view, setView] = useState<View>(() => (mobile ? 'day' : 'week'))
  const [anchor, setAnchor] = useState(() => kstDateFromToday(0))
  const [dirty, setDirty] = useState(false)

  const from = view === 'week' ? weekStart(anchor) : anchor
  const to = view === 'week' ? addDays(from, 6) : anchor
  const days = view === 'week' ? Array.from({ length: 7 }, (_, i) => addDays(from, i)) : [anchor]
  const { data, isPending, isError } = useMyAvailability(from, to)
  const step = view === 'week' ? 7 : 1
  const title = view === 'week' ? `${formatMonthDay(from)} ~ ${formatMonthDay(to)}` : `${formatMonthDay(anchor)} (${weekdayKo(anchor)})`

  return (
    <Card className="stack" style={{ gap: 12 }}>
      <h2 className="card-title">내 면담 가능 시간</h2>
      <div className="av-toolbar">
        <div className="chips" role="group" aria-label="보기 단위">
          <Chip selected={view === 'week'} disabled={dirty} onClick={() => setView('week')}>주</Chip>
          <Chip selected={view === 'day'} disabled={dirty} onClick={() => setView('day')}>일</Chip>
        </div>
        <div className="av-nav">
          <Button variant="ghost" size="sm" aria-label={view === 'week' ? '이전 주' : '이전 날'} disabled={dirty} onClick={() => setAnchor(addDays(anchor, -step))}>‹</Button>
          <span className="av-title" aria-live="polite">{title}</span>
          <Button variant="ghost" size="sm" aria-label={view === 'week' ? '다음 주' : '다음 날'} disabled={dirty} onClick={() => setAnchor(addDays(anchor, step))}>›</Button>
          <Button variant="ghost" size="sm" disabled={dirty} onClick={() => setAnchor(kstDateFromToday(0))}>오늘</Button>
        </div>
      </div>
      {dirty && <p className="muted small">저장하지 않은 변경이 있어요. 저장하거나 취소하면 다른 날짜로 이동할 수 있어요.</p>}
      {isPending && <p className="muted" role="status">불러오는 중…</p>}
      {isError && <p role="alert">가능 시간을 불러오지 못했어요.</p>}
      {data && (
        <Editor
          key={`${from}-${to}-${data.slots.join()}-${data.customized_days.join()}`}
          from={from}
          to={to}
          days={days}
          slots={data.slots}
          customized={data.customized_days}
          onDirty={setDirty}
        />
      )}
    </Card>
  )
}

interface EditorProps {
  from: string
  to: string
  days: string[]
  slots: string[]
  customized: string[]
  onDirty: (dirty: boolean) => void
}

function Editor({ from, to, days, slots, customized, onDirty }: EditorProps) {
  const save = useSaveAvailability()
  const reset = useResetAvailability()
  const initial = toKeys(slots)
  const [picked, setPicked] = useState<Set<string>>(initial)
  const dirty = !sameSet(picked, initial)
  useEffect(() => {
    onDirty(dirty)
    return () => onDirty(false)
  }, [dirty, onDirty])

  const paint = (keys: string[], on: boolean) =>
    setPicked((prev) => {
      const next = new Set(prev)
      keys.forEach((k) => (on ? next.add(k) : next.delete(k)))
      return next
    })

  // 마우스 드래그: 누른 칸의 반대 상태로 지나가는 칸을 모두 칠한다. 터치·키보드는 탭(클릭)으로 토글한다.
  const dragging = useRef<boolean | null>(null)
  const skipClick = useRef(false)
  useEffect(() => {
    const end = () => {
      dragging.current = null
    }
    window.addEventListener('pointerup', end)
    window.addEventListener('pointercancel', end)
    return () => {
      window.removeEventListener('pointerup', end)
      window.removeEventListener('pointercancel', end)
    }
  }, [])

  const [target, setTarget] = useState(days.length === 1 ? days[0] : 'weekdays')
  const [start, setStart] = useState('10:00')
  const [end, setEnd] = useState('12:00')
  const rangeInvalid = end <= start
  const apply = (on: boolean) => {
    const dates = target === 'weekdays' ? days.filter(isWeekday) : [target]
    paint(dates.flatMap((d) => timesBetween(start, end).map((t) => slotKey(d, t))), on)
  }

  const error = save.error ?? reset.error
  const message = error instanceof ApiError ? (errorLabel[error.code ?? ''] ?? '처리하지 못했어요. 잠시 후 다시 시도해 주세요.') : error ? '처리하지 못했어요.' : null
  const busy = save.isPending || reset.isPending
  const week = days.length > 1

  return (
    <>
      <div className={`av-grid ${week ? 'week' : 'day'}`} role="group" aria-label="가능 시간 선택">
        <span />
        {days.map((d) => (
          <span key={d} className="av-head">
            {formatMonthDay(d)} ({weekdayKo(d)})
            <small>{customized.includes(d) ? '직접 설정' : '기본'}</small>
          </span>
        ))}
        {TIMES.map((t) => (
          <FragmentRow key={t} time={t}>
            {days.map((d) => {
              const key = slotKey(d, t)
              const on = picked.has(key)
              return (
                <button
                  key={key}
                  type="button"
                  className={`av-cell${on ? ' on' : ''}`}
                  aria-pressed={on}
                  aria-label={`${formatMonthDay(d)} (${weekdayKo(d)}) ${t}`}
                  onPointerDown={(e) => {
                    if (e.pointerType !== 'mouse' || e.button !== 0) return
                    e.preventDefault()
                    dragging.current = !on
                    skipClick.current = true
                    paint([key], !on)
                  }}
                  onPointerEnter={() => dragging.current !== null && paint([key], dragging.current)}
                  onClick={() => {
                    if (skipClick.current) {
                      skipClick.current = false
                      return
                    }
                    paint([key], !on)
                  }}
                >
                  {!week && t}
                </button>
              )
            })}
          </FragmentRow>
        ))}
      </div>

      <fieldset className="av-range">
        <legend className="label">시간 범위로 설정</legend>
        <div className="av-range-row">
          <div className="field">
            <label htmlFor="av-target">날짜</label>
            <select id="av-target" className="input" value={target} onChange={(e) => setTarget(e.target.value)}>
              {week && <option value="weekdays">평일 전체</option>}
              {days.map((d) => (
                <option key={d} value={d}>
                  {formatMonthDay(d)} ({weekdayKo(d)})
                </option>
              ))}
            </select>
          </div>
          <div className="field">
            <label htmlFor="av-start">시작</label>
            <select id="av-start" className="input" value={start} onChange={(e) => setStart(e.target.value)}>
              {TIMES.map((t) => (
                <option key={t} value={t}>{t}</option>
              ))}
            </select>
          </div>
          <div className="field">
            <label htmlFor="av-end">종료</label>
            <select id="av-end" className="input" value={end} onChange={(e) => setEnd(e.target.value)}>
              {END_TIMES.map((t) => (
                <option key={t} value={t}>{t}</option>
              ))}
            </select>
          </div>
        </div>
        {rangeInvalid && <p role="alert" className="error">종료 시간은 시작 시간보다 늦어야 해요.</p>}
        <div className="av-range-actions">
          <Button variant="ghost" size="sm" disabled={rangeInvalid} onClick={() => apply(true)}>열기</Button>
          <Button variant="ghost" size="sm" disabled={rangeInvalid} onClick={() => apply(false)}>닫기</Button>
        </div>
      </fieldset>

      <p className="muted small">
        저장하면 {week ? '이 주의 모든 날이' : '이 날이'} 직접 설정한 날이 돼요. 표시가 &lsquo;기본&rsquo;인 날은 평일 10~12시·13~17시로 열려 있어요.
      </p>
      {message && <p role="alert" className="login-error">{message}</p>}
      <div className="modal-actions">
        <Button variant="ghost" disabled={busy || !customized.length} onClick={() => reset.mutate({ from, to })}>
          기본값으로 되돌리기
        </Button>
        <Button variant="ghost" disabled={busy || !dirty} onClick={() => setPicked(initial)}>
          변경 취소
        </Button>
        <Button disabled={busy || !dirty} onClick={() => save.mutate({ from, to, slots: toSlots(picked) })}>
          {save.isPending ? '저장 중…' : '저장'}
        </Button>
      </div>
    </>
  )
}

/** 시간 라벨 + 날짜별 칸 한 줄(그리드의 자식으로 평탄화) */
function FragmentRow({ time, children }: { time: string; children: React.ReactNode }) {
  return (
    <>
      <span className="av-time">{time.endsWith(':00') ? time : ''}</span>
      {children}
    </>
  )
}
