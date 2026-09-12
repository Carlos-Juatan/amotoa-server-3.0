import { useState, useEffect } from 'react';
import { Settings, Eye, EyeOff, Share2, Lock, X, AlertTriangle } from 'lucide-react';
import { api } from '../services/api';

// ── Types ────────────────────────────────────────────────────────────────────

interface ItemSettings {
  [key: string]: boolean;
}

interface AccountConfig {
  visibility_settings: ItemSettings;
  data_separation_settings: ItemSettings;
}

interface TransitionOption {
  action: 'separate' | 'merge';
  inherit_account_id?: string;
}

interface SeparationPrompt {
  itemId: string;
  label: string;
}

const ITEM_LABELS: Record<string, string> = {
  series: 'Series',          animes: 'Animes',
  youtube: 'YouTube',        light_novels: 'Light Novels',
  manga: 'Manga',            jogos: 'Jogos',
  financas: 'Finanças',      saude_fitness: 'Saúde & Fitness',
  links: 'Links',            trabalho: 'Trabalho',
  estudos: 'Estudos',        filmes: 'Filmes',
};

const ALL_ITEMS = Object.keys(ITEM_LABELS);

// ── Component ────────────────────────────────────────────────────────────────

interface CustomizationPanelProps {
  activeAccount: string;
  config: AccountConfig | null;
  onSaved: (updated: AccountConfig) => void;
  onClose: () => void;
}

