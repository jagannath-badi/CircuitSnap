import { useState, useEffect, useRef, useCallback } from 'react';

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

  // Pre-extract potential clean title heading before stripping
  let titleHeading = '';
  const headingMatch = raw.match(/(?:^|\n)\s*#{1,6}\s*(?:\[\s*(?:CONFIRMED|LIKELY|CANNOT CONFIRM)\s*\])?\s*([^\n#|]+)/i);
  if (headingMatch && headingMatch[1]) {
    titleHeading = headingMatch[1].replace(/[*_`]/g, '').trim();
    titleHeading = titleHeading.replace(/J\.A\.R\.V\.I\.S\.?/gi, 'Jarvis').replace(/\bJARVIS\b/g, 'Jarvis');
  }

  let text = raw;

  // Pronounce "Jarvis" as a single cohesive word instead of spelling J-A-R-V-I-S
  text = text.replace(/J\.A\.R\.V\.I\.S\.?/gi, 'Jarvis');
  text = text.replace(/\bJARVIS\b/g, 'Jarvis');

  // Strip code blocks completely
  text = text.replace(/```[\s\S]*?```/g, ' ');
  text = text.replace(/`([^`]+)`/g, '$1');

  // Strip Markdown tables completely (| ... |) so pipes and table cells are never read aloud
  text = text.replace(/^\s*\|.*\|\s*$/gm, ' ');
  text = text.replace(/\|[^\n]+\|/g, ' ');

  // Strip Markdown header tags (###, ##, #)
  text = text.replace(/(?:^|\n)\s*#{1,6}\s*/g, ' ');

  // Strip confidence badges entirely (CONFIRMED, LIKELY, CANNOT CONFIRM)
  text = text.replace(/\[\s*(?:CONFIRMED|LIKELY|CANNOT CONFIRM)\s*\]\s*[:\-\u2013\u2014]?/gi, '');
  text = text.replace(/\b(?:CONFIRMED|CANNOT CONFIRM)\b\s*[:\-\u2013\u2014]?/gi, '');

  // Replace common LaTeX formulas with natural spoken equivalents
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

  // Spoken electrical units
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

  // Strip residual Markdown formatting
  text = text.replace(/[*_~`>]+/g, ' ');
  text = text.replace(/\[([^\]]+)\]\([^)]+\)/g, '$1');
  text = text.replace(/\s+/g, ' ').trim();

  // Fallback summary if table-stripping or formatting leaves shorter than 12 characters
  if (text.length < 12) {
    if (titleHeading && titleHeading.length >= 3) {
      return `${titleHeading}. Specifications and calculations are displayed on screen.`;
    }
    return 'Specifications and calculations are displayed on screen.';
  }

  // Keep spoken response to key technical findings (concise summary ~320 chars)
  if (text.length > 320) {
    const periodIdx = text.indexOf('.', 200);
    if (periodIdx !== -1 && periodIdx < 420) {
      text = text.substring(0, periodIdx + 1);
    }
  }

  return text;
}

export function useJarvisVoice({ onTranscript, onFinalTranscript }: UseJarvisVoiceOptions = {}) {
  const [isVoiceEnabled, setIsVoiceEnabled] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [supported] = useState<boolean>(() => {
    if (typeof window === 'undefined' || typeof navigator === 'undefined') return false;
    return 'mediaDevices' in navigator && 'MediaRecorder' in window;
  });

  const streamRef = useRef<MediaStream | null>(null);
  const audioCtxRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const vadIntervalRef = useRef<number | null>(null);
  const hasSpokenRef = useRef(false);

  const audioElRef = useRef<HTMLAudioElement | null>(null);
  const onTranscriptRef = useRef(onTranscript);
  const onFinalTranscriptRef = useRef(onFinalTranscript);
  const isVoiceEnabledRef = useRef(isVoiceEnabled);
  const isSpeakingRef = useRef(isSpeaking);
  const wasStartedByMicRef = useRef(false);
  const rearmTimerRef = useRef<number | null>(null);

  // Synchronize latest functions and state across all renders to eliminate stale closures
  useEffect(() => {
    onTranscriptRef.current = onTranscript;
    onFinalTranscriptRef.current = onFinalTranscript;
    isVoiceEnabledRef.current = isVoiceEnabled;
    isSpeakingRef.current = isSpeaking;
  });

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

  const cancelSpeech = useCallback(() => {
    if (rearmTimerRef.current) {
      clearTimeout(rearmTimerRef.current);
      rearmTimerRef.current = null;
    }
    if (audioElRef.current) {
      audioElRef.current.pause();
      audioElRef.current.currentTime = 0;
    }
    if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
      window.speechSynthesis.cancel();
    }
    setIsSpeaking(false);
    isSpeakingRef.current = false;
  }, []);

  // Internal helper to stop VAD recording tracks and analysis loop
  const stopListeningInternal = useCallback((allowProcessing: boolean) => {
    if (vadIntervalRef.current) {
      clearInterval(vadIntervalRef.current);
      vadIntervalRef.current = null;
    }
    if (!allowProcessing) {
      hasSpokenRef.current = false;
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
    setIsListening(false);
  }, []);

  // Fallback to browser Web SpeechSynthesis if neural TTS is unreachable
  const fallbackBrowserSpeak = useCallback((rawText: string, onEnd?: () => void) => {
    if (typeof window === 'undefined' || !('speechSynthesis' in window)) {
      setIsSpeaking(false);
      isSpeakingRef.current = false;
      onEnd?.();
      return;
    }
    window.speechSynthesis.cancel();
    const cleaned = cleanTextForSpeech(rawText);
    const utterance = new SpeechSynthesisUtterance(cleaned);
    utterance.pitch = 0.88;
    utterance.rate = 1.04;

    const voices = window.speechSynthesis.getVoices();
    const ukVoice = voices.find(
      (v) => (v.lang === 'en-GB' || v.lang.startsWith('en-GB')) && !/female/i.test(v.name)
    );
    if (ukVoice) utterance.voice = ukVoice;

    utterance.onend = () => {
      setIsSpeaking(false);
      isSpeakingRef.current = false;
      onEnd?.();
    };
    utterance.onerror = () => {
      setIsSpeaking(false);
      isSpeakingRef.current = false;
      onEnd?.();
    };

    window.speechSynthesis.speak(utterance);
  }, []);

  // Neural British TTS (`POST /api/tts` with fallback)
  const speak = useCallback(
    async (rawText: string, onEndCallback?: () => void, force = false) => {
      if (!isVoiceEnabledRef.current && !force) {
        return;
      }

      // 1. Immediately abort active VAD mic listening before audio plays
      stopListeningInternal(false);
      cancelSpeech();

      // 2. Clear any pending re-arm timer so mic cannot wake while speaking
      if (rearmTimerRef.current) {
        clearTimeout(rearmTimerRef.current);
        rearmTimerRef.current = null;
      }

      setIsSpeaking(true);
      isSpeakingRef.current = true;

      const cleaned = cleanTextForSpeech(rawText);
      if (!cleaned) {
        setIsSpeaking(false);
        isSpeakingRef.current = false;
        return;
      }

      try {
        const response = await fetch('/api/tts', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ text: cleaned }),
        });

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
          setIsSpeaking(false);
          isSpeakingRef.current = false;
          onEndCallback?.();

          // Strict acoustic lock: only re-arm if user started mic, waiting 850ms
          if (wasStartedByMicRef.current && isVoiceEnabledRef.current) {
            if (rearmTimerRef.current) clearTimeout(rearmTimerRef.current);
            rearmTimerRef.current = window.setTimeout(() => {
              if (wasStartedByMicRef.current && isVoiceEnabledRef.current && !isSpeakingRef.current) {
                void startListening();
              }
            }, 850);
          }
        };

        const handleError = () => {
          URL.revokeObjectURL(audioUrl);
          audio.removeEventListener('ended', handleEnded);
          audio.removeEventListener('error', handleError);
          fallbackBrowserSpeak(rawText, onEndCallback);
        };

        audio.addEventListener('ended', handleEnded);
        audio.addEventListener('error', handleError);
        audio.src = audioUrl;
        await audio.play();
      } catch {
        fallbackBrowserSpeak(rawText, onEndCallback);
      }
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [cancelSpeech, fallbackBrowserSpeak, stopListeningInternal]
  );

  // Hands-Free VAD Audio Recording + Local Whisper STT (`POST /api/stt`)
  const startListening = useCallback(async () => {
    if (typeof navigator === 'undefined' || !navigator.mediaDevices?.getUserMedia) return;
    cancelSpeech();
    wasStartedByMicRef.current = true;

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

      const source = audioCtx.createMediaStreamSource(stream);
      const analyser = audioCtx.createAnalyser();
      analyser.fftSize = 512;
      source.connect(analyser);
      analyserRef.current = analyser;

      const mimeType = MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
        ? 'audio/webm;codecs=opus'
        : MediaRecorder.isTypeSupported('audio/webm')
        ? 'audio/webm'
        : 'audio/mp4';

      const mediaRecorder = new MediaRecorder(stream, { mimeType });
      mediaRecorderRef.current = mediaRecorder;
      chunksRef.current = [];

      mediaRecorder.ondataavailable = (e) => {
        if (e.data && e.data.size > 0) {
          chunksRef.current.push(e.data);
        }
      };

      mediaRecorder.onstop = async () => {
        const chunks = chunksRef.current;
        if (chunks.length > 0 && hasSpokenRef.current && !isSpeakingRef.current) {
          const audioBlob = new Blob(chunks, { type: mimeType });
          try {
            const formData = new FormData();
            formData.append('file', audioBlob, 'speech.webm');
            const res = await fetch('/api/stt', { method: 'POST', body: formData });
            if (res.ok) {
              const data = await res.json();
              const rawText = data.text || '';
              const clean = stripWakeWord(rawText);
              if (clean.trim()) {
                // Auto-submit immediately to chat!
                onFinalTranscriptRef.current?.(clean.trim());
              }
            }
          } catch (err) {
            console.warn('STT upload error:', err);
          }
        }
      };

      mediaRecorder.start(250);
      setIsListening(true);

      hasSpokenRef.current = false;
      let silenceStart: number | null = null;
      const dataArray = new Uint8Array(analyser.frequencyBinCount);

      if (vadIntervalRef.current) clearInterval(vadIntervalRef.current);
      vadIntervalRef.current = window.setInterval(() => {
        if (isSpeakingRef.current) {
          stopListeningInternal(false);
          return;
        }

        analyser.getByteFrequencyData(dataArray);
        let sum = 0;
        for (let i = 0; i < dataArray.length; i++) {
          sum += dataArray[i];
        }
        const avg = sum / dataArray.length;

        // VAD threshold for voice activity
        if (avg > 12) {
          hasSpokenRef.current = true;
          silenceStart = null;
        } else if (hasSpokenRef.current) {
          if (silenceStart === null) {
            silenceStart = Date.now();
          } else if (Date.now() - silenceStart > 1200) {
            // 1.2s silence detected after user spoke - auto-stop & transcribe
            stopListeningInternal(true);
          }
        }
      }, 50);
    } catch (err) {
      console.warn('Microphone initialization failed:', err);
      setIsListening(false);
      wasStartedByMicRef.current = false;
    }
  }, [cancelSpeech, stopListeningInternal]);

  const stopListening = useCallback(() => {
    wasStartedByMicRef.current = false;
    if (rearmTimerRef.current) {
      clearTimeout(rearmTimerRef.current);
      rearmTimerRef.current = null;
    }
    stopListeningInternal(false);
  }, [stopListeningInternal]);

  // Clean unmount
  useEffect(() => {
    return () => {
      if (rearmTimerRef.current) {
        clearTimeout(rearmTimerRef.current);
        rearmTimerRef.current = null;
      }
      stopListeningInternal(false);
      cancelSpeech();
    };
  }, [cancelSpeech, stopListeningInternal]);

  const toggleVoiceMode = useCallback(() => {
    setIsVoiceEnabled((prev) => {
      const next = !prev;
      isVoiceEnabledRef.current = next;
      if (next) {
        // Announce readiness via neural voice without auto-starting the mic
        void speak('Jarvis voice systems online.', undefined, true);
      } else {
        wasStartedByMicRef.current = false;
        if (rearmTimerRef.current) {
          clearTimeout(rearmTimerRef.current);
          rearmTimerRef.current = null;
        }
        cancelSpeech();
        stopListening();
      }
      return next;
    });
  }, [cancelSpeech, stopListening, speak]);

  return {
    isVoiceEnabled,
    isListening,
    isSpeaking,
    supported,
    toggleVoiceMode,
    startListening,
    stopListening,
    speak,
    cancelSpeech,
    stopSpeaking: cancelSpeech,
  };
}
