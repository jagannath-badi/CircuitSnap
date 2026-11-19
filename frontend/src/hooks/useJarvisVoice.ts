import { useState, useEffect, useRef, useCallback } from 'react';

export type VoiceState = 'idle' | 'listening' | 'transcribing' | 'speaking';

export interface VoiceSettings {
  voiceId: 'en-GB-SoniaNeural' | 'en-US-AriaNeural' | 'en-US-JennyNeural' | 'en-GB-RyanNeural';
  interactionMode: 'single' | 'live';
  speechRate: number;
  autoSpeak: boolean;
}

export const DEFAULT_VOICE_SETTINGS: VoiceSettings = {
  voiceId: 'en-GB-SoniaNeural',
  interactionMode: 'live',
  speechRate: 1.04,
  autoSpeak: true,
};

const SETTINGS_STORAGE_KEY = 'circuitsnap_voice_settings';

export function loadVoiceSettings(): VoiceSettings {
  if (typeof window === 'undefined') return DEFAULT_VOICE_SETTINGS;
  try {
    const raw = localStorage.getItem(SETTINGS_STORAGE_KEY);
    if (!raw) return DEFAULT_VOICE_SETTINGS;
    return { ...DEFAULT_VOICE_SETTINGS, ...JSON.parse(raw) };
  } catch {
    return DEFAULT_VOICE_SETTINGS;
  }
}

export function saveVoiceSettings(settings: VoiceSettings): void {
  if (typeof window === 'undefined') return;
  try {
    localStorage.setItem(SETTINGS_STORAGE_KEY, JSON.stringify(settings));
  } catch {
    // ignore
  }
}

export interface UseJarvisVoiceOptions {
  onTranscript?: (transcript: string) => void;
  onFinalTranscript?: (transcript: string) => void;
}

export function stripWakeWord(raw: string): string {
  return raw.trim().replace(/^(?:hey|hi|hello|ok|okay)?\s*jarvis[\s,.:!?-]*/i, '').trim() || raw.trim();
}

export function cleanTextForSpeech(raw: string): string {
  if (!raw?.trim()) return 'Specifications and calculations are displayed on screen.';

  let text = raw
    .replace(/J\.A\.R\.V\.I\.S\.?/gi, 'Jarvis')
    .replace(/\bJARVIS\b/g, 'Jarvis')
    .replace(/```[\s\S]*?```/g, ' ')
    .replace(/`([^`]+)`/g, '$1')
    .replace(/^\s*\|.*\|\s*$/gm, ' ')
    .replace(/\|[^\n]+\|/g, ' ')
    .replace(/\|+/g, ' ')
    .replace(/(?:^|\n)\s*#{1,6}\s*/g, ' ')
    .replace(/\[\s*(?:CONFIRMED|LIKELY|CANNOT CONFIRM)\s*\]\s*[:\-–—]?/gi, '')
    .replace(/\b(?:CONFIRMED|CANNOT CONFIRM|LIKELY)\b\s*[:\-–—]?/gi, '')
    .replace(/(?:^|\n)\s*[-*+]\s+/g, ' ')
    .replace(/(?:^|\n)\s*\d+\.\s+/g, ' ')
    .replace(/\$\$([\s\S]*?)\$\$/g, ' $1 ')
    .replace(/\$([^$]+)\$/g, ' $1 ')
    .replace(/\\frac\{([^}]+)\}\{([^}]+)\}/g, '$1 over $2')
    .replace(/\\sqrt\{([^}]+)\}/g, 'square root of $1')
    .replace(/\\cdot|\\times/g, ' times ')
    .replace(/\\approx/g, ' approximately ')
    .replace(/\\implies|=>/g, ' implies ')
    .replace(/\\to|->/g, ' leads to ')
    .replace(/\\pi/g, 'pi')
    .replace(/\\mu/g, 'micro')
    .replace(/\\Omega/g, 'ohms')
    .replace(/\\mathbf\{([^}]+)\}/g, '$1')
    .replace(/\\text\{([^}]+)\}/g, '$1')
    .replace(/\\[,;!]/g, ' ')
    .replace(/\\[a-zA-Z]+/g, ' ')
    .replace(/\$/g, '')
    .replace(/(\d+(?:\.\d+)?)\s*MΩ/g, '$1 mega-ohms')
    .replace(/(\d+(?:\.\d+)?)\s*kΩ/g, '$1 kilo-ohms')
    .replace(/(\d+(?:\.\d+)?)\s*Ω/g, '$1 ohms')
    .replace(/(\d+(?:\.\d+)?)\s*µF/g, '$1 microfarads')
    .replace(/(\d+(?:\.\d+)?)\s*uF/g, '$1 microfarads')
    .replace(/(\d+(?:\.\d+)?)\s*nF/g, '$1 nanofarads')
    .replace(/(\d+(?:\.\d+)?)\s*pF/g, '$1 picofarads')
    .replace(/(\d+(?:\.\d+)?)\s*mH/g, '$1 millihenries')
    .replace(/(\d+(?:\.\d+)?)\s*µH/g, '$1 microhenries')
    .replace(/(\d+(?:\.\d+)?)\s*uH/g, '$1 microhenries')
    .replace(/(\d+(?:\.\d+)?)\s*kHz/g, '$1 kilohertz')
    .replace(/(\d+(?:\.\d+)?)\s*MHz/g, '$1 megahertz')
    .replace(/(\d+(?:\.\d+)?)\s*GHz/g, '$1 gigahertz')
    .replace(/(\d+(?:\.\d+)?)\s*Hz/g, '$1 hertz')
    .replace(/(\d+(?:\.\d+)?)\s*mA/g, '$1 milliamps')
    .replace(/(\d+(?:\.\d+)?)\s*mV/g, '$1 millivolts')
    .replace(/(\d+(?:\.\d+)?)\s*V(?![a-zA-Z])/g, '$1 volts')
    .replace(/(\d+(?:\.\d+)?)\s*W(?![a-zA-Z])/g, '$1 watts')
    .replace(/<[^>]+>/g, ' ')
    .replace(/[*_~`>#]+/g, ' ')
    .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1')
    .replace(/\\/g, ' ')
    .replace(/\r?\n+/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();

  if (text.length < 12) return 'Specifications and calculations are displayed on screen.';

  if (text.length > 480) {
    const cut = text.substring(0, 480);
    const lastPeriod = Math.max(cut.lastIndexOf('. '), cut.lastIndexOf('! '), cut.lastIndexOf('? '));
    text = lastPeriod > 220 ? cut.substring(0, lastPeriod + 1) : cut.substring(0, cut.lastIndexOf(' ')).replace(/[,;:-]+$/, '') + '.';
  }
  return text;
}

