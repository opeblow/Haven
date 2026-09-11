"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Shield, FileText, AlertTriangle, CheckCircle2, Clock, Loader2, AlertCircle } from "lucide-react";
import { fetchAuditLog, fetchDashboardStats, type AuditEntry, type DashboardStats } from "@/lib/api";

const agentColors: Record<string, string> = {
  donor: "text-rose-400",
  volunteer: "text-violet-400",
  recipient: "text-haven-green",
  logistics: "text-haven-amber",
  compliance: "text-haven-cyan",
};

export default function CompliancePage() {
  const [entries, setEntries] = useState<AuditEntry[]>([]);
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      try {
        const [auditData, statsData] = await Promise.all([
          fetchAuditLog(20),
          fetchDashboardStats(),
        ]);
        setEntries(auditData.entries);
        setStats(statsData);
      } catch (e) {
        setError(e instanceof Error ? e.message : "Failed to load compliance data");
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
        <span className="ml-3 text-haven-muted">Loading compliance data...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-64">
        <AlertCircle className="w-6 h-6 text-rose-400" />
        <span className="ml-3 text-haven-muted">{error}</span>
      </div>
    );
  }

  const summaryCards = [
    {
      type: "Donations Tracked",
      period: "All time",
      status: "completed" as const,
      generated: "",
      metrics: {
        total: stats?.total_donations || 0,
        lbs: stats?.total_lbs_distributed || 0,
        open_shifts: stats?.open_shifts || 0,
      },
    },
    {
      type: "Volunteer Activity",
      period: "All time",
      status: "completed" as const,
      generated: "",
      metrics: {
        active: stats?.active_volunteers || 0,
        total: stats?.total_volunteers || 0,
        shifts: stats?.total_shifts || 0,
      },
    },
    {
      type: "Recipient Requests",
      period: "All time",
      status: "completed" as const,
      generated: "",
      metrics: {
        total: stats?.total_recipient_requests || 0,
        resolved: stats?.resolved_requests || 0,
        pending: (stats?.total_recipient_requests || 0) - (stats?.resolved_requests || 0),
      },
    },
  ];

  const statusIcons = {
    completed: <CheckCircle2 className="w-4 h-4 text-haven-green" />,
    in_progress: <Clock className="w-4 h-4 text-haven-amber" />,
  };

  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-2xl font-serif">
          <span className="gradient-text">Compliance</span>
        </h2>
        <p className="text-haven-muted text-sm mt-1">
          Automated reports, audit trails, and regulatory compliance.
        </p>
      </div>

      <div className="space-y-3">
        <h3 className="text-sm font-medium text-haven-muted">System Summary</h3>
        <div className="grid md:grid-cols-3 gap-4">
          {summaryCards.map((card, i) => (
            <motion.div
              key={card.type}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.05 }}
              className="bg-haven-elevated border border-haven-border rounded-card p-5"
            >
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-2">
                  <FileText className="w-4 h-4 text-haven-cyan" />
                  <span className="text-sm font-medium">{card.type}</span>
                </div>
                {statusIcons[card.status]}
              </div>
              <p className="text-xs text-haven-muted mb-3">{card.period}</p>
              <div className="grid grid-cols-3 gap-2">
                {Object.entries(card.metrics).map(([key, value]) => (
                  <div key={key} className="bg-haven-surface rounded p-2">
                    <div className="text-xs font-mono font-bold">{typeof value === "number" ? value.toLocaleString() : value}</div>
                    <div className="text-[10px] text-haven-dim">{key.replace(/_/g, " ")}</div>
                  </div>
                ))}
              </div>
            </motion.div>
          ))}
        </div>
      </div>

      <div className="space-y-3">
        <h3 className="text-sm font-medium text-haven-muted">Immutable Audit Trail ({entries.length})</h3>
        <div className="bg-haven-elevated border border-haven-border rounded-card overflow-hidden">
          <div className="grid grid-cols-[80px_90px_1fr_100px_1fr] gap-4 px-5 py-3 border-b border-haven-border text-[10px] font-medium text-haven-dim uppercase tracking-wider">
            <span>Time</span>
            <span>Agent</span>
            <span>Action</span>
            <span>Entity</span>
            <span>Details</span>
          </div>
          {entries.length === 0 ? (
            <div className="px-5 py-8 text-center text-haven-muted text-sm">
              No audit entries yet. Activity will be logged as agents process events.
            </div>
          ) : (
            entries.map((entry, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.03 }}
                className="grid grid-cols-[80px_90px_1fr_100px_1fr] gap-4 px-5 py-3 border-b border-haven-border last:border-0 hover:bg-haven-surface/50 transition-colors text-sm"
              >
                <span className="font-mono text-haven-dim text-xs">
                  {entry.timestamp ? new Date(entry.timestamp).toLocaleTimeString() : ""}
                </span>
                <span className={`text-xs ${agentColors[entry.agent] || "text-haven-muted"}`}>
                  {entry.agent}
                </span>
                <span className="text-xs">{entry.action}</span>
                <span className="font-mono text-xs text-haven-muted">{entry.entity_id.slice(0, 8)}</span>
                <span className="text-haven-muted text-xs truncate">
                  {Object.values(entry.details || {}).slice(0, 2).join(", ")}
                </span>
              </motion.div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
