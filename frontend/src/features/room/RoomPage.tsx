import { useState, type FormEvent } from 'react'
import { Button, Card, Field } from '../../components'
import { ApiError } from '../../lib/api'
import { kstDateFromToday, kstToIso } from '../../lib/datetime'
import { Calendar } from './Calendar'
import { useAvailability, useCreateReservation, useRooms } from './hooks'
import { errorLabel } from './labels'
import { MyReservations } from './MyReservations'
import { Timeline } from './Timeline'

export function RoomPage() {
  const [date, setDate] = useState(() => kstDateFromToday(0))
  const [start, setStart] = useState('15:00')
  const [end, setEnd] = useState('16:00')
  const [roomId, setRoomId] = useState<number | ''>('')
  const [purpose, setPurpose] = useState('')
  const [headcount, setHeadcount] = useState('')
  const [note, setNote] = useState('')
  const [submitted, setSubmitted] = useState(false)

  const rooms = useRooms()
  const availability = useAvailability(date)
  const create = useCreateReservation()

  const openRooms = rooms.data?.filter((r) => r.status === 'open') ?? []
  const selectedRoomId: number | undefined = roomId === '' ? openRooms[0]?.id : roomId
  const count = Number(headcount)

  const errors = {
    time: start === '' || end === '' || end <= start ? '종료 시간은 시작 시간보다 늦어야 합니다.' : undefined,
    purpose: purpose.trim() === '' ? '목적을 입력해 주세요.' : undefined,
    headcount: !Number.isInteger(count) || count < 1 || count > 100 ? '인원은 1~100명으로 입력해 주세요.' : undefined,
  }
  const hasError = Object.values(errors).some(Boolean) || selectedRoomId === undefined

  const submitError =
    create.error instanceof ApiError
      ? (errorLabel[create.error.code ?? ''] ?? '요청하지 못했습니다. 잠시 후 다시 시도해 주세요.')
      : create.isError
        ? '요청하지 못했습니다. 잠시 후 다시 시도해 주세요.'
        : null

  function onSubmit(e: FormEvent) {
    e.preventDefault()
    setSubmitted(true)
    if (hasError || selectedRoomId === undefined) return
    create.mutate(
      {
        room_id: selectedRoomId,
        start_at: kstToIso(date, start),
        end_at: kstToIso(date, end),
        purpose: purpose.trim(),
        headcount: count,
        note: note.trim(),
      },
      {
        onSuccess: () => {
          setPurpose('')
          setHeadcount('')
          setNote('')
          setSubmitted(false)
        },
      },
    )
  }

  return (
    <>
      <div className="head">
        <div>
          <p className="label">02 · ROOMS</p>
          <h1 className="h1" style={{ marginTop: 8 }}>회의실 예약</h1>
          <p className="sub">날짜와 시간을 고르고 예약을 요청하세요. 교육운영팀이 승인하면 알림과 함께 이용수칙을 안내해 드려요.</p>
        </div>
      </div>

      <div className="split room-split">
        <Card>
          <form className="stack" style={{ gap: 16 }} onSubmit={onSubmit} noValidate>
            <h2 className="card-title">예약 요청</h2>
            <Calendar selected={date} onSelect={setDate} />
            <div className="g2" style={{ gap: 12 }}>
              <Field label="시작" type="time" step={1800} value={start} onChange={(e) => setStart(e.target.value)} />
              <Field label="종료" type="time" step={1800} value={end} onChange={(e) => setEnd(e.target.value)} error={submitted ? errors.time : undefined} />
            </div>
            <div className="field">
              <label htmlFor="room-select">장소</label>
              <select id="room-select" className="input" value={selectedRoomId ?? ''} onChange={(e) => setRoomId(Number(e.target.value))}>
                {openRooms.map((r) => (
                  <option key={r.id} value={r.id}>
                    {r.name}
                  </option>
                ))}
              </select>
            </div>
            <div className="g2" style={{ gap: 12 }}>
              <Field label="목적" value={purpose} onChange={(e) => setPurpose(e.target.value)} error={submitted ? errors.purpose : undefined} />
              <Field label="인원" type="number" min={1} max={100} value={headcount} onChange={(e) => setHeadcount(e.target.value)} error={submitted ? errors.headcount : undefined} />
            </div>
            <Field label="기타 요청사항" placeholder="예: HDMI 케이블 필요" value={note} onChange={(e) => setNote(e.target.value)} />
            {submitError && <p role="alert" className="login-error">{submitError}</p>}
            <Button type="submit" disabled={create.isPending}>
              {create.isPending ? '요청 중…' : '예약 요청하기'}
            </Button>
            <p className="muted small">요청 후 운영팀 승인 전까지는 &lsquo;승인 대기&rsquo; 상태예요.</p>
          </form>
        </Card>

        <div className="col">
          {availability.isPending && <p className="muted" role="status">불러오는 중…</p>}
          {availability.isError && <p role="alert">예약 현황을 불러오지 못했습니다.</p>}
          {availability.data && <Timeline date={date} data={availability.data} />}
          <MyReservations />
        </div>
      </div>
    </>
  )
}
