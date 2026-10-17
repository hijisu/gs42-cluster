import { useState } from 'react'
import { Button, Card, Field, Modal } from '../../components'
import type { RoomRules } from '../room/api'
import { messageFor } from './errors'
import { useSaveRules } from './hooks'

/** 이용수칙 + 운영 시간 보기·편집 */
export function RulesPanel({ rules }: { rules: RoomRules }) {
  const [editing, setEditing] = useState(false)
  return (
    <Card className="stack">
      <div className="row">
        <h2 className="card-title">이용수칙</h2>
        <Button variant="secondary" size="sm" onClick={() => setEditing(true)}>
          편집
        </Button>
      </div>
      <p className="muted small">운영 시간 {String(rules.open_hour).padStart(2, '0')}:00–{String(rules.close_hour).padStart(2, '0')}:00</p>
      <ol className="ol">
        {rules.usage_rules.map((r) => (
          <li key={r}>{r}</li>
        ))}
      </ol>
      <p className="muted" style={{ fontSize: 12 }}>승인 시 교육생에게 팝업으로 전송됩니다.</p>
      <Modal open={editing} title="이용수칙 편집" onClose={() => setEditing(false)}>
        {editing && <RulesEditor key={JSON.stringify(rules)} rules={rules} onClose={() => setEditing(false)} />}
      </Modal>
    </Card>
  )
}

function RulesEditor({ rules, onClose }: { rules: RoomRules; onClose: () => void }) {
  const save = useSaveRules()
  const [open, setOpen] = useState(String(rules.open_hour))
  const [close, setClose] = useState(String(rules.close_hour))
  const [text, setText] = useState(rules.usage_rules.join('\n'))
  const [submitted, setSubmitted] = useState(false)

  const lines = text.split('\n').map((l) => l.trim()).filter(Boolean)
  const o = Number(open)
  const c = Number(close)
  const hoursError = !Number.isInteger(o) || !Number.isInteger(c) || o < 0 || c > 24 || o >= c ? '운영 시간은 0~24 사이에서 시작이 종료보다 빨라야 해요.' : undefined
  const rulesError = lines.length === 0 ? '이용수칙을 한 줄 이상 입력해 주세요.' : undefined
  const error = messageFor(save.error, '저장하지 못했어요. 잠시 후 다시 시도해 주세요.')

  return (
    <>
      <div className="g2" style={{ gap: 12 }}>
        <Field label="운영 시작(시)" type="number" min={0} max={23} value={open} onChange={(e) => setOpen(e.target.value)} error={submitted ? hoursError : undefined} />
        <Field label="운영 종료(시)" type="number" min={1} max={24} value={close} onChange={(e) => setClose(e.target.value)} />
      </div>
      <Field label="이용수칙" hint="한 줄에 하나씩 입력하세요" multiline rows={8} value={text} onChange={(e) => setText(e.target.value)} error={submitted ? rulesError : undefined} />
      {error && <p role="alert" className="login-error">{error}</p>}
      <div className="modal-actions">
        <Button variant="secondary" onClick={onClose}>
          취소
        </Button>
        <Button
          disabled={save.isPending}
          onClick={() => {
            setSubmitted(true)
            if (hoursError || rulesError) return
            save.mutate({ open_hour: o, close_hour: c, usage_rules: lines }, { onSuccess: onClose })
          }}
        >
          {save.isPending ? '저장 중…' : '저장'}
        </Button>
      </div>
    </>
  )
}
