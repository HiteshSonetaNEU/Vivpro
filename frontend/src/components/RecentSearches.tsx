import React from 'react';
import { Clock, X } from 'lucide-react';

interface RecentSearchesProps {
  searches: string[];
  onSearchClick: (query: string) => void;
  onClear: () => void;
}

export const RecentSearches: React.FC<RecentSearchesProps> = ({
  searches,
  onSearchClick,
  onClear,
}) => {
  if (searches.length === 0) return null;

  return (
    <div className="bg-white rounded-lg border border-slate-200 p-4 shadow-sm">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <Clock className="w-4 h-4 text-slate-500" />
          <h3 className="text-sm font-semibold text-slate-700">Recent Searches</h3>
        </div>
        <button
          onClick={onClear}
          className="text-xs text-slate-500 hover:text-slate-700 transition-colors"
          title="Clear history"
        >
          <X className="w-4 h-4" />
        </button>
      </div>
      <div className="space-y-2">
        {searches.map((search, index) => (
          <button
            key={index}
            onClick={() => onSearchClick(search)}
            className="w-full text-left text-sm text-slate-600 hover:text-primary-600 hover:bg-primary-50 px-3 py-2 rounded transition-colors flex items-center gap-2 group"
          >
            <Clock className="w-3 h-3 text-slate-400 group-hover:text-primary-500" />
            <span className="truncate">{search}</span>
          </button>
        ))}
      </div>
    </div>
  );
};
