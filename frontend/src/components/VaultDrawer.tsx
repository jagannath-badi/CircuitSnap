import React, { useState, useEffect, useCallback, useRef } from 'react';
import {
  X,
  Archive,
  Trash2,
  FolderOpen,
  Loader2,
  Camera,
  MessageSquare,
  BookmarkPlus,
  ShieldAlert,
  Clock,
  UserCheck,
} from 'lucide-react';
import {
  fetchVaultSessions,
  fetchSessionDetail,
  saveCurrentSession,
  deleteVaultSession,
  type SessionSummary,
  type SessionDetail,
  type OperatorUser,
} from '../api';
import type { DisplayMessage } from './DiagnosticFeed';

export interface VaultDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  currentUser: OperatorUser | null;
  currentMessages: DisplayMessage[];
  currentDutImage: string | null;
  onRestoreSession: (session: {
    messages: DisplayMessage[];
    dutImage: string | null;
    sessionId: string;
  }) => void;
  onOpenAuthModal: () => void;
  onSessionsChange?: (count: number) => void;
}

function formatRelativeTime(isoString: string): string {
  try {
    const date = new Date(isoString);
    const now = new Date();
    const diffSec = Math.floor((now.getTime() - date.getTime()) / 1000);
    if (diffSec < 60) return 'Just now';
    const diffMin = Math.floor(diffSec / 60);
    if (diffMin < 60) return `${diffMin}m ago`;
    const diffHr = Math.floor(diffMin / 60);
    if (diffHr < 24) return `${diffHr}h ago`;
    const diffDay = Math.floor(diffHr / 24);
    if (diffDay < 7) return `${diffDay}d ago`;
    return date.toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
  } catch {
    return 'Recent';
  }
}

