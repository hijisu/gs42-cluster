import { NavLink, Outlet } from 'react-router-dom'
import { STATS_URL, type NavItem } from '../app/routes'

interface LayoutProps {
  variant: 'student' | 'staff'
  nav: NavItem[]
  switchTo: { to: string; label: string }
}

export function Layout({ variant, nav, switchTo }: LayoutProps) {
  return (
    <div className="app">
      <aside className={`side ${variant}`}>
        <NavLink className="brand" to={variant === 'staff' ? '/staff' : '/'}>
          <b>42</b>gs<span>-cluster</span>
        </NavLink>
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
            <span className="sr-only">(새 창)</span>
          </a>
        </nav>
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
