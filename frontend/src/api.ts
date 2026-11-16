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
  original_model?: string | null;
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

export interface ModelOption {
  id: string;
  label: string;
  provider: string;
  specialty: string;
  supports_vision: boolean;
}

export interface ModelsResponse {
  models: ModelOption[];
  default_model: string;
}

export interface OperatorUser {
  id: string;
  username: string;
  created_at: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: OperatorUser;
}

export interface SessionSummary {
  id: string;
  title: string;
  has_dut: boolean;
  message_count: number;
  created_at: string;
  updated_at: string;
}

export interface SessionMessage {
  id?: string;
  role: 'user' | 'assistant';
  content: string;
  imagePreviewUrl?: string;
  metadata?: {
    provider?: string;
    model_id?: string;
    attempts?: number;
    fallback_used?: boolean;
    [key: string]: unknown;
  };
  [key: string]: unknown;
}

export interface SessionDetail {
  id: string;
  title: string;
  dut_image: string | null;
  messages: SessionMessage[];
  created_at: string;
  updated_at: string;
}

export interface SaveSessionPayload {
  id?: string;
  title?: string;
  dut_image?: string | null;
  messages: unknown[];
}

export interface VaultStats {
  total_documents: number;
  total_chunks: number;
  branches: Record<string, number>;
  source_types: Record<string, number>;
  database_size_bytes: number;
}


const TOKEN_KEY = 'circuitsnap_token';

export function getStoredToken(): string | null {
  try {
    return localStorage.getItem(TOKEN_KEY);
  } catch {
    return null;
  }
}

export function setStoredToken(token: string | null): void {
  try {
    if (token) {
      localStorage.setItem(TOKEN_KEY, token);
    } else {
      localStorage.removeItem(TOKEN_KEY);
    }
  } catch {
    // ignore localStorage errors
  }
}

