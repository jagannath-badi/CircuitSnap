import { useState, useEffect, useRef, useCallback } from 'react';

// Browser Web Speech API type declarations
interface IWindowSpeechRecognition extends EventTarget {
  continuous: boolean;
  interimResults: boolean;
  lang: string;
  start: () => void;
  stop: () => void;
  abort: () => void;
  onstart: (() => void) | null;
  onend: (() => void) | null;
  onerror: ((event: { error: string }) => void) | null;
  onresult: ((event: {
    resultIndex: number;
    results: {
      length: number;
      item: (index: number) => {
        isFinal: boolean;
        item: (idx: number) => { transcript: string };
      };
      [index: number]: {
        isFinal: boolean;
        [index: number]: { transcript: string };
      };
    };
  }) => void) | null;
}

interface WindowWithSpeech extends Window {
  SpeechRecognition?: { new (): IWindowSpeechRecognition };
  webkitSpeechRecognition?: { new (): IWindowSpeechRecognition };
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
  text = text.replace(/\[\s*(?:CONFIRMED|LIKELY|CANNOT CONFIRM)\s*\]\s*[:-–—]?/gi, '');
  text = text.replace(/\b(?:CONFIRMED|CANNOT CONFIRM)\b\s*[:-–—]?/gi, '');

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

/**
 * Finds the best crisp British English male voice available on the host machine.
 */
function selectBritishJarvisVoice(voices: SpeechSynthesisVoice[]): SpeechSynthesisVoice | null {
  if (!voices || voices.length === 0) return null;

  const ukVoices = voices.filter(
    (v) => v.lang === 'en-GB' || v.lang === 'en_GB' || v.lang.startsWith('en-GB')
  );

  // 1. Prioritize natural UK voices (Ryan Online, George, Oliver, Arthur, Google UK English Male)
  const prioritized = ukVoices.find((v) =>
    /Ryan|George|Oliver|Arthur|Google UK English Male/i.test(v.name)
  );
  if (prioritized) return prioritized;

  // 2. Male UK voice
  const maleUk = ukVoices.find((v) => !/female|zira|hazel|susan|catherine/i.test(v.name));
  if (maleUk) return maleUk;

  if (ukVoices.length > 0) return ukVoices[0];

  // 3. Fallback to any natural English male voice
  const enVoices = voices.filter((v) => v.lang.startsWith('en'));
  const maleEn = enVoices.find((v) => /natural|guy|david|male/i.test(v.name));
  return maleEn || enVoices[0] || voices[0];
}

export function useJarvisVoice({ onTranscript, onFinalTranscript }: UseJarvisVoiceOptions = {}) {
  const [isVoiceEnabled, setIsVoiceEnabled] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [supported] = useState<boolean>(() => {
    if (typeof window === 'undefined') return false;
    const win = window as WindowWithSpeech;
    const SpeechRecognition = win.SpeechRecognition || win.webkitSpeechRecognition;
    const hasSynthesis = 'speechSynthesis' in window;
    return !!(SpeechRecognition && hasSynthesis);
  });

  const recognitionRef = useRef<IWindowSpeechRecognition | null>(null);
  const onTranscriptRef = useRef(onTranscript);
  const onFinalTranscriptRef = useRef(onFinalTranscript);
  const isVoiceEnabledRef = useRef(isVoiceEnabled);
  const isSpeakingRef = useRef(isSpeaking);
  const wasStartedByMicRef = useRef(false);
  const rearmTimerRef = useRef<number | null>(null);
  const keepAliveIntervalRef = useRef<number | null>(null);
  const voicesRef = useRef<SpeechSynthesisVoice[]>([]);

  useEffect(() => {
    onTranscriptRef.current = onTranscript;
    onFinalTranscriptRef.current = onFinalTranscript;
    isVoiceEnabledRef.current = isVoiceEnabled;
    isSpeakingRef.current = isSpeaking;
  });

  // Preload voices
  useEffect(() => {
    if (typeof window === 'undefined' || !('speechSynthesis' in window)) return;
    const updateVoices = () => {
      voicesRef.current = window.speechSynthesis.getVoices();
    };
    updateVoices();
    window.speechSynthesis.onvoiceschanged = updateVoices;
    return () => {
      window.speechSynthesis.onvoiceschanged = null;
    };
  }, []);

  const clearKeepAlive = () => {
    if (keepAliveIntervalRef.current) {
      clearInterval(keepAliveIntervalRef.current);
      keepAliveIntervalRef.current = null;
    }
  };

  const cancelSpeech = useCallback(() => {
    clearKeepAlive();
    if (rearmTimerRef.current) {
      clearTimeout(rearmTimerRef.current);
      rearmTimerRef.current = null;
    }
    if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
      window.speechSynthesis.cancel();
      setIsSpeaking(false);
      isSpeakingRef.current = false;
    }
  }, []);

  const startListening = useCallback(() => {
    if (!recognitionRef.current) return;
    cancelSpeech();
    wasStartedByMicRef.current = true;
    try {
      recognitionRef.current.start();
    } catch {
      // recognition already active
    }
  }, [cancelSpeech]);

  const stopListening = useCallback(() => {
    wasStartedByMicRef.current = false;
    if (rearmTimerRef.current) {
      clearTimeout(rearmTimerRef.current);
      rearmTimerRef.current = null;
    }
    if (!recognitionRef.current) return;
    try {
      recognitionRef.current.stop();
    } catch {
      // ignore
    }
  }, []);

