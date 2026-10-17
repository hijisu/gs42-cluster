import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Button, Modal } from '../../components'
import { formatDateTime } from '../../lib/datetime'
import type { AppNotification } from './api'
import { useMarkAllRead, useMarkRead, useNotifications } from './hooks'
import { titleOf } from './labels'
import { PushSettings } from './PushSettings'

function useOpenNotification() {
  const markRead = useMarkRead()
  const navigate = useNavigate()
  return (n: AppNotification, after?: () => void) => {
    if (!n.read) markRead.mutate(n.id)
    after?.()
    if (n.link) navigate(n.link)
  }
}

/** 사이드바 벨 + 안 읽은 수 + 알림 목록(모달) */
export function NotificationBell() {
  const { data, isError } = useNotifications()
  const [open, setOpen] = useState(false)
  const markAll = useMarkAllRead()
  const openNotification = useOpenNotification()

  const unread = data?.unread_count ?? 0
  return (
    <>
      <button type="button" className="bell" onClick={() => setOpen(true)} aria-label={unread > 0 ? `알림 ${unread}개 안 읽음` : '알림'}>
        <span aria-hidden="true">🔔</span>
        <span>알림</span>
        {unread > 0 && <span className="badge">{unread > 99 ? '99+' : unread}</span>}
      </button>
      <Modal
        open={open}
        title="알림"
        onClose={() => setOpen(false)}
        actions={
          <>
            <Button variant="ghost" disabled={unread === 0 || markAll.isPending} onClick={() => markAll.mutate()}>
              모두 읽음 처리
            </Button>
            <Button onClick={() => setOpen(false)}>닫기</Button>
          </>
        }
      >
        <PushSettings />
        {isError && <p role="alert">알림을 불러오지 못했습니다.</p>}
        {data && data.items.length === 0 && <p className="muted">새 알림이 없어요.</p>}
        <ul className="noti-list">
          {data?.items.map((n) => (
            <li key={n.id}>
              <button type="button" className={`noti-item${n.read ? '' : ' unread'}`} onClick={() => openNotification(n, () => setOpen(false))}>
                <span className="noti-title">
                  {!n.read && <span className="sr-only">안 읽음 </span>}
                  {titleOf(n.type, n.title)}
                </span>
                {n.body && <span className="muted small">{n.body}</span>}
                <span className="muted small mono">{formatDateTime(n.created_at)}</span>
              </button>
            </li>
          ))}
        </ul>
      </Modal>
    </>
  )
}

/** 화면 상단 배너: 가장 최근에 안 읽은 알림 1건 */
export function NotificationBanner() {
  const { data } = useNotifications()
  const markRead = useMarkRead()
  const openNotification = useOpenNotification()
  const latest = data?.items.find((n) => !n.read)
  if (!latest) return null
  return (
    <div className="notice" role="status">
      <span className="stack" style={{ gap: 2 }}>
        <span className="label" style={{ color: 'var(--c-side-sub)' }}>새 알림</span>
        <span>
          <b>{titleOf(latest.type, latest.title)}</b>
          {latest.body ? ` · ${latest.body}` : ''}
        </span>
      </span>
      <span className="row" style={{ gap: 8 }}>
        {latest.link && (
          <Button variant="teal" size="sm" onClick={() => openNotification(latest)}>
            확인하기
          </Button>
        )}
        <Button variant="ghost" size="sm" disabled={markRead.isPending} onClick={() => markRead.mutate(latest.id)}>
          닫기
        </Button>
      </span>
    </div>
  )
}
