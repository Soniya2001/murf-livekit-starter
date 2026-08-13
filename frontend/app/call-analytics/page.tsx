'use client';

import { useState, useEffect } from 'react';
import { 
  Phone, 
  CheckCircle2, 
  XCircle, 
  TrendingUp, 
  Languages, 
  HelpCircle, 
  ArrowLeft, 
  RefreshCw, 
  Clock, 
  Database,
  Globe,
  Compass,
  Laptop
} from 'lucide-react';
import Link from 'next/link';

interface CallOutcome {
  call_id: string;
  user_id: string;
  caller_name?: string;
  call_type: string;
  outcome: string;
  duration_seconds: number;
  language: string;
  scheme_name: string;
  success_reason: string;
  created_at: string;
}

interface ReasonBreakdown {
  success_reason: string;
  count: number;
}

interface LanguageDistribution {
  language: string;
  count: number;
}

interface CallTypeDistribution {
  call_type: string;
  count: number;
}

export default function CallAnalyticsPage() {
  const [totalCalls, setTotalCalls] = useState(0);
  const [successfulCalls, setSuccessfulCalls] = useState(0);
  const [failedCalls, setFailedCalls] = useState(0);
  const [successRate, setSuccessRate] = useState(0);
  const [recentCalls, setRecentCalls] = useState<CallOutcome[]>([]);
  const [reasons, setReasons] = useState<ReasonBreakdown[]>([]);
  const [languages, setLanguages] = useState<LanguageDistribution[]>([]);
  const [callTypes, setCallTypes] = useState<CallTypeDistribution[]>([]);
  
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const fetchAnalytics = async () => {
    try {
      setRefreshing(true);
      const res = await fetch('/api/call-analytics', { cache: 'no-store' });
      const data = await res.json();
      if (data.success) {
        setTotalCalls(data.total_calls || 0);
        setSuccessfulCalls(data.successful_calls || 0);
        setFailedCalls(data.failed_calls || 0);
        setSuccessRate(data.success_rate || 0);
        setRecentCalls(data.recent_calls || []);
        setReasons(data.reason_breakdown || []);
        setLanguages(data.language_distribution || []);
        setCallTypes(data.call_types || []);
      }
    } catch (err) {
      console.error('Failed to load analytics:', err);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchAnalytics();
  }, []);

  const formatDuration = (seconds: number) => {
    if (!seconds) return '0s';
    const mins = Math.floor(seconds / 60);
    const secs = Math.round(seconds % 60);
    return mins > 0 ? `${mins}m ${secs}s` : `${secs}s`;
  };

  const formatDate = (dateStr: string) => {
    if (!dateStr) return 'N/A';
    try {
      const d = new Date(dateStr);
      return d.toLocaleString();
    } catch (e) {
      return dateStr;
    }
  };

  return (
    <div className="min-h-screen bg-[#060b18] text-slate-100 flex flex-col font-sans">
      {/* Header */}
      <header className="w-full h-16 sticky top-0 bg-[#060b18]/90 backdrop-blur-md border-b border-white/5 flex items-center justify-between px-6 z-50">
        <div className="flex items-center gap-3">
          <Link href="/" className="p-2 hover:bg-white/5 rounded-full transition-colors">
            <ArrowLeft className="size-4 text-slate-400 hover:text-white" />
          </Link>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-sm font-bold tracking-tight">FinBuddy Call Analytics</h1>
              <span className="px-2 py-0.5 bg-emerald-500/10 border border-emerald-500/30 text-[9px] font-semibold text-emerald-400 rounded-full">
                Outcome Tracking
              </span>
            </div>
            <p className="text-[10px] text-slate-400">Call Success and Business Metric Analysis</p>
          </div>
        </div>

        <button
          onClick={fetchAnalytics}
          disabled={refreshing}
          className="flex items-center gap-1.5 px-3 py-1.5 bg-[#0e1628] border border-white/10 hover:border-slate-500 rounded-lg text-xs font-semibold text-white transition-colors cursor-pointer"
        >
          <RefreshCw className={`size-3.5 ${refreshing ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </header>

      {/* Main Body */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-6 space-y-6">
        {loading ? (
          <div className="flex flex-col items-center justify-center py-20 space-y-4">
            <RefreshCw className="size-8 text-indigo-400 animate-spin" />
            <p className="text-sm text-slate-400">Loading call outcomes...</p>
          </div>
        ) : (
          <>
            {/* Top Cards for Core Metrics */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              {/* TOTAL CALLS */}
              <div className="bg-[#0c1324] border border-white/5 p-6 rounded-2xl flex items-center justify-between shadow-xl">
                <div>
                  <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Total Calls</p>
                  <p className="text-3xl font-extrabold mt-1 text-slate-100">{totalCalls}</p>
                </div>
                <div className="p-3 bg-indigo-500/10 rounded-xl">
                  <Phone className="size-6 text-indigo-400" />
                </div>
              </div>

              {/* SUCCESSFUL CALLS */}
              <div className="bg-[#0c1324] border border-white/5 p-6 rounded-2xl flex items-center justify-between shadow-xl">
                <div>
                  <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Successful Calls</p>
                  <p className="text-3xl font-extrabold mt-1 text-emerald-400">{successfulCalls}</p>
                </div>
                <div className="p-3 bg-emerald-500/10 rounded-xl">
                  <CheckCircle2 className="size-6 text-emerald-400" />
                </div>
              </div>

              {/* FAILED CALLS */}
              <div className="bg-[#0c1324] border border-white/5 p-6 rounded-2xl flex items-center justify-between shadow-xl">
                <div>
                  <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Failed Calls</p>
                  <p className="text-3xl font-extrabold mt-1 text-rose-400">{failedCalls}</p>
                </div>
                <div className="p-3 bg-rose-500/10 rounded-xl">
                  <XCircle className="size-6 text-rose-400" />
                </div>
              </div>

              {/* SUCCESS RATE */}
              <div className="bg-[#0c1324] border border-white/5 p-6 rounded-2xl flex items-center justify-between shadow-xl">
                <div>
                  <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Success Rate</p>
                  <p className="text-3xl font-extrabold mt-1 text-indigo-400">{successRate}%</p>
                </div>
                <div className="p-3 bg-indigo-500/10 rounded-xl">
                  <TrendingUp className="size-6 text-indigo-400" />
                </div>
              </div>
            </div>

            {/* Middle Section: Breakdown charts/lists */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Success Reasons */}
              <div className="bg-[#0c1324] border border-white/5 p-6 rounded-2xl flex flex-col space-y-4 shadow-xl">
                <div className="flex items-center gap-2">
                  <HelpCircle className="size-4 text-emerald-400" />
                  <h2 className="text-sm font-bold">Successful Outcomes Breakdown</h2>
                </div>
                <div className="flex-1 space-y-3">
                  {reasons.length === 0 ? (
                    <p className="text-xs text-slate-500 py-4 text-center">No successful outcomes recorded yet.</p>
                  ) : (
                    reasons.map((r, i) => (
                      <div key={i} className="bg-[#121b2f] p-3 rounded-xl border border-white/5 flex items-center justify-between">
                        <span className="text-xs text-slate-300 font-semibold">{r.success_reason}</span>
                        <span className="px-2 py-0.5 bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-[10px] font-bold rounded-full">
                          {r.count} calls
                        </span>
                      </div>
                    ))
                  )}
                </div>
              </div>

              {/* Languages */}
              <div className="bg-[#0c1324] border border-white/5 p-6 rounded-2xl flex flex-col space-y-4 shadow-xl">
                <div className="flex items-center gap-2">
                  <Languages className="size-4 text-indigo-400" />
                  <h2 className="text-sm font-bold">Language Distribution</h2>
                </div>
                <div className="flex-1 space-y-3">
                  {languages.length === 0 ? (
                    <p className="text-xs text-slate-500 py-4 text-center">No calls recorded yet.</p>
                  ) : (
                    languages.map((l, i) => (
                      <div key={i} className="bg-[#121b2f] p-3 rounded-xl border border-white/5 flex items-center justify-between">
                        <span className="text-xs text-slate-300 font-semibold">{l.language}</span>
                        <span className="px-2 py-0.5 bg-indigo-500/10 border border-indigo-500/30 text-indigo-400 text-[10px] font-bold rounded-full">
                          {l.count} calls
                        </span>
                      </div>
                    ))
                  )}
                </div>
              </div>

              {/* Call Types */}
              <div className="bg-[#0c1324] border border-white/5 p-6 rounded-2xl flex flex-col space-y-4 shadow-xl">
                <div className="flex items-center gap-2">
                  <Laptop className="size-4 text-indigo-400" />
                  <h2 className="text-sm font-bold">Call Channel Breakdown</h2>
                </div>
                <div className="flex-1 space-y-3">
                  {callTypes.length === 0 ? (
                    <p className="text-xs text-slate-500 py-4 text-center">No call channels detected yet.</p>
                  ) : (
                    callTypes.map((t, i) => (
                      <div key={i} className="bg-[#121b2f] p-3 rounded-xl border border-white/5 flex items-center justify-between">
                        <span className="text-xs text-slate-300 font-semibold">{t.call_type === 'SIP' ? 'SIP / Linphone' : 'Browser WebApp'}</span>
                        <span className="px-2 py-0.5 bg-indigo-500/10 border border-indigo-500/30 text-indigo-400 text-[10px] font-bold rounded-full">
                          {t.count} calls
                        </span>
                      </div>
                    ))
                  )}
                </div>
              </div>
            </div>

            {/* Bottom Table: Recent Calls */}
            <div className="bg-[#0c1324] border border-white/5 rounded-2xl shadow-xl overflow-hidden">
              <div className="p-6 border-b border-white/5 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Database className="size-4 text-indigo-400" />
                  <h2 className="text-sm font-bold">Recent Call Logs</h2>
                </div>
                <span className="text-[10px] text-indigo-400 bg-indigo-500/10 px-2 py-0.5 rounded-full font-semibold">
                  Last 10 calls
                </span>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="border-b border-white/5 bg-[#121b2f]/30 text-[10px] font-bold uppercase tracking-wider text-slate-400">
                      <th className="p-4">Call ID</th>
                      <th className="p-4">Caller</th>
                      <th className="p-4">Outcome</th>
                      <th className="p-4">Duration</th>
                      <th className="p-4">Channel</th>
                      <th className="p-4">Language</th>
                      <th className="p-4">Target Scheme</th>
                      <th className="p-4">Resolution Description / Reason</th>
                      <th className="p-4">Timestamp</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-white/5 text-xs text-slate-300">
                    {recentCalls.length === 0 ? (
                      <tr>
                        <td colSpan={9} className="p-8 text-center text-slate-500 font-semibold">
                          No calls tracked in the database yet. Run some calls to see analytics!
                        </td>
                      </tr>
                    ) : (
                      recentCalls.map((call, idx) => (
                        <tr key={idx} className="hover:bg-white/[0.02] transition-colors">
                          <td className="p-4 font-mono text-[10px] text-slate-400 max-w-[120px] truncate">{call.call_id}</td>
                          <td className="p-4 font-semibold text-[11px] text-slate-200">
                            {call.caller_name || call.user_id || 'Unknown'}
                          </td>
                          <td className="p-4">
                            <span className={`px-2 py-0.5 rounded-full text-[9px] font-extrabold tracking-wide uppercase ${
                              call.outcome === 'SUCCESS' 
                                ? 'bg-emerald-500/10 border border-emerald-500/30 text-emerald-400' 
                                : call.outcome === 'FAILED'
                                ? 'bg-rose-500/10 border border-rose-500/30 text-rose-400'
                                : 'bg-amber-500/10 border border-amber-500/30 text-amber-400 animate-pulse'
                            }`}>
                              {call.outcome}
                            </span>
                          </td>
                          <td className="p-4 flex items-center gap-1 text-[11px]">
                            <Clock className="size-3 text-slate-500" />
                            {formatDuration(call.duration_seconds)}
                          </td>
                          <td className="p-4 text-[11px]">{call.call_type}</td>
                          <td className="p-4 flex items-center gap-1 text-[11px]">
                            <Globe className="size-3 text-indigo-400" />
                            {call.language}
                          </td>
                          <td className="p-4 font-semibold text-[11px]">
                            {call.scheme_name ? (
                              <span className="flex items-center gap-1">
                                <Compass className="size-3 text-slate-400" />
                                {call.scheme_name}
                              </span>
                            ) : (
                              <span className="text-slate-500">-</span>
                            )}
                          </td>
                          <td className="p-4 max-w-[200px] truncate text-[11px]">
                            {call.success_reason || <span className="text-slate-500">-</span>}
                          </td>
                          <td className="p-4 text-[10px] text-slate-400">{formatDate(call.created_at)}</td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </>
        )}
      </main>
    </div>
  );
}
