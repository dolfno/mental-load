import { useState } from 'react';
import type { Task } from '../types';

interface TaskCardProps {
  task: Task;
  onComplete: (taskId: number) => void;
  onPostpone: (taskId: number, newDueDate: string) => void;
  onEdit: (task: Task) => void;
  onDelete: (taskId: number) => void;
}

const urgencyColors = {
  high: 'bg-red-100 border-red-400 text-red-800',
  medium: 'bg-yellow-100 border-yellow-400 text-yellow-800',
  low: 'bg-green-100 border-green-400 text-green-800',
};

const autocompleteColors = 'bg-gray-100 border-gray-400 text-gray-700';

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
    case 'eenmalig':
      text = 'Eenmalig';
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

function addDays(days: number): string {
  const date = new Date();
  date.setDate(date.getDate() + days);
  return date.toISOString().split('T')[0];
}

function addMonths(months: number): string {
  const date = new Date();
  date.setMonth(date.getMonth() + months);
  return date.toISOString().split('T')[0];
}

export function TaskCard({ task, onComplete, onPostpone, onEdit, onDelete }: TaskCardProps) {
  const [showPostponeMenu, setShowPostponeMenu] = useState(false);
  const [showOverflowMenu, setShowOverflowMenu] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [showCustomDate, setShowCustomDate] = useState(false);
  const [customDate, setCustomDate] = useState('');
  const [showDescription, setShowDescription] = useState(false);

  const handleComplete = () => {
    onComplete(task.id);
  };

  const handlePostpone = (newDate: string) => {
    onPostpone(task.id, newDate);
    setShowPostponeMenu(false);
    setShowCustomDate(false);
  };

  const handleDelete = () => {
    onDelete(task.id);
    setShowDeleteConfirm(false);
    setShowOverflowMenu(false);
  };

  const cardColors = task.autocomplete ? autocompleteColors : urgencyColors[task.calculated_urgency];

  return (
    <div data-testid="task-card" className={`border-l-4 rounded-lg p-4 shadow-sm ${cardColors} relative`}>
      <div className="flex justify-between items-start mb-2">
        <h3 className="font-semibold text-lg">{task.name}</h3>
        {task.autocomplete ? (
          <span className="px-2 py-1 rounded text-xs font-medium bg-gray-500 text-white">
            Auto
          </span>
        ) : (
          <span className={`px-2 py-1 rounded text-xs font-medium ${urgencyBadge[task.calculated_urgency]}`}>
            {task.calculated_urgency === 'high' ? 'Hoog' : task.calculated_urgency === 'medium' ? 'Gemiddeld' : 'Laag'}
          </span>
        )}
      </div>

      <div className="text-sm opacity-75 mb-3">
        <div>{formatRecurrence(task)}</div>
        {task.next_due && <div className="font-medium">{formatDueDate(task.next_due)}</div>}
        {task.assigned_to_name && (
          <div className="mt-1">
            <span className="inline-block px-2 py-0.5 bg-purple-500 text-white rounded text-xs font-medium">
              {task.assigned_to_name}
            </span>
          </div>
        )}
        {task.description && (
          <div className="mt-2">
            <button
              type="button"
              onClick={() => setShowDescription(!showDescription)}
              className="text-xs text-blue-600 hover:text-blue-800 flex items-center gap-1"
            >
              <span>{showDescription ? '▼' : '▶'}</span>
              <span>Beschrijving</span>
            </button>
            {showDescription && (
              <div className="mt-1 p-2 bg-white/50 rounded text-gray-700 whitespace-pre-wrap">
                {task.description}
              </div>
            )}
          </div>
        )}
      </div>

      <div className="flex gap-2 items-center">
        {/* Complete button - hidden for autocomplete tasks */}
        {!task.autocomplete && (
          <button
            onClick={handleComplete}
            className="px-3 py-1.5 bg-green-500 hover:bg-green-600 text-white rounded text-sm font-medium transition-colors flex items-center gap-1"
          >
            <span>✓</span> Voltooid
          </button>
        )}

        {/* Postpone button */}
        <div className="relative">
          <button
            onClick={() => {
              setShowPostponeMenu(!showPostponeMenu);
              setShowOverflowMenu(false);
            }}
            className="px-3 py-1.5 bg-blue-500 hover:bg-blue-600 text-white rounded text-sm font-medium transition-colors flex items-center gap-1"
          >
            <span>⏱</span> Uitstellen <span className="text-xs">▾</span>
          </button>

          {showPostponeMenu && (
            <div className="absolute left-0 top-full mt-1 bg-white rounded-lg shadow-lg border z-20 min-w-[160px]">
              {!showCustomDate ? (
                <>
                  <button
                    onClick={() => handlePostpone(addDays(1))}
                    className="block w-full text-left px-4 py-2 hover:bg-gray-100 text-sm text-gray-700"
                  >
                    Morgen
                  </button>
                  <button
                    onClick={() => handlePostpone(addDays(3))}
                    className="block w-full text-left px-4 py-2 hover:bg-gray-100 text-sm text-gray-700"
                  >
                    Over 3 dagen
                  </button>
                  <button
                    onClick={() => handlePostpone(addDays(7))}
                    className="block w-full text-left px-4 py-2 hover:bg-gray-100 text-sm text-gray-700"
                  >
                    Volgende week
                  </button>
                  <button
                    onClick={() => handlePostpone(addMonths(1))}
                    className="block w-full text-left px-4 py-2 hover:bg-gray-100 text-sm text-gray-700"
                  >
                    Volgende maand
                  </button>
                  <hr className="my-1" />
                  <button
                    onClick={() => setShowCustomDate(true)}
                    className="block w-full text-left px-4 py-2 hover:bg-gray-100 text-sm text-gray-700"
                  >
                    Kies datum...
                  </button>
                </>
              ) : (
                <div className="p-3">
                  <input
                    type="date"
                    value={customDate}
                    onChange={(e) => setCustomDate(e.target.value)}
                    className="w-full px-2 py-1 border rounded text-sm mb-2"
                    min={new Date().toISOString().split('T')[0]}
                  />
                  <div className="flex gap-2">
                    <button
                      onClick={() => customDate && handlePostpone(customDate)}
                      disabled={!customDate}
                      className="flex-1 px-2 py-1 bg-blue-500 text-white rounded text-sm disabled:opacity-50"
                    >
                      OK
                    </button>
                    <button
                      onClick={() => {
                        setShowCustomDate(false);
                        setCustomDate('');
                      }}
                      className="px-2 py-1 bg-gray-200 rounded text-sm"
                    >
                      Terug
                    </button>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Spacer */}
        <div className="flex-1" />

        {/* Overflow menu */}
        <div className="relative">
          <button
            onClick={() => {
              setShowOverflowMenu(!showOverflowMenu);
              setShowPostponeMenu(false);
            }}
            className="px-2 py-1.5 hover:bg-black/10 rounded text-lg transition-colors"
          >
            ⋮
          </button>

          {showOverflowMenu && (
            <div className="absolute right-0 top-full mt-1 bg-white rounded-lg shadow-lg border z-20 min-w-[140px]">
              <button
                onClick={() => {
                  onEdit(task);
                  setShowOverflowMenu(false);
                }}
                className="block w-full text-left px-4 py-2 hover:bg-gray-100 text-sm text-gray-700"
              >
                Bewerken
              </button>
              <button
                onClick={() => setShowDeleteConfirm(true)}
                className="block w-full text-left px-4 py-2 hover:bg-gray-100 text-sm text-red-600"
              >
                Verwijderen
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Delete confirmation overlay */}
      {showDeleteConfirm && (
        <div className="absolute inset-0 bg-white/95 rounded-lg flex flex-col items-center justify-center p-4 z-30">
          <p className="text-gray-800 mb-4 text-center">
            Weet je zeker dat je<br /><strong>{task.name}</strong><br />wilt verwijderen?
          </p>
          <div className="flex gap-2">
            <button
              onClick={handleDelete}
              className="px-4 py-2 bg-red-500 hover:bg-red-600 text-white rounded text-sm font-medium transition-colors"
            >
              Verwijderen
            </button>
            <button
              onClick={() => {
                setShowDeleteConfirm(false);
                setShowOverflowMenu(false);
              }}
              className="px-4 py-2 bg-gray-200 hover:bg-gray-300 text-gray-700 rounded text-sm font-medium transition-colors"
            >
              Annuleren
            </button>
          </div>
        </div>
      )}

      {/* Click outside handler */}
      {(showPostponeMenu || showOverflowMenu) && (
        <div
          className="fixed inset-0 z-10"
          onClick={() => {
            setShowPostponeMenu(false);
            setShowOverflowMenu(false);
            setShowCustomDate(false);
          }}
        />
      )}
    </div>
  );
}
