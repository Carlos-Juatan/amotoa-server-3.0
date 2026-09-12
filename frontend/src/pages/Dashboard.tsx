import { useState, useEffect, useCallback } from 'react';
import { SlidersHorizontal } from 'lucide-react';
import { DashboardGrid } from '../components/DashboardGrid';
import { CustomizationPanel } from '../components/CustomizationPanel';
import { api } from '../services/api';

interface ItemSettings { [key: string]: boolean; }
interface AccountConfig {
  visibility_settings: ItemSettings;
  data_separation_settings: ItemSettings;
}

interface DashboardProps {
  activeAccount: string;
}

const ALL_ITEMS = [
  'series','animes','youtube','light_novels','manga','jogos',
  'financas','saude_fitness','links','trabalho','estudos','filmes',
];

export function Dashboard({ activeAccount }: DashboardProps) {
  const [config, setConfig] = useState<AccountConfig | null>(null);
  const [loading, setLoading] = useState(true);
  const [panelOpen, setPanelOpen] = useState(false);

  const fetchConfig = useCallback(async () => {
    setLoading(true);
    try {
      const { data } = await api.get('/api/accounts/config');
      const accountData = data[activeAccount];
      if (accountData) setConfig(accountData);
    } catch {
      // Fallback: show all items if backend unreachable
      const defaults = Object.fromEntries(ALL_ITEMS.map((id) => [id, true]));
      setConfig({ visibility_settings: defaults, data_separation_settings: defaults });
    } finally {
      setLoading(false);
    }
  }, [activeAccount]);

  useEffect(() => { fetchConfig(); }, [fetchConfig]);

  // Compute which item IDs are visible for the active account
  const visibleItems = config
    ? ALL_ITEMS.filter((id) => config.visibility_settings[id] !== false)
    : ALL_ITEMS;

  return (
    <div className="min-h-[calc(100vh-57px)]">
      {/* Page header */}
      <div className="flex items-center justify-between px-6 pt-8 pb-2">
        <div>
          <h1 className="text-2xl font-bold text-slate-100 tracking-tight">Dashboard</h1>
          <p className="text-slate-500 text-sm mt-1">Selecione um módulo para começar</p>
        </div>

        <button
          id="open-customization-panel"
          onClick={() => setPanelOpen(true)}
          className="flex items-center gap-2 px-4 py-2 rounded-xl text-sm text-slate-400 border border-slate-700/50 hover:border-blue-500/40 hover:text-slate-200 transition-all"
        >
          <SlidersHorizontal className="w-4 h-4" />
          Personalizar
        </button>
      </div>

      {/* Grid */}
      {loading ? (
        <div className="flex items-center justify-center h-64">
          <div className="w-6 h-6 rounded-full border-2 border-blue-500 border-t-transparent animate-spin" />
        </div>
      ) : (
        <DashboardGrid activeAccount={activeAccount} visibleItems={visibleItems} />
      )}

      {/* Customization panel */}
      {panelOpen && (
        <CustomizationPanel
          activeAccount={activeAccount}
          config={config}
          onSaved={(updated) => { setConfig(updated); }}
          onClose={() => setPanelOpen(false)}
        />
      )}
    </div>
  );
}
