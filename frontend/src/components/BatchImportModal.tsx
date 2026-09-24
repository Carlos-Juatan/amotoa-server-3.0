import React, { useState, useEffect, useCallback, useRef } from 'react';
import {
  X,
  Play,
  Pause,
  RefreshCw,
  AlertTriangle,
  CheckCircle2,
  Clock,
  ChevronDown,
  ChevronUp,
  Download,
  Loader2,
} from 'lucide-react';
import { api } from '../services/api';

// ─── Types ─────────────────────────────────────────────────────────────────

type MediaTypeOption = 'anime' | 'manga' | 'light_novel';
type JobStatus = 'pending' | 'running' | 'paused' | 'completed' | 'failed';

interface JobProgress {
  total_discovered: number;
  imported: number;
  skipped: number;
  failed: number;
}

interface ErrorEntry {
  mal_id: number;
  title: string;
  reason: string;
  timestamp: string;
}

interface BatchJob {
  job_id: string;
  media_type: MediaTypeOption;
  year_start: number;
  year_end: number;
  status: JobStatus;
  current_cursor: { year: number; season_index: number; page: number };
  progress: JobProgress;
  error_logs: ErrorEntry[];
  created_at: string;
  updated_at: string;
}

interface BatchImportModalProps {
  isOpen: boolean;
  onClose: () => void;
}

// ─── Constants ──────────────────────────────────────────────────────────────

const MEDIA_TYPE_LABELS: Record<MediaTypeOption, string> = {
  anime: 'Anime',
  manga: 'Mangá',
  light_novel: 'Light Novel',
};

const STATUS_CONFIG: Record<
  JobStatus,
  { label: string; color: string; icon: React.ReactNode }
> = {
  pending: {
    label: 'Aguardando',
    color: 'text-yellow-400',
    icon: <Clock className="w-4 h-4" />,
  },
  running: {
    label: 'Executando',
    color: 'text-blue-400',
    icon: <Loader2 className="w-4 h-4 animate-spin" />,
  },
  paused: {
    label: 'Pausado',
    color: 'text-orange-400',
    icon: <Pause className="w-4 h-4" />,
  },
  completed: {
    label: 'Concluído',
    color: 'text-green-400',
    icon: <CheckCircle2 className="w-4 h-4" />,
  },
  failed: {
    label: 'Falhou',
    color: 'text-red-400',
    icon: <AlertTriangle className="w-4 h-4" />,
  },
};

const CURRENT_YEAR = new Date().getFullYear();

// ─── Sub-components ─────────────────────────────────────────────────────────

const ProgressBar: React.FC<{ progress: JobProgress; status: JobStatus }> = ({
  progress,
  status,
}) => {
  const total = progress.total_discovered;
  const processed = progress.imported + progress.skipped + progress.failed;
  const pct = total > 0 ? Math.min((processed / total) * 100, 100) : 0;

  const barColor =
    status === 'failed'
      ? 'bg-red-500'
      : status === 'completed'
      ? 'bg-green-500'
      : status === 'paused'
      ? 'bg-orange-500'
      : 'bg-blue-500';

  return (
    <div className="space-y-1">
      <div className="h-2 bg-slate-700 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-700 ${barColor}`}
          style={{ width: `${pct}%` }}
        />
      </div>
      <div className="flex justify-between text-xs text-slate-400">
        <span>
          {processed.toLocaleString()} / {total.toLocaleString()} itens
        </span>
        <span>{pct.toFixed(1)}%</span>
      </div>
    </div>
  );
};

