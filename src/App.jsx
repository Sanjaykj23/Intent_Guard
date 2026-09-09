import React, { useState, useEffect } from 'react';
import AuthScreen from './components/AuthScreen';
import LockScreen from './components/LockScreen';
import Home from './pages/Home';

/**
 * App Component — Root Application Routing & Security State Management
 */
export default function App() {
  const [authenticatedUser, setAuthenticatedUser] = useState(() => {
    const saved = localStorage.getItem('intentguard_user');
    return saved ? JSON.parse(saved) : null;
  });
  const [isAuthenticated, setIsAuthenticated] = useState(() => !!authenticatedUser);
  const [isLocked, setIsLocked] = useState(false);

  // Authentication Success Callback
  const handleAuthenticate = (userData) => {
    setAuthenticatedUser(userData);
    setIsAuthenticated(true);
    setIsLocked(false);
  };

  // Logout / Switch Account Action
  const handleLogout = () => {
    localStorage.removeItem('intentguard_user');
    setAuthenticatedUser(null);
    setIsAuthenticated(false);
    setIsLocked(false);
  };

  // Lock Session Action
  const handleLockSession = () => {
    setIsLocked(true);
  };

  // Unlock Request Action (Redirect to AuthScreen)
  const handleUnlockRequest = () => {
    handleLogout();
  };

  // 1. Initial Authentication View (Sign Up / Sign In)
  if (!isAuthenticated || !authenticatedUser) {
    return <AuthScreen onAuthenticate={handleAuthenticate} />;
  }

  // 2. Locked State View
  if (isLocked) {
    return <LockScreen onUnlockRequest={handleUnlockRequest} />;
  }

  // 3. Authenticated Intent Guard Dashboard
  return (
    <Home
      authenticatedUser={authenticatedUser}
      onLockSession={handleLockSession}
      onLogout={handleLogout}
    />
  );
}
