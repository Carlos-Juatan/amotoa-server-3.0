import React, { useRef } from 'react';
import { ChevronLeft, ChevronRight, GitBranch } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { PlaceholderImage } from './common/PlaceholderImage';

export interface RelatedSeason {
  mal_id: number;
  type: string;
  title_japanese: string;
  title_english?: string;
  cover_image_url: string;
  year?: number;
  total_units?: number;
  published_status: string;
  user_progress?: {
    current_unit: number;
    status: string;
  } | null;
}

interface FranchiseRelationsProps {
  seasons: RelatedSeason[];
  currentMalId: number;
}

const statusColors: Record<string, string> = {
  watching: 'bg-blue-500/80',
  completed: 'bg-emerald-500/80',
  on_hold: 'bg-amber-500/80',
  dropped: 'bg-red-500/80',
  plan_to_watch: 'bg-slate-500/80',
};

export const FranchiseRelations: React.FC<FranchiseRelationsProps> = ({ seasons }) => {
  const scrollRef = useRef<HTMLDivElement>(null);
  const navigate = useNavigate();

  const scroll = (dir: 'left' | 'right') => {
    if (scrollRef.current) {
      scrollRef.current.scrollBy({ left: dir === 'left' ? -280 : 280, behavior: 'smooth' });
    }
  };

  if (!seasons || seasons.length === 0) return null;

  const handleSeasonClick = (season: RelatedSeason) => {
    // Derive the route path from type (anime -> /animes, manga -> /mangas, light_novel -> /light_novels)
    const typeToPath: Record<string, string> = {
      anime: 'animes',
      manga: 'mangas',
      light_novel: 'light_novels',
    };
    const path = typeToPath[season.type] ?? `${season.type}s`;
    navigate(`/${path}/${season.mal_id}`);
  };

  return (
    <section className="mt-8">
      <div className="flex items-center gap-2 mb-4">
        <GitBranch className="w-4 h-4 text-indigo-400" />
        <h2 className="text-lg font-bold text-slate-100">Temporadas da Franquia</h2>
        <span className="text-xs text-slate-500 font-normal ml-1">({seasons.length})</span>
      </div>

      <div className="relative group">
        {/* Left arrow */}
        <button
          onClick={() => scroll('left')}
          className="absolute left-0 top-0 bottom-0 z-10 w-10 flex items-center justify-center bg-gradient-to-r from-slate-950/80 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300"
          aria-label="Rolar para esquerda"
        >
          <ChevronLeft className="w-6 h-6 text-white drop-shadow" />
        </button>

        {/* Scroll container */}
        <div
          ref={scrollRef}
          className="flex gap-3 overflow-x-auto pb-3 pt-1"
          style={{ scrollbarWidth: 'none', msOverflowStyle: 'none' }}
        >
          {seasons.map((season) => {
            const statusBadge = season.user_progress
              ? statusColors[season.user_progress.status] ?? 'bg-slate-500/80'
              : null;

            return (
              <button
                key={season.mal_id}
                onClick={() => handleSeasonClick(season)}
                className="flex-none w-36 text-left group/card glass-card rounded-lg overflow-hidden transition-all duration-300 hover:border-indigo-500/40 hover:shadow-indigo-900/20 hover:shadow-lg"
                title={season.title_japanese}
              >
                {/* Cover image */}
                <div className="relative aspect-[2/3] w-full overflow-hidden bg-slate-800">
                  {season.cover_image_url ? (
                    <img
                      src={season.cover_image_url}
                      alt={season.title_japanese}
                      className="w-full h-full object-cover transition-transform duration-500 group-hover/card:scale-110"
                      loading="lazy"
                    />
                  ) : (
                    <PlaceholderImage text="No Cover" />
                  )}

                  {/* Progress badge */}
                  {season.user_progress && (
                    <div className={`absolute top-1.5 right-1.5 text-[9px] font-bold text-white px-1.5 py-0.5 rounded shadow ${statusBadge}`}>
                      {season.user_progress.current_unit}
                      {season.total_units ? `/${season.total_units}` : ''}
                    </div>
                  )}
                </div>

                {/* Info */}
                <div className="p-2">
                  <p className="text-[11px] font-semibold text-slate-100 truncate leading-tight">
                    {season.title_japanese}
                  </p>
                  {season.title_english && (
                    <p className="text-[10px] text-slate-500 truncate mt-0.5">{season.title_english}</p>
                  )}
                  {season.year && (
                    <p className="text-[10px] text-slate-600 mt-1">{season.year}</p>
                  )}
                </div>
              </button>
            );
          })}
        </div>

        {/* Right arrow */}
        <button
          onClick={() => scroll('right')}
          className="absolute right-0 top-0 bottom-0 z-10 w-10 flex items-center justify-center bg-gradient-to-l from-slate-950/80 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300"
          aria-label="Rolar para direita"
        >
          <ChevronRight className="w-6 h-6 text-white drop-shadow" />
        </button>
      </div>
    </section>
  );
};
