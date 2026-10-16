import { useState } from 'react'
import { Button, Card, Modal, Pill } from '../../components'
import { ApiError } from '../../lib/api'
import { formatMonthDay, formatTimeRange, kstDate } from '../../lib/datetime'
import type { Reservation } from './api'
import { useCancelReservation, useMyReservations } from './hooks'
import { cancelable, errorLabel, statusLabel, statusTone } from './labels'
import { RulesModal } from './RulesModal'

const ACK_KEY = 'gs42.room.rulesAck'

function readAck(): number[] {
  try {
    return JSON.parse(localStorage.getItem(ACK_KEY) ?? '[]')
  } catch {
    return []
  }
}

function writeAck(ids: number[]) {
  try {
    localStorage.setItem(ACK_KEY, JSON.stringify(ids))
  } catch {
    /* 저장소를 못 쓰는 환경이면 확인 표시만 유지하지 않는다 */
  }
}

function detail(r: Reservation): string {
  const parts = [r.purpose, `${r.headcount}명`]
  if (r.note) parts.push(r.note)
  if (r.room.id !== r.requested_room.id) parts.push(`${r.requested_room.name} 대신 대체 배정`)
  if (r.status === 'rejected' && r.reject_reason) parts.push(`반려 사유: ${r.reject_reason}`)
  if (r.status === 'pending' && r.conflict) parts.push('같은 시간에 다른 요청이 있어 조정될 수 있어요')
  return parts.join(' · ')
}

export function MyReservations() {
  const { data, isPending, isError } = useMyReservations()
  const cancel = useCancelReservation()
  const [target, setTarget] = useState<Reservation | null>(null)
  const [rulesFor, setRulesFor] = useState<Reservation | null>(null)
  const [acked, setAcked] = useState<number[]>(readAck)

  const closeCancel = () => {
    setTarget(null)
    cancel.reset()
  }
  const confirmRules = () => {
    if (rulesFor) {
      const next = [...new Set([...acked, rulesFor.id])]
      setAcked(next)
      writeAck(next)
    }
    setRulesFor(null)
  }
  const cancelError =
    cancel.error instanceof ApiError
      ? (errorLabel[cancel.error.code ?? ''] ?? '취소하지 못했습니다. 잠시 후 다시 시도해 주세요.')
      : cancel.isError
        ? '취소하지 못했습니다.'
        : null

  return (
    <Card className="stack" style={{ gap: 8 }}>
      <h2 className="card-title">내 예약 요청</h2>
      {isPending && <p className="muted" role="status">불러오는 중…</p>}
      {isError && <p role="alert">예약 요청 내역을 불러오지 못했습니다.</p>}
      {data && data.length === 0 && <p className="muted">예약 요청 내역이 없습니다.</p>}
      {data && data.length > 0 && (
        <div className="list">
          {data.map((r) => {
            const title = `${r.room.name} · ${formatMonthDay(kstDate(r.start_at))} ${formatTimeRange(r.start_at, r.end_at)}`
            return (
              <div key={r.id} className="row" data-testid={`reservation-${r.id}`}>
                <span style={{ display: 'flex', flexDirection: 'column' }}>
                  <span style={{ fontWeight: 600 }}>{title}</span>
                  <span className="muted small">{detail(r)}</span>
                </span>
                <span style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                  <Pill tone={statusTone[r.status]}>{statusLabel[r.status]}</Pill>
                  {r.status === 'approved' && (
                    <Button variant={acked.includes(r.id) ? 'ghost' : 'teal'} size="sm" onClick={() => setRulesFor(r)}>
                      {acked.includes(r.id) ? '이용수칙 보기' : '이용수칙 확인'}
                    </Button>
                  )}
                  {cancelable(r.status) && (
                    <Button variant="ghost" size="sm" aria-label={`${title} 요청 취소`} onClick={() => setTarget(r)}>
                      요청 취소
                    </Button>
                  )}
                </span>
              </div>
            )
          })}
        </div>
      )}

      <RulesModal open={rulesFor !== null} onClose={() => setRulesFor(null)} onConfirm={confirmRules} />
      <Modal
        open={target !== null}
        title="예약 요청을 취소할까요?"
        onClose={closeCancel}
        actions={
          <>
            <Button variant="ghost" onClick={closeCancel}>
              돌아가기
            </Button>
            <Button variant="warn" disabled={cancel.isPending} onClick={() => target && cancel.mutate(target.id, { onSuccess: closeCancel })}>
              요청 취소
            </Button>
          </>
        }
      >
        {target && (
          <p>
            {target.room.name} · {formatMonthDay(kstDate(target.start_at))} {formatTimeRange(target.start_at, target.end_at)}
          </p>
        )}
        {cancelError && <p role="alert" className="login-error">{cancelError}</p>}
      </Modal>
    </Card>
  )
}
