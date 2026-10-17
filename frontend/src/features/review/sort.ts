import type { Course } from './api'

export type CourseSort = 'reg' | 'name' | 'new' | 'old' | 'most' | 'least'

export const sortOptions: { value: CourseSort; label: string }[] = [
  { value: 'reg', label: '등록순' },
  { value: 'name', label: '과정 이름순' },
  { value: 'new', label: '최신순' },
  { value: 'old', label: '과거순' },
  { value: 'most', label: '후기 많은 순' },
  { value: 'least', label: '후기 적은 순' },
]

const compare: Record<CourseSort, (a: Course, b: Course) => number> = {
  reg: (a, b) => a.id - b.id,
  name: (a, b) => a.name.localeCompare(b.name, 'ko'),
  new: (a, b) => b.start_date.localeCompare(a.start_date),
  old: (a, b) => a.start_date.localeCompare(b.start_date),
  most: (a, b) => b.review_count - a.review_count,
  least: (a, b) => a.review_count - b.review_count,
}

/** 같은 값이면 등록순으로 안정 정렬한다. */
export const sortCourses = (courses: Course[], sort: CourseSort): Course[] =>
  [...courses].sort((a, b) => compare[sort](a, b) || a.id - b.id)
