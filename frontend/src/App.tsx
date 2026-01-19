import { useState, useEffect, useCallback } from 'react';
import { BrowserRouter } from 'react-router-dom';
import { Routes, Route } from 'react-router';
import type { Member } from './types';
import { api } from './api';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { Header } from './components/Header';
import { Dashboard } from './components/Dashboard';
import { AdminPage } from './components/AdminPage';
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
