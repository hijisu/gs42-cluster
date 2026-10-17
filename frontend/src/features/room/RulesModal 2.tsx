import { Button, Modal } from '../../components'
import { useRules } from './hooks'

interface RulesModalProps {
  open: boolean
  onClose: () => void
  /** '확인했습니다' 클릭 */
  onConfirm: () => void
}

export function RulesModal({ open, onClose, onConfirm }: RulesModalProps) {
  const { data, isPending, isError } = useRules()
  return (
    <Modal open={open} title="회의실 이용수칙" onClose={onClose} actions={<Button onClick={onConfirm}>확인했습니다</Button>}>
      {isPending && <p className="muted" role="status">불러오는 중…</p>}
      {isError && <p role="alert">이용수칙을 불러오지 못했습니다.</p>}
      {data && (
        <ol className="ol">
          {data.usage_rules.map((r) => (
            <li key={r}>{r}</li>
          ))}
        </ol>
      )}
    </Modal>
  )
}
