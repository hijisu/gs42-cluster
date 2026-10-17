import { Link } from 'react-router-dom'
import { formatMonthDay, kstTodayLabel } from '../../lib/datetime'
import { useMe } from '../auth/hooks'
import { useCourses } from '../review/hooks'
import { Shortcuts } from './Shortcuts'
import { SummaryCards } from './SummaryCards'
import { reviewTodo } from './summary'

/** 교육생 홈 대시보드(#30): 인사말, 후기 요청 배너, 내 현황 4칸, 바로가기 */
export function HomePage() {
  const { data: me } = useMe()
  const courses = useCourses()
  const todo = courses.data ? reviewTodo(courses.data) : null
  const first = todo?.courses[0]

  return (
    <>
      <div className="head">
        <div>
          <p className="label">{kstTodayLabel()} · 42 GYEONGSAN</p>
          <h1 className="h1" style={{ marginTop: 8 }}>안녕하세요, {me?.intra_id ?? ''}님</h1>
          <p className="sub">클러스터에서 필요한 일을 한 곳에서 처리하세요.</p>
        </div>
      </div>

      {first && (
        <div className="notice" role="status">
          <span className="stack" style={{ gap: 2 }}>
            <span className="label" style={{ color: 'var(--c-side-sub)' }}>
              후기 요청{todo?.deadline ? ` · 마감 ${formatMonthDay(todo.deadline)}` : ''}
            </span>
            <span>
              <b>{first.name}</b>에 참여하셨네요. 다음 교육생을 위해 후기를 남겨 주세요.
            </span>
          </span>
          <Link className="btn teal" to={`/reviews?course=${first.id}&write=1`}>
            후기 작성하기
          </Link>
        </div>
      )}

      <SummaryCards />
      <Shortcuts />
    </>
  )
}
