import React from 'react';
import { useMediaShowcase } from '../hooks/useMediaShowcase';
import type { MediaConfig } from '../services/mediaConfig';
import { MediaCarousel } from '../components/MediaCarousel';
import { Loader2 } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

interface MediaShowcasePageProps {
  config: MediaConfig;
}

export const MediaShowcasePage: React.FC<MediaShowcasePageProps> = ({ config }) => {
  const { data, loading, error } = useMediaShowcase(config);
  const navigate = useNavigate();

  const handleCardClick = (mediaId: number) => {
    navigate(`/${config.type}s/${mediaId}`);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <Loader2 className="w-12 h-12 text-indigo-500 animate-spin" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] text-red-500">
        <h2 className="text-2xl font-bold mb-2">Erro ao carregar os dados</h2>
        <p>{error}</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-2 pb-12 w-full animate-in fade-in duration-500">
      <header className="mb-6 px-4 md:px-8 pt-8">
        <h1 className={`text-4xl font-bold ${config.primaryColor} drop-shadow-md`}>
          {config.title}
        </h1>
        <p className="text-gray-400 mt-2">
          Acompanhe seus {config.title.toLowerCase()} favoritos e descubra novos títulos.
        </p>
      </header>

      {/* Carousels by Status */}
      {data.watching.length > 0 && (
        <MediaCarousel 
          title="Em andamento" 
          items={data.watching} 
          onCardClick={handleCardClick} 
        />
      )}
      
      {data.favorites.length > 0 && (
        <MediaCarousel 
          title="Favoritos" 
          items={data.favorites} 
          onCardClick={handleCardClick} 
        />
      )}
      
      {data.onHold.length > 0 && (
        <MediaCarousel 
          title="Pausados" 
          items={data.onHold} 
          onCardClick={handleCardClick} 
        />
      )}

      {/* Empty State */}
      {data.watching.length === 0 && data.favorites.length === 0 && data.onHold.length === 0 && (
        <div className="flex flex-col items-center justify-center py-20 text-gray-500">
          <p className="text-lg">Você ainda não possui itens monitorados nesta categoria.</p>
        </div>
      )}
    </div>
  );
};
