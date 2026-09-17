import { useState, useEffect } from 'react';
import { api } from '../services/api';
import { MediaConfig } from '../services/mediaConfig';
import { MediaCardData } from '../components/MediaCard';

export interface ShowcaseData {
  watching: MediaCardData[];
  favorites: MediaCardData[];
  onHold: MediaCardData[];
}

export const useMediaShowcase = (config: MediaConfig) => {
  const [data, setData] = useState<ShowcaseData>({
    watching: [],
    favorites: [],
    onHold: []
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;

    const fetchShowcase = async () => {
      setLoading(true);
      setError(null);
      
      try {
        // Fetch parallel requests for each status group
        const [watchingRes, favoritesRes, onHoldRes] = await Promise.all([
          api.get(config.apiPath, { params: { status_group: 'watching' } }),
          api.get(config.apiPath, { params: { status_group: 'favorites' } }),
          api.get(config.apiPath, { params: { status_group: 'on_hold' } })
        ]);

        if (isMounted) {
          setData({
            watching: watchingRes.data,
            favorites: favoritesRes.data,
            onHold: onHoldRes.data
          });
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
  }, [config.apiPath]);

  return { data, loading, error };
};
