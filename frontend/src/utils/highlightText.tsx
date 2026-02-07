import React from 'react';

/**
 * Highlights search terms in text by wrapping matches in <mark> tags
 * @param text - The text to search within
 * @param query - The search query to highlight
 * @returns React elements with highlighted text
 */
export const highlightText = (text: string, query: string): React.ReactNode => {
  if (!query || !text) return text;

  // Extract individual words from query (ignore common words)
  const searchTerms = query
    .toLowerCase()
    .split(/\s+/)
    .filter(term => term.length > 2 && !['the', 'and', 'for', 'with', 'trial', 'trials'].includes(term));

  if (searchTerms.length === 0) return text;

  // Create regex pattern for all search terms
  const pattern = searchTerms.map(term => term.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')).join('|');
  const regex = new RegExp(`(${pattern})`, 'gi');

  // Split text and wrap matches
  const parts = text.split(regex);

  return (
    <>
      {parts.map((part, index) => {
        const isMatch = searchTerms.some(term => part.toLowerCase() === term.toLowerCase());
        return isMatch ? (
          <mark key={index} className="bg-yellow-200 text-slate-900 font-semibold px-0.5 rounded">
            {part}
          </mark>
        ) : (
          <React.Fragment key={index}>{part}</React.Fragment>
        );
      })}
    </>
  );
};