export const VaultDrawer: React.FC<VaultDrawerProps> = ({
  isOpen,
  onClose,
  currentUser,
  currentMessages,
  currentDutImage,
  onRestoreSession,
  onOpenAuthModal,
  onSessionsChange,
}) => {
  const [sessions, setSessions] = useState<SessionSummary[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [actionSessionId, setActionSessionId] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const drawerRef = useRef<HTMLDivElement>(null);

  const loadSessions = useCallback(async () => {
    if (!currentUser) {
      setSessions([]);
      onSessionsChange?.(0);
      return;
    }
    setIsLoading(true);
    setErrorMessage(null);
    try {
      const data = await fetchVaultSessions();
      setSessions(data);
      onSessionsChange?.(data.length);
    } catch (err: unknown) {
      setErrorMessage(err instanceof Error ? err.message : 'Failed to load archived sessions.');
    } finally {
      setIsLoading(false);
    }
  }, [currentUser, onSessionsChange]);

  useEffect(() => {
    if (!isOpen) return;
    const timer = setTimeout(() => {
      void loadSessions();
    }, 0);
    return () => clearTimeout(timer);
  }, [isOpen, loadSessions]);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  const handleArchiveCurrent = async () => {
    if (!currentUser) {
      onOpenAuthModal();
      return;
    }
    if (currentMessages.length === 0 && !currentDutImage) {
      setErrorMessage('No active session telemetry to archive.');
      return;
    }

    setIsSaving(true);
    setErrorMessage(null);
    try {
      const saved: SessionDetail = await saveCurrentSession({
        dut_image: currentDutImage,
        messages: currentMessages.map((m) => ({
          id: m.id,
          role: m.role,
          content: m.content,
          metadata: m.metadata,
        })),
      });
      await loadSessions();
      setErrorMessage(null);
      // Brief feedback
      setActionSessionId(saved.id);
      setTimeout(() => setActionSessionId(null), 2000);
    } catch (err: unknown) {
      setErrorMessage(err instanceof Error ? err.message : 'Failed to archive run.');
    } finally {
      setIsSaving(false);
    }
  };

  const handleLoadSession = async (sessionSummary: SessionSummary) => {
    setActionSessionId(sessionSummary.id);
    setErrorMessage(null);
    try {
      const detail = await fetchSessionDetail(sessionSummary.id);
      const restoredMessages: DisplayMessage[] = detail.messages.map((m, idx) => ({
        id: m.id || `restored-${idx}-${Date.now()}`,
        role: m.role,
        content: m.content,
        metadata:
          m.metadata?.provider && m.metadata?.model_id
            ? {
                provider: m.metadata.provider,
                model_id: m.metadata.model_id,
                attempts: typeof m.metadata.attempts === 'number' ? m.metadata.attempts : 1,
                fallback_used: Boolean(m.metadata.fallback_used),
              }
            : undefined,
      }));

      onRestoreSession({
        messages: restoredMessages,
        dutImage: detail.dut_image,
        sessionId: detail.id,
      });
      onClose();
    } catch (err: unknown) {
      setErrorMessage(err instanceof Error ? err.message : 'Failed to load session detail.');
    } finally {
      setActionSessionId(null);
    }
  };

  const handleDeleteSession = async (e: React.MouseEvent, sessionId: string) => {
    e.stopPropagation();
    if (!window.confirm('Are you sure you want to delete this archived session?')) {
      return;
    }

    setActionSessionId(sessionId);
    setErrorMessage(null);
    try {
      await deleteVaultSession(sessionId);
      const updated = sessions.filter((s) => s.id !== sessionId);
      setSessions(updated);
      onSessionsChange?.(updated.length);
    } catch (err: unknown) {
      setErrorMessage(err instanceof Error ? err.message : 'Failed to delete session.');
    } finally {
      setActionSessionId(null);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex justify-end">
      {/* Dimmed backdrop */}
      <div
        className="fixed inset-0 bg-black/60 backdrop-blur-xs transition-opacity animate-fade-in"
        onClick={onClose}
      />

      {/* Slide-out Pitch-Carbon Drawer */}
      <div
        ref={drawerRef}
        className="relative z-10 w-full sm:w-[420px] h-full bg-slate-950/95 backdrop-blur-2xl border-l border-white/10 shadow-[0_0_50px_rgba(0,0,0,0.8)] flex flex-col text-slate-100 animate-slide-left"
      >
        {/* Top Header */}
        <div className="px-5 py-4 border-b border-white/[0.08] flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-cyan-500/10 border border-cyan-500/25 flex items-center justify-center text-cyan-400">
              <Archive className="w-4 h-4" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-xs font-mono font-bold tracking-wider uppercase text-cyan-300">
                  DIAGNOSTIC VAULT
                </h2>
                {currentUser && (
                  <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-white/[0.04] border border-white/[0.08] text-slate-400">
                    {sessions.length} RUNS
                  </span>
                )}
              </div>
              <p className="text-[11px] text-slate-400 font-mono">
                ARCHIVED HARDWARE SESSIONS
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            type="button"
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-white/[0.06] transition-colors"
            title="Close Vault"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Content Body */}
        <div className="flex-1 overflow-y-auto p-4 flex flex-col gap-4 diagnostic-feed-scrollbar">
          {errorMessage && (
            <div className="p-2.5 rounded-xl bg-rose-950/60 border border-rose-800/60 text-rose-300 text-xs font-mono flex items-center gap-2">
              <ShieldAlert className="w-4 h-4 text-rose-400 flex-shrink-0" />
              <span className="truncate">{errorMessage}</span>
            </div>
          )}

          {!currentUser ? (
            /* Guest Mode Teaser Card */
            <div className="p-5 rounded-2xl bg-white/[0.02] border border-white/[0.06] flex flex-col items-center text-center gap-3 my-auto">
              <div className="w-12 h-12 rounded-xl bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center text-cyan-400 shadow-[0_0_16px_rgba(6,182,212,0.1)]">
                <UserCheck className="w-6 h-6" />
              </div>
              <div>
                <h3 className="text-xs font-mono font-bold uppercase tracking-wider text-slate-200">
                  GUEST MODE ACTIVE
                </h3>
                <p className="text-[11px] text-slate-400 mt-1 leading-relaxed">
                  Authenticate your station callsign to unlock persistent diagnostic archives, optical scope snapshots, and telemetry history.
                </p>
              </div>
              <button
                type="button"
                onClick={() => {
                  onClose();
                  onOpenAuthModal();
                }}
                className="mt-2 w-full py-2 rounded-xl bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white font-mono text-xs uppercase tracking-wider font-semibold transition-all active:scale-[0.98] shadow-lg shadow-cyan-950/50"
              >
                INITIALIZE OPERATOR PROTOCOL
              </button>
            </div>
          ) : (
            <>
              {/* Archive Current Session Button */}
              <button
                type="button"
                onClick={handleArchiveCurrent}
                disabled={isSaving || (currentMessages.length === 0 && !currentDutImage)}
                className={`w-full p-3 rounded-xl border font-mono text-xs flex items-center justify-between transition-all active:scale-[0.99] ${
                  currentMessages.length > 0 || currentDutImage
                    ? 'bg-cyan-500/10 border-cyan-500/30 text-cyan-300 hover:bg-cyan-500/20 hover:border-cyan-500/50 shadow-[0_0_12px_rgba(6,182,212,0.1)]'
                    : 'bg-white/[0.02] border-white/[0.06] text-slate-500 cursor-not-allowed'
                }`}
                title="Archive current diagnostic workbench session"
              >
                <div className="flex items-center gap-2">
                  {isSaving ? (
                    <Loader2 className="w-4 h-4 animate-spin text-cyan-400" />
                  ) : (
                    <BookmarkPlus className="w-4 h-4 text-cyan-400" />
                  )}
                  <span className="font-semibold uppercase tracking-wider">
                    {isSaving ? 'ARCHIVING SESSION...' : 'ARCHIVE CURRENT RUN'}
                  </span>
                </div>
                <span className="text-[10px] text-slate-400">
                  {currentMessages.length} msgs
                </span>
              </button>

              {/* Sessions List */}
              <div className="flex flex-col gap-2">
                <span className="text-[10px] font-mono text-slate-500 uppercase tracking-wider px-1">
                  STORED TELEMETRY SESSIONS
                </span>

                {isLoading ? (
                  <div className="flex flex-col items-center justify-center py-12 gap-2 text-slate-500 font-mono text-xs">
                    <Loader2 className="w-5 h-5 animate-spin text-cyan-400" />
                    <span>SYNCHRONIZING VAULT...</span>
                  </div>
                ) : sessions.length === 0 ? (
                  <div className="p-8 rounded-2xl bg-white/[0.02] border border-white/[0.04] flex flex-col items-center text-center gap-2.5 my-6">
                    <Archive className="w-8 h-8 text-slate-600" />
                    <span className="text-xs font-mono font-medium text-slate-300 uppercase">
                      VAULT STORAGE EMPTY
                    </span>
                    <p className="text-[11px] text-slate-500 max-w-[240px]">
                      No archived runs found. Submit component queries or optical photos, then click &quot;Archive Current Run&quot;.
                    </p>
                  </div>
                ) : (
                  sessions.map((sess) => {
                    const isBusy = actionSessionId === sess.id;

                    return (
                      <div
                        key={sess.id}
                        onClick={() => handleLoadSession(sess)}
                        className="group p-3 rounded-xl bg-white/[0.02] hover:bg-white/[0.06] border border-white/[0.06] hover:border-cyan-500/40 transition-all cursor-pointer flex flex-col gap-2 relative shadow-sm"
                      >
                        <div className="flex items-start justify-between gap-2">
                          <h4 className="text-xs font-medium text-slate-200 group-hover:text-cyan-300 transition-colors line-clamp-1 font-mono">
                            {sess.title}
                          </h4>
                          <button
                            type="button"
                            onClick={(e) => handleDeleteSession(e, sess.id)}
                            className="text-slate-500 hover:text-rose-400 p-1 rounded hover:bg-white/[0.06] transition-colors"
                            title="Delete Archived Run"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        </div>

                        <div className="flex items-center justify-between text-[10px] font-mono text-slate-400">
                          <div className="flex items-center gap-2">
                            <span className="flex items-center gap-1">
                              <Clock className="w-3 h-3 text-slate-500" />
                              {formatRelativeTime(sess.updated_at)}
                            </span>
                            <span className="flex items-center gap-1 bg-white/[0.04] px-1.5 py-0.5 rounded text-slate-300">
                              <MessageSquare className="w-2.5 h-2.5 text-cyan-400" />
                              {sess.message_count}
                            </span>
                          </div>

                          <div className="flex items-center gap-1.5">
                            {sess.has_dut && (
                              <span className="flex items-center gap-1 text-[9px] font-semibold text-cyan-300 bg-cyan-950/60 border border-cyan-500/30 px-1.5 py-0.5 rounded">
                                <Camera className="w-2.5 h-2.5" />
                                SCOPE
                              </span>
                            )}
                            <span className="text-[10px] text-cyan-400 group-hover:underline flex items-center gap-0.5">
                              {isBusy ? (
                                <Loader2 className="w-3 h-3 animate-spin" />
                              ) : (
                                <>
                                  <FolderOpen className="w-3 h-3" />
                                  <span>LOAD</span>
                                </>
                              )}
                            </span>
                          </div>
                        </div>
                      </div>
                    );
                  })
                )}
              </div>
            </>
          )}
        </div>

        {/* Footer */}
        <div className="p-3 border-t border-white/[0.08] text-[10px] font-mono text-slate-500 flex items-center justify-between">
          <span>CIRCUITSNAP // VAULT CORE</span>
          <span className="text-cyan-400">SQLITE ENCRYPTED</span>
        </div>
      </div>
    </div>
  );
};
