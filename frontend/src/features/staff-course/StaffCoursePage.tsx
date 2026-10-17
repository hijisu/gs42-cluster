import { useState } from 'react'
import { Button } from '../../components'
import { CoursesTable } from './CoursesTable'
import { CreateCourseModal } from './CreateCourseModal'
import { EditCourseModal } from './EditCourseModal'
import { useStaffCourses } from './hooks'
import { ReviewRequestModal } from './ReviewRequestModal'

export function StaffCoursePage() {
  const courses = useStaffCourses()
  const [requesting, setRequesting] = useState<number | null>(null)
  const [editing, setEditing] = useState<number | null>(null)
  const [creating, setCreating] = useState(false)
  const [done, setDone] = useState<string | null>(null)
  return (
    <>
      <div className="head">
        <div>
          <p className="label">04 · COURSE ADMIN</p>
          <h1 className="h1" style={{ marginTop: 8 }}>교육과정 · 후기 관리</h1>
          <p className="sub">교육과정을 등록하고 참여 학생을 추가하면 후기 게시판이 열리고, 학생들에게 후기 작성 알림을 보낼 수 있어요.</p>
        </div>
        <Button onClick={() => { setDone(null); setCreating(true) }}>+ 교육과정 등록</Button>
      </div>
      {done && <p role="status" className="info">{done}</p>}
      {courses.isPending && <p className="muted" role="status">불러오는 중…</p>}
      {courses.isError && <p role="alert">교육과정을 불러오지 못했어요.</p>}
      {courses.data && <CoursesTable courses={courses.data} onRequest={setRequesting} onEdit={setEditing} />}
      <CreateCourseModal open={creating} onClose={() => setCreating(false)} onDone={(m) => { setCreating(false); setDone(m) }} />
      <ReviewRequestModal course={courses.data?.find((c) => c.id === requesting) ?? null} onClose={() => setRequesting(null)} />
      <EditCourseModal courseId={editing} onClose={() => setEditing(null)} />
    </>
  )
}
