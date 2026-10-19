import React, { useState, useRef, useEffect } from 'react';
import { Cpu, RefreshCw, RotateCcw, Activity, ShieldAlert, ChevronDown, User, LogOut, Archive } from 'lucide-react';
import type { HealthResponse, ModelOption, OperatorUser } from '../api';

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
  availableModels?: ModelOption[];
  selectedModel?: string;
  onSelectModel?: (modelId: string) => void;
  currentUser?: OperatorUser | null;
  onOpenAuthModal?: () => void;
  onLogout?: () => void;
  onOpenVault?: () => void;
  vaultSessionCount?: number;
}

const DEFAULT_MODEL_ROSTER: ModelOption[] = [
  { id: 'auto', label: 'Auto (Smart Router)', provider: 'auto', specialty: 'Autonomous Task Routing', supports_vision: true },
  { id: 'gemini-3.8-flash', label: 'Gemini 3.8 Flash (Active Default)', provider: 'gemini', specialty: 'Optical Scope & General Telemetry', supports_vision: true },
  { id: 'gemini-3.6-flash', label: 'Gemini 3.6 Flash (Circuit Math)', provider: 'gemini', specialty: 'Circuit Math & Formula Derivations', supports_vision: true },
  { id: 'gemini-2.5-flash', label: 'Gemini 2.5 Flash (Primary Workhorse)', provider: 'gemini', specialty: 'Precision IC & SMD Marking Recognition', supports_vision: true },
  { id: 'llama-3.3-70b-versatile', label: 'Groq Llama 3.3 70B', provider: 'groq', specialty: 'Sub-Second Pinout & Quick Lookups', supports_vision: false },
  { id: 'gemini-2.0-flash-thinking-exp', label: 'Gemini 2.0 Thinking (Experimental)', provider: 'gemini', specialty: 'Formula Derivations (Auto Fallback Protected)', supports_vision: true },
  { id: 'gemini-1.5-pro', label: 'Gemini 1.5 Pro', provider: 'gemini', specialty: 'Deep Datasheets & Dense Schematics', supports_vision: true },
  { id: 'gemini-1.5-flash', label: 'Gemini 1.5 Flash', provider: 'gemini', specialty: 'High-Throughput Quota Fallback', supports_vision: true },
  { id: 'gemini-1.5-flash-8b', label: 'Gemini 1.5 Flash-8B', provider: 'gemini', specialty: 'Ultra-Lightweight Verification', supports_vision: true },
];

