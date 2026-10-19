import React from 'react';
import { Cpu, RefreshCw, RotateCcw, Activity, ShieldAlert } from 'lucide-react';
import type { HealthResponse } from '../api';

export interface TelemetryData {
  provider: string;
  model_id: string;
  attempts: number;
  fallback_used: boolean;
}

export interface TelemetryHeaderProps {
  health: HealthResponse | null;
  isHealthLoading: boolean;
  healthError: string | null;
  onRefreshHealth: () => void;
  telemetry: TelemetryData;
  onResetWorkbench: () => void;
  hasActiveSession: boolean;
}

export const TelemetryHeader: React.FC<TelemetryHeaderProps> = ({
  health,
  isHealthLoading,
  healthError,
  onRefreshHealth,
  telemetry,
  onResetWorkbench,
  hasActiveSession,
}) => {
  const isHealthy = health?.status === 'healthy';

  return (
    <header className="bg-slate-900/70 backdrop-blur-md border-b border-white/10 sticky top-0 z-40 px-4 py-2.5 h-[65px] flex items-center justify-between">
      {/* Left Branding & Hardware LED */}
      <div className="flex items-center gap-3">
        <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center shadow-lg shadow-cyan-500/20 text-white flex-shrink-0">
          <Cpu className="w-5 h-5" />
        </div>
        <div>
          <div className="flex items-center gap-2">
            <span className="font-bold tracking-tight text-white text-base">CircuitSnap</span>
            <span className="text-[10px] tracking-wider uppercase font-mono font-semibold px-1.5 py-0.5 rounded bg-cyan-950/80 text-cyan-400 border border-cyan-800/60">
              v2.0 HUD
            </span>
          </div>
          <div className="flex items-center gap-2 text-[11px] font-mono text-slate-400">
            <span className="hidden sm:inline">CYBER-PHYSICAL BENCH</span>
            <span className="text-slate-600 hidden sm:inline">•</span>
            {/* Hardware LED Status */}
            <div
              className="flex items-center gap-1.5 cursor-pointer group"
              onClick={onRefreshHealth}
              title={
                healthError ||
                (isHealthy ? 'FastAPI Backend Online & Operational' : 'FastAPI Backend Offline')
              }
            >
              <span
                className={`w-2 h-2 rounded-full transition-all duration-300 ${
                  isHealthLoading
                    ? 'bg-amber-400 animate-pulse shadow-[0_0_8px_rgba(251,191,36,0.8)]'
                    : isHealthy
                    ? 'bg-emerald-400 shadow-[0_0_10px_rgba(52,211,153,0.9)] animate-pulse'
                    : 'bg-rose-500 shadow-[0_0_10px_rgba(244,63,94,0.9)]'
                }`}
              />
              <span
                className={`text-[10px] uppercase font-bold tracking-wider ${
                  isHealthLoading
                    ? 'text-amber-400'
                    : isHealthy
                    ? 'text-emerald-400'
                    : 'text-rose-400'
                }`}
              >
                {isHealthLoading ? 'INITIALIZING' : isHealthy ? 'SYS ONLINE' : 'SYS OFFLINE'}
              </span>
              <RefreshCw
                className={`w-2.5 h-2.5 text-slate-500 group-hover:text-cyan-400 transition-colors ${
                  isHealthLoading ? 'animate-spin' : ''
                }`}
              />
            </div>
          </div>
        </div>
      </div>

      {/* Center Monospace Telemetry Chips (Desktop) */}
      <div className="hidden md:flex items-center gap-2">
        {/* Provider Chip */}
        <div className="px-2.5 py-1 rounded-lg bg-slate-950/80 border border-white/10 flex items-center gap-1.5 font-mono text-[11px]">
          <span className="text-slate-500 text-[10px]">PROV:</span>
          <span className="text-cyan-300 font-semibold">{telemetry.provider || 'STANDBY'}</span>
        </div>

        {/* Model Chip */}
        <div className="px-2.5 py-1 rounded-lg bg-slate-950/80 border border-white/10 flex items-center gap-1.5 font-mono text-[11px]">
          <span className="text-slate-500 text-[10px]">MODEL:</span>
          <span className="text-slate-200 truncate max-w-[150px] font-semibold">
            {telemetry.model_id || 'AUTO'}
          </span>
        </div>

        {/* Cycles/Attempts Chip */}
        <div className="px-2 py-1 rounded-lg bg-slate-950/80 border border-white/10 flex items-center gap-1.5 font-mono text-[11px]">
          <Activity className="w-3 h-3 text-cyan-400" />
          <span className="text-slate-400">
            {telemetry.attempts === 1 ? '1 CYCLE' : `${telemetry.attempts} CYCLES`}
          </span>
        </div>

        {/* Fallback Flag */}
        {telemetry.fallback_used && (
          <div className="px-2 py-1 rounded-lg bg-amber-500/15 border border-amber-500/30 flex items-center gap-1 font-mono text-[10px] text-amber-300 font-bold">
            <ShieldAlert className="w-3 h-3 text-amber-400" />
            <span>FALLBACK</span>
          </div>
        )}
      </div>

      {/* Right Actions: Workbench Reset */}
      <div className="flex items-center gap-2">
        <button
          onClick={onResetWorkbench}
          disabled={!hasActiveSession}
          className={`px-3 py-1.5 rounded-xl border flex items-center gap-1.5 text-xs font-mono font-medium transition-all ${
            hasActiveSession
              ? 'bg-rose-950/40 hover:bg-rose-950/70 border-rose-800/60 text-rose-300 hover:text-rose-100 shadow-sm'
              : 'bg-slate-950/30 border-white/5 text-slate-600 cursor-not-allowed opacity-60'
          }`}
          title="Reset Workbench and clear all active telemetry & scope image"
        >
          <RotateCcw className="w-3.5 h-3.5" />
          <span className="hidden sm:inline">RESET BENCH</span>
        </button>
      </div>
    </header>
  );
};

