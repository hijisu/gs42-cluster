import { formatDateTime, formatDateTimeLong, formatPeriod, kstDate, kstDateFromToday, kstTime } from './datetime'

describe('KST 변환', () => {
  it('UTC 시각을 KST로 바꾼다', () => {
    expect(kstTime('2026-10-19T06:00:00Z')).toBe('15:00')
    expect(kstDate('2026-10-19T06:00:00Z')).toBe('2026-10-19')
    expect(formatDateTime('2026-10-19T06:00:00Z')).toBe('10.19 15:00')
    expect(formatDateTimeLong('2026-10-19T06:00:00Z')).toBe('10.19 (월) 15:00')
  })

  it('UTC 날짜가 달라지는 시각도 KST 날짜로 센다', () => {
    expect(kstDate('2026-10-18T16:00:00Z')).toBe('2026-10-19')
    expect(kstDateFromToday(1, new Date('2026-10-18T16:00:00Z'))).toBe('2026-10-20')
  })
})

describe('교육 기간', () => {
  it('같은 해면 시작일에만 연도를 붙인다', () => {
    expect(formatPeriod('2026-10-15', '2026-10-24')).toBe('2026.10.15–10.24')
  })
  it('해가 바뀌면 양쪽에 연도를 붙인다', () => {
    expect(formatPeriod('2026-12-28', '2027-01-09')).toBe('2026.12.28–2027.01.09')
  })
})
