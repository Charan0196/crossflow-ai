import { useState } from 'react';
import { useAuthStore } from '../stores/authStore';
import { Eye, EyeOff, ArrowRight } from 'lucide-react';

const Logo = () => (
  <svg width="48" height="48" viewBox="0 0 32 32" fill="none">
    <circle cx="16" cy="16" r="14" stroke="#2dd4bf" strokeWidth="2" fill="none"/>
    <circle cx="16" cy="16" r="6" fill="#2dd4bf"/>
    <circle cx="16" cy="6" r="3" fill="#2dd4bf"/>
    <circle cx="16" cy="26" r="3" fill="#2dd4bf"/>
    <circle cx="6" cy="16" r="3" fill="#2dd4bf"/>
    <circle cx="26" cy="16" r="3" fill="#2dd4bf"/>
  </svg>
);

const LoginPage = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const { login } = useAuthStore();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);
    try {
      const success = await login(username, password);
      if (!success) setError('Invalid credentials. Try demo/demo123');
    } catch {
      setError('Login failed. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4 bg-[#0d1117]">
      <div className="w-full max-w-md">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="flex items-center justify-center mb-4">
            <Logo />
          </div>
          <h1 className="text-2xl font-bold text-white">
            CROSSFLOW <span className="text-[#2dd4bf]">AI</span>
          </h1>
          <p className="mt-2 text-gray-500">Cross-Chain DeFi Intelligence</p>
        </div>

        {/* Login Card */}
        <div className="rounded-2xl p-6 bg-[#1a1f2e] border border-[#2a3441]">
          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label className="block text-sm font-medium mb-2 text-gray-400">Username</label>
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="Enter username"
                className="w-full px-4 py-3 rounded-xl bg-[#0d1117] border border-[#2a3441] text-white placeholder-gray-600 focus:outline-none focus:border-[#2dd4bf] transition-colors"
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-2 text-gray-400">Password</label>
              <div className="relative">
                <input
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Enter password"
                  className="w-full px-4 py-3 rounded-xl bg-[#0d1117] border border-[#2a3441] text-white placeholder-gray-600 focus:outline-none focus:border-[#2dd4bf] transition-colors pr-12"
                />
                <button type="button" onClick={() => setShowPassword(!showPassword)} className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-300">
                  {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                </button>
              </div>
            </div>

            {error && (
              <div className="p-3 rounded-xl bg-red-500/10 border border-red-500/30 text-red-400 text-sm">
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={isLoading}
              className="w-full py-3 rounded-xl bg-[#2dd4bf] text-black font-semibold flex items-center justify-center gap-2 hover:bg-[#5eead4] transition-colors disabled:opacity-50"
            >
              {isLoading ? 'Signing in...' : 'Sign In'} <ArrowRight size={16} />
            </button>
          </form>

          <div className="mt-6 pt-6 text-center border-t border-[#2a3441]">
            <p className="text-sm text-gray-500">
              Demo: <span className="text-[#2dd4bf]">demo / demo123</span>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;