  // Voice speech synthesis with strict acoustic echo protection
  const speak = useCallback(
    (rawText: string, onEndCallback?: () => void, force = false) => {
      if ((!isVoiceEnabledRef.current && !force) || typeof window === 'undefined' || !('speechSynthesis' in window)) {
        return;
      }

      // 1. Immediately abort active speech recognition and mark listening false
      if (recognitionRef.current) {
        try {
          recognitionRef.current.abort();
        } catch {
          // ignore
        }
      }
      setIsListening(false);

      // 2. Clear any pending re-arm timer so mic cannot start while speaking
      if (rearmTimerRef.current) {
        clearTimeout(rearmTimerRef.current);
        rearmTimerRef.current = null;
      }

      // 3. Set speaking flags BEFORE invoking speechSynthesis
      setIsSpeaking(true);
      isSpeakingRef.current = true;

      window.speechSynthesis.cancel();
      window.speechSynthesis.resume();

      const cleaned = cleanTextForSpeech(rawText);
      if (!cleaned) {
        setIsSpeaking(false);
        isSpeakingRef.current = false;
        return;
      }

      const utterance = new SpeechSynthesisUtterance(cleaned);
      utterance.pitch = 0.88;
      utterance.rate = 1.04;

      const voices = voicesRef.current.length > 0 ? voicesRef.current : window.speechSynthesis.getVoices();
      const britishVoice = selectBritishJarvisVoice(voices);
      if (britishVoice) {
        utterance.voice = britishVoice;
      }

      utterance.onstart = () => {
        setIsSpeaking(true);
        isSpeakingRef.current = true;
        clearKeepAlive();
        // Chrome keep-alive
        keepAliveIntervalRef.current = window.setInterval(() => {
          if (typeof window !== 'undefined' && 'speechSynthesis' in window && window.speechSynthesis.speaking) {
            window.speechSynthesis.pause();
            window.speechSynthesis.resume();
          } else {
            clearKeepAlive();
          }
        }, 10000);
      };

      const handleSpeechComplete = () => {
        clearKeepAlive();
        setIsSpeaking(false);
        isSpeakingRef.current = false;
        onEndCallback?.();

        // ONLY re-arm startListening() if wasStartedByMicRef.current is true AND wait at least 850ms
        if (wasStartedByMicRef.current && isVoiceEnabledRef.current) {
          if (rearmTimerRef.current) clearTimeout(rearmTimerRef.current);
          rearmTimerRef.current = window.setTimeout(() => {
            if (wasStartedByMicRef.current && isVoiceEnabledRef.current && !isSpeakingRef.current) {
              try {
                recognitionRef.current?.start();
              } catch {
                // ignore
              }
            }
          }, 850);
        }
      };

      utterance.onend = handleSpeechComplete;
      utterance.onerror = handleSpeechComplete;

      window.speechSynthesis.speak(utterance);
    },
    []
  );

  // Initialize Speech Recognition
  useEffect(() => {
    if (!supported) return;

    const win = window as WindowWithSpeech;
    const SpeechRecognition = win.SpeechRecognition || win.webkitSpeechRecognition;

    if (SpeechRecognition) {
      try {
        const recognition = new SpeechRecognition();
        recognition.continuous = false;
        recognition.interimResults = true;
        recognition.lang = 'en-US';

        recognition.onstart = () => {
          setIsListening(true);
        };

        recognition.onend = () => {
          setIsListening(false);
          // Only re-arm if started by mic, voice mode is active, and J.A.R.V.I.S. is not speaking
          if (wasStartedByMicRef.current && isVoiceEnabledRef.current && !isSpeakingRef.current) {
            if (rearmTimerRef.current) clearTimeout(rearmTimerRef.current);
            rearmTimerRef.current = window.setTimeout(() => {
              if (wasStartedByMicRef.current && isVoiceEnabledRef.current && !isSpeakingRef.current) {
                try {
                  recognition.start();
                } catch {
                  // ignore
                }
              }
            }, 850);
          }
        };

        recognition.onerror = () => {
          setIsListening(false);
        };

        recognition.onresult = (event) => {
          // Immediately return and ignore any transcript if J.A.R.V.I.S. is speaking or synthesis is active
          if (isSpeakingRef.current || (typeof window !== 'undefined' && window.speechSynthesis?.speaking)) {
            return;
          }

          let interimText = '';
          for (let i = event.resultIndex; i < event.results.length; ++i) {
            const resultItem = event.results[i];
            const transcript = resultItem[0].transcript;
            if (resultItem.isFinal) {
              const cleaned = stripWakeWord(transcript);
              if (cleaned && onFinalTranscriptRef.current) {
                onFinalTranscriptRef.current(cleaned);
              }
            } else {
              interimText += transcript;
            }
          }
          if (interimText && onTranscriptRef.current) {
            onTranscriptRef.current(stripWakeWord(interimText));
          }
        };

        recognitionRef.current = recognition;
      } catch {
        // Ignore initialization error
      }
    }

    return () => {
      if (rearmTimerRef.current) {
        clearTimeout(rearmTimerRef.current);
        rearmTimerRef.current = null;
      }
      clearKeepAlive();
      if (recognitionRef.current) {
        try {
          recognitionRef.current.abort();
        } catch {
          // ignore cleanup abort
        }
      }
      if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
        window.speechSynthesis.cancel();
      }
    };
  }, [supported]);

  const toggleVoiceMode = useCallback(() => {
    setIsVoiceEnabled((prev) => {
      const next = !prev;
      isVoiceEnabledRef.current = next;
      if (next) {
        // Only enable spoken responses and announce readiness - do NOT auto-start the mic!
        speak('Jarvis voice systems online.', undefined, true);
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