export const TelemetryHeader: React.FC<TelemetryHeaderProps> = ({
  health,
  isHealthLoading,
  healthError,
  onRefreshHealth,
  telemetry,
  onResetWorkbench,
  hasActiveSession,
  availableModels = [],
  selectedModel = 'auto',
  onSelectModel,
  currentUser = null,
  onOpenAuthModal,
  onLogout,
  onOpenVault,
  vaultSessionCount,
}) => {
  const isHealthy = health?.status === 'healthy';
  const [isOpen, setIsOpen] = useState(false);
  const [isUserMenuOpen, setIsUserMenuOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const userMenuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
      if (userMenuRef.current && !userMenuRef.current.contains(e.target as Node)) {
        setIsUserMenuOpen(false);
      }
    };
    if (isOpen || isUserMenuOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isOpen, isUserMenuOpen]);

  const modelsToDisplay = availableModels.length > 0 ? availableModels : DEFAULT_MODEL_ROSTER;
  const selectedOption =
    modelsToDisplay.find((opt) => opt.id === selectedModel) || modelsToDisplay[0];

  return (
    <header className="bg-slate-950/70 backdrop-blur-xl border-b border-white/[0.08] sticky top-0 z-40 px-4 sm:px-5 py-2.5 h-[65px] flex items-center justify-between transition-colors">
      {/* Left Branding & Hardware LED */}
      <div className="flex items-center gap-3">
        <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-cyan-500/20 to-blue-600/20 border border-cyan-500/30 flex items-center justify-center text-cyan-400 shadow-[0_0_12px_rgba(6,182,212,0.15)] flex-shrink-0">
          <Cpu className="w-4 h-4" />
        </div>
        <div className="flex items-center gap-2">
          <span className="font-semibold tracking-tight text-white text-sm">CircuitSnap</span>
          <span className="text-[10px] tracking-wider uppercase font-mono text-slate-400 bg-white/[0.04] border border-white/[0.08] px-1.5 py-0.5 rounded">
            v2.0
          </span>
        </div>

        <div className="h-3.5 w-px bg-white/10 hidden sm:block mx-0.5" />

        {/* Breathing Hardware LED Status */}
        <div
          className="flex items-center gap-2 cursor-pointer group"
          onClick={onRefreshHealth}
          title={
            healthError ||
            (isHealthy ? 'FastAPI Backend Online & Operational' : 'FastAPI Backend Offline')
          }
        >
          <div className="relative flex items-center justify-center w-2.5 h-2.5">
            {isHealthLoading ? (
              <span className="w-2 h-2 rounded-full bg-amber-400 animate-pulse shadow-[0_0_8px_rgba(251,191,36,0.8)]" />
            ) : isHealthy ? (
              <>
                <span className="absolute w-3.5 h-3.5 rounded-full bg-emerald-400/30 animate-ping pointer-events-none" />
                <span className="w-2 h-2 rounded-full bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.9)]" />
              </>
            ) : (
              <span className="w-2 h-2 rounded-full bg-rose-500 shadow-[0_0_8px_rgba(244,63,94,0.9)]" />
            )}
          </div>
          <span
            className={`text-[10px] uppercase font-mono font-medium tracking-wider transition-colors ${
              isHealthLoading
                ? 'text-amber-400'
                : isHealthy
                ? 'text-slate-300 group-hover:text-emerald-400'
                : 'text-rose-400'
            }`}
          >
            {isHealthLoading ? 'INIT' : isHealthy ? 'SYS ONLINE' : 'SYS OFFLINE'}
          </span>
          <RefreshCw
            className={`w-2.5 h-2.5 text-slate-500 group-hover:text-cyan-400 transition-colors ${
              isHealthLoading ? 'animate-spin' : ''
            }`}
          />
        </div>
      </div>

      {/* Center Minimalist Micro-Badges & Interactive Model Selector */}
      <div className="hidden md:flex items-center gap-2">
        {/* Provider Chip */}
        <div className="text-xs font-mono text-slate-400 bg-white/[0.03] border border-white/[0.06] rounded-full px-2.5 py-0.5 flex items-center gap-1.5">
          <span className="text-slate-500 text-[10px]">PROV</span>
          <span className="text-cyan-300 font-medium">{telemetry.provider || 'STANDBY'}</span>
        </div>

        {/* Interactive Model Selector Dropdown */}
        <div className="relative" ref={dropdownRef}>
          <button
            type="button"
            onClick={() => setIsOpen((prev) => !prev)}
            className="text-xs font-mono text-slate-300 bg-white/[0.03] hover:bg-white/[0.08] border border-white/[0.08] hover:border-cyan-500/40 rounded-full px-2.5 py-0.5 flex items-center gap-1.5 transition-all shadow-sm group active:scale-95"
            title="Select AI Model Architecture"
          >
            <span className="text-slate-500 text-[10px]">MODEL</span>
            <span className="text-cyan-300 font-medium truncate max-w-[150px]">
              {selectedOption.label.replace(/\s*\(.*\)/, '')}
            </span>
            <ChevronDown
              className={`w-3 h-3 text-slate-400 group-hover:text-cyan-300 transition-transform duration-200 ${
                isOpen ? 'rotate-180 text-cyan-300' : ''
              }`}
            />
          </button>

          {isOpen && (
            <div className="absolute top-full mt-2 right-0 bg-slate-900/95 backdrop-blur-xl border border-white/10 rounded-xl shadow-2xl p-1.5 z-50 min-w-[310px] max-w-[360px] max-h-[390px] overflow-y-auto flex flex-col gap-1 diagnostic-feed-scrollbar">
              <div className="px-2.5 py-1 text-[10px] font-mono uppercase tracking-wider text-slate-400 border-b border-white/5 flex items-center justify-between">
                <span>AI SPECIALIZATION ROSTER</span>
                <span className="text-cyan-400 font-semibold">{modelsToDisplay.length} MODELS</span>
              </div>
              {modelsToDisplay.map((opt) => {
                const isSelected = selectedModel === opt.id;

                return (
                  <button
                    key={opt.id}
                    type="button"
                    onClick={() => {
                      if (onSelectModel) {
                        onSelectModel(opt.id);
                        setIsOpen(false);
                      }
                    }}
                    className={`w-full text-left px-2.5 py-2 rounded-lg transition-all flex items-start justify-between gap-2.5 ${
                      isSelected
                        ? 'bg-cyan-500/15 border border-cyan-500/30 text-white'
                        : 'hover:bg-white/[0.05] text-slate-300 hover:text-white border border-transparent'
                    }`}
                  >
                    <div className="flex flex-col gap-0.5 flex-1 min-w-0">
                      <div className="flex items-center gap-1.5 text-xs font-medium">
                        {isSelected && (
                          <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 shadow-[0_0_6px_rgba(6,182,212,0.8)] flex-shrink-0" />
                        )}
                        <span className="truncate">{opt.label}</span>
                      </div>
                      <span className="text-[10px] text-slate-400 font-normal leading-tight">
                        {opt.specialty}
                      </span>
                    </div>

                    <div className="flex items-center gap-1 flex-shrink-0 self-center">
                      {opt.supports_vision ? (
                        <span className="text-[9px] font-mono font-semibold px-1.5 py-0.5 rounded bg-cyan-500/10 text-cyan-300 border border-cyan-500/25">
                          VISION
                        </span>
                      ) : (
                        <span className="text-[9px] font-mono font-semibold px-1.5 py-0.5 rounded bg-white/[0.03] text-slate-400 border border-white/[0.08]">
                          TEXT
                        </span>
                      )}
                    </div>
                  </button>
                );
              })}
            </div>
          )}
        </div>

        {/* Cycles/Attempts Chip */}
        <div className="text-xs font-mono text-slate-400 bg-white/[0.03] border border-white/[0.06] rounded-full px-2.5 py-0.5 flex items-center gap-1.5">
          <Activity className="w-3 h-3 text-cyan-400" />
          <span>{telemetry.attempts === 1 ? '1 CYCLE' : `${telemetry.attempts} CYCLES`}</span>
        </div>

        {/* Fallback Flag */}
        {telemetry.fallback_used && (
          <div className="text-xs font-mono text-amber-300 bg-amber-500/10 border border-amber-500/20 rounded-full px-2.5 py-0.5 flex items-center gap-1">
            <ShieldAlert className="w-3 h-3 text-amber-400" />
            <span>FALLBACK</span>
          </div>
        )}
      </div>

      {/* Right Actions: Operator Status & Reset Button */}
      <div className="flex items-center gap-2">
        {currentUser ? (
          <div className="relative" ref={userMenuRef}>
            <button
              type="button"
              onClick={() => setIsUserMenuOpen((prev) => !prev)}
              className="px-2.5 py-1 rounded-full text-xs font-mono text-slate-200 bg-cyan-950/40 hover:bg-cyan-950/60 border border-cyan-500/30 hover:border-cyan-500/50 transition-all flex items-center gap-1.5 active:scale-95 shadow-[0_0_8px_rgba(6,182,212,0.15)]"
              title="Operator Profile"
            >
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 shadow-[0_0_6px_rgba(52,211,153,0.8)]" />
              <span className="text-[10px] text-cyan-400">OP:</span>
              <span className="text-[11px] font-semibold text-slate-100 max-w-[90px] truncate">
                {currentUser.username}
              </span>
              <ChevronDown
                className={`w-3 h-3 text-slate-400 transition-transform duration-200 ${
                  isUserMenuOpen ? 'rotate-180' : ''
                }`}
              />
            </button>

            {isUserMenuOpen && (
              <div className="absolute top-full mt-2 right-0 bg-slate-900/95 backdrop-blur-xl border border-white/10 rounded-xl shadow-2xl p-1.5 z-50 min-w-[190px] flex flex-col gap-1">
                <div className="px-3 py-1.5 border-b border-white/5">
                  <span className="text-[9px] text-slate-500 block uppercase font-mono">CALLSIGN</span>
                  <span className="text-xs font-semibold text-cyan-300 block truncate font-mono">
                    {currentUser.username}
                  </span>
                </div>
                <button
                  type="button"
                  onClick={() => {
                    setIsUserMenuOpen(false);
                    onLogout?.();
                  }}
                  className="w-full text-left px-3 py-1.5 rounded-lg text-xs font-mono text-rose-300 hover:text-rose-200 hover:bg-rose-500/10 flex items-center gap-2 transition-colors"
                >
                  <LogOut className="w-3.5 h-3.5 text-rose-400" />
                  <span>Sign Out Operator</span>
                </button>
              </div>
            )}
          </div>
        ) : (
          <button
            type="button"
            onClick={onOpenAuthModal}
            className="px-2.5 py-1 rounded-full text-xs font-mono text-slate-300 hover:text-cyan-300 bg-white/[0.03] hover:bg-white/[0.08] border border-white/[0.08] hover:border-cyan-500/40 transition-all flex items-center gap-1.5 group active:scale-95"
            title="Authenticate as Station Operator"
          >
            <User className="w-3 h-3 text-slate-500 group-hover:text-cyan-400" />
            <span className="text-[10px] text-slate-500">OP:</span>
            <span className="text-[11px] font-medium">GUEST</span>
          </button>
        )}

        {/* Diagnostic Vault Trigger Chip */}
        <button
          type="button"
          onClick={currentUser ? onOpenVault : onOpenAuthModal}
          className="px-2.5 py-1 rounded-full text-xs font-mono text-slate-300 hover:text-cyan-300 bg-white/[0.03] hover:bg-white/[0.08] border border-white/[0.08] hover:border-cyan-500/40 transition-all flex items-center gap-1.5 group active:scale-95"
          title={currentUser ? 'Open Diagnostic Vault' : 'Authenticate to Access Diagnostic Vault'}
        >
          <Archive className="w-3 h-3 text-slate-500 group-hover:text-cyan-400" />
          <span className="text-[10px] text-slate-500">VAULT</span>
          {currentUser && vaultSessionCount !== undefined && vaultSessionCount > 0 && (
            <span className="text-[9px] font-bold text-cyan-300 bg-cyan-950/80 border border-cyan-500/30 px-1 rounded-full">
              {vaultSessionCount}
            </span>
          )}
        </button>

        <button
          onClick={onResetWorkbench}
          disabled={!hasActiveSession}
          className={`px-2.5 py-1 rounded-lg flex items-center gap-1.5 text-xs font-mono transition-all ${
            hasActiveSession
              ? 'text-slate-400 hover:text-rose-400 hover:bg-rose-500/10 active:scale-95'
              : 'text-slate-600 cursor-not-allowed opacity-40'
          }`}
          title="Reset Workbench and clear all active telemetry & scope image"
        >
          <RotateCcw className="w-3.5 h-3.5" />
          <span className="hidden sm:inline">Reset Bench</span>
        </button>
      </div>
    </header>
  );
};
