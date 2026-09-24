import React, { useState, useEffect, useCallback } from 'react';
import { Download, Loader2, CheckCircle2, AlertTriangle, Pause } from 'lucide-react';
import { api } from '../services/api';

// ─── Types ──────────────────────────────────────────────────────────────────

type JobStatus = 'pending' | 'running' | 'paused' | 'completed' | 'failed';

interface JobSummary {
  job_id: string;
  status: JobStatus;
  media_type: string;
  progress: {
    total_discovered: number;
    imported: number;
    skipped: number;
    failed: number;
  };
}

interface NavbarBatchIndicatorProps {
  /** Called when the indicator is clicked — parent opens the BatchImportModal */
  onOpen: () => void;
}

// ─── Helpers ────────────────────────────────────────────────────────────────

function deriveIndicatorState(jobs: JobSummary[]): {
  icon: React.ReactNode;
  label: string;
  colorClass: string;
  pulse: boolean;
} {
  const running = jobs.filter((j) => j.status === 'running' || j.status === 'pending');
  const paused = jobs.filter((j) => j.status === 'paused');
  const failed = jobs.filter((j) => j.status === 'failed');

  if (running.length > 0) {
    const total = running.reduce((s, j) => s + j.progress.total_discovered, 0);
    const done = running.reduce(
      (s, j) => s + j.progress.imported + j.progress.skipped + j.progress.failed,
      0
    );
    const pct = total > 0 ? Math.round((done / total) * 100) : 0;
    return {
      icon: <Loader2 className="w-4 h-4 animate-spin" />,
      label: `${running.length} importando… ${pct}%`,
      colorClass: 'text-blue-400 border-blue-500/40 bg-blue-500/10',
      pulse: true,
    };
  }

  if (paused.length > 0) {
    return {
      icon: <Pause className="w-4 h-4" />,
      label: `${paused.length} pausado(s)`,
      colorClass: 'text-orange-400 border-orange-500/40 bg-orange-500/10',
      pulse: false,
    };
  }

  if (failed.length > 0) {
    return {
      icon: <AlertTriangle className="w-4 h-4" />,
      label: `${failed.length} falha(s)`,
      colorClass: 'text-red-400 border-red-500/40 bg-red-500/10',
      pulse: false,
    };
  }

  // All completed or empty — show a neutral import icon
  return {
    icon: <Download className="w-4 h-4" />,
    label: 'Importação em Lote',
    colorClass: 'text-slate-400 border-slate-600/40 bg-slate-700/20',
    pulse: false,
  };
}

// ─── Component ───────────────────────────────────────────────────────────────

export const NavbarBatchIndicator: React.FC<NavbarBatchIndicatorProps> = ({ onOpen }) => {
  const [jobs, setJobs] = useState<JobSummary[]>([]);

  const fetchJobs = useCallback(async () => {
    try {
      const res = await api.get<JobSummary[]>('/api/batch-jobs');
      setJobs(res.data);
    } catch {
      // silently ignore — this is a passive background indicator
    }
  }, []);

  // Poll every 5 seconds when any job is active; otherwise every 30 s
  useEffect(() => {
    fetchJobs();
    const hasActive = jobs.some(
      (j) => j.status === 'running' || j.status === 'pending'
    );
    const interval = setInterval(fetchJobs, hasActive ? 5000 : 30000);
    return () => clearInterval(interval);
  }, [fetchJobs, jobs.length]);

  const { icon, label, colorClass, pulse } = deriveIndicatorState(jobs);

  return (
    <button
      id="navbar-batch-indicator"
      onClick={onOpen}
      title="Abrir painel de importação em lote"
      className={`
        flex items-center gap-2 px-3 py-1.5 rounded-lg border text-xs font-medium
        transition-all duration-200 hover:scale-105 active:scale-95
        ${colorClass}
        ${pulse ? 'animate-pulse' : ''}
      `}
    >
      {icon}
      <span className="hidden sm:inline">{label}</span>
    </button>
  );
};
