import { useState } from 'react'
import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import { STATS_URL, type NavItem } from '../app/routes'
import { useLogout, useMe } from '../features/auth/hooks'
import { NotificationBanner, NotificationBell } from '../features/notification/Notifications'
import { MOBILE_QUERY, useMediaQuery } from '../lib/useMediaQuery'
import { Modal } from './Modal'

interface LayoutProps {
  variant: 'student' | 'staff'
  nav: NavItem[]
  switchTo: { to: string; label: string }
}

const roleLabel = { student: '42경산 · 교육생', staff: '교육운영팀' }

const ExternalIcon = () => (
  <>
    <svg className="ext" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M7 17 17 7" />
      <path d="M8 7h9v9" />
    </svg>
    <span className="sr-only">(새 창)</span>
  </>
)

function MenuLinks({ nav, onNavigate }: { nav: NavItem[]; onNavigate?: () => void }) {
  return (
    <nav className="nav" aria-label="주요 메뉴">
      {nav.map((item) =>
        item.external ? (
          <a key={item.path} href={item.external} target="_blank" rel="noopener noreferrer" onClick={onNavigate}>
            <span className="n">{item.no}</span>
            <span>{item.label}</span>
            <ExternalIcon />
          </a>
        ) : (
          <NavLink key={item.path} to={item.path} end onClick={onNavigate}>
            <span className="n">{item.no}</span>
            <span>{item.label}</span>
          </NavLink>
        ),
      )}
      <a href={STATS_URL} target="_blank" rel="noopener noreferrer">
        <span className="n">05</span>
        <span>gs42stats</span>
        <ExternalIcon />
      </a>
    </nav>
  )
}

export function Layout({ variant, nav, switchTo }: LayoutProps) {
  const { data: me } = useMe()
  const logout = useLogout()
  const navigate = useNavigate()
  const mobile = useMediaQuery(MOBILE_QUERY)
  const [menuOpen, setMenuOpen] = useState(false)
  const [failedImage, setFailedImage] = useState<string | null>(null)
  const home = variant === 'staff' ? '/staff' : '/'

  const brand = (
    <NavLink className="brand" to={home}>
      <b>42</b>gs<span>-cluster</span>
    </NavLink>
  )
  const avatar = me && (
    <>
      {me.image_url && me.image_url !== failedImage
        ? <img src={me.image_url} alt={`${me.intra_id} 프로필 사진`} referrerPolicy="no-referrer" onError={() => setFailedImage(me.image_url ?? null)} />
        : me.intra_id.slice(0, 2).toUpperCase()}
    </>
  )
  const account = me && (
    <div className="me">
      <div className="av">{avatar}</div>
      <div className="me-text">
        <span className="me-name">{me.intra_id}</span>
        <span className="me-role">{roleLabel[me.role]}</span>
      </div>
    </div>
  )
  // 운영팀 계정에만 화면 전환 토글을 보여준다
  const switcher = me?.role === 'staff' && (
    <NavLink className="switch" to={switchTo.to} onClick={() => setMenuOpen(false)}>
      {switchTo.label}
    </NavLink>
  )
  const logoutButton = (
    <button
      type="button"
      className="switch"
      disabled={logout.isPending}
      onClick={() => logout.mutate(undefined, { onSuccess: () => navigate('/login', { replace: true }) })}
    >
      로그아웃
    </button>
  )

  return (
    <div className="app">
      <a className="skip" href="#main">본문 바로가기</a>
      {mobile ? (
        <>
          {/* 모바일: 56px 상단 바(메뉴·로고·알림·계정) + 좌측 드로어 */}
          <header className={`topbar ${variant}`}>
            <button type="button" className="icon-btn" aria-label="메뉴 열기" aria-haspopup="dialog" onClick={() => setMenuOpen(true)}>
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" aria-hidden="true">
                <path d="M4 7h16M4 12h16M4 17h16" />
              </svg>
            </button>
            {brand}
            {variant === 'staff' && <span className="role">STAFF</span>}
            <span className="topbar-end">
              {me && <NotificationBell compact />}
              {me && <div className="av" aria-label={`${me.intra_id} 계정`} role="img">{avatar}</div>}
            </span>
          </header>
          <Modal open={menuOpen} title="메뉴" placement="left" onClose={() => setMenuOpen(false)}>
            <MenuLinks nav={nav} onNavigate={() => setMenuOpen(false)} />
            {account}
            {switcher}
            {logoutButton}
          </Modal>
        </>
      ) : (
        <aside className={`side ${variant}`}>
          {brand}
          {variant === 'staff' && <span className="role">STAFF</span>}
          <MenuLinks nav={nav} />
          {me && <NotificationBell />}
          {switcher}
          {logoutButton}
          {account}
        </aside>
      )}
      <main id="main" className="main" tabIndex={-1}>
        {me && <NotificationBanner />}
        <Outlet />
      </main>
    </div>
  )
}
