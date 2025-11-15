import React, { useState, useEffect } from 'react';
import { FileText, Calendar, Globe, Search, ChevronLeft, ChevronRight } from 'lucide-react';
import { crawlerAPI } from '../services/api';
import { useDarkMode } from '../contexts/DarkModeContext';
import { formatDateTimeWithTehranTime } from '../utils/timeFormatter';

const CrawlResults = () => {
  const { isDark } = useDarkMode();
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(true);
  const [siteFilter, setSiteFilter] = useState('');
  const [availableSites, setAvailableSites] = useState([]);
  const [currentPage, setCurrentPage] = useState(0);
  const [totalResults, setTotalResults] = useState(0);
  const itemsPerPage = 20;

  const fetchResults = async () => {
    try {
      setLoading(true);
      const data = await crawlerAPI.getResults(
        siteFilter || null,
        itemsPerPage,
        currentPage * itemsPerPage
      );
      setResults(data);
      // Estimate total based on current results
      if (data.length === itemsPerPage) {
        setTotalResults((currentPage + 1) * itemsPerPage + 1);
      } else {
        setTotalResults(currentPage * itemsPerPage + data.length);
      }
    } catch (error) {
      console.error('Error fetching results:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchConfigs = async () => {
    try {
      const configs = await crawlerAPI.getConfigs();
      const sites = [...new Set(configs.map(c => c.site_name))];
      setAvailableSites(sites);
    } catch (error) {
      console.error('Error fetching configs:', error);
    }
  };

  useEffect(() => {
    fetchConfigs();
  }, []);

  useEffect(() => {
    fetchResults();
    const interval = setInterval(fetchResults, 10000); // Refresh every 10 seconds
    return () => clearInterval(interval);
  }, [siteFilter, currentPage]);

  const formatDate = (dateString) => {
    return formatDateTimeWithTehranTime(dateString);
  };

  const truncateText = (text, maxLength = 150) => {
    if (!text) return 'No content';
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
  };

  const totalPages = Math.ceil(totalResults / itemsPerPage);

  return (
    <div className="glass-card dark:glass-card-dark rounded-xl p-6">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-2">
          <FileText className="w-6 h-6 text-white dark:text-primary-300 drop-shadow-lg" />
          <h2 className="text-2xl font-bold text-white dark:text-gray-100 drop-shadow-lg">Crawled Results</h2>
        </div>
        <div className="flex items-center gap-3">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-white/70 dark:text-gray-400 z-10" />
            <select
              value={siteFilter}
              onChange={(e) => {
                setSiteFilter(e.target.value);
                setCurrentPage(0);
              }}
                className="pl-10 pr-4 py-2 glass-input dark:glass-input text-white dark:text-gray-100 rounded-lg focus:ring-2 focus:ring-white/30 focus:border-white/50"
            >
              <option value="" className="bg-gray-800 text-white">All Sites</option>
              {availableSites.map((site) => (
                <option key={site} value={site} className="bg-gray-800 text-white">
                  {site}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {loading && results.length === 0 ? (
        <div className="animate-pulse space-y-4">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="h-32 glass-card dark:glass-card-dark rounded-xl"></div>
          ))}
        </div>
      ) : results.length === 0 ? (
        <div className="text-center py-12 text-white/70 dark:text-gray-400">
          <FileText className="w-12 h-12 mx-auto mb-4 text-white/30 dark:text-gray-600" />
          <p>No crawl results found</p>
          {siteFilter && (
            <p className="text-sm mt-2">Try selecting a different site or clear the filter</p>
          )}
        </div>
      ) : (
        <>
          <div className="space-y-4 mb-6">
            {results.map((result) => (
              <div
                key={result.id}
                className="glass-card dark:glass-card-dark rounded-xl p-4 hover:shadow-lg transition-all"
              >
                <div className="flex items-start justify-between mb-2">
                  <div className="flex-1">
                    <h3 className="text-lg font-semibold text-white dark:text-gray-100 mb-2 drop-shadow">
                      {result.title || 'Untitled Article'}
                    </h3>
                    <div className="flex items-center gap-4 text-sm text-white/80 dark:text-gray-300 mb-3 flex-wrap">
                      <div className="flex items-center gap-1">
                        <Globe className="w-4 h-4" />
                        <span className="font-medium">{result.source_site}</span>
                      </div>
                      <div className="flex items-center gap-1">
                        <Calendar className="w-4 h-4" />
                        <span>{formatDate(result.crawl_timestamp)}</span>
                      </div>
                      {result.is_processed && (
                        <span className="px-2 py-1 bg-green-100 dark:bg-green-900/50 text-green-700 dark:text-green-300 text-xs font-medium rounded">
                          Processed
                        </span>
                      )}
                    </div>
                    <p className="text-white/70 dark:text-gray-300 text-sm mb-3 line-clamp-2">
                      {truncateText(result.content)}
                    </p>
                    <a
                      href={result.source_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-white/90 dark:text-primary-300 hover:text-white dark:hover:text-primary-200 text-sm font-medium inline-flex items-center gap-1 glass-button dark:glass-button px-3 py-1.5 rounded-lg transition-all"
                    >
                      View Source
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                      </svg>
                    </a>
                  </div>
                </div>
                {result.meta && Object.keys(result.meta).length > 0 && (
                  <div className="mt-3 pt-3 border-t border-white/10 dark:border-gray-700">
                    <div className="flex flex-wrap gap-2">
                      {Object.entries(result.meta).slice(0, 5).map(([key, value]) => (
                        <span
                          key={key}
                          className="px-2 py-1 bg-white/10 dark:bg-gray-700/50 text-white/80 dark:text-gray-300 text-xs rounded-lg border border-white/10"
                        >
                          {key}: {String(value).substring(0, 20)}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>

          <div className="flex items-center justify-between pt-4 border-t border-white/20 dark:border-gray-700">
            <div className="text-sm text-white/80 dark:text-gray-300">
              Showing {currentPage * itemsPerPage + 1} to{' '}
              {Math.min((currentPage + 1) * itemsPerPage, totalResults)} of {totalResults} results
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setCurrentPage((prev) => Math.max(0, prev - 1))}
                disabled={currentPage === 0}
                className="p-2 glass-button dark:glass-button text-white dark:text-gray-300 rounded-lg hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100 transition-all"
              >
                <ChevronLeft className="w-5 h-5" />
              </button>
              <span className="px-4 py-2 text-sm text-white/90 dark:text-gray-200 font-medium">
                Page {currentPage + 1} {totalPages > 0 && `of ${totalPages}`}
              </span>
              <button
                onClick={() => setCurrentPage((prev) => prev + 1)}
                disabled={results.length < itemsPerPage}
                className="p-2 glass-button dark:glass-button text-white dark:text-gray-300 rounded-lg hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100 transition-all"
              >
                <ChevronRight className="w-5 h-5" />
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export default CrawlResults;

