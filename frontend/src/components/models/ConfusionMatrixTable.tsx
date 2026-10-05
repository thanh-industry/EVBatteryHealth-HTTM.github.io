import type { ConfusionMatrix } from '../../types/api'
import { cx } from '../../lib/utils'

export interface ConfusionMatrixTableProps {
  confusionMatrix: ConfusionMatrix
}

/**
 * Confusion matrix as a simple table (never a heatmap-only view - every
 * cell shows its number so color is never the only signal).
 */
export function ConfusionMatrixTable({ confusionMatrix }: ConfusionMatrixTableProps) {
  const { labels, matrix } = confusionMatrix
  const max = Math.max(1, ...matrix.flat())

  return (
    <div className="overflow-x-auto">
      <table className="border-collapse text-sm">
        <caption className="sr-only">Confusion matrix: rows are actual class, columns are predicted class</caption>
        <thead>
          <tr>
            <th scope="col" className="px-md py-sm" />
            <th scope="colgroup" colSpan={labels.length} className="px-md py-sm text-center text-caption font-medium text-text-muted">
              Predicted
            </th>
          </tr>
          <tr>
            <th scope="col" className="px-md py-sm text-right text-caption font-medium text-text-muted">
              Actual
            </th>
            {labels.map((label) => (
              <th key={label} scope="col" className="px-md py-sm text-center font-semibold text-text-primary">
                {label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {matrix.map((row, i) => (
            <tr key={labels[i]}>
              <th scope="row" className="px-md py-sm text-right font-semibold text-text-primary">
                {labels[i]}
              </th>
              {row.map((value, j) => {
                const intensity = value / max
                const isDiagonal = i === j
                return (
                  <td
                    key={j}
                    className={cx(
                      'min-w-[56px] px-md py-sm text-center font-mono tabular-nums',
                      isDiagonal ? 'font-semibold text-text-primary' : 'text-text-secondary',
                    )}
                    style={{ backgroundColor: `color-mix(in srgb, var(--color-primary) ${Math.round(8 + intensity * 30)}%, white)` }}
                  >
                    {value}
                  </td>
                )
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
