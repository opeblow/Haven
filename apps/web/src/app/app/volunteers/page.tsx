"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Users, Star, Clock, Loader2, AlertCircle, Plus } from "lucide-react";
import { fetchVolunteers, fetchShifts, submitVolunteerInquiry, type Volunteer, type Shift } from "@/lib/api";

const statusColors: Record<string, string> = {
  available: "bg-haven-green/20 text-haven-green",
  on_shift: "bg-haven-cyan/20 text-haven-cyan",
  matched: "bg-haven-amber/20 text-haven-amber",
  completed: "bg-violet-500/20 text-violet-400",
  no_show: "bg-rose-500/20 text-rose-400",
};

export default function VolunteersPage() {
  const [volunteers, setVolunteers] = useState<Volunteer[]>([]);
  const [shifts, setShifts] = useState<Shift[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [form, setForm] = useState({ name: "", phone: "", email: "", skills: "" });

  async function load() {
    try {
      const [vData, sData] = await Promise.all([fetchVolunteers(), fetchShifts()]);
      setVolunteers(vData.volunteers);
      setShifts(sData.shifts);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load volunteers");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); }, []);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    try {
      await submitVolunteerInquiry({
        name: form.name,
        phone: form.phone,
        email: form.email,
        skills: form.skills.split(",").map((s) => s.trim()).filter(Boolean),
      });
      setShowForm(false);
      setForm({ name: "", phone: "", email: "", skills: "" });
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
        <span className="ml-3 text-haven-muted">Loading volunteers...</span>
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
            <span className="gradient-text">Volunteers</span>
          </h2>
          <p className="text-haven-muted text-sm mt-1">
            Manage volunteer roster, shifts, and intelligent matching.
          </p>
        </div>
        <button
          onClick={() => setShowForm(!showForm)}
          className="flex items-center gap-2 px-4 py-2 bg-haven-green text-haven-bg rounded-button text-sm font-medium hover:bg-haven-green/90 transition-colors"
        >
          <Plus className="w-4 h-4" />
          Add Volunteer
        </button>
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
              <label className="text-xs text-haven-muted block mb-1">Name</label>
              <input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required className="w-full bg-haven-surface border border-haven-border rounded-button px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-haven-green/50" />
            </div>
            <div>
              <label className="text-xs text-haven-muted block mb-1">Phone</label>
              <input value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} required className="w-full bg-haven-surface border border-haven-border rounded-button px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-haven-green/50" />
            </div>
            <div>
              <label className="text-xs text-haven-muted block mb-1">Email</label>
              <input value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} className="w-full bg-haven-surface border border-haven-border rounded-button px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-haven-green/50" />
            </div>
            <div>
              <label className="text-xs text-haven-muted block mb-1">Skills (comma-separated)</label>
              <input value={form.skills} onChange={(e) => setForm({ ...form, skills: e.target.value })} placeholder="driving, food_sorting, customer_service" className="w-full bg-haven-surface border border-haven-border rounded-button px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-haven-green/50" />
            </div>
          </div>
          <div className="flex gap-3">
            <button type="submit" disabled={submitting} className="px-4 py-2 bg-haven-green text-haven-bg rounded-button text-sm font-medium hover:bg-haven-green/90 transition-colors disabled:opacity-50">
              {submitting ? "Adding..." : "Add Volunteer"}
            </button>
            <button type="button" onClick={() => setShowForm(false)} className="px-4 py-2 border border-haven-border rounded-button text-sm text-haven-muted hover:text-haven-text transition-colors">
              Cancel
            </button>
          </div>
        </motion.form>
      )}

      <div className="grid lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-3">
          <h3 className="text-sm font-medium text-haven-muted">Volunteer Roster ({volunteers.length})</h3>
          {volunteers.length === 0 ? (
            <div className="bg-haven-elevated/50 border border-dashed border-haven-border rounded-card p-8 text-center text-haven-muted text-sm">
              No volunteers yet. Add one to get started.
            </div>
          ) : (
            volunteers.map((vol, i) => (
              <motion.div
                key={vol.id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.05 }}
                className="bg-haven-elevated border border-haven-border rounded-card p-4 hover:border-haven-green/20 transition-all"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-full bg-gradient-to-br from-haven-green/30 to-haven-cyan/30 flex items-center justify-center text-sm font-bold">
                      {vol.name.split(" ").map((n) => n[0]).join("")}
                    </div>
                    <div>
                      <p className="text-sm font-medium">{vol.name}</p>
                      <div className="flex items-center gap-2 mt-0.5">
                        {vol.skills.map((s) => (
                          <span key={s} className="text-[10px] px-1.5 py-0.5 bg-haven-surface rounded text-haven-muted">{s.replace(/_/g, " ")}</span>
                        ))}
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-6 text-right">
                    <div>
                      <div className="text-lg font-mono font-bold">{vol.total_shifts_completed}</div>
                      <div className="text-[10px] text-haven-muted">shifts</div>
                    </div>
                    <div>
                      <div className="flex items-center gap-1 text-haven-amber">
                        <Star className="w-3 h-3 fill-current" />
                        <span className="text-sm font-mono font-bold">{vol.rating}</span>
                      </div>
                    </div>
                    <span className={`px-2 py-0.5 rounded text-[10px] font-medium ${statusColors[vol.status] || "bg-haven-border text-haven-muted"}`}>
                      {vol.status.replace(/_/g, " ")}
                    </span>
                  </div>
                </div>
              </motion.div>
            ))
          )}
        </div>

        <div className="space-y-3">
          <h3 className="text-sm font-medium text-haven-muted">Open Shifts ({shifts.filter((s) => s.status === "open").length})</h3>
          {shifts.filter((s) => s.status === "open").length === 0 ? (
            <div className="bg-haven-elevated/50 border border-dashed border-haven-border rounded-card p-8 text-center text-haven-muted text-sm">
              No open shifts.
            </div>
          ) : (
            shifts.filter((s) => s.status === "open").map((shift, i) => (
              <motion.div
                key={shift.id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.05 }}
                className="bg-haven-elevated border border-haven-border rounded-card p-4"
              >
                <div className="flex items-start justify-between mb-2">
                  <span className="text-xs font-mono text-haven-dim">{shift.id.slice(0, 8)}</span>
                  <span className={`text-[10px] px-2 py-0.5 rounded font-medium ${
                    shift.volunteers_assigned.length === 0 ? "bg-rose-500/20 text-rose-400" :
                    shift.volunteers_assigned.length < shift.volunteers_needed ? "bg-haven-amber/20 text-haven-amber" :
                    "bg-haven-green/20 text-haven-green"
                  }`}>
                    {shift.volunteers_assigned.length}/{shift.volunteers_needed} filled
                  </span>
                </div>
                <p className="text-sm font-medium">{shift.pantry_name}</p>
                <div className="flex items-center gap-3 mt-2 text-xs text-haven-muted">
                  <span className="flex items-center gap-1"><Clock className="w-3 h-3" /> {new Date(shift.start_time).toLocaleDateString()}</span>
                </div>
                <p className="text-[10px] text-haven-dim mt-1">Role: {shift.role.replace(/_/g, " ")}</p>
              </motion.div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
