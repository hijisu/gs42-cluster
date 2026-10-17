import { render } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { createMemoryRouter, RouterProvider } from 'react-router-dom'
import { routes } from './app/router'

export type Handler = (req: { method: string; url: string; body: unknown }) => { status?: number; json?: unknown } | undefined

/** fetch를 URL 기반으로 모킹한다. 핸들러가 undefined를 돌려주면 다음 핸들러로 넘어가고, 모두 없으면 빈 배열(200). */
export function mockApi(...handlers: Handler[]) {
  const calls: { method: string; url: string; body: unknown }[] = []
  vi.stubGlobal(
    'fetch',
    vi.fn(async (url: string, init?: RequestInit) => {
      const req = { method: init?.method ?? 'GET', url, body: init?.body ? JSON.parse(init.body as string) : undefined }
      calls.push(req)
      for (const h of handlers) {
        const r = h(req)
        if (r) return new Response(r.status === 204 ? null : JSON.stringify(r.json ?? {}), { status: r.status ?? 200 })
      }
      // 핸들러가 없으면 화면이 깨지지 않는 빈 응답을 돌려준다.
      if (url.includes('/books/my-requests')) return new Response(JSON.stringify({ reports: [], wishes: [] }), { status: 200 })
      if (url.includes('/books/')) return new Response(JSON.stringify({ total: 0, categories: [], results: [] }), { status: 200 })
      if (url.includes('/notifications')) return new Response(JSON.stringify({ unread_count: 0, items: [] }), { status: 200 })
      if (url.includes('/rooms/availability')) return new Response(JSON.stringify({ date: '', rooms: [] }), { status: 200 })
      if (url.endsWith('/rooms/rules')) return new Response(JSON.stringify({ open_hour: 9, close_hour: 22, step_minutes: 30, usage_rules: [] }), { status: 200 })
      if (url.includes('/staff/availability')) return new Response(JSON.stringify({ slots: [], customized_days: [] }), { status: 200 })
      return new Response('[]', { status: 200 })
    }),
  )
  return calls
}

export const asUser = (role: 'student' | 'staff'): Handler => (req) =>
  req.url.endsWith('/auth/me') ? { json: { id: 1, intra_id: 'jisu', name: '지수', role, slack_id: null } } : undefined

export const anonymous: Handler = (req) => (req.url.endsWith('/auth/me') ? { status: 401, json: { detail: 'x' } } : undefined)

export function renderAt(path: string) {
  const router = createMemoryRouter(routes, { initialEntries: [path] })
  render(
    <QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}>
      <RouterProvider router={router} />
    </QueryClientProvider>,
  )
  return router
}
