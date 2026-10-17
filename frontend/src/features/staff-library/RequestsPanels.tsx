import { useState } from 'react'
import { Button, Card, Field, Modal, Pill } from '../../components'
import { formatMonthDay, kstDate } from '../../lib/datetime'
import type { BookWish } from './api'
import { messageFor } from './errors'
import { useReports, useResolveReport, useUpdateWish, useWishes } from './hooks'
import { ALREADY_OWNED_NOTE, reportKindLabel, wishStatusLabel } from './labels'

const day = (iso: string) => formatMonthDay(kstDate(iso))

export function WishesPanel() {
  const wishes = useWishes()
  const update = useUpdateWish()
  const [rejecting, setRejecting] = useState<BookWish | null>(null)
  const [reason, setReason] = useState('')
  const [submitted, setSubmitted] = useState(false)
  const error = messageFor(update.error, '처리하지 못했어요. 잠시 후 다시 시도해 주세요.')
  const closeReject = () => {
    setRejecting(null)
    setReason('')
    setSubmitted(false)
  }

  return (
    <Card className="stack" style={{ gap: 8 }}>
      <h2 className="card-title">희망 도서 신청 {wishes.data ? wishes.data.filter((w) => w.status === 'requested').length : ''}</h2>
      {wishes.isPending && <p className="muted" role="status">불러오는 중…</p>}
      {wishes.isError && <p role="alert">희망 도서를 불러오지 못했어요.</p>}
      {error && <p role="alert" className="login-error">{error}</p>}
      {wishes.data?.length === 0 && <p className="muted">접수된 희망 도서가 없어요.</p>}
      <ul className="stack" style={{ gap: 12, listStyle: 'none', padding: 0, margin: 0 }}>
        {wishes.data?.map((w) => {
          const s = wishStatusLabel[w.status]
          const open = w.status === 'requested' || w.status === 'approved'
          return (
            <li key={w.id} className="stack" style={{ gap: 4 }} aria-label={`희망 도서 ${w.title}`}>
              <div style={{ display: 'flex', justifyContent: 'space-between', gap: 8 }}>
                <strong>{w.title}</strong>
                <Pill tone={s.tone}>{s.label}</Pill>
              </div>
              <p className="muted small">{w.requester.intra_id} · {day(w.created_at)}{w.author ? ` · ${w.author}` : ''}{w.reason ? ` — ${w.reason}` : ''}</p>
              {w.staff_note && <p className="small">메모: {w.staff_note}</p>}
              {open && (
                <span style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                  {w.status === 'requested' && <Button variant="ghost" size="sm" disabled={update.isPending} aria-label={`${w.title} 검토 중으로`} onClick={() => update.mutate({ id: w.id, status: 'approved' })}>검토 중</Button>}
                  {w.status === 'approved' && <Button variant="teal" size="sm" disabled={update.isPending} aria-label={`${w.title} 구매 확정`} onClick={() => update.mutate({ id: w.id, status: 'purchased' })}>구매 확정</Button>}
                  <Button variant="ghost" size="sm" disabled={update.isPending} aria-label={`${w.title} 이미 비치됨`} onClick={() => update.mutate({ id: w.id, status: 'rejected', note: ALREADY_OWNED_NOTE })}>이미 비치됨</Button>
                  <Button variant="ghost" size="sm" aria-label={`${w.title} 반려`} onClick={() => setRejecting(w)}>반려</Button>
                </span>
              )}
            </li>
          )
        })}
      </ul>
      <Modal
        open={rejecting !== null}
        title="희망 도서 반려"
        onClose={closeReject}
        actions={
          <>
            <Button variant="ghost" onClick={closeReject}>돌아가기</Button>
            <Button
              variant="warn"
              disabled={update.isPending}
              onClick={() => {
                setSubmitted(true)
                if (!rejecting || reason.trim() === '') return
                update.mutate({ id: rejecting.id, status: 'rejected', note: reason.trim() }, { onSuccess: closeReject })
              }}
            >
              반려
            </Button>
          </>
        }
      >
        {rejecting && <p className="muted small">{rejecting.requester.intra_id} · {rejecting.title}</p>}
        <Field label="반려 사유" multiline value={reason} onChange={(e) => setReason(e.target.value)} error={submitted && reason.trim() === '' ? '반려 사유를 입력해 주세요.' : undefined} />
      </Modal>
    </Card>
  )
}

export function ReportsPanel() {
  const reports = useReports()
  const resolve = useResolveReport()
  const open = reports.data?.filter((r) => r.status === 'received') ?? []
  const error = messageFor(resolve.error, '처리하지 못했어요. 잠시 후 다시 시도해 주세요.')
  return (
    <Card className="stack" style={{ gap: 8 }}>
      <h2 className="card-title">분실 · 훼손 신고 {reports.data ? open.length : ''}</h2>
      {reports.isPending && <p className="muted" role="status">불러오는 중…</p>}
      {reports.isError && <p role="alert">신고를 불러오지 못했어요.</p>}
      {error && <p role="alert" className="login-error">{error}</p>}
      {reports.data && open.length === 0 && <p className="muted">확인할 신고가 없어요.</p>}
      <ul className="stack" style={{ gap: 12, listStyle: 'none', padding: 0, margin: 0 }}>
        {open.map((r) => (
          <li key={r.id} className="stack" style={{ gap: 4 }} aria-label={`신고 ${r.book_title}`}>
            <div style={{ display: 'flex', justifyContent: 'space-between', gap: 8 }}>
              <strong>{r.book_title}</strong>
              <Pill tone="wait">{reportKindLabel[r.kind]}</Pill>
            </div>
            <p className="muted small">신고 {r.reporter.intra_id} · {day(r.created_at)}{r.detail ? ` — ${r.detail}` : ''}</p>
            <span>
              <Button variant="ghost" size="sm" disabled={resolve.isPending} aria-label={`${r.book_title} 처리 완료`} onClick={() => resolve.mutate(r.id)}>처리 완료</Button>
            </span>
          </li>
        ))}
      </ul>
    </Card>
  )
}
