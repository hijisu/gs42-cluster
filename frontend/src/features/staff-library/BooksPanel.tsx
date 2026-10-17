import { useState } from 'react'
import { Button, Card, Field, Modal, Table, type Column } from '../../components'
import type { Book } from './api'
import { BookFormModal } from './BookFormModal'
import { messageFor } from './errors'
import { useBooks, useDeleteBook } from './hooks'

export function BooksPanel() {
  const [q, setQ] = useState('')
  const [page, setPage] = useState(1)
  const books = useBooks(q.trim(), page)
  const del = useDeleteBook()
  const [editing, setEditing] = useState<Book | 'new' | null>(null)
  const [removing, setRemoving] = useState<Book | null>(null)
  const error = messageFor(del.error, '삭제하지 못했어요. 잠시 후 다시 시도해 주세요.')

  const columns: Column<Book>[] = [
    { key: 'title', header: '제목', render: (b) => <span style={{ fontWeight: 600 }}>{b.title}</span> },
    { key: 'author', header: '저자', render: (b) => b.author || '-' },
    { key: 'category', header: '분류', render: (b) => b.category },
    { key: 'quantity', header: '수량', render: (b) => <span className="mono">{b.quantity}권</span> },
    {
      key: 'act',
      header: '',
      render: (b) => (
        <span style={{ display: 'flex', gap: 8, justifyContent: 'flex-end', whiteSpace: 'nowrap' }}>
          <Button variant="ghost" size="sm" aria-label={`${b.title} 수정`} onClick={() => setEditing(b)}>수정</Button>
          <Button variant="ghost" size="sm" aria-label={`${b.title} 삭제`} onClick={() => setRemoving(b)}>삭제</Button>
        </span>
      ),
    },
  ]

  const data = books.data
  return (
    <Card className="stack" style={{ gap: 8 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12, flexWrap: 'wrap', alignItems: 'end' }}>
        <h2 className="card-title">도서 목록</h2>
        <Button onClick={() => setEditing('new')}>도서 추가</Button>
      </div>
      <Field label="도서 검색" value={q} onChange={(e) => { setQ(e.target.value); setPage(1) }} placeholder="제목·저자·출판사·ISBN" />
      {books.isPending && <p className="muted" role="status">불러오는 중…</p>}
      {books.isError && <p role="alert">도서를 불러오지 못했어요.</p>}
      {error && <p role="alert" className="login-error">{error}</p>}
      {data && (
        <>
          <p className="muted small" role="status">
            총 {data.total}종{data.total > data.results.length ? ` 중 ${data.results.length}종 표시` : ''}
          </p>
          {data.total > 20 && <nav aria-label="도서 페이지" className="row">
            <Button variant="ghost" disabled={page <= 1 || books.isPlaceholderData} onClick={() => setPage(page - 1)}>이전</Button>
            <span>{page} / {Math.ceil(data.total / 20)} 페이지</span>
            <Button variant="ghost" disabled={page >= Math.ceil(data.total / 20) || books.isPlaceholderData} onClick={() => setPage(page + 1)}>다음</Button>
          </nav>}
          <Table caption="도서 목록" columns={columns} rows={data.results} rowKey={(b) => b.id} empty="조건에 맞는 도서가 없어요." />
        </>
      )}
      {editing && (
        <BookFormModal
          key={editing === 'new' ? 'new' : editing.id}
          open
          book={editing === 'new' ? null : editing}
          categories={data?.categories ?? []}
          onClose={() => setEditing(null)}
        />
      )}
      <Modal
        open={removing !== null}
        title="도서 삭제"
        onClose={() => setRemoving(null)}
        actions={
          <>
            <Button variant="ghost" onClick={() => setRemoving(null)}>돌아가기</Button>
            <Button variant="warn" disabled={del.isPending} onClick={() => removing && del.mutate(removing.id, { onSettled: () => setRemoving(null) })}>삭제</Button>
          </>
        }
      >
        {removing && <p>「{removing.title}」을(를) 삭제할까요? 이 도서에 접수된 분실·훼손 신고도 함께 사라져요.</p>}
      </Modal>
    </Card>
  )
}
