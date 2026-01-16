import { useState } from 'react';
import type { TaskCreateRequest, RecurrenceType, Urgency, TimeOfDay } from '../types';

interface AddTaskFormProps {
  onSubmit: (task: TaskCreateRequest) => void;
  onCancel: () => void;
}

const recurrenceTypes: { value: RecurrenceType; label: string }[] = [
  { value: 'daily', label: 'Dagelijks' },
  { value: 'weekly', label: 'Wekelijks' },
  { value: 'biweekly', label: 'Om de 2 weken' },
  { value: 'monthly', label: 'Maandelijks' },
  { value: 'quarterly', label: 'Per kwartaal' },
  { value: 'yearly', label: 'Jaarlijks' },
  { value: 'continuous', label: 'Doorlopend' },
];

const dayNames = ['Ma', 'Di', 'Wo', 'Do', 'Vr', 'Za', 'Zo'];

export function AddTaskForm({ onSubmit, onCancel }: AddTaskFormProps) {
  const [name, setName] = useState('');
  const [recurrenceType, setRecurrenceType] = useState<RecurrenceType>('weekly');
  const [interval, setInterval] = useState(1);
  const [selectedDays, setSelectedDays] = useState<number[]>([]);
  const [timeOfDay, setTimeOfDay] = useState<TimeOfDay | ''>('');
  const [urgency, setUrgency] = useState<Urgency | ''>('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;

    const task: TaskCreateRequest = {
      name: name.trim(),
      recurrence: {
        type: recurrenceType,
        interval,
        days: recurrenceType === 'weekly' && selectedDays.length > 0 ? selectedDays : null,
        time_of_day: timeOfDay || null,
      },
      urgency_label: urgency || null,
    };

    onSubmit(task);
  };

  const toggleDay = (day: number) => {
    setSelectedDays(prev =>
      prev.includes(day) ? prev.filter(d => d !== day) : [...prev, day].sort()
    );
  };

  return (
    <form onSubmit={handleSubmit} className="bg-white rounded-lg shadow-md p-6 space-y-4">
      <h2 className="text-xl font-semibold text-gray-800">Nieuwe taak</h2>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Naam</label>
        <input
          type="text"
          value={name}
          onChange={e => setName(e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          placeholder="Bijv. Stofzuigen"
          required
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Herhaling</label>
        <select
          value={recurrenceType}
          onChange={e => setRecurrenceType(e.target.value as RecurrenceType)}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          {recurrenceTypes.map(rt => (
            <option key={rt.value} value={rt.value}>{rt.label}</option>
          ))}
        </select>
      </div>

      {recurrenceType === 'weekly' && (
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Dagen</label>
          <div className="flex gap-2">
            {dayNames.map((day, index) => (
              <button
                key={index}
                type="button"
                onClick={() => toggleDay(index)}
                className={`px-3 py-1 rounded text-sm ${
                  selectedDays.includes(index)
                    ? 'bg-blue-500 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                {day}
              </button>
            ))}
          </div>
        </div>
      )}

      {['monthly', 'yearly'].includes(recurrenceType) && (
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Interval</label>
          <input
            type="number"
            min="1"
            value={interval}
            onChange={e => setInterval(parseInt(e.target.value) || 1)}
            className="w-24 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <span className="ml-2 text-gray-600">
            {recurrenceType === 'monthly' ? 'maand(en)' : 'jaar'}
          </span>
        </div>
      )}

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Tijd van de dag</label>
        <select
          value={timeOfDay}
          onChange={e => setTimeOfDay(e.target.value as TimeOfDay | '')}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="">Geen voorkeur</option>
          <option value="morning">Ochtend</option>
          <option value="evening">Avond</option>
        </select>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Urgentie (optioneel)</label>
        <select
          value={urgency}
          onChange={e => setUrgency(e.target.value as Urgency | '')}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="">Automatisch bepalen</option>
          <option value="high">Hoog</option>
          <option value="medium">Gemiddeld</option>
          <option value="low">Laag</option>
        </select>
      </div>

      <div className="flex gap-3 pt-2">
        <button
          type="submit"
          className="flex-1 px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600 transition-colors"
        >
          Toevoegen
        </button>
        <button
          type="button"
          onClick={onCancel}
          className="px-4 py-2 bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300 transition-colors"
        >
          Annuleren
        </button>
      </div>
    </form>
  );
}
