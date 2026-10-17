import { Link } from 'react-router-dom'
import { LIBRARY_URL } from '../../app/routes'

// 임시 홈. 홈 대시보드는 Phase 3.
export function HomePage() {
  return (
    <>
      <h1 className="h1">홈</h1>
      <p>클러스터에서 필요한 일을 한 곳에서 처리하세요.</p>
      <p className="chips">
        <Link className="btn ghost" to="/meeting">면담 신청</Link>
        <Link className="btn ghost" to="/room">회의실 예약</Link>
        {/* 도서 화면(#28) 전까지 임시 외부 링크(#100) */}
        <a className="btn ghost" href={LIBRARY_URL} target="_blank" rel="noopener noreferrer">
          오아시스 도서<span className="sr-only">(새 창)</span>
        </a>
      </p>
    </>
  )
}