const formatMicError = (err: unknown): string => {
  const name = (err as { name?: string })?.name || '';
  switch (name) {
    case 'NotAllowedError': case 'PermissionDeniedError':
      return 'Microphone permission denied. Allow mic access in browser settings, then tap the mic again.';
    case 'NotFoundError': case 'DevicesNotFoundError':
      return 'No microphone detected. Connect a mic or headset, then retry.';
    case 'OverconstrainedError': case 'ConstraintNotSatisfiedError':
      return 'Microphone constraints not satisfied. Try a different input device.';
    case 'NotSupportedError':
      return 'Media devices not supported in this browser or context.';
    case 'AbortError':
      return 'Microphone access interrupted. Please try again.';
    default:
      return `Microphone error: ${(err as Error)?.message || 'unknown error'}`;
  }
};

const pickMimeType = (): string | undefined => {
  for (const t of ['audio/webm', 'audio/mp4', 'audio/ogg']) {
    if (MediaRecorder.isTypeSupported(t)) return t;
  }
  return undefined;
};

export function useJarvisVoice({ onTranscript, onFinalTranscript }: UseJarvisVoiceOptions = {}) {
  const [isVoiceEnabled, setIsVoiceEnabled] = useState(true);
  const [voiceState, setVoiceState] = useState<VoiceState>('idle');
  const [voiceSettings, setVoiceSettingsState] = useState<VoiceSettings>(loadVoiceSettings);
  const [liveTranscript, setLiveTranscript] = useState('');
  const [voiceError, setVoiceError] = useState<string | null>(null);

  const [supported] = useState(() =>
    typeof navigator !== 'undefined' && 'mediaDevices' in navigator && 'MediaRecorder' in window
  );

  // SpeechRecognition is WebKit-prefixed; declare ambient types
  interface SpeechRecognition extends EventTarget {
    continuous: boolean; interimResults: boolean; lang: string;
    start(): void; stop(): void; abort(): void;
    onresult: (event: SpeechRecognitionEvent) => void;
    onerror: (event: SpeechRecognitionErrorEvent) => void;
  }
  interface SpeechRecognitionEvent extends Event { results: SpeechRecognitionResultList; }
  interface SpeechRecognitionResultList { length: number; [index: number]: SpeechRecognitionResult; }
  interface SpeechRecognitionResult { 0: SpeechRecognitionAlternative; }
  interface SpeechRecognitionAlternative { transcript: string; }
  interface SpeechRecognitionErrorEvent extends Event { error: string; }

  const streamRef = useRef<MediaStream | null>(null);
  const audioCtxRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const recognitionRef = useRef<SpeechRecognition | null>(null);
  const latestLiveTranscriptRef = useRef('');
  const vadIntervalRef = useRef<number | null>(null);
  const recordingTimerRef = useRef<number | null>(null);
  const rearmTimerRef = useRef<number | null>(null);
  const sttAbortControllerRef = useRef<AbortController | null>(null);
  const ttsAbortControllerRef = useRef<AbortController | null>(null);
  const hasQualifiedSpeechRef = useRef(false);
  const activeSpeechMsRef = useRef(0);
  const audioElRef = useRef<HTMLAudioElement | null>(null);
  const onTranscriptRef = useRef(onTranscript);
  const onFinalTranscriptRef = useRef(onFinalTranscript);
  const isVoiceEnabledRef = useRef(isVoiceEnabled);
  const voiceStateRef = useRef(voiceState);
  const voiceSettingsRef = useRef(voiceSettings);
  const startListeningRef = useRef<() => Promise<void>>(() => Promise.resolve());

  useEffect(() => {
    onTranscriptRef.current = onTranscript;
    onFinalTranscriptRef.current = onFinalTranscript;
    isVoiceEnabledRef.current = isVoiceEnabled;
    voiceStateRef.current = voiceState;
    voiceSettingsRef.current = voiceSettings;
  }, [onTranscript, onFinalTranscript, isVoiceEnabled, voiceState, voiceSettings]);

  const updateVoiceSettings = useCallback((partial: Partial<VoiceSettings>) => {
    setVoiceSettingsState((prev) => {
      const next = { ...prev, ...partial };
      saveVoiceSettings(next);
      return next;
    });
  }, []);

  useEffect(() => {
    if (typeof Audio !== 'undefined') audioElRef.current = new Audio();
    return () => {
      if (audioElRef.current) { audioElRef.current.pause(); audioElRef.current.src = ''; }
    };
  }, []);

  const clearVoiceError = useCallback(() => setVoiceError(null), []);

  const hardResetVoice = useCallback(() => {
    [vadIntervalRef, recordingTimerRef, rearmTimerRef].forEach(r => { if (r.current) { clearTimeout(r.current); r.current = null; } });
    if (recognitionRef.current) { try { recognitionRef.current.abort(); } catch {} recognitionRef.current = null; }
    [sttAbortControllerRef, ttsAbortControllerRef].forEach(r => { if (r.current) { r.current.abort(); r.current = null; } });
    const mr = mediaRecorderRef.current;
    if (mr && mr.state !== 'inactive') { try { mr.onstop = null; mr.stop(); } catch {} }
    mediaRecorderRef.current = null; chunksRef.current = [];
    if (streamRef.current) { streamRef.current.getTracks().forEach(t => t.stop()); streamRef.current = null; }
    const actx = audioCtxRef.current;
    if (actx && actx.state !== 'closed') { try { actx.close(); } catch {} audioCtxRef.current = null; }
    analyserRef.current = null;
    if (audioElRef.current) { audioElRef.current.pause(); audioElRef.current.currentTime = 0; audioElRef.current.src = ''; }
    if (typeof window !== 'undefined' && 'speechSynthesis' in window) window.speechSynthesis.cancel();
    hasQualifiedSpeechRef.current = false; activeSpeechMsRef.current = 0; latestLiveTranscriptRef.current = '';
    setLiveTranscript(''); setVoiceError(null); setVoiceState('idle');
  }, []);

  const cancelSpeech = useCallback(() => {
    if (audioElRef.current) { audioElRef.current.pause(); audioElRef.current.currentTime = 0; }
    if (typeof window !== 'undefined' && 'speechSynthesis' in window) window.speechSynthesis.cancel();
    if (voiceStateRef.current === 'speaking') setVoiceState('idle');
  }, []);

  const stopListeningInternal = useCallback((allowProcessing: boolean) => {
    if (vadIntervalRef.current) { clearInterval(vadIntervalRef.current); vadIntervalRef.current = null; }
    if (recordingTimerRef.current) { clearTimeout(recordingTimerRef.current); recordingTimerRef.current = null; }
    if (recognitionRef.current) { try { recognitionRef.current.stop(); } catch {} recognitionRef.current = null; }
    if (!allowProcessing) { hasQualifiedSpeechRef.current = false; activeSpeechMsRef.current = 0; }
    const mr = mediaRecorderRef.current;
    if (mr && mr.state !== 'inactive') { try { mr.stop(); } catch {} }
    if (streamRef.current) { streamRef.current.getTracks().forEach(t => t.stop()); streamRef.current = null; }
    const actx = audioCtxRef.current;
    if (actx && actx.state !== 'closed') { try { actx.close(); } catch {} audioCtxRef.current = null; }
    if (voiceStateRef.current === 'listening') setVoiceState(allowProcessing && hasQualifiedSpeechRef.current ? 'transcribing' : 'idle');
  }, []);

  // Browser TTS fallback
  const fallbackBrowserSpeak = useCallback((rawText: string, onEnd?: () => void, targetVoiceId?: VoiceSettings['voiceId']) => {
    if (typeof window === 'undefined' || !('speechSynthesis' in window)) { setVoiceState('idle'); onEnd?.(); return; }
    window.speechSynthesis.cancel();
    const cleaned = cleanTextForSpeech(rawText);
    const utterance = new SpeechSynthesisUtterance(cleaned);
    utterance.pitch = 1.0; utterance.rate = voiceSettingsRef.current.speechRate;
    const targetLang = (targetVoiceId || voiceSettingsRef.current.voiceId).startsWith('en-GB') ? 'en-GB' : 'en-US';
    const chosenVoice = window.speechSynthesis.getVoices().find(v => v.lang.startsWith(targetLang));
    if (chosenVoice) utterance.voice = chosenVoice;
    utterance.onend = () => { setVoiceState('idle'); onEnd?.(); if (isVoiceEnabledRef.current && voiceSettingsRef.current.interactionMode === 'live') { rearmTimerRef.current = window.setTimeout(() => void startListeningRef.current(), 800); } };
    utterance.onerror = () => { setVoiceState('idle'); onEnd?.(); };
    setVoiceState('speaking'); window.speechSynthesis.speak(utterance);
  }, []);

  // Neural TTS via /api/tts
  const speak = useCallback(async (rawText: string, onEndCallback?: () => void, force = false, overrideVoiceId?: VoiceSettings['voiceId']) => {
    if (!isVoiceEnabledRef.current && !force) return;
    if (!voiceSettingsRef.current.autoSpeak && !force) return;
    stopListeningInternal(false); cancelSpeech();
    const cleaned = cleanTextForSpeech(rawText);
    if (!cleaned) { setVoiceState('idle'); return; }
    setVoiceState('speaking');
    const rateStr = `${Math.round((voiceSettingsRef.current.speechRate - 1) * 100) >= 0 ? '+' : ''}${Math.round((voiceSettingsRef.current.speechRate - 1) * 100)}%`;
    const activeVoice = overrideVoiceId || voiceSettingsRef.current.voiceId;
    const controller = new AbortController(); ttsAbortControllerRef.current = controller;
    const timeoutId = setTimeout(() => controller.abort(), 8000);
    try {
      const res = await fetch('/api/tts', { method: 'POST', signal: controller.signal, headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ text: cleaned, voice: activeVoice, rate: rateStr }) });
      clearTimeout(timeoutId); ttsAbortControllerRef.current = null;
      if (!res.ok) throw new Error(`TTS server error: ${res.status}`);
      const blob = await res.blob(); const audioUrl = URL.createObjectURL(blob);
      const audio = audioElRef.current || new Audio(); audioElRef.current = audio;
      const handleEnded = () => { URL.revokeObjectURL(audioUrl); audio.removeEventListener('ended', handleEnded); audio.removeEventListener('error', handleError); setVoiceState('idle'); onEndCallback?.(); if (isVoiceEnabledRef.current && voiceSettingsRef.current.interactionMode === 'live') rearmTimerRef.current = window.setTimeout(() => void startListeningRef.current(), 800); };
      const handleError = () => { URL.revokeObjectURL(audioUrl); audio.removeEventListener('ended', handleEnded); audio.removeEventListener('error', handleError); fallbackBrowserSpeak(rawText, onEndCallback, activeVoice); };
      audio.addEventListener('ended', handleEnded); audio.addEventListener('error', handleError); audio.src = audioUrl; await audio.play();
    } catch (err) { clearTimeout(timeoutId); ttsAbortControllerRef.current = null; if ((err as Error)?.name !== 'AbortError') fallbackBrowserSpeak(rawText, onEndCallback, activeVoice); else setVoiceState('idle'); }
  }, [cancelSpeech, fallbackBrowserSpeak, stopListeningInternal]);

  const startListening = useCallback(async () => {
    if (!navigator.mediaDevices?.getUserMedia || voiceStateRef.current === 'listening' || voiceStateRef.current === 'transcribing') return;
    cancelSpeech(); setVoiceError(null); setLiveTranscript(''); latestLiveTranscriptRef.current = '';
    try {
      if (streamRef.current) streamRef.current.getTracks().forEach(t => t.stop());
      let stream: MediaStream;
      try { stream = await navigator.mediaDevices.getUserMedia({ audio: { echoCancellation: true, noiseSuppression: true, autoGainControl: true } }); }
      catch (err) { setVoiceError(formatMicError(err)); setVoiceState('idle'); return; }
      streamRef.current = stream;
      const AudioCtxClass = window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext;
      const audioCtx = new AudioCtxClass(); audioCtxRef.current = audioCtx;
      if (audioCtx.state === 'suspended') await audioCtx.resume();
      const source = audioCtx.createMediaStreamSource(stream); const analyser = audioCtx.createAnalyser();
      analyser.fftSize = 512; source.connect(analyser); analyserRef.current = analyser;
      const mimeType = pickMimeType();
      const mediaRecorder = new MediaRecorder(stream, mimeType ? { mimeType } : undefined);
      mediaRecorderRef.current = mediaRecorder; chunksRef.current = [];
      mediaRecorder.ondataavailable = e => { if (e.data?.size) chunksRef.current.push(e.data); };
      mediaRecorder.onstop = async () => {
        if (recognitionRef.current) { try { recognitionRef.current.abort(); } catch {} recognitionRef.current = null; }
        const chunks = chunksRef.current; const liveFallbackText = latestLiveTranscriptRef.current.trim();
        if (liveFallbackText) hasQualifiedSpeechRef.current = true;
        const qualified = hasQualifiedSpeechRef.current || chunks.length > 0; let sttDispatched = false;
        if (chunks.length > 0 && qualified && voiceStateRef.current !== 'speaking') {
          setVoiceState('transcribing');
          const audioBlob = new Blob(chunks, mimeType ? { type: mimeType } : undefined);
          const controller = new AbortController(); sttAbortControllerRef.current = controller; const timeoutId = setTimeout(() => controller.abort(), 8000);
          try {
            const formData = new FormData(); formData.append('file', audioBlob, `speech.${mimeType?.includes('ogg') ? 'ogg' : mimeType?.includes('mp4') ? 'mp4' : 'webm'}`);
            const res = await fetch('/api/stt', { method: 'POST', body: formData, signal: controller.signal });
            clearTimeout(timeoutId); sttAbortControllerRef.current = null;
            if (res.ok) { const data = await res.json(); const clean = stripWakeWord(data.text || ''); if (clean.trim()) { sttDispatched = true; setVoiceError(null); setLiveTranscript(clean.trim()); onTranscriptRef.current?.(clean.trim()); onFinalTranscriptRef.current?.(clean.trim()); setTimeout(() => setLiveTranscript(''), 1000); } }
          } catch (err) { clearTimeout(timeoutId); sttAbortControllerRef.current = null; if ((err as Error)?.name !== 'AbortError') console.warn('STT upload error:', err); }
        }
        if (!sttDispatched) {
          const fallbackText = stripWakeWord(latestLiveTranscriptRef.current);
          if (fallbackText.trim() && voiceStateRef.current !== 'speaking') { setVoiceError(null); setLiveTranscript(fallbackText.trim()); onTranscriptRef.current?.(fallbackText.trim()); onFinalTranscriptRef.current?.(fallbackText.trim()); setTimeout(() => setLiveTranscript(''), 1000); }
          else { setVoiceError(recognitionRef.current ? 'Speech detected but transcription unavailable — backend STT offline, using browser fallback' : 'No speech detected — check mic input or speak closer'); setTimeout(() => setLiveTranscript(''), 600); }
        }
        hasQualifiedSpeechRef.current = false; activeSpeechMsRef.current = 0; latestLiveTranscriptRef.current = '';
        if (voiceStateRef.current === 'transcribing') setVoiceState('idle');
      };
      // Parallel browser SpeechRecognition for interim + final fallback
      if (typeof window !== 'undefined') {
        const SpeechRec = (window as unknown as { SpeechRecognition?: any }).SpeechRecognition || (window as unknown as { webkitSpeechRecognition?: any }).webkitSpeechRecognition;
        if (SpeechRec) {
          try { const rec = new SpeechRec(); rec.continuous = true; rec.interimResults = true; rec.lang = 'en-US'; rec.onresult = (e: SpeechRecognitionEvent) => { let interim = ''; for (let i = 0; i < e.results.length; i++) interim += e.results[i][0].transcript; const t = interim.trim(); if (t) { latestLiveTranscriptRef.current = t; setLiveTranscript(t); onTranscriptRef.current?.(t); } }; rec.onerror = () => {}; rec.start(); recognitionRef.current = rec; } catch {}
        }
      }
      mediaRecorder.start(250); setVoiceState('listening');
      hasQualifiedSpeechRef.current = false; activeSpeechMsRef.current = 0; let silenceStart: number | null = null; const startTime = Date.now(); const timeDomainData = new Uint8Array(analyser.fftSize);
      recordingTimerRef.current = window.setTimeout(() => stopListeningInternal(true), 15000);
      vadIntervalRef.current = window.setInterval(() => {
        if (voiceStateRef.current === 'speaking') { stopListeningInternal(false); return; }
        analyser.getByteTimeDomainData(timeDomainData);
        let sumSquares = 0; for (let i = 0; i < timeDomainData.length; i++) { const n = (timeDomainData[i] - 128) / 128; sumSquares += n * n; }
        const rms = Math.sqrt(sumSquares / timeDomainData.length);
        const hasLiveWords = latestLiveTranscriptRef.current.trim().length > 0;
        if (hasLiveWords) hasQualifiedSpeechRef.current = true;
        if (rms > 0.012 || hasLiveWords) { activeSpeechMsRef.current += 50; if (activeSpeechMsRef.current >= 150 || hasLiveWords) { hasQualifiedSpeechRef.current = true; silenceStart = null; } }
        else if (hasQualifiedSpeechRef.current) { if (silenceStart === null) silenceStart = Date.now(); else if (Date.now() - silenceStart > 1200) stopListeningInternal(true); }
        else if (Date.now() - startTime > 7000) stopListeningInternal(false);
      }, 50);
    } catch (err) { console.warn('Microphone init failed:', err); setVoiceState('idle'); }
  }, [cancelSpeech, stopListeningInternal]);
  startListeningRef.current = startListening;

  const stopListening = useCallback(() => { hasQualifiedSpeechRef.current = true; stopListeningInternal(true); }, [stopListeningInternal]);
  const testVoicePersona = useCallback(async (voiceId?: string) => { const v = (voiceId as VoiceSettings['voiceId']) || voiceSettingsRef.current.voiceId; const sample = v.includes('Sonia') ? 'Jarvis online. Sonia British neural persona active.' : v.includes('Aria') ? 'Aria studio persona initialized.' : v.includes('Jenny') ? 'Jenny tutor persona online.' : 'Ryan classic British persona active.'; await speak(sample, undefined, true, v); }, [speak]);

  useEffect(() => () => hardResetVoice(), [hardResetVoice]);
  const toggleVoiceMode = useCallback(() => { setIsVoiceEnabled(p => { const n = !p; isVoiceEnabledRef.current = n; if (n) void speak('Jarvis voice systems online.', () => void startListeningRef.current(), true); else hardResetVoice(); return n; }); }, [hardResetVoice, speak]);

  return { isVoiceEnabled, voiceState, isListening: voiceState === 'listening', isSpeaking: voiceState === 'speaking', isTranscribing: voiceState === 'transcribing', supported, voiceSettings, liveTranscript, voiceError, clearVoiceError, updateVoiceSettings, toggleVoiceMode, startListening, stopListening, speak, cancelSpeech, stopSpeaking: cancelSpeech, hardResetVoice, testVoicePersona };
}