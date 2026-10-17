import { BooksPanel } from './BooksPanel'
import { LibraryRequestsCard } from './RequestsPanels'

export function StaffLibraryPage() {
  return (
    <>
      <div className="head">
        <div>
          <p className="label">03 · LIBRARY ADMIN</p>
          <h1 className="h1" style={{ marginTop: 2 }}>도서 관리</h1>
          <p className="sub">오아시스 비치 도서와 교육생의 희망 도서 · 분실 신고를 관리하세요.</p>
        </div>
      </div>
      <div className="split staff-library-split">
        <BooksPanel />
        <LibraryRequestsCard />
      </div>
    </>
  )
}
