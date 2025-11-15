import React, { useState } from 'react';
import { Activity, FileText, BarChart3, Moon, Sun, History } from 'lucide-react';
import ActiveCrawls from './components/ActiveCrawls';
import CrawlResults from './components/CrawlResults';
import StatsOverview from './components/StatsCard';
import CrawlLogs from './components/CrawlLogs';
import { useDarkMode } from './contexts/DarkModeContext';

function App() {
  const [activeTab, setActiveTab] = useState('active');
  const { isDark, toggleDarkMode } = useDarkMode();

  return (
    <div className="min-h-screen transition-colors">
      {/* Header */}
      <header className="glass-card dark:glass-card-dark sticky top-0 z-50 transition-all">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-white dark:text-gray-100 drop-shadow-lg">Rasad Pedia</h1>
              <p className="text-sm text-white/80 dark:text-gray-300 mt-1 drop-shadow">Crawler Dashboard</p>
            </div>
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2 text-sm text-white/90 dark:text-gray-200">
                <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse shadow-lg shadow-green-400/50"></div>
                <span className="font-medium">System Online</span>
              </div>
              <button
                onClick={toggleDarkMode}
                className="p-2 rounded-xl glass-button dark:glass-button text-white dark:text-gray-200 hover:scale-110 transition-transform"
                aria-label="Toggle dark mode"
              >
                {isDark ? (
                  <Sun className="w-5 h-5" />
                ) : (
                  <Moon className="w-5 h-5" />
                )}
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Navigation Tabs */}
      <div className="glass dark:glass-dark border-b border-white/20 dark:border-white/10 transition-all">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <nav className="flex space-x-8">
            <button
              onClick={() => setActiveTab('active')}
              className={`flex items-center gap-2 py-4 px-1 border-b-2 font-medium text-sm transition-all ${
                activeTab === 'active'
                  ? 'border-white/60 dark:border-primary-400 text-white dark:text-primary-300'
                  : 'border-transparent text-white/70 dark:text-gray-400 hover:text-white dark:hover:text-gray-300 hover:border-white/30 dark:hover:border-gray-500'
              }`}
            >
              <Activity className="w-5 h-5" />
              Active Crawls
            </button>
            <button
              onClick={() => setActiveTab('results')}
              className={`flex items-center gap-2 py-4 px-1 border-b-2 font-medium text-sm transition-all ${
                activeTab === 'results'
                  ? 'border-white/60 dark:border-primary-400 text-white dark:text-primary-300'
                  : 'border-transparent text-white/70 dark:text-gray-400 hover:text-white dark:hover:text-gray-300 hover:border-white/30 dark:hover:border-gray-500'
              }`}
            >
              <FileText className="w-5 h-5" />
              Crawl Results
            </button>
            <button
              onClick={() => setActiveTab('stats')}
              className={`flex items-center gap-2 py-4 px-1 border-b-2 font-medium text-sm transition-all ${
                activeTab === 'stats'
                  ? 'border-white/60 dark:border-primary-400 text-white dark:text-primary-300'
                  : 'border-transparent text-white/70 dark:text-gray-400 hover:text-white dark:hover:text-gray-300 hover:border-white/30 dark:hover:border-gray-500'
              }`}
            >
              <BarChart3 className="w-5 h-5" />
              Statistics
            </button>
            <button
              onClick={() => setActiveTab('logs')}
              className={`flex items-center gap-2 py-4 px-1 border-b-2 font-medium text-sm transition-all ${
                activeTab === 'logs'
                  ? 'border-white/60 dark:border-primary-400 text-white dark:text-primary-300'
                  : 'border-transparent text-white/70 dark:text-gray-400 hover:text-white dark:hover:text-gray-300 hover:border-white/30 dark:hover:border-gray-500'
              }`}
            >
              <History className="w-5 h-5" />
              Crawl Logs
            </button>
          </nav>
        </div>
      </div>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {activeTab === 'stats' && (
          <div className="mb-8">
            <StatsOverview />
          </div>
        )}
        
        {activeTab === 'active' && (
          <div className="space-y-6">
            <StatsOverview />
            <ActiveCrawls />
          </div>
        )}

        {activeTab === 'results' && (
          <div className="space-y-6">
            <StatsOverview />
            <CrawlResults />
          </div>
        )}

        {activeTab === 'logs' && (
          <div className="space-y-6">
            <StatsOverview />
            <CrawlLogs />
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="glass dark:glass-dark border-t border-white/20 dark:border-white/10 mt-12 transition-all">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <p className="text-center text-sm text-white/80 dark:text-gray-300">
            © 2025 Rasad Pedia Crawler. All rights reserved.
          </p>
        </div>
      </footer>
    </div>
  );
}

export default App;


