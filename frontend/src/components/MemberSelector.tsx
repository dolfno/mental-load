import { useState } from 'react';
import type { Member } from '../types';

interface MemberSelectorProps {
  members: Member[];
  onAddMember: (name: string) => void;
  onDeleteMember: (id: number) => void;
}

export function MemberSelector({ members, onAddMember, onDeleteMember }: MemberSelectorProps) {
  const [newName, setNewName] = useState('');
  const [isAdding, setIsAdding] = useState(false);

  const handleAdd = (e: React.FormEvent) => {
    e.preventDefault();
    if (newName.trim()) {
      onAddMember(newName.trim());
      setNewName('');
      setIsAdding(false);
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-4">
      <h3 className="font-semibold text-gray-800 mb-3">Huisgenoten</h3>

      <div className="flex flex-wrap gap-2 mb-3">
        {members.map(member => (
          <div
            key={member.id}
            className="flex items-center gap-1 px-3 py-1 bg-gray-100 rounded-full text-sm"
          >
            <span>{member.name}</span>
            <button
              onClick={() => onDeleteMember(member.id)}
              className="ml-1 text-gray-400 hover:text-red-500"
              title="Verwijderen"
            >
              ×
            </button>
          </div>
        ))}
      </div>

      {isAdding ? (
        <form onSubmit={handleAdd} className="flex gap-2">
          <input
            type="text"
            value={newName}
            onChange={e => setNewName(e.target.value)}
            className="flex-1 px-3 py-1 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="Naam"
            autoFocus
          />
          <button
            type="submit"
            className="px-3 py-1 bg-blue-500 text-white rounded-md text-sm hover:bg-blue-600"
          >
            Toevoegen
          </button>
          <button
            type="button"
            onClick={() => setIsAdding(false)}
            className="px-3 py-1 bg-gray-200 text-gray-700 rounded-md text-sm hover:bg-gray-300"
          >
            Annuleren
          </button>
        </form>
      ) : (
        <button
          onClick={() => setIsAdding(true)}
          className="text-sm text-blue-500 hover:text-blue-600"
        >
          + Huisgenoot toevoegen
        </button>
      )}
    </div>
  );
}
