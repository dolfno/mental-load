import { NavLink, useNavigate } from 'react-router';
import { useAuth } from '../contexts/AuthContext';

export function Header() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const linkClass = ({ isActive }: { isActive: boolean }) =>
    `px-3 py-1 rounded-md text-sm transition-colors ${
      isActive
        ? 'bg-blue-100 text-blue-700'
        : 'text-gray-600 hover:bg-gray-100'
    }`;

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <header className="bg-white shadow-sm">
      <div className="max-w-7xl mx-auto px-4 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-800">Aivin</h1>
            <p className="text-gray-500 text-sm">Huishoudelijk taakbeheer</p>
          </div>
          <div className="flex items-center gap-4">
            <nav className="flex gap-2">
              <NavLink to="/" className={linkClass}>
                Dashboard
              </NavLink>
              <NavLink to="/kladblok" className={linkClass}>
                Kladblok
              </NavLink>
              <NavLink to="/beheer" className={linkClass}>
                Beheer
              </NavLink>
            </nav>
            <div className="flex items-center gap-3 pl-4 border-l border-gray-200">
              <span className="text-sm text-gray-600">{user?.name}</span>
              <button
                onClick={handleLogout}
                className="px-3 py-1 text-sm text-gray-600 hover:text-gray-800 hover:bg-gray-100 rounded-md transition-colors"
              >
                Uitloggen
              </button>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}
