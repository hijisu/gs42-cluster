import { Button, Card, Pill, Table, type Column } from '../../components'
import { formatMonthDay, kstDateFromToday } from '../../lib/datetime'
import type { StaffCourse } from './api'
import { useOpenReviews } from './hooks'
import { canRequest, courseState } from './labels'
import { messageFor } from './errors'

export function CoursesTable({ courses, onRequest }: { courses: StaffCourse[]; onRequest: (id: number) => void }) {
  const open = useOpenReviews()
  const today = kstDateFromToday(0)
  const error = messageFor(open.error, '변경하지 못했어요. 잠시 후 다시 시도해 주세요.')

  const columns: Column<StaffCourse>[] = [
    { key: 'name', header: '과정명', render: (c) => <span style={{ fontWeight: 600 }}>{c.name}</span> },
    { key: 'period', header: '기간', render: (c) => <span className="mono">{formatMonthDay(c.start_date)}–{formatMonthDay(c.end_date)}</span> },
    { key: 'count', header: '참여', render: (c) => <span className="mono">{c.participant_count}명</span> },
    {
      key: 'rate',
      header: '후기 작성률',
      render: (c) => {
        const pct = c.review_rate === null ? null : Math.round(c.review_rate * 100)
        return (
          <div style={{ display: 'flex', gap: 8, alignItems: 'center', minWidth: 140 }}>
            <div className="bar" style={{ flexGrow: 1 }}>
              <div style={{ width: `${pct ?? 0}%` }} />
            </div>
            <span className="mono muted small" style={{ fontSize: 12 }}>{pct === null ? '-' : `${pct}%`}</span>
          </div>
        )
      },
    },
    {
      key: 'state',
      header: '상태',
      render: (c) => {
        const s = courseState(c, today)
        return <Pill tone={s.tone}>{s.label}</Pill>
      },
    },
    {
      key: 'act',
      header: '',
      render: (c) => (
        <span style={{ display: 'flex', gap: 8, justifyContent: 'flex-end', whiteSpace: 'nowrap' }}>
          {c.status !== 'completed' && (
            <Button variant="ghost" size="sm" disabled={open.isPending} aria-label={`${c.name} 종료 처리·후기 열기`} onClick={() => open.mutate(c.id)}>
              종료 · 후기 열기
            </Button>
          )}
          {canRequest(c, today) && (
            <Button variant="ghost" size="sm" aria-label={`${c.name} 후기 요청`} onClick={() => onRequest(c.id)}>
              후기 요청
            </Button>
          )}
        </span>
      ),
    },
  ]

  return (
    <Card className="stack" style={{ gap: 8 }}>
      <h2 className="card-title">교육과정</h2>
      {error && <p role="alert" className="login-error">{error}</p>}
      <Table caption="교육과정 목록" columns={columns} rows={courses} rowKey={(c) => c.id} empty="등록된 교육과정이 없어요." />
    </Card>
  )
}
