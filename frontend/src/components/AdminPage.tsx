import type { Member } from '../types';
import { MemberSelector } from './MemberSelector';

interface AdminPageProps {
  members: Member[];
  onAddMember: (name: string) => void;
  onDeleteMember: (id: number) => void;
}

export function AdminPage({ members, onAddMember, onDeleteMember }: AdminPageProps) {
  return (
    <main className="max-w-7xl mx-auto px-4 py-6 space-y-6">
      <h2 className="text-xl font-semibold text-gray-800">Beheer</h2>

      <MemberSelector
        members={members}
        onAddMember={onAddMember}
        onDeleteMember={onDeleteMember}
      />
    </main>
  );
}
