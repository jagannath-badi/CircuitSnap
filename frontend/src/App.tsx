import React, { useState, useEffect, useRef, useCallback } from 'react';
import ReactMarkdown, { type Components } from 'react-markdown';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import {
  Cpu,
  Send,
  Image as ImageIcon,
  X,
  AlertCircle,
  Loader2,
  User,
  Bot,
  Sparkles,
  Crosshair,
  Camera,
  Palette,
  Clock,
  AlertTriangle,
  Layers,
  Terminal,
  Scan,
} from 'lucide-react';
import type {
  ChatMessage,
  ChatResponse,
  HealthResponse,
} from './api';
import {
  checkHealth,
  sendChatMessage,
  analyzeImage,
  ALLOWED_IMAGE_TYPES,
  MAX_FILE_SIZE_BYTES,
} from './api';
import { TelemetryHeader, type TelemetryData } from './TelemetryHeader';

interface DisplayMessage {
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

const QUICK_ACTION_CHIPS = [
  {
    label: 'Decode Color Bands',
    icon: Palette,
    prompt:
      'Decode the color bands on this resistor. State the nominal resistance, tolerance, standard E-series designation, and verification tips.',
  },
  {
    label: 'Op-Amp Pinout & Specs',
    icon: Cpu,
    prompt:
      'Identify this operational amplifier, explain its pinout diagram, maximum ratings, supply rail requirements, and typical negative feedback configuration.',
  },
  {
    label: '555 Timer Config',
    icon: Clock,
    prompt:
      'Explain the pinout and calculate the timing components (R1, R2, C) for this 555 timer in astable/monostable mode.',
  },
  {
    label: 'Troubleshoot Short / Noise',
    icon: AlertTriangle,
    prompt:
      'Analyze this circuit for potential issues: check for ground loop vulnerability, missing decoupling capacitors, polarity inversion, or short circuits.',
  },
];

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

export default function App() {
  const [messages, setMessages] = useState<DisplayMessage[]>([]);
  const [inputPrompt, setInputPrompt] = useState('');
  const [attachedFile, setAttachedFile] = useState<File | null>(null);
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const [activeDutImage, setActiveDutImage] = useState<string | null>(null);
  const [activeDutName, setActiveDutName] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isDragOver, setIsDragOver] = useState(false);

  // Backend Health State
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [isHealthLoading, setIsHealthLoading] = useState(true);
  const [healthError, setHealthError] = useState<string | null>(null);

  // Active Telemetry State
  const [telemetry, setTelemetry] = useState<TelemetryData>({
    provider: '',
    model_id: '',
    attempts: 1,
    fallback_used: false,
  });

  const fileInputRef = useRef<HTMLInputElement>(null);
  const chatBottomRef = useRef<HTMLDivElement>(null);
  const activeObjectUrlsRef = useRef<Set<string>>(new Set());
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const fetchHealth = useCallback(async () => {
    setIsHealthLoading(true);
    setHealthError(null);
    try {
      const data = await checkHealth();
      setHealth(data);
      if (data.models?.default || data.models?.model_id) {
        setTelemetry((prev) => ({
          ...prev,
          provider: (data.models?.provider as string) || (data.models?.default as string) || prev.provider,
          model_id: (data.models?.model_id as string) || prev.model_id,
        }));
      }
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to reach backend';
      setHealthError(message);
      setHealth(null);
    } finally {
      setIsHealthLoading(false);
    }
  }, []);

  // Initial health check on mount
  useEffect(() => {
    let active = true;
    checkHealth()
      .then((data) => {
        if (active) {
          setHealth(data);
          setIsHealthLoading(false);
          if (data.models?.default || data.models?.model_id) {
            setTelemetry((prev) => ({
              ...prev,
              provider: (data.models?.provider as string) || (data.models?.default as string) || '',
              model_id: (data.models?.model_id as string) || '',
            }));
          }
        }
      })
      .catch((err: unknown) => {
        if (active) {
          const message = err instanceof Error ? err.message : 'Failed to reach backend';
          setHealthError(message);
          setIsHealthLoading(false);
        }
      });

    return () => {
      active = false;
    };
  }, []);

