import { parsePushPayload, safeLink } from './pushPayload'

describe('parsePushPayload', () => {
  it('JSON payload를 알림 내용으로 바꾼다', () => {
    expect(parsePushPayload('{"title":"회의실 예약이 승인되었어요","body":"10.22 10:00","link":"/room"}')).toEqual({
      title: '회의실 예약이 승인되었어요',
      body: '10.22 10:00',
      link: '/room',
    })
  })

  it('일반 텍스트나 빈 payload는 기본 제목으로 대체한다', () => {
    expect(parsePushPayload('그냥 문구')).toEqual({ title: '42gs-cluster', body: '그냥 문구', link: '/' })
    expect(parsePushPayload(null)).toEqual({ title: '42gs-cluster', body: '', link: '/' })
    expect(parsePushPayload('{"body":3}')).toEqual({ title: '42gs-cluster', body: '', link: '/' })
  })

  it('앱 밖으로 나가는 link는 홈으로 바꾼다', () => {
    expect(safeLink('/meeting')).toBe('/meeting')
    expect(safeLink('https://evil.example')).toBe('/')
    expect(safeLink('//evil.example')).toBe('/')
    expect(safeLink('')).toBe('/')
  })
})
