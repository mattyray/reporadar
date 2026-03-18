import { Outlet, Link } from 'react-router-dom';

export default function AnonLayout() {
  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-gray-800">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-4">
              <Link to="/" className="text-white font-bold text-xl">
                RepoRadar
              </Link>
              <div className="flex gap-1">
                <span className="px-3 py-2 rounded-md text-sm font-medium bg-gray-900 text-white">
                  Jobs
                </span>
              </div>
            </div>
            <Link
              to="/login"
              className="bg-indigo-600 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-indigo-700"
            >
              Sign up free
            </Link>
          </div>
        </div>
      </nav>
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Outlet />
      </main>
    </div>
  );
}
