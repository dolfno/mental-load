import type { Task, TaskCreateRequest, TaskUpdateRequest, Member, TaskCompletion, User, AuthResponse, LoginRequest, RegisterRequest, Note, NoteUpdateRequest } from './types';

// Use VITE_API_URL for production deployment, defaults to /api for local development
const BASE_URL = import.meta.env.VITE_API_URL || '/api';

// Error types for better error handling
export interface MemberDeleteConflict {
  detail: string;
  completion_count: number;
  assignment_count: number;
}

export class ApiError extends Error {
  status: number;
  data?: unknown;

  constructor(message: string, status: number, data?: unknown) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.data = data;
  }
}

// Token management
export function getToken(): string | null {
  return localStorage.getItem('auth_token');
}

export function setToken(token: string): void {
  localStorage.setItem('auth_token', token);
}

export function clearToken(): void {
  localStorage.removeItem('auth_token');
}

async function fetchJSON<T>(url: string, options?: RequestInit): Promise<T> {
  const token = getToken();
  const response = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(token && { 'Authorization': `Bearer ${token}` }),
      ...options?.headers,
    },
  });

  // Handle 401 Unauthorized - redirect to login (but not for auth endpoints)
  if (response.status === 401 && !url.includes('/auth/login') && !url.includes('/auth/register')) {
    clearToken();
    window.location.href = '/login';
    throw new ApiError('Unauthorized', 401);
  }

  if (!response.ok) {
    // Try to parse error response body for detailed error info
    let errorData: unknown;
    try {
      errorData = await response.json();
    } catch {
      // Ignore JSON parse errors
    }
    throw new ApiError(`HTTP error: ${response.status}`, response.status, errorData);
  }
  // Handle 204 No Content responses (e.g., DELETE)
  if (response.status === 204) {
    return undefined as T;
  }
  return response.json();
}

export const api = {
  tasks: {
    list: () => fetchJSON<Task[]>(`${BASE_URL}/tasks`),

    urgent: () => fetchJSON<Task[]>(`${BASE_URL}/tasks/urgent`),

    upcoming: () => fetchJSON<Task[]>(`${BASE_URL}/tasks/upcoming`),

    create: (data: TaskCreateRequest) =>
      fetchJSON<Task>(`${BASE_URL}/tasks`, {
        method: 'POST',
        body: JSON.stringify(data),
      }),

    complete: (taskId: number) =>
      fetchJSON<Task>(`${BASE_URL}/tasks/${taskId}/complete`, {
        method: 'POST',
        body: JSON.stringify({}),
      }),

    update: (taskId: number, data: TaskUpdateRequest) =>
      fetchJSON<Task>(`${BASE_URL}/tasks/${taskId}`, {
        method: 'PUT',
        body: JSON.stringify(data),
      }),

    postpone: (taskId: number, newDueDate: string) =>
      fetchJSON<Task>(`${BASE_URL}/tasks/${taskId}`, {
        method: 'PUT',
        body: JSON.stringify({ next_due: newDueDate }),
      }),

    delete: (taskId: number) =>
      fetchJSON<void>(`${BASE_URL}/tasks/${taskId}`, {
        method: 'DELETE',
      }),
  },

  members: {
    list: () => fetchJSON<Member[]>(`${BASE_URL}/members`),

    create: (name: string) =>
      fetchJSON<Member>(`${BASE_URL}/members`, {
        method: 'POST',
        body: JSON.stringify({ name }),
      }),

    delete: (memberId: number, force: boolean = false) =>
      fetchJSON<void>(`${BASE_URL}/members/${memberId}?force=${force}`, {
        method: 'DELETE',
      }),
  },

  history: {
    list: () => fetchJSON<TaskCompletion[]>(`${BASE_URL}/history`),
  },

  auth: {
    login: (data: LoginRequest) =>
      fetchJSON<AuthResponse>(`${BASE_URL}/auth/login`, {
        method: 'POST',
        body: JSON.stringify(data),
      }),

    register: (data: RegisterRequest) =>
      fetchJSON<AuthResponse>(`${BASE_URL}/auth/register`, {
        method: 'POST',
        body: JSON.stringify(data),
      }),

    me: () => fetchJSON<User>(`${BASE_URL}/auth/me`),
  },

  notes: {
    get: () => fetchJSON<Note>(`${BASE_URL}/notes`),

    update: (data: NoteUpdateRequest) =>
      fetchJSON<Note>(`${BASE_URL}/notes`, {
        method: 'PUT',
        body: JSON.stringify(data),
      }),
  },
};