export function getAuthHeaders(extraHeaders: Record<string, string> = {}): Record<string, string> {
  const token = getStoredToken();
  const headers: Record<string, string> = { ...extraHeaders };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  return headers;
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
 * Fetches available AI models from GET /api/models.
 */
export async function fetchAvailableModels(): Promise<ModelOption[]> {
  const response = await fetch('/api/models');
  if (!response.ok) {
    let errorDetail = `Failed to fetch models (${response.status})`;
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
  const data: ModelsResponse = await response.json();
  return data.models || [];
}

/**
 * Sends a textual multi-turn chat message to POST /api/chat.
 */
export async function sendChatMessage(
  message: string,
  history: ChatMessage[] = [],
  model?: string,
  provider?: string,
  modelId?: string
): Promise<ChatResponse> {
  const response = await fetch('/api/chat', {
    method: 'POST',
    headers: getAuthHeaders({
      'Content-Type': 'application/json',
    }),
    body: JSON.stringify({
      message,
      history,
      model: model || undefined,
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
  model?: string,
  provider?: string,
  modelId?: string
): Promise<ChatResponse> {
  const formData = new FormData();
  formData.append('file', file);
  if (prompt && prompt.trim()) {
    formData.append('prompt', prompt.trim());
  }
  if (model) {
    formData.append('model', model);
  }
  if (provider) {
    formData.append('provider', provider);
  }
  if (modelId) {
    formData.append('model_id', modelId);
  }

  const response = await fetch('/api/analyze', {
    method: 'POST',
    headers: getAuthHeaders(),
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

/**
 * Registers a new operator account and saves access token in localStorage.
 */
export async function registerOperator(username: string, password: string): Promise<AuthResponse> {
  const response = await fetch('/api/auth/register', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password }),
  });

  if (!response.ok) {
    let errorDetail = `Registration failed (${response.status})`;
    try {
      const errJson = await response.json();
      if (errJson && errJson.detail) {
        errorDetail = typeof errJson.detail === 'string' ? errJson.detail : JSON.stringify(errJson.detail);
      }
    } catch {
      // ignore
    }
    throw new Error(errorDetail);
  }

  const data: AuthResponse = await response.json();
  setStoredToken(data.access_token);
  return data;
}

/**
 * Logs in an existing operator and saves access token in localStorage.
 */
export async function loginOperator(username: string, password: string): Promise<AuthResponse> {
  const response = await fetch('/api/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password }),
  });

  if (!response.ok) {
    let errorDetail = `Login failed (${response.status})`;
    try {
      const errJson = await response.json();
      if (errJson && errJson.detail) {
        errorDetail = typeof errJson.detail === 'string' ? errJson.detail : JSON.stringify(errJson.detail);
      }
    } catch {
      // ignore
    }
    throw new Error(errorDetail);
  }

  const data: AuthResponse = await response.json();
  setStoredToken(data.access_token);
  return data;
}

/**
 * Validates current stored bearer token and returns operator profile, or null if guest/expired.
 */
export async function fetchCurrentOperator(): Promise<OperatorUser | null> {
  const token = getStoredToken();
  if (!token) return null;

  try {
    const response = await fetch('/api/auth/me', {
      headers: getAuthHeaders(),
    });
    if (!response.ok) {
      if (response.status === 401) {
        setStoredToken(null);
      }
      return null;
    }
    return response.json();
  } catch {
    return null;
  }
}

/**
 * Logs out current operator by clearing stored bearer token.
 */
export function logoutOperator(): void {
  setStoredToken(null);
}

/**
 * Fetches all saved diagnostic sessions for the current operator.
 */
export async function fetchVaultSessions(): Promise<SessionSummary[]> {
  const response = await fetch('/api/vault/sessions', {
    headers: getAuthHeaders(),
  });
  if (!response.ok) {
    if (response.status === 401) return [];
    throw new Error(`Failed to fetch sessions (${response.status})`);
  }
  return response.json();
}

/**
 * Fetches full session detail by ID.
 */
export async function fetchSessionDetail(id: string): Promise<SessionDetail> {
  const response = await fetch(`/api/vault/sessions/${encodeURIComponent(id)}`, {
    headers: getAuthHeaders(),
  });
  if (!response.ok) {
    throw new Error(`Failed to fetch session detail (${response.status})`);
  }
  return response.json();
}

/**
 * Saves or updates a session in the operator's diagnostic vault.
 */
export async function saveCurrentSession(payload: SaveSessionPayload): Promise<SessionDetail> {
  const response = await fetch('/api/vault/sessions', {
    method: 'POST',
    headers: getAuthHeaders({ 'Content-Type': 'application/json' }),
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    let errorDetail = `Failed to save session (${response.status})`;
    try {
      const errJson = await response.json();
      if (errJson?.detail) {
        errorDetail = typeof errJson.detail === 'string' ? errJson.detail : JSON.stringify(errJson.detail);
      }
    } catch {
      // ignore
    }
    throw new Error(errorDetail);
  }
  return response.json();
}

/**
 * Deletes a session from the operator's vault.
 */
export async function deleteVaultSession(id: string): Promise<void> {
  const response = await fetch(`/api/vault/sessions/${encodeURIComponent(id)}`, {
    method: 'DELETE',
    headers: getAuthHeaders(),
  });
  if (!response.ok) {
    throw new Error(`Failed to delete session (${response.status})`);
  }
}

/**
 * Fetches statistics from the Self-Evolving Knowledge Vault.
 */
export async function fetchVaultStats(): Promise<VaultStats> {
  const response = await fetch('/api/learn/stats');
  if (!response.ok) {
    throw new Error(`Failed to fetch vault stats (${response.status})`);
  }
  return response.json();
}

/**
 * Ingests a syllabus note, PDF, or markdown document into the Self-Evolving Knowledge Vault.
 */
export async function ingestVaultDocument(
  file: File,
  branch = 'ALL'
): Promise<{ message: string; title: string; chunks_indexed: number }> {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('branch', branch);

  const response = await fetch('/api/learn/ingest', {
    method: 'POST',
    headers: getAuthHeaders(),
    body: formData,
  });

  if (!response.ok) {
    let errorDetail = `Document ingestion failed (${response.status})`;
    try {
      const err = await response.json();
      if (err?.detail) {
        errorDetail = typeof err.detail === 'string' ? err.detail : JSON.stringify(err.detail);
      }
    } catch {
      // ignore
    }
    throw new Error(errorDetail);
  }

  return response.json();
}

/**
 * Teaches or records user knowledge/feedback into the Knowledge Vault.
 */
export async function sendFeedbackToVault(
  text: string,
  branch = 'ALL',
  title = 'User Knowledge Contribution'
): Promise<{ message: string; chunks_indexed: number }> {
  const response = await fetch('/api/learn/feedback', {
    method: 'POST',
    headers: getAuthHeaders({ 'Content-Type': 'application/json' }),
    body: JSON.stringify({ text, branch, title }),
  });

  if (!response.ok) {
    let errorDetail = `Feedback ingestion failed (${response.status})`;
    try {
      const err = await response.json();
      if (err?.detail) {
        errorDetail = typeof err.detail === 'string' ? err.detail : JSON.stringify(err.detail);
      }
    } catch {
      // ignore
    }
    throw new Error(errorDetail);
  }

  return response.json();
}

export interface StreamChatOptions {
  model?: string;
  provider?: string;
  modelId?: string;
  responseStyle?: string;
  signal?: AbortSignal;
  onStep?: (step: string) => void;
  onChunk?: (chunk: string) => void;
  onDone?: (res: ChatResponse) => void;
  onError?: (err: Error) => void;
}

/**
 * Streams a chat query via Server-Sent Events (SSE) with real-time cognitive trace steps and chunk delivery.
 */
export async function streamChatMessage(
  message: string,
  history: ChatMessage[] = [],
  options: StreamChatOptions = {}
): Promise<void> {
  const { model, provider, modelId, responseStyle, signal, onStep, onChunk, onDone, onError } = options;

  try {
    const response = await fetch('/api/chat/stream', {
      method: 'POST',
      signal,
      headers: getAuthHeaders({
        'Content-Type': 'application/json',
      }),
      body: JSON.stringify({
        message,
        history,
        model: model || undefined,
        provider: provider || undefined,
        model_id: modelId || undefined,
        response_style: responseStyle || undefined,
      }),
    });

    if (!response.ok || !response.body) {
      // Fallback to standard chat endpoint if streaming fails
      const fallbackRes = await sendChatMessage(message, history, model, provider, modelId);
      onChunk?.(fallbackRes.answer);
      onDone?.(fallbackRes);
      return;
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder('utf-8');
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n\n');
      buffer = lines.pop() || '';

      for (const line of lines) {
        if (!line.trim()) continue;

        let eventType = 'message';
        let dataStr = '';

        const subLines = line.split('\n');
        for (const sub of subLines) {
          if (sub.startsWith('event:')) {
            eventType = sub.replace('event:', '').trim();
          } else if (sub.startsWith('data:')) {
            dataStr = sub.replace('data:', '').trim();
          }
        }

        if (!dataStr) continue;

        try {
          const parsed = JSON.parse(dataStr);
          if (eventType === 'step' && parsed.step) {
            onStep?.(parsed.step);
          } else if (eventType === 'chunk' && parsed.chunk) {
            onChunk?.(parsed.chunk);
          } else if (eventType === 'done') {
            const chatRes: ChatResponse = {
              answer: parsed.answer || '',
              provider: parsed.provider || 'J.A.R.V.I.S. Core',
              model_id: parsed.model_id || 'jarvis-auto',
              status: 'success',
              fallback_used: parsed.fallback_used ?? false,
              attempts: parsed.attempts ?? 1,
            };
            onDone?.(chatRes);
          }
        } catch {
          // ignore malformed SSE line
        }
      }
    }
  } catch (err: unknown) {
    if ((err as Error)?.name === 'AbortError') {
      return;
    }
    if (onError) {
      onError(err instanceof Error ? err : new Error(String(err)));
    } else {
      throw err;
    }
  }
}


