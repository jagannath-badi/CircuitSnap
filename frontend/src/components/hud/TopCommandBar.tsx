import React, { useState } from 'react';
import { Shield, ShieldAlert, ShieldCheck, Terminal, Cpu, Mic, Settings, Search, RefreshCw, Zap, Lock } from 'lucide-react';
import type { SystemTelemetry } from '../../api';

export type HudTab = 'command' | 'core' | 'voice' | 'settings';

interface TopCommandBarProps {
  currentTab: HudTab;
  onSelectTab: (tab: HudTab) => void;
  telemetry: SystemTelemetry | null;
  privacyMode: 'strict' | 'guarded' | 'relaxed';
  onPrivacyModeChange: (mode: 'strict' | 'guarded' | 'relaxed') => void;
  onResetBench: () => void;
  emergencyStop: boolean;
  onOpenQuickSearch?: () => void;
}

export const TopCommandBar: React.FC<TopCommandBarProps> = ({
  currentTab,
  onSelectTab,
  telemetry,
  privacyMode,
  onPrivacyModeChange,
  onResetBench,
  emergencyStop,
  onOpenQuickSearch,
}) => {
  const [isTrustOpen, setIsTrustOpen] = useState(false);

  const tabs: Array<{ id: HudTab; label: string; icon: React.ReactNode }> = [
    { id: 'command', label: 'Command Center', icon: <Terminal className="w-4 h-4" /> },
    { id: 'core', label: 'AI Core', icon: <Cpu className="w-4 h-4" /> },
    { id: 'voice', label: 'AI Voice', icon: <Mic className="w-4 h-4" /> },
    { id: 'settings', label: 'Settings', icon: <Settings className="w-4 h-4" /> },
  ];

  return (
    <header className="min-h-[56px] h-auto border-b border-cyan-950/60 bg-[#070C18]/90 backdrop-blur-md px-3 sm:px-4 py-1.5 sm:py-0 flex items-center justify-between gap-3 sm:gap-4 z-40 select-none overflow-x-auto no-scrollbar scroll-smooth">
      {/* Brand & Tabs */}
      <div className="flex items-center gap-3 sm:gap-4 lg:gap-6 flex-shrink-0">
        <div className="flex items-center gap-2 sm:gap-2.5 flex-shrink-0">
          <div className="relative flex items-center justify-center w-8 h-8 rounded-lg bg-cyan-950/40 border border-cyan-500/30 flex-shrink-0">
            <Zap className="w-4 h-4 text-cyan-400 animate-pulse" />
            <div className="absolute inset-0 rounded-lg bg-cyan-500/10 blur-[6px]" />
          </div>
          <div className="whitespace-nowrap flex-shrink-0">
            <div className="flex items-center gap-1.5 whitespace-nowrap">
              <span className="font-mono text-xs font-bold tracking-wider text-cyan-300">MARK 85</span>
              <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-cyan-950 text-cyan-400 border border-cyan-800/40 whitespace-nowrap">PRO</span>
            </div>
            <div className="text-[10px] text-slate-400 font-mono tracking-tight whitespace-nowrap">Multi-Discipline Engineering OS</div>
          </div>
        </div>

        {/* Navigation Tabs */}
        <nav className="flex items-center gap-1 p-1 rounded-lg bg-slate-900/60 border border-slate-800/60 flex-shrink-0">
          {tabs.map((t) => (
            <button
              key={t.id}
              onClick={() => onSelectTab(t.id)}
              className={`flex items-center gap-1.5 sm:gap-2 px-2.5 sm:px-3 py-1.5 min-h-[44px] rounded-md text-xs font-mono transition-transform duration-200 ease-[cubic-bezier(0.22,1,0.36,1)] will-change-transform ${
                currentTab === t.id
                  ? 'bg-cyan-500/15 text-cyan-300 border border-cyan-500/40 shadow-[0_0_12px_rgba(0,166,232,0.25)] scale-[1.02]'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/40'
              }`}
            >
              {t.icon}
              <span className="whitespace-nowrap">{t.label}</span>
            </button>
          ))}
        </nav>
      </div>

      {/* Desktop Compact Search (lg to 2xl) */}
      <div className="hidden lg:flex 2xl:hidden items-center flex-shrink-0">
        <button
          onClick={onOpenQuickSearch}
          className="flex items-center gap-1.5 px-2.5 py-1.5 min-h-[44px] rounded-md bg-slate-900/80 border border-slate-800 text-slate-400 hover:text-slate-200 text-xs font-mono transition-transform duration-200 ease-[cubic-bezier(0.22,1,0.36,1)] will-change-transform"
          title="Quick Lookup (Ctrl + K)"
        >
          <Search className="w-3.5 h-3.5 text-cyan-400 flex-shrink-0" />
          <kbd className="px-1.5 py-0.5 rounded bg-slate-800 text-[10px] text-slate-400 border border-slate-700">Ctrl + K</kbd>
        </button>
      </div>

      {/* Full Quick Search Bar (2xl+) */}
      <div className="hidden 2xl:flex items-center min-w-0 flex-1 max-w-sm">
        <button
          onClick={onOpenQuickSearch}
          className="w-full flex items-center justify-between gap-2 px-3 py-1.5 min-h-[44px] rounded-md bg-slate-900/80 border border-slate-800 text-slate-400 hover:text-slate-200 text-xs font-mono transition-transform duration-200 ease-[cubic-bezier(0.22,1,0.36,1)] will-change-transform"
        >
          <div className="flex items-center gap-2 truncate">
            <Search className="w-3.5 h-3.5 text-cyan-400 flex-shrink-0" />
            <span className="truncate">Quick Lookup (Theorems, Formulas, Diagrams, PYQs)</span>
          </div>
          <kbd className="ml-2 px-1.5 py-0.5 rounded bg-slate-800 text-[10px] text-slate-400 border border-slate-700 flex-shrink-0">Ctrl + K</kbd>
        </button>
      </div>

      {/* Status & Privacy Controls */}
      <div className="flex items-center gap-2 sm:gap-3 flex-shrink-0">
        {/* Status Pill */}
        <div className={`flex items-center gap-1.5 px-2.5 py-1 min-h-[44px] rounded-full border text-[11px] font-mono whitespace-nowrap flex-shrink-0 ${
          emergencyStop
            ? 'bg-rose-950/60 border-rose-500/50 text-rose-300'
            : telemetry?.all_operational
            ? 'bg-emerald-950/50 border-emerald-500/40 text-emerald-300'
            : 'bg-amber-950/50 border-amber-500/40 text-amber-300'
        }`}>
          <div className={`w-1.5 h-1.5 rounded-full animate-ping flex-shrink-0 ${
            emergencyStop ? 'bg-rose-400' : telemetry?.all_operational ? 'bg-emerald-400' : 'bg-amber-400'
          }`} />
          <span className="whitespace-nowrap">{emergencyStop ? 'EMERGENCY STOPPED' : telemetry?.all_operational ? 'ALL SYSTEMS OPERATIONAL' : 'DEGRADED COGNITION'}</span>
        </div>

        {/* Shield / Trust Center Button */}
        <div className="relative flex-shrink-0">
          <button
            onClick={() => setIsTrustOpen(!isTrustOpen)}
            className={`flex items-center gap-1.5 px-2.5 py-1 min-h-[44px] rounded-md text-xs font-mono border transition-transform duration-200 ease-[cubic-bezier(0.22,1,0.36,1)] will-change-transform whitespace-nowrap flex-shrink-0 ${
              privacyMode === 'strict'
                ? 'bg-emerald-950/40 border-emerald-500/40 text-emerald-300'
                : privacyMode === 'guarded'
                ? 'bg-cyan-950/40 border-cyan-500/40 text-cyan-300'
                : 'bg-amber-950/40 border-amber-500/40 text-amber-300'
            }`}
          >
            {privacyMode === 'strict' ? <ShieldCheck className="w-3.5 h-3.5 flex-shrink-0" /> : privacyMode === 'guarded' ? <Shield className="w-3.5 h-3.5 flex-shrink-0" /> : <ShieldAlert className="w-3.5 h-3.5 flex-shrink-0" />}
            <span className="whitespace-nowrap">Privacy: {privacyMode.charAt(0).toUpperCase() + privacyMode.slice(1)}</span>
          </button>

          {isTrustOpen && (
            <div className="absolute right-0 mt-2 w-72 rounded-xl bg-slate-900 border border-cyan-900/60 shadow-2xl p-3 z-50 animate-panel-pop">
              <div className="flex items-center justify-between pb-2 mb-2 border-b border-slate-800">
                <div className="flex items-center gap-1.5 text-xs font-bold text-cyan-300 font-mono">
                  <Lock className="w-3.5 h-3.5" />
                  <span>Trust & Privacy Guard</span>
                </div>
                <button onClick={() => setIsTrustOpen(false)} className="text-slate-500 hover:text-slate-300 text-xs min-h-[44px] min-w-[44px] flex items-center justify-center">✕</button>
              </div>

              <div className="space-y-2 text-xs font-mono">
                {(['strict', 'guarded', 'relaxed'] as const).map((mode) => (
                  <button
                    key={mode}
                    onClick={() => { onPrivacyModeChange(mode); setIsTrustOpen(false); }}
                    className={`w-full text-left p-2 min-h-[44px] rounded-lg border transition-transform duration-200 ease-[cubic-bezier(0.22,1,0.36,1)] will-change-transform ${
                      privacyMode === mode ? 'bg-cyan-950/40 border-cyan-500/50 text-cyan-200' : 'border-slate-800 hover:bg-slate-800/40 text-slate-400'
                    }`}
                  >
                    <div className="font-semibold text-slate-200 capitalize">{mode} Privacy</div>
                    <div className="text-[10px] text-slate-400 mt-0.5">
                      {mode === 'strict' && '100% offline J.A.R.V.I.S. Core with zero cloud transmission.'}
                      {mode === 'guarded' && 'Pre-flight redaction of API keys, tokens, and PII before cloud query.'}
                      {mode === 'relaxed' && 'Direct cloud routing without client-side credential scrubbing.'}
                    </div>
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Bench Reset */}
        <button
          onClick={onResetBench}
          title="Reset Bench & Clear Session"
          className="p-2 min-h-[44px] min-w-[44px] flex items-center justify-center rounded-md text-slate-400 hover:text-cyan-300 hover:bg-cyan-950/40 border border-slate-800 transition-transform duration-200 ease-[cubic-bezier(0.22,1,0.36,1)] will-change-transform flex-shrink-0"
        >
          <RefreshCw className="w-3.5 h-3.5" />
        </button>
      </div>
    </header>
  );
};
