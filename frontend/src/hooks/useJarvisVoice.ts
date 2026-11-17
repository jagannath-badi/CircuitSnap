import { useState, useEffect, useRef, useCallback } from 'react';

export type VoiceState = 'idle' | 'listening' | 'transcribing' | 'speaking';

export interface VoiceSettings {
  voiceId: 'en-GB-SoniaNeural' | 'en-US-AriaNeural' | 'en-US-JennyNeural' | 'en-GB-RyanNeural';
  interactionMode: 'single' | 'live';
  speechRate: number; // 0.85 to 1.25, default 1.04
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
    const parsed = JSON.parse(raw);
    return { ...DEFAULT_VOICE_SETTINGS, ...parsed };
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

/**
 * Strips wake words (e.g. "Hey Jarvis, decode brown black red gold" -> "decode brown black red gold").
 * If the user only said "Hey Jarvis" or "Jarvis", preserves it so the greeting handler fires.
 */
export function stripWakeWord(raw: string): string {
  const trimmed = raw.trim();
  const stripped = trimmed.replace(/^(?:hey|hi|hello|ok|okay)?\s*jarvis[\s,.:!?-]*/i, '').trim();
  return stripped.length > 0 ? stripped : trimmed;
}

/**
 * Strips raw markdown, HTML, code blocks, tables, and KaTeX math symbols into spoken plain English.
 * Ensures "Jarvis" is pronounced smoothly as a word and provides an intelligent fallback for table-heavy responses.
 */
export function cleanTextForSpeech(raw: string): string {
  if (!raw || !raw.trim()) {
    return 'Specifications and calculations are displayed on screen.';
  }

  let titleHeading = '';
  const headingMatch = raw.match(/(?:^|\n)\s*#{1,6}\s*(?:\[\s*(?:CONFIRMED|LIKELY|CANNOT CONFIRM)\s*\])?\s*([^\n#|]+)/i);
  if (headingMatch && headingMatch[1]) {
    titleHeading = headingMatch[1].replace(/[*_`]/g, '').trim();
    titleHeading = titleHeading.replace(/J\.A\.R\.V\.I\.S\.?/gi, 'Jarvis').replace(/\bJARVIS\b/g, 'Jarvis');
  }

  let text = raw;
  text = text.replace(/J\.A\.R\.V\.I\.S\.?/gi, 'Jarvis');
  text = text.replace(/\bJARVIS\b/g, 'Jarvis');
  text = text.replace(/```[\s\S]*?```/g, ' ');
  text = text.replace(/`([^`]+)`/g, '$1');
  text = text.replace(/^\s*\|.*\|\s*$/gm, ' ');
  text = text.replace(/\|[^\n]+\|/g, ' ');
  text = text.replace(/(?:^|\n)\s*#{1,6}\s*/g, ' ');
  text = text.replace(/\[\s*(?:CONFIRMED|LIKELY|CANNOT CONFIRM)\s*\]\s*[:\-\u2013\u2014]?/gi, '');
  text = text.replace(/\b(?:CONFIRMED|CANNOT CONFIRM)\b\s*[:\-\u2013\u2014]?/gi, '');

  text = text.replace(/\$\$([\s\S]*?)\$\$/g, ' $1 ');
  text = text.replace(/\$([^$]+)\$/g, ' $1 ');
  text = text.replace(/\\frac\{([^}]+)\}\{([^}]+)\}/g, '$1 over $2');
  text = text.replace(/\\sqrt\{([^}]+)\}/g, 'square root of $1');
  text = text.replace(/\\cdot|\\times/g, ' times ');
  text = text.replace(/\\approx/g, ' approximately ');
  text = text.replace(/\\pi/g, 'pi');
  text = text.replace(/\\mu/g, 'micro');
  text = text.replace(/\\Omega/g, 'ohms');
  text = text.replace(/\\mathbf\{([^}]+)\}/g, '$1');
  text = text.replace(/\\text\{([^}]+)\}/g, '$1');
  text = text.replace(/\\[a-zA-Z]+/g, ' ');

  text = text.replace(/(\d+(?:\.\d+)?)\s*MΩ/g, '$1 mega-ohms');
  text = text.replace(/(\d+(?:\.\d+)?)\s*kΩ/g, '$1 kilo-ohms');
  text = text.replace(/(\d+(?:\.\d+)?)\s*Ω/g, '$1 ohms');
  text = text.replace(/(\d+(?:\.\d+)?)\s*µF/g, '$1 microfarads');
  text = text.replace(/(\d+(?:\.\d+)?)\s*uF/g, '$1 microfarads');
  text = text.replace(/(\d+(?:\.\d+)?)\s*nF/g, '$1 nanofarads');
  text = text.replace(/(\d+(?:\.\d+)?)\s*pF/g, '$1 picofarads');
  text = text.replace(/(\d+(?:\.\d+)?)\s*mH/g, '$1 millihenries');
  text = text.replace(/(\d+(?:\.\d+)?)\s*µH/g, '$1 microhenries');
  text = text.replace(/(\d+(?:\.\d+)?)\s*uH/g, '$1 microhenries');
  text = text.replace(/(\d+(?:\.\d+)?)\s*kHz/g, '$1 kilohertz');
  text = text.replace(/(\d+(?:\.\d+)?)\s*MHz/g, '$1 megahertz');
  text = text.replace(/(\d+(?:\.\d+)?)\s*GHz/g, '$1 gigahertz');
  text = text.replace(/(\d+(?:\.\d+)?)\s*Hz/g, '$1 hertz');
  text = text.replace(/(\d+(?:\.\d+)?)\s*mA/g, '$1 milliamps');
  text = text.replace(/(\d+(?:\.\d+)?)\s*mV/g, '$1 millivolts');
  text = text.replace(/(\d+(?:\.\d+)?)\s*V(?![a-zA-Z])/g, '$1 volts');
  text = text.replace(/(\d+(?:\.\d+)?)\s*W(?![a-zA-Z])/g, '$1 watts');

  text = text.replace(/[*_~`>]+/g, ' ');
  text = text.replace(/\[([^\]]+)\]\([^)]+\)/g, '$1');
  text = text.replace(/\s+/g, ' ').trim();

  if (text.length < 12) {
    if (titleHeading && titleHeading.length >= 3) {
      return `${titleHeading}. Specifications and calculations are displayed on screen.`;
    }
    return 'Specifications and calculations are displayed on screen.';
  }

  // Cap spoken response to key technical findings (~480 chars) at clean sentence boundary
  if (text.length > 480) {
    const cut = text.substring(0, 480);
    const lastPeriod = Math.max(cut.lastIndexOf('. '), cut.lastIndexOf('! '), cut.lastIndexOf('? '));
    if (lastPeriod > 220) {
      text = cut.substring(0, lastPeriod + 1);
    } else {
      text = cut.substring(0, cut.lastIndexOf(' ')).replace(/[,;:-]+$/, '') + '.';
    }
  }

  return text;
}

export function useJarvisVoice({ onTranscript, onFinalTranscript }: UseJarvisVoiceOptions = {}) {
  const [isVoiceEnabled, setIsVoiceEnabled] = useState(true);
  const [voiceState, setVoiceState] = useState<VoiceState>('idle');
  const [voiceSettings, setVoiceSettingsState] = useState<VoiceSettings>(loadVoiceSettings);
  const [liveTranscript, setLiveTranscript] = useState<string>('');
  const [voiceError, setVoiceError] = useState<string | null>(null);

  const [supported] = useState<boolean>(() => {
    if (typeof window === 'undefined' || typeof navigator === 'undefined') return false;
    return 'mediaDevices' in navigator && 'MediaRecorder' in window;
  });

  const streamRef = useRef<MediaStream | null>(null);
  const audioCtxRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const recognitionRef = useRef<any>(null);
  const latestLiveTranscriptRef = useRef<string>('');

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
  });

  const updateVoiceSettings = useCallback((partial: Partial<VoiceSettings>) => {
    setVoiceSettingsState((prev) => {
      const next = { ...prev, ...partial };
      saveVoiceSettings(next);
      return next;
    });
  }, []);

  // Pre-initialize single unlocked HTML5 Audio element
  useEffect(() => {
    if (typeof Audio !== 'undefined') {
      audioElRef.current = new Audio();
    }
    return () => {
      if (audioElRef.current) {
        audioElRef.current.pause();
        audioElRef.current.src = '';
      }
    };
  }, []);

  const clearVoiceError = useCallback(() => {
    setVoiceError(null);
  }, []);

  /**
   * Master bulletproof reset: aborts active MediaRecorder, drops mic tracks,
   * closes audioCtx, clears all timers, aborts fetches, and resets voiceState to idle.
   */
  const hardResetVoice = useCallback(() => {
    if (vadIntervalRef.current) {
      clearInterval(vadIntervalRef.current);
      vadIntervalRef.current = null;
    }
    if (recordingTimerRef.current) {
      clearTimeout(recordingTimerRef.current);
      recordingTimerRef.current = null;
    }
    if (rearmTimerRef.current) {
      clearTimeout(rearmTimerRef.current);
      rearmTimerRef.current = null;
    }

    if (recognitionRef.current) {
      try {
        recognitionRef.current.abort();
      } catch {
        // ignore
      }
      recognitionRef.current = null;
    }

    if (sttAbortControllerRef.current) {
      sttAbortControllerRef.current.abort();
      sttAbortControllerRef.current = null;
    }
    if (ttsAbortControllerRef.current) {
      ttsAbortControllerRef.current.abort();
      ttsAbortControllerRef.current = null;
    }

    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      try {
        mediaRecorderRef.current.onstop = null;
        mediaRecorderRef.current.stop();
      } catch {
        // ignore
      }
    }
    mediaRecorderRef.current = null;
    chunksRef.current = [];

    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }

    if (audioCtxRef.current && audioCtxRef.current.state !== 'closed') {
      try {
        void audioCtxRef.current.close();
      } catch {
        // ignore
      }
      audioCtxRef.current = null;
    }
    analyserRef.current = null;

    if (audioElRef.current) {
      audioElRef.current.pause();
      audioElRef.current.currentTime = 0;
      audioElRef.current.src = '';
    }
    if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
      window.speechSynthesis.cancel();
    }

    hasQualifiedSpeechRef.current = false;
    activeSpeechMsRef.current = 0;
    latestLiveTranscriptRef.current = '';
    setLiveTranscript('');
    setVoiceError(null);
    setVoiceState('idle');
  }, []);

  const cancelSpeech = useCallback(() => {
    if (audioElRef.current) {
      audioElRef.current.pause();
      audioElRef.current.currentTime = 0;
    }
    if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
      window.speechSynthesis.cancel();
    }
    if (voiceStateRef.current === 'speaking') {
      setVoiceState('idle');
    }
  }, []);

  // Internal helper to stop VAD recording tracks and analysis loop
  const stopListeningInternal = useCallback((allowProcessing: boolean) => {
    if (vadIntervalRef.current) {
      clearInterval(vadIntervalRef.current);
      vadIntervalRef.current = null;
    }
    if (recordingTimerRef.current) {
      clearTimeout(recordingTimerRef.current);
      recordingTimerRef.current = null;
    }
    if (recognitionRef.current) {
      try {
        recognitionRef.current.stop();
      } catch {
        // ignore
      }
      recognitionRef.current = null;
    }
    if (!allowProcessing) {
      hasQualifiedSpeechRef.current = false;
      activeSpeechMsRef.current = 0;
    }
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      try {
        mediaRecorderRef.current.stop();
      } catch {
        // ignore
      }
    }
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }
    if (audioCtxRef.current && audioCtxRef.current.state !== 'closed') {
      try {
        void audioCtxRef.current.close();
      } catch {
        // ignore
      }
      audioCtxRef.current = null;
    }

    if (voiceStateRef.current === 'listening') {
      setVoiceState(allowProcessing && hasQualifiedSpeechRef.current ? 'transcribing' : 'idle');
    }
  }, []);

  // Browser SpeechSynthesis fallback
  const fallbackBrowserSpeak = useCallback(
    (rawText: string, onEnd?: () => void, targetVoiceId?: VoiceSettings['voiceId']) => {
      if (typeof window === 'undefined' || !('speechSynthesis' in window)) {
        setVoiceState('idle');
        onEnd?.();
        return;
      }
      window.speechSynthesis.cancel();
      const cleaned = cleanTextForSpeech(rawText);
      const utterance = new SpeechSynthesisUtterance(cleaned);
      utterance.pitch = 1.0;
      utterance.rate = voiceSettingsRef.current.speechRate;

      const voices = window.speechSynthesis.getVoices();
      const voiceToUse = targetVoiceId || voiceSettingsRef.current.voiceId;
      const targetLang = voiceToUse.startsWith('en-GB') ? 'en-GB' : 'en-US';
      const chosenVoice = voices.find((v) => v.lang.startsWith(targetLang));
      if (chosenVoice) utterance.voice = chosenVoice;

      utterance.onend = () => {
        setVoiceState('idle');
        onEnd?.();
        if (isVoiceEnabledRef.current && voiceSettingsRef.current.interactionMode === 'live') {
          rearmTimerRef.current = window.setTimeout(() => {
            void startListeningRef.current();
          }, 800);
        }
      };
      utterance.onerror = () => {
        setVoiceState('idle');
        onEnd?.();
      };

      setVoiceState('speaking');
      window.speechSynthesis.speak(utterance);
      // eslint-disable-next-line react-hooks/exhaustive-deps
    },
    []
  );

  // Neural TTS (`POST /api/tts` with 8.0s timeout and selectable persona)
  const speak = useCallback(
    async (
      rawText: string,
      onEndCallback?: () => void,
      force = false,
      overrideVoiceId?: VoiceSettings['voiceId']
    ) => {
      if (!isVoiceEnabledRef.current && !force) {
        return;
      }
      if (!voiceSettingsRef.current.autoSpeak && !force) {
        return;
      }

      stopListeningInternal(false);
      cancelSpeech();

      const cleaned = cleanTextForSpeech(rawText);
      if (!cleaned) {
        setVoiceState('idle');
        return;
      }

      setVoiceState('speaking');

      const ratePercent = Math.round((voiceSettingsRef.current.speechRate - 1) * 100);
      const rateStr = `${ratePercent >= 0 ? '+' : ''}${ratePercent}%`;
      const activeVoice = overrideVoiceId || voiceSettingsRef.current.voiceId;

      const controller = new AbortController();
      ttsAbortControllerRef.current = controller;
      const timeoutId = setTimeout(() => controller.abort(), 8000);

      try {
        const response = await fetch('/api/tts', {
          method: 'POST',
          signal: controller.signal,
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            text: cleaned,
            voice: activeVoice,
            rate: rateStr,
          }),
        });

        clearTimeout(timeoutId);
        ttsAbortControllerRef.current = null;

        if (!response.ok) {
          throw new Error(`TTS server error: ${response.status}`);
        }

        const blob = await response.blob();
        const audioUrl = URL.createObjectURL(blob);
        const audio = audioElRef.current || new Audio();
        audioElRef.current = audio;

        const handleEnded = () => {
          URL.revokeObjectURL(audioUrl);
          audio.removeEventListener('ended', handleEnded);
          audio.removeEventListener('error', handleError);
          setVoiceState('idle');
          onEndCallback?.();

          // Continuous Conversation Loop (Live Mode)
          if (isVoiceEnabledRef.current && voiceSettingsRef.current.interactionMode === 'live') {
            rearmTimerRef.current = window.setTimeout(() => {
              void startListeningRef.current();
            }, 800);
          }
        };

        const handleError = () => {
          URL.revokeObjectURL(audioUrl);
          audio.removeEventListener('ended', handleEnded);
          audio.removeEventListener('error', handleError);
          fallbackBrowserSpeak(rawText, onEndCallback, activeVoice);
        };

        audio.addEventListener('ended', handleEnded);
        audio.addEventListener('error', handleError);
        audio.src = audioUrl;
        await audio.play();
      } catch (err) {
        clearTimeout(timeoutId);
        ttsAbortControllerRef.current = null;
        if ((err as Error)?.name !== 'AbortError') {
          fallbackBrowserSpeak(rawText, onEndCallback, activeVoice);
        } else {
          setVoiceState('idle');
        }
      }
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [cancelSpeech, fallbackBrowserSpeak, stopListeningInternal]
  );

  // VAD Audio Recording + Whisper STT with 15s max timer and 8s fetch timeout
  const startListening = useCallback(async () => {
    if (typeof navigator === 'undefined' || !navigator.mediaDevices?.getUserMedia) return;
    if (voiceStateRef.current === 'listening' || voiceStateRef.current === 'transcribing') return;

    cancelSpeech();
    setVoiceError(null);
    setLiveTranscript('');
    latestLiveTranscriptRef.current = '';

    try {
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((track) => track.stop());
      }

      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        },
      });
      streamRef.current = stream;

      const AudioCtxClass = window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext;
      const audioCtx = new AudioCtxClass();
      audioCtxRef.current = audioCtx;

      // Ensure AudioContext is active
      if (audioCtx.state === 'suspended') {
        await audioCtx.resume();
      }

      const source = audioCtx.createMediaStreamSource(stream);
      const analyser = audioCtx.createAnalyser();
      analyser.fftSize = 512;
      source.connect(analyser);
      analyserRef.current = analyser;

      let mimeType: string | undefined;
      if (MediaRecorder.isTypeSupported('audio/webm;codecs=opus')) {
        mimeType = 'audio/webm;codecs=opus';
      } else if (MediaRecorder.isTypeSupported('audio/webm')) {
        mimeType = 'audio/webm';
      } else if (MediaRecorder.isTypeSupported('audio/ogg;codecs=opus')) {
        mimeType = 'audio/ogg;codecs=opus';
      } else if (MediaRecorder.isTypeSupported('audio/mp4')) {
        mimeType = 'audio/mp4';
      }

      const mediaRecorder = mimeType
        ? new MediaRecorder(stream, { mimeType })
        : new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      chunksRef.current = [];

      mediaRecorder.ondataavailable = (e) => {
        if (e.data && e.data.size > 0) {
          chunksRef.current.push(e.data);
        }
      };

      mediaRecorder.onstop = async () => {
        if (recognitionRef.current) {
          try {
            recognitionRef.current.abort();
          } catch {
            // ignore
          }
          recognitionRef.current = null;
        }

        const chunks = chunksRef.current;
        const liveFallbackText = latestLiveTranscriptRef.current.trim();
        if (liveFallbackText) {
          hasQualifiedSpeechRef.current = true;
        }
        const qualified = hasQualifiedSpeechRef.current || chunks.length > 0;
        let sttDispatched = false;

        if (chunks.length > 0 && qualified && voiceStateRef.current !== 'speaking') {
          setVoiceState('transcribing');
          const audioBlob = new Blob(chunks, mimeType ? { type: mimeType } : undefined);

          const controller = new AbortController();
          sttAbortControllerRef.current = controller;
          const timeoutId = setTimeout(() => controller.abort(), 8000);

          try {
            const formData = new FormData();
            const extension = mimeType?.includes('ogg') ? 'ogg' : mimeType?.includes('mp4') ? 'mp4' : 'webm';
            formData.append('file', audioBlob, `speech.${extension}`);
            const res = await fetch('/api/stt', {
              method: 'POST',
              body: formData,
              signal: controller.signal,
            });

            clearTimeout(timeoutId);
            sttAbortControllerRef.current = null;

            if (res.ok) {
              const data = await res.json();
              const rawText = data.text || '';
              const clean = stripWakeWord(rawText);
              if (clean.trim()) {
                sttDispatched = true;
                setVoiceError(null);
                setLiveTranscript(clean.trim());
                onTranscriptRef.current?.(clean.trim());
                onFinalTranscriptRef.current?.(clean.trim());
                setTimeout(() => setLiveTranscript(''), 1000);
              }
            }
          } catch (err) {
            clearTimeout(timeoutId);
            sttAbortControllerRef.current = null;
            if ((err as Error)?.name !== 'AbortError') {
              console.warn('STT upload error:', err);
            }
          }
        }

        // If Whisper /api/stt didn't dispatch, fallback to real-time recognized interim transcript
        if (!sttDispatched) {
          const fallbackText = stripWakeWord(latestLiveTranscriptRef.current);
          if (fallbackText.trim() && voiceStateRef.current !== 'speaking') {
            setVoiceError(null);
            setLiveTranscript(fallbackText.trim());
            onTranscriptRef.current?.(fallbackText.trim());
            onFinalTranscriptRef.current?.(fallbackText.trim());
            setTimeout(() => setLiveTranscript(''), 1000);
          } else {
            setVoiceError('No speech detected — check mic input or speak closer');
            setTimeout(() => setLiveTranscript(''), 600);
          }
        }

        hasQualifiedSpeechRef.current = false;
        activeSpeechMsRef.current = 0;
        latestLiveTranscriptRef.current = '';
        if (voiceStateRef.current === 'transcribing') {
          setVoiceState('idle');
        }
      };

      // Parallel browser SpeechRecognition for immediate real-time interim preview
      if (typeof window !== 'undefined') {
        const SpeechRec =
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          (window as unknown as { SpeechRecognition?: any }).SpeechRecognition ||
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          (window as unknown as { webkitSpeechRecognition?: any }).webkitSpeechRecognition;
        if (SpeechRec) {
          try {
            const rec = new SpeechRec();
            rec.continuous = true;
            rec.interimResults = true;
            rec.lang = 'en-US';
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            rec.onresult = (event: any) => {
              let interim = '';
              for (let i = 0; i < event.results.length; i++) {
                interim += event.results[i][0].transcript;
              }
              const trimmed = interim.trim();
              if (trimmed) {
                latestLiveTranscriptRef.current = trimmed;
                setLiveTranscript(trimmed);
                onTranscriptRef.current?.(trimmed);
              }
            };
            rec.onerror = () => {
              // Non-fatal interim preview error
            };
            rec.start();
            recognitionRef.current = rec;
          } catch {
            // SpeechRecognition might fail if exclusive
          }
        }
      }

      mediaRecorder.start(250);
      setVoiceState('listening');

      hasQualifiedSpeechRef.current = false;
      activeSpeechMsRef.current = 0;
      let silenceStart: number | null = null;
      const startTime = Date.now();
      const timeDomainData = new Uint8Array(analyser.fftSize);

      // Hard max 15-second recording safety timer
      if (recordingTimerRef.current) clearTimeout(recordingTimerRef.current);
      recordingTimerRef.current = window.setTimeout(() => {
        stopListeningInternal(true);
      }, 15000);

      if (vadIntervalRef.current) clearInterval(vadIntervalRef.current);
      vadIntervalRef.current = window.setInterval(() => {
        if (voiceStateRef.current === 'speaking') {
          stopListeningInternal(false);
          return;
        }

        analyser.getByteTimeDomainData(timeDomainData);
        let sumSquares = 0;
        for (let i = 0; i < timeDomainData.length; i++) {
          const normalized = (timeDomainData[i] - 128) / 128;
          sumSquares += normalized * normalized;
        }
        const rms = Math.sqrt(sumSquares / timeDomainData.length);

        const hasLiveWords = latestLiveTranscriptRef.current.trim().length > 0;
        if (hasLiveWords) {
          hasQualifiedSpeechRef.current = true;
        }

        if (rms > 0.012 || hasLiveWords) {
          activeSpeechMsRef.current += 50;
          if (activeSpeechMsRef.current >= 150 || hasLiveWords) {
            hasQualifiedSpeechRef.current = true;
            silenceStart = null;
          }
        } else if (hasQualifiedSpeechRef.current) {
          if (silenceStart === null) {
            silenceStart = Date.now();
          } else if (Date.now() - silenceStart > 1200) {
            stopListeningInternal(true);
          }
        } else if (Date.now() - startTime > 7000) {
          stopListeningInternal(false);
        }
      }, 50);
    } catch (err) {
      console.warn('Microphone initialization failed:', err);
      setVoiceState('idle');
    }
  }, [cancelSpeech, stopListeningInternal]);
  startListeningRef.current = startListening;

  const stopListening = useCallback(() => {
    hasQualifiedSpeechRef.current = true;
    stopListeningInternal(true);
  }, [stopListeningInternal]);

  const testVoicePersona = useCallback(
    async (voiceId?: string) => {
      const targetVoice = (voiceId as VoiceSettings['voiceId']) || voiceSettingsRef.current.voiceId;
      const personaSample = targetVoice.includes('Sonia')
        ? 'Jarvis online. Sonia British neural persona active and verified.'
        : targetVoice.includes('Aria')
        ? 'Aria studio persona initialized. Clear, expressive audio ready.'
        : targetVoice.includes('Jenny')
        ? 'Jenny educational tutor persona online. Ready for engineering concepts.'
        : 'Ryan classic British gentleman persona active. Standing by.';
      await speak(personaSample, undefined, true, targetVoice);
    },
    [speak]
  );

  useEffect(() => {
    return () => {
      hardResetVoice();
    };
  }, [hardResetVoice]);

  const toggleVoiceMode = useCallback(() => {
    setIsVoiceEnabled((prev) => {
      const next = !prev;
      isVoiceEnabledRef.current = next;
      if (next) {
        void speak(
          'Jarvis voice systems online.',
          () => {
            void startListeningRef.current();
          },
          true
        );
      } else {
        hardResetVoice();
      }
      return next;
    });
  }, [hardResetVoice, speak]);

  return {
    isVoiceEnabled,
    voiceState,
    isListening: voiceState === 'listening',
    isSpeaking: voiceState === 'speaking',
    isTranscribing: voiceState === 'transcribing',
    supported,
    voiceSettings,
    liveTranscript,
    voiceError,
    clearVoiceError,
    updateVoiceSettings,
    toggleVoiceMode,
    startListening,
    stopListening,
    speak,
    cancelSpeech,
    stopSpeaking: cancelSpeech,
    hardResetVoice,
    testVoicePersona,
  };
}
