"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { clsx } from "clsx";
import {
  LayoutDashboard,
  Bot,
  Package,
  Users,
  Globe,
  Shield,
  Settings,
  ChevronLeft,
  ChevronRight,
  Search,
} from "lucide-react";
import { useState } from "react";

const navItems = [
  { href: "/app", label: "Dashboard", icon: LayoutDashboard },
  { href: "/app/agents", label: "Agent Console", icon: Bot },
  { href: "/app/donations", label: "Donations", icon: Package },
  { href: "/app/volunteers", label: "Volunteers", icon: Users },
  { href: "/app/recipients", label: "Recipients", icon: Globe },
  { href: "/app/compliance", label: "Compliance", icon: Shield },
  { href: "/app/settings", label: "Settings", icon: Settings },
];

export default function AppLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const [collapsed, setCollapsed] = useState(false);

  return (
    <div className="flex h-screen overflow-hidden">
      {/* Sidebar */}
      <aside
        className={clsx(
          "flex flex-col border-r border-haven-border bg-haven-elevated transition-all duration-300",
          collapsed ? "w-16" : "w-60"
        )}
      >
        <div className="flex items-center gap-2 px-4 h-14 border-b border-haven-border">
          <div className="w-6 h-6 rounded bg-gradient-to-br from-haven-green to-haven-cyan shrink-0" />
          {!collapsed && <span className="font-semibold text-sm">Haven</span>}
        </div>

        <nav className="flex-1 py-3 px-2 space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            const active = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={clsx(
                  "flex items-center gap-3 px-3 py-2 rounded-button text-sm transition-all",
                  active
                    ? "bg-haven-green/10 text-haven-green"
                    : "text-haven-muted hover:text-haven-text hover:bg-haven-border/50"
                )}
              >
                <Icon className="w-4 h-4 shrink-0" />
                {!collapsed && <span>{item.label}</span>}
              </Link>
            );
          })}
        </nav>

        <button
          onClick={() => setCollapsed(!collapsed)}
          className="flex items-center justify-center h-10 border-t border-haven-border text-haven-muted hover:text-haven-text transition-colors"
        >
          {collapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
        </button>
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-y-auto">
        {/* Top bar */}
        <header className="sticky top-0 z-10 flex items-center justify-between h-14 px-6 border-b border-haven-border bg-haven-bg/80 backdrop-blur-md">
          <div className="flex items-center gap-4">
            <h1 className="text-sm font-medium">
              {navItems.find((i) => i.href === pathname)?.label || "Haven"}
            </h1>
          </div>
          <div className="flex items-center gap-4">
            <button className="flex items-center gap-2 px-3 py-1.5 bg-haven-elevated border border-haven-border rounded-button text-sm text-haven-muted hover:text-haven-text transition-colors">
              <Search className="w-3.5 h-3.5" />
              <span className="hidden md:inline">Search...</span>
              <kbd className="text-[10px] bg-haven-border px-1.5 py-0.5 rounded">⌘K</kbd>
            </button>
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-haven-green to-haven-cyan" />
          </div>
        </header>

        <div className="p-6">{children}</div>
      </main>
    </div>
  );
}
