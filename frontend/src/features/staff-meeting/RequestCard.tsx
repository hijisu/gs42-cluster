import { useState } from 'react'
import { Button, Card, Field, Pill } from '../../components'
import { ApiError } from '../../lib/api'
import { formatDateTimeLong, timeAgo } from '../../lib/datetime'
import { statusLabel } from '../meeting/labels'
import type { StaffMeeting, StaffMember, StaffMeetingType } from './api'
import { useConfirm } from './hooks'
import { DEFAULT_LOCATION, errorLabel } from './labels'

interface RequestCardProps {
  meeting: StaffMeeting
  members: StaffMember[]
  types: StaffMeetingType[]
  meId: number | undefined
  /** 제안 모달을 연다. 카드에 입력한 장소를 기본값으로 넘긴다. */
  onPropose: (m: StaffMeeting, location: string) => void
}

export function RequestCard({ meeting, members, types, meId, onPropose }: RequestCardProps) {
  const confirm = useConfirm()
  const open = meeting.status === 'pending' || meeting.status === 'proposed'
  const defaultStaff = types.find((t) => t.id === meeting.type.id)?.default_staff?.id
  const [staffId, setStaffId] = useState<number | undefined>(meeting.staff?.id ?? defaultStaff ?? meId)
  const [location, setLocation] = useState(meeting.location || DEFAULT_LOCATION)
  const [submitted, setSubmitted] = useState(false)

  const error =
    confirm.error instanceof ApiError ? (errorLabel[confirm.error.code ?? ''] ?? '확정하지 못했어요. 잠시 후 다시 시도해 주세요.') : confirm.isError ? '확정하지 못했어요.' : null
  const proposed = meeting.status === 'proposed' && meeting.proposed_at

  return (
    <Card className="stack" data-testid={`meeting-${meeting.id}`} style={meeting.status === 'pending' ? { border: '2px solid var(--c-ink)' } : undefined}>
      <div className="row">
        <span style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
          <span className="av" style={{ width: 32, height: 32, fontSize: 12 }}>{meeting.student.intra_id.slice(0, 2).toUpperCase()}</span>
          <span style={{ display: 'flex', flexDirection: 'column' }}>
            <span style={{ fontWeight: 700 }}>{meeting.student.intra_id}</span>
            <span className="muted" style={{ fontSize: 12 }}>신청 {timeAgo(meeting.created_at)}</span>
          </span>
        </span>
        <span style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          {!open && <Pill tone={meeting.status === 'confirmed' ? 'ok' : 'neu'}>{statusLabel[meeting.status]}</Pill>}
          <Pill tone="wait">{meeting.type.name}</Pill>
        </span>
      </div>
      <p className="body-sm">{meeting.content}</p>

      {open ? (
        <>
          <div className="g3" style={{ gap: 12, alignItems: 'end' }}>
            <div className="field">
              <span className="field-label">희망 일시</span>
              <span className="mono" style={{ minHeight: 44, display: 'flex', alignItems: 'center' }}>{formatDateTimeLong(meeting.slot_at)}</span>
              {proposed && <span className="muted small">제안한 시간 {formatDateTimeLong(meeting.proposed_at!)} (확정하면 이 시간으로 확정돼요)</span>}
            </div>
            <div className="field">
              <label htmlFor={`staff-${meeting.id}`}>담당자</label>
              <select id={`staff-${meeting.id}`} className="input" value={staffId ?? ''} onChange={(e) => setStaffId(e.target.value === '' ? undefined : Number(e.target.value))}>
                {members.map((m) => (
                  <option key={m.id} value={m.id}>
                    {m.name}
                  </option>
                ))}
              </select>
            </div>
            <Field
              label="장소"
              value={location}
              onChange={(e) => setLocation(e.target.value)}
              error={submitted && location.trim() === '' ? '장소를 입력해 주세요.' : undefined}
            />
          </div>
          {error && <p role="alert" className="login-error">{error}</p>}
          <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end', flexWrap: 'wrap' }}>
            <Button variant="ghost" size="sm" onClick={() => onPropose(meeting, location.trim())}>
              다른 시간 제안
            </Button>
            <Button
              size="sm"
              disabled={confirm.isPending}
              onClick={() => {
                setSubmitted(true)
                if (location.trim() === '') return
                confirm.mutate({ id: meeting.id, location: location.trim(), staff_id: staffId })
              }}
            >
              {confirm.isPending ? '확정 중…' : proposed ? '제안한 시간으로 확정' : '희망 일시로 확정'}
            </Button>
          </div>
        </>
      ) : (
        <div className="g3" style={{ gap: 12 }}>
          <div className="field"><span className="field-label">일시</span><span className="mono">{formatDateTimeLong(meeting.slot_at)}</span></div>
          <div className="field"><span className="field-label">담당자</span><span>{meeting.staff?.name ?? '-'}</span></div>
          <div className="field"><span className="field-label">장소</span><span>{meeting.location || '-'}</span></div>
        </div>
      )}
    </Card>
  )
}
