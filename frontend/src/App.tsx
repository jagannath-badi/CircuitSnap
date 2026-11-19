import { useState, useEffect, useRef, useCallback } from 'react';
import { AlertCircle, X } from 'lucide-react';
import {
  analyzeImage, fetchAvailableModels, fetchCurrentOperator,
  ALLOWED_IMAGE_TYPES, MAX_FILE_SIZE_BYTES, streamChatMessage, fetchVaultStats,
  ingestVaultDocument, sendFeedbackToVault, fetchSystemTelemetry, fetchOperations,
  submitDecision, triggerEmergencyStop, resetOperations,
  type ChatResponse, type ModelOption, type OperatorUser, type SystemTelemetry, type OperationsState
} from './api';
import { TopCommandBar, type HudTab } from './components/hud/TopCommandBar';
import { TelemetryLeftPanel } from './components/hud/TelemetryLeftPanel';
import { AiCoreVisualizer } from './components/hud/AiCoreVisualizer';
import { TasksApprovalsPanel } from './components/hud/TasksApprovalsPanel';
import { QuickActionsRail } from './components/hud/QuickActionsRail';
import { BottomCommandDock } from './components/hud/BottomCommandDock';
import { AiCoreSettingsModal } from './components/hud/AiCoreSettingsModal';
import { AiVoiceSettingsModal } from './components/hud/AiVoiceSettingsModal';
import { InspectionDeck } from './components/InspectionDeck';
import { DiagnosticFeed, type DisplayMessage } from './components/DiagnosticFeed';
import { AuthModal } from './components/AuthModal';
import { VaultDrawer } from './components/VaultDrawer';
import { useJarvisVoice } from './hooks/useJarvisVoice';
import { MobileDrawer } from './components/hud/MobileDrawer';

