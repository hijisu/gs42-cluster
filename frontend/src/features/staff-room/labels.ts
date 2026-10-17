export const roomStatusLabel = { open: '예약 받는 중', blocked: '교육 기간 차단' } as const

export const errorLabel: Record<string, string> = {
  room_conflict: '같은 시간에 이미 승인된 예약이 있어요. 대체 장소로 배정하거나 반려해 주세요.',
  room_blocked: '현재 예약을 받지 않는 장소예요.',
  invalid_transition: '이미 처리된 요청이에요. 목록을 새로 불러왔어요.',
  reservation_not_found: '예약 요청을 찾을 수 없어요.',
  room_not_found: '장소를 찾을 수 없어요.',
  reason_required: '반려 사유를 입력해 주세요.',
  past_time: '지난 시간은 예약할 수 없어요.',
  outside_hours: '운영 시간 밖이거나 하루를 넘기는 시간이에요.',
  invalid_range: '종료 시간은 시작 시간보다 늦어야 하고 30분 단위여야 해요.',
  invalid_rules: '운영 시간(시작 < 종료)과 이용수칙을 1줄 이상 입력해 주세요.',
  room_block_conflict: '운영팀이 차단한 시간이라 예약할 수 없어요.',
  invalid_block: '차단 정보를 확인해 주세요(사유, 시간, 반복 종료일, 매주 반복은 요일 1개 이상).',
  block_not_found: '차단 일정을 찾을 수 없어요. 목록을 새로 불러왔어요.',
  room_code_taken: '이미 사용 중인 장소 코드예요.',
}
