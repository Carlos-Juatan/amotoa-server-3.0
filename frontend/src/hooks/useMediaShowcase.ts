import { useState, useEffect } from 'react';
import { api } from '../services/api';
import type { MediaConfig } from '../services/mediaConfig';
import type { MediaCardData } from '../components/MediaCard';

export interface ShowcaseData {
  watching: MediaCardData[];
  favorites: MediaCardData[];
  onHold: MediaCardData[];
  searchResults: MediaCardData[];
}

export interface ShowcaseFilters {
  search?: string;
  genre?: string;
  year?: number;
  letter?: string;
  sort_by?: string;
  order?: 'asc' | 'desc';
}

export const useMediaShowcase = (config: MediaConfig, filters?: ShowcaseFilters) => {
  const [data, setData] = useState<ShowcaseData>({
    watching: [],
    favorites: [],
    onHold: [],
    searchResults: []
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;

    const fetchShowcase = async () => {
      setLoading(true);
      setError(null);
      
      try {
        const hasFilters = filters && (filters.search || filters.genre || filters.year || filters.letter);
        
        if (hasFilters) {
          // If filtering/searching, we want all matching catalog items
          const res = await api.get(config.apiPath, { params: { ...filters } });
          if (isMounted) {
            setData({
              watching: [],
              favorites: [],
              onHold: [],
              searchResults: res.data
            });
          }
        } else {
          // Default showcase view
          const sortParams = {
            sort_by: filters?.sort_by || 'title',
            order: filters?.order || 'asc'
          };
          
          const [watchingRes, favoritesRes, onHoldRes] = await Promise.all([
            api.get(config.apiPath, { params: { status_group: 'watching', ...sortParams } }),
            api.get(config.apiPath, { params: { status_group: 'favorites', ...sortParams } }),
            api.get(config.apiPath, { params: { status_group: 'on_hold', ...sortParams } })
          ]);

          if (isMounted) {
            setData({
              watching: watchingRes.data,
              favorites: favoritesRes.data,
              onHold: onHoldRes.data,
              searchResults: []
            });
          }
        }
      } catch (err: any) {
        if (isMounted) {
          setError(err.message || 'Failed to fetch media showcase');
        }
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    };

    fetchShowcase();

    return () => {
      isMounted = false;
    };
  }, [config.apiPath, filters?.search, filters?.genre, filters?.year, filters?.letter, filters?.sort_by, filters?.order]);

  return { data, loading, error };
};
