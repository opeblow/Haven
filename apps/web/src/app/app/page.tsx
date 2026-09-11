"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import {
  Package,
  Users,
  Globe,
  Truck,
  TrendingUp,
  Clock,
  Zap,
  ArrowUpRight,
  Loader2,
  AlertCircle,
} from "lucide-react";
import {
  fetchDashboardStats,
  fetchEventFeed,
  type DashboardStats,
  type AgentEvent,
} from "@/lib/api";

const agentColors: Record<string, string> = {
  donor_agent: "bg-rose-500/20 text-rose-400",
  volunteer_agent: "bg-violet-500/20 text-violet-400",
  recipient_agent: "bg-haven-green/20 text-haven-green",
  logistics_agent: "bg-amber-500/20 text-amber-400",
  compliance_agent: "bg-cyan-500/20 text-cyan-400",
};

const statusColors: Record<string, string> = {
  completed: "bg-haven-green/20 text-haven-green",
  processing: "bg-haven-amber/20 text-haven-amber",
  in_progress: "bg-haven-cyan/20 text-haven-cyan",
  medium: "bg-haven-amber/20 text-haven-amber",
  high: "bg-rose-500/20 text-rose-400",
  critical: "bg-rose-500/20 text-rose-400",
  low: "bg-haven-green/20 text-haven-green",
};

