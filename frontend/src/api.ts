import type { Task, TaskCreateRequest, TaskUpdateRequest, Member, TaskCompletion, User, AuthResponse, LoginRequest, RegisterRequest } from './types';

// Use VITE_API_URL for production deployment, defaults to /api for local development
const BASE_URL = import.meta.env.VITE_API_URL || '/api';

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
    throw new Error('Unauthorized');
  }

  if (!response.ok) {
    throw new Error(`HTTP error: ${response.status}`);
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

    delete: (memberId: number) =>
      fetchJSON<void>(`${BASE_URL}/members/${memberId}`, {
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
};
