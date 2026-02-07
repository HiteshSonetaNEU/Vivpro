import React from 'react';
import { Search, Sparkles } from 'lucide-react';

interface EmptyStateProps {
  title: string;
  description: string;
  icon?: 'search' | 'sparkles';
  suggestions?: string[];
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  title,
  description,
  icon = 'search',
  suggestions,
}) => {
  const IconComponent = icon === 'search' ? Search : Sparkles;

  return (
    <div className="flex flex-col items-center justify-center py-16 px-4 animate-fade-in">
      <div className="bg-primary-100 p-6 rounded-full mb-6">
        <IconComponent className="w-12 h-12 text-primary-600" />
      </div>
      <h3 className="text-2xl font-bold text-slate-800 mb-2">{title}</h3>
      <p className="text-slate-600 text-center max-w-md mb-6">{description}</p>
      
      {suggestions && suggestions.length > 0 && (
        <div className="bg-white rounded-lg border border-slate-200 p-6 max-w-md w-full">
          <p className="text-sm font-medium text-slate-700 mb-3">Try searching for:</p>
          <ul className="space-y-2">
            {suggestions.map((suggestion, index) => (
              <li key={index} className="text-sm text-slate-600 flex items-start gap-2">
                <span className="text-primary-500 mt-1">•</span>
                <span>{suggestion}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};
