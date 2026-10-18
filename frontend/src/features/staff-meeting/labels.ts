import type { StaffMeetingStatus } from './api'

export const tabs: { status: StaffMeetingStatus; label: string; counted: boolean }[] = [
  { status: 'pending', label: '신규 요청', counted: true },
  { status: 'proposed', label: '시간 조율 중', counted: true },
  { status: 'confirmed', label: '확정', counted: false },
  { status: 'completed', label: '완료', counted: false },
]

export const emptyLabel: Record<string, string> = {
  pending: '새로 들어온 면담 요청이 없어요.',
  proposed: '시간을 조율 중인 면담이 없어요.',
  confirmed: '확정된 면담이 없어요.',
  completed: '완료된 면담이 없어요.',
}

export const errorLabel: Record<string, string> = {
  slot_unavailable: '같은 담당자가 그 시간에 이미 확정된 면담이 있어요. 담당자나 시간을 바꿔 주세요.',
  invalid_transition: '이미 처리된 요청이에요. 목록을 새로 불러왔어요.',
  invalid_slot: '선택할 수 없는 시간이에요.',
  staff_not_found: '운영팀 계정이 아닌 담당자예요.',
  meeting_not_found: '면담 요청을 찾을 수 없어요.',
  meeting_type_not_found: '면담 유형을 찾을 수 없어요.',
  availability_past: '지난 날짜의 가능 시간은 바꿀 수 없어요.',
  availability_too_far: '오늘부터 4주 안에서만 설정할 수 있어요.',
  slot_has_meeting: '확정된 면담이 있는 시간은 닫을 수 없어요.',
}

export const DEFAULT_LOCATION = '1층 사무실 앞'
