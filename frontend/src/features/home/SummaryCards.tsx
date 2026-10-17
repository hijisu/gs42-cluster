import { Link } from 'react-router-dom'
import { Card, Pill } from '../../components'
import { LIBRARY_URL } from '../../app/routes'
import { formatDateTime, formatMonthDay, formatTimeRange, kstDate } from '../../lib/datetime'
import { useMyMeetings } from '../meeting/hooks'
import { statusLabel as meetingStatus, statusTone as meetingTone } from '../meeting/labels'
import { useCourses } from '../review/hooks'
import { useMyReservations } from '../room/hooks'
import { statusLabel as reservationStatus, statusTone as reservationTone } from '../room/labels'
import { nextMeeting, nextReservation, reviewTodo } from './summary'

interface CardProps {
  label: string
  to?: string
  children: React.ReactNode
}

function SummaryCard({ label, to, children }: CardProps) {
  return (
    <Card className="stack summary-card" style={{ gap: 10 }}>
      <p className="label">{label}</p>
      {children}
      {to && (
        <Link className="summary-link" to={to}>
          자세히 보기<span className="sr-only"> ({label})</span>
        </Link>
      )}
    </Card>
  )
}

const Big = ({ children }: { children: React.ReactNode }) => <p className="summary-big">{children}</p>
const Sub = ({ children }: { children: React.ReactNode }) => <p className="muted body-sm">{children}</p>
const Loading = () => <p className="muted body-sm" role="status">불러오는 중…</p>
const Failed = ({ what }: { what: string }) => <p role="alert" className="body-sm">{what}을(를) 불러오지 못했어요.</p>

/** 내 현황 4칸: 다음 면담 · 회의실 요청 · 희망 도서 · 작성할 후기 */
export function SummaryCards() {
  const meetings = useMyMeetings()
  const reservations = useMyReservations()
  const courses = useCourses()

  const meeting = meetings.data ? nextMeeting(meetings.data) : null
  const reservation = reservations.data ? nextReservation(reservations.data) : null
  const todo = courses.data ? reviewTodo(courses.data) : null

  return (
    <section className="g4" aria-label="내 현황">
      <SummaryCard label="다음 면담" to="/meeting">
        {meetings.isPending && <Loading />}
        {meetings.isError && <Failed what="면담" />}
        {meetings.data && (meeting ? (
          <>
            <Big>{formatDateTime(meeting.slot_at)}</Big>
            <Sub>{[meeting.type.name, meeting.location, meeting.staff?.name].filter(Boolean).join(' · ')}</Sub>
            <Pill tone={meetingTone[meeting.status]}>{meetingStatus[meeting.status]}</Pill>
          </>
        ) : (
          <Sub>예정된 면담이 없어요.</Sub>
        ))}
      </SummaryCard>

      <SummaryCard label="회의실 요청" to="/room">
        {reservations.isPending && <Loading />}
        {reservations.isError && <Failed what="회의실 예약" />}
        {reservations.data && (reservation ? (
          <>
            <Big>
              {formatMonthDay(kstDate(reservation.start_at))} {formatTimeRange(reservation.start_at, reservation.end_at)}
            </Big>
            <Sub>{reservation.room.name} · {reservation.headcount}명</Sub>
            <Pill tone={reservationTone[reservation.status]}>{reservationStatus[reservation.status]}</Pill>
          </>
        ) : (
          <Sub>예약 요청이 없어요.</Sub>
        ))}
      </SummaryCard>

      {/* 도서 화면(#28) 전까지 희망 도서는 42gslib에서 확인한다(#100) */}
      <Card className="stack summary-card" style={{ gap: 10 }}>
        <p className="label">희망 도서</p>
        <Sub>희망 도서 신청과 검색은 42gslib에서 해요.</Sub>
        <a className="summary-link" href={LIBRARY_URL} target="_blank" rel="noopener noreferrer">
          42gslib 열기<span className="sr-only"> (새 창)</span>
        </a>
      </Card>

      <SummaryCard label="작성할 후기" to="/reviews">
        {courses.isPending && <Loading />}
        {courses.isError && <Failed what="교육과정" />}
        {todo && (todo.courses.length > 0 ? (
          <>
            <Big>{todo.courses.length}건</Big>
            <Sub>{todo.deadline ? `마감 ${formatMonthDay(todo.deadline)}` : '마감일 없음'}</Sub>
            <Pill tone="wait">작성 대기</Pill>
          </>
        ) : (
          <Sub>지금 작성할 후기가 없어요.</Sub>
        ))}
      </SummaryCard>
    </section>
  )
}
