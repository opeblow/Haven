"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Globe, Phone, Languages, MapPin, Clock, CheckCircle2, Loader2, AlertCircle } from "lucide-react";
import { fetchRecipientRequests, type RecipientRequest } from "@/lib/api";

const statusColors: Record<string, string> = {
  resolved: "bg-haven-green/20 text-haven-green",
  processing: "bg-haven-amber/20 text-haven-amber",
  escalated: "bg-rose-500/20 text-rose-400",
};

function timeAgo(iso: string): string {
  try {
    const diff = Date.now() - new Date(iso).getTime();
    const mins = Math.floor(diff / 60000);
    if (mins < 1) return "just now";
    if (mins < 60) return `${mins} min ago`;
    const hrs = Math.floor(mins / 60);
    if (hrs < 24) return `${hrs} hr ago`;
    return `${Math.floor(hrs / 24)} day ago`;
  } catch {
    return "";
  }
}

export default function RecipientsPage() {
  const [requests, setRequests] = useState<RecipientRequest[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      try {
        const data = await fetchRecipientRequests();
        setRequests(data.requests);
      } catch (e) {
        setError(e instanceof Error ? e.message : "Failed to load recipient requests");
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
        <span className="ml-3 text-haven-muted">Loading recipients...</span>
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

  const resolvedCount = requests.filter((r) => r.resolved).length;
  const languages = Array.from(new Set(requests.map((r) => r.language)));

  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-2xl font-serif">
          <span className="gradient-text">Recipients</span>
        </h2>
        <p className="text-haven-muted text-sm mt-1">
          Multi-language assistance for people seeking aid. Anonymized for privacy.
        </p>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { label: "Total Inquiries", value: requests.length.toLocaleString(), icon: Globe },
          { label: "Languages", value: languages.length.toString(), icon: Languages },
          { label: "Resolved", value: resolvedCount.toLocaleString(), icon: CheckCircle2 },
          { label: "Pending", value: (requests.length - resolvedCount).toLocaleString(), icon: Clock },
        ].map((stat) => {
          const Icon = stat.icon;
          return (
            <div key={stat.label} className="bg-haven-elevated border border-haven-border rounded-card p-4">
              <div className="flex items-center gap-2 mb-2">
                <Icon className="w-4 h-4 text-haven-cyan" />
                <span className="text-xs text-haven-muted">{stat.label}</span>
              </div>
              <div className="text-xl font-mono font-bold">{stat.value}</div>
            </div>
          );
        })}
      </div>

      <div className="space-y-3">
        <h3 className="text-sm font-medium text-haven-muted">Recent Inquiries ({requests.length})</h3>
        {requests.length === 0 ? (
          <div className="bg-haven-elevated/50 border border-dashed border-haven-border rounded-card p-8 text-center text-haven-muted text-sm">
            No recipient requests yet. They will appear here when people reach out for help.
          </div>
        ) : (
          requests.map((req, i) => (
            <motion.div
              key={req.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.05 }}
              className="bg-haven-elevated border border-haven-border rounded-card p-5"
            >
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-mono text-haven-dim">{req.id.slice(0, 8)}</span>
                  <span className="flex items-center gap-1 text-xs text-haven-muted">
                    <Languages className="w-3 h-3" /> {req.language}
                  </span>
                </div>
                <span className={`px-2 py-0.5 rounded text-[10px] font-medium ${req.resolved ? statusColors.resolved : statusColors.processing}`}>
                  {req.resolved ? "resolved" : "processing"}
                </span>
              </div>

              <div className="bg-haven-surface rounded-lg p-4 mb-3">
                <p className="text-sm italic text-haven-text">"{req.request_text}"</p>
              </div>

              <div className="flex items-center justify-between text-xs text-haven-muted">
                <div className="flex items-center gap-4">
                  <span className="flex items-center gap-1"><Phone className="w-3 h-3" /> {req.phone.slice(0, 7)}***</span>
                  {req.assigned_pantry && (
                    <span className="flex items-center gap-1"><MapPin className="w-3 h-3" /> {req.assigned_pantry}</span>
                  )}
                  {req.household_size > 1 && (
                    <span>Household: {req.household_size}</span>
                  )}
                </div>
                <span>{timeAgo(req.created_at)}</span>
              </div>
            </motion.div>
          ))
        )}
      </div>
    </div>
  );
}
