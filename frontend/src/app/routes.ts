// 메뉴·라우트 정의. design/*.dc.html 파일 이름과 1:1 (Main→/, StaffMain→/staff ...).
export interface NavItem {
  no: string
  label: string
  path: string
  /** 시안 파일 이름 */
  design: string
  /** 있으면 메뉴·바로가기를 새 탭 외부 링크로 연결한다(내부 라우트는 그대로 두고 화면이 완성되면 교체). */
  external?: string
}

export const LIBRARY_URL = 'https://42gslib.pages.dev/'

export const studentNav: NavItem[] = [
  { no: '00', label: '홈', path: '/', design: 'Main' },
  { no: '01', label: '면담 신청', path: '/meeting', design: 'Meeting' },
  { no: '02', label: '회의실 예약', path: '/room', design: 'Room' },
  // 도서 화면(#28) 전까지 임시로 42gslib 외부 링크(#100). 화면이 완성되면 external을 지운다.
  { no: '03', label: '오아시스 도서', path: '/library', design: 'Library', external: LIBRARY_URL },
  { no: '04', label: '교육과정 후기', path: '/reviews', design: 'Reviews' },
]

export const staffNav: NavItem[] = [
  { no: '00', label: '운영 홈', path: '/staff', design: 'StaffMain' },
  { no: '01', label: '면담 관리', path: '/staff/meeting', design: 'StaffMeeting' },
  { no: '02', label: '회의실 관리', path: '/staff/room', design: 'StaffRoom' },
  { no: '03', label: '도서 관리', path: '/staff/library', design: 'StaffLibrary' },
  { no: '04', label: '교육과정 · 후기 관리', path: '/staff/courses', design: 'StaffCourses' },
]

export const STATS_URL = 'https://gs42stat.hijae.dev/home'
