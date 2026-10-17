import { useRef, useState, type KeyboardEvent } from 'react'
import { Button, Field, Modal } from '../../components'
import type { StaffCourse } from './api'
import { messageFor } from './errors'
import { useAddParticipants, useRemoveParticipant, useStaffCourse, useUpdateCourse } from './hooks'

const splitIds = (raw: string) => raw.split(/[\s,]+/).map((s) => s.trim().toLowerCase()).filter(Boolean)

/** 등록한 교육과정 수정: 기본 정보·후기 마감일 + 참여 학생 추가/제거 */
export function EditCourseModal({ courseId, onClose }: { courseId: number | null; onClose: () => void }) {
  const course = useStaffCourse(courseId)
  return (
    <Modal open={courseId !== null} title="교육과정 수정" onClose={onClose}>
      {course.isPending && courseId !== null && <p className="muted" role="status">불러오는 중…</p>}
      {course.isError && <p role="alert">교육과정을 불러오지 못했어요.</p>}
      {course.data && <EditBody key={course.data.id} course={course.data} onClose={onClose} />}
    </Modal>
  )
}

function EditBody({ course, onClose }: { course: StaffCourse; onClose: () => void }) {
  const update = useUpdateCourse()
  const [name, setName] = useState(course.name)
  const [start, setStart] = useState(course.start_date)
  const [end, setEnd] = useState(course.end_date)
  const [location, setLocation] = useState(course.location)
  const [intro, setIntro] = useState(course.intro)
  const [deadline, setDeadline] = useState(course.review_deadline ?? '')
  const [submitted, setSubmitted] = useState(false)

  const errors = {
    name: name.trim() === '' ? '과정명을 입력해 주세요.' : undefined,
    start: start === '' ? '시작일을 선택해 주세요.' : undefined,
    end: end === '' ? '종료일을 선택해 주세요.' : end < start ? '종료일은 시작일 이후여야 해요.' : undefined,
    deadline: deadline !== '' && end !== '' && deadline < end ? '마감일은 종료일 이후여야 해요.' : undefined,
  }
  const error = messageFor(update.error, '저장하지 못했어요. 잠시 후 다시 시도해 주세요.')

  function save() {
    setSubmitted(true)
    if (Object.values(errors).some(Boolean)) return
    update.mutate(
      { id: course.id, body: { name: name.trim(), start_date: start, end_date: end, location: location.trim(), intro: intro.trim(), review_deadline: deadline || null } },
      { onSuccess: onClose },
    )
  }

  return (
    <div className="stack">
      <Field label="과정명" value={name} onChange={(e) => setName(e.target.value)} error={submitted ? errors.name : undefined} />
      <div className="g2" style={{ gap: 12 }}>
        <Field label="시작일" type="date" value={start} onChange={(e) => setStart(e.target.value)} error={submitted ? errors.start : undefined} />
        <Field label="종료일" type="date" value={end} onChange={(e) => setEnd(e.target.value)} error={submitted ? errors.end : undefined} />
      </div>
      <Field label="장소" value={location} onChange={(e) => setLocation(e.target.value)} />
      <Field label="과정 소개" multiline value={intro} onChange={(e) => setIntro(e.target.value)} />
      <Field label="후기 작성 마감(선택)" type="date" value={deadline} onChange={(e) => setDeadline(e.target.value)} error={submitted ? errors.deadline : undefined} />
      {error && <p role="alert" className="login-error">{error}</p>}
      <div className="modal-actions">
        <Button disabled={update.isPending} onClick={save}>
          {update.isPending ? '저장 중…' : '정보 저장'}
        </Button>
      </div>
      <Participants course={course} />
      <div className="modal-actions">
        <Button variant="secondary" onClick={onClose}>
          닫기
        </Button>
      </div>
    </div>
  )
}

