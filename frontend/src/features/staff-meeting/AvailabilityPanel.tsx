import { useState } from 'react'
import { Button, Card, Chip, Field, Modal } from '../../components'
import { ApiError } from '../../lib/api'
import { formatMonthDay, kstDateFromToday, kstTime, kstToIso } from '../../lib/datetime'
import { useMyAvailability, useSaveAvailability } from './hooks'
import { errorLabel } from './labels'

// 30분 단위 후보 시간 09:00 ~ 17:30
const TIMES = Array.from({ length: 18 }, (_, i) => `${String(9 + Math.floor(i / 2)).padStart(2, '0')}:${i % 2 ? '30' : '00'}`)

/** 내 면담 가능 시간 (선택한 날짜) + 설정 모달 */
export function AvailabilityPanel() {
  const [date, setDate] = useState(() => kstDateFromToday(0))
  const [editing, setEditing] = useState(false)
  const { data, isPending, isError } = useMyAvailability(date, date)

  const times = (data?.slots ?? []).map(kstTime).sort()
  return (
    <Card className="stack" style={{ gap: 8 }}>
      <h2 className="card-title">내 면담 가능 시간 · {formatMonthDay(date)}</h2>
      <Field label="날짜" type="date" value={date} onChange={(e) => e.target.value && setDate(e.target.value)} />
      {isPending && <p className="muted" role="status">불러오는 중…</p>}
      {isError && <p role="alert">가능 시간을 불러오지 못했어요.</p>}
      {data && <p className="mono muted small">{times.length > 0 ? times.join(' · ') : '열어 둔 시간이 없어요'}</p>}
      <div>
        <Button variant="ghost" size="sm" onClick={() => setEditing(true)}>
          내 면담 가능 시간 설정
        </Button>
      </div>
      <p className="muted small">다른 담당자의 가능 시간은 아직 조회할 수 없어요(API 없음).</p>
      <Modal open={editing} title={`면담 가능 시간 설정 · ${formatMonthDay(date)}`} onClose={() => setEditing(false)}>
        {data && <Editor key={`${date}-${data.slots.join()}`} date={date} initial={times} onClose={() => setEditing(false)} />}
      </Modal>
    </Card>
  )
}

function Editor({ date, initial, onClose }: { date: string; initial: string[]; onClose: () => void }) {
  const save = useSaveAvailability()
  const [picked, setPicked] = useState<string[]>(initial)
  const toggle = (t: string) => setPicked((p) => (p.includes(t) ? p.filter((x) => x !== t) : [...p, t]))
  const error =
    save.error instanceof ApiError ? (errorLabel[save.error.code ?? ''] ?? '저장하지 못했어요. 잠시 후 다시 시도해 주세요.') : save.isError ? '저장하지 못했어요.' : null

  return (
    <>
      <p className="muted small">면담을 받을 수 있는 시간을 모두 고르세요. 선택한 날짜의 가능 시간이 이 목록으로 바뀌어요.</p>
      <div className="chips" role="group" aria-label="가능 시간">
        {TIMES.map((t) => (
          <Chip key={t} selected={picked.includes(t)} onClick={() => toggle(t)}>
            {t}
          </Chip>
        ))}
      </div>
      {error && <p role="alert" className="login-error">{error}</p>}
      <div className="modal-actions">
        <Button variant="ghost" onClick={onClose}>
          닫기
        </Button>
        <Button disabled={save.isPending} onClick={() => save.mutate({ from: date, to: date, slots: [...picked].sort().map((t) => kstToIso(date, t)) }, { onSuccess: onClose })}>
          {save.isPending ? '저장 중…' : '저장'}
        </Button>
      </div>
    </>
  )
}
