import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { LayoutGrid } from 'lucide-react';
import { Dashboard } from './pages/Dashboard';
import { WIPPage } from './pages/WIPPage';
import { AccountSwitcher } from './components/AccountSwitcher';
import { useActiveAccount } from './hooks/useActiveAccount';
import { MediaShowcasePage } from './pages/MediaShowcasePage';
import { getMediaConfig } from './services/mediaConfig';
import './App.css';

function AppShell() {
  const { activeAccount, switchAccount } = useActiveAccount();

  return (
    <div className="min-h-screen flex flex-col">
      {/* ── App Header ── */}
      <header className="sticky top-0 z-40 flex items-center justify-between px-6 py-3 glass-panel border-b border-slate-800/60">
        {/* Brand */}
        <div className="flex items-center gap-2.5 text-slate-100">
          <LayoutGrid className="w-5 h-5 text-blue-400" />
          <span className="text-sm font-bold tracking-wide">Amontoa Hub</span>
        </div>

        {/* Account switcher */}
        <AccountSwitcher activeAccount={activeAccount} onSwitch={switchAccount} />
      </header>

      {/* ── Page Content ── */}
      <main className="flex-1">
        <Routes>
          <Route path="/"           element={<Dashboard activeAccount={activeAccount} />} />
          <Route path="/animes"     element={<MediaShowcasePage config={getMediaConfig('anime')} />} />
          <Route path="/manga"      element={<MediaShowcasePage config={getMediaConfig('manga')} />} />
          <Route path="/light_novels" element={<MediaShowcasePage config={getMediaConfig('light_novel')} />} />
          <Route path="/wip/:module" element={<WIPPage />} />
          <Route path="*"           element={<Navigate to="/" replace />} />
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
