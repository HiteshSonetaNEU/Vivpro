// Utility functions for managing recent searches in localStorage

const RECENT_SEARCHES_KEY = 'clinical_trials_recent_searches';
const MAX_RECENT_SEARCHES = 5;

export const getRecentSearches = (): string[] => {
  try {
    const stored = localStorage.getItem(RECENT_SEARCHES_KEY);
    return stored ? JSON.parse(stored) : [];
  } catch (error) {
    console.error('Error reading recent searches:', error);
    return [];
  }
};

export const addRecentSearch = (query: string): void => {
  try {
    const searches = getRecentSearches();
    
    // Remove duplicate if exists
    const filtered = searches.filter((s) => s.toLowerCase() !== query.toLowerCase());
    
    // Add to beginning
    const updated = [query, ...filtered].slice(0, MAX_RECENT_SEARCHES);
    
    localStorage.setItem(RECENT_SEARCHES_KEY, JSON.stringify(updated));
  } catch (error) {
    console.error('Error saving recent search:', error);
  }
};

export const clearRecentSearches = (): void => {
  try {
    localStorage.removeItem(RECENT_SEARCHES_KEY);
  } catch (error) {
    console.error('Error clearing recent searches:', error);
  }
};
