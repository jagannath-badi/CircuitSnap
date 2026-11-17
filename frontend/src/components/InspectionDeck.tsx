import React, { useRef, useState } from 'react';
import {
  Scan,
  Crosshair,
  Camera,
  Terminal,
  Cpu,
  Calculator,
  Compass,
  Binary,
  RotateCcw,
  X,
  BookOpen,
  FileText,
} from 'lucide-react';

export interface InspectionDeckProps {
  activeDutImage: string | null;
  activeDutName: string | null;
  attachedFile: File | null;
  isLoading: boolean;
  onFileSelect: (file: File) => void;
  onEjectDut: () => void;
  onReplaceDut?: () => void;
  onQuickAction: (prompt: string) => void;
  vaultConceptCount?: number;
}

const QUICK_ACTION_CHIPS = [
  {
    label: 'Laplace & ODEs',
    icon: Calculator,
    accent: 'border-[#00A6E8]/30 hover:border-[#00A6E8]/70 hover:bg-[#00A6E8]/10 text-[#00A6E8]',
    prompt: 'Solve Laplace transform of sin(2*t) and solve 2nd order ODE y\'\' + 4y = 0',
  },
  {
    label: 'SFD, BMD & Soil',
    icon: Compass,
    accent: 'border-amber-500/30 hover:border-amber-500/70 hover:bg-amber-500/10 text-amber-400',
    prompt: 'Calculate SFD and maximum bending moment for simply supported beam L=6m with point load P=20kN at center, and find soil void ratio e for porosity n=0.4',
  },
  {
    label: 'Manning Flow & Bernoulli',
    icon: Compass,
    accent: 'border-emerald-500/30 hover:border-emerald-500/70 hover:bg-emerald-500/10 text-emerald-400',
    prompt: 'Calculate open channel discharge with Manning equation n=0.015 A=2.5m^2 R=0.6m S=0.002, and Bernoulli head loss',
  },
  {
    label: '3-Phase & Control Systems',
    icon: Cpu,
    accent: 'border-[#FF2D95]/30 hover:border-[#FF2D95]/70 hover:bg-[#FF2D95]/10 text-[#FF2D95]',
    prompt: 'Calculate 3-phase real and reactive power for V_L=415V I_L=15A pf=0.85, and 2nd order damping ratio zeta and peak overshoot for wn=10 rad/s',
  },
  {
    label: 'NE555 & Pinouts',
    icon: Cpu,
    accent: 'border-cyan-500/30 hover:border-cyan-500/70 hover:bg-cyan-500/10 text-cyan-300',
    prompt: 'Display NE555 pinout table and calculate astable timing for R1=10k R2=47k C=10uF',
  },
  {
    label: 'FCFS, Subnet & Big-O',
    icon: Binary,
    accent: 'border-purple-500/30 hover:border-purple-500/70 hover:bg-purple-500/10 text-purple-400',
    prompt: 'Simulate FCFS CPU scheduling for burst times [5, 3, 8], subnet 192.168.1.0/24, and explain 3NF vs BCNF',
  },
];

