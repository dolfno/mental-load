import { useState, useEffect, useCallback } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import type { Member } from './types';
import { api } from './api';
import { Header } from './components/Header';
import { Dashboard } from './components/Dashboard';
import { AdminPage } from './components/AdminPage';

function App() {
  const [members, setMembers] = useState<Member[]>([]);
  const [membersLoading, setMembersLoading] = useState(true);

  const loadMembers = useCallback(async () => {
    try {
      const loadedMembers = await api.members.list();
      setMembers(loadedMembers);
    } catch (err) {
      console.error('Failed to load members:', err);
    }
  }, []);

  useEffect(() => {
    const init = async () => {
      await loadMembers();
      setMembersLoading(false);
    };
    init();
  }, [loadMembers]);

  const handleAddMember = async (name: string) => {
    try {
      await api.members.create(name);
      await loadMembers();
    } catch (err) {
      console.error('Failed to add member:', err);
    }
  };

  const handleDeleteMember = async (id: number) => {
    try {
      await api.members.delete(id);
      await loadMembers();
    } catch (err) {
      console.error('Failed to delete member:', err);
    }
  };

  if (membersLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-gray-500">Laden...</div>
      </div>
    );
  }

  return (
    <BrowserRouter>
      <div className="min-h-screen bg-gray-50">
        <Header />
        <Routes>
          <Route path="/" element={<Dashboard members={members} />} />
          <Route
            path="/beheer"
            element={
              <AdminPage
                members={members}
                onAddMember={handleAddMember}
                onDeleteMember={handleDeleteMember}
              />
            }
          />
        </Routes>
      </div>
    </BrowserRouter>
  );
}

export default App;
