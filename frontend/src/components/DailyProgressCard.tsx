import React, { useState } from 'react';
import { Plus, ExternalLink } from 'lucide-react';
import clsx from 'clsx';
import { MediaCardData } from './MediaCard';
import { PlaceholderImage } from './common/PlaceholderImage';
import { Link } from 'react-router-dom';

interface DailyProgressCardProps {
  media: MediaCardData;
  onIncrement: (malId: number) => void;
  onUnitSelect: (malId: number, unit: number) => void;
}

export const DailyProgressCard: React.FC<DailyProgressCardProps> = ({ media, onIncrement, onUnitSelect }) => {
  const [imageError, setImageError] = useState(false);
  const current = media.user_progress?.current_unit || 0;
  const total = media.total_units || 0;
  const isCompleted = total > 0 && current >= total;

  const maxDropdown = total > 0 ? total : Math.max(current + 20, 100);
  const options = Array.from({ length: maxDropdown + 1 }, (_, i) => i);

  const primaryLink = media.user_progress?.external_links?.[0]?.url;

  return (
    <div className="flex gap-4 p-4 rounded-xl glass-panel group transition-all hover:bg-slate-800/40 border border-slate-800/60 hover:border-indigo-500/30">
      <Link to={`/${media.type}/${media.mal_id}`} className="flex-none w-20 sm:w-24 aspect-[2/3] overflow-hidden rounded-md relative cursor-pointer">
        {!imageError && media.cover_image_url ? (
          <img 
            src={media.cover_image_url} 
            alt={media.title_japanese || media.title_default}
            className="w-full h-full object-cover transition-transform duration-300 group-hover:scale-105"
            onError={() => setImageError(true)}
          />
        ) : (
          <PlaceholderImage text="Cover" />
        )}
      </Link>
      
      <div className="flex flex-col flex-1 min-w-0 justify-between">
        <div>
          <Link to={`/${media.type}/${media.mal_id}`}>
            <h3 className="font-bold text-slate-100 text-lg truncate hover:text-indigo-400 transition-colors" title={media.title_japanese || media.title_default}>
              {media.title_japanese || media.title_default}
            </h3>
          </Link>
          {media.title_english && (
            <p className="text-sm text-slate-400 truncate" title={media.title_english}>{media.title_english}</p>
          )}
        </div>
        
        <div className="flex items-center gap-3 mt-4">
          <button 
            onClick={() => onIncrement(media.mal_id)}
            disabled={isCompleted}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-indigo-600/90 hover:bg-indigo-500 text-white font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Plus size={16} />
            <span>+1</span>
          </button>
          
          <select 
            value={current}
            onChange={(e) => onUnitSelect(media.mal_id, parseInt(e.target.value, 10))}
            className="bg-slate-900/60 border border-slate-700/50 rounded-lg px-3 py-1.5 text-sm text-slate-200 focus:outline-none focus:ring-1 focus:ring-indigo-500/60"
          >
            {options.map(opt => (
              <option key={opt} value={opt}>{opt}</option>
            ))}
          </select>
          
          <span className="text-slate-400 text-sm font-medium">
            / {total > 0 ? total : '?'} {media.type === 'anime' ? 'ep' : 'ch'}
          </span>
          
          {primaryLink && (
            <a 
              href={primaryLink}
              target="_blank"
              rel="noreferrer"
              className="ml-auto text-slate-400 hover:text-indigo-400 p-2 rounded-full hover:bg-slate-800 transition-colors"
              title="Open primary link"
            >
              <ExternalLink size={18} />
            </a>
          )}
        </div>
      </div>
    </div>
  );
};
