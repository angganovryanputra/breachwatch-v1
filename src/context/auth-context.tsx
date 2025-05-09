
'use client';

import React, { createContext, useState, useContext, ReactNode, useEffect, useCallback } from 'react';
import type { User, LoginPayload, RegisterPayload, AuthTokenResponse } from '@/types';
import { loginUser, registerUser, getCurrentUser as fetchCurrentUserFromApi } from '@/services/breachwatch-api';
import { useRouter } from 'next/navigation'; // Import useRouter for redirects

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  signup: (email: string, password: string, name?: string) => Promise<User>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const router = useRouter();

  const storeToken = (token: string) => {
    if (typeof window !== 'undefined') {
      localStorage.setItem('breachwatchAuthToken', token);
    }
  };

  const removeToken = () => {
    if (typeof window !== 'undefined') {
      localStorage.removeItem('breachwatchAuthToken');
    }
  };

  const fetchAndSetUser = useCallback(async () => {
    const token = typeof window !== 'undefined' ? localStorage.getItem('breachwatchAuthToken') : null;
    if (token) {
      try {
        const currentUser = await fetchCurrentUserFromApi();
        if (currentUser) {
          setUser(currentUser);
        } else {
          // Token might be invalid or expired
          removeToken();
          setUser(null);
        }
      } catch (error) {
        console.error("Failed to fetch current user:", error);
        removeToken(); // Clear token if fetching user fails
        setUser(null);
      }
    }
    setIsLoading(false);
  }, []);


  useEffect(() => {
    fetchAndSetUser();
  }, [fetchAndSetUser]);

  const login = async (email: string, password: string): Promise<void> => {
    setIsLoading(true);
    try {
      const payload: LoginPayload = { email, password };
      const response: AuthTokenResponse = await loginUser(payload);
      if (response.access_token) {
        storeToken(response.access_token);
        // Fetch user details after successful login
        const currentUser = await fetchCurrentUserFromApi();
        setUser(currentUser);
      } else {
        throw new Error('Login failed: No access token received.');
      }
    } catch (error) {
        removeToken(); // Ensure token is cleared on login failure
        setUser(null);
        setIsLoading(false); // Set loading to false on error
        throw error; // Re-throw error to be caught by calling component
    } finally {
       // Only set loading to false if no error was thrown and login was successful
       // If an error was thrown, it's already set to false in the catch block
       if (user) setIsLoading(false);
    }
  };

  const signup = async (email: string, password: string, name?: string): Promise<User> => {
    setIsLoading(true);
    try {
      const payload: RegisterPayload = { email, password, full_name: name };
      const newUser = await registerUser(payload);
      // Do not automatically log in user after signup, they should login explicitly
      setIsLoading(false);
      return newUser;
    } catch (error) {
      setIsLoading(false);
      throw error;
    }
  };

  const logout = () => {
    setUser(null);
    removeToken();
    // Redirect to login page handled by AppShell or individual components
    router.push('/login'); // Explicit redirect on logout
  };

  return (
    <AuthContext.Provider value={{ user, isAuthenticated: !!user, isLoading, login, signup, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
