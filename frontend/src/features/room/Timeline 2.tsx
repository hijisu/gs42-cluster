import { Card } from '../../components'
import { formatDayLabel } from '../../lib/datetime'
import type { Availability } from './api'
import { hourStateLabel } from './labels'

// 선택한 날짜의 장소 × 시간 타임라인 (확정/대기/빔/차단)
export function Timeline({ date, data }: { date: string; data: Availability }) {
  const hours = data.rooms[0]?.hours.map((h) => h.hour) ?? []
  const cols = `repeat(${hours.length}, minmax(0, 1fr))`
  return (
    <Card className="stack">
      <div className="row">
        <h2 className="card-title">{formatDayLabel(date)} 예약 현황</h2>
        <span className="muted small">선택한 날짜 기준</span>
      </div>
      <div className="timeline-scroll">
        <div className="timeline" role="table" aria-label="장소별 예약 현황">
          <div className="tl-row">
            <span className="label">장소</span>
            <div className="tl-cells" style={{ gridTemplateColumns: cols }}>
              {hours.map((h) => (
                <span key={h} className="mono muted" style={{ fontSize: 11 }}>
                  {String(h).padStart(2, '0')}
                </span>
              ))}
            </div>
          </div>
          {data.rooms.map(({ room, hours: hs }) => (
            <div key={room.id} className="tl-row tl-body" role="row" aria-label={room.name}>
              <div className="tl-name">
                <span style={{ fontWeight: 700, fontSize: 14 }}>{room.name}</span>
                <span className="muted" style={{ fontSize: 12 }}>
                  {[room.capacity_note, room.equipment].filter(Boolean).join(' · ')}
                </span>
              </div>
              <div className="tl-cells" style={{ gridTemplateColumns: cols }}>
                {hs.map((h) => (
                  <div key={h.hour} className={`tl-cell ${h.state}`} role="cell" title={`${h.hour}시 ${hourStateLabel[h.state]}`}>
                    <span className="sr-only">
                      {h.hour}시 {hourStateLabel[h.state]}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>
      <div className="legend muted">
        <span><i className="sw approved" />예약 확정</span>
        <span><i className="sw pending" />승인 대기</span>
        <span><i className="sw free" />비어 있음</span>
        <span><i className="sw blocked" />이용 불가</span>
      </div>
    </Card>
  )
}
