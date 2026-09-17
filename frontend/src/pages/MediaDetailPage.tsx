import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  ChevronLeft, ChevronRight, ArrowLeft, Star, BookOpen,
  Play, Calendar, Tag, ExternalLink as ExternalLinkIcon,
  Loader2, AlertCircle, Images, Heart, Edit3, Plus, X,
  Check, Link2, Minus
} from 'lucide-react';
import { api } from '../services/api';
import { ImageGalleryModal } from '../components/ImageGalleryModal';
import { FranchiseRelations, type RelatedSeason } from '../components/FranchiseRelations';
import { FranchiseMoviesList, type FranchiseMovie } from '../components/FranchiseMoviesList';
import { PlaceholderImage } from '../components/common/PlaceholderImage';

// Derive the API media_type from the URL segment (animes -> anime, etc.)
const pathToApiType: Record<string, string> = {
  animes: 'anime',
  mangas: 'manga',
  light_novels: 'light_novel',
};

interface ExternalLink {
  label: string;
  url: string;
}

interface UserProgress {
  current_unit: number;
  status: string;
  is_favorite: boolean;
  personal_score?: number;
  personal_tags: string[];
  external_links: ExternalLink[];
  franchise_movies?: FranchiseMovie[];
}

interface MediaDetail {
  mal_id: number;
  type: string;
  title_japanese: string;
  title_english?: string;
  title_default: string;
  synopsis?: string;
  cover_image_url: string;
  gallery_image_urls?: string[];
  published_status: string;
  total_units?: number;
  season?: string;
  year?: number;
  genres?: string[];
  score_public?: number;
  franchise_root_id?: number;
  related_seasons: RelatedSeason[];
  user_progress?: UserProgress | null;
}

const PROGRESS_STATUSES = [
  { value: 'watching',      label: 'Em andamento' },
  { value: 'completed',     label: 'Finalizado'   },
  { value: 'on_hold',       label: 'Pausado'       },
  { value: 'dropped',       label: 'Dropado'       },
  { value: 'plan_to_watch', label: 'Planejado'    },
];

const statusColor: Record<string, string> = {
  watching:      'text-blue-400 bg-blue-400/10 border-blue-400/30',
  completed:     'text-emerald-400 bg-emerald-400/10 border-emerald-400/30',
  on_hold:       'text-amber-400 bg-amber-400/10 border-amber-400/30',
  dropped:       'text-red-400 bg-red-400/10 border-red-400/30',
  plan_to_watch: 'text-slate-400 bg-slate-400/10 border-slate-400/30',
};

// Default empty progress when no record exists yet
const defaultProgress = (): UserProgress => ({
  current_unit: 0,
  status: 'plan_to_watch',
  is_favorite: false,
  personal_score: undefined,
  personal_tags: [],
  external_links: [],
  franchise_movies: [],
});

// ── Small reusable "saving" spinner indicator ─────────────────────────────
const SavingIndicator: React.FC<{ saving: boolean }> = ({ saving }) =>
  saving ? <Loader2 className="w-3.5 h-3.5 animate-spin text-indigo-400 inline ml-1" /> : null;

