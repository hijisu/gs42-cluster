import { useState } from 'react'
import { Button, Field, Modal } from '../../components'
import type { Book, BookInput } from './api'
import { messageFor } from './errors'
import { useSaveBook } from './hooks'

const empty: BookInput = { code: '', title: '', category: '', quantity: 1, author: '', publisher: '' }

/** book이 null이면 새 도서 추가, 있으면 수정(도서 코드는 바꿀 수 없다). */
export function BookFormModal({ open, book, categories, onClose }: { open: boolean; book: Book | null; categories: string[]; onClose: () => void }) {
  const save = useSaveBook()
  const [form, setForm] = useState<BookInput>(book ?? empty)
  const [submitted, setSubmitted] = useState(false)
  const set = <K extends keyof BookInput>(key: K, value: BookInput[K]) => setForm((f) => ({ ...f, [key]: value }))
  const close = () => {
    setSubmitted(false)
    save.reset()
    onClose()
  }
  const invalid = (v: string) => (submitted && v.trim() === '' ? '필수 항목이에요.' : undefined)
  const error = messageFor(save.error, '저장하지 못했어요. 잠시 후 다시 시도해 주세요.')
  const submit = () => {
    setSubmitted(true)
    if (!form.code.trim() || !form.title.trim() || !form.category.trim()) return
    save.mutate({ id: book?.id, body: { ...form, quantity: Number(form.quantity) } }, { onSuccess: close })
  }
  return (
    <Modal
      open={open}
      title={book ? '도서 수정' : '도서 추가'}
      onClose={close}
      actions={
        <>
          <Button variant="ghost" onClick={close}>취소</Button>
          <Button disabled={save.isPending} onClick={submit}>{save.isPending ? '저장 중…' : '저장'}</Button>
        </>
      }
    >
      <Field label="도서 코드" value={form.code} disabled={!!book} onChange={(e) => set('code', e.target.value)} placeholder="예: GSIA-IT-999" error={invalid(form.code)} />
      <Field label="제목" value={form.title} onChange={(e) => set('title', e.target.value)} error={invalid(form.title)} />
      <Field label="분류" list="book-categories" value={form.category} onChange={(e) => set('category', e.target.value)} error={invalid(form.category)} />
      <datalist id="book-categories">{categories.map((c) => <option key={c} value={c} />)}</datalist>
      <Field label="저자" value={form.author} onChange={(e) => set('author', e.target.value)} />
      <Field label="출판사" value={form.publisher} onChange={(e) => set('publisher', e.target.value)} />
      <Field label="수량" type="number" min={0} value={form.quantity} onChange={(e) => set('quantity', Number(e.target.value))} />
      {error && <p role="alert" className="login-error">{error}</p>}
    </Modal>
  )
}
