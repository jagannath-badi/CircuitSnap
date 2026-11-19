import React from 'react';
import { X, Mic, Volume2, Sparkles, Play } from 'lucide-react';
import type { VoiceSettings } from '../../hooks/useJarvisVoice';

interface AiVoiceSettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
  voiceSettings: VoiceSettings;
  onUpdateVoiceSettings: (settings: Partial<VoiceSettings>) => void;
  onTestVoice: () => void;
}

export const AiVoiceSettingsModal: React.FC<AiVoiceSettingsModalProps> = ({
  isOpen,
  onClose,
  voiceSettings,
  onUpdateVoiceSettings,
  onTestVoice,
}) => {
  if (!isOpen) return null;

  const voices: Array<{ id: NonNullable<VoiceSettings['voiceId']>; name: string; accent: string; pitch: string; rate: string }> = [
    { id: 'en-GB-SoniaNeural', name: 'Sonia — J.A.R.V.I.S. Pro Elite Female', accent: 'British', pitch: '+2Hz', rate: '+4%' },
    { id: 'en-US-AriaNeural', name: 'Aria — Studio Crisp Female', accent: 'American', pitch: '+0Hz', rate: '+3%' },
    { id: 'en-US-JennyNeural', name: 'Jenny — Warm Student Tutor', accent: 'American', pitch: '+0Hz', rate: '+2%' },
    { id: 'en-GB-RyanNeural', name: 'Ryan — Classic British Male', accent: 'British', pitch: '-4Hz', rate: '+5%' },
  ];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-in fade-in select-none font-mono">
      <div className="w-full max-w-xl rounded-2xl bg-[#090F1E] border border-cyan-900/60 shadow-2xl p-5 flex flex-col gap-4 text-slate-100">
        {/* Header */}
        <div className="flex items-center justify-between pb-3 border-b border-slate-800">
          <div className="flex items-center gap-2">
            <Mic className="w-5 h-5 text-cyan-400" />
            <div>
              <h2 className="text-sm font-bold text-slate-100">AI Voice & Audio Subsystem</h2>
              <p className="text-[11px] text-slate-400">Configure neural persona, speech recognition, and wake-word trigger</p>
            </div>
          </div>
          <button onClick={onClose} className="p-2 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 min-h-[44px] min-w-[44px] flex items-center justify-center">
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* 1. Voice Persona Selection */}
        <div>
          <label className="block text-xs font-bold text-cyan-300 uppercase mb-2">Neural Voice Persona</label>
          <div className="space-y-1.5">
            {voices.map((v) => (
              <button
                key={v.id}
                onClick={() => onUpdateVoiceSettings({ voiceId: v.id })}
                className={`w-full flex items-center justify-between p-2.5 rounded-xl border text-left transition-all ${
                  voiceSettings.voiceId === v.id
                    ? 'bg-cyan-950/40 border-cyan-500/60 text-cyan-200 shadow-[0_0_8px_rgba(0,166,232,0.2)]'
                    : 'bg-slate-900/60 border-slate-800 text-slate-400 hover:border-slate-700'
                }`}
              >
                <div>
                  <div className="text-xs font-bold text-slate-200">{v.name}</div>
                  <div className="text-[10px] text-slate-400">{v.accent} • Pitch: {v.pitch} • Speed: {v.rate}</div>
                </div>
                {voiceSettings.voiceId === v.id && (
                  <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-cyan-500/20 text-cyan-300 border border-cyan-500/40">
                    ACTIVE
                  </span>
                )}
              </button>
            ))}
          </div>
        </div>

        {/* 2. Audio Latency & Sensitivity */}
        <div className="grid grid-cols-2 gap-3 text-xs">
          <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800">
            <div className="flex items-center gap-1.5 font-bold text-slate-300 mb-1">
              <Sparkles className="w-3.5 h-3.5 text-cyan-400" />
              <span>Wake-Word Engine</span>
            </div>
            <div className="text-[10px] text-slate-400">Trigger: &quot;Hey Jarvis&quot;</div>
            <div className="text-[10px] text-emerald-400 font-bold mt-1">Status: ARMED (0.012 RMS gate)</div>
          </div>

          <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800">
            <div className="flex items-center gap-1.5 font-bold text-slate-300 mb-1">
              <Volume2 className="w-3.5 h-3.5 text-cyan-400" />
              <span>STT / TTS Latency</span>
            </div>
            <div className="text-[10px] text-slate-400">Speech-to-Text: ~140ms</div>
            <div className="text-[10px] text-cyan-300 font-bold mt-1">Neural Synthesis: ~220ms</div>
          </div>
        </div>

        {/* Footer */}
        <div className="pt-3 border-t border-slate-800 flex items-center justify-between">
          <button
            onClick={onTestVoice}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold border border-slate-700 transition-colors"
          >
            <Play className="w-3.5 h-3.5 text-cyan-400" />
            <span>Test Sonia Voice</span>
          </button>

          <button
            onClick={onClose}
            className="px-4 py-2 rounded-xl bg-cyan-500/20 hover:bg-cyan-500/30 text-cyan-300 border border-cyan-500/50 text-xs font-bold transition-all"
          >
            Save & Close
          </button>
        </div>
      </div>
    </div>
  );
};