export default function App() {
  const [messages, setMessages] = useState<DisplayMessage[]>([]);
  const [inputPrompt, setInputPrompt] = useState('');
  const [attachedFile, setAttachedFile] = useState<File | null>(null);
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const [activeDutImage, setActiveDutImage] = useState<string | null>(null);
  const [activeDutName, setActiveDutName] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [availableModels, setAvailableModels] = useState<ModelOption[]>([]);
  const [selectedModel, setSelectedModel] = useState<string>('auto');
  const [currentUser, setCurrentUser] = useState<OperatorUser | null>(null);
  const [isAuthModalOpen, setIsAuthModalOpen] = useState(false);
  const [isVaultOpen, setIsVaultOpen] = useState(false);
  const [_vaultCount, setVaultCount] = useState(0);
  const [vaultConcepts, setVaultConcepts] = useState(10);
  const [responseStyle, setResponseStyle] = useState('auto');
  const [cognitiveStep, setCognitiveStep] = useState<string | null>(null);
  const [speakingMsgId, setSpeakingMsgId] = useState<string | null>(null);
  const [currentTab, setCurrentTab] = useState<HudTab>('command');
  const [centerView, setCenterView] = useState<'feed' | 'deck'>('feed');
  const [privacyMode, setPrivacyMode] = useState<'strict' | 'guarded' | 'relaxed'>('guarded');
  const [systemTelemetry, setSystemTelemetry] = useState<SystemTelemetry | null>(null);
  const [operations, setOperations] = useState<OperationsState | null>(null);
  const [emergencyStop, setEmergencyStop] = useState(false);
  const [autoApprove, setAutoApprove] = useState(false);
  const [isTelemetryLoading, setIsTelemetryLoading] = useState(false);
    const [isMobileDrawerOpen, setIsMobileDrawerOpen] = useState(false);

  const fileInputRef = useRef<HTMLInputElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const activeObjectUrlsRef = useRef<Set<string>>(new Set());
  const abortControllerRef = useRef<AbortController | null>(null);

  const { isVoiceEnabled, voiceState, isListening, isSpeaking, voiceSettings, liveTranscript, voiceError, clearVoiceError, updateVoiceSettings, toggleVoiceMode, startListening, stopListening, speak, cancelSpeech, hardResetVoice, testVoicePersona } = useJarvisVoice({
    onTranscript: (t) => { setInputPrompt(t); textareaRef.current?.focus(); },
    onFinalTranscript: (t) => { if (t.trim()) void handleSendMessage(t.trim()); },
  });

  const pollSystem = useCallback(async () => {
    try {
      setIsTelemetryLoading(true);
      const [tData, opData] = await Promise.all([fetchSystemTelemetry(), fetchOperations()]);
      setSystemTelemetry(tData);
      setOperations(opData);
      setEmergencyStop(opData.emergency_stop);
    } catch { /* offline safe */ } finally { setIsTelemetryLoading(false); }
  }, []);

  useEffect(() => {
    const timer = setTimeout(() => {
      void pollSystem();
      void fetchAvailableModels().then(setAvailableModels).catch(() => {});
      void fetchCurrentOperator().then(setCurrentUser).catch(() => {});
      void fetchVaultStats().then((s) => setVaultConcepts(s.total_chunks)).catch(() => {});
    }, 0);
    const interval = setInterval(() => void pollSystem(), 4000);
    return () => { clearTimeout(timer); clearInterval(interval); };
  }, [pollSystem]);

  useEffect(() => {
    return () => { if (imagePreview && imagePreview !== activeDutImage) URL.revokeObjectURL(imagePreview); };
  }, [imagePreview, activeDutImage]);

  useEffect(() => {
    const urls = activeObjectUrlsRef.current;
    return () => {
      urls.forEach((url) => URL.revokeObjectURL(url)); urls.clear();
      if (abortControllerRef.current) abortControllerRef.current.abort();
    };
  }, []);

  const handleFileSelect = useCallback((file: File) => {
    setErrorMessage(null);
    const isImg = ALLOWED_IMAGE_TYPES.includes(file.type);
    const isDoc = file.type === 'application/pdf' || file.name.endsWith('.pdf') || file.name.endsWith('.txt') || file.name.endsWith('.md');
    if (!isImg && !isDoc) { setErrorMessage('Unsupported file. Use JPG/PNG/WEBP or PDF/TXT/MD notes.'); return; }
    if (file.size > MAX_FILE_SIZE_BYTES) { setErrorMessage(`File exceeds 10 MB limit (${(file.size / (1024 * 1024)).toFixed(1)} MB).`); return; }
    const objectUrl = URL.createObjectURL(file);
    activeObjectUrlsRef.current.add(objectUrl);
    setAttachedFile(file); setImagePreview(objectUrl); setActiveDutImage(objectUrl); setActiveDutName(file.name);
    setCenterView('deck');
    if (isDoc) { void ingestVaultDocument(file).then((r) => setVaultConcepts((c) => c + r.chunks_indexed)).catch(() => {}); }
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

  const handleEjectDut = () => { setActiveDutImage(null); setActiveDutName(null); removeAttachedFile(); setCenterView('feed'); };

  const handleEmergencyStop = async () => {
    if (abortControllerRef.current) { abortControllerRef.current.abort(); abortControllerRef.current = null; }
    cancelSpeech(); hardResetVoice(); setIsLoading(false); setCognitiveStep(null); setSpeakingMsgId(null); setEmergencyStop(true);
    try { await triggerEmergencyStop(); } catch { /* ignore */ }
    setErrorMessage('EMERGENCY KILLSWITCH ENGAGED. All autonomous solvers halted.');
  };

  const handleTakeControl = async () => {
    try { await resetOperations(); setEmergencyStop(false); setErrorMessage(null); void pollSystem(); } catch { /* ignore */ }
  };

  const handleDecision = async (opId: string, decision: 'approve' | 'decline') => {
    try { await submitDecision(opId, decision); void pollSystem(); } catch { /* ignore */ }
  };

  const handleClearChat = () => {
    if (abortControllerRef.current) { abortControllerRef.current.abort(); abortControllerRef.current = null; }
    hardResetVoice(); setSpeakingMsgId(null); setCognitiveStep(null); setIsLoading(false);
    activeObjectUrlsRef.current.forEach((url) => URL.revokeObjectURL(url)); activeObjectUrlsRef.current.clear();
    setActiveDutImage(null); setActiveDutName(null); setMessages([]); setErrorMessage(null); removeAttachedFile();
  };

  const handleSendMessage = async (overridePrompt?: string) => {
    if (emergencyStop) { setErrorMessage('Cannot send: Command Center is in Emergency Stop state.'); return; }
    const text = (overridePrompt !== undefined ? overridePrompt : inputPrompt).trim();
    if (!text && !attachedFile) return;
    setErrorMessage(null); setIsLoading(true); setCenterView('feed');
    let msgImg: string | undefined = undefined;
    if (attachedFile) { msgImg = URL.createObjectURL(attachedFile); activeObjectUrlsRef.current.add(msgImg); }
    setMessages((p) => [...p, { id: `user-${Date.now()}`, role: 'user', content: text || '(Inspection artifact)', imagePreviewUrl: msgImg }]);
    setInputPrompt('');
    const fileToUpload = attachedFile;
    removeAttachedFile();

    if (fileToUpload) {
      try {
        const res: ChatResponse = await analyzeImage(fileToUpload, text || undefined, selectedModel);
        const aId = `assistant-${Date.now()}`;
        setMessages((p) => [...p, { id: aId, role: 'assistant', content: res.answer, metadata: { provider: res.provider, model_id: res.model_id, attempts: res.attempts, fallback_used: res.fallback_used, original_model: res.original_model } }]);
        if (isVoiceEnabled && res.answer) { setSpeakingMsgId(aId); void speak(res.answer, () => setSpeakingMsgId(null)); }
      } catch (err: unknown) { setErrorMessage(err instanceof Error ? err.message : 'Error analyzing image.'); setInputPrompt(text); }
      finally { setIsLoading(false); }
    } else {
      if (abortControllerRef.current) abortControllerRef.current.abort();
      const ctrl = new AbortController(); abortControllerRef.current = ctrl;
      const aId = `assistant-${Date.now()}`;
      setMessages((p) => [...p, { id: aId, role: 'assistant', content: '', metadata: { provider: 'J.A.R.V.I.S. Core', model_id: selectedModel, attempts: 1, fallback_used: false } }]);
      try {
        await streamChatMessage(text, messages.map((m) => ({ role: m.role, content: m.content })), {
          model: selectedModel, responseStyle, privacyMode, signal: ctrl.signal,
          onStep: (s) => setCognitiveStep(s),
          onChunk: (chunk) => setMessages((p) => p.map((m) => (m.id === aId ? { ...m, content: m.content + chunk } : m))),
          onDone: (res) => {
            setCognitiveStep(null);
            setMessages((p) => p.map((m) => (m.id === aId ? { ...m, content: res.answer, metadata: { provider: res.provider, model_id: res.model_id, attempts: res.attempts, fallback_used: res.fallback_used } } : m)));
            if (isVoiceEnabled && res.answer) { setSpeakingMsgId(aId); void speak(res.answer, () => setSpeakingMsgId(null)); }
          },
          onError: (err) => { setErrorMessage(err.message); setInputPrompt(text); },
        });
      } catch (err: unknown) { setErrorMessage(err instanceof Error ? err.message : 'Streaming error.'); setInputPrompt(text); }
      finally { setIsLoading(false); setCognitiveStep(null); abortControllerRef.current = null; }
    }
  };

  const handleReadAloud = (id: string, text: string) => {
    if (speakingMsgId === id) { cancelSpeech(); setSpeakingMsgId(null); }
    else { setSpeakingMsgId(id); void speak(text, () => setSpeakingMsgId(null), true); }
  };

  return (
    <div className="h-[100dvh] max-h-[100dvh] overflow-hidden flex flex-col bg-[#050811] text-slate-100 font-mono select-none w-full max-w-[100vw]">
      <TopCommandBar
        currentTab={currentTab}
        onSelectTab={setCurrentTab}
        telemetry={systemTelemetry}
        privacyMode={privacyMode}
        onPrivacyModeChange={setPrivacyMode}
        onResetBench={handleClearChat}
        emergencyStop={emergencyStop}
        onOpenQuickSearch={() => setIsVaultOpen(true)}
        onToggleMobileDrawer={() => setIsMobileDrawerOpen(true)}
        availableModels={availableModels}
        selectedModel={selectedModel}
      />
      {errorMessage && (
        <div className="px-4 py-1.5 bg-rose-950/80 border-b border-rose-800 text-rose-200 flex items-center justify-between text-xs font-mono z-30">
          <div className="flex items-center gap-2"><AlertCircle className="w-3.5 h-3.5 text-rose-400 flex-shrink-0" /><span>[COMMAND CENTER NOTICE]: {errorMessage}</span></div>
          <button onClick={() => setErrorMessage(null)} className="text-rose-400 hover:text-white p-0.5"><X className="w-3.5 h-3.5" /></button>
        </div>
      )}
      <input type="file" ref={fileInputRef} onChange={(e) => e.target.files?.[0] && handleFileSelect(e.target.files[0])} accept="image/jpeg,image/png,image/webp,image/gif,application/pdf,text/plain,text/markdown,.pdf,.txt,.md" className="hidden" />

      {/* Desktop: Full 3-panel grid */}
      <main className="hidden lg:flex-1 lg:min-h-0 lg:w-full lg:overflow-y-auto lg:overflow-hidden lg:p-2 lg:p-3 lg:grid lg:grid-cols-12 lg:gap-3">
        <div className="lg:flex lg:col-span-3 min-h-0 flex-col overflow-hidden">
          <TelemetryLeftPanel telemetry={systemTelemetry} isLoading={isTelemetryLoading} onRefresh={() => void pollSystem()} />
        </div>
        <div className="lg:flex lg:col-span-6 flex flex-col gap-2 min-h-0 overflow-hidden">
          <AiCoreVisualizer voiceState={voiceState} cognitiveStep={cognitiveStep} isStreaming={isLoading} />
          <div className="flex items-center justify-between px-2.5 py-1 bg-slate-900/70 border border-slate-800 rounded-lg text-xs">
            <div className="flex items-center gap-1">
              <button onClick={() => setCenterView('feed')} className={`px-2.5 py-0.5 rounded text-[11px] transition-colors ${centerView === 'feed' ? 'bg-cyan-500/20 text-cyan-300 font-bold border border-cyan-500/30' : 'text-slate-400 hover:text-white'}`}>Diagnostic Feed {messages.length > 0 && `(${messages.length})`}</button>
              <button onClick={() => setCenterView('deck')} className={`px-2.5 py-0.5 rounded text-[11px] transition-colors flex items-center gap-1 ${centerView === 'deck' ? 'bg-cyan-500/20 text-cyan-300 font-bold border border-cyan-500/30' : 'text-slate-400 hover:text-white'}`}>Optical Scope {activeDutImage && <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-pulse" />}</button>
            </div>
            {activeDutName && <span className="text-[10px] text-slate-400 truncate max-w-[140px]">{activeDutName}</span>}
          </div>
          <div className="flex-1 min-h-0 overflow-hidden flex flex-col">
            {centerView === 'deck' ? (
              <InspectionDeck activeDutImage={activeDutImage} activeDutName={activeDutName} attachedFile={attachedFile} isLoading={isLoading} onFileSelect={handleFileSelect} onEjectDut={handleEjectDut} onReplaceDut={() => fileInputRef.current?.click()} onQuickAction={(p) => { setInputPrompt(p); setCenterView('feed'); }} vaultConceptCount={vaultConcepts} />
            ) : (
              <DiagnosticFeed messages={messages} isLoading={isLoading} inputPrompt={inputPrompt} onInputChange={setInputPrompt} onSendMessage={() => void handleSendMessage()} attachedFile={attachedFile} onRemoveAttachment={removeAttachedFile} onAttachClick={() => fileInputRef.current?.click()} textareaRef={textareaRef} isVoiceEnabled={isVoiceEnabled} isListening={isListening} isSpeaking={isSpeaking} onToggleListening={() => (isListening ? stopListening() : void startListening())} onQuickAction={(p) => setInputPrompt(p)} speakingMessageId={speakingMsgId} onReadAloud={handleReadAloud} responseStyle={responseStyle} onResponseStyleChange={setResponseStyle} cognitiveStep={cognitiveStep} onSaveToVault={async (t) => { await sendFeedbackToVault(t); setVaultConcepts((c) => c + 1); }} voiceState={voiceState} onHardResetVoice={hardResetVoice} liveTranscript={liveTranscript} voiceError={voiceError} onClearVoiceError={clearVoiceError} hideInput />
            )}
          </div>
        </div>
        <div className="lg:flex lg:col-span-3 min-h-0 flex-col gap-3 overflow-y-auto">
          <TasksApprovalsPanel operations={operations} onDecision={handleDecision} />
          <QuickActionsRail onVoiceCommand={() => (isListening ? stopListening() : void startListening())} onSystemScan={() => void pollSystem()} onClearContext={handleClearChat} onEmergencyStop={handleEmergencyStop} onTakeControl={handleTakeControl} emergencyStop={emergencyStop} provider={selectedModel} modelId={selectedModel} />
        </div>
      </main>

      {/* Mobile: Clean 3-zone layout (Top Bar + Full-Bleed Chat + Bottom Prompt) */}
      <div className="lg:hidden flex-1 min-h-0 flex flex-col">
        <DiagnosticFeed messages={messages} isLoading={isLoading} inputPrompt={inputPrompt} onInputChange={setInputPrompt} onSendMessage={() => void handleSendMessage()} attachedFile={attachedFile} onRemoveAttachment={removeAttachedFile} onAttachClick={() => fileInputRef.current?.click()} textareaRef={textareaRef} isVoiceEnabled={isVoiceEnabled} isListening={isListening} isSpeaking={isSpeaking} onToggleListening={() => (isListening ? stopListening() : void startListening())} onQuickAction={(p) => setInputPrompt(p)} speakingMessageId={speakingMsgId} onReadAloud={handleReadAloud} responseStyle={responseStyle} onResponseStyleChange={setResponseStyle} cognitiveStep={cognitiveStep} onSaveToVault={async (t) => { await sendFeedbackToVault(t); setVaultConcepts((c) => c + 1); }} voiceState={voiceState} onHardResetVoice={hardResetVoice} liveTranscript={liveTranscript} voiceError={voiceError} onClearVoiceError={clearVoiceError} hideInput mobileFullBleed />
      </div>

      <BottomCommandDock inputPrompt={inputPrompt} onInputChange={setInputPrompt} onSendMessage={() => void handleSendMessage()} isLoading={isLoading} isListening={isListening} isSpeaking={isSpeaking} isVoiceEnabled={isVoiceEnabled} onToggleVoiceMode={toggleVoiceMode} onToggleListening={() => (isListening ? stopListening() : void startListening())} autoApprove={autoApprove} onToggleAutoApprove={() => setAutoApprove((a) => !a)} onAttachClick={() => fileInputRef.current?.click()} attachedFile={attachedFile} onRemoveAttachment={removeAttachedFile} liveTranscript={liveTranscript} voiceState={voiceState} />
      <AiCoreSettingsModal isOpen={currentTab === 'core' || currentTab === 'settings'} onClose={() => setCurrentTab('command')} availableModels={availableModels} selectedModel={selectedModel} onSelectModel={setSelectedModel} privacyMode={privacyMode} onPrivacyModeChange={setPrivacyMode} />
      <AiVoiceSettingsModal isOpen={currentTab === 'voice'} onClose={() => setCurrentTab('command')} voiceSettings={voiceSettings} onUpdateVoiceSettings={updateVoiceSettings} onTestVoice={testVoicePersona} />
      <AuthModal isOpen={isAuthModalOpen} onClose={() => setIsAuthModalOpen(false)} onSuccess={setCurrentUser} />
      <VaultDrawer isOpen={isVaultOpen} onClose={() => setIsVaultOpen(false)} currentUser={currentUser} currentMessages={messages} currentDutImage={activeDutImage} onRestoreSession={(r) => { setMessages(r.messages); if (r.dutImage) { setActiveDutImage(r.dutImage); setActiveDutName('Archived Component'); } }} onOpenAuthModal={() => setIsAuthModalOpen(true)} onSessionsChange={setVaultCount} />
      <MobileDrawer
        isOpen={isMobileDrawerOpen}
        onClose={() => setIsMobileDrawerOpen(false)}
        currentUser={currentUser}
        onLogout={() => { setCurrentUser(null); setIsMobileDrawerOpen(false); }}
        onOpenVault={() => setIsVaultOpen(true)}
        onOpenAuth={() => { setIsAuthModalOpen(true); setIsMobileDrawerOpen(false); }}
        onOpenSettings={() => { setCurrentTab('settings'); setIsMobileDrawerOpen(false); }}
        centerView={centerView}
        onToggleCenterView={setCenterView}
        activeDutImage={activeDutImage}
        operations={operations}
        onDecision={handleDecision}
        systemTelemetry={systemTelemetry}
        isListening={isListening}
        isSpeaking={isSpeaking}
        isVoiceEnabled={isVoiceEnabled}
        onToggleVoice={toggleVoiceMode}
        onToggleListening={() => (isListening ? stopListening() : void startListening())}
        responseStyle={responseStyle}
        onResponseStyleChange={setResponseStyle}
        availableModels={availableModels}
        selectedModel={selectedModel}
        onSelectModel={setSelectedModel}
        onSystemScan={() => void pollSystem()}
        onClearContext={handleClearChat}
        onEmergencyStop={handleEmergencyStop}
        onTakeControl={handleTakeControl}
        emergencyStop={emergencyStop}
        autoApprove={autoApprove}
        onToggleAutoApprove={() => setAutoApprove((a) => !a)}
      />
    </div>
  );
}
