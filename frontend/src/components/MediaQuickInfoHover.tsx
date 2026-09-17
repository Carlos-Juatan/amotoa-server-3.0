import React from 'react';
import clsx from 'clsx';

interface MediaQuickInfoHoverProps {
  synopsis?: string;
  scorePublic?: number;
  year?: number;
  genres?: string[];
  totalUnits?: number;
}

export const MediaQuickInfoHover: React.FC<MediaQuickInfoHoverProps> = ({
  synopsis,
  scorePublic,
  year,
  genres = [],
  totalUnits
}) => {
  return (
    <div className={clsx(
      "absolute inset-0 z-20 flex flex-col justify-end p-4",
      "bg-gradient-to-t from-gray-950 via-gray-900/90 to-transparent",
      "opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none"
    )}>
      <div className="flex items-center justify-between mb-2 text-xs font-semibold text-gray-300">
        {year && <span>{year}</span>}
        {scorePublic && (
          <span className="flex items-center text-yellow-400">
            ★ {scorePublic.toFixed(2)}
          </span>
        )}
      </div>
      
      {genres.length > 0 && (
        <div className="flex flex-wrap gap-1 mb-2">
          {genres.slice(0, 3).map((genre) => (
            <span key={genre} className="px-1.5 py-0.5 text-[10px] bg-gray-800/80 rounded-sm text-gray-300 backdrop-blur-sm">
              {genre}
            </span>
          ))}
        </div>
      )}
      
      {synopsis && (
        <p className="text-xs text-gray-400 line-clamp-3 mb-2">
          {synopsis}
        </p>
      )}
      
      {totalUnits && (
        <div className="text-xs text-gray-500 font-medium mt-auto">
          {totalUnits} Episódios
        </div>
      )}
    </div>
  );
};
