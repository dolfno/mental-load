import type { Task } from '../types';
import { TaskCard } from './TaskCard';

interface TaskListProps {
  tasks: Task[];
  onComplete: (taskId: number) => void;
  onPostpone: (taskId: number, newDueDate: string) => void;
  onEdit: (task: Task) => void;
  onDelete: (taskId: number) => void;
}

export function TaskList({ tasks, onComplete, onPostpone, onEdit, onDelete }: TaskListProps) {
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
          onComplete={onComplete}
          onPostpone={onPostpone}
          onEdit={onEdit}
          onDelete={onDelete}
        />
      ))}
    </div>
  );
}
