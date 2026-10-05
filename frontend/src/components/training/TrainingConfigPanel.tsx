import { useState, type FormEvent } from 'react'
import type { Algorithm, Dataset, TrainingRequest } from '../../types/api'
import { Button } from '../ui/Button'
import { Input } from '../ui/Input'
import { Select } from '../ui/Select'

export interface TrainingConfigPanelProps {
  datasets: Dataset[]
  onSubmit: (request: TrainingRequest) => void
  isSubmitting: boolean
  serverError?: string | null
}

const ALGORITHM_OPTIONS = [
  { value: 'svm', label: 'SVM' },
  { value: 'random_forest', label: 'Random Forest' },
  { value: 'logistic_regression', label: 'Logistic Regression' },
]

interface SvmParams { C: string; kernel: 'rbf' | 'linear'; gamma: 'scale' | 'auto' }
interface RfParams { n_estimators: string; max_depth: string; min_samples_leaf: string }
interface LrParams { C: string; max_iter: string }

const DEFAULT_SVM: SvmParams = { C: '1.0', kernel: 'rbf', gamma: 'scale' }
const DEFAULT_RF: RfParams = { n_estimators: '200', max_depth: '', min_samples_leaf: '1' }
const DEFAULT_LR: LrParams = { C: '1.0', max_iter: '1000' }

export function TrainingConfigPanel({ datasets, onSubmit, isSubmitting, serverError }: TrainingConfigPanelProps) {
  const readyDatasets = datasets.filter((d) => d.status === 'ready')
  const [datasetId, setDatasetId] = useState<string>(readyDatasets[0] ? String(readyDatasets[0].id) : '')
  const [algorithm, setAlgorithm] = useState<Algorithm>('random_forest')
  const [testSize, setTestSize] = useState('0.2')
  const [svmParams, setSvmParams] = useState<SvmParams>(DEFAULT_SVM)
  const [rfParams, setRfParams] = useState<RfParams>(DEFAULT_RF)
  const [lrParams, setLrParams] = useState<LrParams>(DEFAULT_LR)
  const [formError, setFormError] = useState<string | null>(null)

  const noDatasets = readyDatasets.length === 0

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault()
    setFormError(null)

    if (!datasetId) {
      setFormError('Choose a dataset first.')
      return
    }
    const size = Number(testSize)
    if (Number.isNaN(size) || size < 0.1 || size > 0.4) {
      setFormError('Test size must be between 0.1 and 0.4.')
      return
    }

    let params: Record<string, number | string | boolean> = {}
    if (algorithm === 'svm') {
      const c = Number(svmParams.C)
      if (Number.isNaN(c) || c <= 0) {
        setFormError('C must be a positive number.')
        return
      }
      params = { C: c, kernel: svmParams.kernel, gamma: svmParams.gamma }
    } else if (algorithm === 'random_forest') {
      const nEstimators = Number(rfParams.n_estimators)
      const minLeaf = Number(rfParams.min_samples_leaf)
      if (Number.isNaN(nEstimators) || nEstimators <= 0) {
        setFormError('Number of trees must be a positive integer.')
        return
      }
      params = { n_estimators: nEstimators, min_samples_leaf: minLeaf || 1 }
      if (rfParams.max_depth.trim() !== '') {
        const depth = Number(rfParams.max_depth)
        if (Number.isNaN(depth) || depth <= 0) {
          setFormError('Max depth must be a positive integer, or left blank for unlimited.')
          return
        }
        params.max_depth = depth
      }
    } else {
      const c = Number(lrParams.C)
      const maxIter = Number(lrParams.max_iter)
      if (Number.isNaN(c) || c <= 0) {
        setFormError('C must be a positive number.')
        return
      }
      params = { C: c, max_iter: maxIter || 1000 }
    }

    onSubmit({
      dataset_id: Number(datasetId),
      algorithm,
      test_size: size,
      params,
    })
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-xl rounded-lg border border-border bg-surface p-xl shadow-sm">
      <Select
        label="Dataset"
        value={datasetId}
        onChange={(e) => setDatasetId(e.target.value)}
        disabled={noDatasets}
        options={
          noDatasets
            ? [{ value: '', label: 'No ready datasets - upload one first' }]
            : readyDatasets.map((d) => ({ value: String(d.id), label: `${d.name} (${d.row_count.toLocaleString()} rows)` }))
        }
      />

      <Select
        label="Algorithm"
        value={algorithm}
        onChange={(e) => setAlgorithm(e.target.value as Algorithm)}
        options={ALGORITHM_OPTIONS}
      />

      <Input
        label="Test size"
        type="number"
        min={0.1}
        max={0.4}
        step={0.05}
        value={testSize}
        onChange={(e) => setTestSize(e.target.value)}
        hint="Fraction of rows held out for evaluation (0.1 - 0.4)."
      />

      {algorithm === 'svm' && (
        <div className="grid grid-cols-1 gap-lg sm:grid-cols-3">
          <Input label="C" type="number" min={0.001} step={0.1} value={svmParams.C} onChange={(e) => setSvmParams({ ...svmParams, C: e.target.value })} />
          <Select
            label="Kernel"
            value={svmParams.kernel}
            onChange={(e) => setSvmParams({ ...svmParams, kernel: e.target.value as SvmParams['kernel'] })}
            options={[{ value: 'rbf', label: 'RBF' }, { value: 'linear', label: 'Linear' }]}
          />
          <Select
            label="Gamma"
            value={svmParams.gamma}
            onChange={(e) => setSvmParams({ ...svmParams, gamma: e.target.value as SvmParams['gamma'] })}
            options={[{ value: 'scale', label: 'Scale' }, { value: 'auto', label: 'Auto' }]}
          />
        </div>
      )}

      {algorithm === 'random_forest' && (
        <div className="grid grid-cols-1 gap-lg sm:grid-cols-3">
          <Input
            label="Number of trees"
            type="number"
            min={1}
            value={rfParams.n_estimators}
            onChange={(e) => setRfParams({ ...rfParams, n_estimators: e.target.value })}
          />
          <Input
            label="Max depth"
            type="number"
            min={1}
            placeholder="Unlimited"
            value={rfParams.max_depth}
            onChange={(e) => setRfParams({ ...rfParams, max_depth: e.target.value })}
            hint="Leave blank for unlimited depth."
          />
          <Input
            label="Min samples per leaf"
            type="number"
            min={1}
            value={rfParams.min_samples_leaf}
            onChange={(e) => setRfParams({ ...rfParams, min_samples_leaf: e.target.value })}
          />
        </div>
      )}

      {algorithm === 'logistic_regression' && (
        <div className="grid grid-cols-1 gap-lg sm:grid-cols-2">
          <Input label="C" type="number" min={0.001} step={0.1} value={lrParams.C} onChange={(e) => setLrParams({ ...lrParams, C: e.target.value })} />
          <Input
            label="Max iterations"
            type="number"
            min={1}
            value={lrParams.max_iter}
            onChange={(e) => setLrParams({ ...lrParams, max_iter: e.target.value })}
          />
        </div>
      )}

      {(formError || serverError) && (
        <p role="alert" className="text-sm text-critical">
          {formError ?? serverError}
        </p>
      )}

      <div>
        <Button
          type="submit"
          loading={isSubmitting}
          disabled={noDatasets}
          disabledReason={noDatasets ? 'Upload a ready dataset before training.' : undefined}
        >
          Start training
        </Button>
      </div>
    </form>
  )
}
