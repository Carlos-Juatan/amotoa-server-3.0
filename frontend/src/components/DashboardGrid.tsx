import { useNavigate } from 'react-router-dom';
import {
  Tv2,
  Sword,
  Youtube,
  BookOpen,
  BookMarked,
  Gamepad2,
  Landmark,
  HeartPulse,
  Link2,
  Briefcase,
  GraduationCap,
  Clapperboard,
} from 'lucide-react';

interface DashboardItem {
  id: string;
  label: string;
  icon: React.ReactNode;
  isReady: boolean;
  gradient: string;
}

const DASHBOARD_ITEMS: DashboardItem[] = [
  {
    id: 'series',
    label: 'Series',
    icon: <Tv2 className="w-8 h-8" />,
    isReady: false,
    gradient: 'from-violet-500/20 to-purple-600/10',
  },
  {
    id: 'animes',
    label: 'Animes',
    icon: <Sword className="w-8 h-8" />,
    isReady: false,
    gradient: 'from-pink-500/20 to-rose-600/10',
  },
  {
    id: 'youtube',
    label: 'YouTube',
    icon: <Youtube className="w-8 h-8" />,
    isReady: false,
    gradient: 'from-red-500/20 to-orange-600/10',
  },
  {
    id: 'light_novels',
    label: 'Light Novels',
    icon: <BookOpen className="w-8 h-8" />,
    isReady: false,
    gradient: 'from-amber-500/20 to-yellow-600/10',
  },
  {
    id: 'manga',
    label: 'Manga',
    icon: <BookMarked className="w-8 h-8" />,
    isReady: false,
    gradient: 'from-cyan-500/20 to-sky-600/10',
  },
  {
    id: 'jogos',
    label: 'Jogos',
    icon: <Gamepad2 className="w-8 h-8" />,
    isReady: false,
    gradient: 'from-green-500/20 to-emerald-600/10',
  },
  {
    id: 'financas',
    label: 'Finanças',
    icon: <Landmark className="w-8 h-8" />,
    isReady: false,
    gradient: 'from-teal-500/20 to-green-600/10',
  },
  {
    id: 'saude_fitness',
    label: 'Saúde & Fitness',
    icon: <HeartPulse className="w-8 h-8" />,
    isReady: false,
    gradient: 'from-rose-500/20 to-pink-600/10',
  },
  {
    id: 'links',
    label: 'Links',
    icon: <Link2 className="w-8 h-8" />,
    isReady: false,
    gradient: 'from-blue-500/20 to-indigo-600/10',
  },
  {
    id: 'trabalho',
    label: 'Trabalho',
    icon: <Briefcase className="w-8 h-8" />,
    isReady: false,
    gradient: 'from-slate-400/20 to-slate-500/10',
  },
  {
    id: 'estudos',
    label: 'Estudos',
    icon: <GraduationCap className="w-8 h-8" />,
    isReady: false,
    gradient: 'from-indigo-500/20 to-blue-600/10',
  },
  {
    id: 'filmes',
    label: 'Filmes',
    icon: <Clapperboard className="w-8 h-8" />,
    isReady: false,
    gradient: 'from-orange-500/20 to-amber-600/10',
  },
];

interface DashboardGridProps {
  activeAccount: string;
  visibleItems?: string[];
}

export function DashboardGrid({ visibleItems }: DashboardGridProps) {
  const navigate = useNavigate();

  const items = visibleItems
    ? DASHBOARD_ITEMS.filter((item) => visibleItems.includes(item.id))
    : DASHBOARD_ITEMS;

  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4 p-4">
      {items.map((item) => (
        <button
          key={item.id}
          id={`dashboard-card-${item.id}`}
          onClick={() => navigate(item.isReady ? `/${item.id}` : `/wip/${item.id}`)}
          className={`
            glass-card group relative flex flex-col items-center justify-center gap-4
            rounded-2xl p-7 cursor-pointer text-center overflow-hidden
            bg-gradient-to-br ${item.gradient}
          `}
        >
          {/* Icon glow */}
          <div className="relative">
            <div className="absolute inset-0 blur-xl opacity-40 group-hover:opacity-70 transition-opacity bg-current" />
            <div className="relative text-slate-300 group-hover:text-white transition-colors">
              {item.icon}
            </div>
          </div>

          {/* Label */}
          <span className="text-sm font-semibold text-slate-300 group-hover:text-white transition-colors tracking-wide">
            {item.label}
          </span>

          {/* WIP badge */}
          {!item.isReady && (
            <span className="absolute top-3 right-3 text-[10px] font-bold uppercase tracking-widest text-slate-500 bg-slate-800/60 px-2 py-0.5 rounded-full border border-slate-700/40">
              WIP
            </span>
          )}
        </button>
      ))}
    </div>
  );
}
