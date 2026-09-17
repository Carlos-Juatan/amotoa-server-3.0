import React, { useRef } from 'react';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import { MediaCard, MediaCardData } from './MediaCard';

interface MediaCarouselProps {
  title: string;
  items: MediaCardData[];
  onCardClick?: (mediaId: number) => void;
}

export const MediaCarousel: React.FC<MediaCarouselProps> = ({ title, items, onCardClick }) => {
  const scrollRef = useRef<HTMLDivElement>(null);

  const scroll = (direction: 'left' | 'right') => {
    if (scrollRef.current) {
      const scrollAmount = scrollRef.current.clientWidth * 0.8;
      scrollRef.current.scrollBy({
        left: direction === 'left' ? -scrollAmount : scrollAmount,
        behavior: 'smooth'
      });
    }
  };

  if (!items || items.length === 0) {
    return null; // Don't render empty carousels
  }

  return (
    <div className="py-6 group">
      <h2 className="text-xl font-bold text-white mb-4 px-4 md:px-8 border-l-4 border-indigo-500 pl-3 ml-1 md:ml-5">
        {title}
        <span className="text-sm text-gray-500 font-normal ml-3">({items.length})</span>
      </h2>
      
      <div className="relative">
        {/* Navigation Arrows */}
        <button 
          onClick={() => scroll('left')}
          className="absolute left-0 top-0 bottom-0 z-40 w-12 flex items-center justify-center bg-gradient-to-r from-black/80 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300 disabled:opacity-0"
          aria-label="Scroll left"
        >
          <ChevronLeft className="w-8 h-8 text-white drop-shadow-md hover:scale-125 transition-transform" />
        </button>
        
        {/* Scroll Container */}
        <div 
          ref={scrollRef}
          className="flex gap-4 overflow-x-auto overflow-y-hidden px-4 md:px-8 pb-8 pt-4 snap-x snap-mandatory scrollbar-hide"
          style={{ scrollbarWidth: 'none', msOverflowStyle: 'none' }}
        >
          {items.map((item) => (
            <div key={item.mal_id} className="snap-start shrink-0">
              <MediaCard media={item} onClick={onCardClick} />
            </div>
          ))}
        </div>

        <button 
          onClick={() => scroll('right')}
          className="absolute right-0 top-0 bottom-0 z-40 w-12 flex items-center justify-center bg-gradient-to-l from-black/80 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300 disabled:opacity-0"
          aria-label="Scroll right"
        >
          <ChevronRight className="w-8 h-8 text-white drop-shadow-md hover:scale-125 transition-transform" />
        </button>
      </div>
    </div>
  );
};