  // Auto-scroll chat log to bottom
  useEffect(() => {
    chatBottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  // Clean up draft preview object URL when it changes
  useEffect(() => {
    return () => {
      if (imagePreview) {
        URL.revokeObjectURL(imagePreview);
      }
    };
  }, [imagePreview]);

  // Clean up all message object URLs on unmount
  useEffect(() => {
    const urls = activeObjectUrlsRef.current;
    return () => {
      urls.forEach((url) => {
        URL.revokeObjectURL(url);
      });
      urls.clear();
    };
  }, []);

  const handleFileSelect = useCallback((file: File) => {
    setErrorMessage(null);

    // Validate MIME type
    if (!ALLOWED_IMAGE_TYPES.includes(file.type)) {
      setErrorMessage('Unsupported file type. Please upload a JPEG, PNG, WEBP, or GIF image.');
      return;
    }

    // Validate Size
    if (file.size > MAX_FILE_SIZE_BYTES) {
      setErrorMessage(
        `File is too large (${(file.size / (1024 * 1024)).toFixed(1)} MB). The maximum allowed size is 10 MB.`
      );
      return;
    }

    const objectUrl = URL.createObjectURL(file);
    activeObjectUrlsRef.current.add(objectUrl);

    setAttachedFile(file);
    setImagePreview(objectUrl);
    setActiveDutImage(objectUrl);
    setActiveDutName(file.name);
  }, []);

  // Global clipboard paste listener (Ctrl+V anywhere loads optical scope)
  useEffect(() => {
    const handlePaste = (e: ClipboardEvent) => {
      const items = e.clipboardData?.items;
      if (!items) return;

      for (let i = 0; i < items.length; i++) {
        if (items[i].type.startsWith('image/')) {
          const file = items[i].getAsFile();
          if (file) {
            handleFileSelect(file);
            break;
          }
        }
      }
    };

    window.addEventListener('paste', handlePaste);
    return () => window.removeEventListener('paste', handlePaste);
  }, [handleFileSelect]);

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      handleFileSelect(e.target.files[0]);
    }
  };

  const removeAttachedFile = () => {
    setAttachedFile(null);
    if (imagePreview) {
      if (imagePreview !== activeDutImage) {
        URL.revokeObjectURL(imagePreview);
      }
      setImagePreview(null);
    }
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleEjectDut = () => {
    setActiveDutImage(null);
    setActiveDutName(null);
    removeAttachedFile();
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileSelect(e.dataTransfer.files[0]);
    }
  };

