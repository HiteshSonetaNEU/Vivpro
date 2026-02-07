import React, { useState, useEffect } from 'react';
import { SearchBar } from './components/SearchBar';
import { ResultsList } from './components/ResultsList';
import { TrialDetailModal } from './components/TrialDetailModal';
import { EmptyState } from './components/EmptyState';
import { LoadingSpinner } from './components/LoadingSpinner';
import { FiltersDropdown, FilterOptions } from './components/FiltersDropdown';
import { searchTrials } from './services/api';
import type { Trial, SearchResponse } from './types/trial';
import { Sparkles, Database, Zap, Brain } from 'lucide-react';
import { getRecentSearches, addRecentSearch } from './utils/localStorage';

function App() {
  const [searchResults, setSearchResults] = useState<SearchResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedTrial, setSelectedTrial] = useState<string | null>(null);
  const [hasSearched, setHasSearched] = useState(false);
  const [currentQuery, setCurrentQuery] = useState('');
  const [filters, setFilters] = useState<FilterOptions>({ phases: [], statuses: [] });
  const [recentSearches, setRecentSearches] = useState<string[]>([]);

  useEffect(() => {
    setRecentSearches(getRecentSearches());
  }, []);

  const handleSearch = async (query: string, page: number = 1) => {
    try {
      setIsLoading(true);
      setError(null);
      setHasSearched(true);
      setCurrentQuery(query);

      // Add to recent searches
      addRecentSearch(query);
      setRecentSearches(getRecentSearches());

      const results = await searchTrials({
        query,
        page,
        page_size: 10,
        phases: filters.phases.length > 0 ? filters.phases : undefined,
        statuses: filters.statuses.length > 0 ? filters.statuses : undefined,
        city: filters.city || undefined,
      });

      setSearchResults(results);
    } catch (err) {
      setError('Failed to search trials. Please try again.');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleFilterChange = (newFilters: FilterOptions) => {
    console.log('🎯 Filters changed:', newFilters);
    setFilters(newFilters);
    
    // Search with the NEW filters immediately, don't wait for state update
    if (currentQuery) {
      handleSearchWithFilters(currentQuery, 1, newFilters);
    }
  };

  const handleClearFilters = () => {
    const emptyFilters = { phases: [], statuses: [] };
    console.log('🧹 Clearing filters');
    setFilters(emptyFilters);
    
    // Search with empty filters immediately
    if (currentQuery) {
      handleSearchWithFilters(currentQuery, 1, emptyFilters);
    }
  };

  // Helper function to search with specific filters
  const handleSearchWithFilters = async (query: string, page: number, filtersToUse: FilterOptions) => {
    try {
      setIsLoading(true);
      setError(null);

      const results = await searchTrials({
        query,
        page,
        page_size: 10,
        phases: filtersToUse.phases.length > 0 ? filtersToUse.phases : undefined,
        statuses: filtersToUse.statuses.length > 0 ? filtersToUse.statuses : undefined,
        city: filtersToUse.city || undefined,
      });

      setSearchResults(results);
    } catch (err) {
      setError('Failed to search trials. Please try again.');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  const handlePageChange = (page: number) => {
    if (searchResults) {
      handleSearch(currentQuery, page);
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }
  };

  const handleTrialClick = (trial: Trial) => {
    setSelectedTrial(trial.nct_id);
  };

  return (
    <div className="min-h-screen">
      {/* Header */}
      <header className="bg-white border-b border-slate-200 shadow-sm sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="bg-gradient-to-br from-primary-600 to-primary-700 p-3 rounded-xl shadow-lg">
                <Sparkles className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold bg-gradient-to-r from-primary-700 to-primary-900 bg-clip-text text-transparent">
                  Clinical Trials Search
                </h1>
                <p className="text-sm text-slate-600">Intelligent Discovery Platform</p>
              </div>
            </div>
            
            {/* Stats */}
            <div className="hidden md:flex items-center gap-6">
              <div className="flex items-center gap-2 text-sm">
                <Database className="w-4 h-4 text-primary-600" />
                <span className="text-slate-600">1,000+ Trials</span>
              </div>
              <div className="flex items-center gap-2 text-sm">
                <Brain className="w-4 h-4 text-primary-600" />
                <span className="text-slate-600">AI-Powered</span>
              </div>
              <div className="flex items-center gap-2 text-sm">
                <Zap className="w-4 h-4 text-primary-600" />
                <span className="text-slate-600">Real-time</span>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 py-12">
        {/* Hero Section */}
        <div className="text-center mb-12 animate-fade-in">
          <h2 className="text-4xl md:text-5xl font-bold text-slate-800 mb-4 leading-tight">
            Find Clinical Trials
            <span className="block bg-gradient-to-r from-primary-600 to-primary-700 bg-clip-text text-transparent pb-2">
              with Natural Language
            </span>
          </h2>
          <p className="text-lg text-slate-600 max-w-2xl mx-auto mb-8">
            Search thousands of clinical trials using natural language queries
          </p>

          {/* Search Bar */}
          <div className="mb-6">
            <SearchBar
              onSearch={(query) => handleSearch(query, 1)}
              isLoading={isLoading}
              recentSearches={recentSearches}
              currentQuery={currentQuery}
            />
          </div>

          {/* Quick Examples */}
          {!hasSearched && (
            <div className="flex flex-wrap justify-center items-center gap-3 animate-slide-up">
              <span className="text-sm text-slate-500">Try:</span>
              {[
                'Phase 2 breast cancer trials',
                'Recruiting diabetes studies',
                'Pfizer trials in Boston',
              ].map((example) => (
                <button
                  key={example}
                  onClick={() => handleSearch(example, 1)}
                  className="text-sm bg-white text-primary-700 px-4 py-2 rounded-full border border-primary-200 hover:bg-primary-50 hover:border-primary-300 transition-all duration-200 shadow-sm hover:shadow"
                >
                  {example}
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Results Section */}
        {(hasSearched || searchResults) && (
          <div>
            {/* Filters and Results Header */}
            {hasSearched && (
              <div className="mb-6 flex items-center gap-3">
                <FiltersDropdown
                  filters={filters}
                  onFilterChange={handleFilterChange}
                  onClearFilters={handleClearFilters}
                />
              </div>
            )}

            {isLoading && (
              <LoadingSpinner size="lg" text="Searching clinical trials..." />
            )}

            {error && (
              <div className="card p-6 bg-red-50 border-red-200 text-center">
                <p className="text-red-700">{error}</p>
              </div>
            )}

            {!isLoading && !error && searchResults && (
              <ResultsList
                trials={searchResults.results}
                totalResults={searchResults.total_results}
                currentPage={searchResults.page}
                totalPages={searchResults.total_pages}
                onPageChange={handlePageChange}
                onTrialClick={handleTrialClick}
                searchType={searchResults.search_type}
                searchQuery={currentQuery}
              />
            )}

            {!isLoading && !error && !searchResults && hasSearched && (
              <EmptyState
                title="No results"
                description="Try a different search query"
                suggestions={[
                  'Phase 2 breast cancer trials',
                  'Recruiting diabetes studies',
                  'Pfizer trials in Boston',
                ]}
              />
            )}
          </div>
        )}

        {/* Features Section */}
        {!hasSearched && (
          <div className="max-w-md mx-auto mt-16 animate-fade-in">
            <div className="card p-6 text-center hover:scale-105 transition-transform">
              <div className="bg-primary-100 p-4 rounded-full w-fit mx-auto mb-4">
                <Brain className="w-8 h-8 text-primary-600" />
              </div>
              <h3 className="font-bold text-slate-800 mb-2">AI-Powered Search</h3>
              <p className="text-sm text-slate-600">
                Natural language processing extracts key entities from your query for precise results
              </p>
            </div>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-slate-200 mt-20">
        <div className="max-w-7xl mx-auto px-4 py-8">
          <div className="flex flex-col md:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-2 text-sm text-slate-600">
              <Sparkles className="w-4 h-4 text-primary-600" />
              <span>Powered by Elasticsearch + OpenAI</span>
            </div>
            <div className="text-sm text-slate-500">
              © {new Date().getFullYear()} Clinical Trials Search Platform
            </div>
          </div>
        </div>
      </footer>

      {/* Trial Detail Modal */}
      {selectedTrial && (
        <TrialDetailModal
          nctId={selectedTrial}
          onClose={() => setSelectedTrial(null)}
          onTrialChange={(nctId) => setSelectedTrial(nctId)}
        />
      )}
    </div>
  );
}

export default App;
