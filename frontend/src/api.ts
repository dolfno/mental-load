import type { Task, TaskCreateRequest, TaskUpdateRequest, Member, TaskCompletion } from './types';

const BASE_URL = '/api';

async function fetchJSON<T>(url: string, options?: RequestInit): Promise<T> {
  const response = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  });
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
};
