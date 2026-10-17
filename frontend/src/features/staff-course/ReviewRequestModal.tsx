import { useState } from 'react'
import { Button, Field, Modal } from '../../components'
import type { ReviewRequestResult, StaffCourse } from './api'
import { messageFor } from './errors'
import { useSendRequest } from './hooks'

const defaultMessage = (name: string) => `${name}에 참여해 주셔서 감사합니다. 다음 교육생을 위해 후기를 남겨 주세요.`

/** 후기 요청 보내기(팝업). course가 null이면 닫혀 있다. */
export function ReviewRequestModal({ course, onClose }: { course: StaffCourse | null; onClose: () => void }) {
  return (
    <Modal open={course !== null} title="후기 요청 보내기" onClose={onClose}>
      {/* 과정이 바뀌면 문구·마감일을 그 과정 기준으로 다시 채운다. */}
      {course && <Body key={course.id} course={course} onClose={onClose} />}
    </Modal>
  )
}

function Body({ course, onClose }: { course: StaffCourse; onClose: () => void }) {
  const send = useSendRequest()
  const [message, setMessage] = useState(defaultMessage(course.name))
  const [deadline, setDeadline] = useState(course.review_deadline ?? '')
  const [result, setResult] = useState<ReviewRequestResult | null>(null)
  const error = messageFor(send.error, '보내지 못했어요. 잠시 후 다시 시도해 주세요.')

  const submit = (target: 'all' | 'pending') => {
    setResult(null)
    send.mutate({ course, deadline: deadline || null, target, message }, { onSuccess: setResult })
  }

  return (
    <div className="stack">
      <Field label="교육과정" value={course.name} readOnly />
      <div className="g2" style={{ gap: 12 }}>
        <div className="info">
          <span className="label">작성 완료</span>
          <span className="mono stat">{course.reviewed_count}명</span>
        </div>
        <div className="info">
          <span className="label">미작성</span>
          <span className="mono stat">{course.pending_count}명</span>
        </div>
      </div>
      <Field label="알림 문구" multiline value={message} onChange={(e) => setMessage(e.target.value)} />
      <Field label="작성 마감" type="date" value={deadline} onChange={(e) => setDeadline(e.target.value)} />
      {error && <p role="alert" className="login-error">{error}</p>}
      {result && (
        <p role="status" className="info">
          {result.recipient_count > 0 ? `${result.recipient_count}명에게 후기 요청을 보냈어요.` : '보낼 대상이 없어요.'}
        </p>
      )}
      <div className="modal-actions" style={{ flexWrap: 'wrap' }}>
        <Button variant="ghost" onClick={onClose}>
          닫기
        </Button>
        <Button variant="ghost" disabled={send.isPending} onClick={() => submit('all')}>
          전체에게 보내기
        </Button>
        <Button variant="teal" disabled={send.isPending} onClick={() => submit('pending')}>
          미작성자에게 보내기
        </Button>
      </div>
      <p className="muted small">참여자의 앱 안 알림으로 전송됩니다. (푸시·Slack은 이후 단계)</p>
    </div>
  )
}
