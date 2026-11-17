import React, { useEffect, useRef } from 'react';
import { Sparkles, Brain, Radio } from 'lucide-react';

interface AiCoreVisualizerProps {
  voiceState: 'idle' | 'listening' | 'transcribing' | 'speaking';
  cognitiveStep: string | null;
  activeBranch?: string;
  isStreaming?: boolean;
}

export const AiCoreVisualizer: React.FC<AiCoreVisualizerProps> = ({
  voiceState,
  cognitiveStep,
  activeBranch = 'ECE',
  isStreaming = false,
}) => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animId: number;
    let phase = 0;
    const prefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    const render = () => {
      const dpr = window.devicePixelRatio || 1;
      const rect = canvas.getBoundingClientRect();
      const width = Math.max(1, Math.round(rect.width));
      const height = Math.max(1, Math.round(rect.height));

      if (canvas.width !== Math.round(width * dpr) || canvas.height !== Math.round(height * dpr)) {
        canvas.width = Math.round(width * dpr);
        canvas.height = Math.round(height * dpr);
      }

      ctx.save();
      ctx.scale(dpr, dpr);
      ctx.clearRect(0, 0, width, height);

      const numBars = 16;
      const gap = 4;
      const totalGaps = (numBars - 1) * gap;
      const barWidth = Math.max(3, (width - totalGaps) / numBars);

      const isSpeaking = voiceState === 'speaking';
      const isListening = voiceState === 'listening';
      const isTranscribing = voiceState === 'transcribing';

      let barColor = 'rgba(100, 116, 139, 0.45)'; // standby slate
      let shadowColor = 'transparent';

      if (isListening) {
        barColor = '#00A6E8'; // cyan
        shadowColor = 'rgba(0, 166, 232, 0.55)';
      } else if (isSpeaking) {
        barColor = '#10B981'; // emerald
        shadowColor = 'rgba(16, 185, 129, 0.55)';
      } else if (isTranscribing) {
        barColor = '#F59E0B'; // amber
        shadowColor = 'rgba(245, 158, 11, 0.55)';
      } else if (isStreaming) {
        barColor = '#818CF8'; // indigo
        shadowColor = 'rgba(129, 140, 248, 0.55)';
      }

      ctx.fillStyle = barColor;
      if (shadowColor !== 'transparent') {
        ctx.shadowColor = shadowColor;
        ctx.shadowBlur = 6;
      }

      for (let i = 0; i < numBars; i++) {
        let barHeight = 4;
        if (!prefersReduced) {
          if (isSpeaking || isListening) {
            const wave = Math.sin(phase + i * 0.45) * 0.5 + 0.5;
            const wave2 = Math.cos(phase * 0.7 + i * 0.3) * 0.5 + 0.5;
            barHeight = 5 + (height - 8) * (wave * 0.6 + wave2 * 0.4);
          } else if (isStreaming) {
            const wave = Math.sin(phase * 1.5 + i * 0.5) * 0.5 + 0.5;
            barHeight = 4 + (height - 12) * wave * 0.6;
          } else {
            barHeight = 4;
          }
        }

        const x = i * (barWidth + gap);
        const y = (height - barHeight) / 2;
        const radius = Math.min(barWidth / 2, 2);

        ctx.beginPath();
        ctx.roundRect(x, y, barWidth, barHeight, radius);
        ctx.fill();
      }

      ctx.restore();

      if (!prefersReduced) {
        phase += isSpeaking ? 0.12 : isListening ? 0.09 : isStreaming ? 0.06 : 0.02;
        animId = requestAnimationFrame(render);
      }
    };

    animId = requestAnimationFrame(render);
    return () => cancelAnimationFrame(animId);
  }, [voiceState, isStreaming]);

  const getCoreState = () => {
    if (voiceState === 'listening') return { label: 'LISTENING', color: 'cyan', pulse: 'animate-ping' };
    if (voiceState === 'transcribing') return { label: 'TRANSCRIBING', color: 'amber', pulse: 'animate-pulse' };
    if (voiceState === 'speaking') return { label: 'SPEAKING (SONIA)', color: 'emerald', pulse: 'animate-bounce' };
    if (isStreaming || cognitiveStep) return { label: 'THINKING', color: 'indigo', pulse: 'animate-spin' };
    return { label: 'STANDBY', color: 'slate', pulse: '' };
  };

  const state = getCoreState();

  return (
    <div className="relative w-full rounded-2xl bg-gradient-to-b from-[#0B1528] to-[#060D1A] border border-cyan-950/70 p-3 sm:p-4 shadow-xl overflow-hidden font-mono select-none flex-shrink-0 gpu-composited">
      {/* Decorative Arc Reactor Grid */}
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,rgba(0,166,232,0.08)_0,transparent_70%)] pointer-events-none" />

      <div className="relative z-10 flex flex-col md:flex-row items-center justify-between gap-3 sm:gap-4">
        {/* Left: Glowing Radial Core */}
        <div className="flex items-center gap-3 sm:gap-4 w-full md:w-auto">
          <div className="relative flex items-center justify-center w-14 h-14 sm:w-16 sm:h-16 rounded-full bg-slate-950 border border-cyan-500/40 shadow-[0_0_25px_rgba(0,166,232,0.35)] flex-shrink-0">
            {/* Outer Rotating Ring */}
            <div className="absolute inset-1 rounded-full border border-dashed border-cyan-400/50 animate-[spin_12s_linear_infinite]" />
            {/* Inner Ring */}
            <div className="absolute inset-2.5 rounded-full border border-cyan-300/30 animate-[spin_6s_linear_infinite_reverse]" />
            {/* Core Center Orb */}
            <div className={`w-6 h-6 rounded-full flex items-center justify-center transition-colors duration-300 ${
              state.color === 'cyan' ? 'bg-cyan-400 shadow-[0_0_15px_#00A6E8]' :
              state.color === 'amber' ? 'bg-amber-400 shadow-[0_0_15px_#f59e0b]' :
              state.color === 'emerald' ? 'bg-emerald-400 shadow-[0_0_15px_#10b981]' :
              state.color === 'indigo' ? 'bg-indigo-400 shadow-[0_0_15px_#6366f1]' :
              'bg-slate-600'
            }`}>
              <Brain className="w-3.5 h-3.5 text-slate-950" />
            </div>
          </div>

          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-1.5 sm:gap-2 flex-wrap">
              <span className="text-xs font-bold text-slate-100 tracking-wider whitespace-nowrap">MARK 85 ARC REASONER</span>
              <span className="px-1.5 py-0.2 rounded text-[10px] bg-cyan-950 text-cyan-300 border border-cyan-800/40 whitespace-nowrap">
                BRANCH: {activeBranch}
              </span>
            </div>
            <div className="flex items-center gap-2 mt-1">
              <span className={`w-2 h-2 rounded-full flex-shrink-0 ${
                state.color === 'cyan' ? 'bg-cyan-400 animate-pulse' :
                state.color === 'emerald' ? 'bg-emerald-400 animate-ping' :
                state.color === 'amber' ? 'bg-amber-400 animate-pulse' :
                state.color === 'indigo' ? 'bg-indigo-400 animate-spin' :
                'bg-slate-500'
              }`} />
              <span className="text-xs font-bold tracking-widest text-cyan-300 whitespace-nowrap">{state.label}</span>
              <span className="text-[10px] text-slate-500 whitespace-nowrap">• SUB-20ms LATENCY</span>
            </div>
          </div>
        </div>

        {/* Center: 120Hz rAF Waveform Canvas */}
        <div className="flex-1 w-full max-w-xs flex flex-col items-center">
          <div className="h-7 w-full flex items-center justify-center">
            <canvas
              ref={canvasRef}
              className="w-full h-7 rounded-lg"
              style={{ width: '100%', height: '28px' }}
            />
          </div>
          {cognitiveStep ? (
            <div className="text-[11px] text-cyan-300 font-semibold tracking-tight truncate max-w-[280px] flex items-center gap-1.5 animate-pulse mt-1">
              <Sparkles className="w-3 h-3 text-cyan-400 flex-shrink-0" />
              <span>{cognitiveStep}</span>
            </div>
          ) : (
            <div className="text-[10px] text-slate-500 mt-1 flex items-center gap-1">
              <Radio className="w-2.5 h-2.5 text-cyan-400/80 flex-shrink-0" />
              <span className="truncate">Waveform calibrated for Sonia Neural 48kHz</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

