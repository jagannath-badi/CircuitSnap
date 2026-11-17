import React from 'react';
import { Terminal, Activity, CheckSquare, Zap } from 'lucide-react';

export type MobileHudView = 'core' | 'telemetry' | 'tasks' | 'quick';

interface MobilePanelNavProps {
  currentView: MobileHudView;
  onSelectView: (view: MobileHudView) => void;
  pendingApprovalsCount?: number;
}

export const MobilePanelNav: React.FC<MobilePanelNavProps> = ({
  currentView,
  onSelectView,
  pendingApprovalsCount = 0,
}) => {
  const views: Array<{ id: MobileHudView; label: string; icon: React.ReactNode; badge?: number }> = [
    { id: 'core', label: 'Core & Chat', icon: <Terminal className="w-3.5 h-3.5 flex-shrink-0" /> },
    { id: 'telemetry', label: 'Telemetry', icon: <Activity className="w-3.5 h-3.5 flex-shrink-0" /> },
    { id: 'tasks', label: 'Tasks & Approvals', icon: <CheckSquare className="w-3.5 h-3.5 flex-shrink-0" />, badge: pendingApprovalsCount },
    { id: 'quick', label: 'Quick Actions', icon: <Zap className="w-3.5 h-3.5 flex-shrink-0" /> },
  ];

  return (
    <nav
      aria-label="Mobile HUD Navigation"
      className="lg:hidden flex items-center justify-between gap-1 p-1 mx-2 sm:mx-3 mb-2 rounded-xl bg-slate-900/90 border border-slate-800/80 backdrop-blur-md overflow-x-auto no-scrollbar scroll-smooth select-none flex-shrink-0 z-20"
    >
      {views.map((v) => {
        const isActive = currentView === v.id;
        return (
          <button
            key={v.id}
            onClick={() => onSelectView(v.id)}
            className={`flex-1 min-w-[76px] sm:min-w-[90px] min-h-[44px] flex items-center justify-center gap-1.5 px-2 py-1.5 rounded-lg text-[11px] font-mono transition-transform duration-200 ease-[cubic-bezier(0.22,1,0.36,1)] will-change-transform ${
              isActive
                ? 'bg-cyan-500/20 text-cyan-300 font-bold border border-cyan-500/40 shadow-[0_0_10px_rgba(0,166,232,0.25)] scale-[1.02]'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/40'
            }`}
          >
            {v.icon}
            <span className="whitespace-nowrap">{v.label}</span>
            {v.badge !== undefined && v.badge > 0 && (
              <span className="px-1.5 py-0.2 rounded-full text-[9px] bg-amber-500 text-slate-950 font-bold">
                {v.badge}
              </span>
            )}
          </button>
        );
      })}
    </nav>
  );
};
