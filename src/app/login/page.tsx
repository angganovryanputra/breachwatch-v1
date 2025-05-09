
'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/context/auth-context';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useToast } from '@/hooks/use-toast';
import Link from 'next/link';
import { LogIn, Loader2, ShieldAlert } from 'lucide-react';
import { APP_NAME } from '@/lib/constants';

export default function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const { login, isLoading: authIsLoading } = useAuth(); // Get auth loading state
  const router = useRouter();
  const { toast } = useToast();

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);

    try {
      await login(email, password);
      toast({ title: 'Login Successful', description: 'Redirecting to dashboard...' });
      router.push('/dashboard');
    } catch (error) {
      console.error('Login failed:', error);
      toast({
        title: 'Login Failed',
        description: error instanceof Error ? error.message : 'Invalid credentials or server error.',
        variant: 'destructive',
      });
    } finally {
        setIsLoading(false);
    }
  };
  
  const combinedLoading = isLoading || authIsLoading;

  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-background p-4 sm:p-6 md:p-8">
      <Card className="w-full max-w-md rounded-xl bg-card shadow-2xl">
        <CardHeader className="space-y-1 text-center p-6">
           <div className="flex items-center justify-center gap-2 mb-3">
             <ShieldAlert className="h-8 w-8 text-accent" />
             <span className="text-3xl font-bold tracking-tight text-foreground">{APP_NAME}</span>
           </div>
          <CardTitle className="text-2xl font-semibold">Welcome Back</CardTitle>
          <CardDescription className="text-muted-foreground">Enter your credentials to access your account.</CardDescription>
        </CardHeader>
        <form onSubmit={handleLogin}>
          <CardContent className="space-y-6 p-6">
            <div className="space-y-2">
              <Label htmlFor="email" className="text-sm font-medium">Email Address</Label>
              <Input
                id="email"
                type="email"
                placeholder="e.g., user@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                disabled={combinedLoading}
                className="h-11 text-base"
              />
            </div>
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label htmlFor="password" className="text-sm font-medium">Password</Label>
              </div>
              <Input
                id="password"
                type="password"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                disabled={combinedLoading}
                className="h-11 text-base"
              />
            </div>
          </CardContent>
          <CardFooter className="flex flex-col gap-4 p-6">
            <Button type="submit" className="w-full h-11 text-base" disabled={combinedLoading}>
              {combinedLoading ? <Loader2 className="mr-2 h-5 w-5 animate-spin" /> : <LogIn className="mr-2 h-5 w-5" />}
              {combinedLoading ? 'Signing In...' : 'Sign In'}
            </Button>
             <p className="text-center text-sm text-muted-foreground">
              Don&apos;t have an account yet?{' '}
              <Link href="/signup" className="font-semibold text-accent hover:underline">
                Create one
              </Link>
            </p>
          </CardFooter>
        </form>
      </Card>
    </div>
  );
}
