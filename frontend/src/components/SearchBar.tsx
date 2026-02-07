import React, { useState, useRef, useEffect } from 'react';
import { Search, X, Sparkles, Clock } from 'lucide-react';

interface SearchBarProps {
  onSearch: (query: string) => void;
  isLoading: boolean;
  placeholder?: string;
  recentSearches?: string[];
  currentQuery?: string;
}

export const SearchBar: React.FC<SearchBarProps> = ({
  onSearch,
  isLoading,
  placeholder = 'Search clinical trials... (e.g., "Phase 2 breast cancer trials")',
  recentSearches = [],
  currentQuery = '',
}) => {
  const [query, setQuery] = useState(currentQuery);
  const [showRecent, setShowRecent] = useState(false);
  const [isFocused, setIsFocused] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Sync internal state with prop when it changes
  useEffect(() => {
    setQuery(currentQuery);
  }, [currentQuery]);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(event.target as Node) &&
        !inputRef.current?.contains(event.target as Node)
      ) {
        setShowRecent(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim() && !isLoading) {
      onSearch(query.trim());
      setShowRecent(false);
      inputRef.current?.blur();
    }
  };

  const handleClear = () => {
    setQuery('');
    inputRef.current?.focus();
  };

  const handleFocus = () => {
    setIsFocused(true);
    if (recentSearches.length > 0 && !query) {
      setShowRecent(true);
    }
  };

  const handleBlur = () => {
    setIsFocused(false);
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setQuery(value);
    // Hide recent searches when user starts typing
    if (value.trim()) {
      setShowRecent(false);
    } else if (isFocused && recentSearches.length > 0) {
      setShowRecent(true);
    }
  };

  const handleRecentClick = (search: string) => {
    setQuery(search);
    onSearch(search);
    setShowRecent(false);
    inputRef.current?.blur();
  };

  return (
    <form onSubmit={handleSubmit} className="w-full max-w-4xl mx-auto relative">
      <div className="relative">
        <div className="absolute left-4 top-1/2 -translate-y-1/2 pointer-events-none">
          <Search className="w-5 h-5 text-slate-400" />
        </div>
        
        <input
          ref={inputRef}
          type="text"
          value={query}
          onChange={handleInputChange}
          onFocus={handleFocus}
          onBlur={handleBlur}
          placeholder={placeholder}
          disabled={isLoading}
          className="w-full pl-12 pr-24 py-4 rounded-xl border-2 border-slate-200 focus:border-primary-500 focus:ring-4 focus:ring-primary-100 outline-none transition-all duration-200 text-lg disabled:bg-slate-50 disabled:cursor-not-allowed shadow-sm"
        />
        
        {query && (
          <button
            type="button"
            onClick={handleClear}
            className="absolute right-24 top-1/2 -translate-y-1/2 p-1 hover:bg-slate-100 rounded-full transition-colors"
            disabled={isLoading}
          >
            <X className="w-4 h-4 text-slate-400" />
          </button>
        )}
        
        <button
          type="submit"
          disabled={!query.trim() || isLoading}
          className="absolute right-2 top-1/2 -translate-y-1/2 btn-primary px-6 py-2.5 flex items-center gap-2"
        >
          {isLoading ? (
            <>
              <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
              <span>Searching...</span>
            </>
          ) : (
            <>
              <Sparkles className="w-4 h-4" />
              <span>Search</span>
            </>
          )}
        </button>
      </div>

      {/* Recent Searches Dropdown */}
      {showRecent && recentSearches.length > 0 && (
        <div
          ref={dropdownRef}
          className="absolute top-full left-0 right-0 mt-2 bg-white border border-slate-200 rounded-lg shadow-xl z-30 overflow-hidden"
        >
          <div className="p-2">
            <div className="flex items-center gap-2 px-3 py-2 text-xs font-semibold text-slate-500 uppercase tracking-wide">
              <Clock className="w-3 h-3" />
              <span>Recent Searches</span>
            </div>
            <div className="space-y-1">
              {recentSearches.map((search, index) => (
                <button
                  key={index}
                  type="button"
                  onMouseDown={(e) => {
                    e.preventDefault(); // Prevent input blur
                    handleRecentClick(search);
                  }}
                  className="w-full text-left px-3 py-2 text-sm text-slate-700 hover:bg-slate-50 rounded transition-colors"
                >
                  {search}
                </button>
              ))}
            </div>
          </div>
        </div>
      )}
      
      <div className="mt-3 flex items-center gap-2 text-sm text-slate-500">
        <Sparkles className="w-4 h-4 text-primary-500" />
        <span>Powered by AI - Natural language search with intelligent entity extraction</span>
      </div>
    </form>
  );
};
