import type { ButtonHTMLAttributes } from 'react'

/**
 * 버튼 규격(역할 3가지 + 어두운 배너용 1가지)
 * - primary: 기본(검정). 화면·폼·모달의 주 동작
 * - secondary: 보조(흰색 + 테두리)
 * - danger: 위험(빨간 테두리). 반려·삭제·취소·신고처럼 되돌리기 어려운 동작
 * - ondark: 어두운 배너 위에서만 쓰는 강조(티얼)
 * 크기 2단계: md=36px(페이지·폼·모달 하단), sm=28px(카드·표 안). 모바일(900px 이하)은 둘 다 44px.
 */
export type ButtonVariant = 'primary' | 'secondary' | 'danger' | 'ondark'

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant
  size?: 'md' | 'sm'
}

const variantClass: Record<ButtonVariant, string> = {
  primary: '',
  secondary: 'secondary',
  danger: 'danger',
  ondark: 'ondark',
}

export function Button({ variant = 'primary', size = 'md', className = '', type = 'button', ...rest }: ButtonProps) {
  const cls = ['btn', variantClass[variant], size === 'sm' ? 'sm' : '', className].filter(Boolean).join(' ')
  return <button type={type} className={cls} {...rest} />
}
