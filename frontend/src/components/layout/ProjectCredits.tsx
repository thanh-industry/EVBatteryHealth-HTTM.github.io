import { GraduationCap, Users } from 'lucide-react'

/**
 * Academic attribution for the project. Shown on the login page (before sign
 * in) and in the application shell (after sign in), so the authors and
 * supervisor are visible from every screen.
 *
 * Names are Vietnamese and must keep their diacritics. Do not transliterate
 * them to plain ASCII.
 */

export const PROJECT_AUTHORS = [
  { name: 'Phạm Văn Thành', studentId: '2570496' },
  { name: 'Đồng Quang Trí', studentId: '2570523' },
] as const

export const PROJECT_SUPERVISOR = 'Quản Thành Thơ'

interface ProjectCreditsProps {
  /** `full` for the login page, `compact` for the sidebar and mobile footer. */
  variant?: 'full' | 'compact'
  className?: string
}

export function ProjectCredits({ variant = 'full', className = '' }: ProjectCreditsProps) {
  if (variant === 'compact') {
    return (
      <section
        className={`border-t border-border px-lg py-lg ${className}`}
        aria-label="Thông tin nhóm thực hiện"
      >
        <ul className="flex flex-col gap-xs">
          {PROJECT_AUTHORS.map((a) => (
            <li key={a.studentId} className="text-xs leading-snug text-text-secondary">
              <span className="font-medium text-text-primary">{a.name}</span>
              <span className="ml-sm font-mono text-text-muted">{a.studentId}</span>
            </li>
          ))}
        </ul>
        <p className="mt-sm text-xs leading-snug text-text-muted">
          GVHD: <span className="text-text-secondary">{PROJECT_SUPERVISOR}</span>
        </p>
      </section>
    )
  }

  return (
    <section
      className={`rounded-lg border border-border bg-muted/60 p-lg ${className}`}
      aria-label="Thông tin nhóm thực hiện"
    >
      <h2 className="flex items-center gap-sm text-xs font-semibold uppercase tracking-wide text-text-secondary">
        <Users className="h-4 w-4" aria-hidden="true" />
        Nhóm thực hiện
      </h2>

      <ul className="mt-md flex flex-col gap-sm">
        {PROJECT_AUTHORS.map((a) => (
          <li key={a.studentId} className="flex flex-wrap items-baseline justify-between gap-sm">
            <span className="text-sm font-medium text-text-primary">{a.name}</span>
            <span className="font-mono text-xs text-text-secondary">
              MSSV {a.studentId}
            </span>
          </li>
        ))}
      </ul>

      <p className="mt-md flex items-center gap-sm border-t border-border pt-md text-sm text-text-secondary">
        <GraduationCap className="h-4 w-4 shrink-0" aria-hidden="true" />
        <span>
          Giáo viên hướng dẫn:{' '}
          <span className="font-medium text-text-primary">{PROJECT_SUPERVISOR}</span>
        </span>
      </p>
    </section>
  )
}
