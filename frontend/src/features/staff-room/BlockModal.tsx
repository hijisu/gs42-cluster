import { useState } from 'react'
import { Button, Chip, Field, Modal } from '../../components'
import { formatDayLabel, kstDate, kstDateFromToday, kstTime, kstToIso } from '../../lib/datetime'
import type { Room } from '../room/api'
import type { BlockInput, BlockRepeat, BlockResult, RoomBlock } from './api'
import { HALF_HOURS, repeatOptions, WEEKDAY_LABELS } from './blockLabels'
import { messageFor } from './errors'
import { useCreateBlock, useUpdateBlock, useUpdateOccurrence } from './hooks'

/** create=새 차단, series=반복 전체 수정, occurrence=한 회차만 수정 */
export type BlockTarget = { mode: 'create' } | { mode: 'series'; block: RoomBlock } | { mode: 'occurrence'; block: RoomBlock; day: string }

const titles = { create: '예약 차단 추가', series: '차단 일정 수정(전체 회차)', occurrence: '이 회차만 수정' } as const

export function BlockModal({ target, rooms, onClose }: { target: BlockTarget | null; rooms: Room[]; onClose: () => void }) {
  return (
    <Modal open={target !== null} title={target ? titles[target.mode] : titles.create} onClose={onClose}>
      {target && <BlockForm key={target.mode + ('block' in target ? target.block.id : '') + ('day' in target ? target.day : '')} target={target} rooms={rooms} onClose={onClose} />}
    </Modal>
  )
}

function initial(target: BlockTarget, rooms: Room[]) {
  if (target.mode === 'create') {
    return { roomId: rooms[0]?.id ?? 0, date: kstDateFromToday(0), start: '10:00', end: '12:00', reason: '', repeat: 'none' as BlockRepeat, weekdays: [] as number[], until: '' }
  }
  const b = target.block
  const occ = target.mode === 'occurrence' ? b.occurrences.find((o) => o.date === target.day) : undefined
  const startIso = occ?.start_at ?? b.start_at
  const endIso = occ?.end_at ?? b.end_at
  return { roomId: b.room_id, date: kstDate(startIso), start: kstTime(startIso), end: kstTime(endIso), reason: b.reason, repeat: b.repeat, weekdays: b.weekdays, until: b.until ?? '' }
}

