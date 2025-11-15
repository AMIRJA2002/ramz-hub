import React, { useState, useEffect } from 'react';
import { FileText, Activity, CheckCircle2, Clock } from 'lucide-react';
import { crawlerAPI } from '../services/api';

const StatsCard = ({ icon: Icon, title, value, subtitle, color = 'primary' }) => {
  const colorClasses = {
    primary: 'bg-primary-500/20 text-primary-200 border-primary-400/30',
    green: 'bg-green-500/20 text-green-200 border-green-400/30',
    blue: 'bg-blue-500/20 text-blue-200 border-blue-400/30',
    purple: 'bg-purple-500/20 text-purple-200 border-purple-400/30',
  };

  return (
    <div className="glass-card dark:glass-card-dark rounded-xl p-6 hover:shadow-lg transition-all">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-white/80 dark:text-gray-300 mb-1">{title}</p>
          <p className="text-3xl font-bold text-white dark:text-gray-100 drop-shadow-lg">{value}</p>
          {subtitle && <p className="text-xs text-white/70 dark:text-gray-400 mt-1">{subtitle}</p>}
        </div>
        <div className={`p-4 rounded-xl ${colorClasses[color]}`}>
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
          <div key={i} className="glass-card dark:glass-card-dark rounded-xl p-6 animate-pulse">
            <div className="h-20 bg-white/10 dark:bg-white/5 rounded-lg"></div>
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


