import React, { useEffect, useRef } from 'react';
import ReactMarkdown, { type Components } from 'react-markdown';
import remarkGfm from 'remark-gfm';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import {
  Layers,
  Sparkles,
  Loader2,
  Image as ImageIcon,
  X,
  Send,
  Mic,
  Zap,
  BookOpen,
  Palette,
  Volume2,
  Square,
} from 'lucide-react';

export interface DisplayMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  imagePreviewUrl?: string;
  metadata?: {
    provider: string;
    model_id: string;
    attempts: number;
    fallback_used: boolean;
    original_model?: string | null;
  };
}

export interface DiagnosticFeedProps {
  messages: DisplayMessage[];
  isLoading: boolean;
  inputPrompt: string;
  onInputChange: (value: string) => void;
  onSendMessage: () => void;
  attachedFile: File | null;
  onRemoveAttachment: () => void;
  onAttachClick: () => void;
  textareaRef?: React.RefObject<HTMLTextAreaElement | null>;
  isVoiceEnabled?: boolean;
  isListening?: boolean;
  isSpeaking?: boolean;
  onToggleListening?: () => void;
  onQuickAction?: (prompt: string) => void;
  speakingMessageId?: string | null;
  onReadAloud?: (id: string, text: string) => void;
}

/**
 * Transforms occurrences of confidence tags into a single clean styled badge at the AST level:
 * - CONFIRMED (with optional [ ], :, or —) -> Emerald badge
 * - LIKELY (with optional [ ], :, or —) -> Amber badge
 * - CANNOT CONFIRM (with optional [ ], :, or —) -> Rose badge
 */
const BADGE_REGEX =
  /((?:\[\s*CANNOT CONFIRM\s*\]|\bCANNOT CONFIRM\b|\[\s*CONFIRMED\s*\]|\bCONFIRMED\b|\[\s*LIKELY\s*\]|\bLIKELY\b)(?:\s*[:—–-])?\s*)/g;

interface HastNode {
  type: string;
  tagName?: string;
  properties?: Record<string, unknown>;
  children?: HastNode[];
  value?: string;
}

function rehypeConfidenceBadges() {
  return (tree: HastNode) => {
    function walk(node: HastNode) {
      if (!node.children || !Array.isArray(node.children)) return;

      // Skip code blocks and KaTeX math nodes
      if (
        node.tagName === 'code' ||
        node.tagName === 'pre' ||
        (node.properties?.className &&
          String(node.properties.className).includes('katex'))
      ) {
        return;
      }

      const nextChildren: HastNode[] = [];
      let prevWasBadge = false;

      for (const child of node.children) {
        if (child.type === 'text' && typeof child.value === 'string') {
          let textVal = child.value;
          if (prevWasBadge) {
            textVal = textVal.replace(/^[\s:—–-]+/, ' ');
          }

          const parts = textVal.split(BADGE_REGEX);
          if (parts.length > 1) {
            for (let i = 0; i < parts.length; i++) {
              const part = parts[i];
              if (!part) continue;

              if (part.includes('CONFIRMED') && !part.includes('CANNOT')) {
                nextChildren.push({
                  type: 'element',
                  tagName: 'span',
                  properties: {
                    className:
                      'inline-flex items-center px-2 py-0.5 rounded text-[11px] font-mono font-bold tracking-wide uppercase mr-1.5 align-middle bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 shadow-[0_0_10px_rgba(16,185,129,0.2)]',
                  },
                  children: [{ type: 'text', value: 'CONFIRMED' }],
                });
                prevWasBadge = true;
              } else if (part.includes('LIKELY')) {
                nextChildren.push({
                  type: 'element',
                  tagName: 'span',
                  properties: {
                    className:
                      'inline-flex items-center px-2 py-0.5 rounded text-[11px] font-mono font-bold tracking-wide uppercase mr-1.5 align-middle bg-amber-500/20 text-amber-300 border border-amber-500/40 shadow-[0_0_10px_rgba(245,158,11,0.2)]',
                  },
                  children: [{ type: 'text', value: 'LIKELY' }],
                });
                prevWasBadge = true;
              } else if (part.includes('CANNOT CONFIRM')) {
                nextChildren.push({
                  type: 'element',
                  tagName: 'span',
                  properties: {
                    className:
                      'inline-flex items-center px-2 py-0.5 rounded text-[11px] font-mono font-bold tracking-wide uppercase mr-1.5 align-middle bg-rose-500/20 text-rose-300 border border-rose-500/40 shadow-[0_0_10px_rgba(244,63,94,0.2)]',
                  },
                  children: [{ type: 'text', value: 'CANNOT CONFIRM' }],
                });
                prevWasBadge = true;
              } else {
                nextChildren.push({ type: 'text', value: part });
                prevWasBadge = false;
              }
            }
          } else {
            nextChildren.push({ ...child, value: textVal });
            prevWasBadge = false;
          }
        } else {
          walk(child);
          nextChildren.push(child);
          prevWasBadge = false;
        }
      }

      node.children = nextChildren;
    }

    walk(tree);
  };
}

