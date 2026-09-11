const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface Donation {
  id: string;
  donor_name: string;
  donor_phone: string;
  donor_email?: string;
  description: string;
  quantity: string;
  category: string;
  requires_refrigeration: boolean;
  address: string;
  latitude?: number;
  longitude?: number;
  status: string;
  notes?: string;
  created_at: string;
  updated_at?: string;
}

export interface Volunteer {
  id: string;
  name: string;
  phone: string;
  email: string;
  skills: string[];
  languages: string[];
  has_vehicle?: boolean;
  max_distance_miles?: number;
  availability?: string[];
  total_shifts_completed: number;
  no_shows: number;
  rating: number;
  status: string;
  created_at: string;
}

export interface Shift {
  id: string;
  pantry_id: string;
  pantry_name: string;
  role: string;
  start_time: string;
  end_time: string;
  volunteers_needed: number;
  volunteers_assigned: string[];
  status: string;
  requirements?: string[];
  created_at: string;
}

export interface RecipientRequest {
  id: string;
  phone: string;
  language: string;
  request_text: string;
  category?: string;
  household_size: number;
  dietary_restrictions?: string[];
  address?: string;
  latitude?: number;
  longitude?: number;
  resolved: boolean;
  assigned_pantry?: string;
  notes?: string;
  created_at: string;
}

export interface AgentEvent {
  id: string;
  event_type: string;
  source: string;
  payload: Record<string, unknown>;
  urgency: string;
  requires_human?: boolean;
  processed_by?: string[];
  created_at: string;
}

export interface AuditEntry {
  action: string;
  agent: string;
  entity_type: string;
  entity_id: string;
  details: Record<string, unknown>;
  timestamp: string;
}

export interface DashboardStats {
  total_donations: number;
  donations_by_status: Record<string, number>;
  total_lbs_distributed: number;
  active_volunteers: number;
  total_volunteers: number;
  open_shifts: number;
  total_shifts: number;
  total_recipient_requests: number;
  resolved_requests: number;
}

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`API error ${res.status}: ${body}`);
  }
  return res.json();
}

// ── Donations ──────────────────────────────────────────────────────────

export async function fetchDonations(status?: string): Promise<{ donations: Donation[]; total: number }> {
  const params = status ? `?status=${status}` : "";
  return apiFetch(`/api/donations${params}`);
}

export async function fetchDonation(id: string): Promise<Donation> {
  return apiFetch(`/api/donations/${id}`);
}

export async function submitDonationOffer(data: {
  donor_name: string;
  donor_phone: string;
  description: string;
  quantity: string;
  category?: string;
  requires_refrigeration?: boolean;
  address?: string;
}): Promise<{ success: boolean; result: Record<string, unknown> }> {
  return apiFetch("/api/donations/offer", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

// ── Volunteers ─────────────────────────────────────────────────────────

export async function fetchVolunteers(status?: string): Promise<{ volunteers: Volunteer[]; total: number }> {
  const params = status ? `?status=${status}` : "";
  return apiFetch(`/api/volunteers${params}`);
}

export async function submitVolunteerInquiry(data: {
  name: string;
  phone: string;
  email?: string;
  skills?: string[];
  languages?: string[];
}): Promise<{ success: boolean; result: Record<string, unknown>; volunteer_id: string }> {
  return apiFetch("/api/volunteers/inquiry", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

// ── Shifts ─────────────────────────────────────────────────────────────

export async function fetchShifts(status?: string): Promise<{ shifts: Shift[]; total: number }> {
  const params = status ? `?status=${status}` : "";
  return apiFetch(`/api/shifts${params}`);
}

// ── Recipients ─────────────────────────────────────────────────────────

export async function fetchRecipientRequests(resolved?: boolean): Promise<{ requests: RecipientRequest[]; total: number }> {
  const params = resolved !== undefined ? `?resolved=${resolved}` : "";
  return apiFetch(`/api/recipients${params}`);
}

export async function submitRecipientRequest(data: {
  phone: string;
  request_text: string;
  language?: string;
  latitude?: number;
  longitude?: number;
  household_size?: number;
}): Promise<{ success: boolean; result: Record<string, unknown> }> {
  return apiFetch("/api/recipients/request", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

// ── Events ─────────────────────────────────────────────────────────────

export async function fetchEventFeed(limit?: number): Promise<{ events: AgentEvent[]; total: number }> {
  const params = limit ? `?limit=${limit}` : "";
  return apiFetch(`/api/events/feed${params}`);
}

// ── Stats ──────────────────────────────────────────────────────────────

export async function fetchDashboardStats(): Promise<DashboardStats> {
  return apiFetch("/api/stats");
}

// ── Audit ──────────────────────────────────────────────────────────────

export async function fetchAuditLog(limit?: number): Promise<{ entries: AuditEntry[]; total: number }> {
  const params = limit ? `?limit=${limit}` : "";
  return apiFetch(`/api/audit${params}`);
}

// ── Health ─────────────────────────────────────────────────────────────

export async function fetchHealth(): Promise<Record<string, unknown>> {
  return apiFetch("/api/health");
}
