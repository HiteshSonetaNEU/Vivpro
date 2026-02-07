import React from 'react';
import { Filter, X } from 'lucide-react';

export interface FilterOptions {
  phases: string[];
  statuses: string[];
  city?: string;
}

interface FilterSidebarProps {
  filters: FilterOptions;
  onFilterChange: (filters: FilterOptions) => void;
  onClearFilters: () => void;
  isOpen: boolean;
  onClose: () => void;
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

export const FilterSidebar: React.FC<FilterSidebarProps> = ({
  filters,
  onFilterChange,
  onClearFilters,
  isOpen,
  onClose,
}) => {
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

  return (
    <>
      {/* Mobile Overlay */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-40 lg:hidden"
          onClick={onClose}
        />
      )}

      {/* Sidebar */}
      <div
        className={`fixed lg:sticky top-0 right-0 lg:right-auto h-screen lg:h-auto w-80 bg-white border-l lg:border-l-0 lg:border-r border-slate-200 shadow-xl lg:shadow-none z-50 lg:z-0 overflow-y-auto transition-transform duration-300 ${
          isOpen ? 'translate-x-0' : 'translate-x-full lg:translate-x-0'
        }`}
      >
        <div className="p-6 space-y-6">
          {/* Header */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Filter className="w-5 h-5 text-primary-600" />
              <h3 className="font-bold text-slate-800">Filters</h3>
            </div>
            <div className="flex items-center gap-2">
              {hasActiveFilters && (
                <button
                  onClick={onClearFilters}
                  className="text-sm text-primary-600 hover:text-primary-700 font-medium"
                >
                  Clear all
                </button>
              )}
              <button
                onClick={onClose}
                className="lg:hidden p-1 hover:bg-slate-100 rounded"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
          </div>

          {/* Phase Filter */}
          <div>
            <h4 className="font-semibold text-slate-700 mb-3">Phase</h4>
            <div className="space-y-2">
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
            <h4 className="font-semibold text-slate-700 mb-3">Status</h4>
            <div className="space-y-2">
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

          {/* City Filter */}
          <div>
            <h4 className="font-semibold text-slate-700 mb-3">City</h4>
            <input
              type="text"
              value={filters.city || ''}
              onChange={(e) => handleCityChange(e.target.value)}
              placeholder="Enter city name..."
              className="input-field text-sm"
            />
            <p className="text-xs text-slate-500 mt-2">
              Filter trials by facility location
            </p>
          </div>
        </div>
      </div>
    </>
  );
};
