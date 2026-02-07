import React from 'react';
import { TrialCard } from './TrialCard';
import { EmptyState } from './EmptyState';
import { Pagination } from './Pagination';
import type { Trial } from '../types/trial';

interface ResultsListProps {
  trials: Trial[];
  totalResults: number;
  currentPage: number;
  totalPages: number;
  onPageChange: (page: number) => void;
  onTrialClick: (trial: Trial) => void;
  isLoading?: boolean;
  searchType?: string;
  searchQuery?: string;
}

export const ResultsList: React.FC<ResultsListProps> = ({
  trials,
  totalResults,
  currentPage,
  totalPages,
  onPageChange,
  onTrialClick,
  isLoading = false,
  searchType,
  searchQuery,
}) => {
  if (trials.length === 0) {
    return (
      <EmptyState
        title="No trials found"
        description="Try adjusting your search query or use different keywords"
        suggestions={[
          'Phase 2 breast cancer trials',
          'Recruiting diabetes studies',
          'Pfizer trials in Boston',
          'BRCA1 gene clinical trials',
        ]}
      />
    );
  }

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Results Header */}
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div>
          <h2 className="text-2xl font-bold text-slate-800">
            Search Results
          </h2>
          <p className="text-slate-600 mt-1">
            Found <span className="font-semibold text-primary-600">{totalResults.toLocaleString()}</span> matching trials
            {searchType && (
              <span className="ml-2 text-sm bg-slate-100 text-slate-700 px-2 py-1 rounded-full">
                {searchType} search
              </span>
            )}
          </p>
        </div>
        
        <div className="text-sm text-slate-600 bg-white px-4 py-2 rounded-lg border border-slate-200">
          Page {currentPage} of {totalPages}
        </div>
      </div>

      {/* Trials Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {trials.map((trial) => (
          <TrialCard
            key={trial.nct_id}
            trial={trial}
            onClick={() => onTrialClick(trial)}
            searchQuery={searchQuery}
          />
        ))}
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex justify-center pt-6">
          <Pagination
            currentPage={currentPage}
            totalPages={totalPages}
            onPageChange={onPageChange}
            isLoading={isLoading}
          />
        </div>
      )}
    </div>
  );
};
