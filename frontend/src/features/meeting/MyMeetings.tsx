import { useState } from 'react'
import { Button, Card, Modal, Pill } from '../../components'
import { ApiError } from '../../lib/api'
import { formatDateTime } from '../../lib/datetime'
import type { Meeting } from './api'
import { useAcceptMeetingProposal, useCancelMeeting, useMyMeetings } from './hooks'
import { cancelable, errorLabel, statusLabel, statusTone } from './labels'

export function MyMeetings() {
  const { data, isPending, isError } = useMyMeetings()
  const cancel = useCancelMeeting()
  const accept = useAcceptMeetingProposal()
  const [target, setTarget] = useState<Meeting | null>(null)

  const cancelError =
    cancel.error instanceof ApiError ? (errorLabel[cancel.error.code ?? ''] ?? '취소하지 못했습니다. 잠시 후 다시 시도해 주세요.') : cancel.isError ? '취소하지 못했습니다.' : null

  const close = () => {
    setTarget(null)
    cancel.reset()
  }

  return (
    <Card style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
      <h2 className="card-title">내 면담 신청</h2>
      {isPending && <p className="muted" role="status">불러오는 중…</p>}
      {isError && <p role="alert">신청 내역을 불러오지 못했습니다.</p>}
      {data?.length === 0 && <p className="muted">신청한 면담이 없습니다.</p>}
      <ul className="list" aria-label="내 면담 신청 내역" style={{ listStyle: 'none', padding: 0, margin: 0 }}>
        {data?.map((m) => (
          <li key={m.id} className="my-meeting" data-testid={`meeting-${m.id}`}>
            <span className="stack" style={{ gap: 2, minWidth: 0 }}>
              <span className="small">
                <b className="mono">{formatDateTime(m.slot_at)}</b> · {m.type.name}
              </span>
              <span className="muted small">
                {m.staff?.name ?? '배정 중'}
                {m.location ? ` · ${m.location}` : ''}
                {m.status === 'proposed' && m.proposed_at ? ` · 제안 ${formatDateTime(m.proposed_at)}` : ''}
              </span>
            </span>
            <span className="my-meeting-end">
              <Pill tone={statusTone[m.status]}>{statusLabel[m.status]}</Pill>
              {m.status === 'proposed' && m.proposed_at && (
                <Button size="sm" disabled={accept.isPending} onClick={() => accept.mutate(m.id)}>
                  제안 수락(확정하기)
                </Button>
              )}
              {cancelable(m.status) && (
                <Button variant="danger" size="sm" aria-label={`${formatDateTime(m.slot_at)} ${m.type.name} 취소`} onClick={() => setTarget(m)}>
                  취소
                </Button>
              )}
            </span>
          </li>
        ))}
      </ul>
      <p className="muted small">확정된 면담은 취소할 수 없어요. 변경이 필요하면 Slack #pedago로 문의해 주세요.</p>
      {accept.isError && <p role="alert">제안을 수락하지 못했습니다. 시간 충돌 또는 만료 여부를 확인해 주세요.</p>}
      <Modal
        open={target !== null}
        title="면담을 취소할까요?"
        onClose={close}
        actions={
          <>
            <Button variant="secondary" onClick={close}>
              돌아가기
            </Button>
            <Button
              variant="danger"
              disabled={cancel.isPending}
              onClick={() => target && cancel.mutate(target.id, { onSuccess: close })}
            >
              면담 취소
            </Button>
          </>
        }
      >
        {target && (
          <p>
            {formatDateTime(target.slot_at)} · {target.type.name}
          </p>
        )}
        {cancelError && <p role="alert" className="login-error">{cancelError}</p>}
      </Modal>
    </Card>
  )
}
