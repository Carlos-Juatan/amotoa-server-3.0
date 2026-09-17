import React, { useState } from 'react';
import { useMediaShowcase, ShowcaseFilters } from '../hooks/useMediaShowcase';
import type { MediaConfig } from '../services/mediaConfig';
import { MediaCarousel } from '../components/MediaCarousel';
import { SearchBar } from '../components/SearchBar';
import { CatalogFilterBar } from '../components/CatalogFilterBar';
import { Loader2 } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

interface MediaShowcasePageProps {
  config: MediaConfig;
}

export const MediaShowcasePage: React.FC<MediaShowcasePageProps> = ({ config }) => {
  const [filters, setFilters] = useState<ShowcaseFilters>({
    sort_by: 'title',
    order: 'asc'
  });
  
  const { data, loading, error } = useMediaShowcase(config, filters);
  const navigate = useNavigate();

  const handleCardClick = (mediaId: number) => {
    navigate(`/${config.type}s/${mediaId}`);
  };

  const handleSearchLocal = (query: string) => {
    setFilters(prev => ({ ...prev, search: query === '' ? undefined : query }));
  };

  const handleImportSuccess = () => {
    // Optionally trigger a refresh by toggling a state or refetching
    // For now, removing the search filter will naturally refresh the showcase
    if (filters.search) {
      handleSearchLocal('');
    }
  };

  const isFiltering = filters.search || filters.genre || filters.year || filters.letter;

  return (
    <div className="flex flex-col gap-2 pb-12 w-full animate-in fade-in duration-500">
      <header className="mb-4 px-4 md:px-8 pt-8 flex flex-col gap-6">
        <div>
          <h1 className={`text-4xl font-bold ${config.primaryColor} drop-shadow-md`}>
            {config.title}
          </h1>
          <p className="text-gray-400 mt-2">
            Acompanhe seus {config.title.toLowerCase()} favoritos e descubra novos títulos.
          </p>
        </div>
        
        <div className="flex flex-col gap-3">
          <SearchBar 
            mediaType={config.type} 
            onSearchLocal={handleSearchLocal}
            onImportSuccess={handleImportSuccess}
          />
          <CatalogFilterBar 
            filters={filters}
            onChange={setFilters}
          />
        </div>
      </header>

      {error ? (
        <div className="flex flex-col items-center justify-center min-h-[40vh] text-red-500">
          <h2 className="text-2xl font-bold mb-2">Erro ao carregar os dados</h2>
          <p>{error}</p>
        </div>
      ) : loading ? (
        <div className="flex items-center justify-center min-h-[40vh]">
          <Loader2 className="w-12 h-12 text-indigo-500 animate-spin" />
        </div>
      ) : (
        <>
          {/* Search/Filtered Results */}
          {isFiltering && (
            <div className="px-4 md:px-8">
              {data.searchResults.length > 0 ? (
                <div className="mt-4">
                  <h2 className="text-2xl font-semibold text-white mb-4">Resultados da Busca</h2>
                  <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-4">
                    {/* Render grid of items (similar to carousel but wrapped) */}
                    {/* For simplicity we'll just use a carousel component acting as a list, or we need a grid component. 
                        Since MediaCarousel displays a horizontal list, we can just pass them to it if they fit. 
                        Wait, a grid is better for search results. I'll implement a quick grid here using MediaCard. */}
                  </div>
                </div>
              ) : (
                <div className="flex flex-col items-center justify-center py-20 text-gray-500">
                  <p className="text-lg">Nenhum resultado encontrado para os filtros selecionados.</p>
                </div>
              )}
            </div>
          )}

          {isFiltering && data.searchResults.length > 0 && (
             <MediaCarousel 
               title="Resultados" 
               items={data.searchResults} 
               onCardClick={handleCardClick} 
             />
          )}

          {/* Default Carousels by Status */}
          {!isFiltering && (
            <>
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
            </>
          )}
        </>
      )}
    </div>
  );
};
