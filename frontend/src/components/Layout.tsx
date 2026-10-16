import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import { STATS_URL, type NavItem } from '../app/routes'
import { useLogout, useMe } from '../features/auth/hooks'
import { NotificationBanner, NotificationBell } from '../features/notification/Notifications'

interface LayoutProps {
  variant: 'student' | 'staff'
  nav: NavItem[]
  switchTo: { to: string; label: string }
}

const roleLabel = { student: '42경산 · 교육생', staff: '교육운영팀' }

export function Layout({ variant, nav, switchTo }: LayoutProps) {
  const { data: me } = useMe()
  const logout = useLogout()
  const navigate = useNavigate()
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
        {me && <NotificationBell />}
        {me && (
          <div className="me">
            <div className="av">{me.intra_id.slice(0, 2).toUpperCase()}</div>
            <div className="me-text">
              <span className="me-name">{me.intra_id}</span>
              <span className="me-role">{roleLabel[me.role]}</span>
            </div>
          </div>
        )}
        {/* 운영팀 계정에만 화면 전환 토글을 보여준다 */}
        {me?.role === 'staff' && (
          <NavLink className="switch" to={switchTo.to}>
            {switchTo.label}
          </NavLink>
        )}
        <button
          type="button"
          className="switch"
          disabled={logout.isPending}
          onClick={() => logout.mutate(undefined, { onSuccess: () => navigate('/login', { replace: true }) })}
        >
          로그아웃
        </button>
      </aside>
      <main className="main">
        {me && <NotificationBanner />}
        <Outlet />
      </main>
    </div>
  )
}
