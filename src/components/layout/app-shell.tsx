'use client'; // Required because we use hooks like usePathname and useAuth

import type { ReactNode } from 'react';
import { useEffect } from 'react';
import Link from 'next/link';
import { useRouter, usePathname } from 'next/navigation'; // Corrected import
import {
  Sidebar,
  SidebarHeader,
  SidebarContent,
  SidebarMenu,
  SidebarMenuItem,
  SidebarMenuButton,
  SidebarTrigger,
  SidebarInset,
  SidebarFooter,
} from '@/components/ui/sidebar';
import { Button } from '@/components/ui/button';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuLabel, DropdownMenuSeparator, DropdownMenuTrigger } from '@/components/ui/dropdown-menu';
import { ShieldAlert, LogOut, UserCircle, Loader2, UserCog } from 'lucide-react'; // Added icons
import { APP_NAME, NAV_LINKS } from '@/lib/constants';
import { useAuth } from '@/context/auth-context'; // Import useAuth

interface AppShellProps {
  children: ReactNode;
}

export function AppShell({ children }: AppShellProps) {
  const pathname = usePathname();
  const router = useRouter();
  const { user, isAuthenticated, isLoading, logout } = useAuth();

  // Route Protection Logic
  useEffect(() => {
    // Don't run protection logic until auth state is determined
    if (isLoading) return;

    const publicPaths = ['/login', '/signup'];
    const isAdminRoute = pathname?.startsWith('/admin');
    const isAuthRoute = publicPaths.includes(pathname || '');

    // If user is not authenticated and trying to access a protected route
    if (!isAuthenticated && !isAuthRoute) {
      router.replace('/login');
    }
    // If user is authenticated and trying to access login/signup
    else if (isAuthenticated && isAuthRoute) {
      router.replace('/dashboard'); // Redirect logged-in users away from auth pages
    }
    // If user is not admin and trying to access an admin route
    else if (isAuthenticated && user?.role !== 'admin' && isAdminRoute) {
      router.replace('/dashboard'); // Redirect non-admins away from admin pages
    }
  }, [isAuthenticated, isLoading, pathname, router, user?.role]);


  // Determine which nav links to show based on role
  const visibleNavLinks = NAV_LINKS.filter(link => {
    if (link.adminOnly) {
      return user?.role === 'admin';
    }
    return true;
  });

  // Show loading state or nothing if loading and not authenticated yet on protected routes
  if (isLoading && !['/login', '/signup'].includes(pathname || '')) {
    return (
      <div className="flex h-screen items-center justify-center bg-background">
        <Loader2 className="h-8 w-8 animate-spin text-accent" />
      </div>
    );
  }

  // If trying to access protected routes while not authenticated (after loading), render null or redirect
  if (!isLoading && !isAuthenticated && !['/login', '/signup'].includes(pathname || '')) {
    return null; // Or a specific "Unauthorized" component
  }
  // If trying to access admin routes while not admin (after loading), render null or redirect
  if (!isLoading && isAuthenticated && user?.role !== 'admin' && pathname?.startsWith('/admin')) {
       return null; // Or a specific "Forbidden" component
  }


  // Render AppShell only if authenticated or on public paths
  if (isAuthenticated || ['/login', '/signup'].includes(pathname || '')) {
      // Don't render shell for login/signup pages
      if (['/login', '/signup'].includes(pathname || '')) {
        return <>{children}</>; // Render only the page content
      }
    
    return (
      <div className="flex min-h-screen w-full">
        <Sidebar collapsible="icon" variant="sidebar" side="left">
          <SidebarHeader className="p-4">
            <Link href="/" className="flex items-center gap-2 text-xl font-semibold text-primary-foreground">
              <ShieldAlert className="h-7 w-7 text-accent" />
              <span>{APP_NAME}</span>
            </Link>
          </SidebarHeader>
          <SidebarContent className="p-2">
            <SidebarMenu>
              {visibleNavLinks.map((item) => (
                <SidebarMenuItem key={item.title}>
                  <Link href={item.href} legacyBehavior passHref>
                    <SidebarMenuButton
                      asChild
                      isActive={pathname === item.href}
                      tooltip={item.title}
                      disabled={item.disabled}
                    >
                      <a>
                        <item.icon />
                        <span>{item.title}</span>
                      </a>
                    </SidebarMenuButton>
                  </Link>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarContent>
          <SidebarFooter className="p-4 mt-auto border-t border-sidebar-border">
             <DropdownMenu>
                <DropdownMenuTrigger asChild>
                   <Button variant="ghost" className="w-full justify-start px-2 py-1 h-auto text-left text-sidebar-foreground hover:bg-sidebar-accent">
                      <Avatar className="h-7 w-7 mr-2">
                          <AvatarImage src={user?.avatarUrl || undefined} alt={user?.name || user?.email || 'User'}/>
                          <AvatarFallback className="bg-sidebar-accent text-sidebar-accent-foreground text-xs">
                              {user?.name ? user.name[0].toUpperCase() : user?.email ? user.email[0].toUpperCase() : '?'}
                          </AvatarFallback>
                      </Avatar>
                      <div className="flex-1 truncate group-data-[collapsible=icon]:hidden">
                          <p className="text-sm font-medium">{user?.name || 'User Profile'}</p>
                          <p className="text-xs text-muted-foreground truncate">{user?.email}</p>
                      </div>
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent side="right" align="start" className="w-56">
                   <DropdownMenuLabel className="font-normal">
                      <div className="flex flex-col space-y-1">
                          <p className="text-sm font-medium leading-none">{user?.name || 'User'}</p>
                          <p className="text-xs leading-none text-muted-foreground">{user?.email}</p>
                      </div>
                   </DropdownMenuLabel>
                  <DropdownMenuSeparator />
                  {/* Add Profile Link if profile page exists */}
                  {/* <DropdownMenuItem asChild><Link href="/profile">Profile</Link></DropdownMenuItem> */}
                  <DropdownMenuItem onClick={logout}>
                    <LogOut className="mr-2 h-4 w-4" />
                    <span>Log out</span>
                  </DropdownMenuItem>
                </DropdownMenuContent>
             </DropdownMenu>
          </SidebarFooter>
        </Sidebar>

        <SidebarInset className="flex flex-col">
          <header className="sticky top-0 z-10 flex h-14 items-center justify-between border-b bg-background/80 px-4 backdrop-blur-sm lg:px-6">
            <div className="flex items-center gap-2">
              <SidebarTrigger className="md:hidden" />
              <h1 className="text-xl font-semibold">
                {NAV_LINKS.find(link => pathname?.startsWith(link.href))?.title || APP_NAME}
              </h1>
            </div>
            {/* Header actions could go here */}
          </header>
          <main className="flex-1 overflow-y-auto p-4 lg:p-6">
            {children}
          </main>
        </SidebarInset>
      </div>
    );
  }
  
  // Fallback if none of the conditions match (should ideally not happen)
  return null;
}