import React from 'react';
import { Image as ImageIcon } from 'lucide-react';
import clsx from 'clsx';

interface PlaceholderImageProps {
  className?: string;
  text?: string;
}

export const PlaceholderImage: React.FC<PlaceholderImageProps> = ({ 
  className,
  text = 'No Image Available'
}) => {
  return (
    <div 
      className={clsx(
        "flex flex-col items-center justify-center bg-gray-800 text-gray-500 rounded-md shadow-inner w-full h-full",
        className
      )}
    >
      <ImageIcon className="w-12 h-12 mb-2 opacity-50" />
      <span className="text-xs font-medium text-center px-2">{text}</span>
    </div>
  );
};
