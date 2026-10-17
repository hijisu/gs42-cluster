import type { HTMLAttributes } from 'react'

interface CardProps extends HTMLAttributes<HTMLElement> {
  as?: 'div' | 'article' | 'section'
}

export function Card({ as: Tag = 'div', className = '', ...rest }: CardProps) {
  return <Tag className={`card ${className}`.trim()} {...rest} />
}
