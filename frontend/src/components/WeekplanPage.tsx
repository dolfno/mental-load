import { useState, useEffect, useCallback } from 'react';
import { api } from '../api';
import type { Member, WeeklyRoutine, RoutineCreateRequest } from '../types';
import { WeekplanAddForm } from './WeekplanAddForm';

const DAY_LABELS = ['Ma', 'Di', 'Wo', 'Do', 'Vr', 'Za', 'Zo'];
const UNASSIGNED_COLOR = '#D1D5DB';

interface WeekplanPageProps {
  members: Member[];
  onMembersChanged: () => void;
}

export function WeekplanPage({ members, onMembersChanged }: WeekplanPageProps) {
  const [routines, setRoutines] = useState<WeeklyRoutine[]>([]);
  const [loading, setLoading] = useState(true);
  const [showAddForm, setShowAddForm] = useState(false);

  const loadRoutines = useCallback(async () => {
    try {
      const data = await api.routines.list();
      setRoutines(data);
    } catch (err) {
      console.error('Failed to load routines:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadRoutines();
  }, [loadRoutines]);

  const handleCreate = async (data: RoutineCreateRequest) => {
    try {
      await api.routines.create(data);
      await loadRoutines();
      setShowAddForm(false);
    } catch (err) {
      console.error('Failed to create routine:', err);
    }
  };

  const cycleAssignment = async (routine: WeeklyRoutine) => {
    if (members.length === 0) return;

    let nextAssignedId: number | null;
    if (routine.assigned_to_id === null) {
      nextAssignedId = members[0].id;
    } else {
      const currentIndex = members.findIndex(m => m.id === routine.assigned_to_id);
      if (currentIndex === -1 || currentIndex === members.length - 1) {
        nextAssignedId = null;
      } else {
        nextAssignedId = members[currentIndex + 1].id;
      }
    }

    // Optimistic update
    setRoutines(prev =>
      prev.map(r => r.id === routine.id ? { ...r, assigned_to_id: nextAssignedId } : r)
    );

    try {
      await api.routines.assign(routine.id, nextAssignedId);
    } catch (err) {
      console.error('Failed to assign routine:', err);
      await loadRoutines();
    }
  };

  const handleDelete = async (routineId: number) => {
    setRoutines(prev => prev.filter(r => r.id !== routineId));
    try {
      await api.routines.delete(routineId);
    } catch (err) {
      console.error('Failed to delete routine:', err);
      await loadRoutines();
    }
  };

  const getMemberColor = (assignedToId: number | null): string => {
    if (assignedToId === null) return UNASSIGNED_COLOR;
    const member = members.find(m => m.id === assignedToId);
    return member?.color || UNASSIGNED_COLOR;
  };

  const getMemberName = (assignedToId: number | null): string => {
    if (assignedToId === null) return '';
    const member = members.find(m => m.id === assignedToId);
    return member?.name || '';
  };

  // Ensure members have colors assigned
  useEffect(() => {
    const PALETTE = ['#3B82F6', '#EF4444', '#10B981', '#F59E0B', '#8B5CF6', '#EC4899', '#06B6D4', '#F97316'];
    const membersWithoutColor = members.filter(m => !m.color);
    if (membersWithoutColor.length === 0) return;

    const usedColors = new Set(members.filter(m => m.color).map(m => m.color));

    const assignColors = async () => {
      for (const member of membersWithoutColor) {
        const availableColor = PALETTE.find(c => !usedColors.has(c)) || PALETTE[0];
        usedColors.add(availableColor);
        try {
          await api.members.updateColor(member.id, availableColor);
        } catch (err) {
          console.error('Failed to assign color:', err);
        }
      }
      onMembersChanged();
    };
    assignColors();
  }, [members, onMembersChanged]);

  const getRoutinesForDayAndTime = (day: number, time: 'morning' | 'evening') =>
    routines.filter(r => r.day_of_week === day && r.time_of_day === time);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-gray-500">Laden...</div>
      </div>
    );
  }

  return (
    <main className="max-w-7xl mx-auto px-4 py-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-semibold text-gray-800">Weekplan</h2>
        <button
          onClick={() => setShowAddForm(true)}
          className="px-4 py-2 bg-blue-500 text-white rounded-md text-sm font-medium hover:bg-blue-600 transition-colors"
        >
          + Toevoegen
        </button>
      </div>

      {/* Legend */}
      {members.length > 0 && (
        <div className="flex flex-wrap gap-3 mb-4">
          {members.map(m => (
            <div key={m.id} className="flex items-center gap-1.5 text-sm text-gray-600">
              <span
                className="w-3 h-3 rounded-full inline-block"
                style={{ backgroundColor: m.color || UNASSIGNED_COLOR }}
              />
              {m.name}
            </div>
          ))}
        </div>
      )}

      {/* Grid */}
      <div className="grid grid-cols-7 gap-2">
        {DAY_LABELS.map((label, dayIndex) => (
          <div key={dayIndex} className="min-w-0">
            <div className="text-center text-sm font-semibold text-gray-700 mb-2 py-1 bg-gray-100 rounded">
              {label}
            </div>

            {/* Morning section */}
            <div className="mb-2">
              <div className="text-xs text-gray-400 uppercase tracking-wide mb-1 px-1">Ochtend</div>
              <div className="space-y-1 min-h-[2rem]">
                {getRoutinesForDayAndTime(dayIndex, 'morning').map(routine => (
                  <RoutinePill
                    key={routine.id}
                    routine={routine}
                    color={getMemberColor(routine.assigned_to_id)}
                    memberName={getMemberName(routine.assigned_to_id)}
                    onClick={() => cycleAssignment(routine)}
                    onDelete={() => handleDelete(routine.id)}
                  />
                ))}
              </div>
            </div>

            {/* Evening section */}
            <div>
              <div className="text-xs text-gray-400 uppercase tracking-wide mb-1 px-1">Avond</div>
              <div className="space-y-1 min-h-[2rem]">
                {getRoutinesForDayAndTime(dayIndex, 'evening').map(routine => (
                  <RoutinePill
                    key={routine.id}
                    routine={routine}
                    color={getMemberColor(routine.assigned_to_id)}
                    memberName={getMemberName(routine.assigned_to_id)}
                    onClick={() => cycleAssignment(routine)}
                    onDelete={() => handleDelete(routine.id)}
                  />
                ))}
              </div>
            </div>
          </div>
        ))}
      </div>

      {showAddForm && (
        <WeekplanAddForm
          members={members}
          onSubmit={handleCreate}
          onClose={() => setShowAddForm(false)}
        />
      )}
    </main>
  );
}

function RoutinePill({
  routine,
  color,
  memberName,
  onClick,
  onDelete,
}: {
  routine: WeeklyRoutine;
  color: string;
  memberName: string;
  onClick: () => void;
  onDelete: () => void;
}) {
  const [showDelete, setShowDelete] = useState(false);

  return (
    <div
      className="relative group"
      onMouseEnter={() => setShowDelete(true)}
      onMouseLeave={() => setShowDelete(false)}
    >
      <button
        onClick={onClick}
        className="w-full text-left px-2 py-1.5 rounded text-xs font-medium text-white truncate transition-opacity hover:opacity-80"
        style={{ backgroundColor: color }}
        title={`${routine.name}${memberName ? ` — ${memberName}` : ''}\nKlik om toe te wijzen`}
      >
        {routine.name}
      </button>
      {showDelete && (
        <button
          onClick={e => {
            e.stopPropagation();
            onDelete();
          }}
          className="absolute -top-1 -right-1 w-4 h-4 bg-red-500 text-white rounded-full text-xs leading-none flex items-center justify-center hover:bg-red-600"
          title="Verwijderen"
        >
          &times;
        </button>
      )}
    </div>
  );
}
