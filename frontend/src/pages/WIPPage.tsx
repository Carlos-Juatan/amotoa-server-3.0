import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';
import { WIPPlaceholder } from '../components/WIPPlaceholder';

// Human-readable names for each module key
const MODULE_NAMES: Record<string, string> = {
  series: 'Series',
  youtube: 'YouTube',
  jogos: 'Jogos',
  financas: 'Finanças',
  saude_fitness: 'Saúde & Fitness',
  links: 'Links',
  trabalho: 'Trabalho',
  estudos: 'Estudos',
  filmes: 'Filmes',
};

export function WIPPage() {
  const { module } = useParams<{ module: string }>();
  const navigate = useNavigate();
  const moduleName = module ? (MODULE_NAMES[module] ?? module) : 'Módulo';

  return (
    <div className="min-h-screen flex flex-col">
      {/* Back navigation */}
      <div className="flex-none px-6 pt-6">
        <button
          id="wip-back-button"
          onClick={() => navigate('/')}
          className="inline-flex items-center gap-2 text-slate-400 hover:text-slate-200 transition-colors text-sm group"
        >
          <ArrowLeft className="w-4 h-4 group-hover:-translate-x-0.5 transition-transform" />
          Voltar ao Dashboard
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 flex items-center justify-center">
        <WIPPlaceholder moduleName={moduleName} />
      </div>
    </div>
  );
}
