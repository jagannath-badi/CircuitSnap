import React from 'react';
import {
  Volume2,
  SlidersHorizontal,
  Sparkles,
  Zap,
  Radio,
  Check,
  X,
  Play,
  Loader2,
} from 'lucide-react';
import type { VoiceSettings } from '../hooks/useJarvisVoice';

export interface VoiceSettingsPopoverProps {
  isOpen: boolean;
  onClose: () => void;
  voiceSettings: VoiceSettings;
  onUpdateSettings: (partial: Partial<VoiceSettings>) => void;
  onTestVoice: (voiceId?: string) => Promise<void>;
  isSpeaking?: boolean;
}

const PERSONAS = [
  {
    id: 'en-GB-SoniaNeural',
    name: 'Sonia',
    tag: 'Flagship British Female',
    desc: 'Crisp, authoritative J.A.R.V.I.S. Pro Elite persona with natural British inflection',
    accent: 'en-GB',
  },
  {
    id: 'en-US-AriaNeural',
    name: 'Aria',
    tag: 'Studio Female',
    desc: 'Expressive American voice optimized for clear technical derivations',
    accent: 'en-US',
  },
  {
    id: 'en-US-JennyNeural',
    name: 'Jenny',
    tag: 'Warm Tutor',
    desc: 'Friendly, patient instructional voice ideal for step-by-step concept learning',
    accent: 'en-US',
  },
  {
    id: 'en-GB-RyanNeural',
    name: 'Ryan',
    tag: 'Classic British Male',
    desc: 'Deep, composed British gentleman AI persona for traditional hardware bench work',
    accent: 'en-GB',
  },
] as const;

