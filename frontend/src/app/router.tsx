import { createBrowserRouter } from 'react-router-dom'
import { Layout } from '../components/Layout'
import { HomePage } from '../features/home/HomePage'
import { StyleGuidePage } from '../features/home/StyleGuidePage'
import { ReviewPage } from '../features/review/ReviewPage'
import { RoomPage } from '../features/room/RoomPage'
import { StaffMeetingPage } from '../features/staff-meeting/StaffMeetingPage'
import { StaffRoomPage } from '../features/staff-room/StaffRoomPage'
import { StaffCoursePage } from '../features/staff-course/StaffCoursePage'
import { LibraryPage } from '../features/library/LibraryPage'
import { StaffHomePage } from '../features/staff-home/StaffHomePage'
import { StaffLibraryPage } from '../features/staff-library/StaffLibraryPage'
import { MeetingPage } from '../features/meeting/MeetingPage'
import { RequireAuth } from '../features/auth/guards'
import { LoginPage } from '../features/auth/LoginPage'
import { staffNav, studentNav } from './routes'

export const routes = [
  { path: '/login', element: <LoginPage /> },
  {
    element: <RequireAuth role="student" />,
    children: [
  {
    path: '/',
    element: (
      <Layout variant="student" nav={studentNav} />
    ),
    children: [
      { index: true, element: <HomePage /> },
      { path: 'meeting', element: <MeetingPage /> },
      { path: 'room', element: <RoomPage /> },
      { path: 'library', element: <LibraryPage /> },
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
      <Layout variant="staff" nav={staffNav} />
    ),
    children: [
      { index: true, element: <StaffHomePage /> },
      { path: 'meeting', element: <StaffMeetingPage /> },
      { path: 'room', element: <StaffRoomPage /> },
      { path: 'library', element: <StaffLibraryPage /> },
      { path: 'courses', element: <StaffCoursePage /> },
    ],
  },
    ],
  },
]


export const router = createBrowserRouter(routes)
