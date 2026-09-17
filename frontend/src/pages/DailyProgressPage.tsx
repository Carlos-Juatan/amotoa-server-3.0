import React, { useEffect, useState } from 'react';
import { useParams, Link, Navigate } from 'react-router-dom';
import { CalendarCheck, LayoutGrid, Loader2, PartyPopper } from 'lucide-react';
import { DailyProgressCard } from '../components/DailyProgressCard';
import { MediaCardData } from '../components/MediaCard';
import api from '../services/api';
import { getMediaConfig } from '../services/mediaConfig';

export const DailyProgressPage: React.FC = () => {
  const { type } = useParams<{ type: string }>();
  const [activeMedia, setActiveMedia] = useState<MediaCardData[]>([]);
  const [loading, setLoading] = useState(true);

  if (!type || !['anime', 'manga', 'light_novels'].includes(type)) {
    return <Navigate to="/" replace />;
  }
  
  // normalize type for API if needed, we expect 'anime', 'manga', 'light_novel'
  const apiType = type === 'light_novels' ? 'light_novel' : type;
  const config = getMediaConfig(apiType as 'anime' | 'manga' | 'light_novel');

  useEffect(() => {
    loadActiveMedia();
  }, [type]);

  const loadActiveMedia = async () => {
    try {
      setLoading(true);
      const { data } = await api.get<MediaCardData[]>(`/api/media/${apiType}/active-progress`);
      // Filter out completed ones just in case
      const filtered = data.filter(m => m.user_progress?.status !== 'completed' && m.user_progress?.status !== 'dropped');
      setActiveMedia(filtered);
    } catch (error) {
      console.error('Failed to load active media', error);
    } finally {
      setLoading(false);
    }
  };

  const handleIncrement = async (malId: number) => {
    try {
      const { data: updatedProgress } = await api.post(`/api/media/${apiType}/${malId}/increment`);
      setActiveMedia(prev => prev.map(m => {
        if (m.mal_id === malId) {
          return { ...m, user_progress: updatedProgress };
        }
        return m;
      }).filter(m => m.user_progress?.status !== 'completed'));
    } catch (error) {
      console.error('Failed to increment progress', error);
    }
  };

  const handleUnitSelect = async (malId: number, unit: number) => {
    try {
      const { data: updatedProgress } = await api.put(`/api/media/${apiType}/${malId}/progress`, {
        current_unit: unit
      });
      setActiveMedia(prev => prev.map(m => {
        if (m.mal_id === malId) {
          return { ...m, user_progress: updatedProgress };
        }
        return m;
      }).filter(m => m.user_progress?.status !== 'completed'));
    } catch (error) {
      console.error('Failed to select unit', error);
    }
  };

  return (
    <div className="min-h-screen bg-[#0B0F19] text-slate-200">
      <div className="max-w-4xl mx-auto px-6 py-10">
        
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-indigo-500/20 flex items-center justify-center text-indigo-400">
              <CalendarCheck className="w-5 h-5" />
            </div>
            <div>
              <h1 className="text-2xl font-bold tracking-tight text-white">Daily Progress</h1>
              <p className="text-sm text-slate-400">Track your active {config.labelPlural.toLowerCase()}</p>
            </div>
          </div>
          
          <Link 
            to={`/${type}`}
            className="flex items-center gap-2 px-4 py-2 rounded-lg glass-panel hover:bg-slate-800/60 transition-colors text-sm font-medium text-slate-300"
          >
            <LayoutGrid size={16} />
            Showcase
          </Link>
        </div>

        {/* Content */}
        {loading ? (
          <div className="flex justify-center items-center py-20">
            <Loader2 className="w-8 h-8 text-indigo-500 animate-spin" />
          </div>
        ) : activeMedia.length > 0 ? (
          <div className="grid grid-cols-1 gap-4">
            {activeMedia.map(media => (
              <DailyProgressCard 
                key={media.mal_id}
                media={media}
                onIncrement={handleIncrement}
                onUnitSelect={handleUnitSelect}
              />
            ))}
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center py-20 px-4 text-center glass-panel rounded-2xl border border-slate-800/50">
            <div className="w-16 h-16 rounded-full bg-slate-800/60 flex items-center justify-center text-slate-400 mb-4">
              <PartyPopper size={32} />
            </div>
            <h2 className="text-xl font-bold text-slate-200 mb-2">All caught up!</h2>
            <p className="text-slate-400 max-w-md mb-6">
              You don't have any active {config.labelPlural.toLowerCase()} to track right now. 
              Find something new in the showcase or add to your list.
            </p>
            <Link 
              to={`/${type}`}
              className="px-6 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg font-medium transition-colors shadow-lg shadow-indigo-500/20"
            >
              Go to Showcase
            </Link>
          </div>
        )}
        
      </div>
    </div>
  );
};
