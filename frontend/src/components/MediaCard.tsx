import React, { useState } from 'react';
import clsx from 'clsx';
import { PlaceholderImage } from './common/PlaceholderImage';
import { MediaQuickInfoHover } from './MediaQuickInfoHover';

export interface MediaCardData {
  mal_id: number;
  type: string;
  title_japanese: string;
  title_english?: string;
  title_default: string;
  cover_image_url: string;
  synopsis?: string;
  score_public?: number;
  year?: number;
  genres?: string[];
  total_units?: number;
  user_progress?: {
    current_unit: number;
    status: string;
  };
}

interface MediaCardProps {
  media: MediaCardData;
  onClick?: (mediaId: number) => void;
}

export const MediaCard: React.FC<MediaCardProps> = ({ media, onClick }) => {
  const [imageError, setImageError] = useState(false);

  return (
    <div 
      className={clsx(
        "group relative flex-none w-40 md:w-48 lg:w-56 overflow-hidden rounded-lg bg-gray-900 cursor-pointer",
        "transition-transform duration-300 hover:scale-105 hover:z-10 shadow-lg hover:shadow-xl hover:shadow-indigo-500/20"
      )}
      onClick={() => onClick && onClick(media.mal_id)}
    >
      <div className="relative aspect-[2/3] w-full overflow-hidden">
        {!imageError && media.cover_image_url ? (
          <img 
            src={media.cover_image_url} 
            alt={media.title_japanese || media.title_default}
            className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-110"
            onError={() => setImageError(true)}
            loading="lazy"
          />
        ) : (
          <PlaceholderImage text="No Cover" />
        )}

        <MediaQuickInfoHover 
          synopsis={media.synopsis}
          scorePublic={media.score_public}
          year={media.year}
          genres={media.genres}
          totalUnits={media.total_units}
        />
        
        {/* Progress Badge overlay */}
        {media.user_progress && media.user_progress.current_unit > 0 && (
          <div className="absolute top-2 right-2 z-30 bg-indigo-600/90 text-white text-[10px] font-bold px-2 py-1 rounded shadow-md backdrop-blur-sm">
            {media.user_progress.current_unit} 
            {media.total_units ? ` / ${media.total_units}` : ''}
          </div>
        )}
      </div>

      <div className="p-3 bg-gray-900 z-30 relative">
        <h3 className="text-sm font-bold text-gray-100 truncate" title={media.title_japanese || media.title_default}>
          {media.title_japanese || media.title_default}
        </h3>
        {media.title_english && (
          <p className="text-xs text-gray-500 truncate mt-0.5" title={media.title_english}>
            {media.title_english}
          </p>
        )}
      </div>
    </div>
  );
};
