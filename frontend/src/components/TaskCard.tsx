import type { Task, Member } from '../types';

interface TaskCardProps {
  task: Task;
  members: Member[];
  onComplete: (taskId: number, memberId: number) => void;
}

const urgencyColors = {
  high: 'bg-red-100 border-red-400 text-red-800',
  medium: 'bg-yellow-100 border-yellow-400 text-yellow-800',
  low: 'bg-green-100 border-green-400 text-green-800',
};

const urgencyBadge = {
  high: 'bg-red-500 text-white',
  medium: 'bg-yellow-500 text-white',
  low: 'bg-green-500 text-white',
};

function formatRecurrence(task: Task): string {
  const { type, interval, days, time_of_day } = task.recurrence;
  const dayNames = ['Ma', 'Di', 'Wo', 'Do', 'Vr', 'Za', 'Zo'];

  let text = '';
  switch (type) {
    case 'daily':
      text = interval === 1 ? 'Dagelijks' : `Elke ${interval} dagen`;
      break;
    case 'weekly':
      if (days && days.length > 0) {
        text = days.map(d => dayNames[d]).join(', ');
      } else {
        text = interval === 1 ? 'Wekelijks' : `Elke ${interval} weken`;
      }
      break;
    case 'biweekly':
      text = 'Om de 2 weken';
      break;
    case 'monthly':
      text = interval === 1 ? 'Maandelijks' : `Elke ${interval} maanden`;
      break;
    case 'quarterly':
      text = 'Per kwartaal';
      break;
    case 'yearly':
      text = interval === 1 ? 'Jaarlijks' : `${interval}x per jaar`;
      break;
    case 'continuous':
      text = 'Doorlopend';
      break;
  }

  if (time_of_day) {
    text += ` (${time_of_day === 'morning' ? 'ochtend' : 'avond'})`;
  }

  return text;
}

function formatDueDate(dateStr: string | null): string {
  if (!dateStr) return '';
  const date = new Date(dateStr);
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const due = new Date(date);
  due.setHours(0, 0, 0, 0);

  const diffDays = Math.floor((due.getTime() - today.getTime()) / (1000 * 60 * 60 * 24));

  if (diffDays < 0) return `${Math.abs(diffDays)} dagen te laat`;
  if (diffDays === 0) return 'Vandaag';
  if (diffDays === 1) return 'Morgen';
  return `Over ${diffDays} dagen`;
}

export function TaskCard({ task, members, onComplete }: TaskCardProps) {
  const handleComplete = (memberId: number) => {
    onComplete(task.id, memberId);
  };

  return (
    <div className={`border-l-4 rounded-lg p-4 shadow-sm ${urgencyColors[task.calculated_urgency]}`}>
      <div className="flex justify-between items-start mb-2">
        <h3 className="font-semibold text-lg">{task.name}</h3>
        <span className={`px-2 py-1 rounded text-xs font-medium ${urgencyBadge[task.calculated_urgency]}`}>
          {task.calculated_urgency === 'high' ? 'Hoog' : task.calculated_urgency === 'medium' ? 'Gemiddeld' : 'Laag'}
        </span>
      </div>

      <div className="text-sm opacity-75 mb-3">
        <div>{formatRecurrence(task)}</div>
        {task.next_due && <div className="font-medium">{formatDueDate(task.next_due)}</div>}
      </div>

      <div className="flex gap-2 flex-wrap">
        {members.map(member => (
          <button
            key={member.id}
            onClick={() => handleComplete(member.id)}
            className="px-3 py-1 bg-white/50 hover:bg-white/80 rounded border border-current/20 text-sm transition-colors"
          >
            {member.name}
          </button>
        ))}
      </div>
    </div>
  );
}
