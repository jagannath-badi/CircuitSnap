import React from 'react';
import { Check, X, ShieldAlert, Clock, Compass, Layers, CheckCircle } from 'lucide-react';
import type { OperationsState } from '../../api';

interface TasksApprovalsPanelProps {
  operations: OperationsState | null;
  onDecision: (opId: string, decision: 'approve' | 'decline') => void;
  isLoading?: boolean;
}

export const TasksApprovalsPanel: React.FC<TasksApprovalsPanelProps> = ({
  operations,
  onDecision,
  isLoading = false,
}) => {
  const approvals = operations?.approvals ?? [];
  const tasks = operations?.tasks ?? [];
  const recent = operations?.recent_activity ?? [];
  const rightNow = operations?.right_now;

  return (
    <div className="w-full h-full flex flex-col gap-3 font-mono select-none overflow-y-auto pr-1 pb-4">
      {/* 1. "Needs You" Human-in-the-Loop Approval Queue */}
      <div className="p-3.5 rounded-xl bg-cyan-950/20 border border-cyan-500/40 shadow-lg flex-shrink-0 animate-in fade-in">
        <div className="flex items-center justify-between pb-2 mb-2 border-b border-cyan-900/50">
          <div className="flex items-center gap-2 text-xs font-bold tracking-wider text-cyan-300 uppercase">
            <ShieldAlert className="w-3.5 h-3.5 text-cyan-400" />
            <span>Needs You ({approvals.length})</span>
          </div>
          <span className={`text-[10px] px-1.5 py-0.5 rounded border font-mono ${
            approvals.length > 0
              ? 'text-amber-300 bg-amber-950/60 border-amber-600/40'
              : 'text-emerald-400 bg-emerald-950/40 border-emerald-500/30'
          }`}>
            {approvals.length > 0 ? 'PENDING CONFIRMATION' : 'BENCH CLEAR'}
          </span>
        </div>

        {approvals.length > 0 ? (
          <div className="space-y-2.5">
            {approvals.map((appr) => (
              <div
                key={appr.id}
                className="p-2.5 rounded-lg bg-slate-900/90 border border-cyan-900/60 flex flex-col gap-2"
              >
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
                      disabled={isLoading}
                      className="flex items-center gap-1 px-2.5 py-1 min-h-[44px] rounded bg-slate-800 hover:bg-rose-950/60 text-slate-300 hover:text-rose-300 border border-slate-700 hover:border-rose-600/40 text-xs transition-transform duration-200 ease-[cubic-bezier(0.22,1,0.36,1)] will-change-transform"
                    >
                      <X className="w-3 h-3" />
                      <span>Decline</span>
                    </button>
                    <button
                      onClick={() => onDecision(appr.id, 'approve')}
                      disabled={isLoading}
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
        ) : (
          <div className="text-[11px] text-slate-400 py-1 text-center italic">
            Zero pending authorizations. Bench fully autonomous.
          </div>
        )}
      </div>

      {/* 2. "Right Now" Smart Study Recommendation */}
      {rightNow && (
        <div className="p-3.5 rounded-xl bg-slate-900/70 border border-slate-800/80 shadow-md flex-shrink-0">
          <div className="flex items-center gap-2 pb-2 mb-2 border-b border-slate-800/60 text-xs font-bold tracking-wider text-cyan-300 uppercase">
            <Compass className="w-3.5 h-3.5 text-cyan-400" />
            <span>Right Now Recommendation</span>
          </div>
          <div className="text-xs text-slate-200 font-semibold leading-snug">
            {rightNow.recommendation}
          </div>
          <div className="mt-2 flex items-center gap-2 text-[10px] text-slate-400">
            <span className="px-1.5 py-0.5 rounded bg-slate-800 text-slate-300">{rightNow.branch}</span>
            <span>• {rightNow.topic}</span>
          </div>
        </div>
      )}

      {/* 3. Active Background Solvers */}
      <div className="p-3.5 rounded-xl bg-slate-900/70 border border-slate-800/80 shadow-md flex-shrink-0">
        <div className="flex items-center justify-between pb-2 mb-2 border-b border-slate-800/60">
          <div className="flex items-center gap-2 text-xs font-bold tracking-wider text-cyan-300 uppercase">
            <Layers className="w-3.5 h-3.5 text-cyan-400" />
            <span>Active Solvers ({tasks.length})</span>
          </div>
          <span className="text-[10px] text-slate-400">Deterministic</span>
        </div>

        <div className="space-y-3">
          {tasks.map((task) => (
            <div key={task.id} className="text-xs">
              <div className="flex justify-between items-center mb-1">
                <span className="text-slate-200 truncate pr-2 font-semibold text-[11px]">{task.title}</span>
                <span className="text-cyan-400 font-bold text-[11px]">{task.progress}%</span>
              </div>
              <div className="w-full h-1.5 rounded-full bg-slate-800 overflow-hidden">
                <div
                  className="h-full rounded-full bg-cyan-400 transition-transform duration-300 ease-[cubic-bezier(0.22,1,0.36,1)] will-change-transform origin-left w-full"
                  style={{ transform: `scaleX(${Math.max(0.04, task.progress / 100)})` }}
                />
              </div>
              <div className="flex justify-between text-[10px] text-slate-500 mt-1">
                <span>Branch: {task.branch}</span>
                <span>{task.eta_seconds ? `ETA: ${task.eta_seconds}s` : task.status}</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* 4. Recent Completed Activity */}
      {recent.length > 0 && (
        <div className="p-3.5 rounded-xl bg-slate-900/70 border border-slate-800/80 text-xs flex-shrink-0">
          <div className="flex items-center gap-2 pb-2 mb-2 border-b border-slate-800/60 text-xs font-bold tracking-wider text-slate-400 uppercase">
            <Clock className="w-3.5 h-3.5 text-slate-400" />
            <span>Recent Activity</span>
          </div>
          <div className="space-y-1.5">
            {recent.slice(0, 3).map((act) => (
              <div key={act.id} className="flex items-center justify-between text-[11px] text-slate-300">
                <div className="flex items-center gap-1.5 truncate pr-2">
                  <CheckCircle className="w-3 h-3 text-emerald-400 flex-shrink-0" />
                  <span className="truncate">{act.title}</span>
                </div>
                <span className="text-[10px] text-slate-500 flex-shrink-0">{act.timestamp}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