export function CustomizationPanel({
  activeAccount,
  config,
  onSaved,
  onClose,
}: CustomizationPanelProps) {
  const [visibility, setVisibility] = useState<ItemSettings>({});
  const [separation, setSeparation] = useState<ItemSettings>({});
  const [originalSeparation, setOriginalSeparation] = useState<ItemSettings>({});
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // T024 — separation transition prompt state
  const [pendingPrompt, setPendingPrompt] = useState<SeparationPrompt | null>(null);
  const [inheritChoice, setInheritChoice] = useState<string>(activeAccount);

  useEffect(() => {
    if (config) {
      setVisibility({ ...config.visibility_settings });
      setSeparation({ ...config.data_separation_settings });
      setOriginalSeparation({ ...config.data_separation_settings });
    }
  }, [config]);

  // ── Toggle handlers ────────────────────────────────────────────────────────

  function toggleVisibility(id: string) {
    setVisibility((prev) => ({ ...prev, [id]: !prev[id] }));
  }

  function requestSeparationToggle(id: string) {
    const current = separation[id] ?? false;
    const next = !current;

    if (!current && next) {
      // Shared → Separated: show ownership prompt (T024)
      setPendingPrompt({ itemId: id, label: ITEM_LABELS[id] });
      setInheritChoice(activeAccount);
    } else {
      // Separated → Shared: merge immediately (no prompt needed)
      setSeparation((prev) => ({ ...prev, [id]: false }));
    }
  }

  function confirmSeparation() {
    if (!pendingPrompt) return;
    setSeparation((prev) => ({ ...prev, [pendingPrompt.itemId]: true }));
    setPendingPrompt(null);
  }

  // ── Save ──────────────────────────────────────────────────────────────────

  async function handleSave() {
    setSaving(true);
    setError(null);

    try {
      // Build transition_options for items whose separation changed
      const transitionOptions: Record<string, TransitionOption> = {};

      for (const id of ALL_ITEMS) {
        const was = originalSeparation[id] ?? false;
        const will = separation[id] ?? false;
        if (was === will) continue;

        if (!was && will) {
          transitionOptions[id] = {
            action: 'separate',
            inherit_account_id: inheritChoice,
          };
        } else if (was && !will) {
          transitionOptions[id] = { action: 'merge' };
        }
      }

      await api.put('/api/accounts/config', {
        account_id: activeAccount,
        visibility_settings: visibility,
        data_separation_settings: separation,
        ...(Object.keys(transitionOptions).length > 0 && {
          transition_options: transitionOptions,
        }),
      });

      onSaved({
        visibility_settings: visibility,
        data_separation_settings: separation,
      });
      onClose();
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })
        ?.response?.data?.detail ?? 'Erro ao salvar configurações.';
      setError(msg);
    } finally {
      setSaving(false);
    }
  }

  // ── Render ────────────────────────────────────────────────────────────────

  return (
    <>
      {/* ── Separation ownership prompt (T024) ────────────────────── */}
      {pendingPrompt && (
        <div className="fixed inset-0 z-[60] flex items-center justify-center bg-black/60 backdrop-blur-sm">
          <div className="glass-panel rounded-2xl p-6 w-80 shadow-2xl">
            <div className="flex items-start gap-3 mb-4">
              <AlertTriangle className="w-5 h-5 text-amber-400 flex-shrink-0 mt-0.5" />
              <div>
                <p className="font-semibold text-slate-100 text-sm">Separar dados</p>
                <p className="text-slate-400 text-xs mt-1">
                  Qual conta ficará com os dados existentes de{' '}
                  <span className="text-slate-200 font-medium">{pendingPrompt.label}</span>?
                  A outra conta começará vazia.
                </p>
              </div>
            </div>

            <div className="space-y-2 mb-5">
              {(['car-j-works', 'car-j-home'] as const).map((acc) => (
                <label
                  key={acc}
                  className={`flex items-center gap-3 px-4 py-3 rounded-xl cursor-pointer border transition-all ${
                    inheritChoice === acc
                      ? 'border-blue-500/50 bg-blue-500/10 text-blue-300'
                      : 'border-slate-700/40 bg-slate-800/40 text-slate-400 hover:border-slate-600'
                  }`}
                >
                  <input
                    type="radio"
                    name="inherit"
                    value={acc}
                    checked={inheritChoice === acc}
                    onChange={() => setInheritChoice(acc)}
                    className="hidden"
                  />
                  <span className="text-base">{acc === 'car-j-works' ? '💼' : '🏠'}</span>
                  <span className="text-sm font-medium">{acc}</span>
                  {inheritChoice === acc && (
                    <span className="ml-auto w-1.5 h-1.5 rounded-full bg-blue-400" />
                  )}
                </label>
              ))}
            </div>

            <div className="flex gap-2">
              <button
                onClick={() => setPendingPrompt(null)}
                className="flex-1 py-2 rounded-xl text-sm text-slate-400 border border-slate-700/50 hover:border-slate-600 transition-colors"
              >
                Cancelar
              </button>
              <button
                onClick={confirmSeparation}
                className="flex-1 py-2 rounded-xl text-sm font-semibold bg-blue-500/20 text-blue-300 border border-blue-500/40 hover:bg-blue-500/30 transition-colors"
              >
                Confirmar
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ── Main panel ────────────────────────────────────────────── */}
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
        <div className="glass-panel rounded-2xl w-full max-w-lg max-h-[80vh] flex flex-col shadow-2xl">
          {/* Header */}
          <div className="flex items-center justify-between px-5 py-4 border-b border-slate-800/60">
            <div className="flex items-center gap-2.5">
              <Settings className="w-4 h-4 text-blue-400" />
              <span className="font-semibold text-slate-100 text-sm">Personalizar Dashboard</span>
            </div>
            <button
              id="customization-close"
              onClick={onClose}
              className="text-slate-500 hover:text-slate-300 transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          {/* Column headings */}
          <div className="flex items-center px-5 py-2 border-b border-slate-800/40 text-[10px] font-bold uppercase tracking-widest text-slate-500">
            <span className="flex-1">Módulo</span>
            <span className="w-20 text-center">Visível</span>
            <span className="w-20 text-center">Dados</span>
          </div>

          {/* Item rows */}
          <div className="overflow-y-auto flex-1">
            {ALL_ITEMS.map((id) => (
              <div
                key={id}
                className="flex items-center px-5 py-3 border-b border-slate-800/20 hover:bg-slate-800/20 transition-colors"
              >
                <span className="flex-1 text-sm text-slate-300">{ITEM_LABELS[id]}</span>

                {/* Visibility toggle */}
                <button
                  id={`toggle-visibility-${id}`}
                  onClick={() => toggleVisibility(id)}
                  className={`w-20 flex justify-center transition-colors ${
                    visibility[id] ? 'text-blue-400' : 'text-slate-600'
                  }`}
                  title={visibility[id] ? 'Visível' : 'Oculto'}
                >
                  {visibility[id]
                    ? <Eye className="w-4 h-4" />
                    : <EyeOff className="w-4 h-4" />}
                </button>

                {/* Separation toggle */}
                <button
                  id={`toggle-separation-${id}`}
                  onClick={() => requestSeparationToggle(id)}
                  className={`w-20 flex justify-center gap-1.5 items-center text-xs font-medium transition-colors ${
                    separation[id]
                      ? 'text-amber-400'
                      : 'text-slate-500 hover:text-slate-300'
                  }`}
                  title={separation[id] ? 'Separado' : 'Compartilhado'}
                >
                  {separation[id]
                    ? <><Lock className="w-3.5 h-3.5" /> Sep</>
                    : <><Share2 className="w-3.5 h-3.5" /> Comp</>}
                </button>
              </div>
            ))}
          </div>

          {/* Footer */}
          <div className="flex items-center justify-between gap-3 px-5 py-4 border-t border-slate-800/60">
            {error && (
              <p className="text-xs text-red-400 flex-1">{error}</p>
            )}
            <div className="flex gap-2 ml-auto">
              <button
                onClick={onClose}
                className="px-4 py-2 rounded-xl text-sm text-slate-400 border border-slate-700/50 hover:border-slate-600 transition-colors"
              >
                Cancelar
              </button>
              <button
                id="customization-save"
                onClick={handleSave}
                disabled={saving}
                className="px-5 py-2 rounded-xl text-sm font-semibold bg-blue-500/20 text-blue-300 border border-blue-500/40 hover:bg-blue-500/30 disabled:opacity-50 transition-all"
              >
                {saving ? 'Salvando…' : 'Salvar'}
              </button>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
