import React, { useState, useRef, useEffect, useCallback } from 'react';
import { X, Lock, User, Loader2, ShieldCheck, AlertCircle } from 'lucide-react';
import { loginOperator, registerOperator, type OperatorUser } from '../api';

export interface AuthModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: (user: OperatorUser) => void;
}

export const AuthModal: React.FC<AuthModalProps> = ({
  isOpen,
  onClose,
  onSuccess,
}) => {
  const [mode, setMode] = useState<'login' | 'register'>('login');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const modalRef = useRef<HTMLDivElement>(null);

  const handleClose = useCallback(() => {
    setUsername('');
    setPassword('');
    setError(null);
    setIsLoading(false);
    onClose();
  }, [onClose]);

  useEffect(() => {
    const handleOutsideClick = (e: MouseEvent) => {
      if (modalRef.current && !modalRef.current.contains(e.target as Node)) {
        handleClose();
      }
    };
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        handleClose();
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleOutsideClick);
      document.addEventListener('keydown', handleKeyDown);
    }
    return () => {
      document.removeEventListener('mousedown', handleOutsideClick);
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [isOpen, handleClose]);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const cleanUser = username.trim();
    if (!cleanUser) {
      setError('Please provide a valid operator username.');
      return;
    }
    if (password.length < 6) {
      setError('Password must contain at least 6 characters.');
      return;
    }

    setError(null);
    setIsLoading(true);

    try {
      const result =
        mode === 'register'
          ? await registerOperator(cleanUser, password)
          : await loginOperator(cleanUser, password);

      onSuccess(result.user);
      handleClose();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Authentication failed.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-fade-in">
      <div
        ref={modalRef}
        className="w-full max-w-sm bg-slate-950/95 backdrop-blur-2xl border border-white/10 rounded-2xl shadow-[0_16px_48px_rgba(0,0,0,0.8)] p-5 sm:p-6 relative flex flex-col gap-4 text-slate-100"
      >
        {/* Top Floating Close Button */}
        <button
          onClick={handleClose}
          type="button"
          className="absolute top-3.5 right-3.5 sm:top-4 sm:right-4 p-2 rounded-lg text-slate-400 hover:text-white hover:bg-white/[0.06] transition-colors min-h-[38px] min-w-[38px] flex items-center justify-center"
          title="Dismiss (Continue as Guest)"
        >
          <X className="w-4 h-4" />
        </button>

        {/* Header Branding */}
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-cyan-500/20 to-blue-600/20 border border-cyan-500/30 flex items-center justify-center text-cyan-400 shadow-[0_0_12px_rgba(6,182,212,0.15)] flex-shrink-0">
            <ShieldCheck className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-xs font-mono font-bold tracking-wider uppercase text-cyan-300">
              OPERATOR PROTOCOL
            </h3>
            <p className="text-[11px] text-slate-400">
              Sign in to anchor diagnostic telemetry to your callsign
            </p>
          </div>
        </div>

        {/* Tab Controls */}
        <div className="grid grid-cols-2 p-1 bg-white/[0.03] border border-white/[0.06] rounded-xl text-xs font-mono">
          <button
            type="button"
            onClick={() => {
              setMode('login');
              setError(null);
            }}
            className={`py-1.5 rounded-lg transition-all ${
              mode === 'login'
                ? 'bg-cyan-500/15 border border-cyan-500/30 text-cyan-300 font-bold shadow-sm'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            LOG IN
          </button>
          <button
            type="button"
            onClick={() => {
              setMode('register');
              setError(null);
            }}
            className={`py-1.5 rounded-lg transition-all ${
              mode === 'register'
                ? 'bg-cyan-500/15 border border-cyan-500/30 text-cyan-300 font-bold shadow-sm'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            REGISTER
          </button>
        </div>

        {/* Form Inputs */}
        <form onSubmit={handleSubmit} className="flex flex-col gap-3">
          <div className="flex flex-col gap-1.5">
            <label className="text-[10px] font-mono uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
              <User className="w-3 h-3 text-cyan-400" />
              <span>Operator Callsign / Username</span>
            </label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="e.g. quantum_cadet"
              required
              className="bg-white/[0.04] border border-white/10 focus:border-cyan-500/50 rounded-xl px-3 py-2 text-xs text-slate-100 placeholder:text-slate-600 focus:outline-none focus:ring-1 focus:ring-cyan-500/30 font-mono transition-all"
            />
          </div>

          <div className="flex flex-col gap-1.5">
            <label className="text-[10px] font-mono uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
              <Lock className="w-3 h-3 text-cyan-400" />
              <span>Security Key / Password</span>
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Minimum 6 characters"
              required
              className="bg-white/[0.04] border border-white/10 focus:border-cyan-500/50 rounded-xl px-3 py-2 text-xs text-slate-100 placeholder:text-slate-600 focus:outline-none focus:ring-1 focus:ring-cyan-500/30 font-mono transition-all"
            />
          </div>

          {error && (
            <div className="p-2.5 rounded-xl bg-rose-950/60 border border-rose-800/60 text-rose-300 text-[11px] font-mono flex items-center gap-2">
              <AlertCircle className="w-3.5 h-3.5 text-rose-400 flex-shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <button
            type="submit"
            disabled={isLoading}
            className="mt-1 py-2 rounded-xl bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white font-mono text-xs uppercase tracking-wider font-semibold shadow-lg shadow-cyan-950/40 transition-all active:scale-[0.98] disabled:opacity-50 flex items-center justify-center gap-2"
          >
            {isLoading ? (
              <>
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
                <span>AUTHORIZING...</span>
              </>
            ) : (
              <span>{mode === 'login' ? 'INITIALIZE SESSION' : 'REGISTER CALLSIGN'}</span>
            )}
          </button>
        </form>

        <p className="text-center text-[10px] text-slate-500 font-mono">
          Workbench is operational in Guest Mode without logging in.
        </p>
      </div>
    </div>
  );
};
