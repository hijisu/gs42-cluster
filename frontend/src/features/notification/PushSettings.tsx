import { useEffect, useState } from 'react'
import { Button } from '../../components'
import { ApiError } from '../../lib/api'
import { ServiceWorkerNotReadyError, disablePush, enablePush, pushSupport, serviceWorkerReady } from '../../lib/push'

type State = 'loading' | 'on' | 'off'

const SW_HINT = '서비스워커가 아직 준비되지 않았어요. 새로고침 후 다시 시도해 주세요.'

/** 알림 목록 모달 안의 푸시 알림 켜기/끄기. 구독하지 않아도 앱 안 알림은 그대로 표시된다. */
export function PushSettings() {
  const support = pushSupport()
  const [state, setState] = useState<State>('loading')
  const [message, setMessage] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    if (support !== 'ready') return
    let alive = true
    serviceWorkerReady()
      .then(async (reg) => {
        if (!alive) return
        if (!reg) {
          // 서비스워커가 아직 없으면 버튼을 영구 비활성으로 두지 않고 안내한다.
          setState('off')
          setMessage(SW_HINT)
          return
        }
        setState((await reg.pushManager.getSubscription()) ? 'on' : 'off')
      })
      .catch(() => alive && setState('off'))
    return () => {
      alive = false
    }
  }, [support])

  if (support === 'ios-install') {
    return <p className="info small">iPhone·iPad에서는 Safari의 '홈 화면에 추가'로 앱을 설치한 뒤 설치한 앱에서만 푸시 알림을 켤 수 있어요. 그 전에는 앱 안 알림만 표시돼요.</p>
  }
  if (support === 'unsupported') {
    return <p className="info small">이 브라우저는 푸시 알림을 지원하지 않아요. 앱 안 알림만 표시돼요.</p>
  }

  async function toggle() {
    setBusy(true)
    setMessage(null)
    try {
      if (state === 'on') {
        await disablePush()
        setState('off')
      } else {
        const result = await enablePush()
        if (result === 'denied') setMessage('브라우저에서 알림이 차단돼 있어요. 주소창의 사이트 설정에서 알림을 허용해 주세요.')
        else setState('on')
      }
    } catch (e) {
      // 서버에 VAPID 키가 없으면 503 push_not_configured
      setMessage(
        e instanceof ServiceWorkerNotReadyError
          ? SW_HINT
          : e instanceof ApiError && e.code === 'push_not_configured'
            ? '서버에 푸시 알림이 아직 설정되지 않았어요. 앱 안 알림만 표시돼요.'
            : '푸시 설정을 바꾸지 못했어요. 잠시 후 다시 시도해 주세요.',
      )
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="info">
      <span className="label">푸시 알림</span>
      <span className="small">{state === 'on' ? '이 기기에서 푸시 알림을 받고 있어요.' : '켜면 앱을 열지 않아도 이 기기로 알림을 받아요. 끄면 앱 안 알림만 표시돼요.'}</span>
      <div>
        <Button size="sm" variant={state === 'on' ? 'ghost' : 'teal'} disabled={busy || state === 'loading'} onClick={toggle}>
          {state === 'on' ? '푸시 알림 끄기' : '푸시 알림 켜기'}
        </Button>
      </div>
      {message && <p role="alert" className="login-error">{message}</p>}
    </div>
  )
}
