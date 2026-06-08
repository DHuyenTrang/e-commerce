import type { ButtonHTMLAttributes, ReactNode } from 'react'
import { clsx } from 'clsx'

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger'
  children: ReactNode
}

export function Button({ className, variant = 'primary', type = 'button', ...props }: ButtonProps) {
  return <button className={clsx('btn', `btn-${variant}`, className)} type={type} {...props} />
}