export const VoiceSettingsPopover: React.FC<VoiceSettingsPopoverProps> = ({
  isOpen,
  onClose,
  voiceSettings,
  onUpdateSettings,
  onTestVoice,
  isSpeaking = false,
}) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-end p-3 sm:p-5 pointer-events-none">
      {/* Backdrop overlay */}
      <div
        className="fixed inset-0 bg-black/40 backdrop-blur-sm pointer-events-auto transition-opacity duration-200"
        onClick={onClose}
      />

      {/* Popover Card */}
      <div className="pointer-events-auto relative mt-14 sm:mt-12 w-full max-w-[380px] rounded-3xl bg-[#060911]/95 border border-white/10 shadow-[0_20px_50px_rgba(0,0,0,0.6)] backdrop-blur-2xl p-4 sm:p-5 text-slate-100 specular-glass flow-card animate-panel-pop">
        {/* Header */}
        <div className="flex items-center justify-between pb-3 mb-3 border-b border-white/[0.08]">
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-[#00A6E8]/20 to-[#FF2D95]/20 border border-[#00A6E8]/30 flex items-center justify-center text-[#00A6E8]">
              <SlidersHorizontal className="w-3.5 h-3.5" />
            </div>
            <div>
              <h3 className="text-xs font-mono font-bold tracking-wider uppercase text-cyan-200">
                Voice Mode Settings
              </h3>
              <p className="text-[10px] text-slate-400">J.A.R.V.I.S. Audio & Persona Engine</p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-white/[0.05] transition-colors"
            title="Close voice settings"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Section 1: Persona Selection */}
        <div className="space-y-2 mb-4">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-mono uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
              <Sparkles className="w-3 h-3 text-[#FF2D95]" />
              Voice Persona
            </span>
            <button
              type="button"
              onClick={() => void onTestVoice(voiceSettings.voiceId)}
              disabled={isSpeaking}
              className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-cyan-950/40 border border-cyan-500/30 text-cyan-300 hover:bg-cyan-500/20 hover:text-cyan-200 transition-all flex items-center gap-1 tactile-spring disabled:opacity-50"
            >
              {isSpeaking ? (
                <>
                  <Loader2 className="w-2.5 h-2.5 animate-spin text-cyan-400" />
                  <span>Testing...</span>
                </>
              ) : (
                <>
                  <Play className="w-2.5 h-2.5 fill-current" />
                  <span>Test Voice</span>
                </>
              )}
            </button>
          </div>

          <div className="grid grid-cols-1 gap-1.5">
            {PERSONAS.map((p) => {
              const isSelected = voiceSettings.voiceId === p.id;
              return (
                <button
                  key={p.id}
                  type="button"
                  onClick={() => onUpdateSettings({ voiceId: p.id })}
                  className={`w-full text-left p-2.5 rounded-xl border transition-all flow-pill flex items-start justify-between gap-2 ${
                    isSelected
                      ? 'bg-gradient-to-r from-[#00A6E8]/15 to-[#FF2D95]/10 border-[#00A6E8]/50 shadow-[0_0_15px_rgba(0,166,232,0.2)]'
                      : 'bg-white/[0.02] border-white/[0.06] hover:bg-white/[0.05] hover:border-white/15'
                  }`}
                >
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-1.5">
                      <span className={`text-xs font-bold ${isSelected ? 'text-white' : 'text-slate-300'}`}>
                        {p.name}
                      </span>
                      <span className="text-[9px] font-mono px-1.5 py-0.2 rounded bg-white/[0.05] text-cyan-300 border border-white/[0.08]">
                        {p.accent}
                      </span>
                      <span className="text-[9px] font-mono text-slate-400 truncate">
                        • {p.tag}
                      </span>
                    </div>
                    <p className="text-[10px] text-slate-400 leading-tight mt-0.5 truncate">
                      {p.desc}
                    </p>
                  </div>
                  {isSelected && (
                    <div className="w-4 h-4 rounded-full bg-[#00A6E8] flex items-center justify-center text-slate-950 flex-shrink-0 mt-0.5">
                      <Check className="w-2.5 h-2.5 stroke-[3]" />
                    </div>
                  )}
                </button>
              );
            })}
          </div>
        </div>

        {/* Section 2: Conversation Mode (Single vs Live Hands-Free) */}
        <div className="space-y-2 mb-4 pt-3 border-t border-white/[0.06]">
          <span className="text-[11px] font-mono uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
            <Radio className="w-3 h-3 text-[#00A6E8]" />
            Interaction Mode
          </span>
          <div className="grid grid-cols-2 gap-2">
            <button
              type="button"
              onClick={() => onUpdateSettings({ interactionMode: 'single' })}
              className={`p-2.5 rounded-xl border text-left transition-all flow-pill ${
                voiceSettings.interactionMode === 'single'
                  ? 'bg-[#00A6E8]/15 border-[#00A6E8]/50 text-cyan-200 shadow-[0_0_12px_rgba(0,166,232,0.2)]'
                  : 'bg-white/[0.02] border-white/[0.06] text-slate-400 hover:text-slate-200 hover:bg-white/[0.04]'
              }`}
            >
              <div className="text-xs font-semibold">Single-Turn</div>
              <div className="text-[10px] text-slate-400 mt-0.5 leading-tight">
                Click mic to talk; turns off after reply
              </div>
            </button>

            <button
              type="button"
              onClick={() => onUpdateSettings({ interactionMode: 'live' })}
              className={`p-2.5 rounded-xl border text-left transition-all flow-pill ${
                voiceSettings.interactionMode === 'live'
                  ? 'bg-gradient-to-r from-[#FF2D95]/20 to-[#00A6E8]/15 border-[#FF2D95]/50 text-rose-200 shadow-[0_0_14px_rgba(255,45,149,0.25)]'
                  : 'bg-white/[0.02] border-white/[0.06] text-slate-400 hover:text-slate-200 hover:bg-white/[0.04]'
              }`}
            >
              <div className="flex items-center gap-1.5">
                <span className="text-xs font-semibold text-rose-300">Live Loop</span>
                <span className="w-1.5 h-1.5 rounded-full bg-[#FF2D95] animate-ping" />
              </div>
              <div className="text-[10px] text-slate-400 mt-0.5 leading-tight">
                Hands-free; auto-rearms after speaking
              </div>
            </button>
          </div>
        </div>

        {/* Section 3: Speech Rate Slider */}
        <div className="space-y-2 mb-4 pt-3 border-t border-white/[0.06]">
          <div className="flex items-center justify-between text-[11px] font-mono">
            <span className="uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
              <Zap className="w-3 h-3 text-amber-400" />
              Speech Rate
            </span>
            <span className="px-2 py-0.5 rounded-full bg-white/[0.05] border border-white/10 text-cyan-300 font-bold text-[10px]">
              {voiceSettings.speechRate.toFixed(2)}x
            </span>
          </div>
          <div className="flex items-center gap-3">
            <span className="text-[10px] font-mono text-slate-500">0.85x</span>
            <input
              type="range"
              min="0.85"
              max="1.25"
              step="0.01"
              value={voiceSettings.speechRate}
              onChange={(e) => onUpdateSettings({ speechRate: parseFloat(e.target.value) })}
              className="flex-1 accent-[#00A6E8] bg-slate-800 h-1.5 rounded-lg appearance-none cursor-pointer"
            />
            <span className="text-[10px] font-mono text-slate-500">1.25x</span>
          </div>
        </div>

        {/* Section 4: Auto-Speak Replies Toggle */}
        <div className="pt-3 border-t border-white/[0.06] flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Volume2 className="w-3.5 h-3.5 text-[#00A6E8]" />
            <div>
              <div className="text-xs font-medium text-slate-200">Auto-Speak Replies</div>
              <div className="text-[10px] text-slate-400">Read out assistant solutions automatically</div>
            </div>
          </div>
          <button
            type="button"
            onClick={() => onUpdateSettings({ autoSpeak: !voiceSettings.autoSpeak })}
            className={`w-10 h-5 rounded-full transition-colors relative p-0.5 flex items-center tactile-spring ${
              voiceSettings.autoSpeak ? 'bg-[#00A6E8]' : 'bg-slate-800'
            }`}
          >
            <span
              className={`w-4 h-4 rounded-full bg-white shadow-md transform transition-transform ${
                voiceSettings.autoSpeak ? 'translate-x-5' : 'translate-x-0'
              }`}
            />
          </button>
        </div>
      </div>
    </div>
  );
};
