'use client';

import { useState, useEffect } from 'react';
import { AlertCircle, CheckCircle2, Clock, Inbox, ShieldAlert, ArrowLeft, RefreshCw } from 'lucide-react';
import Link from 'next/link';

interface Escalation {
  reference_id: string;
  user_id: string;
  caller_name: string;
  issue_summary: string;
  what_happened: string;
  agent_checks: string;
  urgency: string;
  language: string;
  preferred_follow_up: string;
  status: string;
  created_at: string;
}

export default function EscalationsPage() {
  const [escalations, setEscalations] = useState<Escalation[]>([]);
  const [loading, setLoading] = useState(true);
  const [filterStatus, setFilterStatus] = useState<string>('ALL');
  const [refreshing, setRefreshing] = useState(false);

  const fetchEscalations = async () => {
    try {
      setRefreshing(true);
      const url = filterStatus === 'ALL' ? '/api/escalations' : `/api/escalations?status=${filterStatus}`;
      const res = await fetch(url);
      const data = await res.json();
      if (data.success) {
        setEscalations(data.escalations || []);
      }
    } catch (err) {
      console.error('Failed to load escalations:', err);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchEscalations();
  }, [filterStatus]);

  const handleStatusChange = async (refId: string, newStatus: string) => {
    try {
      const res = await fetch('/api/escalations', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ reference_id: refId, status: newStatus }),
      });
      const data = await res.json();
      if (data.success) {
        // Update local state
        setEscalations(prev =>
          prev.map(item => (item.reference_id === refId ? { ...item, status: newStatus } : item))
        );
      }
    } catch (err) {
      console.error('Failed to update status:', err);
    }
  };

  const getUrgencyColor = (urgency: string) => {
    switch (urgency.toLowerCase()) {
      case 'high':
        return 'bg-red-500/10 border-red-500/30 text-red-400';
      case 'medium':
        return 'bg-amber-500/10 border-amber-500/30 text-amber-400';
      default:
        return 'bg-indigo-500/10 border-indigo-500/30 text-indigo-400';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'RESOLVED':
      case 'CLOSED':
        return <CheckCircle2 className="size-4 text-emerald-400" />;
      case 'IN_REVIEW':
        return <Clock className="size-4 text-amber-400 animate-pulse" />;
      default:
        return <AlertCircle className="size-4 text-indigo-400" />;
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
              <h1 className="text-sm font-bold tracking-tight">FinBuddy Support</h1>
              <span className="px-2 py-0.5 bg-indigo-500/10 border border-indigo-500/30 text-[9px] font-semibold text-indigo-400 rounded-full">
                Escalations Admin
              </span>
            </div>
            <p className="text-[10px] text-slate-400">Human-Help Escalation Dashboard</p>
          </div>
        </div>

        <button
          onClick={fetchEscalations}
          disabled={refreshing}
          className="flex items-center gap-1.5 px-3 py-1.5 bg-[#0e1628] border border-white/10 hover:border-slate-500 rounded-lg text-xs font-semibold text-white transition-colors cursor-pointer"
        >
          <RefreshCw className={`size-3.5 ${refreshing ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </header>

      {/* Main Body */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-6 space-y-6">
        {/* Filters */}
        <div className="flex flex-wrap items-center justify-between gap-4 bg-[#0c1324] border border-white/5 p-4 rounded-2xl">
          <div className="flex gap-2">
            {['ALL', 'OPEN', 'IN_REVIEW', 'RESOLVED', 'CLOSED'].map(status => (
              <button
                key={status}
                onClick={() => setFilterStatus(status)}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold tracking-wider transition-all cursor-pointer ${
                  filterStatus === status
                    ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-500/20'
                    : 'bg-[#141d30] text-slate-400 hover:bg-[#1a263e] hover:text-slate-200'
                }`}
              >
                {status.replace('_', ' ')}
              </button>
            ))}
          </div>
          
          <div className="text-xs text-slate-400">
            Total Requests: <span className="font-bold text-white">{escalations.length}</span>
          </div>
        </div>

        {/* Dashboard Grid */}
        {loading ? (
          <div className="flex flex-col items-center justify-center py-20 space-y-4">
            <RefreshCw className="size-8 text-indigo-400 animate-spin" />
            <p className="text-sm text-slate-400">Loading escalation requests...</p>
          </div>
        ) : escalations.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-20 bg-[#0c1324] border border-dashed border-white/5 rounded-3xl space-y-4">
            <Inbox className="size-12 text-slate-600" />
            <div className="text-center">
              <p className="font-bold text-slate-300">No requests found</p>
              <p className="text-xs text-slate-500">There are no escalations matching the filter criteria.</p>
            </div>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {escalations.map(esc => (
              <div
                key={esc.reference_id}
                className="bg-[#0c1324] border border-white/5 rounded-3xl p-6 flex flex-col justify-between hover:border-indigo-500/30 transition-all hover:shadow-2xl hover:shadow-indigo-500/5 group"
              >
                <div>
                  {/* Card Header */}
                  <div className="flex items-start justify-between mb-4">
                    <span className="text-xs font-mono font-bold text-indigo-400 tracking-wider">
                      {esc.reference_id}
                    </span>
                    <div className="flex gap-1.5">
                      <span className={`px-2 py-0.5 border text-[9px] font-bold rounded-full uppercase tracking-wider ${getUrgencyColor(esc.urgency)}`}>
                        {esc.urgency}
                      </span>
                    </div>
                  </div>

                  {/* Summary / Issue */}
                  <h3 className="text-base font-bold text-white mb-3 group-hover:text-indigo-300 transition-colors">
                    {esc.issue_summary}
                  </h3>

                  {/* Context Block */}
                  <div className="space-y-3 bg-[#11192b] border border-white/5 p-4 rounded-2xl text-xs mb-4">
                    <div>
                      <span className="text-slate-400 font-semibold block mb-0.5">Caller Name</span>
                      <span className="text-slate-200 font-medium">{esc.caller_name}</span>
                    </div>
                    <div>
                      <span className="text-slate-400 font-semibold block mb-0.5">What Happened</span>
                      <span className="text-slate-200 leading-relaxed block">{esc.what_happened}</span>
                    </div>
                    <div>
                      <span className="text-slate-400 font-semibold block mb-0.5">Agent Checks</span>
                      <span className="text-slate-200 leading-relaxed block">{esc.agent_checks}</span>
                    </div>
                  </div>

                  {/* Metadata */}
                  <div className="grid grid-cols-2 gap-3 text-xs mb-6 border-b border-white/5 pb-4">
                    <div>
                      <span className="text-slate-500 block">Language</span>
                      <span className="font-semibold text-slate-300">{esc.language}</span>
                    </div>
                    <div>
                      <span className="text-slate-500 block">Preferred Contact</span>
                      <span className="font-semibold text-slate-300 uppercase">{esc.preferred_follow_up}</span>
                    </div>
                    <div className="col-span-2">
                      <span className="text-slate-500 block">Created At</span>
                      <span className="font-semibold text-slate-300">
                        {new Date(esc.created_at).toLocaleString()}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Actions / Status update */}
                <div className="flex items-center justify-between gap-3 pt-2">
                  <div className="flex items-center gap-1.5 text-xs font-semibold text-slate-300">
                    {getStatusIcon(esc.status)}
                    <span>{esc.status}</span>
                  </div>

                  <select
                    value={esc.status}
                    onChange={e => handleStatusChange(esc.reference_id, e.target.value)}
                    className="bg-[#141d30] border border-white/10 text-white rounded-lg text-xs font-semibold px-2.5 py-1.5 cursor-pointer hover:border-indigo-500 transition-colors"
                  >
                    <option value="OPEN">OPEN</option>
                    <option value="IN_REVIEW">IN REVIEW</option>
                    <option value="RESOLVED">RESOLVED</option>
                    <option value="CLOSED">CLOSED</option>
                  </select>
                </div>
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
