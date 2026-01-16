export type RecurrenceType =
  | 'daily'
  | 'weekly'
  | 'biweekly'
  | 'monthly'
  | 'quarterly'
  | 'yearly'
  | 'continuous';

export type Urgency = 'high' | 'medium' | 'low';

export type TimeOfDay = 'morning' | 'evening';

export interface RecurrencePattern {
  type: RecurrenceType;
  days?: number[] | null;
  interval: number;
  time_of_day?: TimeOfDay | null;
}

export interface Task {
  id: number;
  name: string;
  recurrence: RecurrencePattern;
  urgency_label: Urgency | null;
  calculated_urgency: Urgency;
  last_completed: string | null;
  next_due: string | null;
  is_active: boolean;
}

export interface TaskCreateRequest {
  name: string;
  recurrence: RecurrencePattern;
  urgency_label?: Urgency | null;
  next_due?: string | null;
}

export interface Member {
  id: number;
  name: string;
}

export interface TaskCompletion {
  id: number;
  task_id: number;
  task_name?: string;
  completed_at: string;
  completed_by_id: number;
  completed_by_name?: string;
}
