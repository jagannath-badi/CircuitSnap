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
}

/**
 * Strips raw markdown, HTML, and KaTeX math symbols into spoken plain English with natural electronics units.
 */
export function cleanTextForSpeech(raw: string): string {
  let text = raw;

  // Replace single-pill confidence badges
  text = text.replace(/\[\s*CONFIRMED\s*\]/gi, 'Confirmed: ');
  text = text.replace(/\[\s*LIKELY\s*\]/gi, 'Likely: ');
  text = text.replace(/\[\s*CANNOT CONFIRM\s*\]/gi, 'Unconfirmed: ');

  // Replace Markdown tables with spoken equivalents
  text = text.replace(/\|[^\n]+\|/g, (match) => {
    // If it's a delimiter row like | :--- | :--- |, remove it
    if (/^\|[\s\-:]+\|$/.test(match.trim())) return '';
    const cells = match
      .split('|')
      .map((c) => c.trim())
      .filter(Boolean);
    return cells.join(', ') + '. ';
  });

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
  text = text.replace(/[*#_~`>]+/g, ' ');
  text = text.replace(/\[([^\]]+)\]\([^)]+\)/g, '$1');
  text = text.replace(/\s+/g, ' ').trim();

  // Keep spoken response to key technical findings (first 2-3 sentences or ~350 chars) to stay punchy and responsive
  if (text.length > 350) {
    const periodIdx = text.indexOf('.', 250);
    if (periodIdx !== -1 && periodIdx < 450) {
      text = text.substring(0, periodIdx + 1);
    }
  }

  return text;
}

export function useJarvisVoice({ onTranscript }: UseJarvisVoiceOptions = {}) {
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

  useEffect(() => {
    onTranscriptRef.current = onTranscript;
  }, [onTranscript]);

  useEffect(() => {
    if (!supported) return;

    const win = window as WindowWithSpeech;
    const SpeechRecognition = win.SpeechRecognition || win.webkitSpeechRecognition;

    if (SpeechRecognition) {
      try {
        const recognition = new SpeechRecognition();
        recognition.continuous = false;
        recognition.interimResults = false;
        recognition.lang = 'en-US';

        recognition.onstart = () => {
          setIsListening(true);
        };

        recognition.onend = () => {
          setIsListening(false);
        };

        recognition.onerror = () => {
          setIsListening(false);
        };

        recognition.onresult = (event) => {
          const lastIdx = event.results.length - 1;
          const transcript = event.results[lastIdx][0].transcript;
          if (transcript && onTranscriptRef.current) {
            onTranscriptRef.current(transcript.trim());
          }
        };

        recognitionRef.current = recognition;
      } catch {
        // Ignore initialization error
      }
    }

    return () => {
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

  const cancelSpeech = useCallback(() => {
    if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
      window.speechSynthesis.cancel();
      setIsSpeaking(false);
    }
  }, []);

  const startListening = useCallback(() => {
    if (!recognitionRef.current) return;
    cancelSpeech();
    try {
      recognitionRef.current.start();
    } catch {
      // recognition already active
    }
  }, [cancelSpeech]);

  const stopListening = useCallback(() => {
    if (!recognitionRef.current) return;
    try {
      recognitionRef.current.stop();
    } catch {
      // ignore
    }
  }, []);

  const speak = useCallback(
    (rawText: string) => {
      if (!isVoiceEnabled || typeof window === 'undefined' || !('speechSynthesis' in window)) {
        return;
      }

      window.speechSynthesis.cancel();
      const cleaned = cleanTextForSpeech(rawText);
      if (!cleaned) return;

      const utterance = new SpeechSynthesisUtterance(cleaned);
      utterance.pitch = 0.92;
      utterance.rate = 1.05;

      // Select a crisp English voice (UK or US)
      const voices = window.speechSynthesis.getVoices();
      const ukVoice = voices.find(
        (v) => (v.lang === 'en-GB' || v.name.includes('UK') || v.name.includes('British')) && !v.name.includes('Female')
      );
      const enVoice = ukVoice || voices.find((v) => v.lang.startsWith('en')) || null;
      if (enVoice) {
        utterance.voice = enVoice;
      }

      utterance.onstart = () => setIsSpeaking(true);
      utterance.onend = () => setIsSpeaking(false);
      utterance.onerror = () => setIsSpeaking(false);

      window.speechSynthesis.speak(utterance);
    },
    [isVoiceEnabled]
  );

  const toggleVoiceMode = useCallback(() => {
    setIsVoiceEnabled((prev) => {
      const next = !prev;
      if (!next) {
        cancelSpeech();
        stopListening();
      }
      return next;
    });
  }, [cancelSpeech, stopListening]);

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
  };
}
