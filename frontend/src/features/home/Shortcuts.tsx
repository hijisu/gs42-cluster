import { Link } from 'react-router-dom'
import { Card } from '../../components'
import { STATS_URL } from '../../app/routes'

interface Shortcut {
  no: string
  title: string
  desc: string
  to?: string
  external?: string
}

const shortcuts: Shortcut[] = [
  { no: '01', title: '면담 신청', desc: '대면 면담 일정 잡기', to: '/meeting' },
  { no: '02', title: '회의실 예약', desc: '날짜 선택 후 예약 요청 · 운영팀 승인', to: '/room' },
  { no: '03', title: '오아시스 도서', desc: '도서 검색 · 분실 신고 · 희망 도서', to: '/library' },
  { no: '04', title: '교육과정 후기', desc: '아카데미 운영 과정 후기 읽고 쓰기', to: '/reviews' },
  { no: '05', title: 'gs42stats', desc: '클러스터 · 과제 진행 통계', external: STATS_URL },
]

function Body({ s }: { s: Shortcut }) {
  return (
    <>
      <span className="row" style={{ justifyContent: 'space-between' }}>
        <span className="mono shortcut-no">{s.no}</span>
        {s.external && <span className="muted small" aria-hidden="true">외부 링크 ↗</span>}
      </span>
      <span style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
        <span className="shortcut-title">{s.title}</span>
        <span className="muted body-sm">{s.desc}</span>
      </span>
    </>
  )
}

/** 바로가기 5칸 + #pedago 안내 */
export function Shortcuts() {
  return (
    <section className="stack" style={{ gap: 14 }} aria-label="바로가기">
      <h2 style={{ fontSize: 18 }}>바로가기</h2>
      <div className="g3">
        {shortcuts.map((s) =>
          s.external ? (
            <a key={s.no} className="card shortcut" href={s.external} target="_blank" rel="noopener noreferrer">
              <Body s={s} />
              <span className="sr-only">(새 창)</span>
            </a>
          ) : (
            <Link key={s.no} className="card shortcut" to={s.to!}>
              <Body s={s} />
            </Link>
          ),
        )}
        <Card className="stack" style={{ gap: 10, minHeight: 140, background: 'var(--c-bg)' }}>
          <span className="label">문의는 #pedago</span>
          <p className="body-sm">프리즈, 타 사업 참여, 기숙사 이용 등 문의 내용을 함께 적어 주시면 담당자 대응이 빨라집니다. 운영팀 개인 DM은 먼저 보내지 말아 주세요.</p>
        </Card>
      </div>
    </section>
  )
}
