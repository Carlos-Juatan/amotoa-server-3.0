import { ChevronDown, User } from 'lucide-react';
import { useState, useRef, useEffect } from 'react';

const ACCOUNTS = [
  { id: 'car-j-works', label: 'car-j works', emoji: '💼' },
  { id: 'car-j-home',  label: 'car-j home',  emoji: '🏠' },
] as const;

type AccountId = typeof ACCOUNTS[number]['id'];

interface AccountSwitcherProps {
  activeAccount: AccountId;
  onSwitch: (id: AccountId) => void;
}

export function AccountSwitcher({ activeAccount, onSwitch }: AccountSwitcherProps) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  const current = ACCOUNTS.find((a) => a.id === activeAccount) ?? ACCOUNTS[1];

  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  return (
    <div ref={ref} className="relative">
      <button
        id="account-switcher-trigger"
        onClick={() => setOpen((v) => !v)}
        className="flex items-center gap-2.5 px-4 py-2 rounded-xl bg-slate-800/60 border border-slate-700/50 hover:border-blue-500/40 hover:bg-slate-800 transition-all text-sm font-medium text-slate-200 group"
        aria-haspopup="listbox"
        aria-expanded={open}
      >
        <span className="text-base leading-none">{current.emoji}</span>
        <span>{current.label}</span>
        <ChevronDown
          className={`w-4 h-4 text-slate-400 transition-transform duration-200 ${open ? 'rotate-180' : ''}`}
        />
      </button>

      {open && (
        <div
          role="listbox"
          className="absolute right-0 mt-2 w-52 rounded-xl glass-panel overflow-hidden z-50 animate-in fade-in slide-in-from-top-2 duration-150"
        >
          <div className="px-3 py-2 border-b border-slate-800/80">
            <p className="text-[10px] font-semibold uppercase tracking-widest text-slate-500 flex items-center gap-1.5">
              <User className="w-3 h-3" /> Conta ativa
            </p>
          </div>

          {ACCOUNTS.map((account) => (
            <button
              key={account.id}
              id={`account-option-${account.id}`}
              role="option"
              aria-selected={account.id === activeAccount}
              onClick={() => { onSwitch(account.id); setOpen(false); }}
              className={`
                w-full flex items-center gap-3 px-4 py-3 text-sm transition-colors text-left
                ${account.id === activeAccount
                  ? 'bg-blue-500/10 text-blue-300'
                  : 'text-slate-300 hover:bg-slate-800/60 hover:text-slate-100'
                }
              `}
            >
              <span className="text-base">{account.emoji}</span>
              <span className="font-medium">{account.label}</span>
              {account.id === activeAccount && (
                <span className="ml-auto w-1.5 h-1.5 rounded-full bg-blue-400" />
              )}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