// ─────────────────────────────────────────────────────────────────────────
export const MediaDetailPage: React.FC = () => {
  const { type, id } = useParams<{ type: string; id: string }>();
  const navigate = useNavigate();

  const [media, setMedia] = useState<MediaDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Gallery state
  const [galleryOpen, setGalleryOpen] = useState(false);
  const [galleryIndex, setGalleryIndex] = useState(0);

  // Sibling navigation — list of sibling mal_ids for lateral arrows
  const [siblingIds, setSiblingIds] = useState<number[]>([]);

  // Local progress state (reflects confirmed server state)
  const [progress, setProgress] = useState<UserProgress>(defaultProgress());

  // Saving flags per section
  const [savingProgress, setSavingProgress] = useState(false);
  const [savingTags, setSavingTags] = useState(false);
  const [savingLinks, setSavingLinks] = useState(false);

  // Tag editing
  const [tagInput, setTagInput] = useState('');

  // Link editing
  const [linkLabelInput, setLinkLabelInput] = useState('');
  const [linkUrlInput, setLinkUrlInput] = useState('');
  const [showLinkForm, setShowLinkForm] = useState(false);

  const apiType = type ? (pathToApiType[type] ?? type) : '';

  // ── Data fetching ────────────────────────────────────────────────────────
  useEffect(() => {
    if (!apiType || !id) return;

    setLoading(true);
    setError(null);

    api
      .get(`/api/media/${apiType}/${id}`)
      .then((res) => {
        const data: MediaDetail = res.data;
        setMedia(data);

        // Sync local progress state from server
        setProgress(data.user_progress ?? defaultProgress());

        // Build sibling id list from related_seasons for lateral nav
        if (data.related_seasons && data.related_seasons.length > 0) {
          const allIds = [data.mal_id, ...data.related_seasons.map((s) => s.mal_id)].sort(
            (a, b) => a - b
          );
          setSiblingIds(allIds);
        } else {
          setSiblingIds([]);
        }
      })
      .catch((err) => {
        setError(err.response?.data?.detail ?? err.message ?? 'Erro ao carregar detalhes.');
      })
      .finally(() => setLoading(false));
  }, [apiType, id]);

  // ── Lateral navigation ───────────────────────────────────────────────────
  const currentPos = media ? siblingIds.indexOf(media.mal_id) : -1;
  const prevSiblingId = currentPos > 0 ? siblingIds[currentPos - 1] : null;
  const nextSiblingId = currentPos < siblingIds.length - 1 ? siblingIds[currentPos + 1] : null;

  const navigateToSibling = (siblingId: number) => {
    navigate(`/${type}/${siblingId}`);
  };

  const openGallery = (idx: number) => {
    setGalleryIndex(idx);
    setGalleryOpen(true);
  };

  // ── Progress update helpers ──────────────────────────────────────────────

  const patchProgress = useCallback(
    async (payload: Record<string, any>) => {
      if (!media) return;
      setSavingProgress(true);
      try {
        const resp = await api.put(`/api/media/${apiType}/${media.mal_id}/progress`, payload);
        setProgress((prev) => ({ ...prev, ...resp.data }));
      } catch (err) {
        console.error('Failed to save progress:', err);
      } finally {
        setSavingProgress(false);
      }
    },
    [media, apiType]
  );

  const handleUnitChange = useCallback(
    async (delta: number) => {
      if (!media) return;
      const next = Math.max(0, progress.current_unit + delta);
      if (media.total_units != null && next > media.total_units) return;
      await patchProgress({ current_unit: next, status: progress.status });
    },
    [media, progress, patchProgress]
  );

  const handleUnitInput = useCallback(
    async (value: number) => {
      if (!media) return;
      const clamped = Math.min(Math.max(0, value), media.total_units ?? Infinity);
      await patchProgress({ current_unit: clamped, status: progress.status });
    },
    [media, progress.status, patchProgress]
  );

  const handleStatusChange = useCallback(
    async (newStatus: string) => {
      await patchProgress({ current_unit: progress.current_unit, status: newStatus });
    },
    [progress.current_unit, patchProgress]
  );

  const handleFavoriteToggle = useCallback(async () => {
    await patchProgress({
      current_unit: progress.current_unit,
      status: progress.status,
      is_favorite: !progress.is_favorite,
    });
  }, [progress, patchProgress]);

  const handleScoreChange = useCallback(
    async (score: number | undefined) => {
      await patchProgress({
        current_unit: progress.current_unit,
        status: progress.status,
        personal_score: score ?? null,
      });
    },
    [progress, patchProgress]
  );

  // ── Tags ─────────────────────────────────────────────────────────────────

  const commitTags = useCallback(
    async (tags: string[]) => {
      if (!media) return;
      setSavingTags(true);
      try {
        const resp = await api.put(`/api/media/${apiType}/${media.mal_id}/tags`, { tags });
        setProgress((prev) => ({ ...prev, personal_tags: resp.data.personal_tags ?? tags }));
      } catch (err) {
        console.error('Failed to save tags:', err);
      } finally {
        setSavingTags(false);
      }
    },
    [media, apiType]
  );

  const addTag = useCallback(async () => {
    const tag = tagInput.trim();
    if (!tag || progress.personal_tags.includes(tag)) {
      setTagInput('');
      return;
    }
    const updated = [...progress.personal_tags, tag];
    setTagInput('');
    await commitTags(updated);
  }, [tagInput, progress.personal_tags, commitTags]);

  const removeTag = useCallback(
    async (tag: string) => {
      const updated = progress.personal_tags.filter((t) => t !== tag);
      await commitTags(updated);
    },
    [progress.personal_tags, commitTags]
  );

  // ── External Links ───────────────────────────────────────────────────────

  const commitLinks = useCallback(
    async (links: ExternalLink[]) => {
      if (!media) return;
      setSavingLinks(true);
      try {
        const resp = await api.put(`/api/media/${apiType}/${media.mal_id}/links`, links);
        setProgress((prev) => ({
          ...prev,
          external_links: resp.data.external_links ?? links,
        }));
      } catch (err) {
        console.error('Failed to save links:', err);
      } finally {
        setSavingLinks(false);
      }
    },
    [media, apiType]
  );

  const addLink = useCallback(async () => {
    const label = linkLabelInput.trim();
    const url = linkUrlInput.trim();
    if (!label || !url) return;
    const updated = [...progress.external_links, { label, url }];
    setLinkLabelInput('');
    setLinkUrlInput('');
    setShowLinkForm(false);
    await commitLinks(updated);
  }, [linkLabelInput, linkUrlInput, progress.external_links, commitLinks]);

  const removeLink = useCallback(
    async (url: string) => {
      const updated = progress.external_links.filter((l) => l.url !== url);
      await commitLinks(updated);
    },
    [progress.external_links, commitLinks]
  );

  // ── Loading / Error states ────────────────────────────────────────────────
  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <Loader2 className="w-12 h-12 text-indigo-500 animate-spin" />
      </div>
    );
  }

  if (error || !media) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] gap-4 text-red-400 px-8">
        <AlertCircle className="w-12 h-12" />
        <h2 className="text-xl font-bold">Não foi possível carregar os detalhes</h2>
        <p className="text-slate-400 text-sm">{error}</p>
        <button
          onClick={() => navigate(-1)}
          className="mt-2 flex items-center gap-2 px-4 py-2 glass-panel rounded-lg text-slate-300 hover:text-white transition-all"
        >
          <ArrowLeft className="w-4 h-4" />
          Voltar
        </button>
      </div>
    );
  }

  const galleries = media.gallery_image_urls ?? [];
  const unitLabel = media.type === 'anime' ? 'Ep.' : 'Cap.';
  const isAnime = media.type === 'anime';

  return (
    <>
      {/* ── Image Gallery Modal ─────────────────────────────────────────────── */}
      <ImageGalleryModal
        images={galleries}
        initialIndex={galleryIndex}
        isOpen={galleryOpen}
        onClose={() => setGalleryOpen(false)}
      />

      {/* ── Page Layout ──────────────────────────────────────────────────────── */}
      <div className="min-h-screen pb-20">

        {/* ── Hero Banner (blurred cover bg) ───────────────────────────────── */}
        <div className="relative overflow-hidden">
          {/* Blurred background */}
          <div
            className="absolute inset-0 scale-110 blur-2xl opacity-20"
            style={{
              backgroundImage: `url(${media.cover_image_url})`,
              backgroundSize: 'cover',
              backgroundPosition: 'center',
            }}
          />
          <div className="absolute inset-0 bg-gradient-to-b from-transparent via-[#080b11]/60 to-[#080b11]" />

          {/* Back button + Lateral nav */}
          <div className="relative z-10 flex items-center justify-between px-4 md:px-8 pt-6 pb-2">
            <button
              onClick={() => navigate(-1)}
              className="flex items-center gap-1.5 text-slate-400 hover:text-slate-100 transition-colors text-sm"
              aria-label="Voltar"
            >
              <ArrowLeft className="w-4 h-4" />
              Voltar
            </button>

            {/* Lateral navigation arrows */}
            {siblingIds.length > 1 && (
              <div className="flex items-center gap-2">
                <button
                  onClick={() => prevSiblingId && navigateToSibling(prevSiblingId)}
                  disabled={!prevSiblingId}
                  className="p-1.5 rounded-full glass-panel text-slate-300 hover:text-white transition-all duration-200 disabled:opacity-30 disabled:cursor-not-allowed"
                  aria-label="Temporada anterior"
                >
                  <ChevronLeft className="w-5 h-5" />
                </button>
                <span className="text-xs text-slate-500 font-mono">
                  {currentPos + 1}/{siblingIds.length}
                </span>
                <button
                  onClick={() => nextSiblingId && navigateToSibling(nextSiblingId)}
                  disabled={!nextSiblingId}
                  className="p-1.5 rounded-full glass-panel text-slate-300 hover:text-white transition-all duration-200 disabled:opacity-30 disabled:cursor-not-allowed"
                  aria-label="Próxima temporada"
                >
                  <ChevronRight className="w-5 h-5" />
                </button>
              </div>
            )}
          </div>

          {/* Main content row: Cover + Meta */}
          <div className="relative z-10 flex flex-col md:flex-row gap-6 px-4 md:px-8 pt-4 pb-8">
            {/* Cover image */}
            <div className="flex-none">
              <div className="relative w-40 md:w-52 aspect-[2/3] rounded-xl overflow-hidden shadow-2xl shadow-black/60 ring-1 ring-white/10">
                {media.cover_image_url ? (
                  <img
                    src={media.cover_image_url}
                    alt={media.title_japanese}
                    className="w-full h-full object-cover"
                  />
                ) : (
                  <PlaceholderImage text="No Cover" />
                )}
              </div>
            </div>

            {/* Metadata */}
            <div className="flex flex-col gap-3 flex-1 min-w-0">
              {/* Titles */}
              <div>
                <h1 className="text-2xl md:text-4xl font-black text-white leading-tight tracking-tight">
                  {media.title_japanese || media.title_default}
                </h1>
                {media.title_english && (
                  <p className="text-base md:text-lg text-slate-400 mt-1 font-medium">
                    {media.title_english}
                  </p>
                )}
                {media.title_default !== media.title_japanese &&
                  media.title_default !== media.title_english && (
                    <p className="text-sm text-slate-600 mt-0.5">{media.title_default}</p>
                  )}
              </div>

              {/* Quick stats row */}
              <div className="flex flex-wrap items-center gap-3 mt-1">
                {/* Status badge */}
                <span
                  className={`text-xs font-semibold px-2.5 py-1 rounded-full border ${
                    statusColor[progress.status] ?? 'text-slate-400 bg-slate-400/10 border-slate-400/30'
                  }`}
                >
                  {PROGRESS_STATUSES.find((s) => s.value === progress.status)?.label ?? progress.status}
                </span>

                {/* Public score */}
                {media.score_public != null && (
                  <div className="flex items-center gap-1 text-amber-400">
                    <Star className="w-4 h-4 fill-amber-400" />
                    <span className="text-sm font-bold">{media.score_public.toFixed(1)}</span>
                  </div>
                )}

                {/* Progress */}
                <div className="flex items-center gap-1 text-slate-300">
                  {isAnime ? <Play className="w-3.5 h-3.5" /> : <BookOpen className="w-3.5 h-3.5" />}
                  <span className="text-sm">
                    {unitLabel} {progress.current_unit}
                    {media.total_units ? ` / ${media.total_units}` : ''}
                  </span>
                </div>

                {/* Year/Season */}
                {media.year && (
                  <div className="flex items-center gap-1 text-slate-400 text-sm">
                    <Calendar className="w-3.5 h-3.5" />
                    {media.season
                      ? `${media.season.charAt(0).toUpperCase()}${media.season.slice(1)} `
                      : ''}
                    {media.year}
                  </div>
                )}

                {/* Published status */}
                <span className="text-xs text-slate-500 bg-slate-800/60 px-2 py-0.5 rounded">
                  {media.published_status}
                </span>
              </div>

              {/* Genres */}
              {media.genres && media.genres.length > 0 && (
                <div className="flex flex-wrap gap-1.5 mt-1">
                  {media.genres.map((g) => (
                    <span
                      key={g}
                      className="text-xs text-indigo-300 bg-indigo-900/30 border border-indigo-700/30 px-2 py-0.5 rounded-full"
                    >
                      {g}
                    </span>
                  ))}
                </div>
              )}

              {/* Personal tags (read-only view in hero) */}
              {progress.personal_tags.length > 0 && (
                <div className="flex flex-wrap items-center gap-1.5 mt-1">
                  <Tag className="w-3.5 h-3.5 text-slate-500" />
                  {progress.personal_tags.map((tag) => (
                    <span
                      key={tag}
                      className="text-xs text-slate-300 bg-slate-800/60 border border-slate-700/40 px-2 py-0.5 rounded-full"
                    >
                      {tag}
                    </span>
                  ))}
                </div>
              )}

              {/* External links (read-only view in hero) */}
              {progress.external_links.length > 0 && (
                <div className="flex flex-wrap gap-2 mt-1">
                  {progress.external_links.map((link) => (
                    <a
                      key={link.url}
                      href={link.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-center gap-1.5 text-xs text-blue-400 hover:text-blue-300 glass-panel px-3 py-1.5 rounded-lg transition-all duration-200 hover:border-blue-400/30"
                    >
                      <ExternalLinkIcon className="w-3 h-3" />
                      {link.label}
                    </a>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* ── Body ─────────────────────────────────────────────────────────── */}
        <div className="px-4 md:px-8 mt-2 flex flex-col gap-8">

          {/* ── US6: Progress Tracker Panel ─────────────────────────────────── */}
          <section className="glass-panel rounded-xl p-5 flex flex-col gap-5">
            <h2 className="text-xs font-bold text-slate-400 uppercase tracking-widest">
              Gestão de Progresso
              <SavingIndicator saving={savingProgress} />
            </h2>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">

              {/* Current unit stepper */}
              <div className="flex flex-col gap-2">
                <label className="text-xs text-slate-500">
                  {isAnime ? 'Episódio atual' : 'Capítulo atual'}
                </label>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => handleUnitChange(-1)}
                    disabled={progress.current_unit <= 0 || savingProgress}
                    className="p-2 rounded-lg glass-panel text-slate-300 hover:text-white disabled:opacity-30 disabled:cursor-not-allowed transition-all"
                    aria-label="Decrementar"
                  >
                    <Minus className="w-4 h-4" />
                  </button>
                  <input
                    type="number"
                    min={0}
                    max={media.total_units ?? undefined}
                    value={progress.current_unit}
                    onChange={(e) => handleUnitInput(parseInt(e.target.value, 10) || 0)}
                    className="w-20 text-center bg-slate-900/60 border border-slate-700/50 rounded-lg px-2 py-2 text-sm text-slate-200 focus:outline-none focus:ring-1 focus:ring-indigo-500/60"
                  />
                  <button
                    onClick={() => handleUnitChange(+1)}
                    disabled={
                      savingProgress ||
                      (media.total_units != null && progress.current_unit >= media.total_units)
                    }
                    className="p-2 rounded-lg glass-panel text-slate-300 hover:text-white disabled:opacity-30 disabled:cursor-not-allowed transition-all"
                    aria-label="Incrementar"
                  >
                    <Plus className="w-4 h-4" />
                  </button>
                  {media.total_units && (
                    <span className="text-xs text-slate-600">/ {media.total_units}</span>
                  )}
                </div>
              </div>

              {/* Status selector */}
              <div className="flex flex-col gap-2">
                <label className="text-xs text-slate-500">Status</label>
                <select
                  value={progress.status}
                  onChange={(e) => handleStatusChange(e.target.value)}
                  disabled={savingProgress}
                  className="bg-slate-900/60 border border-slate-700/50 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:ring-1 focus:ring-indigo-500/60 disabled:opacity-50"
                >
                  {PROGRESS_STATUSES.map((s) => (
                    <option key={s.value} value={s.value}>
                      {s.label}
                    </option>
                  ))}
                </select>
              </div>

              {/* Personal score */}
              <div className="flex flex-col gap-2">
                <label className="text-xs text-slate-500">Nota pessoal (0-10)</label>
                <div className="flex items-center gap-2">
                  {[...Array(11)].map((_, score) => (
                    <button
                      key={score}
                      onClick={() =>
                        handleScoreChange(progress.personal_score === score ? undefined : score)
                      }
                      disabled={savingProgress}
                      className={`w-7 h-7 rounded-md text-xs font-bold transition-all duration-150 disabled:opacity-50 ${
                        progress.personal_score === score
                          ? 'bg-amber-500 text-white shadow-md shadow-amber-500/30'
                          : 'glass-panel text-slate-500 hover:text-amber-400 hover:border-amber-500/30'
                      }`}
                      aria-label={`Nota ${score}`}
                    >
                      {score}
                    </button>
                  ))}
                </div>
              </div>

              {/* Favorite toggle */}
              <div className="flex flex-col gap-2">
                <label className="text-xs text-slate-500">Favorito</label>
                <button
                  onClick={handleFavoriteToggle}
                  disabled={savingProgress}
                  className={`self-start flex items-center gap-2 px-4 py-2 rounded-lg border text-sm font-semibold transition-all duration-200 disabled:opacity-50 ${
                    progress.is_favorite
                      ? 'bg-pink-500/20 border-pink-500/40 text-pink-400 hover:bg-pink-500/30'
                      : 'glass-panel text-slate-400 hover:text-pink-400 hover:border-pink-500/30'
                  }`}
                  aria-pressed={progress.is_favorite}
                >
                  <Heart
                    className={`w-4 h-4 transition-all ${
                      progress.is_favorite ? 'fill-pink-400' : ''
                    }`}
                  />
                  {progress.is_favorite ? 'Favoritado' : 'Favoritar'}
                </button>
              </div>
            </div>
          </section>

          {/* ── US6: Tags Management ─────────────────────────────────────────── */}
          <section className="glass-panel rounded-xl p-5 flex flex-col gap-3">
            <h2 className="text-xs font-bold text-slate-400 uppercase tracking-widest flex items-center gap-2">
              <Tag className="w-3.5 h-3.5" />
              Tags Pessoais
              <SavingIndicator saving={savingTags} />
            </h2>

            <div className="flex flex-wrap gap-2">
              {progress.personal_tags.map((tag) => (
                <span
                  key={tag}
                  className="flex items-center gap-1 text-xs text-slate-300 bg-slate-800/60 border border-slate-700/40 px-2.5 py-1 rounded-full group"
                >
                  {tag}
                  <button
                    onClick={() => removeTag(tag)}
                    className="text-slate-600 hover:text-red-400 transition-colors ml-0.5"
                    aria-label={`Remover tag ${tag}`}
                  >
                    <X className="w-3 h-3" />
                  </button>
                </span>
              ))}

              {/* Add tag input */}
              <div className="flex items-center gap-1">
                <input
                  type="text"
                  value={tagInput}
                  onChange={(e) => setTagInput(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && addTag()}
                  placeholder="Nova tag..."
                  className="bg-slate-900/60 border border-slate-700/50 rounded-full px-3 py-1 text-xs text-slate-200 placeholder-slate-600 focus:outline-none focus:ring-1 focus:ring-indigo-500/60 w-28 transition-all focus:w-36"
                />
                {tagInput.trim() && (
                  <button
                    onClick={addTag}
                    className="text-xs text-indigo-400 hover:text-indigo-300 transition-colors"
                    aria-label="Adicionar tag"
                  >
                    <Check className="w-4 h-4" />
                  </button>
                )}
              </div>
            </div>
          </section>

          {/* ── US6: External Links Editor ───────────────────────────────────── */}
          <section className="glass-panel rounded-xl p-5 flex flex-col gap-3">
            <h2 className="text-xs font-bold text-slate-400 uppercase tracking-widest flex items-center gap-2">
              <Link2 className="w-3.5 h-3.5" />
              Links Externos
              <SavingIndicator saving={savingLinks} />
            </h2>

            <div className="flex flex-col gap-2">
              {progress.external_links.map((link) => (
                <div
                  key={link.url}
                  className="flex items-center justify-between gap-3 p-2.5 rounded-lg border border-slate-700/30 bg-slate-800/20"
                >
                  <a
                    href={link.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-2 text-sm text-blue-400 hover:text-blue-300 transition-colors min-w-0"
                  >
                    <ExternalLinkIcon className="w-3.5 h-3.5 flex-none" />
                    <span className="truncate font-medium">{link.label}</span>
                    <span className="text-xs text-slate-600 truncate hidden sm:block">{link.url}</span>
                  </a>
                  <button
                    onClick={() => removeLink(link.url)}
                    className="flex-none text-slate-600 hover:text-red-400 transition-colors"
                    aria-label={`Remover link ${link.label}`}
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>
              ))}

              {/* Add link form */}
              {showLinkForm ? (
                <div className="flex flex-col gap-2 p-3 rounded-lg border border-slate-700/40 bg-slate-800/30 mt-1">
                  <div className="flex gap-2">
                    <input
                      type="text"
                      value={linkLabelInput}
                      onChange={(e) => setLinkLabelInput(e.target.value)}
                      placeholder="Rótulo (ex: Crunchyroll)"
                      className="flex-1 bg-slate-900/60 border border-slate-700/50 rounded-lg px-3 py-1.5 text-sm text-slate-200 placeholder-slate-600 focus:outline-none focus:ring-1 focus:ring-indigo-500/60"
                    />
                    <input
                      type="url"
                      value={linkUrlInput}
                      onChange={(e) => setLinkUrlInput(e.target.value)}
                      onKeyDown={(e) => e.key === 'Enter' && addLink()}
                      placeholder="https://..."
                      className="flex-[2] bg-slate-900/60 border border-slate-700/50 rounded-lg px-3 py-1.5 text-sm text-slate-200 placeholder-slate-600 focus:outline-none focus:ring-1 focus:ring-indigo-500/60"
                    />
                  </div>
                  <div className="flex gap-2 justify-end">
                    <button
                      onClick={addLink}
                      disabled={!linkLabelInput.trim() || !linkUrlInput.trim()}
                      className="flex items-center gap-1 text-xs px-3 py-1.5 rounded-lg bg-indigo-600/80 hover:bg-indigo-500/80 text-white border border-indigo-500/30 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
                    >
                      <Check className="w-3 h-3" />
                      Adicionar
                    </button>
                    <button
                      onClick={() => { setShowLinkForm(false); setLinkLabelInput(''); setLinkUrlInput(''); }}
                      className="flex items-center gap-1 text-xs px-3 py-1.5 rounded-lg border border-slate-700/40 text-slate-400 hover:text-slate-200 transition-all"
                    >
                      <X className="w-3 h-3" />
                      Cancelar
                    </button>
                  </div>
                </div>
              ) : (
                <button
                  onClick={() => setShowLinkForm(true)}
                  className="flex items-center gap-1.5 text-xs text-slate-500 hover:text-indigo-400 border border-dashed border-slate-700/50 hover:border-indigo-500/40 rounded-lg py-2 px-3 transition-all duration-200 self-start mt-1"
                >
                  <Plus className="w-3.5 h-3.5" />
                  Adicionar link
                </button>
              )}
            </div>
          </section>

          {/* ── Synopsis ─────────────────────────────────────────────────────── */}
          {media.synopsis && (
            <section>
              <h2 className="text-base font-bold text-slate-300 mb-2 uppercase tracking-widest text-xs">
                Sinopse
              </h2>
              <p className="text-slate-400 leading-relaxed text-sm md:text-base">
                {media.synopsis}
              </p>
            </section>
          )}

          {/* ── Image Gallery ─────────────────────────────────────────────────── */}
          {galleries.length > 0 && (
            <section>
              <div className="flex items-center gap-2 mb-3">
                <Images className="w-4 h-4 text-indigo-400" />
                <h2 className="text-base font-bold text-slate-100">Galeria de Imagens</h2>
                <span className="text-xs text-slate-500">({galleries.length})</span>
              </div>

              <div className="flex gap-3 overflow-x-auto pb-2" style={{ scrollbarWidth: 'thin' }}>
                {galleries.map((url, idx) => (
                  <button
                    key={idx}
                    onClick={() => openGallery(idx)}
                    className="flex-none w-32 md:w-44 aspect-video rounded-lg overflow-hidden ring-1 ring-white/5 hover:ring-blue-400/40 transition-all duration-200 hover:scale-[1.03] shadow-md"
                    aria-label={`Abrir imagem ${idx + 1} em tela cheia`}
                  >
                    <img
                      src={url}
                      alt={`Gallery ${idx + 1}`}
                      className="w-full h-full object-cover"
                      loading="lazy"
                    />
                  </button>
                ))}
              </div>
            </section>
          )}

          {/* ── US6: Franchise Movies (anime-only) ───────────────────────────── */}
          {isAnime && (
            <FranchiseMoviesList
              malId={media.mal_id}
              mediaType={media.type}
              movies={progress.franchise_movies ?? []}
              onMoviesChange={(updated) =>
                setProgress((prev) => ({ ...prev, franchise_movies: updated }))
              }
            />
          )}

          {/* ── Franchise Relations ───────────────────────────────────────────── */}
          {media.related_seasons && media.related_seasons.length > 0 && (
            <FranchiseRelations
              seasons={media.related_seasons}
              currentMalId={media.mal_id}
            />
          )}

        </div>
      </div>
    </>
  );
};
