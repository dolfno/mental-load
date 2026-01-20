import { useState, useEffect, useCallback } from 'react';
import type { Task, Member, TaskCreateRequest, TaskUpdateRequest } from '../types';
import { api } from '../api';
import { TaskList } from './TaskList';
import { TaskForm } from './TaskForm';
import { Modal } from './Modal';

type ViewMode = 'all' | 'urgent' | 'upcoming';

interface DashboardProps {
  members: Member[];
}

export function Dashboard({ members }: DashboardProps) {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<ViewMode>('all');
  const [showAddForm, setShowAddForm] = useState(false);
  const [editingTask, setEditingTask] = useState<Task | null>(null);
  const [formHasChanges, setFormHasChanges] = useState(false);

  const loadTasks = useCallback(async () => {
    try {
      let loadedTasks: Task[];
      switch (viewMode) {
        case 'urgent':
          loadedTasks = await api.tasks.urgent();
          break;
        case 'upcoming':
          loadedTasks = await api.tasks.upcoming();
          break;
        default:
          loadedTasks = await api.tasks.list();
      }
      setTasks(loadedTasks);
    } catch (err) {
      setError('Kan taken niet laden');
      console.error(err);
    }
  }, [viewMode]);

  useEffect(() => {
    const init = async () => {
      setLoading(true);
      await loadTasks();
      setLoading(false);
    };
    init();
  }, [loadTasks]);

  const handleComplete = async (taskId: number) => {
    try {
      await api.tasks.complete(taskId);
      await loadTasks();
    } catch (err) {
      setError('Kan taak niet voltooien');
      console.error(err);
    }
  };

  const handlePostpone = async (taskId: number, newDueDate: string) => {
    try {
      await api.tasks.postpone(taskId, newDueDate);
      await loadTasks();
    } catch (err) {
      setError('Kan taak niet uitstellen');
      console.error(err);
    }
  };

  const handleEdit = (task: Task) => {
    setEditingTask(task);
    setShowAddForm(false);
    setFormHasChanges(false);
    setError(null);
  };

  const handleCloseAttempt = (): boolean => {
    if (formHasChanges) {
      return window.confirm('Je hebt niet-opgeslagen wijzigingen. Weet je zeker dat je wilt sluiten?');
    }
    return true;
  };

  const handleCloseAddForm = () => {
    setShowAddForm(false);
    setFormHasChanges(false);
  };

  const handleCloseEditForm = () => {
    setEditingTask(null);
    setFormHasChanges(false);
  };

  const handleDelete = async (taskId: number) => {
    try {
      await api.tasks.delete(taskId);
      await loadTasks();
    } catch (err) {
      setError('Kan taak niet verwijderen');
      console.error(err);
    }
  };

  const handleAddTask = async (data: TaskCreateRequest | TaskUpdateRequest) => {
    try {
      await api.tasks.create(data as TaskCreateRequest);
      await loadTasks();
      setShowAddForm(false);
      setFormHasChanges(false);
    } catch (err) {
      setError('Kan taak niet toevoegen');
      console.error(err);
    }
  };

  const handleUpdateTask = async (data: TaskCreateRequest | TaskUpdateRequest) => {
    if (!editingTask) return;
    try {
      await api.tasks.update(editingTask.id, data as TaskUpdateRequest);
      await loadTasks();
      setEditingTask(null);
      setFormHasChanges(false);
    } catch (err) {
      setError('Kan taak niet bijwerken');
      console.error(err);
    }
  };

  if (loading) {
    return (
      <main className="max-w-7xl mx-auto px-4 py-6">
        <div className="text-gray-500">Laden...</div>
      </main>
    );
  }

  return (
    <main className="max-w-7xl mx-auto px-4 py-6 space-y-6">
      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative">
          {error}
          <button
            onClick={() => setError(null)}
            className="absolute top-3 right-4 text-red-700"
          >
            ×
          </button>
        </div>
      )}

      <div className="flex justify-end">
        <button
          onClick={() => {
            setShowAddForm(true);
            setEditingTask(null);
            setFormHasChanges(false);
            setError(null);
          }}
          className="px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600 transition-colors"
        >
          + Nieuwe taak
        </button>
      </div>

      <Modal
        isOpen={showAddForm}
        onClose={handleCloseAddForm}
        onCloseAttempt={handleCloseAttempt}
      >
        <TaskForm
          members={members}
          onSubmit={handleAddTask}
          onCancel={handleCloseAddForm}
          onFormChange={setFormHasChanges}
          error={error}
        />
      </Modal>

      <Modal
        isOpen={!!editingTask}
        onClose={handleCloseEditForm}
        onCloseAttempt={handleCloseAttempt}
      >
        {editingTask && (
          <TaskForm
            task={editingTask}
            members={members}
            onSubmit={handleUpdateTask}
            onCancel={handleCloseEditForm}
            onFormChange={setFormHasChanges}
            error={error}
          />
        )}
      </Modal>

      <div className="bg-white rounded-lg shadow-md p-4">
        <div className="flex gap-2 mb-4">
          <button
            onClick={() => setViewMode('all')}
            className={`px-4 py-2 rounded-md text-sm transition-colors ${
              viewMode === 'all'
                ? 'bg-blue-500 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            Alle taken
          </button>
          <button
            onClick={() => setViewMode('urgent')}
            className={`px-4 py-2 rounded-md text-sm transition-colors ${
              viewMode === 'urgent'
                ? 'bg-red-500 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            Urgent
          </button>
          <button
            onClick={() => setViewMode('upcoming')}
            className={`px-4 py-2 rounded-md text-sm transition-colors ${
              viewMode === 'upcoming'
                ? 'bg-yellow-500 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            Komende week
          </button>
        </div>

        <TaskList
          tasks={tasks}
          onComplete={handleComplete}
          onPostpone={handlePostpone}
          onEdit={handleEdit}
          onDelete={handleDelete}
        />
      </div>
    </main>
  );
}
