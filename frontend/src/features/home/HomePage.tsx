import { Link } from 'react-router-dom'

// 임시 홈. 홈 대시보드는 Phase 3.
export function HomePage() {
  return (
    <>
      <h1 className="h1">홈</h1>
      <p>클러스터에서 필요한 일을 한 곳에서 처리하세요.</p>
      <p className="chips">
        <Link className="btn ghost" to="/meeting">면담 신청</Link>
        <Link className="btn ghost" to="/room">회의실 예약</Link>
      </p>
    </>
  )
}
