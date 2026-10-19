import { useState, useEffect, useRef, useCallback } from 'react';
import { AlertCircle, X } from 'lucide-react';
import {
  checkHealth, sendChatMessage, analyzeImage,
  ALLOWED_IMAGE_TYPES, MAX_FILE_SIZE_BYTES,
  type ChatResponse, type HealthResponse,
} from './api';
import { TelemetryHeader, type TelemetryData } from './components/TelemetryHeader';
import { InspectionDeck } from './components/InspectionDeck';
import { DiagnosticFeed, type DisplayMessage } from './components/DiagnosticFeed';

export default function App() {
  const [messages, setMessages] = useState<DisplayMessage[]>([]);
  const [inputPrompt, setInputPrompt] = useState('');
  const [attachedFile, setAttachedFile] = useState<File | null>(null);
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const [activeDutImage, setActiveDutImage] = useState<string | null>(null);
  const [activeDutName, setActiveDutName] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [isHealthLoading, setIsHealthLoading] = useState(true);
  const [healthError, setHealthError] = useState<string | null>(null);
  const [telemetry, setTelemetry] = useState<TelemetryData>({ provider: '', model_id: '', attempts: 1, fallback_used: false });

  const fileInputRef = useRef<HTMLInputElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const activeObjectUrlsRef = useRef<Set<string>>(new Set());

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
      setHealthError(err instanceof Error ? err.message : 'Failed to reach backend');
      setHealth(null);
    } finally {
      setIsHealthLoading(false);
    }
  }, []);

  useEffect(() => {
    const timer = setTimeout(() => { void fetchHealth(); }, 0);
    return () => clearTimeout(timer);
  }, [fetchHealth]);

  useEffect(() => {
    return () => {
      if (imagePreview && imagePreview !== activeDutImage) URL.revokeObjectURL(imagePreview);
    };
  }, [imagePreview, activeDutImage]);

  useEffect(() => {
    const urls = activeObjectUrlsRef.current;
    return () => {
      urls.forEach((url) => URL.revokeObjectURL(url));
      urls.clear();
    };
  }, []);

  const handleFileSelect = useCallback((file: File) => {
    setErrorMessage(null);
    if (!ALLOWED_IMAGE_TYPES.includes(file.type)) {
      setErrorMessage('Unsupported file type. Please upload a JPEG, PNG, WEBP, or GIF image.');
      return;
    }
    if (file.size > MAX_FILE_SIZE_BYTES) {
      setErrorMessage(`File is too large (${(file.size / (1024 * 1024)).toFixed(1)} MB). Max size is 10 MB.`);
      return;
    }

    const objectUrl = URL.createObjectURL(file);
    activeObjectUrlsRef.current.add(objectUrl);
    setAttachedFile(file);
    setImagePreview(objectUrl);
    setActiveDutImage(objectUrl);
    setActiveDutName(file.name);
  }, []);

  useEffect(() => {
    const handlePaste = (e: ClipboardEvent) => {
      const file = Array.from(e.clipboardData?.items || []).find((i) => i.type.startsWith('image/'))?.getAsFile();
      if (file) handleFileSelect(file);
    };
    window.addEventListener('paste', handlePaste);
    return () => window.removeEventListener('paste', handlePaste);
  }, [handleFileSelect]);

  const removeAttachedFile = () => {
    setAttachedFile(null);
    if (imagePreview && imagePreview !== activeDutImage) URL.revokeObjectURL(imagePreview);
    setImagePreview(null);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const handleEjectDut = () => {
    setActiveDutImage(null);
    setActiveDutName(null);
    removeAttachedFile();
  };

  const handleClearChat = () => {
    activeObjectUrlsRef.current.forEach((url) => URL.revokeObjectURL(url));
    activeObjectUrlsRef.current.clear();
    setActiveDutImage(null);
    setActiveDutName(null);
    setMessages([]);
    setErrorMessage(null);
    removeAttachedFile();
  };

  const handleSendMessage = async (overridePrompt?: string) => {
    const text = (overridePrompt !== undefined ? overridePrompt : inputPrompt).trim();
    if (!text && !attachedFile) return;

    setErrorMessage(null);
    setIsLoading(true);

    let messageImageUrl: string | undefined = undefined;
    if (attachedFile) {
      messageImageUrl = URL.createObjectURL(attachedFile);
      activeObjectUrlsRef.current.add(messageImageUrl);
    }

    setMessages((prev) => [
      ...prev,
      {
        id: `user-${Date.now()}`,
        role: 'user',
        content: text || '(Optical Inspection Photo Submitted for Component Identification)',
        imagePreviewUrl: messageImageUrl,
      },
    ]);
    setInputPrompt('');

    const fileToUpload = attachedFile;
    removeAttachedFile();

    try {
      const response: ChatResponse = fileToUpload
        ? await analyzeImage(fileToUpload, text || undefined)
        : await sendChatMessage(text, messages.map((m) => ({ role: m.role, content: m.content })));

      setTelemetry({
        provider: response.provider,
        model_id: response.model_id,
        attempts: response.attempts,
        fallback_used: response.fallback_used,
      });

      setMessages((prev) => [
        ...prev,
        {
          id: `assistant-${Date.now()}`,
          role: 'assistant',
          content: response.answer,
          metadata: {
            provider: response.provider,
            model_id: response.model_id,
            attempts: response.attempts,
            fallback_used: response.fallback_used,
          },
        },
      ]);
    } catch (err: unknown) {
      setErrorMessage(err instanceof Error ? err.message : 'An unexpected error occurred.');
      setInputPrompt(text);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="h-screen bg-[#0b0f19] text-slate-100 flex flex-col overflow-hidden selection:bg-cyan-900 selection:text-cyan-200">
      <TelemetryHeader
        health={health}
        isHealthLoading={isHealthLoading}
        healthError={healthError}
        onRefreshHealth={fetchHealth}
        telemetry={telemetry}
        onResetWorkbench={handleClearChat}
        hasActiveSession={messages.length > 0 || attachedFile !== null || activeDutImage !== null}
      />

      {errorMessage && (
        <div className="px-4 py-2 bg-rose-950/80 border-b border-rose-800 text-rose-200 flex items-center justify-between text-xs font-mono z-30">
          <div className="flex items-center gap-2">
            <AlertCircle className="w-4 h-4 text-rose-400 flex-shrink-0" />
            <span>[FAULT DETECTED]: {errorMessage}</span>
          </div>
          <button onClick={() => setErrorMessage(null)} className="text-rose-400 hover:text-white p-1 rounded transition-colors">
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      )}

      <input
        type="file"
        ref={fileInputRef}
        onChange={(e) => e.target.files?.[0] && handleFileSelect(e.target.files[0])}
        accept="image/jpeg,image/png,image/webp,image/gif"
        className="hidden"
      />

      <main className="flex-1 h-[calc(100vh-65px)] overflow-hidden p-3 sm:p-4 lg:p-5">
        <div className="h-full grid grid-cols-1 lg:grid-cols-12 gap-4 lg:gap-5 overflow-hidden">
          <InspectionDeck
            activeDutImage={activeDutImage}
            activeDutName={activeDutName}
            attachedFile={attachedFile}
            isLoading={isLoading}
            onFileSelect={handleFileSelect}
            onEjectDut={handleEjectDut}
            onReplaceDut={() => fileInputRef.current?.click()}
            onQuickAction={(prompt) => {
              setInputPrompt(prompt);
              textareaRef.current?.focus();
            }}
          />

          <DiagnosticFeed
            messages={messages}
            isLoading={isLoading}
            inputPrompt={inputPrompt}
            onInputChange={setInputPrompt}
            onSendMessage={handleSendMessage}
            attachedFile={attachedFile}
            onRemoveAttachment={removeAttachedFile}
            onAttachClick={() => fileInputRef.current?.click()}
            textareaRef={textareaRef}
          />
        </div>
      </main>
    </div>
  );
}
