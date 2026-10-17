import { createBrowserRouter } from 'react-router-dom'
import { Layout } from '../components/Layout'
import { PlaceholderPage } from '../components/PlaceholderPage'
import { HomePage } from '../features/home/HomePage'
import { StyleGuidePage } from '../features/home/StyleGuidePage'
import { ReviewPage } from '../features/review/ReviewPage'
import { RoomPage } from '../features/room/RoomPage'
import { StaffMeetingPage } from '../features/staff-meeting/StaffMeetingPage'
import { StaffRoomPage } from '../features/staff-room/StaffRoomPage'
import { MeetingPage } from '../features/meeting/MeetingPage'
import { RequireAuth } from '../features/auth/guards'
import { LoginPage } from '../features/auth/LoginPage'
import { staffNav, studentNav } from './routes'

const page = (title: string) => <PlaceholderPage title={title} />

export const routes = [
  { path: '/login', element: <LoginPage /> },
  {
    element: <RequireAuth />,
    children: [
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
      { path: 'meeting', element: <MeetingPage /> },
      { path: 'room', element: <RoomPage /> },
      { path: 'library', element: page('오아시스 도서') },
      { path: 'reviews', element: <ReviewPage /> },
      ...(import.meta.env.DEV ? [{ path: 'styleguide', element: <StyleGuidePage /> }] : []),
    ],
  },
  ],
  },
  {
    element: <RequireAuth role="staff" />,
    children: [
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
      { path: 'meeting', element: <StaffMeetingPage /> },
      { path: 'room', element: <StaffRoomPage /> },
      { path: 'library', element: page('도서 관리') },
      { path: 'courses', element: page('교육과정 · 후기 관리') },
    ],
  },
    ],
  },
]


export const router = createBrowserRouter(routes)