  const handleSendMessage = async (overridePrompt?: string) => {
    const text = (overridePrompt !== undefined ? overridePrompt : inputPrompt).trim();
    if (!text && !attachedFile) return;

    setErrorMessage(null);
    setIsLoading(true);

    // Create a dedicated, persistent object URL for the user message thumbnail
    let messageImageUrl: string | undefined = undefined;
    if (attachedFile) {
      messageImageUrl = URL.createObjectURL(attachedFile);
      activeObjectUrlsRef.current.add(messageImageUrl);
    }

    const userMessageId = `user-${Date.now()}`;
    const userDisplayMsg: DisplayMessage = {
      id: userMessageId,
      role: 'user',
      content: text || '(Optical Inspection Photo Submitted for Component Identification)',
      imagePreviewUrl: messageImageUrl,
    };

    // Optimistically update conversation
    setMessages((prev) => [...prev, userDisplayMsg]);
    setInputPrompt('');

    // Save image ref for request, then clear draft attachment UI
    const fileToUpload = attachedFile;
    removeAttachedFile();

    try {
      let response: ChatResponse;

      if (fileToUpload) {
        // Multi-modal image analysis endpoint
        response = await analyzeImage(fileToUpload, text || undefined);
      } else {
        // Multi-turn text chat endpoint
        const historyPayload: ChatMessage[] = messages.map((m) => ({
          role: m.role,
          content: m.content,
        }));
        response = await sendChatMessage(text, historyPayload);
      }

      // Update telemetry display
      setTelemetry({
        provider: response.provider,
        model_id: response.model_id,
        attempts: response.attempts,
        fallback_used: response.fallback_used,
      });

      const assistantDisplayMsg: DisplayMessage = {
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        content: response.answer,
        metadata: {
          provider: response.provider,
          model_id: response.model_id,
          attempts: response.attempts,
          fallback_used: response.fallback_used,
        },
      };

      setMessages((prev) => [...prev, assistantDisplayMsg]);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'An unexpected error occurred.';
      setErrorMessage(msg);
      // Restore input prompt so student does not lose their typed work
      setInputPrompt(text);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handleClearChat = () => {
    // Revoke all active message image object URLs to free memory
    activeObjectUrlsRef.current.forEach((url) => {
      URL.revokeObjectURL(url);
    });
    activeObjectUrlsRef.current.clear();

    setActiveDutImage(null);
    setActiveDutName(null);
    setMessages([]);
    setErrorMessage(null);
    removeAttachedFile();
  };

  const handleQuickActionClick = (prompt: string) => {
    setInputPrompt(prompt);
    textareaRef.current?.focus();
  };

  return (
    <div className="h-screen bg-[#0b0f19] text-slate-100 flex flex-col overflow-hidden selection:bg-cyan-900 selection:text-cyan-200">
      {/* 1. Pinned Top Telemetry Header */}
      <TelemetryHeader
        health={health}
        isHealthLoading={isHealthLoading}
        healthError={healthError}
        onRefreshHealth={fetchHealth}
        telemetry={telemetry}
        onResetWorkbench={handleClearChat}
        hasActiveSession={messages.length > 0 || attachedFile !== null || activeDutImage !== null}
      />

      {/* Error Notification Banner */}
      {errorMessage && (
        <div className="px-4 py-2 bg-rose-950/80 border-b border-rose-800 text-rose-200 flex items-center justify-between text-xs font-mono z-30">
          <div className="flex items-center gap-2">
            <AlertCircle className="w-4 h-4 text-rose-400 flex-shrink-0" />
            <span>[FAULT DETECTED]: {errorMessage}</span>
          </div>
          <button
            onClick={() => setErrorMessage(null)}
            className="text-rose-400 hover:text-white p-1 rounded transition-colors"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      )}

      {/* 2. Main Two-Column Cyber-Physical Hardware Workbench Grid */}
      <main className="flex-1 h-[calc(100vh-65px)] overflow-hidden p-3 sm:p-4 lg:p-5">
        <div className="h-full grid grid-cols-1 lg:grid-cols-12 gap-4 lg:gap-5 overflow-hidden">
          {/* ========================================================= */}
          {/* COLUMN A: Inspection Scope (~38% / lg:col-span-5)         */}
          {/* ========================================================= */}
          <section className="lg:col-span-5 h-full flex flex-col overflow-hidden bg-slate-900/60 border border-white/10 backdrop-blur-md rounded-2xl p-4 sm:p-5 shadow-2xl">
            {/* Scope Header */}
            <div className="flex items-center justify-between pb-3 border-b border-white/10 flex-shrink-0">
              <div className="flex items-center gap-2">
                <Scan className="w-4 h-4 text-cyan-400" />
                <h2 className="text-xs font-mono font-bold tracking-wider uppercase text-cyan-300">
                  OPTICAL INSPECTION SCOPE
                </h2>
              </div>
              <span
                className={`text-[10px] font-mono font-semibold px-2 py-0.5 rounded-full border ${
                  activeDutImage
                    ? 'bg-cyan-950/80 text-cyan-400 border-cyan-800/80 animate-pulse'
                    : 'bg-slate-950/60 text-slate-500 border-white/5'
                }`}
              >
                {activeDutImage ? 'CH 1 // OPTICAL FEED LOCKED' : 'STANDBY // RETICLE READY'}
              </span>
            </div>

            {/* Hidden File Input */}
            <input
              type="file"
              ref={fileInputRef}
              onChange={handleFileInputChange}
              accept="image/jpeg,image/png,image/webp,image/gif"
              className="hidden"
            />

            {/* Pinned Optical HUD Scope Viewport */}
            <div className="flex-1 my-3 relative flex flex-col justify-center min-h-[220px] overflow-hidden">
              {activeDutImage ? (
                /* Active Loaded Component Scope with Reticle Overlays */
                <div className="relative w-full h-full min-h-[240px] rounded-xl bg-slate-950/80 border border-cyan-800/40 flex flex-col items-center justify-center overflow-hidden p-3 group">
                  {/* Scope Corner HUD Reticles */}
                  <div className="absolute top-2 left-2 w-3.5 h-3.5 border-t-2 border-l-2 border-cyan-400 pointer-events-none" />
                  <div className="absolute top-2 right-2 w-3.5 h-3.5 border-t-2 border-r-2 border-cyan-400 pointer-events-none" />
                  <div className="absolute bottom-2 left-2 w-3.5 h-3.5 border-b-2 border-l-2 border-cyan-400 pointer-events-none" />
                  <div className="absolute bottom-2 right-2 w-3.5 h-3.5 border-b-2 border-r-2 border-cyan-400 pointer-events-none" />

                  {/* Optical Center Crosshairs overlay */}
                  <div className="absolute inset-0 pointer-events-none flex items-center justify-center opacity-30">
                    <Crosshair className="w-16 h-16 text-cyan-300" strokeWidth={1} />
                  </div>

                  {/* Component Preview Image */}
                  <img
                    src={activeDutImage}
                    alt="Loaded Component Under Scope"
                    className="max-h-60 sm:max-h-64 w-auto object-contain rounded-lg relative z-10 shadow-lg"
                  />

                  {/* Scope Bottom Telemetry Overlay */}
                  <div className="absolute bottom-2 inset-x-2 z-20 px-3 py-1.5 rounded-lg bg-slate-950/90 backdrop-blur-md border border-white/10 flex items-center justify-between text-[11px] font-mono">
                    <div className="truncate mr-2">
                      <span className="text-cyan-300 font-semibold truncate block max-w-[200px]">
                        {activeDutName || 'ACTIVE COMPONENT'}
                      </span>
                      <span className="text-[10px] text-slate-400">
                        {attachedFile
                          ? `${(attachedFile.size / (1024 * 1024)).toFixed(2)} MB • ${attachedFile.type}`
                          : 'PINNED DUT // ACTIVE CHANNEL'}
                      </span>
                    </div>

                    <div className="flex items-center gap-1.5 flex-shrink-0">
                      <button
                        type="button"
                        onClick={() => fileInputRef.current?.click()}
                        disabled={isLoading}
                        className="px-2 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-200 text-[10px] font-mono transition-colors"
                        title="Replace scope image"
                      >
                        REPLACE
                      </button>
                      <button
                        type="button"
                        onClick={handleEjectDut}
                        disabled={isLoading}
                        className="px-2 py-1 rounded bg-rose-950/60 hover:bg-rose-900/80 text-rose-300 border border-rose-800/40 text-[10px] font-mono transition-colors"
                        title="Eject / Clear DUT"
                      >
                        EJECT / CLEAR DUT
                      </button>
                    </div>
                  </div>
                </div>
              ) : (
                /* Standby Target Reticle with Drag & Drop & Paste Support */
                <div
                  onDragOver={handleDragOver}
                  onDragLeave={handleDragLeave}
                  onDrop={handleDrop}
                  onClick={() => fileInputRef.current?.click()}
                  className={`w-full h-full min-h-[220px] rounded-xl border-2 border-dashed transition-all cursor-pointer flex flex-col items-center justify-center p-6 text-center relative group ${
                    isDragOver
                      ? 'border-cyan-400 bg-cyan-950/30 shadow-[0_0_20px_rgba(6,182,212,0.2)]'
                      : 'border-white/10 hover:border-cyan-500/50 bg-slate-950/40 hover:bg-slate-950/70'
                  }`}
                >
                  {/* Corner Targets */}
                  <div className="absolute top-2 left-2 w-3 h-3 border-t border-l border-cyan-500/40 group-hover:border-cyan-400 transition-colors" />
                  <div className="absolute top-2 right-2 w-3 h-3 border-t border-r border-cyan-500/40 group-hover:border-cyan-400 transition-colors" />
                  <div className="absolute bottom-2 left-2 w-3 h-3 border-b border-l border-cyan-500/40 group-hover:border-cyan-400 transition-colors" />
                  <div className="absolute bottom-2 right-2 w-3 h-3 border-b border-r border-cyan-500/40 group-hover:border-cyan-400 transition-colors" />

                  {/* Optical Reticle Icon */}
                  <div className="w-12 h-12 rounded-2xl bg-cyan-950/60 border border-cyan-800/60 flex items-center justify-center text-cyan-400 group-hover:scale-105 group-hover:border-cyan-400 transition-all mb-3 shadow-inner">
                    <Camera className="w-6 h-6" />
                  </div>

                  <h3 className="text-sm font-mono font-bold tracking-wide text-slate-200 group-hover:text-cyan-300 transition-colors">
                    AWAITING OPTICAL FEED
                  </h3>
                  <p className="text-xs text-slate-400 mt-1 max-w-[260px] leading-relaxed">
                    Drag & drop circuit photo or schematic, click to browse, or paste directly with{' '}
                    <kbd className="px-1.5 py-0.5 rounded bg-slate-800 text-cyan-300 font-mono text-[10px] border border-slate-700">
                      Ctrl+V
                    </kbd>
                  </p>

                  <div className="mt-4 flex items-center gap-2 text-[10px] font-mono text-slate-500">
                    <span className="px-2 py-0.5 rounded bg-slate-900 border border-white/5">
                      JPEG • PNG • WEBP • GIF
                    </span>
                    <span className="px-2 py-0.5 rounded bg-slate-900 border border-white/5">
                      MAX 10 MB
                    </span>
                  </div>
                </div>
              )}
            </div>

            {/* Workbench Quick-Action Chips */}
            <div className="pt-3 border-t border-white/10 flex-shrink-0">
              <div className="flex items-center gap-1.5 mb-2.5">
                <Terminal className="w-3.5 h-3.5 text-cyan-400" />
                <span className="text-[10px] font-mono uppercase font-bold tracking-wider text-slate-400">
                  BENCH QUICK-ACTIONS
                </span>
              </div>

              <div className="grid grid-cols-2 gap-2">
                {QUICK_ACTION_CHIPS.map((chip, idx) => {
                  const Icon = chip.icon;
                  return (
                    <button
                      key={idx}
                      type="button"
                      onClick={() => handleQuickActionClick(chip.prompt)}
                      className="p-2.5 rounded-xl bg-slate-950/70 hover:bg-slate-800/80 border border-white/10 hover:border-cyan-500/50 text-left transition-all group flex items-start gap-2"
                    >
                      <Icon className="w-4 h-4 text-cyan-400 group-hover:text-cyan-300 mt-0.5 flex-shrink-0" />
                      <div className="overflow-hidden">
                        <span className="text-xs font-mono font-semibold text-slate-200 group-hover:text-cyan-300 block truncate">
                          {chip.label}
                        </span>
                        <span className="text-[10px] text-slate-500 block truncate group-hover:text-slate-400">
                          Pre-calibrated query
                        </span>
                      </div>
                    </button>
                  );
                })}
              </div>
            </div>
          </section>

          {/* ========================================================= */}
          {/* COLUMN B: Diagnostic Feed (~62% / lg:col-span-7)          */}
          {/* ========================================================= */}
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
                      onClick={removeAttachedFile}
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
                    onClick={() => fileInputRef.current?.click()}
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
                    onChange={(e) => setInputPrompt(e.target.value)}
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
                    onClick={() => handleSendMessage()}
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
        </div>
      </main>
    </div>
  );
}
