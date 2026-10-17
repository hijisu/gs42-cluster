import { useState } from 'react'
import { useMe } from '../auth/hooks'
import type { StaffMeeting, StaffMeetingStatus } from './api'
import { AvailabilityPanel } from './AvailabilityPanel'
import { DefaultStaffPanel } from './DefaultStaffPanel'
import { useMembers, useStaffMeetingTypes, useStaffMeetings, useTabCounts } from './hooks'
import { emptyLabel, tabs } from './labels'
import { ProposeModal } from './ProposeModal'
import { RequestCard } from './RequestCard'

export function StaffMeetingPage() {
  const [status, setStatus] = useState<StaffMeetingStatus>('pending')
  const [proposing, setProposing] = useState<{ meeting: StaffMeeting; location: string } | null>(null)
  const list = useStaffMeetings(status)
  const counts = useTabCounts()
  const members = useMembers()
  const types = useStaffMeetingTypes()
  const { data: me } = useMe()

  return (
    <>
      <div className="head">
        <div>
          <p className="label">01 · MEETING ADMIN</p>
          <h1 className="h1" style={{ marginTop: 8 }}>면담 관리</h1>
          <p className="sub">교육생이 신청한 대면 면담을 확인하고 담당자와 일정을 확정하세요. 확정하면 교육생 화면에 확정 일시·담당·장소가 표시돼요.</p>
        </div>
      </div>

      <div className="tabs" role="tablist" aria-label="면담 상태">
        {tabs.map((t) => (
          <button key={t.status} type="button" role="tab" aria-selected={status === t.status} className={status === t.status ? 'on' : ''} onClick={() => setStatus(t.status)}>
            {t.label}
            {t.counted && counts[t.status] !== undefined ? ` ${counts[t.status]}` : ''}
          </button>
        ))}
      </div>

      <div className="split">
        <div className="col" role="tabpanel">
          {list.isPending && <p className="muted" role="status">불러오는 중…</p>}
          {list.isError && <p role="alert">면담 요청을 불러오지 못했어요.</p>}
          {list.data?.length === 0 && <p className="muted">{emptyLabel[status]}</p>}
          {list.data?.map((m) => (
            <RequestCard key={m.id} meeting={m} members={members.data ?? []} types={types.data ?? []} meId={me?.id} onPropose={(meeting, location) => setProposing({ meeting, location })} />
          ))}
        </div>
        <div className="col">
          <AvailabilityPanel />
          {(types.isError || members.isError) && <p role="alert">담당자·유형 정보를 불러오지 못했어요. 새로고침해 주세요.</p>}
          {types.data && <DefaultStaffPanel types={types.data} members={members.data ?? []} />}
          <div className="info">
            <span className="label">비대면 면담</span>
            <span>#pedago에 올라온 비대면 신청은 이 화면을 거치지 않고 Slack DM으로 진행해요.</span>
          </div>
        </div>
      </div>
      <ProposeModal key={proposing?.meeting.id ?? 'none'} meeting={proposing?.meeting ?? null} defaultLocation={proposing?.location ?? ''} onClose={() => setProposing(null)} />
    </>
  )
}