function formatEventType(type: string): string {
  return type.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

function timeAgo(iso: string): string {
  try {
    const diff = Date.now() - new Date(iso).getTime();
    const mins = Math.floor(diff / 60000);
    if (mins < 1) return "just now";
    if (mins < 60) return `${mins}m ago`;
    const hrs = Math.floor(mins / 60);
    if (hrs < 24) return `${hrs}h ago`;
    return `${Math.floor(hrs / 24)}d ago`;
  } catch {
    return "";
  }
}

export default function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [events, setEvents] = useState<AgentEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      try {
        const [statsData, eventsData] = await Promise.all([
          fetchDashboardStats(),
          fetchEventFeed(10),
        ]);
        setStats(statsData);
        setEvents(eventsData.events);
        setError(null);
      } catch (e) {
        setError(e instanceof Error ? e.message : "Failed to load dashboard");
      } finally {
        setLoading(false);
      }
    }
    load();
    const interval = setInterval(load, 30000);
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-6 h-6 text-haven-green animate-spin" />
        <span className="ml-3 text-haven-muted">Loading dashboard...</span>
      </div>
    );
  }

  if (!stats && error) {
    return (
      <div className="flex items-center justify-center h-64">
        <AlertCircle className="w-6 h-6 text-rose-400" />
        <span className="ml-3 text-haven-muted">{error}</span>
      </div>
    );
  }

  const statCards = [
    {
      label: "Total Donations",
      value: stats?.total_donations?.toLocaleString() || "0",
      icon: Package,
      color: "text-haven-green",
    },
    {
      label: "Active Volunteers",
      value: stats?.active_volunteers?.toLocaleString() || "0",
      icon: Users,
      color: "text-violet-400",
    },
    {
      label: "Lbs Distributed",
      value: stats?.total_lbs_distributed?.toLocaleString() || "0",
      icon: Truck,
      color: "text-haven-amber",
    },
    {
      label: "Open Shifts",
      value: stats?.open_shifts?.toLocaleString() || "0",
      icon: Clock,
      color: "text-haven-cyan",
    },
  ];

  const recentEvents = events.slice(0, 6).map((evt) => ({
    ...evt,
    summary: `${formatEventType(evt.event_type)} — ${Object.values(evt.payload).filter((v) => typeof v === "string").slice(0, 2).join(", ")}`,
    agentLabel: formatEventType(evt.source),
    time: timeAgo(evt.created_at),
  }));

  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-2xl font-serif">
          Good afternoon, <span className="gradient-text">Coordinator</span>
        </h2>
        <p className="text-haven-muted text-sm mt-1">
          {stats ? (
            <>
              {stats.active_volunteers} active volunteers. {stats.open_shifts} open shifts.{" "}
              {stats.total_donations} total donations.
            </>
          ) : (
            "System starting up..."
          )}
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {statCards.map((stat, i) => {
          const Icon = stat.icon;
          return (
            <motion.div
              key={stat.label}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.1 }}
              className="bg-haven-elevated border border-haven-border rounded-card p-5 hover:border-haven-green/20 transition-all group"
            >
              <div className="flex items-start justify-between mb-4">
                <div className={`w-9 h-9 rounded-lg bg-haven-surface flex items-center justify-center ${stat.color}`}>
                  <Icon className="w-4 h-4" />
                </div>
              </div>
              <div className="text-2xl font-bold font-mono">{stat.value}</div>
              <div className="text-xs text-haven-muted mt-1">{stat.label}</div>
            </motion.div>
          );
        })}
      </div>

      <div className="grid lg:grid-cols-3 gap-6">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="lg:col-span-1 bg-haven-elevated border border-haven-border rounded-card p-5"
        >
          <h3 className="text-sm font-medium mb-4">Agent Network</h3>
          <div className="relative h-64">
            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-12 h-12 rounded-full bg-gradient-to-br from-haven-green to-haven-cyan flex items-center justify-center z-10">
              <Zap className="w-5 h-5 text-haven-bg" />
            </div>
            {[
              { name: "Donor", angle: 0, color: "#F43F5E" },
              { name: "Volunteer", angle: 72, color: "#8B5CF6" },
              { name: "Recipient", angle: 144, color: "#10B981" },
              { name: "Logistics", angle: 216, color: "#F59E0B" },
              { name: "Compliance", angle: 288, color: "#06B6D4" },
            ].map((agent) => {
              const rad = (agent.angle * Math.PI) / 180;
              const x = 50 + 38 * Math.cos(rad);
              const y = 50 + 38 * Math.sin(rad);
              return (
                <div
                  key={agent.name}
                  className="absolute -translate-x-1/2 -translate-y-1/2 flex flex-col items-center gap-1"
                  style={{ left: `${x}%`, top: `${y}%` }}
                >
                  <div
                    className="w-8 h-8 rounded-full flex items-center justify-center text-[10px] font-bold text-haven-bg animate-pulse-glow"
                    style={{ backgroundColor: agent.color }}
                  >
                    {agent.name[0]}
                  </div>
                  <span className="text-[10px] text-haven-muted">{agent.name}</span>
                </div>
              );
            })}
            <svg className="absolute inset-0 w-full h-full" style={{ zIndex: 0 }}>
              {[0, 72, 144, 216, 288].map((angle) => {
                const rad = (angle * Math.PI) / 180;
                const x = 50 + 38 * Math.cos(rad);
                const y = 50 + 38 * Math.sin(rad);
                return (
                  <line key={angle} x1="50%" y1="50%" x2={`${x}%`} y2={`${y}%`} stroke="#1F1F23" strokeWidth="1" strokeDasharray="4 4" />
                );
              })}
            </svg>
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="lg:col-span-2 bg-haven-elevated border border-haven-border rounded-card"
        >
          <div className="flex items-center justify-between px-5 py-4 border-b border-haven-border">
            <h3 className="text-sm font-medium">Live Activity</h3>
            <span className="flex items-center gap-1.5 text-xs text-haven-muted">
              <span className="w-2 h-2 rounded-full bg-haven-green animate-pulse" />
              Live
            </span>
          </div>
          <div className="divide-y divide-haven-border">
            {recentEvents.length === 0 ? (
              <div className="px-5 py-8 text-center text-haven-muted text-sm">
                No events yet. Submit a donation or volunteer inquiry to get started.
              </div>
            ) : (
              recentEvents.map((event, i) => (
                <motion.div
                  key={event.id}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.5 + i * 0.05 }}
                  className="flex items-start gap-4 px-5 py-4 hover:bg-haven-surface/50 transition-colors"
                >
                  <div className={`px-2 py-1 rounded text-[10px] font-medium ${agentColors[event.source] || "bg-haven-border text-haven-muted"}`}>
                    {event.agentLabel}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm leading-relaxed">{event.summary}</p>
                    <span className="text-xs text-haven-muted">{event.time}</span>
                  </div>
                  <span className={`px-2 py-0.5 rounded text-[10px] font-medium ${statusColors[event.urgency] || statusColors[event.source] || "bg-haven-border text-haven-muted"}`}>
                    {event.urgency}
                  </span>
                </motion.div>
              ))
            )}
          </div>
        </motion.div>
      </div>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.5 }}
        className="grid grid-cols-2 md:grid-cols-4 gap-4"
      >
        {[
          { label: "Log Donation", icon: Package, href: "/app/donations", color: "text-rose-400" },
          { label: "View Shifts", icon: Users, href: "/app/volunteers", color: "text-violet-400" },
          { label: "Find Resources", icon: Globe, href: "/app/recipients", color: "text-haven-green" },
          { label: "Run Report", icon: TrendingUp, href: "/app/compliance", color: "text-haven-cyan" },
        ].map((action) => {
          const Icon = action.icon;
          return (
            <a
              key={action.label}
              href={action.href}
              className="flex items-center gap-3 bg-haven-elevated border border-haven-border rounded-card p-4 hover:border-haven-green/20 transition-all group"
            >
              <Icon className={`w-5 h-5 ${action.color}`} />
              <span className="text-sm font-medium">{action.label}</span>
              <ArrowUpRight className="w-3 h-3 text-haven-muted opacity-0 group-hover:opacity-100 transition-opacity ml-auto" />
            </a>
          );
        })}
      </motion.div>
    </div>
  );
}
