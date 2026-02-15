import { useState } from 'react';
import type { Member, TimeOfDay, RoutineCreateRequest } from '../types';

interface WeekplanAddFormProps {
  members: Member[];
  onSubmit: (data: RoutineCreateRequest) => void;
  onClose: () => void;
}

const DAY_LABELS = ['Ma', 'Di', 'Wo', 'Do', 'Vr', 'Za', 'Zo'];
const WEEKDAYS = [0, 1, 2, 3, 4];
const WEEKEND = [5, 6];

export function WeekplanAddForm({ members, onSubmit, onClose }: WeekplanAddFormProps) {
  const [name, setName] = useState('');
  const [selectedDays, setSelectedDays] = useState<number[]>([]);
  const [timeOfDay, setTimeOfDay] = useState<TimeOfDay>('morning');
  const [assignedToId, setAssignedToId] = useState<number | null>(null);

  const toggleDay = (day: number) => {
    setSelectedDays(prev =>
      prev.includes(day) ? prev.filter(d => d !== day) : [...prev, day].sort()
    );
  };

  const selectWeekdays = () => {
    setSelectedDays(prev => {
      const allSelected = WEEKDAYS.every(d => prev.includes(d));
      if (allSelected) {
        return prev.filter(d => !WEEKDAYS.includes(d));
      }
      return [...new Set([...prev, ...WEEKDAYS])].sort();
    });
  };

  const selectWeekend = () => {
    setSelectedDays(prev => {
      const allSelected = WEEKEND.every(d => prev.includes(d));
      if (allSelected) {
        return prev.filter(d => !WEEKEND.includes(d));
      }
      return [...new Set([...prev, ...WEEKEND])].sort();
    });
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim() || selectedDays.length === 0) return;
    onSubmit({
      name: name.trim(),
      days_of_week: selectedDays,
      time_of_day: timeOfDay,
      assigned_to_id: assignedToId,
    });
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-md">
        <div className="px-4 py-3 border-b border-gray-200 flex items-center justify-between">
          <h3 className="text-lg font-semibold text-gray-800">Routine toevoegen</h3>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-xl leading-none">&times;</button>
        </div>
        <form onSubmit={handleSubmit} className="p-4 space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Naam</label>
            <input
              type="text"
              value={name}
              onChange={e => setName(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="bijv. Marie naar school brengen"
              autoFocus
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Dagen</label>
            <div className="flex gap-1 mb-2">
              {DAY_LABELS.map((label, i) => (
                <button
                  key={i}
                  type="button"
                  onClick={() => toggleDay(i)}
                  className={`flex-1 py-1.5 text-xs font-medium rounded transition-colors ${
                    selectedDays.includes(i)
                      ? 'bg-blue-500 text-white'
                      : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                  }`}
                >
                  {label}
                </button>
              ))}
            </div>
            <div className="flex gap-2">
              <button
                type="button"
                onClick={selectWeekdays}
                className={`px-3 py-1 text-xs rounded-full transition-colors ${
                  WEEKDAYS.every(d => selectedDays.includes(d))
                    ? 'bg-blue-100 text-blue-700'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
              >
                Doordeweeks
              </button>
              <button
                type="button"
                onClick={selectWeekend}
                className={`px-3 py-1 text-xs rounded-full transition-colors ${
                  WEEKEND.every(d => selectedDays.includes(d))
                    ? 'bg-blue-100 text-blue-700'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
              >
                Weekend
              </button>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Moment</label>
            <div className="flex gap-2">
              <button
                type="button"
                onClick={() => setTimeOfDay('morning')}
                className={`flex-1 py-2 text-sm rounded-md transition-colors ${
                  timeOfDay === 'morning'
                    ? 'bg-blue-500 text-white'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
              >
                Ochtend
              </button>
              <button
                type="button"
                onClick={() => setTimeOfDay('evening')}
                className={`flex-1 py-2 text-sm rounded-md transition-colors ${
                  timeOfDay === 'evening'
                    ? 'bg-blue-500 text-white'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
              >
                Avond
              </button>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Toegewezen aan</label>
            <select
              value={assignedToId ?? ''}
              onChange={e => setAssignedToId(e.target.value ? Number(e.target.value) : null)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Niet toegewezen</option>
              {members.map(m => (
                <option key={m.id} value={m.id}>{m.name}</option>
              ))}
            </select>
          </div>

          <div className="flex gap-2 pt-2">
            <button
              type="submit"
              disabled={!name.trim() || selectedDays.length === 0}
              className="flex-1 py-2 bg-blue-500 text-white rounded-md text-sm font-medium hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              Toevoegen
            </button>
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 bg-gray-100 text-gray-700 rounded-md text-sm hover:bg-gray-200 transition-colors"
            >
              Annuleren
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
