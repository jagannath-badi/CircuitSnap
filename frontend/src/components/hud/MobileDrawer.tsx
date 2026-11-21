import React from 'react';
import { X, Cpu, Archive, Settings, Shield, LogOut, Activity, CheckSquare, Zap, Terminal as TerminalIcon, Mic, Sparkles, BookOpen, GraduationCap, Code2, Search, Trash2, Power, AlertOctagon, Image as ImageIcon, Check } from 'lucide-react';
import type { OperatorUser } from '../../api';
import type { SystemTelemetry, OperationsState } from '../../api';
import type { ModelOption } from '../../api';

interface MobileDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  currentUser: OperatorUser | null;
  onLogout: () => void;
  onOpenVault: () => void;
  onOpenAuth: () => void;
  onOpenSettings: () => void;
  // Extra props for mobile-only controls
  centerView?: 'feed' | 'deck';
  onToggleCenterView?: (view: 'feed' | 'deck') => void;
  activeDutImage?: string | null;
  operations?: OperationsState | null;
  onDecision?: (opId: string, decision: 'approve' | 'decline') => void;
  systemTelemetry?: SystemTelemetry | null;
  isListening?: boolean;
  isSpeaking?: boolean;
  isVoiceEnabled?: boolean;
  onToggleVoice?: () => void;
  onToggleListening?: () => void;
  responseStyle?: string;
  onResponseStyleChange?: (style: string) => void;
  availableModels?: ModelOption[];
  selectedModel?: string;
  onSelectModel?: (modelId: string) => void;
  onSystemScan?: () => void;
  onClearContext?: () => void;
  onEmergencyStop?: () => void;
  onTakeControl?: () => void;
  emergencyStop?: boolean;
  autoApprove?: boolean;
  onToggleAutoApprove?: () => void;
}

const DEMAND_MODES = [
  { id: 'auto', label: 'Auto', icon: Sparkles, desc: 'Adaptive AI balance' },
  { id: 'simple', label: 'Simple', icon: BookOpen, desc: 'Intuitive & plain' },
  { id: 'exam', label: 'Exam Steps', icon: GraduationCap, desc: 'Step-by-step derivation' },
  { id: 'gate', label: 'GATE Trick', icon: Zap, desc: 'Fast shortcut & formula' },
  { id: 'code', label: 'Code', icon: Code2, desc: 'Python, Verilog & MATLAB' },
] as const;

const DEFAULT_MODEL_ROSTER: ModelOption[] = [
  { id: 'jarvis-auto', label: 'Auto (J.A.R.V.I.S. Smart Router)', provider: 'J.A.R.V.I.S. Core', specialty: 'Smart router across all engineering branches', supports_vision: true },
  { id: 'jarvis-math', label: 'J.A.R.V.I.S. Math Engine', provider: 'J.A.R.V.I.S. Core', specialty: 'Symbolic calculus, Laplace, circuits & mechanics math', supports_vision: false },
  { id: 'jarvis-vision', label: 'J.A.R.V.I.S. Optical Vision', provider: 'J.A.R.V.I.S. Core', specialty: 'Scan diagrams, circuits, lab setups & handwritten notes', supports_vision: true },
  { id: 'jarvis-datasheets', label: 'J.A.R.V.I.S. Datasheet Archive', provider: 'J.A.R.V.I.S. Core', specialty: 'IC pinouts, Big-O tables, material & thermo constants', supports_vision: false },
];