export const InspectionDeck: React.FC<InspectionDeckProps> = ({
  activeDutImage,
  activeDutName,
  attachedFile,
  isLoading,
  onFileSelect,
  onEjectDut,
  onReplaceDut,
  onQuickAction,
  vaultConceptCount,
}) => {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [isDragOver, setIsDragOver] = useState(false);

  const handleTriggerFileInput = () => {
    if (onReplaceDut) {
      onReplaceDut();
    }
    fileInputRef.current?.click();
  };

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      onFileSelect(e.target.files[0]);
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      onFileSelect(e.dataTransfer.files[0]);
    }
  };

  return (
    <section className="w-full min-h-[380px] h-full flex flex-col overflow-hidden bg-slate-950/60 backdrop-blur-2xl border border-white/[0.08] border-t-white/15 rounded-3xl p-4 sm:p-5 shadow-2xl specular-glass flow-bento-card flow-stagger-1">
      {/* Scope Header */}
      <div className="flex items-center justify-between pb-3 border-b border-white/[0.08] flex-shrink-0">
        <div className="flex items-center gap-2">
          <Scan className="w-4 h-4 text-[#00A6E8]" />
          <h2 className="text-xs font-mono font-semibold tracking-wider uppercase text-cyan-200">
            Study & Inspection Deck
          </h2>
        </div>
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-cyan-950/40 border border-cyan-500/30 text-[10px] font-mono text-cyan-300">
            <BookOpen className="w-3 h-3 text-[#00A6E8]" />
            <span>Vault: {vaultConceptCount ?? 10}+ Concepts</span>
          </div>
          <span
            className={`text-[10px] font-mono font-medium px-2 py-0.5 rounded-full border transition-all ${
              activeDutImage
                ? 'bg-[#00A6E8]/20 text-[#00A6E8] border-[#00A6E8]/40 shadow-[0_0_10px_rgba(0,166,232,0.3)] animate-pulse'
                : 'bg-white/[0.03] text-slate-500 border-white/[0.06]'
            }`}
          >
            {activeDutImage ? 'File Ready' : 'Ready'}
          </span>
        </div>
      </div>

      {/* Hidden File Input */}
      <input
        type="file"
        ref={fileInputRef}
        onChange={handleFileInputChange}
        accept="image/jpeg,image/png,image/webp,image/gif,application/pdf,text/plain,text/markdown,.pdf,.txt,.md"
        className="hidden"
      />

      {/* Pinned Optical HUD Scope Viewport */}
      <div className="flex-1 my-3 relative flex flex-col justify-center min-h-[220px] overflow-hidden">
        {activeDutImage ? (
          /* Active Loaded Component Scope with Reticle Overlays & Floating Glass Controls */
          <div className="relative w-full h-full min-h-[240px] rounded-2xl bg-slate-950/80 border border-white/[0.08] flex flex-col items-center justify-center overflow-hidden p-3 group">
            {/* Dual Cerulean / Neon Rose Corner HUD Reticles */}
            <div className="absolute top-2.5 left-2.5 w-3.5 h-3.5 border-t-2 border-l-2 border-[#00A6E8] pointer-events-none z-20 shadow-[0_0_8px_#00A6E8]" />
            <div className="absolute top-2.5 right-2.5 w-3.5 h-3.5 border-t-2 border-r-2 border-[#FF2D95] pointer-events-none z-20 shadow-[0_0_8px_#FF2D95]" />
            <div className="absolute bottom-2.5 left-2.5 w-3.5 h-3.5 border-b-2 border-l-2 border-[#FF2D95] pointer-events-none z-20 shadow-[0_0_8px_#FF2D95]" />
            <div className="absolute bottom-2.5 right-2.5 w-3.5 h-3.5 border-b-2 border-r-2 border-[#00A6E8] pointer-events-none z-20 shadow-[0_0_8px_#00A6E8]" />

            {/* Optical Center Crosshairs overlay */}
            <div className="absolute inset-0 pointer-events-none flex items-center justify-center opacity-25 z-10">
              <Crosshair className="w-14 h-14 text-[#00A6E8]" strokeWidth={1} />
            </div>

            {/* Subtle Vignette Overlay */}
            <div className="absolute inset-0 pointer-events-none shadow-[inset_0_0_40px_rgba(0,0,0,0.6)] z-15" />

            {/* Radar scanner sweep overlay during active diagnosis */}
            {isLoading && (
              <div className="absolute inset-0 pointer-events-none z-25 overflow-hidden rounded-xl">
                {/* Laser scan line sweep */}
                <div className="absolute inset-x-0 h-1 bg-gradient-to-r from-transparent via-cyan-400 to-transparent shadow-[0_0_16px_#22d3ee] animate-radar-sweep" />
                {/* Background radar pulse */}
                <div className="absolute inset-0 bg-cyan-500/5 animate-pulse pointer-events-none" />
                {/* Tactical HUD Scanning Tag */}
                <div className="absolute top-3 left-1/2 -translate-x-1/2 px-2.5 py-0.5 rounded-full bg-slate-950/90 border border-cyan-500/40 text-[10px] font-mono text-cyan-300 font-semibold tracking-widest uppercase flex items-center gap-1.5 shadow-lg">
                  <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-ping" />
                  Scanning circuit...
                </div>
              </div>
            )}

            {/* Component Preview Image or Engineering Document Preview */}
            {activeDutName?.toLowerCase().endsWith('.pdf') ||
            activeDutName?.toLowerCase().endsWith('.txt') ||
            activeDutName?.toLowerCase().endsWith('.md') ? (
              <div className="w-full h-full max-h-60 flex flex-col items-center justify-center p-6 bg-slate-900/60 rounded-xl border border-white/10 relative z-10 text-center">
                <FileText className="w-14 h-14 text-[#00A6E8] mb-2.5 animate-pulse" />
                <span className="text-xs font-mono text-slate-100 font-semibold truncate max-w-[260px]">
                  {activeDutName}
                </span>
                <span className="text-[10px] font-mono text-cyan-400 mt-1 uppercase tracking-wider">
                  Engineering Syllabus / Notes Loaded
                </span>
              </div>
            ) : (
              <img
                src={activeDutImage}
                alt={activeDutName || 'Loaded Component Under Scope'}
                className="max-h-60 sm:max-h-64 w-auto max-w-full object-contain rounded-lg relative z-10 shadow-2xl transition-transform duration-300 group-hover:scale-[1.01]"
              />
            )}

            {/* Top-Right Floating Semi-Transparent Glass Controls */}
            <div className="absolute top-3 right-3 z-30 flex items-center gap-1.5 opacity-90 group-hover:opacity-100 transition-opacity">
              <button
                type="button"
                onClick={handleTriggerFileInput}
                disabled={isLoading}
                className="px-2.5 py-1 rounded-lg bg-slate-900/80 hover:bg-slate-800 backdrop-blur-md border border-white/10 text-slate-200 text-[11px] font-mono transition-all hover:border-cyan-500/40 shadow-sm flex items-center gap-1 tactile-spring"
                title="Replace scope image"
              >
                <RotateCcw className="w-3 h-3 text-cyan-400" />
                Replace
              </button>
              <button
                type="button"
                onClick={onEjectDut}
                disabled={isLoading}
                className="p-1 rounded-lg bg-rose-950/50 hover:bg-rose-900/80 backdrop-blur-md border border-rose-800/40 text-rose-300 transition-all hover:text-white shadow-sm tactile-spring"
                title="Clear photo"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            </div>

            {/* Bottom Telemetry Overlay Badge */}
            <div className="absolute bottom-2.5 inset-x-3 z-30 px-3 py-1.5 rounded-xl bg-slate-950/80 backdrop-blur-md border border-white/[0.08] flex items-center justify-between text-[11px] font-mono">
              <div className="truncate mr-2">
                <span className="text-slate-200 font-medium truncate block max-w-[180px] sm:max-w-[220px]">
                  {activeDutName || 'Active Photo'}
                </span>
                <span className="text-[10px] text-slate-500">
                  {attachedFile
                    ? `${(attachedFile.size / (1024 * 1024)).toFixed(2)} MB • ${attachedFile.type}`
                    : 'Active Photo'}
                </span>
              </div>
              <span className="text-[10px] text-cyan-400/90 uppercase tracking-wider font-semibold">
                Photo Added
              </span>
            </div>
          </div>
        ) : (
          /* Subtle, Functional Standby Target Reticle with Hairline Markers & Clear CTA */
          <div
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            onClick={handleTriggerFileInput}
            className={`w-full h-full min-h-[220px] rounded-xl border border-dashed transition-all duration-300 cursor-pointer flex flex-col items-center justify-center p-6 text-center relative group ${
              isDragOver
                ? 'border-cyan-400 bg-cyan-950/30 shadow-[0_0_24px_rgba(6,182,212,0.18)]'
                : 'border-white/10 hover:border-cyan-500/40 bg-slate-950/30 hover:bg-slate-950/50'
            }`}
          >
            {/* Fine Hairline Corner HUD Reticles */}
            <div className="absolute top-3 left-3 w-3 h-3 border-t border-l border-cyan-400/30 group-hover:border-cyan-400/70 transition-colors pointer-events-none" />
            <div className="absolute top-3 right-3 w-3 h-3 border-t border-r border-cyan-400/30 group-hover:border-cyan-400/70 transition-colors pointer-events-none" />
            <div className="absolute bottom-3 left-3 w-3 h-3 border-b border-l border-cyan-400/30 group-hover:border-cyan-400/70 transition-colors pointer-events-none" />
            <div className="absolute bottom-3 right-3 w-3 h-3 border-b border-r border-cyan-400/30 group-hover:border-cyan-400/70 transition-colors pointer-events-none" />

            {/* Subtle Crosshairs Background */}
            <div className="absolute inset-0 pointer-events-none flex items-center justify-center opacity-10 group-hover:opacity-20 transition-opacity">
              <Crosshair className="w-16 h-16 text-cyan-400" strokeWidth={1} />
            </div>

            {/* Optical Reticle Icon */}
            <div className="w-10 h-10 rounded-xl bg-white/[0.04] border border-white/[0.08] flex items-center justify-center text-cyan-400 group-hover:scale-105 group-hover:border-cyan-400/40 group-hover:text-cyan-300 transition-all mb-2.5 shadow-sm relative z-10">
              <Camera className="w-5 h-5" />
            </div>

            <h3 className="text-xs font-mono font-semibold tracking-wider text-slate-200 group-hover:text-cyan-300 transition-colors uppercase relative z-10">
              Drop circuit photo or lecture notes/PDF
            </h3>
            <p className="text-[11px] text-slate-400 mt-1 max-w-[280px] leading-relaxed relative z-10">
              Upload photos, diagrams, or syllabus notes (.pdf, .txt, .md), or paste with Ctrl+V
            </p>

            <div className="mt-3 flex flex-wrap items-center justify-center gap-2 text-[10px] font-mono text-slate-400 relative z-10">
              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-white/[0.04] border border-white/[0.08]">
                <kbd className="px-1 rounded bg-white/[0.08] text-cyan-300 font-mono text-[9px] border border-white/[0.1]">
                  Ctrl+V
                </kbd>
                <span className="text-slate-300">to paste</span>
              </span>
              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-white/[0.04] border border-white/[0.08]">
                <span className="text-slate-300">Images, PDFs & Notes</span>
              </span>
              <span className="px-2 py-0.5 rounded bg-white/[0.04] border border-white/[0.08] text-slate-400">
                Max 10 MB
              </span>
            </div>
          </div>
        )}
      </div>

      {/* Workbench Quick-Action Chips in Neatly Aligned Grid */}
      <div className="pt-3 border-t border-white/[0.06] flex-shrink-0">
        <div className="flex items-center gap-1.5 mb-2">
          <Terminal className="w-3.5 h-3.5 text-cyan-400" />
          <span className="text-[10px] font-mono uppercase font-semibold tracking-wider text-slate-400">
            Quick Questions
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
          {QUICK_ACTION_CHIPS.map((chip, idx) => {
            const Icon = chip.icon;
            return (
              <button
                key={idx}
                type="button"
                onClick={() => onQuickAction(chip.prompt)}
                className={`rounded-xl px-2.5 py-2 bg-slate-900/50 border transition-all text-xs text-slate-200 font-medium flex items-center gap-2 group text-left tactile-spring shadow-sm ${chip.accent}`}
              >
                <Icon className="w-3.5 h-3.5 flex-shrink-0 transition-transform group-hover:scale-110" />
                <span className="truncate">{chip.label}</span>
              </button>
            );
          })}
        </div>
      </div>
    </section>
  );
};
