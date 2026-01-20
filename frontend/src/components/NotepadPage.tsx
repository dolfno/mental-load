import { useState, useEffect, useCallback } from 'react';
import { api } from '../api';
import type { Note } from '../types';

export function NotepadPage() {
  const [note, setNote] = useState<Note | null>(null);
  const [content, setContent] = useState('');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [lastSaved, setLastSaved] = useState<Date | null>(null);

  const loadNote = useCallback(async () => {
    try {
      const loadedNote = await api.notes.get();
      setNote(loadedNote);
      setContent(loadedNote.content);
    } catch (err) {
      console.error('Failed to load note:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadNote();
  }, [loadNote]);

  // Auto-save with debounce
  useEffect(() => {
    if (loading || note === null) return;
    if (content === note.content) return;

    const timeoutId = setTimeout(async () => {
      setSaving(true);
      try {
        const updatedNote = await api.notes.update({ content });
        setNote(updatedNote);
        setLastSaved(new Date());
      } catch (err) {
        console.error('Failed to save note:', err);
      } finally {
        setSaving(false);
      }
    }, 1000);

    return () => clearTimeout(timeoutId);
  }, [content, note, loading]);

  const formatLastSaved = () => {
    if (!lastSaved) return null;
    return lastSaved.toLocaleTimeString('nl-NL', {
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-gray-500">Laden...</div>
      </div>
    );
  }

  return (
    <main className="max-w-4xl mx-auto px-4 py-6">
      <div className="bg-white rounded-lg shadow-sm border border-gray-200">
        <div className="px-4 py-3 border-b border-gray-200 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-gray-800">Kladblok</h2>
          <div className="text-sm text-gray-500">
            {saving ? (
              <span>Opslaan...</span>
            ) : lastSaved ? (
              <span>Opgeslagen om {formatLastSaved()}</span>
            ) : note?.updated_at ? (
              <span>
                Laatst bewerkt:{' '}
                {new Date(note.updated_at).toLocaleString('nl-NL', {
                  day: 'numeric',
                  month: 'short',
                  hour: '2-digit',
                  minute: '2-digit',
                })}
              </span>
            ) : null}
          </div>
        </div>
        <div className="p-4">
          <textarea
            value={content}
            onChange={(e) => setContent(e.target.value)}
            placeholder="Schrijf hier notities, boodschappenlijstjes, ideeën..."
            className="w-full h-96 p-3 border border-gray-300 rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>
      </div>
    </main>
  );
}
