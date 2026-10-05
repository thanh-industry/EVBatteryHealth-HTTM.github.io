import { ArrowDown, ArrowUp, ArrowUpDown } from 'lucide-react'
import { useMemo, useState, type ReactNode } from 'react'
import { cx } from '../../lib/utils'
import { EmptyState } from './EmptyState'

export interface DataTableColumn<T> {
  key: string
  header: string
  render?: (row: T) => ReactNode
  accessor?: (row: T) => string | number | null
  sortable?: boolean
  align?: 'left' | 'right'
  numeric?: boolean
}

export interface DataTableProps<T> {
  columns: DataTableColumn<T>[]
  rows: T[]
  getRowId: (row: T, index: number) => string | number
  caption: string
  emptyTitle?: string
  emptyDescription?: string
  onRowClick?: (row: T) => void
  selectedRowId?: string | number | null
}

type SortDirection = 'asc' | 'desc'

export function DataTable<T>({
  columns,
  rows,
  getRowId,
  caption,
  emptyTitle = 'No rows to show',
  emptyDescription,
  onRowClick,
  selectedRowId,
}: DataTableProps<T>) {
  const [sort, setSort] = useState<{ key: string; direction: SortDirection } | null>(null)

  const sortedRows = useMemo(() => {
    if (!sort) return rows
    const column = columns.find((c) => c.key === sort.key)
    if (!column?.accessor) return rows
    const accessor = column.accessor
    const copy = [...rows]
    copy.sort((a, b) => {
      const av = accessor(a)
      const bv = accessor(b)
      if (av === null) return 1
      if (bv === null) return -1
      if (typeof av === 'number' && typeof bv === 'number') return av - bv
      return String(av).localeCompare(String(bv))
    })
    if (sort.direction === 'desc') copy.reverse()
    return copy
  }, [rows, sort, columns])

  if (rows.length === 0) {
    return <EmptyState title={emptyTitle} description={emptyDescription} />
  }

  const toggleSort = (key: string) => {
    setSort((prev) => {
      if (!prev || prev.key !== key) return { key, direction: 'asc' }
      if (prev.direction === 'asc') return { key, direction: 'desc' }
      return null
    })
  }

  return (
    <div className="overflow-x-auto rounded-lg border border-border">
      <table className="w-full min-w-[640px] border-collapse text-sm">
        <caption className="sr-only">{caption}</caption>
        <thead>
          <tr className="border-b border-border bg-muted">
            {columns.map((col) => {
              const isSorted = sort?.key === col.key
              const ariaSort = !col.sortable ? undefined : isSorted ? (sort?.direction === 'asc' ? 'ascending' : 'descending') : 'none'
              return (
                <th
                  key={col.key}
                  scope="col"
                  aria-sort={ariaSort}
                  className={cx(
                    'px-lg py-md text-left font-semibold text-text-secondary',
                    col.align === 'right' && 'text-right',
                  )}
                >
                  {col.sortable ? (
                    <button
                      type="button"
                      onClick={() => toggleSort(col.key)}
                      className={cx(
                        'inline-flex items-center gap-xs hover:text-text-primary',
                        col.align === 'right' && 'flex-row-reverse',
                      )}
                    >
                      {col.header}
                      {isSorted ? (
                        sort?.direction === 'asc' ? (
                          <ArrowUp className="h-3.5 w-3.5" aria-hidden="true" />
                        ) : (
                          <ArrowDown className="h-3.5 w-3.5" aria-hidden="true" />
                        )
                      ) : (
                        <ArrowUpDown className="h-3.5 w-3.5 opacity-40" aria-hidden="true" />
                      )}
                    </button>
                  ) : (
                    col.header
                  )}
                </th>
              )
            })}
          </tr>
        </thead>
        <tbody>
          {sortedRows.map((row, index) => {
            const rowId = getRowId(row, index)
            const clickable = !!onRowClick
            return (
              <tr
                key={rowId}
                onClick={clickable ? () => onRowClick?.(row) : undefined}
                tabIndex={clickable ? 0 : undefined}
                role={clickable ? 'button' : undefined}
                onKeyDown={
                  clickable
                    ? (e) => {
                        if (e.key === 'Enter' || e.key === ' ') {
                          e.preventDefault()
                          onRowClick?.(row)
                        }
                      }
                    : undefined
                }
                className={cx(
                  'border-b border-border last:border-0',
                  clickable && 'cursor-pointer hover:bg-muted focus-visible:bg-muted',
                  selectedRowId === rowId && 'bg-muted',
                )}
              >
                {columns.map((col) => (
                  <td
                    key={col.key}
                    className={cx(
                      'px-lg py-md text-text-primary',
                      col.numeric && 'font-mono tabular-nums',
                      col.align === 'right' && 'text-right',
                    )}
                  >
                    {col.render ? col.render(row) : String(col.accessor?.(row) ?? '')}
                  </td>
                ))}
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}
