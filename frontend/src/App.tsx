import { useState, useEffect, useCallback } from 'react';
import { BrowserRouter } from 'react-router-dom';
import { Routes, Route } from 'react-router';
import type { Member } from './types';
import { api, ApiError } from './api';
import type { MemberDeleteConflict } from './api';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { Header } from './components/Header';
import { Dashboard } from './components/Dashboard';
import { AdminPage } from './components/AdminPage';
import { NotepadPage } from './components/NotepadPage';
import { LoginPage } from './components/LoginPage';
import { RegisterPage } from './components/RegisterPage';
import { ProtectedRoute } from './components/ProtectedRoute';

function AuthenticatedApp() {
  const [members, setMembers] = useState<Member[]>([]);
  const [membersLoading, setMembersLoading] = useState(true);
  const { isAuthenticated } = useAuth();

  const loadMembers = useCallback(async () => {
    if (!isAuthenticated) return;
    try {
      const loadedMembers = await api.members.list();
      setMembers(loadedMembers);
    } catch (err) {
      console.error('Failed to load members:', err);
    }
  }, [isAuthenticated]);

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
      if (err instanceof ApiError && err.status === 409) {
        const conflict = err.data as MemberDeleteConflict;
        const parts: string[] = [];
        if (conflict.completion_count > 0) {
          parts.push(`${conflict.completion_count} voltooide ${conflict.completion_count === 1 ? 'taak' : 'taken'}`);
        }
        if (conflict.assignment_count > 0) {
          parts.push(`${conflict.assignment_count} toegewezen ${conflict.assignment_count === 1 ? 'taak' : 'taken'}`);
        }
        const message = `Dit gezinslid heeft ${parts.join(' en ')}. Wil je deze verwijderen en de geschiedenis anonimiseren?`;

        if (window.confirm(message)) {
          try {
            await api.members.delete(id, true);
            await loadMembers();
          } catch (forceErr) {
            console.error('Failed to force delete member:', forceErr);
          }
        }
      } else {
        console.error('Failed to delete member:', err);
      }
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
    <div className="min-h-screen bg-gray-50">
      <Header />
      <Routes>
        <Route path="/" element={<Dashboard members={members} />} />
        <Route path="/kladblok" element={<NotepadPage />} />
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
  );
}

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          <Route
            path="/*"
            element={
              <ProtectedRoute>
                <AuthenticatedApp />
              </ProtectedRoute>
            }
          />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