function BlockForm({ target, rooms, onClose }: { target: BlockTarget; rooms: Room[]; onClose: () => void }) {
  const init = initial(target, rooms)
  const [roomId, setRoomId] = useState(init.roomId)
  const [date, setDate] = useState(init.date)
  const [start, setStart] = useState(init.start)
  const [end, setEnd] = useState(init.end)
  const [reason, setReason] = useState(init.reason)
  const [repeat, setRepeat] = useState<BlockRepeat>(init.repeat)
  const [weekdays, setWeekdays] = useState<number[]>(init.weekdays)
  const [until, setUntil] = useState(init.until)
  const [submitted, setSubmitted] = useState(false)
  const [warning, setWarning] = useState<BlockResult | null>(null)

  const create = useCreateBlock()
  const updateSeries = useUpdateBlock()
  const updateOne = useUpdateOccurrence()
  const mutation = target.mode === 'create' ? create : target.mode === 'series' ? updateSeries : updateOne
  const series = target.mode !== 'occurrence'
  const repeating = series && repeat !== 'none'

  const errors = {
    reason: reason.trim() === '' ? '차단 사유를 입력해 주세요.' : undefined,
    date: date === '' ? '날짜를 선택해 주세요.' : undefined,
    time: end <= start ? '종료 시간은 시작 시간보다 늦어야 해요.' : undefined,
    weekdays: repeat === 'weekly' && weekdays.length === 0 ? '요일을 하나 이상 골라 주세요.' : undefined,
    until: repeating && until === '' ? '반복 종료일을 선택해 주세요.' : repeating && date !== '' && until < date ? '반복 종료일은 첫 회차 날짜 이후여야 해요.' : undefined,
  }
  const hasError = Object.values(errors).some(Boolean) || roomId === 0
  const error = messageFor(mutation.error, '저장하지 못했어요. 잠시 후 다시 시도해 주세요.')

  const base = { room_id: roomId, start_at: kstToIso(date || '2000-01-01', start), end_at: kstToIso(date || '2000-01-01', end), reason: reason.trim() }
  const seriesBody: BlockInput = { ...base, repeat, weekdays: repeat === 'weekly' ? [...weekdays].sort() : [], until: repeating ? until : null }

  /** 겹치는 예약이 있으면 먼저 경고하고, 확인 후 저장한다. */
  function run(checkOnly: boolean) {
    const done = (r: BlockResult) => {
      if (checkOnly) {
        if (r.conflicting_reservations.length > 0) setWarning(r)
        else run(false)
      } else {
        onClose()
      }
    }
    if (target.mode === 'create') create.mutate({ ...seriesBody, check_only: checkOnly }, { onSuccess: done })
    else if (target.mode === 'series') updateSeries.mutate({ id: target.block.id, body: seriesBody, check_only: checkOnly }, { onSuccess: done })
    else updateOne.mutate({ id: target.block.id, day: target.day, body: base, check_only: checkOnly }, { onSuccess: done })
  }
  function submit() {
    setSubmitted(true)
    setWarning(null)
    if (!hasError) run(true)
  }
  const toggleDay = (d: number) => setWeekdays((cur) => (cur.includes(d) ? cur.filter((x) => x !== d) : [...cur, d]))

  return (
    <div className="stack">
      {target.mode === 'occurrence' && <p className="muted small">{formatDayLabel(target.day)} 회차만 바뀌고, 나머지 회차는 그대로예요.</p>}
      <div className="field">
        <label htmlFor="block-room">장소</label>
        <select id="block-room" className="input" value={roomId} onChange={(e) => setRoomId(Number(e.target.value))}>
          {rooms.map((r) => (
            <option key={r.id} value={r.id}>
              {r.name}
            </option>
          ))}
        </select>
      </div>
      <div className="g3" style={{ gap: 12 }}>
        {target.mode === 'occurrence' ? (
          <div className="field">
            <span className="label">날짜</span>
            <span>{formatDayLabel(target.day)}</span>
          </div>
        ) : (
          <Field label={repeating ? '첫 회차 날짜' : '날짜'} type="date" value={date} onChange={(e) => setDate(e.target.value)} error={submitted ? errors.date : undefined} />
        )}
        <TimeSelect label="시작" value={start} onChange={setStart} />
        <TimeSelect label="종료" value={end} onChange={setEnd} error={submitted ? errors.time : undefined} />
      </div>
      {series && (
        <>
          <div className="field">
            <label htmlFor="block-repeat">반복</label>
            <select id="block-repeat" className="input" value={repeat} onChange={(e) => setRepeat(e.target.value as BlockRepeat)}>
              {repeatOptions.map((o) => (
                <option key={o.value} value={o.value}>
                  {o.label}
                </option>
              ))}
            </select>
          </div>
          {repeat === 'weekly' && (
            <div className="field">
              <span className="label">요일</span>
              <div className="chips" role="group" aria-label="반복 요일">
                {WEEKDAY_LABELS.map((w, d) => (
                  <Chip key={w} selected={weekdays.includes(d)} onClick={() => toggleDay(d)}>
                    {w}
                  </Chip>
                ))}
              </div>
              {submitted && errors.weekdays && <span className="error" role="alert">{errors.weekdays}</span>}
            </div>
          )}
          {repeating && <Field label="반복 종료일" type="date" value={until} onChange={(e) => setUntil(e.target.value)} error={submitted ? errors.until : undefined} hint="첫 회차부터 최대 1년까지 반복할 수 있어요." />}
        </>
      )}
      <Field label="사유" placeholder="예: 수학 교육" value={reason} onChange={(e) => setReason(e.target.value)} error={submitted ? errors.reason : undefined} />
      {warning && (
        <div className="info" role="alert" style={{ background: 'var(--c-warn-bg)', color: 'var(--c-warn-text)' }}>
          <p>이 시간과 겹치는 예약이 {warning.conflicting_reservations.length}건 있어요. 저장해도 기존 예약은 자동으로 취소되지 않으니 직접 확인해 주세요.</p>
          <ul>
            {warning.conflicting_reservations.map((r) => (
              <li key={r.id}>
                {formatDayLabel(kstDate(r.start_at))} {kstTime(r.start_at)}–{kstTime(r.end_at)} · {r.purpose}
              </li>
            ))}
          </ul>
        </div>
      )}
      {error && <p role="alert" className="login-error">{error}</p>}
      <div className="modal-actions">
        <Button variant="secondary" onClick={onClose}>
          닫기
        </Button>
        {warning ? (
          <Button variant="danger" disabled={mutation.isPending} onClick={() => run(false)}>
            겹치는 예약이 있어도 저장
          </Button>
        ) : (
          <Button disabled={mutation.isPending} onClick={submit}>
            {mutation.isPending ? '확인 중…' : '저장'}
          </Button>
        )}
      </div>
    </div>
  )
}

function TimeSelect({ label, value, onChange, error }: { label: string; value: string; onChange: (v: string) => void; error?: string }) {
  return (
    <div className="field">
      <label>
        {label}
        <select className="input" value={value} aria-invalid={error ? true : undefined} onChange={(e) => onChange(e.target.value)}>
          {HALF_HOURS.map((t) => (
            <option key={t} value={t}>
              {t}
            </option>
          ))}
        </select>
      </label>
      {error && <span className="error" role="alert">{error}</span>}
    </div>
  )
}