const markdownComponents: Components = {
  p: ({ children }) => (
    <p className="my-2 text-slate-200 leading-relaxed text-sm">{children}</p>
  ),
  li: ({ children }) => (
    <li className="my-1 text-slate-200 leading-relaxed text-sm">{children}</li>
  ),
  span: ({ children, className, ...props }) => (
    <span className={className} {...props}>
      {children}
    </span>
  ),
  strong: ({ children }) => (
    <strong className="font-semibold text-slate-100">{children}</strong>
  ),
  em: ({ children }) => (
    <em className="italic text-slate-300">{children}</em>
  ),
  h1: ({ children }) => (
    <h1 className="text-lg font-bold text-cyan-200 mt-4 mb-2">{children}</h1>
  ),
  h2: ({ children }) => (
    <h2 className="text-base font-bold text-cyan-300 mt-3.5 mb-1.5">{children}</h2>
  ),
  h3: ({ children }) => (
    <h3 className="text-sm font-semibold text-cyan-400 mt-3 mb-1">{children}</h3>
  ),
  h4: ({ children }) => (
    <h4 className="text-xs font-semibold text-cyan-400 mt-2 mb-1">{children}</h4>
  ),
  ul: ({ children }) => (
    <ul className="list-disc list-outside space-y-1.5 my-2 ml-5 text-slate-200">{children}</ul>
  ),
  ol: ({ children }) => (
    <ol className="list-decimal list-outside space-y-1.5 my-2 ml-5 text-slate-200">{children}</ol>
  ),
  blockquote: ({ children }) => (
    <blockquote className="border-l-2 border-cyan-400/60 pl-3 py-1 my-2 text-slate-300 bg-white/[0.02] rounded-r text-sm italic">
      {children}
    </blockquote>
  ),
  code: ({ className, children, ...props }) => {
    return (
      <code
        className={
          className ||
          'px-1.5 py-0.5 rounded bg-white/[0.05] text-cyan-300 text-xs font-mono border border-white/[0.08]'
        }
        {...props}
      >
        {children}
      </code>
    );
  },
  pre: ({ children }) => (
    <pre className="p-3 my-2.5 rounded-xl bg-slate-950/80 border border-white/[0.08] overflow-x-auto text-xs font-mono text-cyan-300">
      {children}
    </pre>
  ),
  table: ({ node: _node, ...props }) => (
    <div className="overflow-x-auto my-3">
      <table className="min-w-full border-collapse border border-white/10 text-xs text-left" {...props} />
    </div>
  ),
  thead: ({ node: _node, ...props }) => (
    <thead className="bg-slate-900/90 border-b border-white/15 text-cyan-300 font-mono" {...props} />
  ),
  th: ({ node: _node, ...props }) => (
    <th className="py-2.5 px-3.5 font-semibold border-r border-white/10 last:border-r-0 tracking-wide" {...props} />
  ),
  tbody: ({ node: _node, ...props }) => (
    <tbody className="divide-y divide-white/5" {...props} />
  ),
  tr: ({ node: _node, ...props }) => (
    <tr className="hover:bg-white/[0.03] transition-colors" {...props} />
  ),
  td: ({ node: _node, ...props }) => (
    <td className="py-2 px-3.5 text-slate-300 border-r border-white/5 last:border-r-0 font-sans leading-relaxed" {...props} />
  ),
  a: ({ children, href, ...props }) => (
    <a
      href={href}
      target="_blank"
      rel="noreferrer"
      className="text-cyan-400 hover:text-cyan-300 underline underline-offset-2"
      {...props}
    >
      {children}
    </a>
  ),
  hr: () => <hr className="my-3 border-white/[0.08]" />,
};

