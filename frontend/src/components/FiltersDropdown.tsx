import React, { useState } from 'react';
import { Filter, X, ChevronDown } from 'lucide-react';

export interface FilterOptions {
  phases: string[];
  statuses: string[];
  city?: string;
}

interface FiltersDropdownProps {
  filters: FilterOptions;
  onFilterChange: (filters: FilterOptions) => void;
  onClearFilters: () => void;
}

const PHASE_OPTIONS = ['PHASE1', 'PHASE2', 'PHASE3', 'PHASE4', 'PHASE1/PHASE2', 'PHASE2/PHASE3', 'NA'];
const STATUS_OPTIONS = [
  'RECRUITING',
  'NOT_YET_RECRUITING',
  'ACTIVE_NOT_RECRUITING',
  'COMPLETED',
  'TERMINATED',
  'SUSPENDED',
  'WITHDRAWN',
];

export const FiltersDropdown: React.FC<FiltersDropdownProps> = ({
  filters,
  onFilterChange,
  onClearFilters,
}) => {
  const [isOpen, setIsOpen] = useState(false);

  const handlePhaseToggle = (phase: string) => {
    const newPhases = filters.phases.includes(phase)
      ? filters.phases.filter((p) => p !== phase)
      : [...filters.phases, phase];
    onFilterChange({ ...filters, phases: newPhases });
  };

  const handleStatusToggle = (status: string) => {
    const newStatuses = filters.statuses.includes(status)
      ? filters.statuses.filter((s) => s !== status)
      : [...filters.statuses, status];
    onFilterChange({ ...filters, statuses: newStatuses });
  };

  const handleCityChange = (city: string) => {
    onFilterChange({ ...filters, city: city.trim() || undefined });
  };

  const formatLabel = (value: string) => {
    return value.split('_').map(word => 
      word.charAt(0) + word.slice(1).toLowerCase()
    ).join(' ');
  };

  const hasActiveFilters = filters.phases.length > 0 || filters.statuses.length > 0 || filters.city;
  const activeFilterCount = filters.phases.length + filters.statuses.length + (filters.city ? 1 : 0);

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="btn-secondary flex items-center gap-2 relative"
      >
        <Filter className="w-4 h-4" />
        <span>Filters</span>
        {activeFilterCount > 0 && (
          <span className="bg-primary-600 text-white text-xs rounded-full px-2 py-0.5 min-w-[20px] text-center">
            {activeFilterCount}
          </span>
        )}
        <ChevronDown className={`w-4 h-4 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
      </button>

      {isOpen && (
        <>
          {/* Backdrop */}
          <div
            className="fixed inset-0 z-10"
            onClick={() => setIsOpen(false)}
          />

          {/* Dropdown Panel */}
          <div className="absolute top-full left-0 mt-2 bg-white border border-slate-200 rounded-lg shadow-xl z-20 w-[600px] max-h-[500px] overflow-y-auto">
            <div className="p-4">
              {/* Header */}
              <div className="flex items-center justify-between mb-4 pb-3 border-b border-slate-200">
                <h3 className="font-semibold text-slate-800">Filter Results</h3>
                {hasActiveFilters && (
                  <button
                    onClick={() => {
                      onClearFilters();
                      setIsOpen(false);
                    }}
                    className="text-sm text-primary-600 hover:text-primary-700 font-medium"
                  >
                    Clear all
                  </button>
                )}
              </div>

              <div className="grid grid-cols-2 gap-6">
                {/* Phase Filter */}
                <div>
                  <h4 className="font-semibold text-slate-700 mb-3 text-sm">Phase</h4>
                  <div className="space-y-2 max-h-[200px] overflow-y-auto">
                    {PHASE_OPTIONS.map((phase) => (
                      <label
                        key={phase}
                        className="flex items-center gap-2 cursor-pointer hover:bg-slate-50 p-2 rounded"
                      >
                        <input
                          type="checkbox"
                          checked={filters.phases.includes(phase)}
                          onChange={() => handlePhaseToggle(phase)}
                          className="w-4 h-4 text-primary-600 border-slate-300 rounded focus:ring-primary-500"
                        />
                        <span className="text-sm text-slate-700">{formatLabel(phase)}</span>
                      </label>
                    ))}
                  </div>
                </div>

                {/* Status Filter */}
                <div>
                  <h4 className="font-semibold text-slate-700 mb-3 text-sm">Status</h4>
                  <div className="space-y-2 max-h-[200px] overflow-y-auto">
                    {STATUS_OPTIONS.map((status) => (
                      <label
                        key={status}
                        className="flex items-center gap-2 cursor-pointer hover:bg-slate-50 p-2 rounded"
                      >
                        <input
                          type="checkbox"
                          checked={filters.statuses.includes(status)}
                          onChange={() => handleStatusToggle(status)}
                          className="w-4 h-4 text-primary-600 border-slate-300 rounded focus:ring-primary-500"
                        />
                        <span className="text-sm text-slate-700">{formatLabel(status)}</span>
                      </label>
                    ))}
                  </div>
                </div>
              </div>

              {/* City Filter */}
              <div className="mt-4 pt-4 border-t border-slate-200">
                <h4 className="font-semibold text-slate-700 mb-3 text-sm">Location (City)</h4>
                <input
                  type="text"
                  value={filters.city || ''}
                  onChange={(e) => handleCityChange(e.target.value)}
                  placeholder="Enter city name..."
                  className="input-field text-sm w-full"
                />
                <p className="text-xs text-slate-500 mt-2">
                  Filter trials by facility location
                </p>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
};
