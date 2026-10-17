import type { ReactNode } from 'react'

// ok=완료·긍정, wait=대기·주의, neu=중립, done=종료
export type PillTone = 'ok' | 'wait' | 'neu' | 'done' | 'lost'

export function Pill({ tone = 'neu', children }: { tone?: PillTone; children: ReactNode }) {
  return <span className={`pill ${tone}`}>{children}</span>
}
