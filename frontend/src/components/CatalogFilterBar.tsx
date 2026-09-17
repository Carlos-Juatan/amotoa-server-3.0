import React from 'react';
import { Filter, SortAsc, SortDesc } from 'lucide-react';
import type { ShowcaseFilters } from '../hooks/useMediaShowcase';

interface CatalogFilterBarProps {
  filters: ShowcaseFilters;
  onChange: (filters: ShowcaseFilters) => void;
}

export const CatalogFilterBar: React.FC<CatalogFilterBarProps> = ({ filters, onChange }) => {
  const handleSortChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    onChange({ ...filters, sort_by: e.target.value });
  };

  const handleOrderToggle = () => {
    onChange({ ...filters, order: filters.order === 'asc' ? 'desc' : 'asc' });
  };

  const handleGenreChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const val = e.target.value;
    onChange({ ...filters, genre: val === '' ? undefined : val });
  };

  const handleYearChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = parseInt(e.target.value);
    onChange({ ...filters, year: isNaN(val) ? undefined : val });
  };

  const handleLetterChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const val = e.target.value;
    onChange({ ...filters, letter: val === '' ? undefined : val });
  };

  const letters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'.split('');
  const popularGenres = ['Action', 'Adventure', 'Comedy', 'Drama', 'Fantasy', 'Romance', 'Sci-Fi', 'Slice of Life', 'Sports', 'Supernatural'];

  return (
    <div className="flex flex-wrap items-center gap-4 p-4 bg-gray-800 rounded-lg border border-gray-700 w-full text-sm shadow-md">
      <div className="flex items-center gap-2">
        <Filter className="w-4 h-4 text-gray-400" />
        <span className="text-gray-300 font-medium">Filtros:</span>
      </div>

      <select
        value={filters.genre || ''}
        onChange={handleGenreChange}
        className="bg-gray-700 border border-gray-600 text-white rounded-md px-2 py-1.5 focus:ring-1 focus:ring-indigo-500 focus:outline-none"
      >
        <option value="">Gênero (Todos)</option>
        {popularGenres.map(g => <option key={g} value={g}>{g}</option>)}
      </select>

      <input
        type="number"
        value={filters.year || ''}
        onChange={handleYearChange}
        placeholder="Ano"
        className="bg-gray-700 border border-gray-600 text-white rounded-md px-2 py-1.5 w-20 focus:ring-1 focus:ring-indigo-500 focus:outline-none"
      />

      <select
        value={filters.letter || ''}
        onChange={handleLetterChange}
        className="bg-gray-700 border border-gray-600 text-white rounded-md px-2 py-1.5 focus:ring-1 focus:ring-indigo-500 focus:outline-none"
      >
        <option value="">Letra Inicial</option>
        {letters.map(l => <option key={l} value={l}>{l}</option>)}
      </select>

      <div className="h-6 w-px bg-gray-600 mx-2 hidden md:block"></div>

      <div className="flex items-center gap-2 ml-auto">
        <span className="text-gray-300 font-medium mr-1">Ordenar por:</span>
        <select
          value={filters.sort_by || 'title'}
          onChange={handleSortChange}
          className="bg-gray-700 border border-gray-600 text-white rounded-md px-2 py-1.5 focus:ring-1 focus:ring-indigo-500 focus:outline-none"
        >
          <option value="title">Título</option>
          <option value="score_public">Nota Pública</option>
          <option value="personal_score">Minha Nota</option>
          <option value="year">Ano Lançamento</option>
        </select>
        
        <button
          onClick={handleOrderToggle}
          className="p-1.5 bg-gray-700 hover:bg-gray-600 rounded border border-gray-600 transition-colors"
          title={`Ordem ${filters.order === 'asc' ? 'Crescente' : 'Decrescente'}`}
        >
          {filters.order === 'asc' ? <SortAsc className="w-5 h-5 text-gray-200" /> : <SortDesc className="w-5 h-5 text-gray-200" />}
        </button>
      </div>
    </div>
  );
};
