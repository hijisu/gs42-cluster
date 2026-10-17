import { useState } from 'react'
import { Button, Field, Modal } from '../../components'
import type { StaffReservation } from './api'
import { messageFor } from './errors'
import { useReject } from './hooks'

export function RejectModal({ reservation, onClose }: { reservation: StaffReservation | null; onClose: () => void }) {
  const reject = useReject()
  const [reason, setReason] = useState('')
  const [submitted, setSubmitted] = useState(false)
  const close = () => {
    setReason('')
    setSubmitted(false)
    reject.reset()
    onClose()
  }
  const error = messageFor(reject.error, '반려하지 못했어요. 잠시 후 다시 시도해 주세요.')
  return (
    <Modal
      open={reservation !== null}
      title="예약 요청 반려"
      onClose={close}
      actions={
        <>
          <Button variant="secondary" onClick={close}>
            돌아가기
          </Button>
          <Button
            variant="danger"
            disabled={reject.isPending}
            onClick={() => {
              setSubmitted(true)
              if (!reservation || reason.trim() === '') return
              reject.mutate({ id: reservation.id, reason: reason.trim() }, { onSuccess: close })
            }}
          >
            {reject.isPending ? '반려 중…' : '반려'}
          </Button>
        </>
      }
    >
      {reservation && <p className="muted small">{reservation.user.intra_id} · {reservation.purpose} — 사유는 교육생에게 그대로 보여요.</p>}
      <Field label="반려 사유" multiline value={reason} onChange={(e) => setReason(e.target.value)} placeholder="예: 해당 시간 기존 예약" error={submitted && reason.trim() === '' ? '반려 사유를 입력해 주세요.' : undefined} />
      {error && <p role="alert" className="login-error">{error}</p>}
    </Modal>
  )
}
