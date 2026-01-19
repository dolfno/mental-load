import { Link } from 'react-router';

export function RegisterPage() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div>
          <h1 className="text-center text-3xl font-bold text-gray-800">Aivin</h1>
          <p className="mt-1 text-center text-sm text-gray-500">Huishoudelijk taakbeheer</p>
          <h2 className="mt-6 text-center text-xl font-semibold text-gray-900">
            Registreren
          </h2>
        </div>
        <div className="mt-8 space-y-6">
          <div className="rounded-md bg-amber-50 p-4">
            <div className="text-sm text-amber-700">
              Registratie is uitgeschakeld. Neem contact op met de beheerder.
            </div>
          </div>
          <div className="text-center">
            <Link to="/login" className="font-medium text-blue-600 hover:text-blue-500">
              Terug naar inloggen
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
