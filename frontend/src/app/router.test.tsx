import { render, screen, within } from '@testing-library/react'
import { createMemoryRouter, RouterProvider } from 'react-router-dom'
import { routes } from './router'
import { staffNav, studentNav } from './routes'

const paths = [...studentNav, ...staffNav].map((n) => n.path)

describe('routes', () => {
  it('라우트가 10개이고 시안 파일 이름과 1:1이다', () => {
    expect(paths).toHaveLength(10)
    expect(new Set([...studentNav, ...staffNav].map((n) => n.design)).size).toBe(10)
  })

  it.each(paths)('%s 가 열린다', (path) => {
    const router = createMemoryRouter(routes, { initialEntries: [path] })
    render(<RouterProvider router={router} />)
    expect(screen.getByRole('main')).toBeInTheDocument()
    expect(screen.getByRole('heading', { level: 1 })).toBeInTheDocument()
  })

  it('임시 홈에 면담/회의실 바로가기가 있다', () => {
    const router = createMemoryRouter(routes, { initialEntries: ['/'] })
    render(<RouterProvider router={router} />)
    const main = within(screen.getByRole('main'))
    expect(main.getByRole('link', { name: '면담 신청' })).toHaveAttribute('href', '/meeting')
    expect(main.getByRole('link', { name: '회의실 예약' })).toHaveAttribute('href', '/room')
  })
})
