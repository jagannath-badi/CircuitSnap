import React from 'react';
import { Activity, Server, AlertTriangle, HardDrive, Cpu, Radio } from 'lucide-react';
import type { SystemTelemetry } from '../../api';

interface TelemetryLeftPanelProps {
  telemetry: SystemTelemetry | null;
  isLoading: boolean;
  onRefresh?: () => void;
}

export const TelemetryLeftPanel: React.FC<TelemetryLeftPanelProps> = ({
  telemetry,
  isLoading,
  onRefresh,
}) => {
  const cpu = telemetry?.cpu_percent ?? 0;
  const ram = telemetry?.ram_percent ?? 0;
  const disk = telemetry?.disk_percent ?? 0;

  // Sorted services: online first (0), standby second (1), offline last (2)
  const servicesList = telemetry?.services
    ? Object.entries(telemetry.services).sort(([, a], [, b]) => {
        const score = (status: string) => (status === 'online' ? 0 : status === 'standby' ? 1 : 2);
        const scoreDiff = score(a.status) - score(b.status);
        if (scoreDiff !== 0) return scoreDiff;
        return a.name.localeCompare(b.name);
      })
    : [];

  const alerts: string[] = [];
  if (cpu > 85) alerts.push(`High CPU Load (${cpu.toFixed(1)}%) — offline symbolic execution prioritized.`);
  if (ram > 85) alerts.push(`Memory Pressure (${ram.toFixed(1)}%) — streaming garbage collection active.`);
  if (telemetry && !telemetry.services?.gemini?.active && !telemetry.services?.groq?.active) {
    alerts.push('Cloud AI offline — running in autonomous J.A.R.V.I.S. offline mode.');
  }

  return (
    <aside className="w-full h-full flex flex-col gap-3 font-mono select-none overflow-y-auto pr-1">
      {/* 1. Host System Overview */}
      <div className="p-3.5 rounded-xl bg-slate-900/70 border border-slate-800/80 shadow-md">
        <div className="flex items-center justify-between pb-2 mb-3 border-b border-slate-800/60">
          <div className="flex items-center gap-2 text-xs font-bold tracking-wider text-cyan-300 uppercase">
            <Activity className="w-3.5 h-3.5 text-cyan-400" />
            <span>System Telemetry</span>
          </div>
          <button
            onClick={onRefresh}
            className="text-[10px] text-slate-500 hover:text-cyan-400 min-h-[44px] min-w-[44px] flex items-center justify-center transition-transform duration-200 ease-[cubic-bezier(0.22,1,0.36,1)] will-change-transform"
            title="Refresh Host Metrics"
          >
            {isLoading ? 'SYNCING...' : 'LIVE'}
          </button>
        </div>

        <div className="space-y-3 text-xs">
          {/* CPU Bar */}
          <div>
            <div className="flex justify-between text-[11px] mb-1">
              <span className="flex items-center gap-1.5 text-slate-400">
                <Cpu className="w-3 h-3 text-cyan-400" /> CPU Load
              </span>
              <span className="font-semibold text-slate-200">{telemetry?.cpu_percent !== null && telemetry?.cpu_percent !== undefined ? `${cpu.toFixed(1)}%` : 'N/A'}</span>
            </div>
            <div className="w-full h-1.5 rounded-full bg-slate-800 overflow-hidden">
              <div
                className={`h-full rounded-full transition-transform duration-300 ease-[cubic-bezier(0.22,1,0.36,1)] will-change-transform origin-left w-full ${
                  cpu > 80 ? 'bg-rose-500' : cpu > 50 ? 'bg-amber-400' : 'bg-cyan-400'
                }`}
                style={{ transform: `scaleX(${Math.min(1, Math.max(0.02, cpu / 100))})` }}
              />
            </div>
          </div>

          {/* RAM Bar */}
          <div>
            <div className="flex justify-between text-[11px] mb-1">
              <span className="flex items-center gap-1.5 text-slate-400">
                <Server className="w-3 h-3 text-cyan-400" /> RAM Usage
              </span>
              <span className="font-semibold text-slate-200">
                {telemetry?.ram_used_gb ? `${telemetry.ram_used_gb} / ${telemetry.ram_total_gb} GB` : `${ram.toFixed(1)}%`}
              </span>
            </div>
            <div className="w-full h-1.5 rounded-full bg-slate-800 overflow-hidden">
              <div
                className={`h-full rounded-full transition-transform duration-300 ease-[cubic-bezier(0.22,1,0.36,1)] will-change-transform origin-left w-full ${
                  ram > 85 ? 'bg-rose-500' : ram > 65 ? 'bg-amber-400' : 'bg-cyan-400'
                }`}
                style={{ transform: `scaleX(${Math.min(1, Math.max(0.02, ram / 100))})` }}
              />
            </div>
          </div>

          {/* Disk Bar */}
          <div>
            <div className="flex justify-between text-[11px] mb-1">
              <span className="flex items-center gap-1.5 text-slate-400">
                <HardDrive className="w-3 h-3 text-cyan-400" /> Disk Space
              </span>
              <span className="font-semibold text-slate-200">{disk.toFixed(1)}%</span>
            </div>
            <div className="w-full h-1.5 rounded-full bg-slate-800 overflow-hidden">
              <div
                className="h-full rounded-full bg-slate-400 transition-transform duration-300 ease-[cubic-bezier(0.22,1,0.36,1)] will-change-transform origin-left w-full"
                style={{ transform: `scaleX(${Math.min(1, Math.max(0.02, disk / 100))})` }}
              />
            </div>
          </div>

          {/* Network & Uptime */}
          <div className="pt-2 border-t border-slate-800/60 flex items-center justify-between text-[10px] text-slate-400">
            <span className="flex items-center gap-1">
              <Radio className="w-3 h-3 text-emerald-400" /> Network: <b className="text-slate-200 uppercase">{telemetry?.network_status ?? 'ONLINE'}</b>
            </span>
            <span>Uptime: <b className="text-slate-200">{telemetry?.uptime_seconds ? `${Math.floor(telemetry.uptime_seconds / 60)}m` : '0m'}</b></span>
          </div>
        </div>
      </div>

      {/* 2. Connected AI & Local Services */}
      <div className="p-3.5 rounded-xl bg-slate-900/70 border border-slate-800/80 shadow-md flex-1">
        <div className="flex items-center justify-between pb-2 mb-2 border-b border-slate-800/60">
          <div className="flex items-center gap-2 text-xs font-bold tracking-wider text-cyan-300 uppercase">
            <Server className="w-3.5 h-3.5 text-cyan-400" />
            <span>Connected Services</span>
          </div>
          <span className="text-[10px] px-1.5 py-0.5 rounded bg-cyan-950 text-cyan-300 border border-cyan-800/40">
            {servicesList.filter(([, s]) => s.status === 'online').length} / {servicesList.length}
          </span>
        </div>

        <div className="space-y-1.5">
          {servicesList.map(([key, service]) => {
            const isOnline = service.status === 'online';
            const isStandby = service.status === 'standby';
            return (
              <div
                key={key}
                className="flex items-center justify-between p-2 rounded-lg bg-slate-950/40 border border-slate-800/50 hover:border-slate-700 transition-colors text-xs"
              >
                <div className="flex flex-col min-w-0 pr-2">
                  <span className="font-semibold text-slate-200 truncate text-[11px]">{service.name}</span>
                  <span className="text-[10px] text-slate-500 capitalize">{service.provider}</span>
                </div>
                <div className="flex items-center gap-1.5 flex-shrink-0">
                  <span
                    className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${
                      isOnline
                        ? 'bg-emerald-950/70 text-emerald-300 border border-emerald-500/30'
                        : isStandby
                        ? 'bg-amber-950/70 text-amber-300 border border-amber-500/30'
                        : 'bg-rose-950/70 text-rose-300 border border-rose-500/30'
                    }`}
                  >
                    {isOnline ? 'ONLINE' : isStandby ? 'STANDBY' : 'OFFLINE'}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* 3. Important System Alerts */}
      {alerts.length > 0 && (
        <div className="p-3 rounded-xl bg-amber-950/30 border border-amber-600/30 text-amber-200 text-xs">
          <div className="flex items-center gap-1.5 font-bold mb-1.5 text-amber-300">
            <AlertTriangle className="w-3.5 h-3.5 flex-shrink-0" />
            <span>Attention Required</span>
          </div>
          <ul className="space-y-1 text-[11px] text-amber-200/90 list-disc list-inside">
            {alerts.map((alert, i) => (
              <li key={i}>{alert}</li>
            ))}
          </ul>
        </div>
      )}
    </aside>
  );
};
