import { useState } from 'react'
import { Button, Card } from '../../components'
import { kstDateFromToday } from '../../lib/datetime'
import { Calendar } from '../room/Calendar'
import { useAvailability, useRooms, useRules } from '../room/hooks'
import { Timeline } from '../room/Timeline'
import { DirectModal } from './DirectModal'
import { useStaffPending } from './hooks'
import { PendingCard } from './PendingCard'
import { RejectModal } from './RejectModal'
import { RoomsPanel } from './RoomsPanel'
import { RulesPanel } from './RulesPanel'
import type { StaffReservation } from './api'

export function StaffRoomPage() {
  const [date, setDate] = useState(() => kstDateFromToday(0))
  const [rejecting, setRejecting] = useState<StaffReservation | null>(null)
  const [direct, setDirect] = useState(false)
  const pending = useStaffPending()
  const availability = useAvailability(date)
  const rooms = useRooms()
  const rules = useRules()

  return (
    <>
      <div className="head">
        <div>
          <p className="label">02 · ROOM ADMIN</p>
          <h1 className="h1" style={{ marginTop: 8 }}>회의실 관리</h1>
          <p className="sub">교육생의 예약 요청을 확인하고 승인하세요. 승인하면 교육생 화면에 이용수칙이 함께 표시됩니다.</p>
        </div>
      </div>

      <div className="room-split">
        <Card className="stack" style={{ gap: 16 }}>
          <h2 className="card-title">날짜 선택</h2>
          <Calendar selected={date} onSelect={setDate} allowPast />
          <Button variant="ghost" size="sm" onClick={() => setDirect(true)}>
            운영팀 직접 예약
          </Button>
        </Card>
        <div className="col">
          {availability.isPending && <p className="muted" role="status">회의실 현황을 불러오는 중…</p>}
          {availability.isError && <p role="alert">회의실 현황을 불러오지 못했어요.</p>}
          {availability.data && <Timeline date={date} data={availability.data} title="회의실 현황" />}
        </div>
      </div>

      <div className="split">
        <div className="col">
          <section className="col" style={{ gap: 12 }} aria-label="승인 대기">
            <h2 style={{ fontSize: 18 }}>승인 대기 {pending.data?.length ?? ''}</h2>
            {pending.isPending && <p className="muted" role="status">불러오는 중…</p>}
            {pending.isError && <p role="alert">예약 요청을 불러오지 못했어요.</p>}
            {pending.data?.length === 0 && <p className="muted">승인 대기 중인 요청이 없어요.</p>}
            {pending.data?.map((r) => (
              <PendingCard key={r.id} reservation={r} rooms={rooms.data ?? []} onReject={setRejecting} />
            ))}
          </section>
        </div>
        <div className="col">
          {(rules.isError || rooms.isError) && <p role="alert">이용수칙·장소 목록을 불러오지 못했어요.</p>}
          {(rules.isPending || rooms.isPending) && <p className="muted" role="status">이용수칙·장소 목록을 불러오는 중…</p>}
          {rules.data && <RulesPanel rules={rules.data} />}
          {rooms.data && <RoomsPanel rooms={rooms.data} />}
        </div>
      </div>

      <RejectModal reservation={rejecting} onClose={() => setRejecting(null)} />
      <DirectModal open={direct} date={date} rooms={rooms.data ?? []} onClose={() => setDirect(false)} />
    </>
  )
}