const JobCard: React.FC<{
  job: BatchJob;
  onPause: (id: string) => Promise<void>;
  onResume: (id: string) => Promise<void>;
}> = ({ job, onPause, onResume }) => {
  const [showErrors, setShowErrors] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);
  const cfg = STATUS_CONFIG[job.status];

  const handlePause = async () => {
    setActionLoading(true);
    try {
      await onPause(job.job_id);
    } finally {
      setActionLoading(false);
    }
  };

  const handleResume = async () => {
    setActionLoading(true);
    try {
      await onResume(job.job_id);
    } finally {
      setActionLoading(false);
    }
  };

  return (
    <div className="glass-card rounded-xl p-4 border border-slate-700/50 space-y-3">
      {/* Header */}
      <div className="flex items-start justify-between gap-3">
        <div>
          <div className="flex items-center gap-2">
            <span className={`flex items-center gap-1.5 text-sm font-medium ${cfg.color}`}>
              {cfg.icon}
              {cfg.label}
            </span>
            <span className="text-slate-500 text-xs">•</span>
            <span className="text-slate-300 text-sm font-semibold">
              {MEDIA_TYPE_LABELS[job.media_type]}
            </span>
          </div>
          <p className="text-slate-400 text-xs mt-0.5">
            {job.year_start === job.year_end
              ? `Ano ${job.year_start}`
              : `${job.year_start} – ${job.year_end}`}{' '}
            •{' '}
            <span className="font-mono text-slate-500 text-[10px]">
              {job.job_id.slice(0, 8)}…
            </span>
          </p>
        </div>

        {/* Actions */}
        <div className="flex gap-2 shrink-0">
          {job.status === 'running' && (
            <button
              id={`pause-job-${job.job_id.slice(0, 8)}`}
              onClick={handlePause}
              disabled={actionLoading}
              className="flex items-center gap-1.5 px-3 py-1.5 bg-orange-500/20 hover:bg-orange-500/30 text-orange-400 rounded-lg text-xs font-medium transition-colors disabled:opacity-50"
            >
              {actionLoading ? (
                <Loader2 className="w-3 h-3 animate-spin" />
              ) : (
                <Pause className="w-3 h-3" />
              )}
              Pausar
            </button>
          )}
          {(job.status === 'paused' || job.status === 'failed') && (
            <button
              id={`resume-job-${job.job_id.slice(0, 8)}`}
              onClick={handleResume}
              disabled={actionLoading}
              className="flex items-center gap-1.5 px-3 py-1.5 bg-blue-500/20 hover:bg-blue-500/30 text-blue-400 rounded-lg text-xs font-medium transition-colors disabled:opacity-50"
            >
              {actionLoading ? (
                <Loader2 className="w-3 h-3 animate-spin" />
              ) : (
                <Play className="w-3 h-3" />
              )}
              Retomar
            </button>
          )}
        </div>
      </div>

      {/* Progress bar */}
      <ProgressBar progress={job.progress} status={job.status} />

      {/* Stats */}
      <div className="grid grid-cols-4 gap-2 text-center">
        {[
          { label: 'Importados', value: job.progress.imported, color: 'text-green-400' },
          { label: 'Pulados', value: job.progress.skipped, color: 'text-slate-400' },
          { label: 'Falhas', value: job.progress.failed, color: 'text-red-400' },
          { label: 'Total', value: job.progress.total_discovered, color: 'text-slate-300' },
        ].map(({ label, value, color }) => (
          <div key={label} className="bg-slate-800/50 rounded-lg py-2">
            <div className={`text-base font-bold ${color}`}>{value.toLocaleString()}</div>
            <div className="text-[10px] text-slate-500 mt-0.5">{label}</div>
          </div>
        ))}
      </div>

      {/* Error log toggle */}
      {job.error_logs.length > 0 && (
        <div>
          <button
            onClick={() => setShowErrors((p) => !p)}
            className="flex items-center gap-1.5 text-xs text-red-400/80 hover:text-red-400 transition-colors"
          >
            <AlertTriangle className="w-3 h-3" />
            {job.error_logs.length} erro(s) registrado(s)
            {showErrors ? (
              <ChevronUp className="w-3 h-3" />
            ) : (
              <ChevronDown className="w-3 h-3" />
            )}
          </button>

          {showErrors && (
            <div className="mt-2 max-h-36 overflow-y-auto custom-scrollbar space-y-1 pr-1">
              {job.error_logs.map((err, i) => (
                <div
                  key={i}
                  className="bg-red-900/20 border border-red-800/30 rounded p-2 text-[11px]"
                >
                  <div className="text-red-300 font-medium truncate">
                    {err.title} (ID: {err.mal_id})
                  </div>
                  <div className="text-red-400/70 mt-0.5 truncate">{err.reason}</div>
                  <div className="text-slate-500 mt-0.5 text-[10px]">
                    {new Date(err.timestamp).toLocaleTimeString('pt-BR')}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

// ─── Main Modal ─────────────────────────────────────────────────────────────

export const BatchImportModal: React.FC<BatchImportModalProps> = ({ isOpen, onClose }) => {
  const [jobs, setJobs] = useState<BatchJob[]>([]);
  const [mediaType, setMediaType] = useState<MediaTypeOption>('anime');
  const [yearStart, setYearStart] = useState(CURRENT_YEAR - 2);
  const [yearEnd, setYearEnd] = useState(CURRENT_YEAR);
  const [isCreating, setIsCreating] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // ── Data fetching ──────────────────────────────────────────────────────

  const fetchJobs = useCallback(async () => {
    try {
      const res = await api.get<BatchJob[]>('/api/batch-jobs');
      setJobs(res.data);
    } catch {
      // silently ignore polling errors
    }
  }, []);

  useEffect(() => {
    if (!isOpen) return;
    fetchJobs();
    // Poll every 4 seconds while modal is open
    pollingRef.current = setInterval(fetchJobs, 4000);
    return () => {
      if (pollingRef.current) clearInterval(pollingRef.current);
    };
  }, [isOpen, fetchJobs]);

  // Stop polling when no jobs are active
  const hasActiveJobs = jobs.some((j) => j.status === 'running' || j.status === 'pending');
  useEffect(() => {
    if (!hasActiveJobs && pollingRef.current) {
      clearInterval(pollingRef.current);
      pollingRef.current = null;
    } else if (hasActiveJobs && !pollingRef.current && isOpen) {
      pollingRef.current = setInterval(fetchJobs, 4000);
    }
  }, [hasActiveJobs, isOpen, fetchJobs]);

  // ── Actions ────────────────────────────────────────────────────────────

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);

    if (yearStart > yearEnd) {
      setFormError('O ano inicial deve ser ≤ ao ano final.');
      return;
    }
    if (yearStart < 1950 || yearEnd > 2100) {
      setFormError('Intervalo de anos deve estar entre 1950 e 2100.');
      return;
    }

    setIsCreating(true);
    try {
      await api.post('/api/batch-jobs', {
        media_type: mediaType,
        year_start: yearStart,
        year_end: yearEnd,
      });
      await fetchJobs();
    } catch (err: any) {
      setFormError(
        err?.response?.data?.detail ?? 'Erro ao criar o job. Tente novamente.'
      );
    } finally {
      setIsCreating(false);
    }
  };

  const handlePause = async (jobId: string) => {
    await api.post(`/api/batch-jobs/${jobId}/pause`);
    await fetchJobs();
  };

  const handleResume = async (jobId: string) => {
    await api.post(`/api/batch-jobs/${jobId}/resume`);
    await fetchJobs();
  };

  // ── Render ─────────────────────────────────────────────────────────────

  if (!isOpen) return null;

  return (
    <div
      id="batch-import-modal-overlay"
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
      onClick={(e) => e.target === e.currentTarget && onClose()}
    >
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" />

      {/* Panel */}
      <div
        id="batch-import-modal"
        className="relative z-10 glass-panel border border-slate-700/60 rounded-2xl shadow-2xl w-full max-w-xl max-h-[90vh] flex flex-col overflow-hidden"
      >
        {/* ── Header ── */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-700/50">
          <div className="flex items-center gap-2.5">
            <Download className="w-5 h-5 text-indigo-400" />
            <h2 className="text-lg font-bold text-slate-100">Importação em Lote</h2>
          </div>
          <button
            id="close-batch-modal"
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-100 hover:bg-slate-700/60 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* ── Scrollable body ── */}
        <div className="flex-1 overflow-y-auto custom-scrollbar px-6 py-5 space-y-6">
          {/* New job form */}
          <form onSubmit={handleCreate} className="space-y-4">
            <h3 className="text-sm font-semibold text-slate-300 uppercase tracking-wide">
              Novo Job
            </h3>

            {/* Media type */}
            <div className="flex gap-2">
              {(['anime', 'manga', 'light_novel'] as MediaTypeOption[]).map((t) => (
                <button
                  key={t}
                  type="button"
                  id={`batch-media-type-${t}`}
                  onClick={() => setMediaType(t)}
                  className={`flex-1 py-2 rounded-lg text-sm font-medium transition-colors ${
                    mediaType === t
                      ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-900/30'
                      : 'bg-slate-800 text-slate-400 hover:bg-slate-700 hover:text-slate-200'
                  }`}
                >
                  {MEDIA_TYPE_LABELS[t]}
                </button>
              ))}
            </div>

            {/* Year range */}
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1">
                <label className="text-xs text-slate-400 font-medium">Ano Inicial</label>
                <input
                  id="batch-year-start"
                  type="number"
                  min={1950}
                  max={CURRENT_YEAR}
                  value={yearStart}
                  onChange={(e) => setYearStart(parseInt(e.target.value))}
                  className="w-full px-3 py-2 bg-slate-800 border border-slate-700 text-slate-100 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none transition"
                />
              </div>
              <div className="space-y-1">
                <label className="text-xs text-slate-400 font-medium">Ano Final</label>
                <input
                  id="batch-year-end"
                  type="number"
                  min={1950}
                  max={CURRENT_YEAR}
                  value={yearEnd}
                  onChange={(e) => setYearEnd(parseInt(e.target.value))}
                  className="w-full px-3 py-2 bg-slate-800 border border-slate-700 text-slate-100 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none transition"
                />
              </div>
            </div>

            {formError && (
              <p className="text-red-400 text-xs flex items-center gap-1.5">
                <AlertTriangle className="w-3.5 h-3.5" />
                {formError}
              </p>
            )}

            <button
              id="batch-start-job"
              type="submit"
              disabled={isCreating}
              className="w-full py-2.5 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white font-semibold rounded-xl transition-all flex items-center justify-center gap-2 shadow-lg shadow-indigo-900/30"
            >
              {isCreating ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Criando…
                </>
              ) : (
                <>
                  <Play className="w-4 h-4" />
                  Iniciar Importação
                </>
              )}
            </button>
          </form>

          {/* Jobs list */}
          {jobs.length > 0 && (
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-semibold text-slate-300 uppercase tracking-wide">
                  Jobs Ativos
                </h3>
                <button
                  onClick={fetchJobs}
                  title="Atualizar lista"
                  className="p-1.5 text-slate-500 hover:text-slate-300 transition-colors rounded-lg hover:bg-slate-700/50"
                >
                  <RefreshCw className="w-4 h-4" />
                </button>
              </div>

              {jobs.map((job) => (
                <JobCard
                  key={job.job_id}
                  job={job}
                  onPause={handlePause}
                  onResume={handleResume}
                />
              ))}
            </div>
          )}

          {jobs.length === 0 && (
            <div className="text-center py-8 text-slate-500">
              <Download className="w-10 h-10 mx-auto mb-2 opacity-30" />
              <p className="text-sm">Nenhum job de importação ainda.</p>
              <p className="text-xs mt-1">Crie um acima para importar histórico.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
