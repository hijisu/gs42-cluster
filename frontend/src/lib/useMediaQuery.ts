import { useSyncExternalStore } from 'react'

/** CSS 미디어 쿼리 결과를 구독한다. matchMedia가 없는 환경(테스트 등)에서는 false. */
export function useMediaQuery(query: string): boolean {
  return useSyncExternalStore(
    (notify) => {
      if (typeof window.matchMedia !== 'function') return () => {}
      const mql = window.matchMedia(query)
      mql.addEventListener('change', notify)
      return () => mql.removeEventListener('change', notify)
    },
    () => (typeof window.matchMedia === 'function' ? window.matchMedia(query).matches : false),
    () => false,
  )
}

/** 사이드바 레이아웃이 상단 바 + 드로어로 바뀌는 폭 (base.css의 @media와 같은 값) */
export const MOBILE_QUERY = '(max-width: 900px)'
