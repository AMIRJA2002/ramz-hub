import React, { useState, useEffect } from 'react';
import { FileText, Activity, CheckCircle2, Clock } from 'lucide-react';
import { crawlerAPI } from '../services/api';

const StatsCard = ({ icon: Icon, title, value, subtitle, color = 'primary' }) => {
  const colorClasses = {
    primary: 'bg-primary-100 dark:bg-primary-900/30 text-primary-600 dark:text-primary-400',
    green: 'bg-green-100 dark:bg-green-900/30 text-green-600 dark:text-green-400',
    blue: 'bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400',
    purple: 'bg-purple-100 dark:bg-purple-900/30 text-purple-600 dark:text-purple-400',
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 transition-colors">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-1">{title}</p>
          <p className="text-3xl font-bold text-gray-800 dark:text-gray-100">{value}</p>
          {subtitle && <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">{subtitle}</p>}
        </div>
        <div className={`p-4 rounded-full ${colorClasses[color]}`}>
          <Icon className="w-8 h-8" />
        </div>
      </div>
    </div>
  );
};

const StatsOverview = () => {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const data = await crawlerAPI.getStats();
        setStats(data);
      } catch (error) {
        console.error('Error fetching stats:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchStats();
    const interval = setInterval(fetchStats, 15000);
    return () => clearInterval(interval);
  }, []);

  if (loading || !stats) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 animate-pulse">
            <div className="h-20 bg-gray-200 dark:bg-gray-700 rounded"></div>
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      <StatsCard
        icon={FileText}
        title="Total Articles"
        value={stats.total_articles || 0}
        subtitle="Crawled articles"
        color="primary"
      />
      <StatsCard
        icon={Activity}
        title="Active Crawlers"
        value={stats.active_crawlers || 0}
        subtitle={`of ${stats.total_crawlers || 0} total`}
        color="green"
      />
      <StatsCard
        icon={CheckCircle2}
        title="Total Crawlers"
        value={stats.total_crawlers || 0}
        subtitle="Configured sites"
        color="blue"
      />
      <StatsCard
        icon={Clock}
        title="Sites with Data"
        value={Object.keys(stats.articles_by_site || {}).length}
        subtitle="Sites crawled"
        color="purple"
      />
    </div>
  );
};

export default StatsOverview;


