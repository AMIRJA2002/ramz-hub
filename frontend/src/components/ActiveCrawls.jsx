import React, { useState, useEffect } from 'react';
import { Activity, Clock, CheckCircle2, XCircle, RefreshCw, Calendar } from 'lucide-react';
import { crawlerAPI } from '../services/api';
import { useDarkMode } from '../contexts/DarkModeContext';
import { formatDateTimeWithTehranTime, getRelativeTimeUntil } from '../utils/timeFormatter';

const ActiveCrawls = () => {
  const [configs, setConfigs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [crawlingStatus, setCrawlingStatus] = useState({});
  const [activeCrawls, setActiveCrawls] = useState({});
  const [beatSchedule, setBeatSchedule] = useState({});
  const { isDark } = useDarkMode();

  const fetchConfigs = async () => {
    try {
      const data = await crawlerAPI.getConfigs();
      setConfigs(data);
    } catch (error) {
      console.error('Error fetching configs:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchActiveCrawls = async () => {
    try {
      const data = await crawlerAPI.getActiveCrawls();
      setActiveCrawls(data.active_crawls || {});
    } catch (error) {
      console.error('Error fetching active crawls:', error);
    }
  };

  const fetchBeatSchedule = async () => {
    try {
      const data = await crawlerAPI.getBeatSchedule();
      setBeatSchedule(data.schedules || {});
    } catch (error) {
      console.error('Error fetching beat schedule:', error);
    }
  };

  const triggerCrawl = async (siteName, baseUrl) => {
    try {
      setCrawlingStatus(prev => ({ ...prev, [siteName]: 'crawling' }));
      await crawlerAPI.triggerCrawl(siteName, baseUrl);
      setTimeout(() => {
        setCrawlingStatus(prev => ({ ...prev, [siteName]: 'completed' }));
        setTimeout(() => {
          setCrawlingStatus(prev => {
            const newStatus = { ...prev };
            delete newStatus[siteName];
            return newStatus;
          });
        }, 2000);
      }, 1000);
    } catch (error) {
      console.error('Error triggering crawl:', error);
      setCrawlingStatus(prev => ({ ...prev, [siteName]: 'error' }));
    }
  };

  useEffect(() => {
    fetchConfigs();
    fetchActiveCrawls();
    fetchBeatSchedule();
    
    // Refresh configs every 5 seconds
    const configInterval = setInterval(fetchConfigs, 5000);
    
    // Refresh active crawls more frequently (every 2 seconds) for real-time updates
    const activeInterval = setInterval(fetchActiveCrawls, 2000);
    
    // Refresh beat schedule every 10 seconds
    const beatInterval = setInterval(fetchBeatSchedule, 10000);
    
    return () => {
      clearInterval(configInterval);
      clearInterval(activeInterval);
      clearInterval(beatInterval);
    };
  }, []);

  if (loading) {
    return (
      <div className="glass-card dark:glass-card-dark rounded-2xl p-6">
        <div className="animate-pulse">
          <div className="h-6 bg-white/10 dark:bg-white/5 rounded w-1/4 mb-4"></div>
          <div className="space-y-3">
            <div className="h-20 bg-white/10 dark:bg-white/5 rounded-xl"></div>
            <div className="h-20 bg-white/10 dark:bg-white/5 rounded-xl"></div>
          </div>
        </div>
      </div>
    );
  }

  const activeConfigs = configs.filter(c => c.is_active);
  const inactiveConfigs = configs.filter(c => !c.is_active);

  return (
    <div className="glass-card dark:glass-card-dark rounded-xl p-6">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-2">
          <Activity className="w-6 h-6 text-white dark:text-primary-300 drop-shadow-lg" />
          <h2 className="text-2xl font-bold text-white dark:text-gray-100 drop-shadow-lg">Active Crawls</h2>
        </div>
        <button
          onClick={fetchConfigs}
          className="flex items-center gap-2 px-4 py-2 glass-button dark:glass-button text-white rounded-lg hover:scale-105 transition-all font-medium"
        >
          <RefreshCw className="w-4 h-4" />
          Refresh
        </button>
      </div>

      {activeConfigs.length === 0 && inactiveConfigs.length === 0 ? (
        <div className="text-center py-12 text-white/70 dark:text-gray-400">
          <Activity className="w-12 h-12 mx-auto mb-4 text-white/30 dark:text-gray-600" />
          <p>No crawler configurations found</p>
        </div>
      ) : (
        <div className="space-y-4">
          {activeConfigs.length > 0 && (
            <div>
              <h3 className="text-sm font-semibold text-white/80 dark:text-gray-300 mb-3 uppercase tracking-wide">
                Active Sites ({activeConfigs.length})
              </h3>
              <div className="grid gap-4">
                {activeConfigs.map((config) => {
                  const status = crawlingStatus[config.site_name];
                  const isCrawling = status === 'crawling';
                  // Check if crawl is active from backend (scheduled or background crawls)
                  const isBackendCrawling = activeCrawls[config.site_name] === true;
                  const isActiveCrawling = isCrawling || isBackendCrawling;
                  const isCompleted = status === 'completed';
                  const hasError = status === 'error';

                  return (
                    <div
                      key={config.id}
                      className={`glass-card dark:glass-card-dark rounded-xl p-4 hover:shadow-lg transition-all border-2 ${
                        isActiveCrawling
                          ? 'border-purple-400 dark:border-purple-500 bg-purple-100/30 dark:bg-purple-900/30 animate-pulse-purple'
                          : 'border-green-200 dark:border-green-800 bg-green-50 dark:bg-green-900/10'
                      }`}
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center gap-3 mb-2">
                            {isActiveCrawling ? (
                              <div className="w-3 h-3 bg-purple-500 dark:bg-purple-400 rounded-full animate-blink-purple shadow-lg shadow-purple-500/70 ring-2 ring-purple-400/50"></div>
                            ) : (
                              <div className="w-3 h-3 bg-green-500 dark:bg-green-400 rounded-full"></div>
                            )}
                            <h4 className="text-lg font-semibold text-white dark:text-gray-100 drop-shadow">
                              {config.site_name}
                            </h4>
                            {isActiveCrawling ? (
                              <span className="px-2 py-1 bg-purple-200 dark:bg-purple-800 text-purple-800 dark:text-purple-200 text-xs font-medium rounded animate-pulse border border-purple-400/50">
                                Crawling...
                              </span>
                            ) : (
                              <span className="px-2 py-1 bg-green-100 dark:bg-green-900/50 text-green-700 dark:text-green-300 text-xs font-medium rounded">
                                Active
                              </span>
                            )}
                          </div>
                          <p className="text-sm text-white/70 dark:text-gray-300 mb-3 truncate">
                            {config.base_url}
                          </p>
                          <div className="flex items-center gap-4 text-sm text-white/80 dark:text-gray-300 flex-wrap">
                            <div className="flex items-center gap-1">
                              <Clock className="w-4 h-4" />
                              <span>Every {config.crawl_interval_minutes} min</span>
                            </div>
                            {config.last_crawl && (
                              <div className="flex items-center gap-1">
                                <CheckCircle2 className="w-4 h-4" />
                                <span>
                                  Last: {formatDateTimeWithTehranTime(config.last_crawl)}
                                </span>
                              </div>
                            )}
                            {(() => {
                              // Try to get next run time from beat schedule first
                              const scheduleKey = Object.keys(beatSchedule).find(key => {
                                const keyLower = key.toLowerCase();
                                const siteNameLower = config.site_name.toLowerCase();
                                return keyLower.includes(siteNameLower) || 
                                       keyLower.includes(siteNameLower.replace('_', '')) ||
                                       beatSchedule[key]?.task?.toLowerCase().includes(siteNameLower);
                              });
                              
                              const nextRunTime = scheduleKey && beatSchedule[scheduleKey]?.next_run
                                ? beatSchedule[scheduleKey].next_run
                                : config.next_scheduled_crawl;
                              
                              if (nextRunTime && !isActiveCrawling) {
                                const relativeTime = scheduleKey && beatSchedule[scheduleKey]?.next_run_relative
                                  ? beatSchedule[scheduleKey].next_run_relative
                                  : getRelativeTimeUntil(nextRunTime);
                                
                                return (
                                  <div className="flex items-center gap-1 text-blue-200 dark:text-blue-400">
                                    <Calendar className="w-4 h-4" />
                                    <span className="font-medium">
                                      Next: {relativeTime}
                                    </span>
                                  </div>
                                );
                              }
                              return null;
                            })()}
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          {isActiveCrawling && (
                            <div className="flex items-center gap-2 px-3 py-1 bg-purple-200 dark:bg-purple-800 text-purple-800 dark:text-purple-200 rounded-lg border border-purple-400/50 animate-pulse">
                              <RefreshCw className="w-4 h-4 animate-spin" />
                              <span className="text-sm font-medium">Crawling...</span>
                            </div>
                          )}
                          {isCompleted && !isActiveCrawling && (
                            <div className="flex items-center gap-2 px-3 py-1 bg-green-100 dark:bg-green-900/50 text-green-700 dark:text-green-300 rounded-lg">
                              <CheckCircle2 className="w-4 h-4" />
                              <span className="text-sm font-medium">Done</span>
                            </div>
                          )}
                          {hasError && (
                            <div className="flex items-center gap-2 px-3 py-1 bg-red-100 dark:bg-red-900/50 text-red-700 dark:text-red-300 rounded-lg">
                              <XCircle className="w-4 h-4" />
                              <span className="text-sm font-medium">Error</span>
                            </div>
                          )}
                          {!isActiveCrawling && !status && (
                            <button
                              onClick={() => triggerCrawl(config.site_name, config.base_url)}
                              className="px-4 py-2 glass-button dark:glass-button text-white rounded-lg hover:scale-105 transition-all text-sm font-medium"
                            >
                              Crawl Now
                            </button>
                          )}
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {inactiveConfigs.length > 0 && (
            <div className="mt-6">
              <h3 className="text-sm font-semibold text-white/80 dark:text-gray-300 mb-3 uppercase tracking-wide">
                Inactive Sites ({inactiveConfigs.length})
              </h3>
              <div className="grid gap-4">
                {inactiveConfigs.map((config) => (
                  <div
                    key={config.id}
                    className="glass-card dark:glass-card-dark rounded-xl p-4 opacity-60"
                  >
                    <div className="flex items-center gap-3 mb-2">
                      <div className="w-3 h-3 bg-white/40 dark:bg-gray-600 rounded-full"></div>
                      <h4 className="text-lg font-semibold text-white/70 dark:text-gray-400">
                        {config.site_name}
                      </h4>
                      <span className="px-2 py-1 bg-white/10 dark:bg-gray-700/50 text-white/70 dark:text-gray-400 text-xs font-medium rounded-lg border border-white/10">
                        Inactive
                      </span>
                    </div>
                    <p className="text-sm text-white/60 dark:text-gray-500 truncate">{config.base_url}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default ActiveCrawls;

