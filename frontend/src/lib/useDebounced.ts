import { useEffect, useState } from 'react'

/** 값이 바뀌고 delay(ms) 동안 더 바뀌지 않으면 그 값을 돌려준다(입력마다 요청하지 않게). */
export function useDebounced<T>(value: T, delay = 300): T {
  const [debounced, setDebounced] = useState(value)
  useEffect(() => {
    const t = setTimeout(() => setDebounced(value), delay)
    return () => clearTimeout(t)
  }, [value, delay])
  return debounced
}
