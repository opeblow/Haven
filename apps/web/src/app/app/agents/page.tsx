"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Bot, Zap, Loader2, AlertCircle } from "lucide-react";
import { fetchHealth } from "@/lib/api";

const agentInfo = [
  {
    name: "Donor Agent",
    model: "Claude Sonnet 4.5",
    tools: ["parse_donation_offer", "check_cold_chain", "accept_donation", "negotiate_pickup", "generate_tax_receipt"],
    color: "#F43F5E",
  },
  {
    name: "Volunteer Agent",
    model: "Claude Sonnet 4.5",
    tools: ["get_open_shifts", "match_volunteer", "send_shift_offer_sms", "handle_no_show", "calculate_volunteer_stats"],
    color: "#8B5CF6",
  },
  {
    name: "Recipient Agent",
    model: "Claude Sonnet 4.5",
    tools: ["find_nearest_pantry", "check_pantry_hours", "verify_eligibility", "list_available_items", "translate_response"],
    color: "#10B981",
  },
  {
    name: "Logistics Agent",
    model: "Claude Sonnet 4.5",
    tools: ["optimize_route", "generate_manifest", "dispatch_driver", "track_cold_chain"],
    color: "#F59E0B",
  },
  {
    name: "Compliance Agent",
    model: "Claude Sonnet 4.5",
    tools: ["generate_usda_report", "log_food_safety_event", "generate_tax_receipt_batch", "audit_trail", "get_audit_log", "get_compliance_summary"],
    color: "#06B6D4",
  },
];

interface HealthData {
  status?: string;
  supervisor?: string;
  agents?: Record<string, { status: string; model: string }>;
  uptime?: string;
}

export default function AgentsPage() {
  const [health, setHealth] = useState<HealthData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      try {
        const data = await fetchHealth();
        setHealth(data as unknown as HealthData);
      } catch (e) {
        setError(e instanceof Error ? e.message : "Failed to fetch agent status");
      } finally {
        setLoading(false);
      }
    }
    load();
    const interval = setInterval(load, 15000);
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-6 h-6 text-haven-green animate-spin" />
        <span className="ml-3 text-haven-muted">Loading agent status...</span>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-2xl font-serif">
          Agent <span className="gradient-text">Console</span>
        </h2>
        <p className="text-haven-muted text-sm mt-1">
          {error
            ? `Error: ${error}`
            : `System status: ${health?.status || "unknown"} | Supervisor: ${health?.supervisor || "unknown"} | Uptime: ${health?.uptime || "unknown"}`}
        </p>
      </div>

      <div className="space-y-4">
        {agentInfo.map((agent, i) => {
          const agentStatus = health?.agents?.[agent.name.toLowerCase().replace(" agent", "").replace(" ", "_")];
          const isActive = agentStatus?.status === "active";

          return (
            <motion.div
              key={agent.name}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.1 }}
              className="bg-haven-elevated border border-haven-border rounded-card overflow-hidden"
            >
              <div className="flex items-center justify-between px-6 py-4 border-b border-haven-border">
                <div className="flex items-center gap-4">
                  <div
                    className="w-10 h-10 rounded-lg flex items-center justify-center"
                    style={{ backgroundColor: `${agent.color}20` }}
                  >
                    <Bot className="w-5 h-5" style={{ color: agent.color }} />
                  </div>
                  <div>
                    <h3 className="font-semibold">{agent.name}</h3>
                    <p className="text-xs text-haven-muted">{agent.model}</p>
                  </div>
                </div>
                <div className="flex items-center gap-6 text-sm">
                  <div className="flex items-center gap-1.5">
                    <span className={`w-2 h-2 rounded-full ${isActive ? "bg-haven-green animate-pulse" : "bg-rose-400"}`} />
                    <span className="text-xs text-haven-muted">{isActive ? "active" : "offline"}</span>
                  </div>
                </div>
              </div>

              <div className="px-6 py-4">
                <h4 className="text-xs font-medium text-haven-muted uppercase tracking-wider mb-3">
                  Tools ({agent.tools.length})
                </h4>
                <div className="flex flex-wrap gap-2">
                  {agent.tools.map((tool) => (
                    <span
                      key={tool}
                      className="px-2 py-1 bg-haven-surface rounded text-xs font-mono text-haven-muted"
                    >
                      {tool}
                    </span>
                  ))}
                </div>
              </div>
            </motion.div>
          );
        })}
      </div>
    </div>
  );
}
