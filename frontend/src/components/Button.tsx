import type { ButtonHTMLAttributes } from 'react'

export type ButtonVariant = 'primary' | 'ghost' | 'teal' | 'warn'

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant
  size?: 'md' | 'sm'
}

const variantClass: Record<ButtonVariant, string> = {
  primary: '',
  ghost: 'ghost',
  teal: 'teal',
  warn: 'warn',
}

export function Button({ variant = 'primary', size = 'md', className = '', type = 'button', ...rest }: ButtonProps) {
  const cls = ['btn', variantClass[variant], size === 'sm' ? 'sm' : '', className].filter(Boolean).join(' ')
  return <button type={type} className={cls} {...rest} />
}
