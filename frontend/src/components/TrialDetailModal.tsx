import React, { useEffect, useState } from 'react';
import {
  X,
  Activity,
  Calendar,
  Users,
  MapPin,
  FileText,
  Building2,
  ExternalLink,
  Loader2,
  AlertCircle,
  Sparkles,
} from 'lucide-react';
import type { TrialDetail, Trial } from '../types/trial';
import { getTrialDetail, findSimilarTrials } from '../services/api';

interface TrialDetailModalProps {
  nctId: string;
  onClose: () => void;
  onTrialChange: (nctId: string) => void;
}

export const TrialDetailModal: React.FC<TrialDetailModalProps> = ({ nctId, onClose, onTrialChange }) => {
  const [trial, setTrial] = useState<TrialDetail | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [similarTrials, setSimilarTrials] = useState<Trial[]>([]);
  const [showingSimilar, setShowingSimilar] = useState(false);
  const [loadingSimilar, setLoadingSimilar] = useState(false);

  useEffect(() => {
    const fetchTrial = async () => {
      try {
        setIsLoading(true);
        setError(null);
        const data = await getTrialDetail(nctId);
        setTrial(data);
        // Reset similar trials when viewing a new trial
        setSimilarTrials([]);
        setShowingSimilar(false);
      } catch (err: any) {
        const errorMessage = err?.response?.data?.detail || 
                           err?.message || 
                           'Failed to load trial details. This trial may not exist in the database.';
        setError(errorMessage);
        console.error('Error fetching trial:', err);
      } finally {
        setIsLoading(false);
      }
    };

    fetchTrial();
  }, [nctId]);

  const handleShowSimilar = async () => {
    if (similarTrials.length > 0) {
      setShowingSimilar(!showingSimilar);
      return;
    }

    try {
      setLoadingSimilar(true);
      const response = await findSimilarTrials(nctId);
      setSimilarTrials(response.results);
      setShowingSimilar(true);
    } catch (err) {
      console.error('Error fetching similar trials:', err);
    } finally {
      setLoadingSimilar(false);
    }
  };

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
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4 z-50 animate-fade-in">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-4xl max-h-[90vh] overflow-hidden animate-slide-up">
        {/* Header */}
        <div className="bg-gradient-to-r from-primary-600 to-primary-700 text-white p-6 flex items-start justify-between">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-2">
              <span className="text-xs font-mono bg-white/20 px-2 py-1 rounded">
                {nctId}
              </span>
              <a
                href={`https://clinicaltrials.gov/study/${nctId}`}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-1 text-xs hover:underline"
              >
                View on ClinicalTrials.gov <ExternalLink className="w-3 h-3" />
              </a>
            </div>
            <h2 className="text-xl font-bold">Trial Details</h2>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-white/20 rounded-lg transition-colors"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        {/* Content */}
        <div className="overflow-y-auto max-h-[calc(90vh-120px)] p-6">
          {isLoading && (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="w-8 h-8 animate-spin text-primary-600" />
            </div>
          )}

          {error && (
            <div className="flex items-center gap-3 p-4 bg-red-50 text-red-700 rounded-lg">
              <AlertCircle className="w-5 h-5" />
              <span>{error}</span>
            </div>
          )}

          {trial && (
            <div className="space-y-6">
              {/* Badges */}
              <div className="flex flex-wrap gap-2">
                <span className={`badge ${getPhaseColor(trial.phase)}`}>
                  <Activity className="w-3 h-3" />
                  {trial.phase}
                </span>
                <span className={`badge ${getStatusColor(trial.overall_status)}`}>
                  {formatStatus(trial.overall_status)}
                </span>
                {trial.study_type && (
                  <span className="badge-gray">
                    {trial.study_type}
                  </span>
                )}
              </div>

              {/* Title */}
              <div>
                <h3 className="text-2xl font-bold text-slate-800 mb-2">
                  {trial.brief_title}
                </h3>
                {trial.official_title && trial.official_title !== trial.brief_title && (
                  <p className="text-slate-600">{trial.official_title}</p>
                )}
              </div>

              {/* Meta Info */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {trial.enrollment && (
                  <div className="flex items-start gap-3 p-4 bg-slate-50 rounded-lg">
                    <Users className="w-5 h-5 text-slate-600 mt-0.5" />
                    <div>
                      <p className="text-xs text-slate-500 font-medium">Enrollment</p>
                      <p className="text-lg font-semibold text-slate-800">
                        {trial.enrollment.toLocaleString()} participants
                      </p>
                    </div>
                  </div>
                )}

                {trial.start_date && (
                  <div className="flex items-start gap-3 p-4 bg-slate-50 rounded-lg">
                    <Calendar className="w-5 h-5 text-slate-600 mt-0.5" />
                    <div>
                      <p className="text-xs text-slate-500 font-medium">Start Date</p>
                      <p className="text-lg font-semibold text-slate-800">
                        {new Date(trial.start_date).toLocaleDateString()}
                      </p>
                    </div>
                  </div>
                )}

                {trial.source && (
                  <div className="flex items-start gap-3 p-4 bg-slate-50 rounded-lg">
                    <Building2 className="w-5 h-5 text-slate-600 mt-0.5" />
                    <div>
                      <p className="text-xs text-slate-500 font-medium">Source</p>
                      <p className="text-sm font-semibold text-slate-800">{trial.source}</p>
                    </div>
                  </div>
                )}

                {trial.completion_date && (
                  <div className="flex items-start gap-3 p-4 bg-slate-50 rounded-lg">
                    <Calendar className="w-5 h-5 text-slate-600 mt-0.5" />
                    <div>
                      <p className="text-xs text-slate-500 font-medium">Completion Date</p>
                      <p className="text-lg font-semibold text-slate-800">
                        {new Date(trial.completion_date).toLocaleDateString()}
                      </p>
                    </div>
                  </div>
                )}
              </div>

              {/* Description */}
              {trial.brief_summaries_description && (
                <div className="card p-6">
                  <h4 className="font-semibold text-slate-800 mb-3 flex items-center gap-2">
                    <FileText className="w-5 h-5 text-primary-600" />
                    Summary
                  </h4>
                  <p className="text-slate-600 leading-relaxed">
                    {trial.brief_summaries_description}
                  </p>
                </div>
              )}

              {/* Detailed Description */}
              {trial.detailed_description && (
                <div className="card p-6">
                  <h4 className="font-semibold text-slate-800 mb-3 flex items-center gap-2">
                    <FileText className="w-5 h-5 text-primary-600" />
                    Detailed Description
                  </h4>
                  <p className="text-slate-600 leading-relaxed whitespace-pre-line">
                    {trial.detailed_description}
                  </p>
                </div>
              )}

              {/* Conditions */}
              {trial.conditions && trial.conditions.length > 0 && (
                <div className="card p-6">
                  <h4 className="font-semibold text-slate-800 mb-3 flex items-center gap-2">
                    <Activity className="w-5 h-5 text-primary-600" />
                    Conditions ({trial.conditions.length})
                  </h4>
                  <div className="flex flex-wrap gap-2">
                    {trial.conditions.map((condition, idx) => (
                      <span
                        key={idx}
                        className="bg-primary-50 text-primary-700 px-3 py-1.5 rounded-lg text-sm border border-primary-200"
                      >
                        {condition.name}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Interventions */}
              {trial.interventions && trial.interventions.length > 0 && (
                <div className="card p-6">
                  <h4 className="font-semibold text-slate-800 mb-3 flex items-center gap-2">
                    <Activity className="w-5 h-5 text-primary-600" />
                    Interventions ({trial.interventions.length})
                  </h4>
                  <div className="space-y-3">
                    {trial.interventions.map((intervention, idx) => (
                      <div
                        key={idx}
                        className="border border-slate-200 rounded-lg p-4 hover:border-primary-300 transition-colors"
                      >
                        <div className="flex items-start gap-3">
                          <span className="badge-primary text-xs">
                            {intervention.intervention_type}
                          </span>
                          <div className="flex-1">
                            <p className="font-medium text-slate-800">{intervention.name}</p>
                            {intervention.description && (
                              <p className="text-sm text-slate-600 mt-1">
                                {intervention.description}
                              </p>
                            )}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Sponsors */}
              {trial.sponsors && trial.sponsors.length > 0 && (
                <div className="card p-6">
                  <h4 className="font-semibold text-slate-800 mb-3 flex items-center gap-2">
                    <Building2 className="w-5 h-5 text-primary-600" />
                    Sponsors ({trial.sponsors.length})
                  </h4>
                  <div className="space-y-2">
                    {trial.sponsors.map((sponsor, idx) => (
                      <div
                        key={idx}
                        className="flex items-center gap-2 text-slate-700 bg-slate-50 px-4 py-2 rounded-lg"
                      >
                        <Building2 className="w-4 h-4 text-slate-400" />
                        {sponsor.name}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Facilities */}
              {trial.facilities && trial.facilities.length > 0 && (
                <div className="card p-6">
                  <h4 className="font-semibold text-slate-800 mb-3 flex items-center gap-2">
                    <MapPin className="w-5 h-5 text-primary-600" />
                    Facilities ({trial.facilities.length})
                  </h4>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    {trial.facilities.slice(0, 10).map((facility, idx) => (
                      <div
                        key={idx}
                        className="flex items-start gap-2 text-sm text-slate-700 bg-slate-50 px-4 py-3 rounded-lg"
                      >
                        <MapPin className="w-4 h-4 text-slate-400 mt-0.5 flex-shrink-0" />
                        <div>
                          {facility.name && <p className="font-medium">{facility.name}</p>}
                          <p className="text-slate-600">
                            {[facility.city, facility.state, facility.country]
                              .filter(Boolean)
                              .join(', ')}
                          </p>
                        </div>
                      </div>
                    ))}
                  </div>
                  {trial.facilities.length > 10 && (
                    <p className="text-sm text-slate-500 mt-3 text-center">
                      +{trial.facilities.length - 10} more facilities
                    </p>
                  )}
                </div>
              )}

              {/* Similar Trials Button */}
              <div className="flex justify-center pt-4">
                <button
                  onClick={handleShowSimilar}
                  disabled={loadingSimilar}
                  className="btn-primary px-6 py-3 flex items-center gap-2"
                >
                  {loadingSimilar ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      <span>Loading Similar Cases...</span>
                    </>
                  ) : (
                    <>
                      <Sparkles className="w-4 h-4" />
                      <span>{showingSimilar ? 'Hide' : 'Show'} Similar Cases</span>
                    </>
                  )}
                </button>
              </div>

              {/* Similar Trials List */}
              {showingSimilar && similarTrials.length > 0 && (
                <div className="card p-6 border-t-4 border-primary-500">
                  <h4 className="font-semibold text-slate-800 mb-4 flex items-center gap-2">
                    <Sparkles className="w-5 h-5 text-primary-600" />
                    Similar Clinical Trials ({similarTrials.length})
                  </h4>
                  <div className="space-y-3">
                    {similarTrials.map((similarTrial) => (
                      <button
                        key={similarTrial.nct_id}
                        onClick={() => {
                          // Change to the similar trial
                          onTrialChange(similarTrial.nct_id);
                        }}
                        className="w-full text-left p-4 bg-slate-50 hover:bg-primary-50 rounded-lg transition-colors border border-slate-200 hover:border-primary-300"
                      >
                        <div className="flex items-start justify-between gap-3">
                          <div className="flex-1">
                            <h5 className="font-semibold text-slate-800 mb-1 hover:text-primary-700">
                              {similarTrial.brief_title}
                            </h5>
                            <p className="text-xs text-slate-600 mb-2">{similarTrial.nct_id}</p>
                            {similarTrial.brief_summaries_description && (
                              <p className="text-sm text-slate-600 line-clamp-2">
                                {similarTrial.brief_summaries_description}
                              </p>
                            )}
                          </div>
                          <div className="flex flex-col gap-1">
                            {similarTrial.phase && (
                              <span className={`badge-sm ${getPhaseColor(similarTrial.phase)}`}>
                                {similarTrial.phase}
                              </span>
                            )}
                            {similarTrial.overall_status && (
                              <span className={`text-xs px-2 py-1 rounded-full ${getStatusColor(similarTrial.overall_status)}`}>
                                {formatStatus(similarTrial.overall_status)}
                              </span>
                            )}
                          </div>
                        </div>
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
