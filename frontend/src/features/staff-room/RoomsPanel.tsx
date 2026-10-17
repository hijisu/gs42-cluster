import { useState } from 'react'
import { Button, Card, Field, Modal, Pill } from '../../components'
import type { Room } from '../room/api'
import { messageFor } from './errors'
import { useCreateRoom, usePatchRoom } from './hooks'
import { roomStatusLabel } from './labels'

/** 장소 목록: 예약 받는 중 / 교육 기간 차단 전환, 장소 추가 */
export function RoomsPanel({ rooms }: { rooms: Room[] }) {
  const patch = usePatchRoom()
  const [adding, setAdding] = useState(false)
  const error = messageFor(patch.error, '변경하지 못했어요. 잠시 후 다시 시도해 주세요.')
  return (
    <Card className="stack" style={{ gap: 8 }}>
      <div className="row">
        <h2 className="card-title">장소 목록</h2>
        <Button variant="ghost" size="sm" onClick={() => setAdding(true)}>
          장소 추가
        </Button>
      </div>
      <div className="list">
        {rooms.map((r) => (
          <div key={r.id} className="row">
            <span>{r.name}</span>
            <span style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
              <Pill tone={r.status === 'open' ? 'ok' : 'neu'}>{roomStatusLabel[r.status]}</Pill>
              <Button
                variant="ghost"
                size="sm"
                disabled={patch.isPending}
                aria-label={`${r.name} ${r.status === 'open' ? '차단' : '차단 해제'}`}
                onClick={() => patch.mutate({ id: r.id, status: r.status === 'open' ? 'blocked' : 'open' })}
              >
                {r.status === 'open' ? '차단' : '차단 해제'}
              </Button>
            </span>
          </div>
        ))}
      </div>
      <p className="muted" style={{ fontSize: 12 }}>차단해도 이미 승인된 예약은 유지되고, 새 요청·승인만 막혀요.</p>
      {error && <p role="alert" className="login-error">{error}</p>}
      <AddRoomModal open={adding} onClose={() => setAdding(false)} />
    </Card>
  )
}

function AddRoomModal({ open, onClose }: { open: boolean; onClose: () => void }) {
  const create = useCreateRoom()
  const [name, setName] = useState('')
  const [capacity, setCapacity] = useState('')
  const [equipment, setEquipment] = useState('')
  const [submitted, setSubmitted] = useState(false)
  const close = () => {
    setName('')
    setCapacity('')
    setEquipment('')
    setSubmitted(false)
    create.reset()
    onClose()
  }
  const error = messageFor(create.error, '추가하지 못했어요. 잠시 후 다시 시도해 주세요.')
  return (
    <Modal
      open={open}
      title="장소 추가"
      onClose={close}
      actions={
        <>
          <Button variant="ghost" onClick={close}>
            취소
          </Button>
          <Button
            disabled={create.isPending}
            onClick={() => {
              setSubmitted(true)
              if (name.trim() === '') return
              create.mutate({ name: name.trim(), capacity_note: capacity.trim(), equipment: equipment.trim() }, { onSuccess: close })
            }}
          >
            {create.isPending ? '추가 중…' : '추가'}
          </Button>
        </>
      }
    >
      <Field label="이름" value={name} onChange={(e) => setName(e.target.value)} error={submitted && name.trim() === '' ? '이름을 입력해 주세요.' : undefined} />
      <Field label="수용 인원" placeholder="예: 6명" value={capacity} onChange={(e) => setCapacity(e.target.value)} />
      <Field label="설비" placeholder="예: TV" value={equipment} onChange={(e) => setEquipment(e.target.value)} />
      {error && <p role="alert" className="login-error">{error}</p>}
    </Modal>
  )
}
