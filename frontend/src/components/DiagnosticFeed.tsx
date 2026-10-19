import React, { useEffect, useRef } from 'react';
import ReactMarkdown, { type Components } from 'react-markdown';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import {
  Layers,
  Sparkles,
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
                      'inline-flex items-center px-2 py-0.5 rounded text-[11px] font-mono font-bold tracking-wide uppercase mr-1.5 align-middle bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 shadow-[0_0_8px_rgba(16,185,129,0.15)]',
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
                      'inline-flex items-center px-2 py-0.5 rounded text-[11px] font-mono font-bold tracking-wide uppercase mr-1.5 align-middle bg-amber-500/15 text-amber-400 border border-amber-500/30 shadow-[0_0_8px_rgba(245,158,11,0.15)]',
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
                      'inline-flex items-center px-2 py-0.5 rounded text-[11px] font-mono font-bold tracking-wide uppercase mr-1.5 align-middle bg-rose-500/15 text-rose-400 border border-rose-500/30 shadow-[0_0_8px_rgba(244,63,94,0.15)]',
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
  table: ({ children }) => (
    <div className="overflow-x-auto my-3 rounded-lg border border-white/[0.08]">
      <table className="min-w-full divide-y divide-white/[0.08] text-xs text-left">
        {children}
      </table>
    </div>
  ),
  th: ({ children }) => (
    <th className="px-3 py-2 bg-white/[0.03] font-semibold text-cyan-300 border-b border-white/[0.08]">
      {children}
    </th>
  ),
  td: ({ children }) => (
    <td className="px-3 py-2 border-b border-white/[0.06] text-slate-300">
      {children}
    </td>
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
    <section className="lg:col-span-7 h-full flex flex-col overflow-hidden bg-slate-900/40 backdrop-blur-xl border border-white/[0.08] border-t-white/15 rounded-2xl p-4 sm:p-5 shadow-2xl relative">
      {/* Feed Header */}
      <div className="flex items-center justify-between pb-3 border-b border-white/[0.08] flex-shrink-0">
        <div className="flex items-center gap-2">
          <Layers className="w-4 h-4 text-cyan-400" />
          <h2 className="text-xs font-mono font-semibold tracking-wider uppercase text-cyan-300">
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
            <div className="w-12 h-12 rounded-2xl bg-white/[0.03] border border-white/[0.08] flex items-center justify-center text-cyan-400 shadow-xl mb-3">
              <Sparkles className="w-6 h-6" />
            </div>
            <h3 className="text-sm font-mono font-bold text-slate-100 tracking-wide">
              CIRCUITSNAP DIAGNOSTIC ENGINE STANDBY
            </h3>
            <p className="text-xs text-slate-400 max-w-sm mt-1 mb-4 leading-relaxed">
              Select a Bench Preset on the left, attach an optical inspection photo, or input an
              electronics query below.
            </p>
            <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-white/[0.03] border border-white/[0.06] text-[11px] font-mono text-slate-400">
              <span className="text-cyan-400 font-semibold">MODE:</span>
              <span>Multi-turn ECE Verification & KaTeX Analysis</span>
            </div>
          </div>
        ) : (
          messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex ${
                msg.role === 'user' ? 'justify-end' : 'justify-start'
              }`}
            >
              <div
                className={`transition-all ${
                  msg.role === 'user'
                    ? 'bg-cyan-950/30 border border-cyan-500/20 text-slate-100 rounded-2xl rounded-tr-sm px-4 py-3 shadow-lg max-w-[85%]'
                    : 'bg-slate-900/40 border border-white/[0.07] text-slate-200 rounded-2xl rounded-tl-sm px-5 py-4 shadow-xl max-w-[92%] sm:max-w-[88%]'
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
                  <div className="mt-3 pt-2.5 border-t border-white/[0.06] flex flex-wrap items-center gap-1.5 text-[10px] font-mono text-slate-400">
                    <span className="px-2 py-0.5 rounded-full bg-white/[0.03] border border-white/[0.06] text-cyan-300 font-medium">
                      {msg.metadata.provider} / {msg.metadata.model_id}
                    </span>
                    <span className="px-2 py-0.5 rounded-full bg-white/[0.03] border border-white/[0.06] text-slate-400">
                      {msg.metadata.attempts === 1 ? '1 CYCLE' : `${msg.metadata.attempts} CYCLES`}
                    </span>
                    {msg.metadata.fallback_used && (
                      <span className="px-2 py-0.5 rounded-full bg-amber-500/15 text-amber-300 border border-amber-500/30 font-bold">
                        FALLBACK ACTIVE
                      </span>
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
              <span className="tracking-wide text-slate-300">Processing hardware telemetry & optical spectrum...</span>
            </div>
          </div>
        )}

        <div ref={chatBottomRef} />
      </div>

      {/* Floating Composer Pinned at Bottom of Column B */}
      <div className="pt-2 flex-shrink-0">
        <div className="bg-slate-900/80 backdrop-blur-xl border border-white/10 shadow-[0_8px_32px_rgba(0,0,0,0.4)] rounded-2xl p-2.5 mx-auto max-w-full focus-within:border-cyan-500/50 focus-within:ring-1 focus-within:ring-cyan-500/30 transition-all">
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
                title="Clear optical target"
              >
                <X className="w-3 h-3" />
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
              className={`p-2 rounded-xl border transition-all flex-shrink-0 ${
                attachedFile
                  ? 'bg-cyan-950/60 text-cyan-300 border-cyan-500/40 shadow-[0_0_10px_rgba(6,182,212,0.2)]'
                  : 'bg-white/[0.03] text-slate-400 border-white/[0.08] hover:text-cyan-300 hover:border-cyan-500/30 hover:bg-white/[0.05]'
              }`}
            >
              <ImageIcon className="w-4 h-4" />
            </button>

            <textarea
              ref={textareaRef}
              value={inputPrompt}
              onChange={(e) => onInputChange(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={
                attachedFile
                  ? 'State verification question or leave blank to auto-identify...'
                  : 'Ask a circuit question, paste part number, or formula...'
              }
              rows={1}
              disabled={isLoading}
              className="flex-1 bg-transparent resize-none outline-none text-sm text-slate-100 placeholder:text-slate-500 max-h-32 py-1.5 px-2 font-sans leading-relaxed"
            />

            {/* Phosphor Emerald Send Trigger */}
            <button
              type="button"
              onClick={onSendMessage}
              disabled={isLoading || (!inputPrompt.trim() && !attachedFile)}
              className="p-2 rounded-xl bg-emerald-500 hover:bg-emerald-400 disabled:opacity-30 disabled:hover:bg-emerald-500 text-slate-950 font-bold shadow-[0_0_16px_rgba(16,185,129,0.35)] transition-all active:scale-95 flex-shrink-0 flex items-center justify-center"
              title="Execute CircuitSnap Query (Enter)"
            >
              {isLoading ? (
                <Loader2 className="w-4 h-4 animate-spin text-slate-950" />
              ) : (
                <Send className="w-4 h-4 text-slate-950" />
              )}
            </button>
          </div>

          {/* Micro Telemetry Bar */}
          <div className="mt-2 pt-1.5 border-t border-white/[0.05] flex items-center justify-between text-[10px] font-mono text-slate-500 px-1">
            <span>Enter: Send • Shift+Enter: Newline • Ctrl+V: Paste</span>
            <span className="text-slate-500">CircuitSnap AI Engine</span>
          </div>
        </div>
      </div>
    </section>
  );
};
