import React from 'react';
import { Activity, Calendar, Users, MapPin, FileText, ChevronRight } from 'lucide-react';
import type { Trial } from '../types/trial';
import { highlightText } from '../utils/highlightText';

interface TrialCardProps {
  trial: Trial;
  onClick: () => void;
  searchQuery?: string;
}

export const TrialCard: React.FC<TrialCardProps> = ({ trial, onClick, searchQuery }) => {
  const getPhaseColor = (phase?: string) => {
    if (!phase) return 'badge-gray';
    const phaseMap: Record<string, string> = {
      'PHASE1': 'badge-primary',
      'PHASE2': 'badge-success',
      'PHASE3': 'badge-warning',
      'PHASE4': 'badge-danger',
      'NA': 'badge-gray',
    };
    return phaseMap[phase] || 'badge-gray';
  };

  const getStatusColor = (status?: string) => {
    if (!status) return 'bg-slate-100 text-slate-700';
    const statusMap: Record<string, string> = {
      'RECRUITING': 'bg-green-100 text-green-700',
      'ACTIVE_NOT_RECRUITING': 'bg-blue-100 text-blue-700',
      'COMPLETED': 'bg-slate-100 text-slate-700',
      'NOT_YET_RECRUITING': 'bg-amber-100 text-amber-700',
      'TERMINATED': 'bg-red-100 text-red-700',
      'SUSPENDED': 'bg-orange-100 text-orange-700',
      'WITHDRAWN': 'bg-red-100 text-red-700',
    };
    return statusMap[status] || 'bg-slate-100 text-slate-700';
  };

  const formatStatus = (status?: string) => {
    if (!status) return 'Unknown';
    return status.split('_').map(word => 
      word.charAt(0) + word.slice(1).toLowerCase()
    ).join(' ');
  };

  return (
    <div
      onClick={onClick}
      className="card p-6 cursor-pointer hover:scale-[1.01] transition-transform animate-fade-in group"
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-2 flex-wrap">
          <span className={`badge ${getPhaseColor(trial.phase)}`}>
            <Activity className="w-3 h-3" />
            {trial.phase}
          </span>
          <span className={`badge ${getStatusColor(trial.overall_status)}`}>
            {formatStatus(trial.overall_status)}
          </span>
        </div>
        <span className="text-xs font-mono text-slate-500 bg-slate-100 px-2 py-1 rounded">
          {trial.nct_id}
        </span>
      </div>

      {/* Title */}
      <h3 className="text-lg font-bold text-slate-800 mb-2 line-clamp-2 group-hover:text-primary-700 transition-colors">
        {searchQuery ? highlightText(trial.brief_title, searchQuery) : trial.brief_title}
      </h3>

      {/* Description */}
      {trial.brief_summaries_description && (
        <p className="text-sm text-slate-600 mb-4 line-clamp-2">
          {searchQuery ? highlightText(trial.brief_summaries_description, searchQuery) : trial.brief_summaries_description}
        </p>
      )}

      {/* Meta Info */}
      <div className="flex flex-wrap gap-4 text-sm text-slate-600 mb-4">
        {trial.conditions && trial.conditions.length > 0 && (
          <div className="flex items-center gap-1.5">
            <FileText className="w-4 h-4 text-slate-400" />
            <span className="line-clamp-1">
              {trial.conditions.map(c => c.name).join(', ')}
            </span>
          </div>
        )}
        {trial.enrollment && (
          <div className="flex items-center gap-1.5">
            <Users className="w-4 h-4 text-slate-400" />
            <span>{trial.enrollment} participants</span>
          </div>
        )}
      </div>

      {/* Interventions */}
      {trial.interventions && trial.interventions.length > 0 && (
        <div className="flex flex-wrap gap-2 mb-4">
          {trial.interventions.slice(0, 3).map((intervention, idx) => (
            <span
              key={idx}
              className="text-xs bg-primary-50 text-primary-700 px-2 py-1 rounded-full border border-primary-200"
            >
              {intervention.name}
            </span>
          ))}
          {trial.interventions.length > 3 && (
            <span className="text-xs text-slate-500 px-2 py-1">
              +{trial.interventions.length - 3} more
            </span>
          )}
        </div>
      )}

      {/* Footer */}
      <div className="flex items-center justify-between pt-4 border-t border-slate-100">
        <div className="flex items-center gap-4 text-xs text-slate-500">
          {trial.start_date && (
            <div className="flex items-center gap-1">
              <Calendar className="w-3 h-3" />
              <span>{new Date(trial.start_date).getFullYear()}</span>
            </div>
          )}
          {trial.source && (
            <div className="flex items-center gap-1">
              <MapPin className="w-3 h-3" />
              <span className="line-clamp-1">{trial.source}</span>
            </div>
          )}
        </div>
        <ChevronRight className="w-5 h-5 text-slate-400 group-hover:text-primary-600 group-hover:translate-x-1 transition-all" />
      </div>
    </div>
  );
};