export const MobileDrawer: React.FC<MobileDrawerProps> = ({
  isOpen,
  onClose,
  currentUser,
  onLogout,
  onOpenVault,
  onOpenAuth,
  onOpenSettings,
  centerView = 'feed',
  onToggleCenterView,
  activeDutImage,
  operations,
  onDecision,
  systemTelemetry,
  isListening,
  isSpeaking,
  isVoiceEnabled,
  onToggleVoice,
  onToggleListening,
  responseStyle = 'auto',
  onResponseStyleChange,
  availableModels = [],
  selectedModel = 'auto',
  onSelectModel,
  onSystemScan,
  onClearContext,
  onEmergencyStop,
  onTakeControl,
  emergencyStop = false,
  autoApprove = false,
  onToggleAutoApprove,
}) => {
  if (!isOpen) return null;

  const modelsToDisplay = availableModels.length > 0 ? availableModels : DEFAULT_MODEL_ROSTER;
  const isHealthy = systemTelemetry?.all_operational === true;

  return (
    <>
      <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 md:hidden" onClick={onClose} />
      <div className="fixed top-0 left-0 bottom-0 w-[280px] max-w-[82vw] bg-[#090F1E] border-r border-cyan-900/60 shadow-2xl z-50 md:hidden p-4 flex flex-col gap-5 animate-drawer-slide overflow-y-auto diagnostic-feed-scrollbar">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-cyan-400 font-mono font-bold text-sm">
            <Cpu className="w-5 h-5" /> CircuitSnap
          </div>
          <button onClick={onClose} className="p-2 text-slate-400">
            <X className="w-6 h-6" />
          </button>
        </div>

        {/* System Health Summary */}
        <div className="p-3 rounded-xl bg-[#0B132B]/72 border border-sky-400/15 specular-glass shadow-md">
          <div className="flex items-center gap-2 text-xs font-bold tracking-wider text-cyan-300 uppercase mb-2 pb-2 border-b border-slate-800/60">
            <Activity className="w-3.5 h-3.5 text-cyan-400" />
            <span>System Health</span>
          </div>
          <div className="flex items-center gap-3">
            <div className="relative flex items-center justify-center w-3 h-3">
              {isHealthy ? (
                <>
                  <span className="absolute w-4 h-4 rounded-full bg-emerald-400/30 animate-ping pointer-events-none" />
                  <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.9)]" />
                </>
              ) : (
                <span className="w-2.5 h-2.5 rounded-full bg-rose-500 shadow-[0_0_8px_rgba(244,63,94,0.9)]" />
              )}
            </div>
            <span className={`text-xs font-mono uppercase tracking-wider ${isHealthy ? 'text-emerald-400' : 'text-rose-400'}`}>
              {isHealthy ? 'Online' : 'Degraded'}
            </span>
          </div>
        </div>

        {/* View Switcher */}
        <div className="p-3 rounded-xl bg-[#0B132B]/72 border border-sky-400/15 specular-glass shadow-md">
          <div className="text-xs font-bold text-cyan-300 uppercase tracking-wider mb-3 pb-2 border-b border-slate-800/60">
            View Mode
          </div>
          <div className="space-y-2">
            <button
              onClick={() => { onToggleCenterView?.('feed'); onClose(); }}
              className={`w-full flex items-center gap-3 p-3 rounded-lg text-left transition-all ${
                centerView === 'feed'
                  ? 'bg-cyan-500/15 border border-cyan-500/30 text-cyan-300'
                  : 'bg-slate-800/60 hover:bg-slate-800 text-slate-200 hover:border-cyan-500/20 border border-transparent'
              }`}
            >
              <TerminalIcon className="w-5 h-5" />
              <span className="font-mono text-sm">Diagnostic Feed</span>
            </button>
            {onToggleCenterView && (
              <button
                onClick={() => onToggleCenterView('deck')}
                className={`w-full flex items-center gap-3 p-3 rounded-lg text-left transition-all ${
                  centerView === 'deck'
                    ? 'bg-cyan-500/15 border border-cyan-500/30 text-cyan-300'
                    : 'bg-slate-800/60 hover:bg-slate-800 text-slate-200 hover:border-cyan-500/20 border border-transparent'
                }`}
              >
                <ImageIcon className="w-5 h-5" />
                <span className="font-mono text-sm">Optical Scope {activeDutImage && <span className="ml-2 w-1.5 h-1.5 rounded-full bg-cyan-400 animate-pulse" />}</span>
              </button>
            )}
          </div>
        </div>

        {/* Response Style Selector */}
        <div className="p-3 rounded-xl bg-[#0B132B]/72 border border-sky-400/15 specular-glass shadow-md">
          <div className="text-xs font-bold text-cyan-300 uppercase tracking-wider mb-3 pb-2 border-b border-slate-800/60">
            Response Style
          </div>
          <div className="flex flex-wrap gap-1.5">
            {DEMAND_MODES.map((dm) => {
              const Icon = dm.icon;
              const isSelected = responseStyle === dm.id;
              return (
                <button
                  key={dm.id}
                  type="button"
                  onClick={() => onResponseStyleChange?.(dm.id)}
                  title={dm.desc}
                  className={`px-3 py-1.5 rounded-full text-[11px] font-mono flex items-center gap-1.5 border transition-all flow-pill ${
                    isSelected
                      ? 'bg-gradient-to-r from-[#00A6E8]/25 to-[#FF2D95]/20 text-cyan-200 border-[#00A6E8]/60 shadow-[0_0_12px_rgba(0,166,232,0.25)] font-semibold'
                      : 'bg-white/[0.03] text-slate-400 border-white/[0.06] hover:text-slate-200 hover:border-white/20'
                  }`}
                >
                  <Icon className={`w-3.5 h-3.5 ${isSelected ? 'text-[#00A6E8]' : 'text-slate-400'}`} />
                  <span>{dm.label}</span>
                </button>
              );
            })}
          </div>
        </div>

        {/* Voice Controls */}
        {isVoiceEnabled !== undefined && (
          <div className="p-3 rounded-xl bg-[#0B132B]/72 border border-sky-400/15 specular-glass shadow-md">
            <div className="text-xs font-bold text-cyan-300 uppercase tracking-wider mb-3 pb-2 border-b border-slate-800/60">
              Voice Assistant
            </div>
            <button
              type="button"
              onClick={onToggleVoice}
              className={`w-full min-h-[44px] px-3 py-2 rounded-lg flex items-center justify-center gap-2 transition-all tactile-spring text-xs font-mono ${
                isVoiceEnabled
                  ? isListening || isSpeaking
                    ? 'bg-[#FF2D95]/20 text-[#FF2D95] border border-[#FF2D95]/50 animate-pulse-ring-rose'
                    : 'bg-[#00A6E8]/20 text-[#00A6E8] border border-[#00A6E8]/50 shadow-[0_0_12px_rgba(0,166,232,0.3)]'
                  : 'bg-white/[0.03] text-slate-400 hover:text-slate-200 border border-white/[0.08] hover:border-white/20'
              }`}
            >
              {isVoiceEnabled ? (
                <>
                  <span className="relative flex h-2 w-2">
                    <span className={`animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 ${isListening ? 'bg-[#FF2D95]' : 'bg-[#00A6E8]'}`} />
                    <span className={`relative inline-flex rounded-full h-2 w-2 ${isListening ? 'bg-[#FF2D95]' : 'bg-[#00A6E8]'}`} />
                  </span>
                  <Mic className="w-3.5 h-3.5 text-[#00A6E8]" />
                  <span className="font-semibold text-[11px] tracking-wide">
                    {isListening ? 'Listening...' : isSpeaking ? 'Speaking...' : 'Voice On'}
                  </span>
                </>
              ) : (
                <>
                  <Mic className="w-3.5 h-3.5 text-slate-500" />
                  <span className="text-[11px]">Voice Off</span>
                </>
              )}
            </button>
          </div>
        )}

        {/* Quick Actions */}
        <div className="p-3 rounded-xl bg-[#0B132B]/72 border border-sky-400/15 specular-glass shadow-md">
          <div className="text-xs font-bold text-cyan-300 uppercase tracking-wider mb-3 pb-2 border-b border-slate-800/60">
            Quick Actions
          </div>
          <div className="space-y-1.5">
            {onToggleListening && (
              <button
                onClick={onToggleListening}
                className="w-full flex items-center gap-2 p-2.5 min-h-[44px] rounded-lg bg-slate-800/60 hover:bg-cyan-950/40 border border-slate-700/60 hover:border-cyan-500/40 text-xs text-slate-200 hover:text-cyan-300 transition-transform duration-200 ease-[cubic-bezier(0.22,1,0.36,1)] will-change-transform"
              >
                <Mic className="w-3.5 h-3.5 text-cyan-400 flex-shrink-0" />
                <span>Voice Command</span>
              </button>
            )}
            {onSystemScan && (
              <button
                onClick={onSystemScan}
                className="w-full flex items-center gap-2 p-2.5 min-h-[44px] rounded-lg bg-slate-800/60 hover:bg-cyan-950/40 border border-slate-700/60 hover:border-cyan-500/40 text-xs text-slate-200 hover:text-cyan-300 transition-transform duration-200 ease-[cubic-bezier(0.22,1,0.36,1)] will-change-transform"
              >
                <Search className="w-3.5 h-3.5 text-cyan-400 flex-shrink-0" />
                <span>Scan Bench & Vault</span>
              </button>
            )}
            {onClearContext && (
              <button
                onClick={onClearContext}
                className="w-full flex items-center gap-2 p-2.5 min-h-[44px] rounded-lg bg-slate-800/60 hover:bg-rose-950/40 border border-slate-700/60 hover:border-rose-500/40 text-xs text-slate-200 hover:text-rose-300 transition-transform duration-200 ease-[cubic-bezier(0.22,1,0.36,1)] will-change-transform"
              >
                <Trash2 className="w-3.5 h-3.5 text-rose-400 flex-shrink-0" />
                <span>Clear Context</span>
              </button>
            )}
          </div>
        </div>

        {/* Emergency Controls */}
        {onEmergencyStop && (
          <div className="p-3 rounded-xl bg-[#0B132B]/72 border border-sky-400/15 specular-glass shadow-lg space-y-2">
            <div className="text-xs font-bold text-rose-400 uppercase tracking-wider mb-2 pb-2 border-b border-slate-800/60 flex items-center gap-2">
              <AlertOctagon className="w-3.5 h-3.5 text-rose-400" />
              <span>Emergency Controls</span>
            </div>
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
            {onTakeControl && (
              <button
                onClick={onTakeControl}
                className="w-full py-2.5 px-3 min-h-[44px] rounded-xl flex items-center justify-center gap-2 text-xs font-mono font-semibold bg-cyan-950/60 hover:bg-cyan-900 text-cyan-300 border border-cyan-700/60 transition-transform duration-200 ease-[cubic-bezier(0.22,1,0.36,1)] will-change-transform"
              >
                <Power className="w-3.5 h-3.5 text-cyan-400 flex-shrink-0" />
                <span>TAKE MANUAL CONTROL</span>
              </button>
            )}
          </div>
        )}

        {/* Auto-Approve */}
        {onToggleAutoApprove !== undefined && (
          <div className="p-3 rounded-xl bg-[#0B132B]/72 border border-sky-400/15 specular-glass shadow-md">
            <button
              onClick={onToggleAutoApprove}
              className={`w-full flex items-center justify-between gap-1.5 px-3 py-2 min-h-[44px] rounded-lg border text-xs transition-transform duration-200 ease-[cubic-bezier(0.22,1,0.36,1)] will-change-transform ${
                autoApprove
                  ? 'bg-amber-950/60 border-amber-500/50 text-amber-300'
                  : 'bg-slate-900 border-slate-800 text-slate-400 hover:text-slate-200'
              }`}
            >
              <div className="flex items-center gap-1.5">
                {autoApprove ? <CheckSquare className="w-3.5 h-3.5 text-amber-400 flex-shrink-0" /> : <Shield className="w-3.5 h-3.5 flex-shrink-0" />}
                <span className="whitespace-nowrap">Auto-Approve</span>
              </div>
              <span className="whitespace-nowrap"><b className={autoApprove ? 'text-amber-300' : 'text-slate-400'}>{autoApprove ? 'ON' : 'OFF'}</b></span>
            </button>
          </div>
        )}

        {/* Model Selector */}
        <div className="p-3 rounded-xl bg-[#0B132B]/72 border border-sky-400/15 specular-glass shadow-md">
          <div className="text-xs font-bold text-cyan-300 uppercase tracking-wider mb-3 pb-2 border-b border-slate-800/60">
            AI Model
          </div>
          <div className="space-y-1.5 max-h-[250px] overflow-y-auto diagnostic-feed-scrollbar">
            {modelsToDisplay.map((opt) => {
              const isSelected = selectedModel === opt.id;
              return (
                <button
                  key={opt.id}
                  type="button"
                  onClick={() => onSelectModel?.(opt.id)}
                  className={`w-full text-left px-3 py-2 rounded-lg transition-all flex items-start justify-between gap-2.5 tactile-spring ${
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
        </div>

        {/* Pending Approvals (if any) */}
        {operations && operations.approvals && operations.approvals.length > 0 && onDecision && (
          <div className="p-3 rounded-xl bg-[#0B132B]/72 border border-sky-400/15 specular-glass shadow-md flex-shrink-0">
            <div className="flex items-center justify-between pb-2 mb-2 border-b border-cyan-900/50">
              <div className="flex items-center gap-2 text-xs font-bold tracking-wider text-cyan-300 uppercase">
                <Shield className="w-3.5 h-3.5 text-cyan-400" />
                <span>Needs You ({operations.approvals.length})</span>
              </div>
            </div>
            <div className="space-y-2">
              {operations.approvals.map((appr) => (
                <div key={appr.id} className="p-2.5 rounded-lg bg-slate-900/90 border border-cyan-900/60 flex flex-col gap-2">
                  <div>
                    <div className="text-xs font-bold text-slate-100">{appr.title}</div>
                    <div className="text-[11px] text-slate-400 mt-0.5 leading-snug">{appr.description}</div>
                  </div>
                  <div className="flex items-center justify-between pt-1 border-t border-slate-800/80">
                    <span className={`text-[10px] uppercase px-1.5 py-0.2 rounded font-bold ${
                      appr.risk_level === 'high' ? 'text-rose-400 bg-rose-950/50' :
                      appr.risk_level === 'medium' ? 'text-amber-400 bg-amber-950/50' :
                      'text-cyan-400 bg-cyan-950/50'
                    }`}>
                      {appr.risk_level} Impact
                    </span>
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => onDecision(appr.id, 'decline')}
                        className="flex items-center gap-1 px-2.5 py-1 min-h-[44px] rounded bg-slate-800 hover:bg-rose-950/60 text-slate-300 hover:text-rose-300 border border-slate-700 hover:border-rose-600/40 text-xs transition-transform duration-200 ease-[cubic-bezier(0.22,1,0.36,1)] will-change-transform"
                      >
                        <X className="w-3 h-3" />
                        <span>Decline</span>
                      </button>
                      <button
                        onClick={() => onDecision(appr.id, 'approve')}
                        className="flex items-center gap-1 px-2.5 py-1 min-h-[44px] rounded bg-cyan-500/20 hover:bg-cyan-500/30 text-cyan-300 border border-cyan-500/50 text-xs font-bold transition-transform duration-200 ease-[cubic-bezier(0.22,1,0.36,1)] will-change-transform shadow-[0_0_8px_rgba(0,166,232,0.2)]"
                      >
                        <Check className="w-3 h-3" />
                        <span>Approve</span>
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Auth & Settings */}
        <div className="mt-auto pt-5 border-t border-slate-800 flex flex-col gap-2">
          <button onClick={() => { onOpenVault(); onClose(); }} className="flex items-center gap-3 p-3 rounded-lg hover:bg-slate-800 text-slate-200">
            <Archive className="w-5 h-5" /> Saved Sessions
          </button>
          <button onClick={() => { onOpenSettings(); onClose(); }} className="flex items-center gap-3 p-3 rounded-lg hover:bg-slate-800 text-slate-200">
            <Settings className="w-5 h-5" /> Settings
          </button>
          {currentUser ? (
            <button onClick={onLogout} className="flex items-center gap-3 p-3 rounded-lg text-rose-300 hover:bg-rose-950/30">
              <LogOut className="w-5 h-5" /> Sign Out
            </button>
          ) : (
            <button onClick={onOpenAuth} className="flex items-center gap-3 p-3 rounded-lg text-cyan-300 hover:bg-cyan-950/30">
              <Shield className="w-5 h-5" /> Sign In
            </button>
          )}
        </div>
      </div>
    </>
  );
};