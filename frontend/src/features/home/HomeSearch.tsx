import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useDebounced } from '../../lib/useDebounced'
import { useBooks } from '../library/hooks'
import { useCourses } from '../review/hooks'
import { useRooms } from '../room/hooks'

interface Hit {
  key: string
  label: string
  kind: string
  to: string
}

/** 통합 검색: 회의실·교육과정은 이미 받은 목록에서 찾고, 도서는 도서 검색 API 결과를 보여 준다. */
export function HomeSearch() {
  const [q, setQ] = useState('')
  const rooms = useRooms()
  const courses = useCourses()
  const query = q.trim().toLowerCase()
  const books = useBooks(useDebounced(q.trim()), '', query !== '')

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
          {books.data?.results.slice(0, 5).map((b) => (
            <li key={`book-${b.id}`}>
              <Link to={`/library?q=${encodeURIComponent(q.trim())}`}>
                <span className="muted small">도서</span> {b.title}
              </Link>
            </li>
          ))}
          <li>
            <Link to={`/library?q=${encodeURIComponent(q.trim())}`}>
              <span className="muted small">도서</span> '{q.trim()}' 도서 검색 결과 보기{books.data ? ` (${books.data.total}종)` : ''}
            </Link>
          </li>
        </ul>
      )}
    </div>
  )
}
