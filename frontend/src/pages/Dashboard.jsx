import React, { useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { 
  Users, 
  MessageSquare, 
  Calendar, 
  BellRing, 
  Cpu, 
  ArrowRight,
  TrendingUp,
  Smile,
  AlertCircle
} from 'lucide-react';
import { 
  AreaChart, 
  Area, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Legend
} from 'recharts';
import { setDashboardData, setLoading, setError } from '../redux/interactionSlice';
import axios from '../api';
import { Link } from 'react-router-dom';

const Dashboard = () => {
  const dispatch = useDispatch();
  const { 
    dashboardStats, 
    recentInteractions, 
    upcomingFollowups, 
    loading, 
    error 
  } = useSelector((state) => state.interaction);
  const user = useSelector((state) => state.auth.user);

  const fetchDashboardStats = async () => {
    dispatch(setLoading(true));
    try {
      const response = await axios.get('/api/interactions/stats/dashboard');
      dispatch(setDashboardData(response.data));
      dispatch(setLoading(false));
    } catch (err) {
      dispatch(setError(err.response?.data?.detail || 'Failed to fetch dashboard metrics.'));
    }
  };

  useEffect(() => {
    fetchDashboardStats();
  }, [dispatch]);

  // Color arrays for Sentiment Pie Chart
  const SENTIMENT_COLORS = {
    'Positive': '#10b981', // green-500
    'Neutral': '#64748b',  // slate-500
    'Negative': '#f43f5e', // rose-500
  };

  const getSentimentColor = (sentiment) => {
    return SENTIMENT_COLORS[sentiment] || '#64748b';
  };

  if (loading && !dashboardStats) {
    return (
      <div className="w-full h-[80vh] flex items-center justify-center">
        <div className="flex flex-col items-center gap-3">
          <div className="w-12 h-12 rounded-full border-4 border-sky-600 border-t-transparent animate-spin"></div>
          <p className="text-slate-500 dark:text-slate-400 font-medium">Analyzing database analytics...</p>
        </div>
      </div>
    );
  }

  // Fallback charts mock if empty
  const trendData = dashboardStats?.trends_chart || [
    { date: 'Jul 03', meetings: 0 },
    { date: 'Jul 04', meetings: 1 },
    { date: 'Jul 05', meetings: 2 },
    { date: 'Jul 06', meetings: 1 },
    { date: 'Jul 07', meetings: 3 },
    { date: 'Jul 08', meetings: 2 },
  ];

  const sentimentData = dashboardStats?.sentiment_chart?.length > 0
    ? dashboardStats.sentiment_chart
    : [
        { name: 'Positive', value: 3 },
        { name: 'Neutral', value: 1 },
        { name: 'Negative', value: 0 },
      ];

  const statCards = [
    {
      title: 'Total HCPs',
      value: dashboardStats?.total_hcps ?? 0,
      icon: Users,
      color: 'from-blue-500 to-indigo-600 shadow-blue-500/10',
      description: 'HCP profiles registered'
    },
    {
      title: 'Total Interactions',
      value: dashboardStats?.total_interactions ?? 0,
      icon: MessageSquare,
      color: 'from-sky-500 to-cyan-600 shadow-sky-500/10',
      description: 'Logged customer touchpoints'
    },
    {
      title: "Today's Meetings",
      value: dashboardStats?.todays_meetings ?? 0,
      icon: Calendar,
      color: 'from-emerald-500 to-teal-600 shadow-emerald-500/10',
      description: 'Scheduled visits today'
    },
    {
      title: 'Upcoming Follow-ups',
      value: dashboardStats?.upcoming_followups ?? 0,
      icon: BellRing,
      color: 'from-amber-500 to-orange-600 shadow-amber-500/10',
      description: 'Pending workflow triggers'
    },
    {
      title: 'AI Activities',
      value: dashboardStats?.ai_activities ?? 0,
      icon: Cpu,
      color: 'from-purple-500 to-fuchsia-600 shadow-purple-500/10',
      description: 'NLP Extractions & Logs'
    }
  ];

  return (
    <div className="space-y-8 max-w-7xl mx-auto">
      {/* Welcome Banner */}
      <div className="bg-gradient-to-r from-sky-600 to-indigo-700 rounded-2xl p-6 text-white shadow-lg relative overflow-hidden">
        <div className="absolute right-0 top-0 -translate-y-12 translate-x-12 w-64 h-64 rounded-full bg-white/10 blur-2xl pointer-events-none"></div>
        <div className="relative z-10 space-y-2">
          <h2 className="text-2xl font-bold">Hello, {user?.full_name || 'Medical Rep'}!</h2>
          <p className="text-sky-100 text-sm max-w-xl">
            Manage your doctor interactions using AI. Log meetings via conversation, search HCPs instantly, or let the CRM outline your follow-up workflows.
          </p>
          <div className="pt-2">
            <Link 
              to="/interaction"
              className="inline-flex items-center gap-2 bg-white text-sky-700 px-4 py-2 rounded-lg text-sm font-semibold hover:bg-sky-5 hover:shadow-md transition"
            >
              <span>Log New Interaction</span>
              <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
        </div>
      </div>

      {/* Statistics Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        {statCards.map((card, idx) => {
          const Icon = card.icon;
          return (
            <div 
              key={idx}
              className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-5 shadow-sm hover:shadow-md transition duration-200 flex flex-col justify-between"
            >
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-slate-400 dark:text-slate-500 uppercase tracking-wider">{card.title}</span>
                <div className={`p-2 rounded-lg bg-gradient-to-br ${card.color} text-white`}>
                  <Icon className="w-4 h-4" />
                </div>
              </div>
              <div className="mt-4">
                <span className="text-3xl font-extrabold text-slate-800 dark:text-white leading-none">{card.value}</span>
                <p className="text-[10px] text-slate-400 mt-1.5 font-medium">{card.description}</p>
              </div>
            </div>
          );
        })}
      </div>

      {/* Analytics Charts section */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Trend Area Chart */}
        <div className="lg:col-span-2 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-5 shadow-sm">
          <div className="flex items-center gap-2 mb-6">
            <TrendingUp className="w-5 h-5 text-sky-500" />
            <h3 className="font-bold text-slate-800 dark:text-white">Interaction Frequencies (7 Days)</h3>
          </div>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={trendData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="colorMeetings" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#0284c7" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#0284c7" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" className="dark:stroke-slate-800" />
                <XAxis dataKey="date" tickLine={false} tick={{ fill: '#94a3b8', fontSize: 11 }} />
                <YAxis allowDecimals={false} tickLine={false} tick={{ fill: '#94a3b8', fontSize: 11 }} />
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: '#1e293b', 
                    borderRadius: '8px', 
                    color: '#fff',
                    border: 'none',
                    fontSize: '12px'
                  }} 
                />
                <Area type="monotone" dataKey="meetings" stroke="#0284c7" strokeWidth={2} fillOpacity={1} fill="url(#colorMeetings)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Sentiment Pie Chart */}
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-5 shadow-sm">
          <div className="flex items-center gap-2 mb-6">
            <Smile className="w-5 h-5 text-sky-500" />
            <h3 className="font-bold text-slate-800 dark:text-white">Sentiment Summary</h3>
          </div>
          <div className="h-64 flex flex-col justify-between">
            <div className="h-44 relative">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={sentimentData}
                    cx="50%"
                    cy="50%"
                    innerRadius={50}
                    outerRadius={70}
                    paddingAngle={3}
                    dataKey="value"
                  >
                    {sentimentData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={getSentimentColor(entry.name)} />
                    ))}
                  </Pie>
                  <Tooltip 
                    contentStyle={{ 
                      backgroundColor: '#1e293b', 
                      borderRadius: '8px', 
                      color: '#fff',
                      border: 'none',
                      fontSize: '12px'
                    }} 
                  />
                </PieChart>
              </ResponsiveContainer>
              <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 text-center">
                <span className="text-2xl font-black text-slate-800 dark:text-white">
                  {sentimentData.reduce((a, b) => a + b.value, 0)}
                </span>
                <p className="text-[10px] text-slate-400 font-bold uppercase">Total</p>
              </div>
            </div>
            
            {/* Custom Legend */}
            <div className="flex justify-around text-xs font-semibold px-2">
              {sentimentData.map((item) => (
                <div key={item.name} className="flex items-center gap-1.5">
                  <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: getSentimentColor(item.name) }}></span>
                  <span className="text-slate-500 dark:text-slate-400">{item.name}: {item.value}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Details Row (Recent Interactions & Followup list) */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Recent Interactions (Col span 2) */}
        <div className="lg:col-span-2 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-5 shadow-sm">
          <div className="flex items-center justify-between mb-6">
            <h3 className="font-bold text-slate-800 dark:text-white">Recent Interactions</h3>
            <Link to="/interaction" className="text-xs font-bold text-sky-600 dark:text-sky-400 hover:underline">View CRM Module</Link>
          </div>

          {!recentInteractions || recentInteractions.length === 0 ? (
            <div className="py-12 text-center text-slate-400">
              <MessageSquare className="w-10 h-10 mx-auto opacity-20 mb-3" />
              <p className="text-sm font-medium">No interactions logged yet.</p>
              <p className="text-xs mt-1">Use the CRM panel to log your first meeting!</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse text-sm">
                <thead>
                  <tr className="border-b border-slate-100 dark:border-slate-800 text-slate-400 text-xs font-bold uppercase">
                    <th className="pb-3">Doctor</th>
                    <th className="pb-3">Type</th>
                    <th className="pb-3">Date</th>
                    <th className="pb-3">Topics Discussed</th>
                    <th className="pb-3 text-right">Sentiment</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                  {recentInteractions.map((item) => (
                    <tr key={item.id} className="hover:bg-slate-50/50 dark:hover:bg-slate-800/30 transition-colors">
                      <td className="py-3.5 font-semibold text-slate-800 dark:text-slate-200">{item.hcp_name}</td>
                      <td className="py-3.5 text-slate-500 dark:text-slate-400">
                        <span className="px-2 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-[11px] font-bold">
                          {item.type}
                        </span>
                      </td>
                      <td className="py-3.5 text-slate-500 dark:text-slate-400 whitespace-nowrap">{item.date}</td>
                      <td className="py-3.5 text-slate-600 dark:text-slate-300 max-w-xs truncate">{item.topics || 'Product discussion'}</td>
                      <td className="py-3.5 text-right">
                        <span 
                          className="px-2 py-0.5 rounded-full text-[10px] font-extrabold uppercase border"
                          style={{ 
                            color: getSentimentColor(item.sentiment),
                            borderColor: getSentimentColor(item.sentiment) + '30',
                            backgroundColor: getSentimentColor(item.sentiment) + '10'
                          }}
                        >
                          {item.sentiment}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Upcoming Tasks / Followups */}
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-5 shadow-sm flex flex-col">
          <div className="flex items-center justify-between mb-6">
            <h3 className="font-bold text-slate-800 dark:text-white">Upcoming Follow-ups</h3>
            <span className="bg-sky-50 dark:bg-sky-950/40 text-sky-600 dark:text-sky-400 text-xs px-2 py-0.5 rounded-full font-bold">
              {upcomingFollowups.length} Tasks
            </span>
          </div>

          <div className="space-y-4 overflow-y-auto flex-1 max-h-72">
            {!upcomingFollowups || upcomingFollowups.length === 0 ? (
              <div className="py-12 text-center text-slate-400 flex flex-col justify-center items-center h-full">
                <BellRing className="w-10 h-10 opacity-20 mb-3" />
                <p className="text-sm font-medium">All caught up!</p>
                <p className="text-xs mt-1">No pending follow-ups found.</p>
              </div>
            ) : (
              upcomingFollowups.map((task) => (
                <div 
                  key={task.id} 
                  className="p-3 bg-slate-50 dark:bg-slate-800/40 border border-slate-200/60 dark:border-slate-800 rounded-lg hover:shadow-sm transition"
                >
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <h4 className="font-bold text-xs text-slate-800 dark:text-slate-200">{task.hcp_name}</h4>
                      <p className="text-xs text-slate-500 dark:text-slate-400 mt-1 leading-snug">{task.action}</p>
                    </div>
                    <span className="text-[10px] font-bold text-slate-400 border border-slate-200 dark:border-slate-700 px-1.5 py-0.5 rounded whitespace-nowrap">
                      {task.due_date}
                    </span>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
