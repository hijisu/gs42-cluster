import { Link } from 'react-router-dom'
import { Card } from '../../components'
import { formatDateTime, kstDateFromToday, kstTime, kstTodayLabel } from '../../lib/datetime'
import { useStaffCourses } from '../staff-course/hooks'
import { useReports, useWishes } from '../staff-library/hooks'
import { useStaffMeetings } from '../staff-meeting/hooks'
import { useReservationsByStatus } from './hooks'
import { latestReviewRate, pendingMeetings, todaySchedule, todoItems, todoKindLabel } from './summary'

interface StatProps {
  label: string
  to: string
  value: string
  sub: string
  state: 'loading' | 'error' | 'ok'
}

function Stat({ label, to, value, sub, state }: StatProps) {
  return (
    <Card className="stack summary-card" style={{ gap: 10 }}>
      <p className="label">{label}</p>
      {state === 'loading' && <p className="muted body-sm" role="status">불러오는 중…</p>}
      {state === 'error' && <p role="alert" className="body-sm">{label}을(를) 불러오지 못했어요.</p>}
      {state === 'ok' && (
        <>
          <p className="summary-big">{value}</p>
          <p className="muted body-sm">{sub}</p>
        </>
      )}
      <Link className="summary-link" to={to}>
        처리하기<span className="sr-only"> ({label})</span>
      </Link>
    </Card>
  )
}

const stateOf = (q: { isPending: boolean; isError: boolean }): StatProps['state'] => (q.isError ? 'error' : q.isPending ? 'loading' : 'ok')

/** 운영 홈 대시보드(#31): 처리 대기 현황 4칸, 처리 대기 요청, 오늘 일정. 기존 운영 API를 조합한다. */
export function StaffHomePage() {
  const today = kstDateFromToday(0)
  const meetings = useStaffMeetings('pending')
  const confirmed = useStaffMeetings('confirmed')
  const pendingRooms = useReservationsByStatus('pending')
  const approvedToday = useReservationsByStatus('approved', today)
  const wishes = useWishes()
  const reports = useReports()
  const courses = useStaffCourses()

  const newMeetings = meetings.data ? pendingMeetings(meetings.data) : []
  const conflicts = pendingRooms.data?.filter((r) => r.conflict).length ?? 0
  const openWishes = wishes.data?.filter((w) => w.status === 'requested').length ?? 0
  const openReports = reports.data?.filter((r) => r.status === 'received').length ?? 0
  const rate = courses.data ? latestReviewRate(courses.data) : null
  const todos = todoItems({
    meetings: newMeetings,
    reservations: pendingRooms.data ?? [],
    wishes: wishes.data ?? [],
    reports: reports.data ?? [],
  })
  const schedule = todaySchedule(confirmed.data ?? [], approvedToday.data ?? [], today)
  const loadingTodos = [meetings, pendingRooms, wishes, reports].some((q) => q.isPending)
  const failedTodos = [meetings, pendingRooms, wishes, reports].some((q) => q.isError)

  return (
    <>
      <div className="head">
        <div>
          <p className="label">{kstTodayLabel()} · 교육운영팀</p>
          <h1 className="h1" style={{ marginTop: 8 }}>오늘 처리할 요청</h1>
          <p className="sub">교육생 요청을 한 곳에서 확인하고 처리하세요.</p>
        </div>
      </div>

      <section className="g4" aria-label="처리 대기 현황">
        <Stat label="면담 요청" to="/staff/meeting" state={stateOf(meetings)} value={`${newMeetings.length}건`} sub="담당자 배정 필요" />
        <Stat label="회의실 승인 대기" to="/staff/room" state={stateOf(pendingRooms)} value={`${pendingRooms.data?.length ?? 0}건`} sub={conflicts ? `${conflicts}건 시간 충돌` : '시간 충돌 없음'} />
        <Stat label="도서 접수" to="/staff/library" state={wishes.isError || reports.isError ? 'error' : wishes.isPending || reports.isPending ? 'loading' : 'ok'} value={`${openWishes + openReports}건`} sub={`희망 도서 ${openWishes} · 분실 신고 ${openReports}`} />
        <Stat label="후기 작성률" to="/staff/courses" state={stateOf(courses)} value={rate ? `${rate.percent}%` : '-'} sub={rate ? rate.name : '후기를 받는 과정이 없어요'} />
      </section>

      <div className="g2" style={{ alignItems: 'start' }}>
        <Card className="stack" style={{ gap: 8 }}>
          <h2 className="card-title">처리 대기 요청</h2>
          {loadingTodos && <p className="muted" role="status">불러오는 중…</p>}
          {failedTodos && <p role="alert">일부 요청을 불러오지 못했어요.</p>}
          {!loadingTodos && !failedTodos && todos.length === 0 && <p className="muted">처리할 요청이 없어요.</p>}
          <ul className="stack" style={{ gap: 10, listStyle: 'none', padding: 0, margin: 0 }}>
            {todos.map((t) => (
              <li key={t.key} style={{ display: 'flex', justifyContent: 'space-between', gap: 8 }}>
                <span className="stack" style={{ gap: 2 }}>
                  <span>{t.who} · {todoKindLabel[t.kind]} · {t.title}</span>
                  {t.detail && <span className="muted small">{formatDateTime(t.detail)}</span>}
                </span>
                <Link className="btn ghost sm" to={t.to} aria-label={`${t.who} ${todoKindLabel[t.kind]} ${t.title} 처리`}>처리</Link>
              </li>
            ))}
          </ul>
        </Card>

        <Card className="stack" style={{ gap: 8 }}>
          <h2 className="card-title">오늘 일정</h2>
          <p className="muted small">확정된 면담 · 회의실</p>
          {(confirmed.isPending || approvedToday.isPending) && <p className="muted" role="status">불러오는 중…</p>}
          {(confirmed.isError || approvedToday.isError) && <p role="alert">일정을 불러오지 못했어요.</p>}
          {confirmed.data && approvedToday.data && schedule.length === 0 && <p className="muted">오늘 확정된 일정이 없어요.</p>}
          <ul className="stack" style={{ gap: 10, listStyle: 'none', padding: 0, margin: 0 }}>
            {schedule.map((s) => (
              <li key={s.key} style={{ display: 'flex', gap: 12 }}>
                <span className="mono">{kstTime(s.at)}</span>
                <span>{s.title}{s.place ? ` · ${s.place}` : ''}</span>
              </li>
            ))}
          </ul>
        </Card>
      </div>
    </>
  )
}