export const DiagnosticFeed: React.FC<DiagnosticFeedProps> = ({
  messages,
  isLoading,
  inputPrompt,
  onInputChange,
  onSendMessage,
  attachedFile,
  onRemoveAttachment,
  onAttachClick,
  textareaRef,
  isVoiceEnabled: _isVoiceEnabled = false,
  isListening = false,
  isSpeaking = false,
  onToggleListening,
  onQuickAction,
  speakingMessageId = null,
  onReadAloud,
}) => {
  const scrollContainerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollContainerRef.current) {
      scrollContainerRef.current.scrollTop = scrollContainerRef.current.scrollHeight;
    }
  }, [messages, isLoading]);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      onSendMessage();
    }
  };

  return (
    <section className="flex flex-col h-full min-h-0 overflow-hidden rounded-3xl border border-white/10 bg-[#060911]/85 backdrop-blur-2xl specular-glass shadow-2xl">
      {/* Feed Header */}
      <div className="flex-shrink-0 px-4 py-3 border-b border-white/10 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Layers className="w-4 h-4 text-[#00A6E8]" />
          <h2 className="text-xs font-mono font-semibold tracking-wider uppercase text-cyan-200">
            J.A.R.V.I.S. Assistant
          </h2>
        </div>
        <div className="flex items-center gap-2 text-[10px] font-mono text-slate-400">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-ping" />
          <span>
            {messages.length === 0
              ? 'Ready'
              : `${messages.length} message${messages.length === 1 ? '' : 's'}`}
          </span>
        </div>
      </div>

      {/* Message Feed Container */}
      <div
        ref={scrollContainerRef}
        className={`flex-1 min-h-0 overflow-y-auto p-4 space-y-4 overscroll-contain diagnostic-feed-scrollbar ${
          messages.length === 0
            ? 'flex flex-col items-center justify-center'
            : ''
        }`}
      >
        {messages.length === 0 ? (
          /* Empty Feed State - Glowing J.A.R.V.I.S. Core Emblem & 3 Clickable Starter Cards */
          <div className="flex flex-col items-center justify-center text-center p-6 max-w-lg mx-auto">
            {/* Glowing J.A.R.V.I.S. Core Emblem with Concentric Rings */}
            <div className="relative w-16 h-16 flex items-center justify-center mb-4">
              <div className="absolute inset-0 rounded-full border border-[#00A6E8]/30 animate-ping pointer-events-none" />
              <div className="absolute inset-1 rounded-full border border-dashed border-[#FF2D95]/40 animate-spin [animation-duration:14s]" />
              <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-[#00A6E8]/20 to-[#FF2D95]/20 border border-[#00A6E8]/50 flex items-center justify-center text-[#00A6E8] shadow-[0_0_24px_rgba(0,166,232,0.45)] animate-jarvis-glow">
                <Sparkles className="w-6 h-6 text-[#00A6E8]" />
              </div>
            </div>

            <h3 className="text-base font-bold text-white tracking-wide font-display">
              J.A.R.V.I.S. Electronics Core Online
            </h3>
            <p className="text-xs text-slate-400 mt-1.5 mb-5 leading-relaxed">
              Sub-50ms offline intelligence for ECE pinouts, SymPy circuit math, and optical vision inspection.
            </p>

            {/* 3 Clickable Starter Cards */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 w-full mb-2">
              <button
                type="button"
                onClick={() => onQuickAction?.('NE555 pinout & specs')}
                className="p-3 rounded-2xl bg-slate-900/60 hover:bg-[#00A6E8]/10 border border-[#00A6E8]/30 hover:border-[#00A6E8]/60 text-left transition-all group tactile-spring shadow-sm"
              >
                <div className="w-7 h-7 rounded-lg bg-[#00A6E8]/20 flex items-center justify-center text-[#00A6E8] mb-2 group-hover:scale-110 transition-transform">
                  <BookOpen className="w-4 h-4" />
                </div>
                <div className="text-xs font-semibold text-slate-200 group-hover:text-cyan-300">NE555 Pinout</div>
                <div className="text-[10px] text-slate-400 mt-0.5">8-pin IC connections & specs</div>
              </button>

              <button
                type="button"
                onClick={() => onQuickAction?.('Decode brown black red gold resistor')}
                className="p-3 rounded-2xl bg-slate-900/60 hover:bg-[#FF2D95]/10 border border-[#FF2D95]/30 hover:border-[#FF2D95]/60 text-left transition-all group tactile-spring shadow-sm"
              >
                <div className="w-7 h-7 rounded-lg bg-[#FF2D95]/20 flex items-center justify-center text-[#FF2D95] mb-2 group-hover:scale-110 transition-transform">
                  <Palette className="w-4 h-4" />
                </div>
                <div className="text-xs font-semibold text-slate-200 group-hover:text-rose-300">Decode Resistor</div>
                <div className="text-[10px] text-slate-400 mt-0.5">Color bands & SMD codes</div>
              </button>

              <button
                type="button"
                onClick={() => onQuickAction?.('555 Astable Calc')}
                className="p-3 rounded-2xl bg-slate-900/60 hover:bg-amber-500/10 border border-amber-500/30 hover:border-amber-500/60 text-left transition-all group tactile-spring shadow-sm"
              >
                <div className="w-7 h-7 rounded-lg bg-amber-500/20 flex items-center justify-center text-amber-400 mb-2 group-hover:scale-110 transition-transform">
                  <Zap className="w-4 h-4" />
                </div>
                <div className="text-xs font-semibold text-slate-200 group-hover:text-amber-300">555 Astable Math</div>
                <div className="text-[10px] text-slate-400 mt-0.5">SymPy frequency & duty cycle</div>
              </button>
            </div>
          </div>
        ) : (
          messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex animate-message-settle ${
                msg.role === 'user' ? 'justify-end' : 'justify-start'
              }`}
            >
              <div
                className={`transition-all break-words ${
                  msg.role === 'user'
                    ? 'bg-cyan-950/30 border border-cyan-500/20 text-slate-100 rounded-2xl rounded-tr-sm px-4 py-3 shadow-lg max-w-[85%]'
                    : 'bg-slate-900/50 border border-white/[0.08] text-slate-200 rounded-2xl rounded-tl-sm px-5 py-4 shadow-xl max-w-[92%] sm:max-w-[88%]'
                }`}
              >
                {/* User message rendering */}
                {msg.role === 'user' ? (
                  <>
                    {/* Attached Image Thumbnail with Sleek Smoked Bezel */}
                    {msg.imagePreviewUrl && (
                      <div className="mb-2.5 max-w-xs">
                        <img
                          src={msg.imagePreviewUrl}
                          alt="Uploaded circuit or component"
                          className="bg-black/40 border border-white/10 rounded-xl p-1 max-h-48 object-contain block shadow-md"
                        />
                      </div>
                    )}
                    <p className="whitespace-pre-wrap break-words text-sm leading-relaxed">{msg.content}</p>
                  </>
                ) : (
                  /* Assistant message rendering with KaTeX and Markdown */
                  <div className="text-sm break-words">
                    <ReactMarkdown
                      remarkPlugins={[remarkGfm, remarkMath]}
                      rehypePlugins={[rehypeKatex, rehypeConfidenceBadges]}
                      components={markdownComponents}
                    >
                      {msg.content}
                    </ReactMarkdown>
                  </div>
                )}

                {/* Assistant Engine Metadata Badge with Read Aloud Trigger */}
                {msg.role === 'assistant' && (
                  <div className="mt-3 pt-2.5 border-t border-white/[0.08] flex items-center justify-between gap-2 text-[10px] font-mono">
                    <div className="flex flex-wrap items-center gap-1.5">
                      <span className="px-2.5 py-0.5 rounded-full bg-[#00A6E8]/15 border border-[#00A6E8]/30 text-[#00A6E8] font-medium">
                        {msg.metadata?.provider || 'J.A.R.V.I.S. Core'} / {msg.metadata?.model_id || 'jarvis-auto'}
                      </span>
                      {msg.metadata && (
                        <span className="px-2.5 py-0.5 rounded-full bg-white/[0.05] border border-white/10 text-slate-300 font-medium">
                          {msg.metadata.attempts === 1 ? '1 CYCLE' : `${msg.metadata.attempts} CYCLES`}
                        </span>
                      )}
                      {msg.metadata?.fallback_used && (
                        <span
                          className="px-2.5 py-0.5 rounded-full bg-amber-500/20 text-amber-200 border border-amber-500/40 font-bold"
                          title={msg.metadata.original_model ? `Fallback from ${msg.metadata.original_model}` : 'Fallback Active'}
                        >
                          FALLBACK ACTIVE{msg.metadata.original_model ? ` (${msg.metadata.original_model})` : ''}
                        </span>
                      )}
                    </div>

                    {/* Compact Read Aloud / Stop Trigger */}
                    {onReadAloud && (
                      <button
                        type="button"
                        onClick={() => onReadAloud(msg.id, msg.content)}
                        className={`flex items-center gap-1 px-2.5 py-0.5 rounded-full border transition-all tactile-spring flex-shrink-0 ${
                          speakingMessageId === msg.id
                            ? 'bg-[#FF2D95]/20 text-[#FF2D95] border-[#FF2D95]/50 animate-pulse'
                            : 'bg-white/[0.04] text-slate-400 hover:text-[#00A6E8] border-white/[0.08] hover:border-[#00A6E8]/40'
                        }`}
                        title={speakingMessageId === msg.id ? 'Stop audio playback' : 'Read aloud with J.A.R.V.I.S. British voice'}
                      >
                        {speakingMessageId === msg.id ? (
                          <>
                            <Square className="w-2.5 h-2.5 fill-current" />
                            <span className="text-[10px] font-sans">Stop</span>
                          </>
                        ) : (
                          <>
                            <Volume2 className="w-2.5 h-2.5" />
                            <span className="text-[10px] font-sans">Speak</span>
                          </>
                        )}
                      </button>
                    )}
                  </div>
                )}
              </div>
            </div>
          ))
        )}

        {/* Loading Indicator Bubble */}
        {isLoading && (
          <div className="flex justify-start">
            <div className="rounded-2xl rounded-tl-sm px-4 py-3 bg-slate-900/40 border border-white/[0.07] flex items-center gap-2.5 text-xs font-mono text-cyan-300 shadow-lg">
              <Loader2 className="w-3.5 h-3.5 animate-spin text-cyan-400" />
              <span className="tracking-wide text-slate-300">Analyzing circuit...</span>
            </div>
          </div>
        )}
      </div>

      {/* Footer Input Composer */}
      <div className="flex-shrink-0 p-4 border-t border-white/10 bg-black/20">
        <div className="bg-slate-900/80 backdrop-blur-xl border border-white/10 shadow-[0_8px_32px_rgba(0,0,0,0.4)] rounded-2xl p-2.5 mx-auto max-w-full focus-within:border-cyan-500/50 focus-within:ring-1 focus-within:ring-cyan-500/30 transition-all specular-glass">
          {/* Active Scope Attachment Indicator in Composer */}
          {attachedFile && (
            <div className="mb-2 px-2.5 py-1 rounded-full bg-cyan-950/40 border border-cyan-500/30 flex items-center justify-between text-xs font-mono text-cyan-300 w-fit max-w-full">
              <div className="flex items-center gap-1.5 truncate mr-2">
                <ImageIcon className="w-3.5 h-3.5 text-cyan-400 flex-shrink-0" />
                <span className="truncate text-[11px] text-slate-200">{attachedFile.name}</span>
              </div>
              <button
                type="button"
                onClick={onRemoveAttachment}
                className="text-slate-400 hover:text-white p-0.5 rounded-full hover:bg-white/10 transition-colors flex-shrink-0"
                title="Clear attachment"
              >
                <X className="w-3 h-3" />
              </button>
            </div>
          )}

          {/* Input, Mic & Cerulean Trigger */}
          <div className="flex items-end gap-2">
            <button
              type="button"
              onClick={onAttachClick}
              disabled={isLoading}
              title="Upload Circuit Photo (JPEG, PNG, WEBP, GIF up to 10 MB)"
              className={`p-2 min-h-[40px] min-w-[40px] flex items-center justify-center rounded-xl border transition-all flex-shrink-0 tactile-spring ${
                attachedFile
                  ? 'bg-[#00A6E8]/20 text-[#00A6E8] border-[#00A6E8]/50 shadow-[0_0_12px_rgba(0,166,232,0.3)]'
                  : 'bg-white/[0.03] text-slate-400 border-white/[0.08] hover:text-[#00A6E8] hover:border-[#00A6E8]/40 hover:bg-white/[0.05]'
              }`}
            >
              <ImageIcon className="w-4 h-4" />
            </button>

            {onToggleListening && (
              <button
                type="button"
                onClick={onToggleListening}
                title={isListening ? 'Listening... (Click to stop)' : 'Speak to J.A.R.V.I.S.'}
                className={`p-2 min-h-[40px] min-w-[40px] flex items-center justify-center rounded-xl border transition-all flex-shrink-0 tactile-spring ${
                  isListening
                    ? 'bg-[#FF2D95]/20 text-[#FF2D95] border-[#FF2D95]/60 animate-pulse-ring-rose shadow-[0_0_14px_rgba(255,45,149,0.4)]'
                    : isSpeaking
                    ? 'bg-[#00A6E8]/20 text-[#00A6E8] border-[#00A6E8]/60 animate-pulse-ring-cerulean shadow-[0_0_14px_rgba(0,166,232,0.4)]'
                    : 'bg-white/[0.03] text-slate-400 border-white/[0.08] hover:text-[#00A6E8] hover:border-[#00A6E8]/40 hover:bg-white/[0.05]'
                }`}
              >
                <Mic className="w-4 h-4" />
              </button>
            )}

            <textarea
              ref={textareaRef}
              value={inputPrompt}
              onChange={(e) => onInputChange(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={
                attachedFile
                  ? 'Ask a question about this photo or leave blank to identify...'
                  : isListening
                  ? 'Listening to speech... Speak clearly'
                  : 'Ask a question or speak to J.A.R.V.I.S...'
              }
              rows={1}
              disabled={isLoading}
              className="flex-1 bg-transparent resize-none outline-none text-sm text-slate-100 placeholder:text-slate-500 max-h-32 py-1.5 px-2 font-sans leading-relaxed"
            />

            {/* Flagship #00A6E8 Cerulean Send Trigger */}
            <button
              type="button"
              onClick={onSendMessage}
              disabled={isLoading || (!inputPrompt.trim() && !attachedFile)}
              className={`p-2 min-h-[40px] min-w-[40px] rounded-xl font-bold flex-shrink-0 flex items-center justify-center transition-all tactile-spring ${
                !isLoading && (inputPrompt.trim() || attachedFile)
                  ? 'bg-gradient-to-r from-[#00A6E8] to-[#0284c7] hover:from-[#00A6E8] hover:to-[#38bdf8] text-slate-950 font-bold shadow-[0_0_18px_rgba(0,166,232,0.45)]'
                  : 'bg-[#00A6E8]/10 border border-white/10 text-slate-500 shadow-none cursor-not-allowed'
              }`}
              title="Send message (Enter)"
            >
              {isLoading ? (
                <Loader2 className="w-4 h-4 animate-spin text-[#00A6E8]" />
              ) : (
                <Send className="w-4 h-4" />
              )}
            </button>
          </div>

          {/* Micro Telemetry Bar */}
          <div className="mt-2 pt-1.5 border-t border-white/[0.05] flex items-center justify-between text-[10px] font-mono text-slate-500 px-1">
            <span>Enter: Send • Shift+Enter: Newline • Ctrl+V: Paste</span>
            <span className="text-slate-500">CircuitSnap</span>
          </div>
        </div>
      </div>
    </section>
  );
};
