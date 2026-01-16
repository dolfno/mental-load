import { NavLink } from 'react-router-dom';

export function Header() {
  const linkClass = ({ isActive }: { isActive: boolean }) =>
    `px-3 py-1 rounded-md text-sm transition-colors ${
      isActive
        ? 'bg-blue-100 text-blue-700'
        : 'text-gray-600 hover:bg-gray-100'
    }`;

  return (
    <header className="bg-white shadow-sm">
      <div className="max-w-7xl mx-auto px-4 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-800">Aivin</h1>
            <p className="text-gray-500 text-sm">Huishoudelijk taakbeheer</p>
          </div>
          <nav className="flex gap-2">
            <NavLink to="/" className={linkClass}>
              Dashboard
            </NavLink>
            <NavLink to="/beheer" className={linkClass}>
              Beheer
            </NavLink>
          </nav>
        </div>
      </div>
    </header>
  );
}
