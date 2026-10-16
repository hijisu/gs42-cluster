import type { ButtonHTMLAttributes } from 'react'

interface ChipProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  selected?: boolean
}

export function Chip({ selected = false, className = '', type = 'button', ...rest }: ChipProps) {
  return <button type={type} aria-pressed={selected} className={`chip ${className}`.trim()} {...rest} />
}
