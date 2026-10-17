import { useState } from 'react'
import { Button, Chip, Field, Modal } from '../../components'
import { ApiError } from '../../lib/api'
import type { Book, ReportKind } from './api'
import { useCreateReport } from './hooks'
import { errorLabel, reportKindOption } from './labels'

/** 분실·훼손 신고. 훼손은 내용 필수. */
export function ReportModal({ book, onClose }: { book: Book | null; onClose: () => void }) {
  const create = useCreateReport()
  const [kind, setKind] = useState<ReportKind>('lost')
  const [detail, setDetail] = useState('')
  const [submitted, setSubmitted] = useState(false)
  const [done, setDone] = useState(false)

  const close = () => {
    setKind('lost')
    setDetail('')
    setSubmitted(false)
    setDone(false)
    create.reset()
    onClose()
  }
  const detailError = submitted && kind === 'damaged' && detail.trim() === '' ? '훼손된 내용을 적어 주세요.' : undefined
  const error =
    create.error instanceof ApiError ? (errorLabel[create.error.code ?? ''] ?? '신고하지 못했어요. 잠시 후 다시 시도해 주세요.') : create.isError ? '신고하지 못했어요.' : null

  return (
    <Modal
      open={book !== null}
      title="분실 · 훼손 신고"
      onClose={close}
      actions={
        done ? (
          <Button onClick={close}>닫기</Button>
        ) : (
          <>
            <Button variant="secondary" onClick={close}>
              취소
            </Button>
            <Button
              disabled={create.isPending}
              onClick={() => {
                setSubmitted(true)
                if (!book || (kind === 'damaged' && detail.trim() === '')) return
                create.mutate({ book_id: book.id, kind, detail: detail.trim() }, { onSuccess: () => setDone(true) })
              }}
            >
              {create.isPending ? '신고 중…' : '신고하기'}
            </Button>
          </>
        )
      }
    >
      {book && <p className="body-sm"><b>{book.title}</b></p>}
      {done ? (
        <p role="status" className="info">신고가 접수됐어요. 운영팀이 확인하면 '내 신청 · 신고'에 처리 상태가 표시돼요.</p>
      ) : (
        <>
          <div className="chips" role="group" aria-label="신고 유형">
            {(Object.keys(reportKindOption) as ReportKind[]).map((k) => (
              <Chip key={k} selected={kind === k} onClick={() => setKind(k)}>
                {reportKindOption[k]}
              </Chip>
            ))}
          </div>
          <Field
            label={kind === 'damaged' ? '훼손 내용' : '발견 위치 · 메모(선택)'}
            multiline
            placeholder={kind === 'damaged' ? '예: 표지가 찢어졌어요' : '예: 클러스터 2층 C열 책상에서 발견'}
            value={detail}
            onChange={(e) => setDetail(e.target.value)}
            error={detailError}
          />
          {error && <p role="alert" className="login-error">{error}</p>}
        </>
      )}
    </Modal>
  )
}
