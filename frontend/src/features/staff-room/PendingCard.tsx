import { useState } from 'react'
import { Button, Card, Pill } from '../../components'
import { formatDayLabel, formatTimeRange, kstDate, kstTime } from '../../lib/datetime'
import type { Availability, Room } from '../room/api'
import { useAvailability } from '../room/hooks'
import type { StaffReservation } from './api'
import { messageFor } from './errors'
import { useApprove, useReassign } from './hooks'

/** 요청 시간대(KST 시 단위)가 모두 비어 있는 장소만 대체 후보로 본다. 현황을 못 받았으면 열려 있는 다른 장소 전체. */
function candidateRooms(r: StaffReservation, rooms: Room[], availability: Availability | undefined): Room[] {
  const others = rooms.filter((x) => x.status === 'open' && x.id !== r.room.id)
  if (!availability) return others
  const from = Number(kstTime(r.start_at).slice(0, 2))
  const [eh, em] = kstTime(r.end_at).split(':').map(Number)
  const to = em > 0 ? eh + 1 : eh
  return others.filter((room) => {
    const row = availability.rooms.find((a) => a.room.id === room.id)
    return row?.hours.filter((h) => h.hour >= from && h.hour < to).every((h) => h.state === 'free') ?? false
  })
}

interface PendingCardProps {
  reservation: StaffReservation
  rooms: Room[]
  onReject: (r: StaffReservation) => void
}

export function PendingCard({ reservation: r, rooms, onReject }: PendingCardProps) {
  const approve = useApprove()
  const reassign = useReassign()
  // 요청 날짜의 현황으로 대체 후보를 계산한다(선택한 날짜와 다른 날 요청도 있다)
  const availability = useAvailability(kstDate(r.start_at))
  const candidates = candidateRooms(r, rooms, availability.data)
  const [altId, setAltId] = useState<number | null>(null)
  const alt = altId !== null && candidates.some((c) => c.id === altId) ? altId : (candidates[0]?.id ?? null)
  const conflict = r.conflict_ids.length > 0
  const error = messageFor(approve.error ?? reassign.error, '처리하지 못했어요. 잠시 후 다시 시도해 주세요.')
  const busy = approve.isPending || reassign.isPending

  return (
    <Card className="stack" data-testid={`pending-${r.id}`} style={conflict ? { border: '2px solid var(--c-ink)' } : undefined}>
      <div className="row">
        <span style={{ fontWeight: 700 }}>
          {r.user.intra_id} · {r.purpose}
        </span>
        <Pill tone={conflict ? 'wait' : 'ok'}>{conflict ? '시간 충돌' : '예약 가능'}</Pill>
      </div>
      <div className="g4" style={{ gap: 12, fontSize: 14 }}>
        <Item label="일시">
          {formatDayLabel(kstDate(r.start_at))} {formatTimeRange(r.start_at, r.end_at)}
        </Item>
        <Item label="장소">{r.room.name}</Item>
        <Item label="인원">{r.headcount}명</Item>
        <Item label="요청사항">{r.note || '없음'}</Item>
      </div>
      {conflict && (
        <div className="info" style={{ background: 'var(--c-warn-bg)', color: 'var(--c-warn-text)' }}>
          {r.room.name}은(는) 해당 시간에 겹치는 예약이 있어요.
          {candidates.length > 0 ? ` 같은 시간에 비어 있는 장소: ${candidates.map((c) => c.name).join(', ')}` : ' 같은 시간에 비어 있는 다른 장소가 없어요.'}
        </div>
      )}
      {error && <p role="alert" className="login-error">{error}</p>}
      <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end', flexWrap: 'wrap', alignItems: 'center' }}>
        {candidates.length > 0 && (
          <>
            <label htmlFor={`alt-${r.id}`} className="sr-only">대체 장소</label>
            <select id={`alt-${r.id}`} className="input" style={{ width: 200 }} value={alt ?? ''} onChange={(e) => setAltId(Number(e.target.value))}>
              {candidates.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name}
                </option>
              ))}
            </select>
            <Button size="sm" variant="ghost" disabled={busy || alt === null} onClick={() => alt !== null && reassign.mutate({ id: r.id, roomId: alt })}>
              대체 장소로 승인
            </Button>
          </>
        )}
        <Button size="sm" variant="warn" disabled={busy} onClick={() => onReject(r)}>
          반려
        </Button>
        <Button size="sm" variant="teal" disabled={busy} onClick={() => approve.mutate(r.id)}>
          {approve.isPending ? '승인 중…' : '승인 · 이용수칙 전송'}
        </Button>
      </div>
    </Card>
  )
}

function Item({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <span style={{ display: 'flex', flexDirection: 'column' }}>
      <span className="label">{label}</span>
      {children}
    </span>
  )
}
