/**
 * T033: FranchiseMoviesList — Anime-exclusive franchise movie management panel.
 *
 * Displays franchise movies with watched toggle, allows adding new movie entries.
 * Strictly hidden for manga and light_novel media types (enforced by parent).
 */
import React, { useState } from 'react';
import { Film, Plus, Check, X, Loader2, ChevronDown, ChevronUp } from 'lucide-react';
import { api } from '../services/api';
import { PlaceholderImage } from './common/PlaceholderImage';

export interface FranchiseMovie {
  movie_id: string;
  title: string;
  cover_image_url?: string | null;
  watched: boolean;
  release_year?: number | null;
}

interface FranchiseMoviesListProps {
  malId: number;
  mediaType: string; // Always 'anime' at this component level
  movies: FranchiseMovie[];
  onMoviesChange: (updated: FranchiseMovie[]) => void;
}

interface AddMovieFormState {
  title: string;
  cover_image_url: string;
  release_year: string;
}

const EMPTY_FORM: AddMovieFormState = {
  title: '',
  cover_image_url: '',
  release_year: '',
};

export const FranchiseMoviesList: React.FC<FranchiseMoviesListProps> = ({
  malId,
  mediaType,
  movies,
  onMoviesChange,
}) => {
  const [isExpanded, setIsExpanded] = useState(true);
  const [showAddForm, setShowAddForm] = useState(false);
  const [form, setForm] = useState<AddMovieFormState>(EMPTY_FORM);
  const [adding, setAdding] = useState(false);
  const [togglingId, setTogglingId] = useState<string | null>(null);
  const [addError, setAddError] = useState<string | null>(null);

  const watchedCount = movies.filter((m) => m.watched).length;

  const handleToggleWatched = async (movie: FranchiseMovie) => {
    setTogglingId(movie.movie_id);
    try {
      const resp = await api.patch(
        `/api/media/${mediaType}/${malId}/movies/${movie.movie_id}`,
        { watched: !movie.watched }
      );
      const updated: FranchiseMovie[] = resp.data.franchise_movies ?? [];
      onMoviesChange(updated);
    } catch (err: any) {
      console.error('Failed to toggle movie watched state:', err);
    } finally {
      setTogglingId(null);
    }
  };

  const handleAddMovie = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.title.trim()) return;

    setAdding(true);
    setAddError(null);

    try {
      const payload: Record<string, any> = { title: form.title.trim() };
      if (form.cover_image_url.trim()) payload.cover_image_url = form.cover_image_url.trim();
      if (form.release_year.trim()) payload.release_year = parseInt(form.release_year, 10);

      const resp = await api.post(`/api/media/${mediaType}/${malId}/movies`, payload);
      const updated: FranchiseMovie[] = resp.data.franchise_movies ?? [];
      onMoviesChange(updated);
      setForm(EMPTY_FORM);
      setShowAddForm(false);
    } catch (err: any) {
      setAddError(err.response?.data?.detail ?? 'Erro ao adicionar filme.');
    } finally {
      setAdding(false);
    }
  };

  return (
    <section className="glass-panel rounded-xl p-4">
      {/* Header */}
      <button
        onClick={() => setIsExpanded((v) => !v)}
        className="w-full flex items-center justify-between text-left group"
        aria-expanded={isExpanded}
      >
        <div className="flex items-center gap-2">
          <Film className="w-4 h-4 text-purple-400" />
          <h3 className="text-sm font-bold text-slate-200 uppercase tracking-widest">
            Filmes da Franquia
          </h3>
          {movies.length > 0 && (
            <span className="text-xs text-slate-500">
              {watchedCount}/{movies.length} assistidos
            </span>
          )}
        </div>
        {isExpanded ? (
          <ChevronUp className="w-4 h-4 text-slate-500 group-hover:text-slate-300 transition-colors" />
        ) : (
          <ChevronDown className="w-4 h-4 text-slate-500 group-hover:text-slate-300 transition-colors" />
        )}
      </button>

      {isExpanded && (
        <div className="mt-3 flex flex-col gap-2">
          {/* Movie list */}
          {movies.length === 0 && !showAddForm && (
            <p className="text-xs text-slate-600 italic py-2 text-center">
              Nenhum filme adicionado ainda.
            </p>
          )}

          {movies.map((movie) => {
            const isToggling = togglingId === movie.movie_id;
            return (
              <div
                key={movie.movie_id}
                className={`flex items-center gap-3 p-2.5 rounded-lg border transition-all duration-200 ${
                  movie.watched
                    ? 'border-emerald-700/30 bg-emerald-900/10'
                    : 'border-slate-700/30 bg-slate-800/30'
                }`}
              >
                {/* Cover thumbnail */}
                <div className="flex-none w-10 h-14 rounded overflow-hidden ring-1 ring-white/5">
                  {movie.cover_image_url ? (
                    <img
                      src={movie.cover_image_url}
                      alt={movie.title}
                      className="w-full h-full object-cover"
                      loading="lazy"
                    />
                  ) : (
                    <PlaceholderImage text="🎬" />
                  )}
                </div>

                {/* Title + year */}
                <div className="flex-1 min-w-0">
                  <p
                    className={`text-sm font-semibold leading-tight truncate ${
                      movie.watched ? 'text-slate-400 line-through' : 'text-slate-200'
                    }`}
                  >
                    {movie.title}
                  </p>
                  {movie.release_year && (
                    <p className="text-xs text-slate-600 mt-0.5">{movie.release_year}</p>
                  )}
                </div>

                {/* Watched toggle button */}
                <button
                  onClick={() => handleToggleWatched(movie)}
                  disabled={isToggling}
                  className={`flex-none flex items-center gap-1 text-xs px-2.5 py-1 rounded-full border transition-all duration-200 ${
                    movie.watched
                      ? 'bg-emerald-500/20 border-emerald-500/40 text-emerald-400 hover:bg-red-500/20 hover:border-red-500/40 hover:text-red-400'
                      : 'bg-slate-700/40 border-slate-600/30 text-slate-400 hover:bg-emerald-500/20 hover:border-emerald-500/40 hover:text-emerald-400'
                  }`}
                  aria-label={movie.watched ? 'Marcar como não assistido' : 'Marcar como assistido'}
                >
                  {isToggling ? (
                    <Loader2 className="w-3 h-3 animate-spin" />
                  ) : movie.watched ? (
                    <Check className="w-3 h-3" />
                  ) : (
                    <Check className="w-3 h-3" />
                  )}
                  {movie.watched ? 'Assistido' : 'Marcar'}
                </button>
              </div>
            );
          })}

          {/* Add Movie Form */}
          {showAddForm ? (
            <form
              onSubmit={handleAddMovie}
              className="mt-2 p-3 rounded-lg border border-slate-700/40 bg-slate-800/30 flex flex-col gap-2"
            >
              <div className="flex flex-col gap-1">
                <label className="text-xs text-slate-500">Título *</label>
                <input
                  type="text"
                  value={form.title}
                  onChange={(e) => setForm((f) => ({ ...f, title: e.target.value }))}
                  placeholder="Ex: Mugen Train"
                  required
                  className="bg-slate-900/60 border border-slate-700/50 rounded-lg px-3 py-1.5 text-sm text-slate-200 placeholder-slate-600 focus:outline-none focus:ring-1 focus:ring-indigo-500/60 transition-all"
                />
              </div>
              <div className="flex gap-2">
                <div className="flex flex-col gap-1 flex-1">
                  <label className="text-xs text-slate-500">Ano de lançamento</label>
                  <input
                    type="number"
                    value={form.release_year}
                    onChange={(e) => setForm((f) => ({ ...f, release_year: e.target.value }))}
                    placeholder="2020"
                    min={1900}
                    max={2100}
                    className="bg-slate-900/60 border border-slate-700/50 rounded-lg px-3 py-1.5 text-sm text-slate-200 placeholder-slate-600 focus:outline-none focus:ring-1 focus:ring-indigo-500/60 transition-all"
                  />
                </div>
              </div>
              <div className="flex flex-col gap-1">
                <label className="text-xs text-slate-500">URL da capa (opcional)</label>
                <input
                  type="url"
                  value={form.cover_image_url}
                  onChange={(e) => setForm((f) => ({ ...f, cover_image_url: e.target.value }))}
                  placeholder="https://..."
                  className="bg-slate-900/60 border border-slate-700/50 rounded-lg px-3 py-1.5 text-sm text-slate-200 placeholder-slate-600 focus:outline-none focus:ring-1 focus:ring-indigo-500/60 transition-all"
                />
              </div>

              {addError && (
                <p className="text-xs text-red-400">{addError}</p>
              )}

              <div className="flex gap-2 mt-1">
                <button
                  type="submit"
                  disabled={adding || !form.title.trim()}
                  className="flex-1 flex items-center justify-center gap-1.5 text-xs py-1.5 rounded-lg bg-indigo-600/80 hover:bg-indigo-500/80 text-white border border-indigo-500/30 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
                >
                  {adding ? <Loader2 className="w-3 h-3 animate-spin" /> : <Plus className="w-3 h-3" />}
                  Adicionar
                </button>
                <button
                  type="button"
                  onClick={() => { setShowAddForm(false); setForm(EMPTY_FORM); setAddError(null); }}
                  className="flex items-center gap-1 text-xs px-3 py-1.5 rounded-lg border border-slate-700/40 text-slate-400 hover:text-slate-200 transition-all"
                >
                  <X className="w-3 h-3" />
                  Cancelar
                </button>
              </div>
            </form>
          ) : (
            <button
              onClick={() => setShowAddForm(true)}
              className="mt-1 flex items-center gap-1.5 text-xs text-slate-500 hover:text-indigo-400 border border-dashed border-slate-700/50 hover:border-indigo-500/40 rounded-lg py-2 px-3 transition-all duration-200"
            >
              <Plus className="w-3.5 h-3.5" />
              Adicionar filme
            </button>
          )}
        </div>
      )}
    </section>
  );
};
