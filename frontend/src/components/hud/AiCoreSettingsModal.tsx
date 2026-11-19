import React from 'react';
import { X, Cpu, Shield, Zap, Lock, Server } from 'lucide-react';
import type { ModelOption } from '../../api';

interface AiCoreSettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
  availableModels: ModelOption[];
  selectedModel: string;
  onSelectModel: (id: string) => void;
  privacyMode: 'strict' | 'guarded' | 'relaxed';
  onPrivacyModeChange: (mode: 'strict' | 'guarded' | 'relaxed') => void;
}

export const AiCoreSettingsModal: React.FC<AiCoreSettingsModalProps> = ({
  isOpen,
  onClose,
  availableModels,
  selectedModel,
  onSelectModel,
  privacyMode,
  onPrivacyModeChange,
}) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-in fade-in select-none font-mono">
      <div className="w-full max-w-xl rounded-2xl bg-[#090F1E] border border-cyan-900/60 shadow-2xl p-5 flex flex-col gap-4 text-slate-100">
        {/* Header */}
        <div className="flex items-center justify-between pb-3 border-b border-slate-800">
          <div className="flex items-center gap-2">
            <Cpu className="w-5 h-5 text-cyan-400" />
            <div>
              <h2 className="text-sm font-bold text-slate-100">AI Core Intelligence Settings</h2>
              <p className="text-[11px] text-slate-400">Configure provider routing, models, and privacy guards</p>
            </div>
          </div>
          <button onClick={onClose} className="p-2 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 min-h-[44px] min-w-[44px] flex items-center justify-center">
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* 1. Reasoning Provider Cards */}
        <div>
          <label className="block text-xs font-bold text-cyan-300 uppercase mb-2">Primary Cognitive Engine</label>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            <button
              onClick={() => onSelectModel('auto')}
              className={`p-3 rounded-xl border text-left transition-all ${
                selectedModel === 'auto' || selectedModel === 'jarvis-auto'
                  ? 'bg-cyan-950/40 border-cyan-500/60 shadow-[0_0_12px_rgba(0,166,232,0.2)]'
                  : 'bg-slate-900/60 border-slate-800 hover:border-slate-700'
              }`}
            >
              <div className="flex items-center justify-between text-xs font-bold text-slate-200">
                <span>J.A.R.V.I.S. Smart Router</span>
                <Zap className="w-3.5 h-3.5 text-cyan-400" />
              </div>
              <div className="text-[10px] text-slate-400 mt-1">Autonomous multi-discipline routing across all branches</div>
            </button>

            {availableModels.map((m) => (
              <button
                key={m.id}
                onClick={() => onSelectModel(m.id)}
                className={`p-3 rounded-xl border text-left transition-all ${
                  selectedModel === m.id
                    ? 'bg-cyan-950/40 border-cyan-500/60 shadow-[0_0_12px_rgba(0,166,232,0.2)]'
                    : 'bg-slate-900/60 border-slate-800 hover:border-slate-700'
                }`}
              >
                <div className="flex items-center justify-between text-xs font-bold text-slate-200">
                  <span className="truncate pr-1">{m.label}</span>
                  <Server className="w-3.5 h-3.5 text-cyan-400" />
                </div>
                <div className="text-[10px] text-slate-400 mt-1 truncate">{m.specialty}</div>
              </button>
            ))}
          </div>
        </div>

        {/* 2. Privacy Mode Selector */}
        <div>
          <label className="block text-xs font-bold text-cyan-300 uppercase mb-2">Data Privacy & Security Guard</label>
          <div className="grid grid-cols-3 gap-2">
            {[
              { id: 'strict', label: 'Strict Offline', desc: 'Zero cloud transit. 100% local memory.', icon: <Lock className="w-3.5 h-3.5 text-emerald-400" /> },
              { id: 'guarded', label: 'Guarded Cloud', desc: 'Pre-flight redaction of keys & PII.', icon: <Shield className="w-3.5 h-3.5 text-cyan-400" /> },
              { id: 'relaxed', label: 'Direct Cloud', desc: 'Standard routing with fast failover.', icon: <Zap className="w-3.5 h-3.5 text-amber-400" /> },
            ].map((p) => (
              <button
                key={p.id}
                onClick={() => onPrivacyModeChange(p.id as 'strict' | 'guarded' | 'relaxed')}
                className={`p-2.5 rounded-xl border text-left transition-all ${
                  privacyMode === p.id
                    ? 'bg-cyan-950/40 border-cyan-500/60 shadow-[0_0_8px_rgba(0,166,232,0.2)]'
                    : 'bg-slate-900/60 border-slate-800 hover:border-slate-700'
                }`}
              >
                <div className="flex items-center gap-1.5 text-xs font-bold text-slate-200">
                  {p.icon}
                  <span>{p.label}</span>
                </div>
                <div className="text-[10px] text-slate-400 mt-1 leading-snug">{p.desc}</div>
              </button>
            ))}
          </div>
        </div>

        {/* Footer */}
        <div className="pt-3 border-t border-slate-800 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-xl bg-cyan-500/20 hover:bg-cyan-500/30 text-cyan-300 border border-cyan-500/50 text-xs font-bold transition-all"
          >
            Apply & Close
          </button>
        </div>
      </div>
    </div>
  );
};
