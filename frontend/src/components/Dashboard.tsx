import { useState, useEffect, useCallback } from 'react';
import type { Task, Member, TaskCreateRequest, TaskUpdateRequest } from '../types';
import { api } from '../api';
import { TaskList } from './TaskList';
import { TaskForm } from './TaskForm';
import { MemberSelector } from './MemberSelector';

type ViewMode = 'all' | 'urgent' | 'upcoming';

export function Dashboard() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [members, setMembers] = useState<Member[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<ViewMode>('all');
  const [showAddForm, setShowAddForm] = useState(false);
  const [editingTask, setEditingTask] = useState<Task | null>(null);

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

  const loadMembers = useCallback(async () => {
    try {
      const loadedMembers = await api.members.list();
      setMembers(loadedMembers);
    } catch (err) {
      console.error(err);
    }
  }, []);

  useEffect(() => {
    const init = async () => {
      setLoading(true);
      await Promise.all([loadTasks(), loadMembers()]);
      setLoading(false);
    };
    init();
  }, [loadTasks, loadMembers]);

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
    } catch (err) {
      setError('Kan taak niet bijwerken');
      console.error(err);
    }
  };

  const handleAddMember = async (name: string) => {
    try {
      await api.members.create(name);
      await loadMembers();
    } catch (err) {
      setError('Kan huisgenoot niet toevoegen');
      console.error(err);
    }
  };

  const handleDeleteMember = async (id: number) => {
    try {
      await api.members.delete(id);
      await loadMembers();
    } catch (err) {
      setError('Kan huisgenoot niet verwijderen');
      console.error(err);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-gray-500">Laden...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <h1 className="text-2xl font-bold text-gray-800">Aivin</h1>
          <p className="text-gray-500 text-sm">Huishoudelijk taakbeheer</p>
        </div>
      </header>

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

        <div className="flex flex-col sm:flex-row gap-4 justify-between">
          <MemberSelector
            members={members}
            onAddMember={handleAddMember}
            onDeleteMember={handleDeleteMember}
          />

          <div className="flex gap-2 items-start">
            <button
              onClick={() => {
                setShowAddForm(true);
                setEditingTask(null);
              }}
              className="px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600 transition-colors"
            >
              + Nieuwe taak
            </button>
          </div>
        </div>

        {showAddForm && (
          <TaskForm
            members={members}
            onSubmit={handleAddTask}
            onCancel={() => setShowAddForm(false)}
          />
        )}

        {editingTask && (
          <TaskForm
            task={editingTask}
            members={members}
            onSubmit={handleUpdateTask}
            onCancel={() => setEditingTask(null)}
          />
        )}

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
    </div>
  );
}
