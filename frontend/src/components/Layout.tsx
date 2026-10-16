import { NavLink, Outlet } from 'react-router-dom'
import { STATS_URL, type NavItem } from '../app/routes'

interface LayoutProps {
  variant: 'student' | 'staff'
  nav: NavItem[]
  switchTo: { to: string; label: string }
}

// 사용자 정보는 인증 프론트(#9)에서 실제 값으로 교체한다.
const profile = {
  student: { initials: 'IN', name: '[intra_id]', role: '42경산 · 교육생' },
  staff: { initials: 'GS', name: '[운영팀 이름]', role: '교육운영팀' },
}

export function Layout({ variant, nav, switchTo }: LayoutProps) {
  const me = profile[variant]
  return (
    <div className="app">
      <aside className={`side ${variant}`}>
        <NavLink className="brand" to={variant === 'staff' ? '/staff' : '/'}>
          <b>42</b>gs<span>-cluster</span>
        </NavLink>
        {variant === 'staff' && <span className="role">STAFF</span>}
        <nav className="nav" aria-label="주요 메뉴">
          {nav.map((item) => (
            <NavLink key={item.path} to={item.path} end>
              <span className="n">{item.no}</span>
              <span>{item.label}</span>
            </NavLink>
          ))}
          <a href={STATS_URL} target="_blank" rel="noopener">
            <span className="n">05</span>
            <span>gs42stats</span>
            <svg className="ext" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
              <path d="M7 17 17 7" />
              <path d="M8 7h9v9" />
            </svg>
            <span className="sr-only">(새 창)</span>
          </a>
        </nav>
        <div className="me">
          <div className="av">{me.initials}</div>
          <div className="me-text">
            <span className="me-name">{me.name}</span>
            <span className="me-role">{me.role}</span>
          </div>
        </div>
        <NavLink className="switch" to={switchTo.to}>
          {switchTo.label}
        </NavLink>
      </aside>
      <main className="main">
        <Outlet />
      </main>
    </div>
  )
}
