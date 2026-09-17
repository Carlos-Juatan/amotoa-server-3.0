import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  ChevronLeft, ChevronRight, ArrowLeft, Star, BookOpen,
  Play, Calendar, Tag, ExternalLink as ExternalLinkIcon,
  Loader2, AlertCircle, Images
} from 'lucide-react';
import { api } from '../services/api';
import { ImageGalleryModal } from '../components/ImageGalleryModal';
import { FranchiseRelations, type RelatedSeason } from '../components/FranchiseRelations';
import { PlaceholderImage } from '../components/common/PlaceholderImage';

// Derive the API media_type from the URL segment (animes -> anime, etc.)
const pathToApiType: Record<string, string> = {
  animes: 'anime',
  mangas: 'manga',
  light_novels: 'light_novel',
};

interface UserProgress {
  current_unit: number;
  status: string;
  is_favorite: boolean;
  personal_score?: number;
  personal_tags: string[];
  external_links: { label: string; url: string }[];
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

const statusLabel: Record<string, string> = {
  watching: 'Em andamento',
  completed: 'Finalizado',
  on_hold: 'Pausado',
  dropped: 'Dropado',
  plan_to_watch: 'Planejado',
};

const statusColor: Record<string, string> = {
  watching: 'text-blue-400 bg-blue-400/10 border-blue-400/30',
  completed: 'text-emerald-400 bg-emerald-400/10 border-emerald-400/30',
  on_hold: 'text-amber-400 bg-amber-400/10 border-amber-400/30',
  dropped: 'text-red-400 bg-red-400/10 border-red-400/30',
  plan_to_watch: 'text-slate-400 bg-slate-400/10 border-slate-400/30',
};

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

  const apiType = type ? (pathToApiType[type] ?? type) : '';

  useEffect(() => {
    if (!apiType || !id) return;

    setLoading(true);
    setError(null);

    api
      .get(`/api/media/${apiType}/${id}`)
      .then((res) => {
        const data: MediaDetail = res.data;
        setMedia(data);

        // Build sibling id list from related_seasons for lateral nav
        if (data.related_seasons && data.related_seasons.length > 0) {
          const allIds = [data.mal_id, ...data.related_seasons.map((s) => s.mal_id)].sort((a, b) => a - b);
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

  // Lateral navigation between siblings
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

  // ── Loading state ──────────────────────────────────────────────────────────
  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <Loader2 className="w-12 h-12 text-indigo-500 animate-spin" />
      </div>
    );
  }

  // ── Error state ────────────────────────────────────────────────────────────
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
  const progress = media.user_progress;
  const unitLabel = media.type === 'anime' ? 'Ep.' : 'Cap.';

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
                {media.title_default !== media.title_japanese && media.title_default !== media.title_english && (
                  <p className="text-sm text-slate-600 mt-0.5">{media.title_default}</p>
                )}
              </div>

              {/* Quick stats row */}
              <div className="flex flex-wrap items-center gap-3 mt-1">
                {/* Status badge */}
                {progress && (
                  <span className={`text-xs font-semibold px-2.5 py-1 rounded-full border ${statusColor[progress.status] ?? 'text-slate-400 bg-slate-400/10 border-slate-400/30'}`}>
                    {statusLabel[progress.status] ?? progress.status}
                  </span>
                )}

                {/* Public score */}
                {media.score_public != null && (
                  <div className="flex items-center gap-1 text-amber-400">
                    <Star className="w-4 h-4 fill-amber-400" />
                    <span className="text-sm font-bold">{media.score_public.toFixed(1)}</span>
                  </div>
                )}

                {/* Progress */}
                {progress && (
                  <div className="flex items-center gap-1 text-slate-300">
                    {media.type === 'anime' ? <Play className="w-3.5 h-3.5" /> : <BookOpen className="w-3.5 h-3.5" />}
                    <span className="text-sm">
                      {unitLabel} {progress.current_unit}
                      {media.total_units ? ` / ${media.total_units}` : ''}
                    </span>
                  </div>
                )}

                {/* Year/Season */}
                {media.year && (
                  <div className="flex items-center gap-1 text-slate-400 text-sm">
                    <Calendar className="w-3.5 h-3.5" />
                    {media.season ? `${media.season.charAt(0).toUpperCase()}${media.season.slice(1)} ` : ''}
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

              {/* Personal tags */}
              {progress && progress.personal_tags.length > 0 && (
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

              {/* External links */}
              {progress && progress.external_links.length > 0 && (
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

          {/* Synopsis */}
          {media.synopsis && (
            <section>
              <h2 className="text-base font-bold text-slate-300 mb-2 uppercase tracking-widest text-xs">Sinopse</h2>
              <p className="text-slate-400 leading-relaxed text-sm md:text-base">{media.synopsis}</p>
            </section>
          )}

          {/* Image Gallery */}
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

          {/* Franchise Relations */}
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
