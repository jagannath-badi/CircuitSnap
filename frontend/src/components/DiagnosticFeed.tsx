import React, { useEffect, useRef, useState } from 'react';
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
  BookOpen,
  Calculator,
  Compass,
  Binary,
  Volume2,
  Square,
  GraduationCap,
  Zap,
  Code2,
  BookmarkPlus,
  Check,
  AlertCircle,
} from 'lucide-react';
import type { VoiceState } from '../hooks/useJarvisVoice';

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
  streamingMessageId?: string | null;
  onReadAloud?: (id: string, text: string) => void;
  responseStyle?: string;
  onResponseStyleChange?: (style: string) => void;
  cognitiveStep?: string | null;
  onSaveToVault?: (text: string) => Promise<boolean | void> | boolean | void;
  voiceState?: VoiceState;
  onHardResetVoice?: () => void;
  liveTranscript?: string;
  voiceError?: string | null;
  onClearVoiceError?: () => void;
  hideInput?: boolean;
  mobileFullBleed?: boolean;
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

/**
 * Normalizes prose whitespace and eliminates stray excessive newlines while preserving
 * code blocks and markdown tables intact.
 */
function normalizeProseContent(raw: string): string {
  if (!raw) return '';
  const parts = raw.split(/(```[\s\S]*?```)/g);
  for (let i = 0; i < parts.length; i += 2) {
    let part = parts[i].replace(/\r\n/g, '\n');
    part = part.replace(/\n{3,}/g, '\n\n');
    part = part.replace(/[^\S\n]{3,}/g, ' ');
    parts[i] = part;
  }
  return parts.join('');
}

