// 서비스워커(src/sw.ts)와 화면이 함께 쓰는 푸시 payload 해석. 서비스워커 전역에 의존하지 않아 테스트할 수 있다.
export interface PushMessage {
  title: string
  body: string
  /** 알림을 눌렀을 때 이동할 앱 안 경로 */
  link: string
}

const FALLBACK_TITLE = '42gs-cluster'

/** 서버 payload(JSON {title, body, link} 또는 일반 텍스트)를 알림 내용으로 바꾼다. 깨진 값은 기본 문구로 대체. */
export function parsePushPayload(text: string | null | undefined): PushMessage {
  if (!text) return { title: FALLBACK_TITLE, body: '', link: '/' }
  try {
    const data = JSON.parse(text) as Record<string, unknown>
    const str = (v: unknown) => (typeof v === 'string' ? v : '')
    return { title: str(data.title) || FALLBACK_TITLE, body: str(data.body), link: safeLink(str(data.link)) }
  } catch {
    return { title: FALLBACK_TITLE, body: text, link: '/' }
  }
}

/** 앱 안 경로(/로 시작, //·프로토콜 제외)만 허용한다. 그 외에는 홈으로. */
export function safeLink(link: string): string {
  return link.startsWith('/') && !link.startsWith('//') ? link : '/'
}
