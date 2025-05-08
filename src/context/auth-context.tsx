'use client';

import React, { createContext, useState, useContext, ReactNode, useEffect } from 'react';
import type { User } from '@/types';

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  signup: (email: string, password: string, name?: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Dummy user data for simulation
const DUMMY_USERS: User[] = [
  { id: 'user-1', email: 'user@example.com', name: 'Regular User', role: 'user' },
  { id: 'admin-1', email: 'admin@example.com', name: 'Admin User', role: 'admin' },
];

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true); // Start loading until check is done

  // Simulate checking auth status on initial load (e.g., from localStorage)
  useEffect(() => {
    const storedUser = localStorage.getItem('breachwatchUser');
    if (storedUser) {
      try {
        setUser(JSON.parse(storedUser));
      } catch (e) {
        console.error("Failed to parse stored user", e);
        localStorage.removeItem('breachwatchUser');
      }
    }
    setIsLoading(false);
  }, []);

  const login = async (email: string, password: string): Promise<void> => {
    setIsLoading(true);
    // Simulate API call delay
    await new Promise(resolve => setTimeout(resolve, 500));

    // Dummy login logic
    const foundUser = DUMMY_USERS.find(u => u.email === email);
    // In a real app, you'd verify the password hash here
    if (foundUser && password === 'password') { // Using 'password' for all dummy users
      setUser(foundUser);
      localStorage.setItem('breachwatchUser', JSON.stringify(foundUser));
      setIsLoading(false);
    } else {
      setIsLoading(false);
      throw new Error('Invalid email or password.');
    }
  };

  const signup = async (email: string, password: string, name?: string): Promise<void> => {
     setIsLoading(true);
    // Simulate API call delay
    await new Promise(resolve => setTimeout(resolve, 700));

    // Dummy signup logic (check if email exists)
    if (DUMMY_USERS.some(u => u.email === email)) {
        setIsLoading(false);
        throw new Error('Email already exists.');
    }
    // Normally, you'd create the user in the backend here.
    // For the dummy version, we won't add to DUMMY_USERS, just simulate success.
     console.log(`Dummy signup successful for: ${email}, Name: ${name || 'N/A'}`);
     setIsLoading(false);
     // Don't log the user in automatically after signup in this dummy version, require login.
  };

  const logout = () => {
    setUser(null);
    localStorage.removeItem('breachwatchUser');
    // Redirect to login might happen in the component using logout
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