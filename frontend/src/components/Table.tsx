import type { ReactNode } from 'react'

export interface Column<T> {
  key: string
  header: string
  render: (row: T) => ReactNode
}

interface TableProps<T> {
  columns: Column<T>[]
  rows: T[]
  rowKey: (row: T) => string | number
  caption?: string
  empty?: ReactNode
}

export function Table<T>({ columns, rows, rowKey, caption, empty = '표시할 내용이 없습니다.' }: TableProps<T>) {
  return (
    <div className="table-wrap">
      <table className="table" role="table">
        {caption && <caption className="sr-only">{caption}</caption>}
        <thead>
          <tr role="row">
            {columns.map((c) => (
              <th key={c.key} scope="col" role="columnheader">
                {c.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.length === 0 ? (
            <tr role="row">
              <td colSpan={columns.length} className="muted table-empty" role="cell">
                {empty}
              </td>
            </tr>
          ) : (
            rows.map((row) => (
              <tr key={rowKey(row)} role="row">
                {columns.map((c) => (
                  // 좁은 화면에서는 행이 카드로 바뀌고 열 이름이 data-label로 표시된다(CSS). 표 의미는 role로 유지한다.
                  <td key={c.key} role="cell" data-label={c.header}>
                    {c.render(row)}
                  </td>
                ))}
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  )
}
