"use client";

import { motion, useScroll, useTransform } from "framer-motion";
import {
  ArrowRight,
  Heart,
  Users,
  Package,
  Truck,
  Shield,
  Globe,
  ChevronRight,
  Zap,
  MapPin,
  Languages,
} from "lucide-react";
import Link from "next/link";

const stats = [
  { label: "Meals Coordinated", value: "247,832", icon: Package },
  { label: "Active Volunteers", value: "1,847", icon: Users },
  { label: "Partner Pantries", value: "23", icon: MapPin },
  { label: "Languages Supported", value: "8", icon: Languages },
];

const agents = [
  {
    name: "Donor Agent",
    description: "Receives donation offers via SMS, email, or voice. Assesses freshness, negotiates pickup times, and generates tax receipts.",
    icon: Heart,
    color: "from-rose-500/20 to-pink-500/20",
    accent: "#F43F5E",
  },
  {
    name: "Volunteer Agent",
    description: "Matches volunteers to shifts using skills, availability, and history. Handles no-shows and sends shift offers via SMS.",
    icon: Users,
    color: "from-violet-500/20 to-purple-500/20",
    accent: "#8B5CF6",
  },
  {
    name: "Recipient Agent",
    description: "Multi-language voice/SMS assistant helping recipients find pantries, hours, eligibility, and alternative resources.",
    icon: Globe,
    color: "from-haven-green/20 to-haven-cyan/20",
    accent: "#10B981",
  },
  {
    name: "Logistics Agent",
    description: "Routes food from donors to distribution points. Respects cold chain constraints and generates driver manifests.",
    icon: Truck,
    color: "from-amber-500/20 to-orange-500/20",
    accent: "#F59E0B",
  },
  {
    name: "Compliance Agent",
    description: "Auto-generates USDA reports, tax receipts, and food safety logs. Maintains immutable audit trails.",
    icon: Shield,
    color: "from-cyan-500/20 to-blue-500/20",
    accent: "#06B6D4",
  },
];

const features = [
  "Multi-agent swarm coordination",
  "Real-time cold chain monitoring",
  "Multi-language voice assistance",
  "Automated USDA compliance",
  "Smart volunteer matching",
  "Human-in-the-loop escalation",
];

function AnimatedCounter({ value, label }: { value: string; label: string }) {
  return (
    <div className="text-center">
      <div className="text-3xl font-bold font-mono gradient-text">{value}</div>
      <div className="text-sm text-haven-muted mt-1">{label}</div>
    </div>
  );
}

function AgentCard({ agent, index }: { agent: typeof agents[0]; index: number }) {
  const Icon = agent.icon;
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      whileInView={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay: index * 0.1 }}
      viewport={{ once: true }}
      whileHover={{ y: -4, transition: { duration: 0.2 } }}
      className="group relative bg-haven-elevated border border-haven-border rounded-card p-6 hover:border-haven-green/30 transition-all duration-300"
    >
      <div
        className={`absolute inset-0 rounded-card bg-gradient-to-br ${agent.color} opacity-0 group-hover:opacity-100 transition-opacity duration-300`}
      />
      <div className="relative">
        <div
          className="w-10 h-10 rounded-lg flex items-center justify-center mb-4"
          style={{ backgroundColor: `${agent.accent}20` }}
        >
          <Icon className="w-5 h-5" style={{ color: agent.accent }} />
        </div>
        <h3 className="text-lg font-semibold mb-2">{agent.name}</h3>
        <p className="text-sm text-haven-muted leading-relaxed">{agent.description}</p>
      </div>
    </motion.div>
  );
}

