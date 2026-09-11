"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Package, ChevronRight, Clock, Thermometer, MapPin, Loader2, AlertCircle, Plus } from "lucide-react";
import { fetchDonations, submitDonationOffer, type Donation } from "@/lib/api";

const columns = [
  { key: "offered" as const, label: "Incoming", color: "text-haven-amber" },
  { key: "accepted" as const, label: "Accepted", color: "text-haven-green" },
  { key: "in_transit" as const, label: "In Transit", color: "text-haven-cyan" },
  { key: "distributed" as const, label: "Distributed", color: "text-violet-400" },
];

const categoryColors: Record<string, string> = {
  produce: "bg-haven-green/20 text-haven-green",
  dairy: "bg-blue-500/20 text-blue-400",
  protein: "bg-rose-500/20 text-rose-400",
  bakery: "bg-amber-500/20 text-amber-400",
  canned: "bg-haven-cyan/20 text-haven-cyan",
  other: "bg-haven-border text-haven-muted",
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

export default function DonationsPage() {
  const [donations, setDonations] = useState<Donation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [form, setForm] = useState({ donor_name: "", donor_phone: "", description: "", quantity: "", category: "other", requires_refrigeration: false, address: "" });

  async function load() {
    try {
      const data = await fetchDonations();
      setDonations(data.donations);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load donations");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); }, []);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    try {
      await submitDonationOffer(form);
      setShowForm(false);
      setForm({ donor_name: "", donor_phone: "", description: "", quantity: "", category: "other", requires_refrigeration: false, address: "" });
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to submit");
    } finally {
      setSubmitting(false);
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-6 h-6 text-haven-green animate-spin" />
        <span className="ml-3 text-haven-muted">Loading donations...</span>
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

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-serif">
            <span className="gradient-text">Donations</span>
          </h2>
          <p className="text-haven-muted text-sm mt-1">
            Track donation offers from intake through distribution.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <div className="text-sm font-mono text-haven-muted">
            {donations.length} total
          </div>
          <button
            onClick={() => setShowForm(!showForm)}
            className="flex items-center gap-2 px-4 py-2 bg-haven-green text-haven-bg rounded-button text-sm font-medium hover:bg-haven-green/90 transition-colors"
          >
            <Plus className="w-4 h-4" />
            New Donation
          </button>
        </div>
      </div>

      {showForm && (
        <motion.form
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          onSubmit={handleSubmit}
          className="bg-haven-elevated border border-haven-border rounded-card p-5 space-y-4"
        >
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-xs text-haven-muted block mb-1">Donor Name</label>
              <input value={form.donor_name} onChange={(e) => setForm({ ...form, donor_name: e.target.value })} required className="w-full bg-haven-surface border border-haven-border rounded-button px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-haven-green/50" />
            </div>
            <div>
              <label className="text-xs text-haven-muted block mb-1">Phone</label>
              <input value={form.donor_phone} onChange={(e) => setForm({ ...form, donor_phone: e.target.value })} required className="w-full bg-haven-surface border border-haven-border rounded-button px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-haven-green/50" />
            </div>
            <div>
              <label className="text-xs text-haven-muted block mb-1">Description</label>
              <input value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} required className="w-full bg-haven-surface border border-haven-border rounded-button px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-haven-green/50" />
            </div>
            <div>
              <label className="text-xs text-haven-muted block mb-1">Quantity</label>
              <input value={form.quantity} onChange={(e) => setForm({ ...form, quantity: e.target.value })} required className="w-full bg-haven-surface border border-haven-border rounded-button px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-haven-green/50" />
            </div>
            <div>
              <label className="text-xs text-haven-muted block mb-1">Category</label>
              <select value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value })} className="w-full bg-haven-surface border border-haven-border rounded-button px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-haven-green/50">
                <option value="produce">Produce</option>
                <option value="dairy">Dairy</option>
                <option value="protein">Protein</option>
                <option value="bakery">Bakery</option>
                <option value="canned">Canned</option>
                <option value="other">Other</option>
              </select>
            </div>
            <div>
              <label className="text-xs text-haven-muted block mb-1">Address</label>
              <input value={form.address} onChange={(e) => setForm({ ...form, address: e.target.value })} className="w-full bg-haven-surface border border-haven-border rounded-button px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-haven-green/50" />
            </div>
          </div>
          <div className="flex items-center gap-2">
            <input type="checkbox" checked={form.requires_refrigeration} onChange={(e) => setForm({ ...form, requires_refrigeration: e.target.checked })} className="rounded" />
            <label className="text-sm text-haven-muted">Requires refrigeration</label>
          </div>
          <div className="flex gap-3">
            <button type="submit" disabled={submitting} className="px-4 py-2 bg-haven-green text-haven-bg rounded-button text-sm font-medium hover:bg-haven-green/90 transition-colors disabled:opacity-50">
              {submitting ? "Submitting..." : "Submit Donation"}
            </button>
            <button type="button" onClick={() => setShowForm(false)} className="px-4 py-2 border border-haven-border rounded-button text-sm text-haven-muted hover:text-haven-text transition-colors">
              Cancel
            </button>
          </div>
        </motion.form>
      )}

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {columns.map((col) => {
          const items = donations.filter((d) => d.status === col.key);
          return (
            <div key={col.key} className="space-y-3">
              <div className="flex items-center gap-2 px-1">
                <span className={`text-sm font-medium ${col.color}`}>{col.label}</span>
                <span className="text-xs text-haven-dim font-mono">{items.length}</span>
              </div>
              {items.length === 0 && (
                <div className="bg-haven-elevated/50 border border-dashed border-haven-border rounded-card p-4 text-center text-xs text-haven-dim">
                  No donations
                </div>
              )}
              {items.map((donation, i) => (
                <motion.div
                  key={donation.id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.05 }}
                  className="bg-haven-elevated border border-haven-border rounded-card p-4 hover:border-haven-green/20 transition-all cursor-pointer group"
                >
                  <div className="flex items-start justify-between mb-2">
                    <span className="text-xs font-mono text-haven-dim">{donation.id.slice(0, 8)}</span>
                    <ChevronRight className="w-3 h-3 text-haven-dim opacity-0 group-hover:opacity-100 transition-opacity" />
                  </div>
                  <p className="text-sm font-medium mb-1">{donation.donor_name}</p>
                  <p className="text-xs text-haven-muted mb-3">{donation.description}</p>
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className={`px-2 py-0.5 rounded text-[10px] font-medium ${categoryColors[donation.category] || categoryColors.other}`}>
                      {donation.category}
                    </span>
                    <span className="text-[10px] text-haven-dim font-mono">{donation.quantity}</span>
                    {donation.requires_refrigeration && <Thermometer className="w-3 h-3 text-haven-cyan" />}
                  </div>
                  <div className="flex items-center gap-3 mt-3 text-[10px] text-haven-dim">
                    <span className="flex items-center gap-1">
                      <Clock className="w-3 h-3" /> {timeAgo(donation.created_at)}
                    </span>
                    {donation.address && (
                      <span className="flex items-center gap-1">
                        <MapPin className="w-3 h-3" /> {donation.address}
                      </span>
                    )}
                  </div>
                </motion.div>
              ))}
            </div>
          );
        })}
      </div>
    </div>
  );
}
