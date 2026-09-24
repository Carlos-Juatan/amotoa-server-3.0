import { useState } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { LayoutGrid } from 'lucide-react';
import { Dashboard } from './pages/Dashboard';
import { WIPPage } from './pages/WIPPage';
import { AccountSwitcher } from './components/AccountSwitcher';
import { useActiveAccount } from './hooks/useActiveAccount';
import { MediaShowcasePage } from './pages/MediaShowcasePage';
import { MediaDetailPage } from './pages/MediaDetailPage';
import { DailyProgressPage } from './pages/DailyProgressPage';
import { getMediaConfig } from './services/mediaConfig';
import { BatchImportModal } from './components/BatchImportModal';
import { NavbarBatchIndicator } from './components/Navbar';
import './App.css';

function AppShell() {
  const { activeAccount, switchAccount } = useActiveAccount();
  const [batchModalOpen, setBatchModalOpen] = useState(false);

  return (
    <div className="min-h-screen flex flex-col">
      {/* ── App Header ── */}
      <header className="sticky top-0 z-40 flex items-center justify-between px-6 py-3 glass-panel border-b border-slate-800/60">
        {/* Brand */}
        <div className="flex items-center gap-2.5 text-slate-100">
          <LayoutGrid className="w-5 h-5 text-blue-400" />
          <span className="text-sm font-bold tracking-wide">Amontoa Hub</span>
        </div>

        {/* Right-side controls */}
        <div className="flex items-center gap-3">
          {/* Batch import indicator */}
          <NavbarBatchIndicator onOpen={() => setBatchModalOpen(true)} />

          {/* Account switcher */}
          <AccountSwitcher activeAccount={activeAccount} onSwitch={switchAccount} />
        </div>
      </header>

      {/* ── Batch Import Modal ── */}
      <BatchImportModal
        isOpen={batchModalOpen}
        onClose={() => setBatchModalOpen(false)}
      />

      {/* ── Page Content ── */}
      <main className="flex-1">
        <Routes>
          <Route path="/"             element={<Dashboard activeAccount={activeAccount} />} />
          <Route path="/animes"       element={<MediaShowcasePage config={getMediaConfig('anime')} />} />
          <Route path="/manga"        element={<MediaShowcasePage config={getMediaConfig('manga')} />} />
          <Route path="/light_novels" element={<MediaShowcasePage config={getMediaConfig('light_novel')} />} />

          <Route path="/:type/progress" element={<DailyProgressPage />} />
          
          {/* US5: Unified Detail Page — /:type/:id MUST precede the catch-all */}
          <Route path="/:type/:id"    element={<MediaDetailPage />} />

          <Route path="/wip/:module"  element={<WIPPage />} />
          <Route path="*"             element={<Navigate to="/" replace />} />
        </Routes>
      </main>
    </div>
  );
}

function App() {
  return (
    <BrowserRouter>
      <AppShell />
    </BrowserRouter>
  );
}

export default App;
