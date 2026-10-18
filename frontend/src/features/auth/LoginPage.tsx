import { Navigate, useLocation, useSearchParams } from 'react-router-dom'
import { Button, Card } from '../../components'
import { loginUrl } from './api'
import { useMe, useMockLogin } from './hooks'

// 백엔드 콜백 실패 시 /login?error=<code> 로 돌아온다. 문구 매핑은 프론트에서 한다.
const errorLabel: Record<string, string> = {
  invalid_state: '로그인 요청이 만료되었습니다. 다시 시도해 주세요.',
  auth_failed: '42 로그인에 실패했습니다. 다시 시도해 주세요.',
}

export function LoginPage() {
  const { data: me, isPending } = useMe()
  const [params] = useSearchParams()
  const location = useLocation()
  const mock = useMockLogin()
  const error = params.get('error')

  if (isPending) return null
  if (me) {
    // 돌아갈 경로가 없으면 역할별 홈: 운영팀은 운영 홈, 교육생은 교육생 홈.
    const home = me.role === 'staff' ? '/staff' : '/'
    return <Navigate to={(location.state as { from?: string } | null)?.from ?? home} replace />
  }

  return (
    <div className="login">
      <Card className="login-card">
        <p className="brand login-brand">
          <b>42</b>gs<span>-cluster</span>
        </p>
        <h1 className="h1">로그인</h1>
        <p className="muted">42 intra 계정으로 로그인하세요.</p>
        {error && (
          <p role="alert" className="login-error">
            {errorLabel[error] ?? '로그인에 실패했습니다.'}
          </p>
        )}
        <a className="btn" href={loginUrl}>
          42 intra로 로그인
        </a>
        {import.meta.env.DEV && (
          <div className="login-mock">
            <p className="label">개발용 모의 로그인</p>
            <div className="row" style={{ justifyContent: 'flex-start' }}>
              <Button variant="secondary" size="sm" disabled={mock.isPending} onClick={() => mock.mutate('student')}>
                교육생
              </Button>
              <Button variant="secondary" size="sm" disabled={mock.isPending} onClick={() => mock.mutate('staff')}>
                운영팀
              </Button>
            </div>
            {mock.isError && <p role="alert" className="login-error">모의 로그인에 실패했습니다(백엔드 DEBUG 확인).</p>}
          </div>
        )}
      </Card>
    </div>
  )
}
