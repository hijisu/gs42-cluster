import { useState } from 'react'
import { CoursesTable } from './CoursesTable'
import { CreateCourseForm } from './CreateCourseForm'
import { EditCourseModal } from './EditCourseModal'
import { useStaffCourses } from './hooks'
import { ReviewRequestForm } from './ReviewRequestForm'

export function StaffCoursePage() {
  const courses = useStaffCourses()
  const [selected, setSelected] = useState<number | null>(null)
  const [editing, setEditing] = useState<number | null>(null)
  return (
    <>
      <div className="head">
        <div>
          <p className="label">04 · COURSE ADMIN</p>
          <h1 className="h1" style={{ marginTop: 8 }}>교육과정 · 후기 관리</h1>
          <p className="sub">교육과정을 등록하고 참여 학생을 추가하면 후기 게시판이 열리고, 학생들에게 후기 작성 알림을 보낼 수 있어요.</p>
        </div>
      </div>
      {courses.isPending && <p className="muted" role="status">불러오는 중…</p>}
      {courses.isError && <p role="alert">교육과정을 불러오지 못했어요.</p>}
      {courses.data && <CoursesTable courses={courses.data} onRequest={setSelected} onEdit={setEditing} />}
      <div className="g2" style={{ alignItems: 'start' }}>
        <CreateCourseForm />
        <ReviewRequestForm courses={courses.data ?? []} selectedId={selected} onSelect={setSelected} />
      </div>
      <EditCourseModal courseId={editing} onClose={() => setEditing(null)} />
    </>
  )
}
