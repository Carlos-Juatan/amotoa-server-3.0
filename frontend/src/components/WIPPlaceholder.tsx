import { Construction, Sparkles } from 'lucide-react';

interface WIPPlaceholderProps {
  moduleName: string;
  description?: string;
}

export function WIPPlaceholder({ moduleName, description }: WIPPlaceholderProps) {
  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] px-6 text-center select-none">
      {/* Glow ring */}
      <div className="relative mb-10">
        <div className="absolute inset-0 rounded-full bg-blue-500/20 blur-3xl scale-150" />
        <div className="relative flex items-center justify-center w-28 h-28 rounded-full bg-slate-900/80 border border-slate-700/60 shadow-2xl ring-1 ring-blue-500/20">
          <Construction className="w-12 h-12 text-blue-400" strokeWidth={1.5} />
        </div>
      </div>

      {/* Badge */}
      <div className="inline-flex items-center gap-2 px-4 py-1.5 mb-5 rounded-full bg-blue-500/10 border border-blue-500/20 text-blue-400 text-xs font-semibold tracking-widest uppercase">
        <Sparkles className="w-3.5 h-3.5" />
        Em Desenvolvimento
      </div>

      {/* Heading */}
      <h1 className="text-3xl font-bold text-slate-100 mb-3 tracking-tight">
        {moduleName}
      </h1>

      {/* Description */}
      <p className="max-w-md text-slate-400 text-base leading-relaxed">
        {description ?? 'Este módulo está sendo construído com todo cuidado. Em breve estará disponível.'}
      </p>

      {/* Decorative divider */}
      <div className="mt-10 flex items-center gap-3 text-slate-700">
        <span className="h-px w-16 bg-current" />
        <span className="text-xs tracking-widest uppercase">em breve</span>
        <span className="h-px w-16 bg-current" />
      </div>
    </div>
  );
}
