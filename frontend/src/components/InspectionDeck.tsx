import React, { useRef, useState } from 'react';
import {
  Scan,
  Crosshair,
  Camera,
  Terminal,
  Palette,
  Cpu,
  Clock,
  Layers,
  AlertTriangle,
  RotateCcw,
  X,
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
}

const QUICK_ACTION_CHIPS = [
  {
    label: 'Decode Color Bands',
    icon: Palette,
    prompt:
      'Decode the color bands on this resistor. State the nominal resistance, tolerance, standard E-series designation, and verification tips.',
  },
  {
    label: 'Op-Amp Pinout & Specs',
    icon: Cpu,
    prompt:
      'Identify this operational amplifier, explain its pinout diagram, maximum ratings, supply rail requirements, and typical negative feedback configuration.',
  },
  {
    label: '555 Timer Astable Calc',
    icon: Clock,
    prompt:
      'Explain the pinout and calculate the timing components (R1, R2, C) for this 555 timer in astable mode.',
  },
  {
    label: 'Identify Package & SMD',
    icon: Layers,
    prompt:
      'Identify the package type (SOIC, QFN, TO-220, etc.), pin pitch, SMD top marking code, and manufacturer specifications for this device.',
  },
  {
    label: 'Troubleshoot Short / Noise',
    icon: AlertTriangle,
    prompt:
      'Analyze this circuit for potential issues: check for ground loop vulnerability, missing decoupling capacitors, polarity inversion, or short circuits.',
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
    <section className="lg:col-span-5 h-full flex flex-col overflow-hidden bg-slate-900/40 backdrop-blur-xl border border-white/[0.08] border-t-white/15 rounded-2xl p-4 sm:p-5 shadow-2xl">
      {/* Scope Header */}
      <div className="flex items-center justify-between pb-3 border-b border-white/[0.08] flex-shrink-0">
        <div className="flex items-center gap-2">
          <Scan className="w-4 h-4 text-cyan-400" />
          <h2 className="text-xs font-mono font-semibold tracking-wider uppercase text-cyan-300">
            OPTICAL INSPECTION SCOPE
          </h2>
        </div>
        <span
          className={`text-[10px] font-mono font-medium px-2.5 py-0.5 rounded-full border transition-all ${
            activeDutImage
              ? 'bg-cyan-950/60 text-cyan-400 border-cyan-800/60 animate-pulse'
              : 'bg-white/[0.03] text-slate-500 border-white/[0.06]'
          }`}
        >
          {activeDutImage ? 'CH 1 // OPTICAL FEED LOCKED' : 'STANDBY // RETICLE READY'}
        </span>
      </div>

      {/* Hidden File Input */}
      <input
        type="file"
        ref={fileInputRef}
        onChange={handleFileInputChange}
        accept="image/jpeg,image/png,image/webp,image/gif"
        className="hidden"
      />

      {/* Pinned Optical HUD Scope Viewport */}
      <div className="flex-1 my-3 relative flex flex-col justify-center min-h-[220px] overflow-hidden">
        {activeDutImage ? (
          /* Active Loaded Component Scope with Reticle Overlays & Floating Glass Controls */
          <div className="relative w-full h-full min-h-[240px] rounded-xl bg-slate-950/60 border border-white/[0.08] flex flex-col items-center justify-center overflow-hidden p-3 group">
            {/* Scope Corner HUD Reticles */}
            <div className="absolute top-2.5 left-2.5 w-3 h-3 border-t-2 border-l-2 border-cyan-400/60 pointer-events-none z-20" />
            <div className="absolute top-2.5 right-2.5 w-3 h-3 border-t-2 border-r-2 border-cyan-400/60 pointer-events-none z-20" />
            <div className="absolute bottom-2.5 left-2.5 w-3 h-3 border-b-2 border-l-2 border-cyan-400/60 pointer-events-none z-20" />
            <div className="absolute bottom-2.5 right-2.5 w-3 h-3 border-b-2 border-r-2 border-cyan-400/60 pointer-events-none z-20" />

            {/* Optical Center Crosshairs overlay */}
            <div className="absolute inset-0 pointer-events-none flex items-center justify-center opacity-25 z-10">
              <Crosshair className="w-14 h-14 text-cyan-400" strokeWidth={1} />
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
                  OPTICAL SPECTRUM SCANNING...
                </div>
              </div>
            )}

            {/* Component Preview Image */}
            <img
              src={activeDutImage}
              alt="Loaded Component Under Scope"
              className="max-h-60 sm:max-h-64 w-auto object-contain rounded-lg relative z-10 shadow-2xl transition-transform duration-300 group-hover:scale-[1.01]"
            />

            {/* Top-Right Floating Semi-Transparent Glass Controls */}
            <div className="absolute top-3 right-3 z-30 flex items-center gap-1.5 opacity-90 group-hover:opacity-100 transition-opacity">
              <button
                type="button"
                onClick={handleTriggerFileInput}
                disabled={isLoading}
                className="px-2.5 py-1 rounded-lg bg-slate-900/80 hover:bg-slate-800 backdrop-blur-md border border-white/10 text-slate-200 text-[11px] font-mono transition-all hover:border-cyan-500/40 shadow-sm flex items-center gap-1 active:scale-95"
                title="Replace scope image"
              >
                <RotateCcw className="w-3 h-3 text-cyan-400" />
                Replace
              </button>
              <button
                type="button"
                onClick={onEjectDut}
                disabled={isLoading}
                className="p-1 rounded-lg bg-rose-950/50 hover:bg-rose-900/80 backdrop-blur-md border border-rose-800/40 text-rose-300 transition-all hover:text-white shadow-sm active:scale-95"
                title="Eject / Clear DUT"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            </div>

            {/* Bottom Telemetry Overlay Badge */}
            <div className="absolute bottom-2.5 inset-x-3 z-30 px-3 py-1.5 rounded-xl bg-slate-950/80 backdrop-blur-md border border-white/[0.08] flex items-center justify-between text-[11px] font-mono">
              <div className="truncate mr-2">
                <span className="text-slate-200 font-medium truncate block max-w-[180px] sm:max-w-[220px]">
                  {activeDutName || 'ACTIVE COMPONENT'}
                </span>
                <span className="text-[10px] text-slate-500">
                  {attachedFile
                    ? `${(attachedFile.size / (1024 * 1024)).toFixed(2)} MB • ${attachedFile.type}`
                    : 'PINNED DUT // ACTIVE CHANNEL'}
                </span>
              </div>
              <span className="text-[10px] text-cyan-400/90 uppercase tracking-wider font-semibold">
                LOCKED
              </span>
            </div>
          </div>
        ) : (
          /* Standby Target Reticle with Drag & Drop & Paste Support */
          <div
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            onClick={handleTriggerFileInput}
            className={`w-full h-full min-h-[220px] rounded-xl border border-dashed transition-all cursor-pointer flex flex-col items-center justify-center p-6 text-center relative group ${
              isDragOver
                ? 'border-cyan-400 bg-cyan-950/20 shadow-[0_0_24px_rgba(6,182,212,0.15)]'
                : 'border-cyan-500/20 hover:border-cyan-500/40 bg-slate-950/20 hover:bg-slate-950/40'
            }`}
          >
            {/* Corner Targets */}
            <div className="absolute top-2.5 left-2.5 w-2.5 h-2.5 border-t border-l border-cyan-500/30 group-hover:border-cyan-400 transition-colors" />
            <div className="absolute top-2.5 right-2.5 w-2.5 h-2.5 border-t border-r border-cyan-500/30 group-hover:border-cyan-400 transition-colors" />
            <div className="absolute bottom-2.5 left-2.5 w-2.5 h-2.5 border-b border-l border-cyan-500/30 group-hover:border-cyan-400 transition-colors" />
            <div className="absolute bottom-2.5 right-2.5 w-2.5 h-2.5 border-b border-r border-cyan-500/30 group-hover:border-cyan-400 transition-colors" />

            {/* Optical Reticle Icon */}
            <div className="w-11 h-11 rounded-xl bg-white/[0.03] border border-white/[0.08] flex items-center justify-center text-cyan-400 group-hover:scale-105 group-hover:border-cyan-400/40 group-hover:text-cyan-300 transition-all mb-3 shadow-sm">
              <Camera className="w-5 h-5" />
            </div>

            <h3 className="text-xs font-mono font-medium tracking-wide text-slate-200 group-hover:text-cyan-300 transition-colors">
              AWAITING OPTICAL FEED
            </h3>
            <p className="text-[11px] text-slate-500 mt-1 max-w-[240px] leading-relaxed">
              Drag & drop schematic or photo, click to browse, or paste directly with{' '}
              <kbd className="px-1.5 py-0.5 rounded bg-white/[0.06] text-cyan-300 font-mono text-[10px] border border-white/[0.08]">
                Ctrl+V
              </kbd>
            </p>

            <div className="mt-3.5 flex items-center gap-1.5 text-[9px] font-mono text-slate-500">
              <span className="px-2 py-0.5 rounded bg-white/[0.03] border border-white/[0.06]">
                JPEG • PNG • WEBP • GIF
              </span>
              <span className="px-2 py-0.5 rounded bg-white/[0.03] border border-white/[0.06]">
                MAX 10 MB
              </span>
            </div>
          </div>
        )}
      </div>

      {/* Workbench Quick-Action Chips */}
      <div className="pt-3 border-t border-white/[0.06] flex-shrink-0">
        <div className="flex items-center gap-1.5 mb-2">
          <Terminal className="w-3.5 h-3.5 text-cyan-400" />
          <span className="text-[10px] font-mono uppercase font-semibold tracking-wider text-slate-400">
            BENCH PRESETS
          </span>
        </div>

        <div className="flex flex-wrap gap-1.5">
          {QUICK_ACTION_CHIPS.map((chip, idx) => {
            const Icon = chip.icon;
            return (
              <button
                key={idx}
                type="button"
                onClick={() => onQuickAction(chip.prompt)}
                className="rounded-xl px-3 py-1.5 bg-white/[0.03] hover:bg-cyan-500/10 border border-white/[0.06] hover:border-cyan-500/30 transition-all text-xs text-slate-300 font-medium flex items-center gap-2 group active:scale-95"
              >
                <Icon className="w-3.5 h-3.5 text-cyan-400 group-hover:text-cyan-300 flex-shrink-0" />
                <span className="truncate">{chip.label}</span>
              </button>
            );
          })}
        </div>
      </div>
    </section>
  );
};
