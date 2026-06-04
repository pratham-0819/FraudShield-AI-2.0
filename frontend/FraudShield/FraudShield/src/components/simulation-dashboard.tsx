"use client";

import { motion } from "framer-motion";
import {
  AlertTriangle,
  ArrowRight,
  CheckCircle2,
  Cpu,
  LoaderCircle,
  Radar,
  ShieldAlert,
  Sparkles,
} from "lucide-react";
import { FormEvent, useMemo, useState } from "react";
import {
  Bar,
  BarChart,
  Cell,
  PolarAngleAxis,
  PolarGrid,
  Radar as RadarChartShape,
  RadarChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { SimulationRequest, SimulationResponse } from "@/lib/types";

const initialForm: SimulationRequest = {
  sender: "alex.johnson",
  receiver: "merchant_204",
  amount: 1250,
  age: 30,
  location: "Mumbai",
  device: "Unknown",
  time: "23:15",
  scenario: "Cross-border e-commerce purchase",
  policy_strictness: 6,
};

const statCards = [
  {
    label: "ML + Heuristics",
    value: "Unified engine",
    detail: "Model, heuristics, graph, geo, and behavior signals combined live.",
    icon: Cpu,
  },
  {
    label: "Decision speed",
    value: "One request",
    detail: "Simulate a transaction and get a risk action in a single API call.",
    icon: Radar,
  },
  {
    label: "Explainability",
    value: "Analyst-ready",
    detail: "Flags, score components, and narrative explanations come back together.",
    icon: Sparkles,
  },
];

const featureLabels: Record<string, string> = {
  amt: "Transaction Amount",
  hour: "Transaction Hour",
  age: "Customer Age",
  city_pop: "City Population",
  geo: "Location Risk",
  behavior: "Behavior Pattern",
  device: "Device Trust",
  velocity: "Transaction Velocity",
};

function scoreTone(score: number) {
  if (score >= 70) {
    return {
      label: "Critical",
      color: "text-rose-300",
      ring: "from-rose-500/30 via-rose-400/10 to-transparent",
    };
  }

  if (score >= 35) {
    return {
      label: "Elevated",
      color: "text-amber-300",
      ring: "from-amber-400/30 via-amber-300/10 to-transparent",
    };
  }

  return {
    label: "Contained",
    color: "text-emerald-300",
    ring: "from-emerald-500/30 via-emerald-400/10 to-transparent",
  };
}

function formatPercent(value: number) {
  return `${(value * 100).toFixed(1)}%`;
}

function formatFeatureLabel(value: string) {
  return featureLabels[value] ?? value.replace(/_/g, " ");
}

function actionTone(action: string) {
  if (action === "ALLOW") {
    return {
      icon: CheckCircle2,
      color: "text-emerald-300",
    };
  }

  if (action === "SUSPICIOUS") {
    return {
      icon: AlertTriangle,
      color: "text-amber-300",
    };
  }

  return {
    icon: ShieldAlert,
    color: "text-rose-300",
  };
}

export function SimulationDashboard() {
  const [formData, setFormData] = useState<SimulationRequest>(initialForm);
  const [result, setResult] = useState<SimulationResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const breakdownData = useMemo(
    () =>
      result
        ? Object.entries(result.risk_breakdown).map(([name, value]) => ({
            name: formatFeatureLabel(name),
            value,
          }))
        : [],
    [result],
  );

  const featureData = useMemo(
    () =>
      result
        ? Object.entries(result.advanced_explanation).map(([feature, value]) => ({
            feature: formatFeatureLabel(feature),
            value: Number((value * 100).toFixed(1)),
          }))
        : [],
    [result],
  );

  const xaiData = useMemo(
    () =>
      result
        ? Object.entries(result.xai).map(([signal, status]) => ({
            signal: formatFeatureLabel(signal),
            status,
          }))
        : [],
    [result],
  );

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const response = await fetch("/api/simulate", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          ...formData,
          amount: Number(formData.amount),
          age: Number(formData.age),
          policy_strictness: Number(formData.policy_strictness),
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error ?? "Unable to simulate transaction.");
      }

      setResult(data as SimulationResponse);
    } catch (submissionError) {
      setError(
        submissionError instanceof Error
          ? submissionError.message
          : "Something went wrong while contacting the backend.",
      );
    } finally {
      setLoading(false);
    }
  }

  const tone = result ? scoreTone(result.risk_score) : null;
  const actionStyle = result ? actionTone(result.action) : null;

  return (
    <main className="mx-auto flex min-h-screen w-full max-w-7xl flex-col gap-10 px-4 py-8 sm:px-6 lg:px-8">
      <motion.section
        initial={{ opacity: 0, y: 24 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.55 }}
        className="glass-panel relative overflow-hidden rounded-[32px] px-6 py-8 sm:px-8 lg:px-10"
      >
        <div className="absolute inset-y-0 right-0 w-1/2 bg-[radial-gradient(circle_at_center,_rgba(56,189,248,0.18),_transparent_60%)]" />
        <div className="relative grid gap-10 lg:grid-cols-[1.35fr_0.9fr]">
          <div className="space-y-6">
            <p className="section-label text-xs font-semibold">FraudShield AI Console</p>
            <div className="space-y-4">
              <h1 className="max-w-3xl text-4xl font-semibold tracking-tight text-white sm:text-5xl">
                Turn your backend fraud engine into a live analyst cockpit.
              </h1>
              <p className="max-w-2xl text-sm leading-7 text-slate-300 sm:text-base">
                This Next.js frontend sends transaction simulations to your FastAPI
                backend, then surfaces the decision, fraud probability, explanations,
                and risk contributors in one place.
              </p>
            </div>
            <div className="grid gap-4 md:grid-cols-3">
              {statCards.map(({ label, value, detail, icon: Icon }, index) => (
                <motion.div
                  key={label}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.08 * index, duration: 0.45 }}
                  className="rounded-3xl border border-white/10 bg-white/5 p-4"
                >
                  <Icon className="mb-4 h-5 w-5 text-sky-300" />
                  <p className="text-xs uppercase tracking-[0.24em] text-slate-400">
                    {label}
                  </p>
                  <p className="mt-2 text-xl font-semibold text-white">{value}</p>
                  <p className="mt-2 text-sm leading-6 text-slate-300">{detail}</p>
                </motion.div>
              ))}
            </div>
          </div>

          <div className="rounded-[28px] border border-sky-400/20 bg-slate-950/40 p-6">
            <div className="flex items-center gap-3 text-slate-200">
              <ShieldAlert className="h-5 w-5 text-sky-300" />
              <span className="font-medium">Live decision profile</span>
            </div>
            <div className="mt-8 space-y-5">
              <div className="rounded-3xl border border-white/10 bg-white/5 p-5">
                <p className="text-xs uppercase tracking-[0.24em] text-slate-400">
                  Current policy mode
                </p>
                <p className="mt-3 text-3xl font-semibold text-white">
                  {formData.policy_strictness}/10
                </p>
                <p className="mt-2 text-sm text-slate-300">
                  Threshold shifts dynamically in the backend based on policy
                  strictness.
                </p>
              </div>
              <div className="grid gap-4 sm:grid-cols-2">
                <div className="rounded-3xl border border-white/10 bg-white/5 p-5">
                  <p className="text-xs uppercase tracking-[0.24em] text-slate-400">
                    Device posture
                  </p>
                  <p className="mt-3 text-lg font-medium text-white">{formData.device}</p>
                </div>
                <div className="rounded-3xl border border-white/10 bg-white/5 p-5">
                  <p className="text-xs uppercase tracking-[0.24em] text-slate-400">
                    Scenario window
                  </p>
                  <p className="mt-3 text-lg font-medium text-white">{formData.time}</p>
                </div>
              </div>
              <div className="rounded-3xl border border-dashed border-sky-300/30 bg-sky-400/10 p-5 text-sm leading-6 text-sky-100">
                The API route in this frontend proxies requests to
                <span className="mx-2 rounded-full bg-white/10 px-2 py-1 font-mono text-xs">
                  BACKEND_URL/simulate
                </span>
                so the browser can stay same-origin.
              </div>
            </div>
          </div>
        </div>
      </motion.section>

      <section className="grid gap-10 lg:grid-cols-[1.05fr_0.95fr]">
        <motion.form
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.55, delay: 0.12 }}
          onSubmit={handleSubmit}
          className="glass-panel rounded-[32px] p-6 sm:p-8"
        >
          <div className="flex items-start justify-between gap-4">
            <div>
              <p className="section-label text-xs font-semibold">Simulation input</p>
              <h2 className="mt-3 text-2xl font-semibold text-white">
                Transaction request builder
              </h2>
            </div>
            <div className="rounded-full border border-white/10 bg-white/5 px-3 py-2 font-mono text-xs text-slate-300">
              POST /simulate
            </div>
          </div>

          <div className="mt-8 grid gap-6 sm:grid-cols-2">
            {[
              { name: "sender", label: "Sender", type: "text" },
              { name: "receiver", label: "Receiver", type: "text" },
              { name: "amount", label: "Amount", type: "number", step: "0.01" },
              { name: "age", label: "Customer age", type: "number", step: "1" },
              { name: "location", label: "Location", type: "text" },
              { name: "time", label: "Time", type: "time" },
              { name: "scenario", label: "Scenario", type: "text" },
            ].map((field) => (
              <label key={field.name} className="space-y-2">
                <span className="text-sm font-medium text-slate-200">
                  {field.label}
                </span>
                <input
                  required
                  type={field.type}
                  step={field.step}
                  value={String(formData[field.name as keyof SimulationRequest])}
                  onChange={(event) =>
                    setFormData((current) => ({
                      ...current,
                      [field.name]:
                        field.type === "number"
                          ? Number(event.target.value)
                          : event.target.value,
                    }))
                  }
                  className="w-full rounded-2xl border border-white/10 bg-slate-950/50 px-4 py-3 text-sm text-white outline-none transition focus:border-sky-400/70 focus:ring-2 focus:ring-sky-400/20"
                />
              </label>
            ))}

            <label className="space-y-2">
              <span className="text-sm font-medium text-slate-200">Device posture</span>
              <select
                value={formData.device}
                onChange={(event) =>
                  setFormData((current) => ({
                    ...current,
                    device: event.target.value,
                  }))
                }
                className="w-full rounded-2xl border border-white/10 bg-slate-950/50 px-4 py-3 text-sm text-white outline-none transition focus:border-sky-400/70 focus:ring-2 focus:ring-sky-400/20"
              >
                <option value="Known">Known</option>
                <option value="Unknown">Unknown</option>
                <option value="New mobile">New mobile</option>
                <option value="Shared kiosk">Shared kiosk</option>
              </select>
            </label>

            <label className="space-y-2">
              <span className="flex items-center justify-between text-sm font-medium text-slate-200">
                Policy strictness
                <span className="font-mono text-xs text-sky-200">
                  {formData.policy_strictness}/10
                </span>
              </span>
              <input
                type="range"
                min="1"
                max="10"
                value={formData.policy_strictness}
                onChange={(event) =>
                  setFormData((current) => ({
                    ...current,
                    policy_strictness: Number(event.target.value),
                  }))
                }
                className="h-3 w-full cursor-pointer accent-sky-400"
              />
            </label>
          </div>

          {error ? (
            <div className="mt-6 flex items-start gap-3 rounded-2xl border border-rose-400/30 bg-rose-500/10 p-4 text-sm text-rose-100">
              <AlertTriangle className="mt-0.5 h-5 w-5 shrink-0" />
              <span>{error}</span>
            </div>
          ) : null}

          <div className="mt-8 flex flex-col gap-3 sm:flex-row sm:items-center">
            <button
              type="submit"
              disabled={loading}
              className="inline-flex items-center justify-center gap-2 rounded-full bg-sky-400 px-5 py-3 text-sm font-semibold text-slate-950 transition hover:bg-sky-300 disabled:cursor-not-allowed disabled:opacity-70"
            >
              {loading ? (
                <>
                  <LoaderCircle className="h-4 w-4 animate-spin" />
                  Running simulation
                </>
              ) : (
                <>
                  Simulate transaction
                  <ArrowRight className="h-4 w-4" />
                </>
              )}
            </button>
            <p className="text-sm text-slate-400">
              Default backend target:
              <span className="ml-2 font-mono text-slate-200">http://127.0.0.1:8001</span>
            </p>
          </div>
        </motion.form>

        <motion.section
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.55, delay: 0.18 }}
          className="glass-panel rounded-[32px] p-6 sm:p-8"
        >
          <div className="flex items-start justify-between gap-4">
            <div>
              <p className="section-label text-xs font-semibold">Simulation output</p>
              <h2 className="mt-3 text-2xl font-semibold text-white">
                Risk evaluation dashboard
              </h2>
            </div>
            {result ? (
              <div
                className={`rounded-full border border-white/10 bg-white/5 px-3 py-2 text-xs font-semibold uppercase tracking-[0.22em] ${tone?.color}`}
              >
                {tone?.label}
              </div>
            ) : null}
          </div>

          {!result ? (
            <div className="mt-12 rounded-[28px] border border-dashed border-white/10 bg-slate-950/30 p-8 text-center">
              <Radar className="mx-auto h-10 w-10 text-sky-300" />
              <p className="mt-5 text-lg font-medium text-white">
                Run a transaction simulation to populate the dashboard.
              </p>
              <p className="mt-2 text-sm leading-6 text-slate-400">
                You’ll see the risk score, action, probability, flags, and feature
                importance returned by the backend.
              </p>
            </div>
          ) : (
            <div className="mt-8 space-y-7">
              <div className="grid gap-5 md:grid-cols-4">
                <div
                  className={`relative overflow-hidden rounded-[28px] border border-white/10 bg-gradient-to-br ${tone?.ring} p-5`}
                >
                  <p className="text-xs uppercase tracking-[0.24em] text-slate-400">
                    Risk score
                  </p>
                  <p className="mt-4 text-4xl font-semibold text-white">
                    {result.risk_score}
                  </p>
                </div>
                <div className="rounded-[28px] border border-white/10 bg-white/5 p-5">
                  <p className="text-xs uppercase tracking-[0.24em] text-slate-400">
                    Fraud probability
                  </p>
                  <p className="mt-4 text-4xl font-semibold text-white">
                    {formatPercent(result.fraud_probability)}
                  </p>
                </div>
                <div className="rounded-[28px] border border-white/10 bg-white/5 p-5">
                  <p className="text-xs uppercase tracking-[0.24em] text-slate-400">
                    Model probability
                  </p>
                  <p className="mt-4 text-4xl font-semibold text-white">
                    {formatPercent(result.model_probability ?? result.fraud_probability)}
                  </p>
                </div>
                <div className="rounded-[28px] border border-white/10 bg-white/5 p-5">
                  <p className="text-xs uppercase tracking-[0.24em] text-slate-400">
                    Action
                  </p>
                  <p className="mt-4 flex items-center gap-2 text-xl font-semibold text-white">
                    {actionStyle ? (
                      <actionStyle.icon className={`h-5 w-5 ${actionStyle.color}`} />
                    ) : null}
                    {result.action}
                  </p>
                </div>
              </div>

              <div className="rounded-[28px] border border-white/10 bg-slate-950/35 p-5">
                <p className="text-xs uppercase tracking-[0.24em] text-slate-400">
                  Summary
                </p>
                <p className="mt-3 text-sm leading-7 text-slate-200">{result.summary}</p>
              </div>

              {result.geo_details ? (
                <div className="grid gap-5 lg:grid-cols-4">
                  <div className="rounded-[28px] border border-white/10 bg-slate-950/35 p-5">
                    <p className="text-xs uppercase tracking-[0.24em] text-slate-400">
                      Geo status
                    </p>
                    <p className="mt-3 text-xl font-semibold text-white">
                      {result.geo_details.flag}
                    </p>
                  </div>
                  <div className="rounded-[28px] border border-white/10 bg-slate-950/35 p-5">
                    <p className="text-xs uppercase tracking-[0.24em] text-slate-400">
                      Trusted locations
                    </p>
                    <p className="mt-3 text-xl font-semibold text-white">
                      {result.geo_details.trusted_locations}
                    </p>
                  </div>
                  <div className="rounded-[28px] border border-white/10 bg-slate-950/35 p-5">
                    <p className="text-xs uppercase tracking-[0.24em] text-slate-400">
                      Impossible travel
                    </p>
                    <p className="mt-3 text-xl font-semibold text-white">
                      {result.geo_details.impossible_travel ? "Yes" : "No"}
                    </p>
                  </div>
                  <div className="rounded-[28px] border border-white/10 bg-slate-950/35 p-5">
                    <p className="text-xs uppercase tracking-[0.24em] text-slate-400">
                      Travel speed
                    </p>
                    <p className="mt-3 text-xl font-semibold text-white">
                      {result.geo_details.travel_speed_kmh
                        ? `${result.geo_details.travel_speed_kmh} km/h`
                        : "N/A"}
                    </p>
                  </div>
                </div>
              ) : null}

              {result.geo_details ? (
                <div className="rounded-[28px] border border-sky-300/15 bg-sky-400/10 p-5">
                  <p className="text-xs uppercase tracking-[0.24em] text-sky-200">
                    Geo explanation
                  </p>
                  <p className="mt-3 text-sm leading-7 text-slate-100">
                    {result.geo_details.explanation}
                  </p>
                </div>
              ) : null}

              {result.model_explanation ? (
                <div className="grid gap-5 xl:grid-cols-[1.05fr_0.95fr]">
                  <div className="rounded-[28px] border border-white/10 bg-slate-950/35 p-5">
                    <h3 className="text-lg font-semibold text-white">
                      Why the model reacted
                    </h3>
                    <p className="mt-4 text-sm leading-7 text-slate-200">
                      {result.model_explanation.narrative}
                    </p>
                  </div>

                  <div className="rounded-[28px] border border-white/10 bg-slate-950/35 p-5">
                    <h3 className="text-lg font-semibold text-white">
                      Top risk drivers
                    </h3>
                    <div className="mt-5 space-y-3">
                      {result.model_explanation.top_risk_drivers.map((item) => (
                        <div
                          key={item.feature}
                          className="rounded-2xl border border-rose-300/15 bg-rose-400/10 px-4 py-3 text-sm leading-6 text-slate-100"
                        >
                          <span className="font-medium text-white">
                            {formatFeatureLabel(item.feature)}
                          </span>
                          {`: +${(item.impact * 100).toFixed(1)} pts vs baseline `}
                          <span className="text-slate-300">
                            ({item.actual_value} vs {item.reference_value})
                          </span>
                        </div>
                      ))}
                      {result.model_explanation.top_risk_drivers.length === 0 ? (
                        <div className="rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-sm text-slate-300">
                          No strong positive model drivers for this transaction.
                        </div>
                      ) : null}
                    </div>
                  </div>
                </div>
              ) : null}

              <div className="grid gap-5 xl:grid-cols-2">
                <div className="rounded-[28px] border border-white/10 bg-slate-950/35 p-5">
                  <div className="flex items-center justify-between">
                    <h3 className="text-lg font-semibold text-white">Risk breakdown</h3>
                    <span className="font-mono text-xs text-slate-400">
                      backend.risk_breakdown
                    </span>
                  </div>
                  <div className="mt-6 h-64">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={breakdownData}>
                        <XAxis
                          dataKey="name"
                          tick={{ fill: "#cbd5e1", fontSize: 12 }}
                          axisLine={false}
                          tickLine={false}
                        />
                        <YAxis
                          tick={{ fill: "#94a3b8", fontSize: 12 }}
                          axisLine={false}
                          tickLine={false}
                        />
                        <Tooltip
                          cursor={{ fill: "rgba(148, 163, 184, 0.08)" }}
                          contentStyle={{
                            background: "#08111f",
                            border: "1px solid rgba(148, 163, 184, 0.14)",
                            borderRadius: "16px",
                            color: "#e2e8f0",
                          }}
                        />
                        <Bar dataKey="value" radius={[10, 10, 0, 0]}>
                          {breakdownData.map((entry) => (
                            <Cell
                              key={entry.name}
                              fill={
                                entry.value > 0
                                  ? "rgba(56, 189, 248, 0.86)"
                                  : "rgba(148, 163, 184, 0.28)"
                              }
                            />
                          ))}
                        </Bar>
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </div>

                <div className="rounded-[28px] border border-white/10 bg-slate-950/35 p-5">
                  <div className="flex items-center justify-between">
                    <h3 className="text-lg font-semibold text-white">
                      Feature importance
                    </h3>
                    <span className="font-mono text-xs text-slate-400">
                      backend.advanced_explanation
                    </span>
                  </div>
                  <div className="mt-6 h-64">
                    <ResponsiveContainer width="100%" height="100%">
                      <RadarChart data={featureData}>
                        <PolarGrid stroke="rgba(148, 163, 184, 0.18)" />
                        <PolarAngleAxis
                          dataKey="feature"
                          tick={{ fill: "#cbd5e1", fontSize: 12 }}
                        />
                        <RadarChartShape
                          dataKey="value"
                          stroke="#38bdf8"
                          fill="#38bdf8"
                          fillOpacity={0.35}
                        />
                        <Tooltip
                          contentStyle={{
                            background: "#08111f",
                            border: "1px solid rgba(148, 163, 184, 0.14)",
                            borderRadius: "16px",
                            color: "#e2e8f0",
                          }}
                        />
                      </RadarChart>
                    </ResponsiveContainer>
                  </div>
                </div>
              </div>

              <div className="grid gap-5 xl:grid-cols-[0.95fr_1.05fr]">
                <div className="rounded-[28px] border border-white/10 bg-slate-950/35 p-5">
                  <h3 className="text-lg font-semibold text-white">Flags</h3>
                  <div className="mt-5 space-y-3">
                    {Object.entries(result.flags).map(([key, value]) => (
                      <div
                        key={key}
                        className="flex items-center justify-between rounded-2xl border border-white/10 bg-white/5 px-4 py-3"
                      >
                        <span className="text-sm text-slate-300">
                          {formatFeatureLabel(key)}
                        </span>
                        <span className="font-mono text-xs uppercase tracking-[0.18em] text-white">
                          {value}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="rounded-[28px] border border-white/10 bg-slate-950/35 p-5">
                  <h3 className="text-lg font-semibold text-white">XAI reasons</h3>
                  <div className="mt-5 space-y-3">
                    {xaiData.map(({ signal, status }) => (
                      <div
                        key={signal}
                        className="rounded-2xl border border-sky-300/15 bg-sky-400/10 px-4 py-3 text-sm leading-6 text-slate-100"
                      >
                        <span className="font-medium capitalize text-white">{signal}:</span>{" "}
                        <span>{status}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )}
        </motion.section>
      </section>
    </main>
  );
}
