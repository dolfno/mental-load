import { useState, useEffect, useCallback, useRef } from 'react';
import { api } from '../api';
import type { Note } from '../types';

export function NotepadPage() {
  const [note, setNote] = useState<Note | null>(null);
  const [content, setContent] = useState('');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [lastSaved, setLastSaved] = useState<Date | null>(null);

  // Refs to track current values for save-on-unmount
  const contentRef = useRef(content);
  const noteRef = useRef(note);
  contentRef.current = content;
  noteRef.current = note;

  const saveNote = useCallback(async (contentToSave: string) => {
    setSaving(true);
    try {
      const updatedNote = await api.notes.update({ content: contentToSave });
      setNote(updatedNote);
      setLastSaved(new Date());
      return updatedNote;
    } catch (err) {
      console.error('Failed to save note:', err);
      return null;
    } finally {
      setSaving(false);
    }
  }, []);

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

  const hasUnsavedChanges = note !== null && content !== note.content;

  // Warn about unsaved changes when leaving the page (browser close/refresh)
  useEffect(() => {
    const handleBeforeUnload = (e: BeforeUnloadEvent) => {
      if (hasUnsavedChanges) {
        e.preventDefault();
      }
    };

    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => window.removeEventListener('beforeunload', handleBeforeUnload);
  }, [hasUnsavedChanges]);

  // Save on unmount (when navigating away within the app)
  useEffect(() => {
    return () => {
      const currentContent = contentRef.current;
      const currentNote = noteRef.current;
      if (currentNote && currentContent !== currentNote.content) {
        // Fire and forget - component is unmounting
        api.notes.update({ content: currentContent }).catch(console.error);
      }
    };
  }, []);

  // Auto-save with debounce
  useEffect(() => {
    if (loading || note === null) return;
    if (content === note.content) return;

    const timeoutId = setTimeout(() => {
      saveNote(content);
    }, 1000);

    return () => clearTimeout(timeoutId);
  }, [content, note, loading, saveNote]);

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
          <div className="flex items-center gap-3 text-sm">
            {hasUnsavedChanges && !saving && (
              <span className="text-yellow-600">Niet-opgeslagen wijzigingen</span>
            )}
            <span className="text-gray-500">
              {saving ? (
                'Opslaan...'
              ) : lastSaved ? (
                `Opgeslagen om ${formatLastSaved()}`
              ) : note?.updated_at ? (
                `Laatst bewerkt: ${new Date(note.updated_at).toLocaleString('nl-NL', {
                  day: 'numeric',
                  month: 'short',
                  hour: '2-digit',
                  minute: '2-digit',
                })}`
              ) : null}
            </span>
            <button
              onClick={loadNote}
              className="px-3 py-1 text-gray-600 hover:text-gray-800 hover:bg-gray-100 rounded-md transition-colors"
              title="Vernieuwen"
            >
              Vernieuwen
            </button>
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
