import { useState } from 'react'
import { Link } from 'react-router-dom'
import { LIBRARY_URL } from '../../app/routes'
import { useCourses } from '../review/hooks'
import { useRooms } from '../room/hooks'

interface Hit {
  key: string
  label: string
  kind: string
  to: string
}

/** 통합 검색: 회의실·교육과정은 이미 받은 목록에서 찾고, 도서는 42gslib(새 탭)로 안내한다. */
export function HomeSearch() {
  const [q, setQ] = useState('')
  const rooms = useRooms()
  const courses = useCourses()
  const query = q.trim().toLowerCase()

  const hits: Hit[] = query
    ? [
        ...(rooms.data ?? []).filter((r) => r.name.toLowerCase().includes(query)).map((r) => ({ key: `room-${r.id}`, label: r.name, kind: '회의실', to: '/room' })),
        ...(courses.data ?? []).filter((c) => c.name.toLowerCase().includes(query)).map((c) => ({ key: `course-${c.id}`, label: c.name, kind: '교육과정 후기', to: '/reviews' })),
      ]
    : []

  return (
    <div className="home-search">
      <label htmlFor="home-q" className="sr-only">통합 검색</label>
      <input id="home-q" className="input" type="search" placeholder="도서, 회의실, 교육과정 검색" value={q} onChange={(e) => setQ(e.target.value)} autoComplete="off" />
      {query && (
        <ul className="search-results" aria-label="검색 결과">
          {hits.map((h) => (
            <li key={h.key}>
              <Link to={h.to}>
                <span className="muted small">{h.kind}</span> {h.label}
              </Link>
            </li>
          ))}
          <li>
            <a href={LIBRARY_URL} target="_blank" rel="noopener noreferrer">
              <span className="muted small">도서</span> 42gslib에서 '{q.trim()}' 찾기<span className="sr-only"> (새 창)</span>
            </a>
          </li>
        </ul>
      )}
    </div>
  )
}
