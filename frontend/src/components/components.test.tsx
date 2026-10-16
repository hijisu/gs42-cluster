import { useState } from 'react'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Button, Chip, Field, Modal, Pill, Table } from '.'

describe('공통 컴포넌트', () => {
  it('Button은 기본 type=button이고 variant 클래스를 붙인다', () => {
    render(<Button variant="teal" size="sm">저장</Button>)
    const btn = screen.getByRole('button', { name: '저장' })
    expect(btn).toHaveAttribute('type', 'button')
    expect(btn).toHaveClass('btn', 'teal', 'sm')
  })

  it('Pill은 tone 클래스를 붙인다', () => {
    render(<Pill tone="wait">대기</Pill>)
    expect(screen.getByText('대기')).toHaveClass('pill', 'wait')
  })

  it('Chip은 aria-pressed로 선택 상태를 알린다', async () => {
    function Demo() {
      const [on, setOn] = useState(false)
      return <Chip selected={on} onClick={() => setOn(!on)}>필터</Chip>
    }
    render(<Demo />)
    const chip = screen.getByRole('button', { name: '필터' })
    expect(chip).toHaveAttribute('aria-pressed', 'false')
    await userEvent.click(chip)
    expect(chip).toHaveAttribute('aria-pressed', 'true')
  })

  it('Field는 label과 입력을 연결하고 오류를 알린다', () => {
    render(<Field label="제목" hint="힌트" error="필수 항목입니다" />)
    const input = screen.getByLabelText('제목')
    expect(input).toHaveAttribute('aria-invalid', 'true')
    expect(input).toHaveAccessibleDescription('힌트 필수 항목입니다')
    expect(screen.getByRole('alert')).toHaveTextContent('필수 항목입니다')
  })

  it('Field multiline은 textarea를 렌더한다', () => {
    render(<Field label="내용" multiline />)
    expect(screen.getByLabelText('내용').tagName).toBe('TEXTAREA')
  })

  it('Table은 행을 그리고 비면 안내 문구를 보여준다', () => {
    const columns = [{ key: 'n', header: '이름', render: (r: { n: string }) => r.n }]
    const { rerender } = render(<Table columns={columns} rows={[{ n: 'a' }]} rowKey={(r) => r.n} />)
    expect(screen.getByRole('columnheader', { name: '이름' })).toBeInTheDocument()
    expect(screen.getByRole('cell', { name: 'a' })).toBeInTheDocument()
    rerender(<Table columns={columns} rows={[]} rowKey={(r) => r.n} />)
    expect(screen.getByText('표시할 내용이 없습니다.')).toBeInTheDocument()
  })

  it('Modal은 열리면 dialog가 되고 Esc·배경 클릭으로 닫는다', async () => {
    const onClose = vi.fn()
    const { rerender } = render(<Modal open={false} title="제목" onClose={onClose}>본문</Modal>)
    expect(screen.queryByRole('dialog')).toBeNull()
    rerender(<Modal open title="제목" onClose={onClose}>본문</Modal>)
    expect(screen.getByRole('dialog', { name: '제목' })).toBeInTheDocument()
    await userEvent.keyboard('{Escape}')
    expect(onClose).toHaveBeenCalledTimes(1)
    await userEvent.click(document.querySelector('.scrim')!)
    expect(onClose).toHaveBeenCalledTimes(2)
  })
})
