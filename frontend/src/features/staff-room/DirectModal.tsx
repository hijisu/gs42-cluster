import { useState } from 'react'
import { Button, Field, Modal } from '../../components'
import { kstToIso } from '../../lib/datetime'
import type { Room } from '../room/api'
import { messageFor } from './errors'
import { useCreateDirect } from './hooks'

/** 운영팀 직접 예약: 만들면 바로 승인된다(본인 명의). */
export function DirectModal({ open, date, rooms, onClose }: { open: boolean; date: string; rooms: Room[]; onClose: () => void }) {
  const create = useCreateDirect()
  const openRooms = rooms.filter((r) => r.status === 'open')
  const [roomId, setRoomId] = useState<number | null>(null)
  const [start, setStart] = useState('10:00')
  const [end, setEnd] = useState('11:00')
  const [purpose, setPurpose] = useState('')
  const [headcount, setHeadcount] = useState('')
  const [note, setNote] = useState('')
  const [submitted, setSubmitted] = useState(false)

  const selected = roomId ?? openRooms[0]?.id ?? null
  const count = Number(headcount)
  const errors = {
    time: end <= start ? '종료 시간은 시작 시간보다 늦어야 합니다.' : undefined,
    purpose: purpose.trim() === '' ? '목적을 입력해 주세요.' : undefined,
    headcount: !Number.isInteger(count) || count < 1 || count > 100 ? '인원은 1~100명으로 입력해 주세요.' : undefined,
  }
  const close = () => {
    setPurpose('')
    setHeadcount('')
    setNote('')
    setSubmitted(false)
    create.reset()
    onClose()
  }
  const error = messageFor(create.error, '예약하지 못했어요. 잠시 후 다시 시도해 주세요.')

  return (
    <Modal
      open={open}
      title="운영팀 직접 예약"
      onClose={close}
      actions={
        <>
          <Button variant="secondary" onClick={close}>
            취소
          </Button>
          <Button
            disabled={create.isPending}
            onClick={() => {
              setSubmitted(true)
              if (selected === null || errors.time || errors.purpose || errors.headcount) return
              create.mutate(
                { room_id: selected, start_at: kstToIso(date, start), end_at: kstToIso(date, end), purpose: purpose.trim(), headcount: count, note: note.trim() },
                { onSuccess: close },
              )
            }}
          >
            {create.isPending ? '예약 중…' : '바로 예약'}
          </Button>
        </>
      }
    >
      <p className="muted small">{date} 날짜로 바로 승인된 예약을 만들어요.</p>
      <div className="field">
        <label htmlFor="direct-room">장소</label>
        <select id="direct-room" className="input" value={selected ?? ''} onChange={(e) => setRoomId(Number(e.target.value))}>
          {openRooms.map((r) => (
            <option key={r.id} value={r.id}>
              {r.name}
            </option>
          ))}
        </select>
      </div>
      <div className="g2" style={{ gap: 12 }}>
        <Field label="시작" type="time" step={1800} value={start} onChange={(e) => setStart(e.target.value)} />
        <Field label="종료" type="time" step={1800} value={end} onChange={(e) => setEnd(e.target.value)} error={submitted ? errors.time : undefined} />
      </div>
      <div className="g2" style={{ gap: 12 }}>
        <Field label="목적" value={purpose} onChange={(e) => setPurpose(e.target.value)} error={submitted ? errors.purpose : undefined} />
        <Field label="인원" type="number" min={1} max={100} value={headcount} onChange={(e) => setHeadcount(e.target.value)} error={submitted ? errors.headcount : undefined} />
      </div>
      <Field label="메모" value={note} onChange={(e) => setNote(e.target.value)} />
      {error && <p role="alert" className="login-error">{error}</p>}
    </Modal>
  )
}
