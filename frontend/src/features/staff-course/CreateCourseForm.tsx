import { useRef, useState, type KeyboardEvent } from 'react'
import { Button, Card, Field, Pill } from '../../components'
import type { CourseStatus } from '../review/api'
import { messageFor } from './errors'
import { useCreateCourse } from './hooks'

const statusOptions: { value: CourseStatus; label: string }[] = [
  { value: 'upcoming', label: '모집 · 수요조사' },
  { value: 'ongoing', label: '진행 중' },
  { value: 'completed', label: '종료 · 후기 수집' },
]

const splitIds = (raw: string) => raw.split(/[\s,]+/).map((s) => s.trim().toLowerCase()).filter(Boolean)

/** STEP 1: 새 교육과정 등록 */
export function CreateCourseForm() {
  const create = useCreateCourse()
  const fileRef = useRef<HTMLInputElement>(null)
  const [name, setName] = useState('')
  const [start, setStart] = useState('')
  const [end, setEnd] = useState('')
  const [location, setLocation] = useState('')
  const [intro, setIntro] = useState('')
  const [status, setStatus] = useState<CourseStatus>('upcoming')
  const [deadline, setDeadline] = useState('')
  const [ids, setIds] = useState<string[]>([])
  const [idInput, setIdInput] = useState('')
  const [csv, setCsv] = useState('')
  const [csvName, setCsvName] = useState('')
  const [submitted, setSubmitted] = useState(false)
  const [done, setDone] = useState<string | null>(null)

  const errors = {
    name: name.trim() === '' ? '과정명을 입력해 주세요.' : undefined,
    start: start === '' ? '시작일을 선택해 주세요.' : undefined,
    end: end === '' ? '종료일을 선택해 주세요.' : end < start ? '종료일은 시작일 이후여야 해요.' : undefined,
    deadline: deadline !== '' && end !== '' && deadline < end ? '마감일은 종료일 이후여야 해요.' : undefined,
  }
  const hasError = Object.values(errors).some(Boolean)
  const error = messageFor(create.error, '등록하지 못했어요. 잠시 후 다시 시도해 주세요.')

  const addIds = (raw: string) => {
    const next = splitIds(raw)
    if (next.length) setIds((cur) => [...new Set([...cur, ...next])])
    setIdInput('')
  }
  const onKey = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      e.preventDefault()
      addIds(idInput)
    }
  }
  const onFile = async (file: File | undefined) => {
    if (!file) return
    setCsv(await file.text())
    setCsvName(file.name)
  }

  function submit() {
    setSubmitted(true)
    setDone(null)
    if (hasError) return
    // 입력 중인 ID도 포함한다.
    const all = [...new Set([...ids, ...splitIds(idInput)])]
    create.mutate(
      { name: name.trim(), start_date: start, end_date: end, location: location.trim(), intro: intro.trim(), status, review_deadline: deadline || null, intra_ids: all, csv },
      {
        onSuccess: (c) => {
          setDone(`'${c.name}' 과정을 등록했어요. 참여 ${c.participant_count}명 · 후기 게시판이 만들어졌어요.`)
          setName('')
          setStart('')
          setEnd('')
          setLocation('')
          setIntro('')
          setStatus('upcoming')
          setDeadline('')
          setIds([])
          setIdInput('')
          setCsv('')
          setCsvName('')
          setSubmitted(false)
        },
      },
    )
  }

  return (
    <Card className="stack">
      <div className="row">
        <h2 className="card-title">새 교육과정 등록</h2>
        <span className="label">STEP 1 · 2</span>
      </div>
      <Field label="과정명" placeholder="예: 2026 경북 특화형 데이터센터 기초과정 심화기수" value={name} onChange={(e) => setName(e.target.value)} error={submitted ? errors.name : undefined} />
      <div className="g3" style={{ gap: 12 }}>
        <Field label="시작일" type="date" value={start} onChange={(e) => setStart(e.target.value)} error={submitted ? errors.start : undefined} />
        <Field label="종료일" type="date" value={end} onChange={(e) => setEnd(e.target.value)} error={submitted ? errors.end : undefined} />
        <Field label="장소" value={location} onChange={(e) => setLocation(e.target.value)} />
      </div>
      <Field label="과정 소개" multiline placeholder="게시판 상단에 보일 소개 문구" value={intro} onChange={(e) => setIntro(e.target.value)} />
      <div className="g2" style={{ gap: 12 }}>
        <div className="field">
          <label htmlFor="course-status">상태</label>
          <select id="course-status" className="input" value={status} onChange={(e) => setStatus(e.target.value as CourseStatus)}>
            {statusOptions.map((o) => (
              <option key={o.value} value={o.value}>
                {o.label}
              </option>
            ))}
          </select>
        </div>
        <Field label="후기 작성 마감(선택)" type="date" value={deadline} onChange={(e) => setDeadline(e.target.value)} error={submitted ? errors.deadline : undefined} />
      </div>
      <div className="field">
        <label htmlFor="course-ids">참여 학생</label>
        <div style={{ display: 'flex', gap: 8 }}>
          <input id="course-ids" className="input" style={{ flexGrow: 1 }} placeholder="intra ID 입력 후 Enter" value={idInput} onChange={(e) => setIdInput(e.target.value)} onKeyDown={onKey} />
          <Button variant="ghost" onClick={() => fileRef.current?.click()}>
            CSV
          </Button>
          <input ref={fileRef} type="file" accept=".csv,text/csv,text/plain" className="sr-only" tabIndex={-1} aria-label="CSV 파일 선택" onChange={(e) => onFile(e.target.files?.[0])} />
        </div>
        <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginTop: 6 }}>
          {ids.map((id) => (
            <span key={id} className="pill neu">
              {id}
              <button type="button" className="pill-x" aria-label={`${id} 삭제`} onClick={() => setIds(ids.filter((x) => x !== id))}>
                ×
              </button>
            </span>
          ))}
          {csvName && <Pill tone="ok">CSV: {csvName}</Pill>}
        </div>
        <span className="muted small">쉼표·공백·줄바꿈으로 여러 명을 한 번에 넣을 수 있어요. 가입 전 ID도 등록돼요.</span>
      </div>
      <p className="muted small">등록하면 후기 게시판이 만들어지고, 상태를 '종료 · 후기 수집'으로 바꾸면 후기를 받기 시작해요.</p>
      {error && <p role="alert" className="login-error">{error}</p>}
      {done && <p role="status" className="info">{done}</p>}
      <Button disabled={create.isPending} onClick={submit}>
        {create.isPending ? '등록 중…' : '과정 등록'}
      </Button>
    </Card>
  )
}
