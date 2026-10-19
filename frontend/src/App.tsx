import { useState, useEffect, useRef, useCallback } from 'react';
import { AlertCircle, X } from 'lucide-react';
import {
  checkHealth, sendChatMessage, analyzeImage, fetchAvailableModels,
  fetchCurrentOperator, logoutOperator, ALLOWED_IMAGE_TYPES, MAX_FILE_SIZE_BYTES,
  type ChatResponse, type HealthResponse, type ModelOption, type OperatorUser,
} from './api';
import { TelemetryHeader, type TelemetryData } from './components/TelemetryHeader';
import { InspectionDeck } from './components/InspectionDeck';
import { DiagnosticFeed, type DisplayMessage } from './components/DiagnosticFeed';
import { AuthModal } from './components/AuthModal';
import { VaultDrawer } from './components/VaultDrawer';

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
  const [availableModels, setAvailableModels] = useState<ModelOption[]>([]);
  const [selectedModel, setSelectedModel] = useState<string>('auto');
  const [visionNotice, setVisionNotice] = useState<string | null>(null);
  const [currentUser, setCurrentUser] = useState<OperatorUser | null>(null);
  const [isAuthModalOpen, setIsAuthModalOpen] = useState(false);
  const [isVaultOpen, setIsVaultOpen] = useState(false);
  const [vaultCount, setVaultCount] = useState(0);

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
    const timer = setTimeout(() => {
      void fetchHealth();
      void fetchAvailableModels().then(setAvailableModels).catch(() => {});
      void fetchCurrentOperator().then(setCurrentUser).catch(() => {});
    }, 0);
    return () => clearTimeout(timer);
  }, [fetchHealth]);

  useEffect(() => {
    return () => { if (imagePreview && imagePreview !== activeDutImage) URL.revokeObjectURL(imagePreview); };
  }, [imagePreview, activeDutImage]);

  useEffect(() => {
    const urls = activeObjectUrlsRef.current;
    return () => { urls.forEach((url) => URL.revokeObjectURL(url)); urls.clear(); };
  }, []);

  const handleFileSelect = useCallback((file: File) => {
    setErrorMessage(null);
    if (!ALLOWED_IMAGE_TYPES.includes(file.type)) { setErrorMessage('Unsupported file type. Please upload a JPEG, PNG, WEBP, or GIF image.'); return; }
    if (file.size > MAX_FILE_SIZE_BYTES) { setErrorMessage(`File is too large (${(file.size / (1024 * 1024)).toFixed(1)} MB). Max size is 10 MB.`); return; }
    const objectUrl = URL.createObjectURL(file);
    activeObjectUrlsRef.current.add(objectUrl);
    setAttachedFile(file); setImagePreview(objectUrl); setActiveDutImage(objectUrl); setActiveDutName(file.name);
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

  const handleEjectDut = () => { setActiveDutImage(null); setActiveDutName(null); removeAttachedFile(); };

  const handleClearChat = () => {
    activeObjectUrlsRef.current.forEach((url) => URL.revokeObjectURL(url));
    activeObjectUrlsRef.current.clear();
    setActiveDutImage(null); setActiveDutName(null);
    setMessages([]); setErrorMessage(null); setVisionNotice(null);
    removeAttachedFile();
  };

  const handleLogout = () => { logoutOperator(); setCurrentUser(null); };

  const handleRestoreSession = (r: { messages: DisplayMessage[]; dutImage: string | null }) => {
    setMessages(r.messages);
    if (r.dutImage) { setActiveDutImage(r.dutImage); setActiveDutName('Archived Component'); }
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
      { id: `user-${Date.now()}`, role: 'user', content: text || '(Optical Inspection Photo Submitted for Component Identification)', imagePreviewUrl: messageImageUrl },
    ]);
    setInputPrompt('');

    const fileToUpload = attachedFile;
    removeAttachedFile();

    if (fileToUpload && selectedModel !== 'auto') {
      const chosen = availableModels.find((m) => m.id === selectedModel);
      if (chosen && !chosen.supports_vision) {
        setVisionNotice('Routing to Gemini Optical Vision Engine');
        setTimeout(() => setVisionNotice(null), 4000);
      }
    }

    try {
      const response: ChatResponse = fileToUpload
        ? await analyzeImage(fileToUpload, text || undefined, selectedModel)
        : await sendChatMessage(text, messages.map((m) => ({ role: m.role, content: m.content })), selectedModel);

      setTelemetry({ provider: response.provider, model_id: response.model_id, attempts: response.attempts, fallback_used: response.fallback_used });
      setMessages((prev) => [
        ...prev,
        { id: `assistant-${Date.now()}`, role: 'assistant', content: response.answer, metadata: { provider: response.provider, model_id: response.model_id, attempts: response.attempts, fallback_used: response.fallback_used, original_model: response.original_model } },
      ]);
    } catch (err: unknown) {
      setErrorMessage(err instanceof Error ? err.message : 'An unexpected error occurred.');
      setInputPrompt(text);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-dvh lg:h-screen lg:overflow-hidden bg-[#090d16] text-slate-100 flex flex-col selection:bg-cyan-900 selection:text-cyan-200">
      <TelemetryHeader
        health={health}
        isHealthLoading={isHealthLoading}
        healthError={healthError}
        onRefreshHealth={fetchHealth}
        telemetry={telemetry}
        onResetWorkbench={handleClearChat}
        hasActiveSession={messages.length > 0 || attachedFile !== null || activeDutImage !== null}
        availableModels={availableModels}
        selectedModel={selectedModel}
        onSelectModel={setSelectedModel}
        currentUser={currentUser}
        onOpenAuthModal={() => setIsAuthModalOpen(true)}
        onLogout={handleLogout}
        onOpenVault={() => setIsVaultOpen(true)}
        vaultSessionCount={vaultCount}
      />

      {visionNotice && (
        <div className="px-4 py-1.5 bg-cyan-950/90 border-b border-cyan-500/40 text-cyan-200 flex items-center justify-between text-xs font-mono z-30 animate-pulse">
          <span>⚡ [OPTICAL ROUTER]: {visionNotice}</span>
          <button onClick={() => setVisionNotice(null)} className="text-cyan-400 hover:text-white p-0.5 transition-colors"><X className="w-3.5 h-3.5" /></button>
        </div>
      )}

      {errorMessage && (
        <div className="px-4 py-2 bg-rose-950/80 border-b border-rose-800 text-rose-200 flex items-center justify-between text-xs font-mono z-30">
          <div className="flex items-center gap-2"><AlertCircle className="w-4 h-4 text-rose-400 flex-shrink-0" /><span>[FAULT DETECTED]: {errorMessage}</span></div>
          <button onClick={() => setErrorMessage(null)} className="text-rose-400 hover:text-white p-1 rounded transition-colors"><X className="w-3.5 h-3.5" /></button>
        </div>
      )}

      <input type="file" ref={fileInputRef} onChange={(e) => e.target.files?.[0] && handleFileSelect(e.target.files[0])} accept="image/jpeg,image/png,image/webp,image/gif" className="hidden" />

      <main className="flex-1 min-h-[calc(100dvh-65px)] lg:h-[calc(100dvh-65px)] overflow-y-auto lg:overflow-hidden p-3 sm:p-4 lg:p-5">
        <div className="min-h-full grid grid-cols-1 lg:grid-cols-12 gap-4 lg:gap-5 lg:overflow-hidden">
          <InspectionDeck
            activeDutImage={activeDutImage}
            activeDutName={activeDutName}
            attachedFile={attachedFile}
            isLoading={isLoading}
            onFileSelect={handleFileSelect}
            onEjectDut={handleEjectDut}
            onReplaceDut={() => fileInputRef.current?.click()}
            onQuickAction={(prompt) => { setInputPrompt(prompt); textareaRef.current?.focus(); }}
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

      <AuthModal isOpen={isAuthModalOpen} onClose={() => setIsAuthModalOpen(false)} onSuccess={setCurrentUser} />
      <VaultDrawer
        isOpen={isVaultOpen}
        onClose={() => setIsVaultOpen(false)}
        currentUser={currentUser}
        currentMessages={messages}
        currentDutImage={activeDutImage}
        onRestoreSession={handleRestoreSession}
        onOpenAuthModal={() => setIsAuthModalOpen(true)}
        onSessionsChange={setVaultCount}
      />
    </div>
  );
}
