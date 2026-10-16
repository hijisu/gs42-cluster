import { createBrowserRouter } from 'react-router-dom'
import { Layout } from '../components/Layout'
import { PlaceholderPage } from '../components/PlaceholderPage'
import { HomePage } from '../features/home/HomePage'
import { staffNav, studentNav } from './routes'

const page = (title: string) => <PlaceholderPage title={title} />

export const routes = [
  {
    path: '/',
    element: (
      <Layout
        variant="student"
        nav={studentNav}
        switchTo={{ to: '/staff', label: '교육운영팀 화면 보기' }}
      />
    ),
    children: [
      { index: true, element: <HomePage /> },
      { path: 'meeting', element: page('면담 신청') },
      { path: 'room', element: page('회의실 예약') },
      { path: 'library', element: page('오아시스 도서') },
      { path: 'reviews', element: page('교육과정 후기') },
    ],
  },
  {
    path: '/staff',
    element: (
      <Layout
        variant="staff"
        nav={staffNav}
        switchTo={{ to: '/', label: '교육생 화면 보기' }}
      />
    ),
    children: [
      { index: true, element: page('운영 홈') },
      { path: 'meeting', element: page('면담 관리') },
      { path: 'room', element: page('회의실 관리') },
      { path: 'library', element: page('도서 관리') },
      { path: 'courses', element: page('교육과정 · 후기 관리') },
    ],
  },
]

export const router = createBrowserRouter(routes)
