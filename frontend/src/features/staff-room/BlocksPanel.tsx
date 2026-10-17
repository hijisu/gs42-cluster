import { useState } from 'react'
import { Button, Card, Pill } from '../../components'
import { formatDayLabel, kstDate, kstDateFromToday } from '../../lib/datetime'
import type { Room } from '../room/api'
import { BlockModal, type BlockTarget } from './BlockModal'
import { blockTime, repeatSummary } from './blockLabels'
import { messageFor } from './errors'
import { useBlocks, useDeleteBlock, useDeleteOccurrence } from './hooks'

const RANGE_DAYS = 365

/** 예약 차단 기간(반복 일정): 교육 활동 등으로 정해진 시간에 회의실 예약을 막는다 */
export function BlocksPanel({ rooms }: { rooms: Room[] }) {
  const today = kstDateFromToday(0)
  const blocks = useBlocks(today, kstDateFromToday(RANGE_DAYS))
  const remove = useDeleteBlock()
  const removeOne = useDeleteOccurrence()
  const [target, setTarget] = useState<BlockTarget | null>(null)
  const [open, setOpen] = useState<number | null>(null)
  const roomName = (id: number) => rooms.find((r) => r.id === id)?.name ?? '(삭제된 장소)'
  const error = messageFor(remove.error ?? removeOne.error, '삭제하지 못했어요. 잠시 후 다시 시도해 주세요.')

  const [confirming, setConfirming] = useState<number | null>(null)

  return (
    <Card className="stack" style={{ gap: 12 }} aria-label="예약 차단 기간">
      <div className="row">
        <h2 className="card-title">예약 차단 기간</h2>
        <Button variant="secondary" size="sm" disabled={rooms.length === 0} onClick={() => setTarget({ mode: 'create' })}>
          차단 추가
        </Button>
      </div>
      <p className="muted small">매주 토요일 10~12시 수학 교육처럼 정해진 시간에 예약을 받지 않도록 막아요. 앞으로 1년 안의 일정을 보여줘요.</p>
      {blocks.isPending && <p className="muted" role="status">불러오는 중…</p>}
      {blocks.isError && <p role="alert">차단 일정을 불러오지 못했어요.</p>}
      {blocks.data?.length === 0 && <p className="muted">설정된 차단 일정이 없어요.</p>}
      {error && <p role="alert" className="login-error">{error}</p>}
      <ul className="stack" style={{ gap: 8, listStyle: 'none', padding: 0, margin: 0 }}>
        {blocks.data?.map((b) => (
          <li key={b.id} className="stack" style={{ gap: 6, borderTop: '1px solid var(--c-line)', paddingTop: 8 }} data-testid={`block-${b.id}`}>
            <div className="row">
              <span style={{ fontWeight: 700 }}>{b.reason}</span>
              <Pill tone="neu">{roomName(b.room_id)}</Pill>
            </div>
            <p className="small">
              <span className="mono">{blockTime(b)}</span> · {repeatSummary(b)} · 남은 {b.occurrences.length}회
            </p>
            <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
              <Button size="sm" variant="secondary" aria-label={`${b.reason} 회차 보기`} aria-expanded={open === b.id} onClick={() => setOpen(open === b.id ? null : b.id)}>
                회차 {open === b.id ? '접기' : '보기'}
              </Button>
              <Button size="sm" variant="secondary" aria-label={`${b.reason} 전체 수정`} onClick={() => setTarget({ mode: 'series', block: b })}>
                전체 수정
              </Button>
              {confirming === b.id ? (
                <>
                  <span className="small">모든 회차가 삭제돼요.</span>
                  <Button size="sm" variant="danger" disabled={remove.isPending} onClick={() => remove.mutate(b.id, { onSuccess: () => setConfirming(null) })}>
                    삭제 확인
                  </Button>
                  <Button size="sm" variant="secondary" onClick={() => setConfirming(null)}>
                    취소
                  </Button>
                </>
              ) : (
                <Button size="sm" variant="danger" aria-label={`${b.reason} 전체 삭제`} onClick={() => setConfirming(b.id)}>
                  전체 삭제
                </Button>
              )}
            </div>
            {open === b.id && (
              <ul className="stack" style={{ gap: 4, listStyle: 'none', padding: 0, margin: 0 }}>
                {b.occurrences.map((o) => (
                  <li key={o.date} className="row">
                    <span className="small">
                      {formatDayLabel(kstDate(o.start_at))} <span className="mono">{blockTime(o)}</span>
                    </span>
                    <span style={{ display: 'flex', gap: 6 }}>
                      <Button size="sm" variant="secondary" aria-label={`${b.reason} ${o.date} 이 회차 수정`} onClick={() => setTarget({ mode: 'occurrence', block: b, day: o.date })}>
                        수정
                      </Button>
                      <Button size="sm" variant="danger" aria-label={`${b.reason} ${o.date} 이 회차 삭제`} disabled={removeOne.isPending} onClick={() => removeOne.mutate({ id: b.id, day: o.date })}>
                        삭제
                      </Button>
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </li>
        ))}
      </ul>
      <BlockModal target={target} rooms={rooms} onClose={() => setTarget(null)} />
    </Card>
  )
}