const markdownComponents: Components = {
  p: ({ children }) => (
    <p className="my-2 text-slate-200 leading-relaxed text-base">{children}</p>
  ),
  li: ({ children }) => (
    <li className="my-1 text-slate-200 leading-relaxed text-base">{children}</li>
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
    <h3 className="text-base font-semibold text-cyan-400 mt-3 mb-1">{children}</h3>
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
    <blockquote className="border-l-2 border-cyan-400/60 pl-3 py-1 my-2 text-slate-300 bg-white/[0.02] rounded-r text-base italic">
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

const DEMAND_MODES = [
  { id: 'auto', label: 'Auto', icon: Sparkles, desc: 'Adaptive AI balance' },
  { id: 'simple', label: 'Simple', icon: BookOpen, desc: 'Intuitive & plain' },
  { id: 'exam', label: 'Exam Steps', icon: GraduationCap, desc: 'Step-by-step derivation' },
  { id: 'gate', label: 'GATE Trick', icon: Zap, desc: 'Fast shortcut & formula' },
  { id: 'code', label: 'Code', icon: Code2, desc: 'Python, Verilog & MATLAB' },
] as const;

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
  streamingMessageId = null,
  onReadAloud,
  responseStyle = 'auto',
  onResponseStyleChange,
  cognitiveStep = null,
  onSaveToVault,
  voiceState = 'idle',
  onHardResetVoice,
  liveTranscript = '',
  voiceError = null,
  onClearVoiceError,
  hideInput = false,
  mobileFullBleed = false,
}) => {
  const scrollContainerRef = useRef<HTMLDivElement>(null);
  const [savedMsgIds, setSavedMsgIds] = useState<Set<string>>(new Set());

  const handleSaveToVault = async (msgId: string, content: string) => {
    if (savedMsgIds.has(msgId)) return;
    try {
      if (onSaveToVault) {
        await onSaveToVault(content);
      }
      setSavedMsgIds((prev) => new Set(prev).add(msgId));
    } catch {
      // ignore
    }
  };

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
    <section className={`flex flex-col h-full min-h-0 overflow-hidden ${mobileFullBleed ? 'border-0 rounded-none bg-transparent shadow-none' : 'rounded-3xl border border-white/10 bg-[#060911]/85 backdrop-blur-2xl specular-glass shadow-2xl flow-bento-card flow-stagger-2'}`}>
      {/* Feed Header (Desktop only) */}
      {!mobileFullBleed && (
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
      )}

      {/* Message Feed Container */}
      <div
        ref={scrollContainerRef}
        className={`flex-1 min-h-0 overflow-y-auto overscroll-contain diagnostic-feed-scrollbar ${
          messages.length === 0
            ? 'flex flex-col'
            : 'p-4 space-y-4'
        }`}
      >
        {messages.length === 0 ? (
          /* Empty Feed State - Glowing J.A.R.V.I.S. Core Emblem & 4 Clickable Starter Cards */
          <div className="flex flex-col items-center justify-center text-center p-4 my-auto max-w-2xl mx-auto">
            {/* Glowing Concentric SVG Arc Core with Cerulean, Electric Violet & Neon Rose */}
            <div className="relative w-12 h-12 flex items-center justify-center mb-3 gpu-composited select-none">
              {/* Outer Pulse */}
              <div className="absolute inset-0 rounded-full border border-[#00A6E8]/20 animate-ping pointer-events-none" />

              {/* Concentric Rotating SVG Arc Rings */}
              <svg className="absolute inset-0 w-12 h-12 pointer-events-none" viewBox="0 0 64 64">
                {/* Outer Cerulean Ring (#00A6E8) - 14s clockwise */}
                <circle
                  cx="32"
                  cy="32"
                  r="28"
                  fill="none"
                  stroke="#00A6E8"
                  strokeWidth="1.5"
                  strokeDasharray="8 6 14 6"
                  strokeOpacity="0.75"
                  className="animate-[spin_14s_linear_infinite] origin-center"
                />
                {/* Middle Electric Violet Ring (#9D4EDD) - 8s counter-clockwise */}
                <circle
                  cx="32"
                  cy="32"
                  r="22"
                  fill="none"
                  stroke="#9D4EDD"
                  strokeWidth="1.5"
                  strokeDasharray="12 8 6 8"
                  strokeOpacity="0.8"
                  className="animate-[spin_8s_linear_infinite_reverse] origin-center"
                />
              </svg>

              {/* Inner Glowing Core (#FF2D95) */}
              <div className="relative w-8 h-8 rounded-full bg-gradient-to-br from-[#00A6E8]/25 via-[#9D4EDD]/30 to-[#FF2D95]/30 border border-[#FF2D95]/60 flex items-center justify-center text-[#00A6E8] shadow-[0_0_20px_rgba(0,166,232,0.4),0_0_12px_rgba(255,45,149,0.35)] animate-jarvis-glow">
                <Sparkles className="w-4 h-4 text-cyan-300 animate-pulse" />
              </div>
            </div>

            <h3 className="text-sm font-bold text-white tracking-wide font-display">
              J.A.R.V.I.S. Multi-Discipline Engineering Core
            </h3>
            <p className="text-[11px] text-slate-400 mt-1 mb-4 leading-relaxed">
              First-principles intelligence for Mathematics, Mechanics, Electronics, Civil, Chemical, and Computing.
            </p>

            {/* Mobile: airy hero + 2 compact quick-prompt pills (desktop keeps full grid) */}
            <div className="md:hidden flex flex-col items-center gap-2 w-full mb-2">
              <p className="text-[10px] text-slate-500 text-center -mt-1 mb-1">
                What circuit or engineering problem are we solving?
              </p>
              <div className="flex flex-row gap-2 w-full">
                <button
                  type="button"
                  onClick={() => onQuickAction?.('Solve Laplace transform of sin(2*t)')}
                  className="flex-1 px-3 py-2 rounded-xl bg-[#0B132B]/72 border border-sky-400/15 specular-glass text-left group"
                >
                  <div className="text-[11px] font-semibold text-slate-200 group-hover:text-cyan-300 whitespace-nowrap">Applied Math</div>
                  <div className="text-[9px] text-slate-400 mt-0.5 leading-snug">Calculus &amp; transforms</div>
                </button>
                <button
                  type="button"
                  onClick={() => onQuickAction?.('Calculate normal stress and strain for F=50kN A=0.001m^2')}
                  className="flex-1 px-3 py-2 rounded-xl bg-[#0B132B]/72 border border-sky-400/15 specular-glass text-left group"
                >
                  <div className="text-[11px] font-semibold text-slate-200 group-hover:text-amber-300 whitespace-nowrap">Mechanics</div>
                  <div className="text-[9px] text-slate-400 mt-0.5 leading-snug">Stress &amp; strain</div>
                </button>
              </div>
            </div>

            {/* Desktop: full multi-discipline starter grid */}
            <div className="hidden md:grid grid-cols-1 sm:grid-cols-2 gap-2 w-full mb-2">
              <button
                type="button"
                onClick={() => onQuickAction?.('Solve Laplace transform of sin(2*t)')}
                className="p-2.5 rounded-xl bg-[#0B132B]/72 border border-sky-400/15 specular-glass hover:-translate-y-0.5 transition-transform duration-200 text-left group shadow-sm"
              >
                <div className="w-6 h-6 rounded-lg bg-[#00A6E8]/20 flex items-center justify-center text-[#00A6E8] mb-1.5 group-hover:scale-110 transition-transform">
                  <Calculator className="w-3.5 h-3.5" />
                </div>
                <div className="text-[11px] font-semibold text-slate-200 group-hover:text-cyan-300 whitespace-nowrap">Applied Mathematics</div>
                <div className="text-[9px] text-slate-400 mt-0.5 leading-snug">Calculus, linear algebra, transforms &amp; ODEs</div>
              </button>

              <button
                type="button"
                onClick={() => onQuickAction?.('Calculate normal stress and strain for F=50kN A=0.001m^2')}
                className="p-2.5 rounded-xl bg-[#0B132B]/72 border border-sky-400/15 specular-glass hover:-translate-y-0.5 transition-transform duration-200 text-left group shadow-sm"
              >
                <div className="w-6 h-6 rounded-lg bg-amber-500/20 flex items-center justify-center text-amber-400 mb-1.5 group-hover:scale-110 transition-transform">
                  <Compass className="w-3.5 h-3.5" />
                </div>
                <div className="text-[11px] font-semibold text-slate-200 group-hover:text-amber-300 whitespace-nowrap">Mechanics &amp; Thermo</div>
                <div className="text-[9px] text-slate-400 mt-0.5 leading-snug">Statics, dynamics, fluids &amp; heat transfer</div>
              </button>

              <button
                type="button"
                onClick={() => onQuickAction?.('Subnet 192.168.1.0/24')}
                className="p-2.5 rounded-xl bg-[#0B132B]/72 border border-sky-400/15 specular-glass hover:-translate-y-0.5 transition-transform duration-200 text-left group shadow-sm"
              >
                <div className="w-6 h-6 rounded-lg bg-purple-500/20 flex items-center justify-center text-purple-400 mb-1.5 group-hover:scale-110 transition-transform">
                  <Binary className="w-3.5 h-3.5" />
                </div>
                <div className="text-[11px] font-semibold text-slate-200 group-hover:text-purple-300 whitespace-nowrap">Computing &amp; Logic</div>
                <div className="text-[9px] text-slate-400 mt-0.5 leading-snug">Algorithms, systems, architecture &amp; digital logic</div>
              </button>

              <button
                type="button"
                onClick={() => onQuickAction?.('NE555 pinout & specs')}
                className="p-2.5 rounded-xl bg-[#0B132B]/72 border border-sky-400/15 specular-glass hover:-translate-y-0.5 transition-transform duration-200 text-left group shadow-sm"
              >
                <div className="w-6 h-6 rounded-lg bg-[#FF2D95]/20 flex items-center justify-center text-[#FF2D95] mb-1.5 group-hover:scale-110 transition-transform">
                  <BookOpen className="w-3.5 h-3.5" />
                </div>
                <div className="text-[11px] font-semibold text-slate-200 group-hover:text-rose-300 whitespace-nowrap">Circuits &amp; Systems</div>
                <div className="text-[9px] text-slate-400 mt-0.5 leading-snug">Networks, signals, control &amp; hardware diagnostics</div>
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
                    <p className="whitespace-pre-wrap break-words overflow-wrap-anywhere text-base leading-relaxed">{msg.content}</p>
                  </>
                ) : (
                  /* Assistant message rendering with KaTeX and Markdown */
                  <div className="text-base break-words">
                    {!msg.content && isLoading ? (
                      <div className="flex items-center gap-2 text-xs font-mono text-cyan-300 py-1">
                        <Loader2 className="w-3.5 h-3.5 animate-spin text-[#00A6E8]" />
                        <span className="flow-shimmer-text">⚡ {cognitiveStep || 'Synthesizing response...'}</span>
                      </div>
                    ) : (
                      <>
                        <ReactMarkdown
                          remarkPlugins={[remarkGfm, remarkMath]}
                          rehypePlugins={[rehypeKatex, rehypeConfidenceBadges]}
                          components={markdownComponents}
                        >
                          {normalizeProseContent(msg.content)}
                        </ReactMarkdown>
                        {isLoading && msg === messages[messages.length - 1] && (
                          <span className="flow-streaming-cursor" />
                        )}
                      </>
                    )}
                  </div>
                )}

                {/* Assistant Engine Metadata Badge with Read Aloud Trigger */}
                {msg.role === 'assistant' && msg.content && !isLoading && (
                  <div className="mt-3 pt-2.5 border-t border-white/[0.08] flex items-center justify-between gap-2 text-[10px] font-mono animate-message-settle">
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
                          speakingMessageId === msg.id || streamingMessageId === msg.id
                            ? 'bg-[#FF2D95]/20 text-[#FF2D95] border-[#FF2D95]/50 animate-pulse'
                            : 'bg-white/[0.04] text-slate-400 hover:text-[#00A6E8] border-white/[0.08] hover:border-[#00A6E8]/40'
                        }`}
                        title={speakingMessageId === msg.id || streamingMessageId === msg.id ? 'Stop audio playback' : 'Read aloud with J.A.R.V.I.S. British voice'}
                      >
                        {speakingMessageId === msg.id || streamingMessageId === msg.id ? (
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

                    {/* Teach / Save to Knowledge Vault Trigger */}
                    {onSaveToVault && (
                      <button
                        type="button"
                        onClick={() => handleSaveToVault(msg.id, msg.content)}
                        className={`flex items-center gap-1 px-2.5 py-0.5 rounded-full border transition-all flow-spring flex-shrink-0 ${
                          savedMsgIds.has(msg.id)
                            ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40'
                            : 'bg-white/[0.04] text-slate-400 hover:text-emerald-300 border-white/[0.08] hover:border-emerald-500/40'
                        }`}
                        title={savedMsgIds.has(msg.id) ? 'Saved to Knowledge Vault' : 'Save concept / solution to Knowledge Vault'}
                      >
                        {savedMsgIds.has(msg.id) ? (
                          <>
                            <Check className="w-2.5 h-2.5 text-emerald-400" />
                            <span className="text-[10px] font-sans">Saved</span>
                          </>
                        ) : (
                          <>
                            <BookmarkPlus className="w-2.5 h-2.5" />
                            <span className="text-[10px] font-sans">Vault</span>
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

        {/* Loading / Cognitive Trace Indicator Bubble (when no active assistant bubble is mounted) */}
        {isLoading && !messages.some((m) => m.role === 'assistant' && !m.content) && (
          <div className="flex justify-start animate-message-settle">
            <div className="rounded-2xl rounded-tl-sm px-4 py-3 bg-slate-900/60 border border-white/[0.1] backdrop-blur-xl flex flex-col gap-1.5 shadow-2xl max-w-[90%]">
              <div className="flex items-center gap-2 text-xs font-mono text-cyan-300">
                <Loader2 className="w-3.5 h-3.5 animate-spin text-[#00A6E8]" />
                <span className="font-semibold text-slate-200">
                  {cognitiveStep ? 'J.A.R.V.I.S. Cognitive Synthesis' : 'Synthesizing response...'}
                </span>
              </div>
              {cognitiveStep && (
                <div className="text-[11px] font-mono flow-shimmer-text flex items-center gap-1.5 pl-5">
                  <span>⚡ {cognitiveStep}</span>
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Footer Input Composer */}
      <div className="flex-shrink-0 p-4 border-t border-white/10 bg-black/20">
        <div className="bg-slate-900/80 backdrop-blur-xl border border-white/10 shadow-[0_8px_32px_rgba(0,0,0,0.4)] rounded-2xl p-2.5 mx-auto max-w-full focus-within:border-cyan-500/50 focus-within:ring-1 focus-within:ring-cyan-500/30 transition-all specular-glass">
          {/* Google Flow Demand Mode Selector Bar (Desktop only) */}
          {!mobileFullBleed && (
            <div className="flex items-center gap-1 mb-2 overflow-x-auto scrollbar-none pb-0.5">
              <span className="text-[10px] font-mono uppercase text-slate-500 mr-1 flex-shrink-0">
                Style:
              </span>
              {DEMAND_MODES.map((dm) => {
                const Icon = dm.icon;
                const isSelected = (responseStyle || 'auto') === dm.id;
                return (
                  <button
                    key={dm.id}
                    type="button"
                    onClick={() => onResponseStyleChange?.(dm.id)}
                    title={dm.desc}
                    className={`px-2.5 py-1 rounded-full text-[11px] font-mono flex items-center gap-1.5 border transition-all flow-pill flex-shrink-0 ${
                      isSelected
                        ? 'bg-gradient-to-r from-[#00A6E8]/25 to-[#FF2D95]/20 text-cyan-200 border-[#00A6E8]/60 shadow-[0_0_12px_rgba(0,166,232,0.25)] font-semibold'
                        : 'bg-white/[0.03] text-slate-400 border-white/[0.06] hover:text-slate-200 hover:border-white/20'
                    }`}
                  >
                    <Icon className={`w-3 h-3 ${isSelected ? 'text-[#00A6E8]' : 'text-slate-400'}`} />
                    <span>{dm.label}</span>
                  </button>
                );
              })}
            </div>
          )}

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

          {/* Active Voice State Live HUD Pill, Error Notice & Interim Transcription Strip */}
          {((voiceState && voiceState !== 'idle') || liveTranscript || voiceError) && (
            <div className="mb-2 space-y-1.5 animate-panel-pop">
              <div className="flex flex-wrap items-center gap-2">
                {voiceState && voiceState !== 'idle' && (
                  <div className="px-3 py-1 rounded-full border border-white/10 bg-slate-950/80 backdrop-blur-md flex items-center justify-between text-xs font-mono w-fit max-w-full shadow-md">
                    {voiceState === 'listening' ? (
                      <div className="flex items-center gap-2 text-[#FF2D95]">
                        <span className="w-2 h-2 rounded-full bg-[#FF2D95] animate-ping" />
                        <span className="font-semibold text-[11px]">Listening... (Speak query)</span>
                      </div>
                    ) : voiceState === 'transcribing' ? (
                      <div className="flex items-center gap-2 text-[#00A6E8]">
                        <Loader2 className="w-3.5 h-3.5 animate-spin text-[#00A6E8]" />
                        <span className="font-semibold text-[11px] flow-shimmer-text">Transcribing neural audio...</span>
                      </div>
                    ) : (
                      <div className="flex items-center gap-2 text-cyan-300">
                        <Volume2 className="w-3.5 h-3.5 animate-pulse text-[#00A6E8]" />
                        <span className="font-semibold text-[11px]">J.A.R.V.I.S. Speaking...</span>
                      </div>
                    )}
                    {onHardResetVoice && (
                      <button
                        type="button"
                        onClick={onHardResetVoice}
                        className="ml-3 px-1.5 py-0.5 rounded-full bg-white/[0.08] hover:bg-rose-500/20 text-slate-400 hover:text-rose-300 text-[10px] transition-colors"
                        title="Stop voice activity & reset engine"
                      >
                        Stop
                      </button>
                    )}
                  </div>
                )}

                {/* Dismissible Voice Error Notice */}
                {voiceError && (
                  <div className="px-3 py-1 rounded-full border border-amber-500/30 bg-amber-950/70 backdrop-blur-md flex items-center gap-2 text-xs font-mono text-amber-200 shadow-sm animate-panel-pop">
                    <AlertCircle className="w-3.5 h-3.5 text-amber-400 flex-shrink-0" />
                    <span className="text-[11px]">{voiceError}</span>
                    {onClearVoiceError && (
                      <button
                        type="button"
                        onClick={onClearVoiceError}
                        className="ml-1 p-0.5 text-amber-400 hover:text-white rounded-full hover:bg-white/10"
                        title="Dismiss notice"
                      >
                        <X className="w-3 h-3" />
                      </button>
                    )}
                  </div>
                )}
              </div>

              {/* Glowing Live Interim Transcription Caption Strip */}
              {liveTranscript && (voiceState === 'listening' || voiceState === 'transcribing') && (
                <div className="px-3 py-1.5 rounded-xl border border-cyan-500/40 bg-cyan-950/50 backdrop-blur-md flex items-center gap-2 text-xs text-cyan-200 shadow-[0_0_15px_rgba(0,166,232,0.15)] animate-pulse">
                  <Sparkles className="w-3.5 h-3.5 text-[#00A6E8] flex-shrink-0" />
                  <span className="font-mono text-[10px] text-cyan-400 uppercase tracking-wider flex-shrink-0 font-bold">
                    Heard:
                  </span>
                  <span className="truncate italic font-sans text-slate-100">"{liveTranscript}"</span>
                </div>
              )}
            </div>
          )}

          {/* Input, Mic & Cerulean Trigger */}
          {!hideInput && (
            <>
              <div className="flex items-end gap-2">
                <button
                  type="button"
                  onClick={onAttachClick}
                  disabled={isLoading}
                  title="Upload Circuit Photo (JPEG, PNG, WEBP, GIF up to 10 MB)"
                  className={`p-2 min-h-[44px] min-w-[44px] flex items-center justify-center rounded-xl border transition-all flex-shrink-0 tactile-spring ${
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
                    className={`p-2 min-h-[44px] min-w-[44px] flex items-center justify-center rounded-xl border transition-all flex-shrink-0 tactile-spring ${
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
                      ? liveTranscript ? `Hearing: "${liveTranscript}"` : 'Listening to speech... Speak clearly'
                      : 'Ask an engineering question or speak to J.A.R.V.I.S...'
                  }
                  rows={1}
                  disabled={isLoading}
                  className="flex-1 bg-transparent resize-none outline-none text-base text-slate-100 placeholder:text-slate-500 max-h-32 py-1.5 px-2 font-sans leading-relaxed"
                />

                {/* Flagship #00A6E8 Cerulean Send Trigger */}
                <button
                  type="button"
                  onClick={onSendMessage}
                  disabled={isLoading || (!inputPrompt.trim() && !attachedFile)}
                  className={`p-2 min-h-[44px] min-w-[44px] rounded-xl font-bold flex-shrink-0 flex items-center justify-center transition-all tactile-spring ${
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
            </>
          )}
        </div>
      </div>
    </section>
  );
};
