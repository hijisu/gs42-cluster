import { Card, Pill } from '../../components'
import { reportKindLabel, reportStatusLabel, reportStatusTone, wishStatusLabel, wishStatusTone } from './labels'
import { useMyRequests } from './hooks'

/** 내 신청(희망 도서) · 신고(분실·훼손) 내역과 처리 상태 */
export function MyRequests() {
  const { data, isPending, isError } = useMyRequests()
  const empty = data && data.wishes.length === 0 && data.reports.length === 0
  return (
    <Card className="stack" style={{ gap: 8 }}>
      <h2 className="card-title">내 신청 · 신고</h2>
      {isPending && <p className="muted body-sm" role="status">불러오는 중…</p>}
      {isError && <p role="alert" className="body-sm">내역을 불러오지 못했어요.</p>}
      {empty && <p className="muted body-sm">신청하거나 신고한 내역이 없어요.</p>}
      <div className="list">
        {data?.wishes.map((w) => (
          <div key={`wish-${w.id}`} className="row" data-testid={`wish-${w.id}`}>
            <span style={{ display: 'flex', flexDirection: 'column', minWidth: 0 }}>
              <span className="body-sm">{w.title} · 희망 도서</span>
              {w.status === 'rejected' && w.staff_note && <span className="muted small">반려 사유: {w.staff_note}</span>}
            </span>
            <Pill tone={wishStatusTone[w.status]}>{wishStatusLabel[w.status]}</Pill>
          </div>
        ))}
        {data?.reports.map((r) => (
          <div key={`report-${r.id}`} className="row" data-testid={`report-${r.id}`}>
            <span className="body-sm">{r.book_title} · {reportKindLabel[r.kind]}</span>
            <Pill tone={reportStatusTone[r.status]}>{reportStatusLabel[r.status]}</Pill>
          </div>
        ))}
      </div>
    </Card>
  )
}