export default function HomePage() {
  const { scrollYProgress } = useScroll();
  const heroOpacity = useTransform(scrollYProgress, [0, 0.2], [1, 0]);
  const heroScale = useTransform(scrollYProgress, [0, 0.2], [1, 0.95]);

  return (
    <main className="min-h-screen">
      {/* Hero */}
      <motion.section
        style={{ opacity: heroOpacity, scale: heroScale }}
        className="relative min-h-screen flex flex-col items-center justify-center px-6 overflow-hidden"
      >
        {/* Background gradient orbs */}
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-haven-green/5 rounded-full blur-[120px] animate-pulse-glow" />
        <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-haven-cyan/5 rounded-full blur-[120px] animate-pulse-glow" />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-haven-amber/3 rounded-full blur-[150px] animate-float" />

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.2 }}
          className="relative text-center max-w-4xl"
        >
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full border border-haven-border bg-haven-elevated/50 text-sm text-haven-muted mb-8">
            <Zap className="w-4 h-4 text-haven-amber" />
            <span>Built with Strands Agents SDK on AWS</span>
          </div>

          <h1 className="text-6xl md:text-8xl font-serif leading-[0.9] mb-6">
            The agent behind
            <br />
            <span className="gradient-text">every helping hand.</span>
          </h1>

          <p className="text-xl text-haven-muted max-w-2xl mx-auto mb-10 leading-relaxed">
            Haven is the autonomous operations layer for food banks, shelters, and
            mutual aid networks — matching donations, volunteers, and recipients so
            human staff can focus on human work.
          </p>

          <div className="flex items-center gap-4 justify-center">
            <Link
              href="/app"
              className="inline-flex items-center gap-2 px-6 py-3 bg-haven-green text-haven-bg font-semibold rounded-button hover:bg-haven-green/90 transition-colors"
            >
              Open Dashboard
              <ArrowRight className="w-4 h-4" />
            </Link>
            <a
              href="https://github.com/haven-agent/haven"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 px-6 py-3 border border-haven-border rounded-button hover:bg-haven-elevated transition-colors"
            >
              View on GitHub
              <ChevronRight className="w-4 h-4" />
            </a>
          </div>
        </motion.div>

        {/* Stats */}
        <motion.div
          initial={{ opacity: 0, y: 40 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.6 }}
          className="relative grid grid-cols-2 md:grid-cols-4 gap-8 md:gap-16 mt-24 max-w-3xl"
        >
          {stats.map((stat) => (
            <AnimatedCounter key={stat.label} value={stat.value} label={stat.label} />
          ))}
        </motion.div>
      </motion.section>

      {/* Agent Swarm */}
      <section className="py-32 px-6">
        <div className="max-w-6xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-center mb-16"
          >
            <h2 className="text-4xl md:text-5xl font-serif mb-4">
              Five agents. <span className="gradient-text">One mission.</span>
            </h2>
            <p className="text-haven-muted max-w-xl mx-auto">
              A specialized swarm that handles the invisible logistics of community
              aid, coordinated by an intelligent supervisor.
            </p>
          </motion.div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {agents.map((agent, i) => (
              <AgentCard key={agent.name} agent={agent} index={i} />
            ))}
          </div>
        </div>
      </section>

      {/* How it works */}
      <section className="py-32 px-6 bg-haven-elevated/50">
        <div className="max-w-6xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-center mb-16"
          >
            <h2 className="text-4xl md:text-5xl font-serif mb-4">
              From need to <span className="gradient-text">impact.</span>
            </h2>
            <p className="text-haven-muted max-w-xl mx-auto">
              Watch Haven coordinate a real day at a food bank in under three minutes.
            </p>
          </motion.div>

          <div className="grid md:grid-cols-3 gap-8">
            {[
              {
                step: "01",
                title: "A donation arrives",
                desc: "A restaurant texts about leftover catering. The DonorAgent parses the offer, checks cold chain needs, and schedules pickup.",
              },
              {
                step: "02",
                title: "Agents coordinate",
                desc: "LogisticsAgent routes the pickup. VolunteerAgent matches a driver. ComplianceAgent logs the transaction. All in seconds.",
              },
              {
                step: "03",
                title: "Community gets fed",
                desc: "RecipientAgent helps a family in Spanish find the nearest open pantry. The food arrives fresh. Nobody fell through the cracks.",
              },
            ].map((item, i) => (
              <motion.div
                key={item.step}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.15 }}
                viewport={{ once: true }}
                className="relative"
              >
                <div className="text-6xl font-mono font-bold text-haven-border mb-4">
                  {item.step}
                </div>
                <h3 className="text-xl font-semibold mb-2">{item.title}</h3>
                <p className="text-haven-muted leading-relaxed">{item.desc}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Tech Stack */}
      <section className="py-32 px-6">
        <div className="max-w-6xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-center mb-16"
          >
            <h2 className="text-4xl md:text-5xl font-serif mb-4">
              Built to <span className="gradient-text">scale.</span>
            </h2>
            <p className="text-haven-muted max-w-xl mx-auto">
              Every technology choice serves the mission of reliability, scale, and trust.
            </p>
          </motion.div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {features.map((feature, i) => (
              <motion.div
                key={feature}
                initial={{ opacity: 0, scale: 0.95 }}
                whileInView={{ opacity: 1, scale: 1 }}
                transition={{ delay: i * 0.05 }}
                viewport={{ once: true }}
                className="px-4 py-3 bg-haven-elevated border border-haven-border rounded-button text-sm text-center text-haven-muted hover:text-haven-text hover:border-haven-green/30 transition-all"
              >
                {feature}
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-32 px-6">
        <div className="max-w-3xl mx-auto text-center">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
          >
            <h2 className="text-4xl md:text-5xl font-serif mb-6">
              Ready to help?
            </h2>
            <p className="text-haven-muted mb-8 max-w-lg mx-auto">
              Haven is open source. Deploy it for your local food bank. Contribute
              to the codebase. Or just spread the word.
            </p>
            <div className="flex items-center gap-4 justify-center">
              <Link
                href="/app"
                className="inline-flex items-center gap-2 px-6 py-3 bg-haven-green text-haven-bg font-semibold rounded-button hover:bg-haven-green/90 transition-colors"
              >
                Launch Dashboard
                <ArrowRight className="w-4 h-4" />
              </Link>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-haven-border py-12 px-6">
        <div className="max-w-6xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded bg-gradient-to-br from-haven-green to-haven-cyan" />
            <span className="font-semibold">Haven</span>
          </div>
          <div className="text-sm text-haven-muted">
            Open source under Apache 2.0. Built for the AWS Agents for Humans Hackathon.
          </div>
          <div className="flex gap-6 text-sm text-haven-muted">
            <a href="https://github.com/haven-agent/haven" className="hover:text-haven-text transition-colors">GitHub</a>
            <a href="#" className="hover:text-haven-text transition-colors">Docs</a>
            <a href="#" className="hover:text-haven-text transition-colors">Discord</a>
          </div>
        </div>
      </footer>
    </main>
  );
}
