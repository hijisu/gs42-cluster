import { useState } from 'react'
import { Button, Card } from '../../components'
import { ApiError } from '../../lib/api'
import type { StaffMeetingType, StaffMember } from './api'
import { useSaveDefaultStaff } from './hooks'
import { errorLabel } from './labels'

/** 유형별 기본 담당자 설정 */
export function DefaultStaffPanel({ types, members }: { types: StaffMeetingType[]; members: StaffMember[] }) {
  const save = useSaveDefaultStaff()
  // 사용자가 바꾼 값만 보관하고, 나머지는 서버 값을 그대로 보여준다.
  const [edits, setEdits] = useState<Record<number, number | null>>({})
  const current = (t: StaffMeetingType) => (t.id in edits ? edits[t.id] : (t.default_staff?.id ?? null))
  const dirty = Object.keys(edits).length > 0
  const error =
    save.error instanceof ApiError ? (errorLabel[save.error.code ?? ''] ?? '저장하지 못했어요. 잠시 후 다시 시도해 주세요.') : save.isError ? '저장하지 못했어요.' : null

  return (
    <Card className="stack" style={{ gap: 10 }}>
      <h2 className="card-title">유형별 기본 담당자</h2>
      <div className="list">
        {types.map((t) => (
          <div key={t.id} className="row">
            <label htmlFor={`default-${t.id}`} style={{ fontSize: 14 }}>
              {t.name}
            </label>
            <select
              id={`default-${t.id}`}
              className="input"
              style={{ width: 150, minHeight: 44 }}
              value={current(t) ?? ''}
              onChange={(e) => setEdits({ ...edits, [t.id]: e.target.value === '' ? null : Number(e.target.value) })}
            >
              <option value="">미지정</option>
              {members.map((m) => (
                <option key={m.id} value={m.id}>
                  {m.name}
                </option>
              ))}
            </select>
          </div>
        ))}
      </div>
      {error && <p role="alert" className="login-error">{error}</p>}
      <div>
        <Button
          size="sm"
          disabled={!dirty || save.isPending}
          onClick={() =>
            save.mutate(
              types.map((t) => ({ id: t.id, default_staff_id: current(t) })),
              { onSuccess: () => setEdits({}) },
            )
          }
        >
          {save.isPending ? '저장 중…' : '기본 담당자 저장'}
        </Button>
      </div>
    </Card>
  )
}
