import React, { useRef } from 'react';
import { Mic, Volume2, VolumeX, Send, Paperclip, Shield, Sparkles, CheckSquare } from 'lucide-react';

interface BottomCommandDockProps {
  inputPrompt: string;
  onInputChange: (val: string) => void;
  onSendMessage: () => void;
  isLoading: boolean;
  isListening: boolean;
  isSpeaking: boolean;
  isVoiceEnabled: boolean;
  onToggleVoiceMode: () => void;
  onToggleListening: () => void;
  autoApprove: boolean;
  onToggleAutoApprove: () => void;
  onAttachClick: () => void;
  attachedFile: File | null;
  onRemoveAttachment: () => void;
  liveTranscript?: string;
  voiceState?: 'idle' | 'listening' | 'transcribing' | 'speaking';
}

export const BottomCommandDock: React.FC<BottomCommandDockProps> = ({
  inputPrompt,
  onInputChange,
  onSendMessage,
  isLoading,
  isListening,
  isSpeaking: _isSpeaking,
  isVoiceEnabled,
  onToggleVoiceMode,
  onToggleListening,
  autoApprove,
  onToggleAutoApprove,
  onAttachClick,
  attachedFile,
  onRemoveAttachment,
  liveTranscript,
  voiceState: _voiceState,
}) => {
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      onSendMessage();
    }
  };

  return (
    <footer className="w-full bg-[#070C18]/95 border-t border-cyan-950/70 p-2 sm:p-3 pb-[calc(0.5rem+env(safe-area-inset-bottom,0px))] sm:pb-[calc(0.75rem+env(safe-area-inset-bottom,0px))] font-mono z-30 select-none flex-shrink-0">
      <div className="max-w-7xl mx-auto flex flex-col gap-2">
        {/* Top Controls Row */}
        <div className="flex flex-wrap items-center justify-between gap-1.5 sm:gap-2 text-xs w-full">
          {/* Voice & Auto-approve Toggles */}
          <div className="flex flex-wrap items-center gap-1.5 sm:gap-2">
            {/* Talk to Jarvis Button */}
            <button
              onClick={onToggleListening}
              className={`flex items-center justify-center gap-1.5 sm:gap-2 px-3 py-2 min-h-[44px] rounded-lg text-xs font-bold transition-transform duration-200 ease-[cubic-bezier(0.22,1,0.36,1)] will-change-transform shadow-md ${
                isListening
                  ? 'bg-rose-600 text-white animate-pulse shadow-[0_0_12px_#e11d48] scale-[1.02]'
                  : 'bg-cyan-500/20 hover:bg-cyan-500/30 text-cyan-300 border border-cyan-500/40 shadow-[0_0_8px_rgba(0,166,232,0.2)]'
              }`}
            >
              {isListening ? <Mic className="w-3.5 h-3.5 animate-bounce flex-shrink-0" /> : <Mic className="w-3.5 h-3.5 flex-shrink-0" />}
              <span className="whitespace-nowrap">{isListening ? 'LISTENING (STOP)' : 'TALK TO JARVIS'}</span>
            </button>

            {/* Speak Responses Toggle */}
            <button
              onClick={onToggleVoiceMode}
              className={`flex items-center justify-center gap-1.5 px-2.5 py-2 min-h-[44px] rounded-lg border text-xs transition-transform duration-200 ease-[cubic-bezier(0.22,1,0.36,1)] will-change-transform ${
                isVoiceEnabled
                  ? 'bg-emerald-950/40 border-emerald-500/40 text-emerald-300'
                  : 'bg-slate-900 border-slate-800 text-slate-400 hover:text-slate-200'
              }`}
              title="Read responses aloud using Sonia British Neural voice"
            >
              {isVoiceEnabled ? <Volume2 className="w-3.5 h-3.5 text-emerald-400 flex-shrink-0" /> : <VolumeX className="w-3.5 h-3.5 flex-shrink-0" />}
              <span className="whitespace-nowrap">{isVoiceEnabled ? 'Sonia Audio ON' : 'Audio Muted'}</span>
            </button>

            {/* Free Hand Hey Jarvis */}
            <div className="hidden sm:flex items-center gap-1.5 px-2.5 py-2 min-h-[44px] rounded-lg bg-slate-900 border border-slate-800 text-[11px] text-slate-400">
              <Sparkles className="w-3 h-3 text-cyan-400 flex-shrink-0" />
              <span className="whitespace-nowrap">Wake-Word: &quot;Hey Jarvis&quot; Active</span>
            </div>
          </div>

          {/* Auto-Approve Safety Switch */}
          <div className="flex items-center gap-2">
            <button
              onClick={onToggleAutoApprove}
              className={`flex items-center justify-center gap-1.5 px-2.5 py-2 min-h-[44px] rounded-lg border text-xs transition-transform duration-200 ease-[cubic-bezier(0.22,1,0.36,1)] will-change-transform ${
                autoApprove
                  ? 'bg-amber-950/60 border-amber-500/50 text-amber-300'
                  : 'bg-slate-900 border-slate-800 text-slate-400 hover:text-slate-200'
              }`}
              title="Automatically approve non-critical background solvers and file operations"
            >
              {autoApprove ? <CheckSquare className="w-3.5 h-3.5 text-amber-400 flex-shrink-0" /> : <Shield className="w-3.5 h-3.5 flex-shrink-0" />}
              <span className="whitespace-nowrap">Auto-Approve: <b className={autoApprove ? 'text-amber-300' : 'text-slate-400'}>{autoApprove ? 'ON' : 'OFF'}</b></span>
            </button>
          </div>
        </div>

        {/* Live Audio Transcript Preview */}
        {liveTranscript && (
          <div className="px-3 py-1.5 rounded bg-cyan-950/40 border border-cyan-800/40 text-cyan-300 text-xs flex items-center gap-2 animate-pulse w-full">
            <span className="w-2 h-2 rounded-full bg-cyan-400 animate-ping flex-shrink-0" />
            <span className="font-semibold text-slate-400 flex-shrink-0">Heard:</span>
            <span className="truncate">&quot;{liveTranscript}&quot;</span>
          </div>
        )}

        {/* Attached File Pill */}
        {attachedFile && (
          <div className="flex items-center gap-2 px-3 py-1 rounded-lg bg-slate-800/80 border border-slate-700 text-xs text-slate-200 w-fit">
            <Paperclip className="w-3.5 h-3.5 text-cyan-400 flex-shrink-0" />
            <span className="truncate max-w-[200px]">{attachedFile.name}</span>
            <button onClick={onRemoveAttachment} className="text-slate-400 hover:text-rose-400 font-bold ml-1 p-1 min-h-[44px] min-w-[44px] flex items-center justify-center">✕</button>
          </div>
        )}

        {/* Input Bar & Actions */}
        <div className="relative flex items-end gap-2 bg-slate-900/90 border border-slate-800 focus-within:border-cyan-500/60 rounded-xl p-1.5 sm:p-2 transition-transform duration-200 ease-[cubic-bezier(0.22,1,0.36,1)] will-change-transform shadow-inner w-full">
          <button
            onClick={onAttachClick}
            className="p-2 min-h-[44px] min-w-[44px] flex items-center justify-center text-slate-400 hover:text-cyan-300 rounded-lg hover:bg-slate-800 transition-transform duration-200 ease-[cubic-bezier(0.22,1,0.36,1)] will-change-transform flex-shrink-0"
            title="Attach diagram, circuit photo, free-body sketch, or PDF notes"
          >
            <Paperclip className="w-4 h-4" />
          </button>

          <textarea
            ref={textareaRef}
            value={inputPrompt}
            onChange={(e) => onInputChange(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={
              isListening
                ? 'Listening to speech... (or type here)'
                : 'Ask anything — derivations, diagrams, mechanics, circuits, code, or lab diagnostics...'
            }
            rows={1}
            className="flex-1 w-full min-w-0 bg-transparent text-slate-100 text-xs sm:text-sm placeholder-slate-500 focus:outline-none resize-none min-h-[40px] max-h-[120px] py-2 font-sans"
          />

          <button
            onClick={onSendMessage}
            disabled={isLoading || (!inputPrompt.trim() && !attachedFile)}
            className="p-2 min-h-[44px] min-w-[44px] flex items-center justify-center rounded-lg bg-cyan-500/20 hover:bg-cyan-500/30 text-cyan-300 border border-cyan-500/50 disabled:opacity-40 disabled:cursor-not-allowed transition-transform duration-200 ease-[cubic-bezier(0.22,1,0.36,1)] will-change-transform shadow-[0_0_8px_rgba(0,166,232,0.2)] flex-shrink-0"
            title="Execute query (Enter)"
          >
            <Send className="w-4 h-4" />
          </button>
        </div>
      </div>
    </footer>
  );
};
