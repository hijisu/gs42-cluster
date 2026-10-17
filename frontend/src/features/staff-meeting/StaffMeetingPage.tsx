import { useState } from 'react'
import { useMe } from '../auth/hooks'
import type { StaffMeeting, StaffMeetingStatus } from './api'
import { AvailabilityPanel } from './AvailabilityPanel'
import { DefaultStaffPanel } from './DefaultStaffPanel'
import { useMembers, useStaffMeetingTypes, useStaffMeetings, useTabCounts } from './hooks'
import { emptyLabel, tabs } from './labels'
import { ProposeModal } from './ProposeModal'
import { RequestCard } from './RequestCard'

type SettingsTab = 'availability' | 'default-staff'

export function StaffMeetingPage() {
  const [settings, setSettings] = useState<SettingsTab>('availability')
  const [status, setStatus] = useState<StaffMeetingStatus>('pending')
  const [proposing, setProposing] = useState<{ meeting: StaffMeeting; location: string } | null>(null)
  const list = useStaffMeetings(status)
  const counts = useTabCounts()
  const members = useMembers()
  const types = useStaffMeetingTypes()
  const { data: me } = useMe()

  const settingsTabs = (
    <div className="tabs compact" role="tablist" aria-label="면담 설정">
      <button type="button" role="tab" aria-selected={settings === 'availability'} className={settings === 'availability' ? 'on' : ''} onClick={() => setSettings('availability')}>
        내 면담 가능 시간
      </button>
      <button type="button" role="tab" aria-selected={settings === 'default-staff'} className={settings === 'default-staff' ? 'on' : ''} onClick={() => setSettings('default-staff')}>
        유형별 기본 담당자
      </button>
    </div>
  )

  return (
    <>
      <div className="head">
        <div>
          <p className="label">01 · MEETING ADMIN</p>
          <h1 className="h1" style={{ marginTop: 2 }}>면담 관리</h1>
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
          <div className="info">
            <span className="label">비대면 면담</span>
            <span>#pedago에 올라온 비대면 신청은 이 화면을 거치지 않고 Slack DM으로 진행해요.</span>
          </div>
        </div>
        <div className="col">
          {/* 두 설정을 한 카드의 탭으로 합친다. 비활성 탭도 마운트해 두어 저장 전 편집이 사라지지 않는다. */}
          <div hidden={settings !== 'availability'}>
            <AvailabilityPanel tabs={settingsTabs} />
          </div>
          {(types.isError || members.isError) && <p role="alert">담당자·유형 정보를 불러오지 못했어요. 새로고침해 주세요.</p>}
          {types.data && (
            <div hidden={settings !== 'default-staff'}>
              <DefaultStaffPanel types={types.data} members={members.data ?? []} tabs={settingsTabs} />
            </div>
          )}
        </div>
      </div>
      <ProposeModal key={proposing?.meeting.id ?? 'none'} meeting={proposing?.meeting ?? null} defaultLocation={proposing?.location ?? ''} onClose={() => setProposing(null)} />
    </>
  )
}
