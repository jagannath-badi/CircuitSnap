import React, { useEffect, useRef } from 'react';
import ReactMarkdown, { type Components } from 'react-markdown';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import {
  Layers,
  Sparkles,
  Bot,
  User,
  Loader2,
  Image as ImageIcon,
  X,
  Send,
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
                      'inline-flex items-center px-2 py-0.5 rounded text-[11px] font-mono font-bold tracking-wide uppercase mr-1.5 align-middle bg-emerald-500/15 text-emerald-400 border border-emerald-500/30',
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
                      'inline-flex items-center px-2 py-0.5 rounded text-[11px] font-mono font-bold tracking-wide uppercase mr-1.5 align-middle bg-amber-500/15 text-amber-400 border border-amber-500/30',
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
                      'inline-flex items-center px-2 py-0.5 rounded text-[11px] font-mono font-bold tracking-wide uppercase mr-1.5 align-middle bg-rose-500/15 text-rose-400 border border-rose-500/30',
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
    <p className="my-2 text-slate-200 leading-relaxed">{children}</p>
  ),
  li: ({ children }) => (
    <li className="my-1 text-slate-200 leading-relaxed">{children}</li>
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
    <h1 className="text-xl font-bold text-cyan-200 mt-4 mb-2">{children}</h1>
  ),
  h2: ({ children }) => (
    <h2 className="text-lg font-bold text-cyan-300 mt-3.5 mb-2">{children}</h2>
  ),
  h3: ({ children }) => (
    <h3 className="text-base font-semibold text-cyan-400 mt-3 mb-1.5">{children}</h3>
  ),
  h4: ({ children }) => (
    <h4 className="text-sm font-semibold text-cyan-400 mt-2 mb-1">{children}</h4>
  ),
  ul: ({ children }) => (
    <ul className="list-disc list-outside space-y-1.5 my-2.5 ml-5 text-slate-200">{children}</ul>
  ),
  ol: ({ children }) => (
    <ol className="list-decimal list-outside space-y-1.5 my-2.5 ml-5 text-slate-200">{children}</ol>
  ),
  blockquote: ({ children }) => (
    <blockquote className="border-l-2 border-cyan-500/60 pl-3 py-1 my-2 text-slate-300 bg-slate-900/60 rounded-r text-sm">
      {children}
    </blockquote>
  ),
  code: ({ className, children, ...props }) => {
    return (
      <code
        className={
          className ||
          'px-1.5 py-0.5 rounded bg-slate-800 text-cyan-300 text-xs font-mono border border-slate-700'
        }
        {...props}
      >
        {children}
      </code>
    );
  },
  pre: ({ children }) => (
    <pre className="p-3 my-2.5 rounded-xl bg-slate-950/90 border border-slate-800 overflow-x-auto text-xs font-mono text-cyan-300">
      {children}
    </pre>
  ),
  table: ({ children }) => (
    <div className="overflow-x-auto my-3 rounded-lg border border-slate-800">
      <table className="min-w-full divide-y divide-slate-800 text-xs text-left">
        {children}
      </table>
    </div>
  ),
  th: ({ children }) => (
    <th className="px-3 py-2 bg-slate-900/90 font-semibold text-cyan-300 border-b border-slate-700/80">
      {children}
    </th>
  ),
  td: ({ children }) => (
    <td className="px-3 py-2 border-b border-slate-800/60 text-slate-300">
      {children}
    </td>
  ),
  a: ({ children, href, ...props }) => (
    <a
      href={href}
      target="_blank"
      rel="noreferrer"
      className="text-cyan-400 hover:text-cyan-300 underline"
      {...props}
    >
      {children}
    </a>
  ),
  hr: () => <hr className="my-3 border-slate-800" />,
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
}) => {
  const chatBottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    chatBottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      onSendMessage();
    }
  };

  return (
    <section className="lg:col-span-7 h-full flex flex-col overflow-hidden bg-slate-900/60 border border-white/10 backdrop-blur-md rounded-2xl p-4 sm:p-5 shadow-2xl relative">
      {/* Feed Header */}
      <div className="flex items-center justify-between pb-3 border-b border-white/10 flex-shrink-0">
        <div className="flex items-center gap-2">
          <Layers className="w-4 h-4 text-cyan-400" />
          <h2 className="text-xs font-mono font-bold tracking-wider uppercase text-cyan-300">
            DIAGNOSTIC LOG & ANALYSIS FEED
          </h2>
        </div>
        <div className="flex items-center gap-2 text-[10px] font-mono text-slate-400">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-ping" />
          <span>
            {messages.length === 0
              ? 'STREAM READY'
              : `${messages.length} RECORD${messages.length === 1 ? '' : 'S'} IN BUFFER`}
          </span>
        </div>
      </div>

      {/* Height-Locked Scrollable Message Log */}
      <div className="flex-1 overflow-y-auto space-y-4 my-3 pr-1 diagnostic-feed-scrollbar">
        {messages.length === 0 ? (
          /* Empty Feed State */
          <div className="h-full min-h-[300px] flex flex-col items-center justify-center text-center p-6">
            <div className="w-14 h-14 rounded-2xl bg-cyan-950/60 border border-cyan-800/60 flex items-center justify-center text-cyan-400 shadow-xl shadow-cyan-950/50 mb-3">
              <Sparkles className="w-7 h-7" />
            </div>
            <h3 className="text-base font-mono font-bold text-slate-100 tracking-wide">
              CIRCUITSNAP DIAGNOSTIC ENGINE STANDBY
            </h3>
            <p className="text-xs text-slate-400 max-w-sm mt-1 mb-4 leading-relaxed">
              Select a Quick-Action chip on the left, attach an optical inspection photo, or input an
              electronics query below.
            </p>
            <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-950/80 border border-white/5 text-[11px] font-mono text-slate-400">
              <span className="text-cyan-400 font-bold">MODE:</span>
              <span>Multi-turn ECE Verification & KaTeX Analysis</span>
            </div>
          </div>
        ) : (
          messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex gap-3 ${
                msg.role === 'user' ? 'justify-end' : 'justify-start'
              }`}
            >
              {msg.role === 'assistant' && (
                <div className="w-8 h-8 rounded-lg bg-cyan-950 border border-cyan-800/80 text-cyan-400 flex items-center justify-center flex-shrink-0 mt-1 shadow-sm">
                  <Bot className="w-4 h-4" />
                </div>
              )}

              <div
                className={`max-w-[90%] sm:max-w-[85%] rounded-2xl p-4 shadow-md transition-all ${
                  msg.role === 'user'
                    ? 'bg-cyan-950/40 border border-cyan-800/50 text-cyan-100 shadow-[0_4px_20px_rgba(6,182,212,0.1)] rounded-tr-none'
                    : 'bg-slate-950/90 border border-slate-800/90 text-slate-200 rounded-tl-none'
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
                          className="bg-slate-950/80 border border-white/10 rounded-lg p-1 max-h-48 object-contain block shadow-md"
                        />
                      </div>
                    )}
                    <p className="whitespace-pre-wrap text-sm leading-relaxed">{msg.content}</p>
                  </>
                ) : (
                  /* Assistant message rendering with KaTeX and Markdown */
                  <div className="text-sm">
                    <ReactMarkdown
                      remarkPlugins={[remarkMath]}
                      rehypePlugins={[rehypeKatex, rehypeConfidenceBadges]}
                      components={markdownComponents}
                    >
                      {msg.content}
                    </ReactMarkdown>
                  </div>
                )}

                {/* Assistant Engine Metadata Badge */}
                {msg.metadata && (
                  <div className="mt-3 pt-2.5 border-t border-slate-800 flex flex-wrap items-center gap-2 text-[10px] font-mono text-slate-400">
                    <span className="px-2 py-0.5 rounded bg-slate-900 border border-slate-700/80 text-cyan-300">
                      {msg.metadata.provider} / {msg.metadata.model_id}
                    </span>
                    <span className="px-1.5 py-0.5 rounded bg-slate-900 border border-slate-700/40">
                      {msg.metadata.attempts === 1 ? '1 CYCLE' : `${msg.metadata.attempts} CYCLES`}
                    </span>
                    {msg.metadata.fallback_used && (
                      <span className="px-2 py-0.5 rounded bg-amber-950/60 text-amber-300 border border-amber-800/60 font-bold">
                        FALLBACK ACTIVE
                      </span>
                    )}
                  </div>
                )}
              </div>

              {msg.role === 'user' && (
                <div className="w-8 h-8 rounded-lg bg-cyan-950/70 border border-cyan-800/60 text-cyan-300 flex items-center justify-center flex-shrink-0 mt-1 shadow-sm">
                  <User className="w-4 h-4" />
                </div>
              )}
            </div>
          ))
        )}

        {/* Loading Indicator Bubble */}
        {isLoading && (
          <div className="flex gap-3 justify-start">
            <div className="w-8 h-8 rounded-lg bg-cyan-950 border border-cyan-800/80 text-cyan-400 flex items-center justify-center flex-shrink-0 mt-1 animate-pulse">
              <Bot className="w-4 h-4" />
            </div>
            <div className="rounded-2xl rounded-tl-none p-4 bg-slate-950/90 border border-slate-800 flex items-center gap-3 text-xs font-mono text-cyan-300 shadow-md">
              <Loader2 className="w-4 h-4 animate-spin text-cyan-400" />
              <span>[DIAGNOSTIC ENGINE ACTIVE]: PROCESSING HARDWARE TELEMETRY...</span>
            </div>
          </div>
        )}

        <div ref={chatBottomRef} />
      </div>

      {/* Floating Composer Pinned at Bottom of Column B */}
      <div className="pt-2 flex-shrink-0">
        <div className="bg-slate-950/90 border border-white/10 rounded-xl p-2.5 shadow-xl">
          {/* Active Scope Attachment Indicator in Composer */}
          {attachedFile && (
            <div className="mb-2 px-2.5 py-1 rounded-lg bg-cyan-950/60 border border-cyan-800/50 flex items-center justify-between text-xs font-mono text-cyan-300">
              <div className="flex items-center gap-2 truncate">
                <ImageIcon className="w-3.5 h-3.5 text-cyan-400 flex-shrink-0" />
                <span className="truncate">
                  OPTICAL SCOPE TARGET: <strong className="text-white">{attachedFile.name}</strong>
                </span>
              </div>
              <button
                type="button"
                onClick={onRemoveAttachment}
                className="text-slate-400 hover:text-white p-0.5 rounded transition-colors ml-2"
                title="Clear optical target"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            </div>
          )}

          {/* Input & Phosphor Emerald Trigger */}
          <div className="flex items-end gap-2">
            <button
              type="button"
              onClick={onAttachClick}
              disabled={isLoading}
              title="Load Photo to Optical Scope (JPEG, PNG, WEBP, GIF up to 10 MB)"
              className={`p-2.5 rounded-xl border transition-colors flex-shrink-0 ${
                attachedFile
                  ? 'bg-cyan-950 text-cyan-300 border-cyan-700'
                  : 'bg-slate-900 text-slate-400 border-white/10 hover:text-cyan-300 hover:border-cyan-600/50'
              }`}
            >
              <ImageIcon className="w-5 h-5" />
            </button>

            <textarea
              ref={textareaRef}
              value={inputPrompt}
              onChange={(e) => onInputChange(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={
                attachedFile
                  ? 'State specific verification question or leave blank to auto-identify component...'
                  : 'Enter circuit query, component part number, or formula (Shift+Enter for newline)...'
              }
              rows={2}
              disabled={isLoading}
              className="flex-1 bg-transparent resize-none outline-none text-sm text-slate-100 placeholder:text-slate-500 max-h-32 py-1 px-2 font-sans"
            />

            {/* Phosphor Emerald Send Trigger */}
            <button
              type="button"
              onClick={onSendMessage}
              disabled={isLoading || (!inputPrompt.trim() && !attachedFile)}
              className="px-4 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 disabled:opacity-40 disabled:hover:bg-emerald-600 text-white font-mono font-semibold text-xs tracking-wider shadow-[0_0_15px_rgba(16,185,129,0.3)] transition-all flex items-center gap-1.5 flex-shrink-0"
              title="Execute CircuitSnap Query (Enter)"
            >
              {isLoading ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <>
                  <Send className="w-3.5 h-3.5" />
                  <span className="hidden sm:inline">SEND</span>
                </>
              )}
            </button>
          </div>

          {/* Micro Telemetry Bar */}
          <div className="mt-2 pt-2 border-t border-white/5 flex items-center justify-between text-[10px] font-mono text-slate-500 px-1">
            <span>Enter: Send • Shift+Enter: Newline • Ctrl+V: Paste Image</span>
            <span className="text-slate-400">CircuitSnap AI Engine</span>
          </div>
        </div>
      </div>
    </section>
  );
};

