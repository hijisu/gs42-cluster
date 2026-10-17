import { useState } from 'react'
import { Button, Field, Modal } from '../../components'
import { ApiError } from '../../lib/api'
import { kstDate, kstToIso } from '../../lib/datetime'
import type { StaffMeeting } from './api'
import { usePropose } from './hooks'
import { errorLabel } from './labels'

export function ProposeModal({ meeting, onClose }: { meeting: StaffMeeting | null; onClose: () => void }) {
  const propose = usePropose()
  const [date, setDate] = useState('')
  const [time, setTime] = useState('')
  const [note, setNote] = useState('')
  const [submitted, setSubmitted] = useState(false)

  const close = () => {
    setDate('')
    setTime('')
    setNote('')
    setSubmitted(false)
    propose.reset()
    onClose()
  }
  const missing = date === '' || time === ''
  const error =
    propose.error instanceof ApiError ? (errorLabel[propose.error.code ?? ''] ?? '제안하지 못했어요. 잠시 후 다시 시도해 주세요.') : propose.isError ? '제안하지 못했어요.' : null

  return (
    <Modal
      open={meeting !== null}
      title="다른 시간 제안"
      onClose={close}
      actions={
        <>
          <Button variant="ghost" onClick={close}>
            취소
          </Button>
          <Button
            disabled={propose.isPending}
            onClick={() => {
              setSubmitted(true)
              if (!meeting || missing) return
              propose.mutate({ id: meeting.id, proposed_at: kstToIso(date, time), note: note.trim() || undefined }, { onSuccess: close })
            }}
          >
            {propose.isPending ? '제안 중…' : '시간 제안하기'}
          </Button>
        </>
      }
    >
      {meeting && <p className="muted small">{meeting.student.intra_id} 님에게 제안할 시간을 고르세요. 교육생이 확인하면 '시간 조율 중'으로 표시돼요. (희망 일시 {kstDate(meeting.slot_at)})</p>}
      <div className="g2" style={{ gap: 12 }}>
        <Field label="날짜" type="date" value={date} onChange={(e) => setDate(e.target.value)} error={submitted && date === '' ? '날짜를 선택해 주세요.' : undefined} />
        <Field label="시간" type="time" step={1800} value={time} onChange={(e) => setTime(e.target.value)} error={submitted && time === '' ? '시간을 선택해 주세요.' : undefined} />
      </div>
      <Field label="메모(선택)" value={note} onChange={(e) => setNote(e.target.value)} />
      {error && <p role="alert" className="login-error">{error}</p>}
    </Modal>
  )
}
