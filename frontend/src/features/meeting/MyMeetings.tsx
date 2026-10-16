import { useState } from 'react'
import { Button, Card, Modal, Pill, Table, type Column } from '../../components'
import { ApiError } from '../../lib/api'
import { formatDateTime } from '../../lib/datetime'
import type { Meeting } from './api'
import { useCancelMeeting, useMyMeetings } from './hooks'
import { cancelable, errorLabel, statusLabel, statusTone } from './labels'

export function MyMeetings() {
  const { data, isPending, isError } = useMyMeetings()
  const cancel = useCancelMeeting()
  const [target, setTarget] = useState<Meeting | null>(null)

  const columns: Column<Meeting>[] = [
    { key: 'at', header: '일시', render: (m) => <span className="mono">{formatDateTime(m.slot_at)}</span> },
    { key: 'type', header: '유형', render: (m) => m.type.name },
    { key: 'staff', header: '담당', render: (m) => m.staff?.name ?? '배정 중' },
    { key: 'loc', header: '장소', render: (m) => m.location || '-' },
    { key: 'status', header: '상태', render: (m) => <Pill tone={statusTone[m.status]}>{statusLabel[m.status]}</Pill> },
    {
      key: 'act',
      header: '',
      render: (m) =>
        cancelable(m.status) ? (
          <Button variant="ghost" size="sm" aria-label={`${formatDateTime(m.slot_at)} ${m.type.name} 취소`} onClick={() => setTarget(m)}>
            취소
          </Button>
        ) : null,
    },
  ]

  const cancelError =
    cancel.error instanceof ApiError ? (errorLabel[cancel.error.code ?? ''] ?? '취소하지 못했습니다. 잠시 후 다시 시도해 주세요.') : cancel.isError ? '취소하지 못했습니다.' : null

  const close = () => {
    setTarget(null)
    cancel.reset()
  }

  return (
    <Card style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
      <h2 className="card-title">내 신청 내역</h2>
      {isPending && <p className="muted" role="status">불러오는 중…</p>}
      {isError && <p role="alert">신청 내역을 불러오지 못했습니다.</p>}
      {data && <Table caption="내 면담 신청 내역" columns={columns} rows={data} rowKey={(m) => m.id} empty="신청한 면담이 없습니다." />}
      <Modal
        open={target !== null}
        title="면담을 취소할까요?"
        onClose={close}
        actions={
          <>
            <Button variant="ghost" onClick={close}>
              돌아가기
            </Button>
            <Button
              variant="warn"
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
