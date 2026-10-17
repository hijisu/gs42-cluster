import { useState } from 'react'
import { Button, Card, Field, Modal, Pill } from '../../components'
import type { Room } from '../room/api'
import { messageFor } from './errors'
import { useCreateRoom } from './hooks'
import { roomStatusLabel } from './labels'

/** 장소 목록: 상태 표시와 장소 추가. 시간 차단은 '예약 차단 기간'에서 설정한다 */
export function RoomsPanel({ rooms }: { rooms: Room[] }) {
  const [adding, setAdding] = useState(false)
  return (
    <Card className="stack" style={{ gap: 8 }}>
      <div className="row">
        <h2 className="card-title">장소 목록</h2>
        <Button variant="secondary" size="sm" onClick={() => setAdding(true)}>
          장소 추가
        </Button>
      </div>
      <div className="list">
        {rooms.map((r) => (
          <div key={r.id} className="row">
            <span>{r.name}</span>
            <Pill tone={r.status === 'open' ? 'ok' : 'neu'}>{roomStatusLabel[r.status]}</Pill>
          </div>
        ))}
      </div>
      <p className="muted" style={{ fontSize: 12 }}>시간 단위 차단은 ‘예약 차단 기간’에서 설정해요. 승인된 예약은 차단해도 유지돼요.</p>
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
          <Button variant="secondary" onClick={close}>
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
