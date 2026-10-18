export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

export interface ChatResponse {
  answer: string;
  provider: string;
  model_id: string;
  status: 'success' | 'error';
  error_type?: string | null;
  fallback_used: boolean;
  attempts: number;
}

export interface HealthResponse {
  status: string;
  models: {
    default?: string;
    model_id?: string;
    provider?: string;
    [key: string]: unknown;
  };
}

export const ALLOWED_IMAGE_TYPES = [
  'image/jpeg',
  'image/png',
  'image/webp',
  'image/gif',
];

export const MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024; // 10 MB

/**
 * Checks the status of the CircuitSnap FastAPI backend.
 */
export async function checkHealth(): Promise<HealthResponse> {
  const response = await fetch('/api/health');
  if (!response.ok) {
    let errorDetail = `Health check failed (${response.status})`;
    try {
      const errJson = await response.json();
      if (errJson && errJson.detail) {
        errorDetail = typeof errJson.detail === 'string' ? errJson.detail : JSON.stringify(errJson.detail);
      }
    } catch {
      // ignore JSON parse error
    }
    throw new Error(errorDetail);
  }
  return response.json();
}

/**
 * Sends a textual multi-turn chat message to POST /api/chat.
 */
export async function sendChatMessage(
  message: string,
  history: ChatMessage[] = [],
  provider?: string,
  modelId?: string
): Promise<ChatResponse> {
  const response = await fetch('/api/chat', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      message,
      history,
      provider: provider || undefined,
      model_id: modelId || undefined,
    }),
  });

  if (!response.ok) {
    let errorDetail = `Chat request failed (${response.status})`;
    try {
      const errJson = await response.json();
      if (errJson && errJson.detail) {
        errorDetail = typeof errJson.detail === 'string' ? errJson.detail : JSON.stringify(errJson.detail);
      }
    } catch {
      // ignore JSON parse error
    }
    throw new Error(errorDetail);
  }

  return response.json();
}

/**
 * Sends an image (with optional prompt) to POST /api/analyze using FormData.
 */
export async function analyzeImage(
  file: File,
  prompt?: string,
  provider?: string,
  modelId?: string
): Promise<ChatResponse> {
  const formData = new FormData();
  formData.append('file', file);
  if (prompt && prompt.trim()) {
    formData.append('prompt', prompt.trim());
  }
  if (provider) {
    formData.append('provider', provider);
  }
  if (modelId) {
    formData.append('model_id', modelId);
  }

  const response = await fetch('/api/analyze', {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    let errorDetail = `Image analysis failed (${response.status})`;
    try {
      const errJson = await response.json();
      if (errJson && errJson.detail) {
        errorDetail = typeof errJson.detail === 'string' ? errJson.detail : JSON.stringify(errJson.detail);
      }
    } catch {
      // ignore JSON parse error
    }
    throw new Error(errorDetail);
  }

  return response.json();
}

