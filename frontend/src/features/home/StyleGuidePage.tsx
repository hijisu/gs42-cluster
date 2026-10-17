import { useState } from 'react'
import { Button, Card, Chip, Field, Modal, Pill, Table } from '../../components'

// 개발 서버 전용 공통 컴포넌트 미리보기(/styleguide). 프로덕션 빌드에는 라우트가 등록되지 않는다.
const rows = [
  { id: 1, name: '면담 신청', status: '승인' },
  { id: 2, name: '회의실 예약', status: '대기' },
]

export function StyleGuidePage() {
  const [open, setOpen] = useState(false)
  const [chip, setChip] = useState(true)
  return (
    <>
      <h1 className="h1">스타일가이드</h1>
      <Card style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
        <div className="row" style={{ justifyContent: 'flex-start' }}>
          <Button>기본</Button>
          <Button variant="secondary">보조</Button>
          <Button variant="danger">위험</Button>
          <Button size="sm">작게(카드·표)</Button>
          <span className="notice" style={{ padding: 8 }}>
            <Button variant="ondark">어두운 배너용</Button>
          </span>
        </div>
        <div className="row" style={{ justifyContent: 'flex-start' }}>
          <Pill tone="ok">승인</Pill>
          <Pill tone="wait">대기</Pill>
          <Pill tone="neu">중립</Pill>
          <Pill tone="done">종료</Pill>
          <Chip selected={chip} onClick={() => setChip(!chip)}>
            칩
          </Chip>
        </div>
        <Field label="제목" hint="힌트 문구" placeholder="입력" />
        <Field label="내용" multiline error="오류 문구" />
        <Table
          caption="예시"
          columns={[
            { key: 'name', header: '항목', render: (r) => r.name },
            { key: 'status', header: '상태', render: (r) => <Pill tone={r.status === '승인' ? 'ok' : 'wait'}>{r.status}</Pill> },
          ]}
          rows={rows}
          rowKey={(r) => r.id}
        />
        <Button onClick={() => setOpen(true)}>모달 열기</Button>
      </Card>
      <Modal
        open={open}
        title="모달 제목"
        onClose={() => setOpen(false)}
        actions={<Button onClick={() => setOpen(false)}>닫기</Button>}
      >
        <p>모달 본문입니다.</p>
      </Modal>
    </>
  )
}
