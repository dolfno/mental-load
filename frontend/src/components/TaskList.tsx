import type { Task, Member } from '../types';
import { TaskCard } from './TaskCard';

interface TaskListProps {
  tasks: Task[];
  members: Member[];
  onComplete: (taskId: number, memberId: number) => void;
}

export function TaskList({ tasks, members, onComplete }: TaskListProps) {
  if (tasks.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        Geen taken gevonden
      </div>
    );
  }

  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
      {tasks.map(task => (
        <TaskCard
          key={task.id}
          task={task}
          members={members}
          onComplete={onComplete}
        />
      ))}
    </div>
  );
}
