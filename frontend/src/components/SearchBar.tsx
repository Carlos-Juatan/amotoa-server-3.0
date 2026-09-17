import React, { useState } from 'react';
import { Search, ExternalLink, Loader2 } from 'lucide-react';
import { api } from '../services/api';
import type { MediaCardData } from './MediaCard';
import { MediaType } from '../services/mediaConfig';

interface SearchBarProps {
  mediaType: MediaType;
  onSearchLocal: (query: string) => void;
  onImportSuccess?: () => void;
}

export const SearchBar: React.FC<SearchBarProps> = ({ mediaType, onSearchLocal, onImportSuccess }) => {
  const [query, setQuery] = useState('');
  const [isSearchingExternal, setIsSearchingExternal] = useState(false);
  const [externalResults, setExternalResults] = useState<MediaCardData[]>([]);
  const [importingId, setImportingId] = useState<number | null>(null);

  const handleLocalSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSearchLocal(query);
    setExternalResults([]); // clear external results when doing a local search
  };

  const handleExternalSearch = async () => {
    if (query.length < 3) return;
    setIsSearchingExternal(true);
    try {
      const res = await api.get('/api/media/external/search', {
        params: { media_type: mediaType, q: query }
      });
      setExternalResults(res.data);
    } catch (error) {
      console.error("External search failed", error);
    } finally {
      setIsSearchingExternal(false);
    }
  };

  const handleImport = async (malId: number) => {
    setImportingId(malId);
    try {
      await api.post('/api/media/external/import', {
        mal_id: malId,
        media_type: mediaType
      });
      if (onImportSuccess) {
        onImportSuccess();
      }
      setExternalResults(prev => prev.filter(r => r.mal_id !== malId));
    } catch (error) {
      console.error("Import failed", error);
    } finally {
      setImportingId(null);
    }
  };

  return (
    <div className="w-full flex flex-col gap-4">
      <form onSubmit={handleLocalSubmit} className="flex gap-2 w-full">
        <div className="relative flex-grow">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder={`Pesquisar...`}
            className="w-full pl-10 pr-4 py-2 bg-gray-800 border border-gray-700 rounded-lg focus:ring-2 focus:ring-indigo-500 text-white placeholder-gray-400"
          />
          <Search className="absolute left-3 top-2.5 w-5 h-5 text-gray-400" />
        </div>
        <button
          type="submit"
          className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg transition-colors"
        >
          Buscar
        </button>
        <button
          type="button"
          onClick={handleExternalSearch}
          disabled={query.length < 3 || isSearchingExternal}
          className="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg transition-colors flex items-center gap-2 disabled:opacity-50"
          title="Buscar no banco de dados Jikan (Online)"
        >
          {isSearchingExternal ? <Loader2 className="w-4 h-4 animate-spin" /> : <ExternalLink className="w-4 h-4" />}
          <span className="hidden sm:inline">Jikan</span>
        </button>
      </form>

      {externalResults.length > 0 && (
        <div className="bg-gray-800 p-4 rounded-lg border border-gray-700">
          <h3 className="text-lg font-semibold mb-3 text-white">Resultados Externos (Jikan)</h3>
          <div className="flex flex-col gap-2 max-h-64 overflow-y-auto pr-2 custom-scrollbar">
            {externalResults.map(item => (
              <div key={item.mal_id} className="flex justify-between items-center p-2 hover:bg-gray-700 rounded transition-colors">
                <div className="flex items-center gap-3">
                  <img src={item.cover_image_url} alt={item.title_default} className="w-10 h-14 object-cover rounded" />
                  <div>
                    <div className="font-medium text-white line-clamp-1" title={item.title_japanese || item.title_default}>
                      {item.title_japanese || item.title_default}
                    </div>
                    <div className="text-xs text-gray-400">
                      {item.year || 'N/A'} • {item.published_status}
                    </div>
                  </div>
                </div>
                <button
                  onClick={() => handleImport(item.mal_id)}
                  disabled={importingId === item.mal_id}
                  className="px-3 py-1 bg-green-600 hover:bg-green-700 text-white text-sm rounded transition-colors disabled:opacity-50 flex items-center gap-1 min-w-[80px] justify-center"
                >
                  {importingId === item.mal_id ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Importar'}
                </button>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
