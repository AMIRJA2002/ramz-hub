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
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 transition-colors">
      {/* Header */}
      <header className="bg-white dark:bg-gray-800 shadow-sm border-b border-gray-200 dark:border-gray-700 transition-colors">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">Rasad Pedia</h1>
              <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">Crawler Dashboard</p>
            </div>
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2 text-sm text-gray-500 dark:text-gray-400">
                <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                <span>System Online</span>
              </div>
              <button
                onClick={toggleDarkMode}
                className="p-2 rounded-lg bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
                aria-label="Toggle dark mode"
              >
                {isDark ? (
                  <Sun className="w-5 h-5 text-yellow-500" />
                ) : (
                  <Moon className="w-5 h-5 text-gray-700" />
                )}
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Navigation Tabs */}
      <div className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 transition-colors">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <nav className="flex space-x-8">
            <button
              onClick={() => setActiveTab('active')}
              className={`flex items-center gap-2 py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                activeTab === 'active'
                  ? 'border-primary-500 dark:border-primary-400 text-primary-600 dark:text-primary-400'
                  : 'border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300 hover:border-gray-300 dark:hover:border-gray-600'
              }`}
            >
              <Activity className="w-5 h-5" />
              Active Crawls
            </button>
            <button
              onClick={() => setActiveTab('results')}
              className={`flex items-center gap-2 py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                activeTab === 'results'
                  ? 'border-primary-500 dark:border-primary-400 text-primary-600 dark:text-primary-400'
                  : 'border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300 hover:border-gray-300 dark:hover:border-gray-600'
              }`}
            >
              <FileText className="w-5 h-5" />
              Crawl Results
            </button>
            <button
              onClick={() => setActiveTab('stats')}
              className={`flex items-center gap-2 py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                activeTab === 'stats'
                  ? 'border-primary-500 dark:border-primary-400 text-primary-600 dark:text-primary-400'
                  : 'border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300 hover:border-gray-300 dark:hover:border-gray-600'
              }`}
            >
              <BarChart3 className="w-5 h-5" />
              Statistics
            </button>
            <button
              onClick={() => setActiveTab('logs')}
              className={`flex items-center gap-2 py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                activeTab === 'logs'
                  ? 'border-primary-500 dark:border-primary-400 text-primary-600 dark:text-primary-400'
                  : 'border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300 hover:border-gray-300 dark:hover:border-gray-600'
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
      <footer className="bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700 mt-12 transition-colors">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <p className="text-center text-sm text-gray-500 dark:text-gray-400">
            © 2024 Rasad Pedia Crawler. All rights reserved.
          </p>
        </div>
      </footer>
    </div>
  );
}

export default App;


