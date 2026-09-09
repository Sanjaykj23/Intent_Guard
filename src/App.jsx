import React, { useState } from 'react';
import AuthScreen from './components/AuthScreen';
import LockScreen from './components/LockScreen';
import Home from './pages/Home';

/**
 * App Component — Root Application Routing & Security State Management
 */
export default function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLocked, setIsLocked] = useState(false);
  const [authenticatedUser, setAuthenticatedUser] = useState(null);

  // Authentication Success Callback
  const handleAuthenticate = (userData) => {
    setAuthenticatedUser(userData);
    setIsAuthenticated(true);
    setIsLocked(false);
  };

  // Lock Session Action
  const handleLockSession = () => {
    setIsLocked(true);
  };

  // Unlock Request Action (Redirect to AuthScreen)
  const handleUnlockRequest = () => {
    setIsLocked(false);
    setIsAuthenticated(false);
  };

  // 1. Initial Authentication View
  if (!isAuthenticated) {
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
    />
  );
}