function Participants({ course }: { course: StaffCourse }) {
  const add = useAddParticipants()
  const remove = useRemoveParticipant()
  const fileRef = useRef<HTMLInputElement>(null)
  const [input, setInput] = useState('')
  const [confirming, setConfirming] = useState<string | null>(null)
  const [notice, setNotice] = useState<string | null>(null)
  const participants = course.participants ?? []
  const error = messageFor(add.error ?? remove.error, '처리하지 못했어요. 잠시 후 다시 시도해 주세요.')

  function addIds() {
    const ids = splitIds(input)
    if (ids.length === 0) return
    setNotice(null)
    add.mutate(
      { id: course.id, intraIds: ids },
      {
        onSuccess: (r) => {
          setInput('')
          setNotice(`${r.added.length}명을 추가했어요.${r.existing.length ? ` 이미 있는 ${r.existing.length}명은 건너뛰었어요.` : ''}`)
        },
      },
    )
  }
  async function addCsv(file: File | undefined) {
    if (!file) return
    setNotice(null)
    add.mutate(
      { id: course.id, csv: await file.text() },
      {
        onSuccess: (r) => setNotice(`${r.added.length}명을 추가했어요.${r.existing.length ? ` 이미 있는 ${r.existing.length}명은 건너뛰었어요.` : ''}`),
      },
    )
  }
  const onKey = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      e.preventDefault()
      addIds()
    }
  }
  function doRemove(intraId: string) {
    setNotice(null)
    remove.mutate(
      { id: course.id, intraId },
      {
        onSuccess: (r) => {
          setConfirming(null)
          setNotice(r.had_review ? `${intraId}님을 뺐어요. 이미 쓴 후기는 남고 작성률에서만 빠져요.` : `${intraId}님을 뺐어요.`)
        },
      },
    )
  }

  return (
    <section className="stack" style={{ gap: 8 }} aria-label="참여 학생">
      <h3 style={{ fontSize: 16 }}>참여 학생 {participants.length}명</h3>
      <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
        <input id="edit-ids" className="input" style={{ flexGrow: 1 }} aria-label="추가할 intra ID" placeholder="intra ID 입력 후 Enter 또는 ‘추가’" value={input} onChange={(e) => setInput(e.target.value)} onKeyDown={onKey} />
        <Button variant="secondary" disabled={add.isPending} onClick={addIds}>
          추가
        </Button>
        <Button variant="secondary" disabled={add.isPending} onClick={() => fileRef.current?.click()}>
          CSV
        </Button>
        <input ref={fileRef} type="file" accept=".csv,text/csv,text/plain" className="sr-only" tabIndex={-1} aria-label="CSV 파일 선택" onChange={(e) => { void addCsv(e.target.files?.[0]); e.target.value = '' }} />
      </div>
      {notice && <p role="status" className="info">{notice}</p>}
      {error && <p role="alert" className="login-error">{error}</p>}
      {participants.length === 0 && <p className="muted small">참여 학생이 없어요.</p>}
      <ul className="stack" style={{ gap: 6, listStyle: 'none', padding: 0, margin: 0 }}>
        {participants.map((p) => (
          <li key={p.intra_id} className="row" data-testid={`participant-${p.intra_id}`}>
            <span>
              <span className="mono">{p.intra_id}</span> <span className="muted small">{p.reviewed ? '후기 작성함' : '후기 미작성'}</span>
            </span>
            {confirming === p.intra_id ? (
              <span style={{ display: 'flex', gap: 6, alignItems: 'center', flexWrap: 'wrap' }}>
                <span className="small">{p.reviewed ? '이미 후기를 썼어요. 빼도 후기는 남고 작성률에서만 빠져요.' : '이 참여자를 뺄까요?'}</span>
                <Button size="sm" variant="danger" disabled={remove.isPending} onClick={() => doRemove(p.intra_id)}>
                  제거 확인
                </Button>
                <Button size="sm" variant="secondary" onClick={() => setConfirming(null)}>
                  취소
                </Button>
              </span>
            ) : (
              <Button size="sm" variant="danger" aria-label={`${p.intra_id} 제거`} onClick={() => setConfirming(p.intra_id)}>
                제거
              </Button>
            )}
          </li>
        ))}
      </ul>
    </section>
  )
}
