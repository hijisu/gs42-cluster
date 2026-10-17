import { useState } from 'react'
import { Button, Card, Field } from '../../components'
import { ApiError } from '../../lib/api'
import { useCreateWish } from './hooks'
import { errorLabel } from './labels'

/** 희망 도서 신청 */
export function WishForm() {
  const create = useCreateWish()
  const [title, setTitle] = useState('')
  const [author, setAuthor] = useState('')
  const [reason, setReason] = useState('')
  const [link, setLink] = useState('')
  const [submitted, setSubmitted] = useState(false)
  const [done, setDone] = useState(false)

  const titleError = submitted && title.trim() === '' ? '도서명을 입력해 주세요.' : undefined
  const error =
    create.error instanceof ApiError
      ? create.error.status === 400 && !create.error.code
        ? '링크 주소 형식을 확인해 주세요(https://…).'
        : (errorLabel[create.error.code ?? ''] ?? '신청하지 못했어요. 잠시 후 다시 시도해 주세요.')
      : create.isError
        ? '신청하지 못했어요.'
        : null

  return (
    <Card>
      <form
        className="stack"
        noValidate
        onSubmit={(e) => {
          e.preventDefault()
          setSubmitted(true)
          setDone(false)
          if (title.trim() === '') return
          create.mutate(
            { title: title.trim(), author: author.trim(), reason: reason.trim(), link_url: link.trim() },
            {
              onSuccess: () => {
                setTitle('')
                setAuthor('')
                setReason('')
                setLink('')
                setSubmitted(false)
                setDone(true)
              },
            },
          )
        }}
      >
        <h2 className="card-title">희망 도서 신청</h2>
        <Field label="도서명" placeholder="예: 이것이 리눅스다" value={title} onChange={(e) => setTitle(e.target.value)} error={titleError} />
        <Field label="저자 · 출판사" value={author} onChange={(e) => setAuthor(e.target.value)} />
        <Field label="신청 사유" multiline placeholder="어떤 과제나 학습에 필요한지 적어 주세요" value={reason} onChange={(e) => setReason(e.target.value)} />
        <Field label="링크(선택)" type="url" placeholder="https://" value={link} onChange={(e) => setLink(e.target.value)} />
        {error && <p role="alert" className="login-error">{error}</p>}
        {done && <p role="status" className="info">신청했어요. 운영팀이 검토하면 아래 '내 신청 · 신고'에 상태가 표시돼요.</p>}
        <Button type="submit" disabled={create.isPending}>
          {create.isPending ? '신청 중…' : '신청하기'}
        </Button>
      </form>
    </Card>
  )
}
