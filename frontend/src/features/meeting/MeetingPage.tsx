import { useState, type FormEvent } from 'react'
import { Button, Card, Chip, Field } from '../../components'
import { ApiError } from '../../lib/api'
import { formatDateTimeLong } from '../../lib/datetime'
import { useCreateMeeting, useMeetingTypes, useSlots } from './hooks'
import { errorLabel } from './labels'
import { MyMeetings } from './MyMeetings'
import { SlotGrid } from './SlotGrid'

export function MeetingPage() {
  const types = useMeetingTypes()
  const slots = useSlots()
  const create = useCreateMeeting()

  const [typeId, setTypeId] = useState<number | null>(null)
  const [slotAt, setSlotAt] = useState<string | null>(null)
  const [content, setContent] = useState('')
  const [notifySlack, setNotifySlack] = useState(true)
  const [submitted, setSubmitted] = useState(false)

  const selectedType = types.data?.find((t) => t.id === typeId)
  // 선택한 시간이 마감되어 목록에서 사라지면 선택을 풀어 준다.
  const slotStillOpen = slotAt !== null && slots.data?.some((s) => s.start_at === slotAt && s.available)
  const effectiveSlot = slotStillOpen ? slotAt : null

  const contentError = submitted && content.trim() === '' ? '문의 내용을 입력해 주세요.' : undefined
  const missing = submitted && (typeId === null || effectiveSlot === null)

  const submitError =
    create.error instanceof ApiError
      ? (errorLabel[create.error.code ?? ''] ?? '신청하지 못했습니다. 잠시 후 다시 시도해 주세요.')
      : create.isError
        ? '신청하지 못했습니다. 잠시 후 다시 시도해 주세요.'
        : null

  function onSubmit(e: FormEvent) {
    e.preventDefault()
    setSubmitted(true)
    if (typeId === null || effectiveSlot === null || content.trim() === '') return
    create.mutate(
      { type_id: typeId, slot_at: effectiveSlot, content: content.trim(), notify_slack: notifySlack },
      {
        onSuccess: () => {
          setSlotAt(null)
          setContent('')
          setSubmitted(false)
        },
      },
    )
  }

  return (
    <>
      <div className="head">
        <div>
          <p className="label">01 · MEETING</p>
          <h1 className="h1" style={{ marginTop: 8 }}>면담 신청</h1>
          <p className="sub">대면 면담 일정을 신청하세요. 비대면 면담은 Slack #pedago 채널에서 신청하면 DM으로 진행됩니다.</p>
        </div>
      </div>

      <form className="split" onSubmit={onSubmit} noValidate>
        <div className="col">
          <Card className="row" style={{ justifyContent: 'flex-start', gap: 12 }}>
            <h2 className="card-title">1. 면담 유형</h2>
            {types.isPending && <p className="muted" role="status">불러오는 중…</p>}
            {types.isError && <p role="alert">면담 유형을 불러오지 못했습니다.</p>}
            <div className="chips" role="group" aria-label="면담 유형">
              {types.data?.map((t) => (
                <Chip key={t.id} selected={typeId === t.id} onClick={() => setTypeId(t.id)}>
                  {t.name}
                </Chip>
              ))}
            </div>
            <span className="muted small">담당자는 운영팀이 유형에 맞게 배정해요.</span>
          </Card>

          <Card className="stack">
            <div className="row">
              <h2 className="card-title">2. 희망 시간</h2>
              <span className="muted small">운영팀 확인 후 확정 · 변경될 수 있어요</span>
            </div>
            {slots.isPending && <p className="muted" role="status">불러오는 중…</p>}
            {slots.isError && <p role="alert">시간 정보를 불러오지 못했습니다.</p>}
            {slots.data && <SlotGrid slots={slots.data} selected={effectiveSlot} onSelect={setSlotAt} />}
          </Card>
        </div>

        <div className="col">
          <Card className="stack">
            <h2 className="card-title">3. 신청 내용</h2>
            <div className="info">
              <span className="label">선택한 일정</span>
              <span style={{ fontWeight: 700 }}>
                {effectiveSlot ? `${formatDateTimeLong(effectiveSlot)}${selectedType ? ` · ${selectedType.name}` : ''}` : '아직 선택하지 않았어요'}
              </span>
            </div>
            <Field
              label="문의 내용"
              multiline
              style={{ minHeight: 64 }}
              placeholder="면담에서 이야기하고 싶은 내용을 적어 주세요. 운영팀만 볼 수 있어요."
              value={content}
              onChange={(e) => setContent(e.target.value)}
              error={contentError}
            />
            <label className="check">
              <input type="checkbox" checked={notifySlack} onChange={(e) => setNotifySlack(e.target.checked)} /> 확정되면 Slack으로 알림 받기
            </label>
            {missing && (
              <p role="alert" className="login-error">
                {typeId === null ? '면담 유형을 선택해 주세요. ' : ''}
                {effectiveSlot === null ? '희망 시간을 선택해 주세요.' : ''}
              </p>
            )}
            {submitError && <p role="alert" className="login-error">{submitError}</p>}
            <Button type="submit" disabled={create.isPending}>
              {create.isPending ? '신청 중…' : '면담 신청하기'}
            </Button>
          </Card>

          <MyMeetings />

          <Card className="stack" style={{ background: 'var(--c-bg)' }}>
            <span className="label">#pedago 이용 안내</span>
            <ul className="ol">
              <li>이미 공지된 내용, 답이 필요 없는 내용, 내부 논의 중인 사항은 답변이 없을 수 있어요.</li>
              <li>운영팀 개인에게 먼저 DM을 보내지 말아 주세요.</li>
            </ul>
          </Card>
        </div>
      </form>
    </>
  )
}
