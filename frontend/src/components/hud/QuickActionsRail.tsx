import React from 'react';
import { Mic, Search, Trash2, Power, AlertOctagon, ShieldCheck } from 'lucide-react';

interface QuickActionsRailProps {
  onVoiceCommand: () => void;
  onSystemScan: () => void;
  onClearContext: () => void;
  onEmergencyStop: () => void;
  onTakeControl: () => void;
  emergencyStop: boolean;
  provider: string;
  modelId: string;
}

export const QuickActionsRail: React.FC<QuickActionsRailProps> = ({
  onVoiceCommand,
  onSystemScan,
  onClearContext,
  onEmergencyStop,
  onTakeControl,
  emergencyStop,
  provider,
  modelId,
}) => {
  return (
    <aside className="w-full flex flex-col gap-3 font-mono select-none">
      {/* 1. Quick Actions */}
      <div className="p-3.5 rounded-xl bg-slate-900/70 border border-slate-800/80 shadow-md">
        <div className="text-xs font-bold text-cyan-300 uppercase tracking-wider mb-2.5 pb-2 border-b border-slate-800/60">
          Quick Actions
        </div>

        <div className="space-y-1.5">
          <button
            onClick={onVoiceCommand}
            className="w-full flex items-center gap-2 p-2.5 min-h-[44px] rounded-lg bg-slate-800/60 hover:bg-cyan-950/40 border border-slate-700/60 hover:border-cyan-500/40 text-xs text-slate-200 hover:text-cyan-300 transition-transform duration-200 ease-[cubic-bezier(0.22,1,0.36,1)] will-change-transform"
          >
            <Mic className="w-3.5 h-3.5 text-cyan-400 flex-shrink-0" />
            <span>Voice Command</span>
          </button>

          <button
            onClick={onSystemScan}
            className="w-full flex items-center gap-2 p-2.5 min-h-[44px] rounded-lg bg-slate-800/60 hover:bg-cyan-950/40 border border-slate-700/60 hover:border-cyan-500/40 text-xs text-slate-200 hover:text-cyan-300 transition-transform duration-200 ease-[cubic-bezier(0.22,1,0.36,1)] will-change-transform"
          >
            <Search className="w-3.5 h-3.5 text-cyan-400 flex-shrink-0" />
            <span>Scan Bench & Vault</span>
          </button>

          <button
            onClick={onClearContext}
            className="w-full flex items-center gap-2 p-2.5 min-h-[44px] rounded-lg bg-slate-800/60 hover:bg-rose-950/40 border border-slate-700/60 hover:border-rose-500/40 text-xs text-slate-200 hover:text-rose-300 transition-transform duration-200 ease-[cubic-bezier(0.22,1,0.36,1)] will-change-transform"
          >
            <Trash2 className="w-3.5 h-3.5 text-rose-400 flex-shrink-0" />
            <span>Clear Context</span>
          </button>
        </div>
      </div>

      {/* 2. Cognitive State / LLM Health */}
      <div className="p-3.5 rounded-xl bg-slate-900/70 border border-slate-800/80 shadow-md text-xs">
        <div className="text-xs font-bold text-cyan-300 uppercase tracking-wider mb-2.5 pb-2 border-b border-slate-800/60 flex items-center justify-between">
          <span>Reasoner Status</span>
          <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
        </div>
        <div className="space-y-1.5 text-[11px]">
          <div className="flex justify-between text-slate-400">
            <span>Provider:</span>
            <span className="font-semibold text-slate-200 truncate max-w-[120px]">{provider || 'J.A.R.V.I.S.'}</span>
          </div>
          <div className="flex justify-between text-slate-400">
            <span>Model:</span>
            <span className="font-semibold text-slate-200 truncate max-w-[120px]">{modelId || 'auto'}</span>
          </div>
          <div className="flex justify-between text-slate-400">
            <span>Mode:</span>
            <span className="text-emerald-400 font-bold">DETERMINISTIC</span>
          </div>
        </div>
      </div>

      {/* 3. High-Visibility Emergency Circuit Controls */}
      <div className="p-3.5 rounded-xl bg-slate-900/90 border border-slate-800/80 shadow-lg space-y-2">
        <button
          onClick={onEmergencyStop}
          className={`w-full py-2.5 px-3 min-h-[44px] rounded-xl flex items-center justify-center gap-2 text-xs font-bold font-mono tracking-wider transition-transform duration-200 ease-[cubic-bezier(0.22,1,0.36,1)] will-change-transform shadow-lg ${
            emergencyStop
              ? 'bg-rose-600 text-white animate-pulse border border-rose-400 shadow-[0_0_15px_#e11d48] scale-[1.02]'
              : 'bg-rose-950/80 hover:bg-rose-700 text-rose-200 hover:text-white border border-rose-600/60'
          }`}
        >
          <AlertOctagon className="w-4 h-4 text-white flex-shrink-0" />
          <span>{emergencyStop ? 'SYSTEM STOPPED (DISARMED)' : 'EMERGENCY STOP'}</span>
        </button>

        <button
          onClick={onTakeControl}
          className="w-full py-2.5 px-3 min-h-[44px] rounded-xl flex items-center justify-center gap-2 text-xs font-mono font-semibold bg-cyan-950/60 hover:bg-cyan-900 text-cyan-300 border border-cyan-700/60 transition-transform duration-200 ease-[cubic-bezier(0.22,1,0.36,1)] will-change-transform"
        >
          <Power className="w-3.5 h-3.5 text-cyan-400 flex-shrink-0" />
          <span>TAKE MANUAL CONTROL</span>
        </button>
      </div>
    </aside>
  );
};
