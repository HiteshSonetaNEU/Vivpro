import axios from 'axios';
import type { SearchRequest, SearchResponse, TrialDetail, FiltersResponse } from '../types/trial';

const API_BASE_URL = '/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const searchTrials = async (request: SearchRequest): Promise<SearchResponse> => {
  console.log('🔍 Sending search request:', JSON.stringify(request, null, 2));
  const response = await api.post<SearchResponse>('/search', request);
  console.log('✅ Search response:', response.data.total_results, 'results');
  return response.data;
};

export const getTrialDetail = async (nctId: string): Promise<TrialDetail> => {
  const response = await api.get<{ trial: TrialDetail; found: boolean }>(`/trial/${nctId}`);
  return response.data.trial;
};

export const getFilters = async (): Promise<FiltersResponse> => {
  const response = await api.get<FiltersResponse>('/filters');
  return response.data;
};

export const findSimilarTrials = async (nctId: string): Promise<SearchResponse> => {
  const response = await api.get<SearchResponse>(`/trial/${nctId}/similar`);
  return response.data;
};

export default api;
