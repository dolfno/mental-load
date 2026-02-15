import { useState } from 'react';
import type { Member } from '../types';
import { api } from '../api';

const COLOR_PALETTE = [
  '#3B82F6', '#EF4444', '#10B981', '#F59E0B',
  '#8B5CF6', '#EC4899', '#06B6D4', '#F97316',
];

interface MemberSelectorProps {
  members: Member[];
  onAddMember: (name: string) => void;
  onDeleteMember: (id: number) => void;
  onMembersChanged?: () => void;
}

export function MemberSelector({ members, onAddMember, onDeleteMember, onMembersChanged }: MemberSelectorProps) {
  const [newName, setNewName] = useState('');
  const [isAdding, setIsAdding] = useState(false);
  const [editingColorId, setEditingColorId] = useState<number | null>(null);

  const handleAdd = (e: React.FormEvent) => {
    e.preventDefault();
    if (newName.trim()) {
      onAddMember(newName.trim());
      setNewName('');
      setIsAdding(false);
    }
  };

  const handleColorChange = async (memberId: number, color: string) => {
    try {
      await api.members.updateColor(memberId, color);
      setEditingColorId(null);
      onMembersChanged?.();
    } catch (err) {
      console.error('Failed to update color:', err);
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-4">
      <h3 className="font-semibold text-gray-800 mb-3">Huisgenoten</h3>

      <div className="flex flex-wrap gap-2 mb-3">
        {members.map(member => (
          <div key={member.id} className="relative">
            <div className="flex items-center gap-1.5 px-3 py-1 bg-gray-100 rounded-full text-sm">
              <button
                onClick={() => setEditingColorId(editingColorId === member.id ? null : member.id)}
                className="w-3 h-3 rounded-full border border-gray-300 flex-shrink-0"
                style={{ backgroundColor: member.color || '#D1D5DB' }}
                title="Kleur wijzigen"
              />
              <span>{member.name}</span>
              <button
                onClick={() => onDeleteMember(member.id)}
                className="ml-1 text-gray-400 hover:text-red-500"
                title="Verwijderen"
              >
                ×
              </button>
            </div>
            {editingColorId === member.id && (
              <div className="absolute top-full left-0 mt-1 bg-white rounded-lg shadow-lg border border-gray-200 p-2 z-10">
                <div className="grid grid-cols-4 gap-1">
                  {COLOR_PALETTE.map(color => (
                    <button
                      key={color}
                      onClick={() => handleColorChange(member.id, color)}
                      className={`w-6 h-6 rounded-full border-2 transition-transform hover:scale-110 ${
                        member.color === color ? 'border-gray-800' : 'border-transparent'
                      }`}
                      style={{ backgroundColor: color }}
                    />
                  ))}
                </div>
              </div>
            )}
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
