"use client";

import { motion } from "framer-motion";
import { Settings as SettingsIcon, Bell, Shield, Plug, Bot } from "lucide-react";

const settingsSections = [
  {
    title: "Organization",
    icon: SettingsIcon,
    fields: [
      { label: "Organization Name", value: "Downtown Community Pantry", type: "text" },
      { label: "EIN", value: "XX-XXXXXXX", type: "text" },
      { label: "Primary Contact", value: "admin@downtownpantry.org", type: "email" },
      { label: "Phone", value: "555-0100", type: "tel" },
    ],
  },
  {
    title: "Agent Preferences",
    icon: Bot,
    fields: [
      { label: "Reasoning Model", value: "Claude Sonnet 4.5", type: "select" },
      { label: "Routing Model", value: "Nova Micro", type: "select" },
      { label: "Max Response Length", value: "500 tokens", type: "select" },
      { label: "Auto-Escalation", value: "Enabled", type: "select" },
    ],
  },
  {
    title: "Escalation Rules",
    icon: Bell,
    fields: [
      { label: "Donation Threshold", value: "$5,000", type: "text" },
      { label: "Slack Webhook", value: "Configured", type: "text" },
      { label: "Escalation SMS", value: "+1-555-0199", type: "tel" },
      { label: "Response SLA", value: "15 minutes", type: "select" },
    ],
  },
  {
    title: "Integrations",
    icon: Plug,
    fields: [
      { label: "Twilio", value: "Connected", type: "text" },
      { label: "Amazon Bedrock", value: "Connected", type: "text" },
      { label: "Langfuse", value: "Connected", type: "text" },
      { label: "Google Maps", value: "Connected", type: "text" },
    ],
  },
];

export default function SettingsPage() {
  return (
    <div className="space-y-8 max-w-3xl">
      <div>
        <h2 className="text-2xl font-serif">
          <span className="gradient-text">Settings</span>
        </h2>
        <p className="text-haven-muted text-sm mt-1">
          Configure your Haven instance and agent preferences.
        </p>
      </div>

      {settingsSections.map((section, i) => {
        const Icon = section.icon;
        return (
          <motion.div
            key={section.title}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.1 }}
            className="bg-haven-elevated border border-haven-border rounded-card"
          >
            <div className="flex items-center gap-3 px-5 py-4 border-b border-haven-border">
              <Icon className="w-4 h-4 text-haven-cyan" />
              <h3 className="text-sm font-medium">{section.title}</h3>
            </div>
            <div className="p-5 space-y-4">
              {section.fields.map((field) => (
                <div key={field.label} className="flex flex-col gap-1.5">
                  <label className="text-xs text-haven-muted">{field.label}</label>
                  <input
                    type={field.type === "select" ? "text" : field.type}
                    defaultValue={field.value}
                    disabled
                    className="bg-haven-surface border border-haven-border rounded-button px-3 py-2 text-sm text-haven-text placeholder:text-haven-dim focus:outline-none focus:ring-1 focus:ring-haven-green/50 focus:border-haven-green/50 disabled:opacity-50"
                  />
                </div>
              ))}
            </div>
          </motion.div>
        );
      })}

      <div className="flex items-center gap-3 p-4 bg-haven-amber/5 border border-haven-amber/20 rounded-card">
        <Shield className="w-4 h-4 text-haven-amber shrink-0" />
        <p className="text-xs text-haven-muted">
          Settings are managed through environment variables in production. 
          This panel is for demonstration purposes.
        </p>
      </div>
    </div>
  );
}
