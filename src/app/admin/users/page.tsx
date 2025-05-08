'use client';

import React, { useState, useEffect } from 'react';
import { AppShell } from '@/components/layout/app-shell';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuLabel, DropdownMenuSeparator, DropdownMenuRadioGroup, DropdownMenuRadioItem } from '@/components/ui/dropdown-menu';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import { Users, MoreHorizontal, ShieldCheck, UserCog } from 'lucide-react';
import type { User, UserRole } from '@/types';
import { useToast } from "@/hooks/use-toast";
// import { useAuth } from '@/context/auth-context'; // Can be used for logged-in user context if needed

// Dummy user data for demonstration
const DUMMY_USERS: User[] = [
  { id: 'user-1', email: 'user@example.com', name: 'Regular User', role: 'user', avatarUrl: 'https://picsum.photos/id/101/50/50' },
  { id: 'admin-1', email: 'admin@example.com', name: 'Admin User', role: 'admin', avatarUrl: 'https://picsum.photos/id/102/50/50' },
  { id: 'user-2', email: 'another@example.com', name: 'Another User', role: 'user', avatarUrl: 'https://picsum.photos/id/103/50/50' },
  { id: 'user-3', email: 'test@test.com', name: null, role: 'user' },
];

export default function UserManagementPage() {
  const [users, setUsers] = useState<User[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const { toast } = useToast();
  // const { user: loggedInUser } = useAuth(); // Get logged-in user info if needed for checks

  useEffect(() => {
    // Simulate fetching users
    setIsLoading(true);
    setTimeout(() => {
      setUsers(DUMMY_USERS);
      setIsLoading(false);
    }, 500); // Simulate network delay
  }, []);

  const handleRoleChange = (userId: string, newRole: UserRole) => {
    // Simulate updating user role (in a real app, call API here)
    console.log(`Attempting to change role for user ${userId} to ${newRole}`);
    
    // Optimistic UI update (remove in real app, rely on API response)
    setUsers(prevUsers =>
      prevUsers.map(user =>
        user.id === userId ? { ...user, role: newRole } : user
      )
    );

    toast({
      title: "Role Change Simulated",
      description: `User ${userId}'s role updated to ${newRole} (frontend simulation).`,
    });
    // In real app:
    // try {
    //   await updateUserRoleAPI(userId, newRole); // API call
    //   toast({ title: "Role Updated", description: `User ${userId}'s role changed to ${newRole}.` });
    //   // Optionally refetch users or update state based on successful response
    // } catch (error) {
    //   toast({ title: "Error Updating Role", description: "Could not update user role.", variant: "destructive" });
    //   // Revert optimistic update if needed
    //   setUsers(DUMMY_USERS); 
    // }
  };

  return (
    <AppShell>
      <Card className="shadow-xl">
        <CardHeader>
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
            <div>
              <CardTitle className="text-2xl flex items-center">
                <Users className="h-7 w-7 mr-2 text-accent" />
                User Management
              </CardTitle>
              <CardDescription>
                View and manage user roles within the application.
              </CardDescription>
            </div>
            {/* Add Button for inviting/adding new users could go here */}
          </div>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="text-center py-10">Loading users...</div>
          ) : users.length === 0 ? (
            <div className="text-center py-10 min-h-[300px] flex flex-col justify-center items-center">
              <Users className="mx-auto h-16 w-16 text-muted-foreground mb-4" />
              <p className="text-xl font-semibold">No Users Found.</p>
              {/* Add invite/add user button here */}
            </div>
          ) : (
            <div className="overflow-x-auto rounded-md border">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-[80px]"></TableHead> {/* Avatar */}
                    <TableHead>Name</TableHead>
                    <TableHead>Email</TableHead>
                    <TableHead>Role</TableHead>
                    <TableHead className="text-right w-[100px]">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {users.map((user) => (
                    <TableRow key={user.id} className="hover:bg-muted/50">
                      <TableCell>
                        <Avatar className="h-9 w-9">
                          <AvatarImage src={user.avatarUrl || undefined} alt={user.name || user.email} data-ai-hint="person avatar" />
                          <AvatarFallback className="bg-muted text-muted-foreground text-xs">
                            {user.name ? user.name.split(' ').map(n => n[0]).join('') : user.email[0].toUpperCase()}
                          </AvatarFallback>
                        </Avatar>
                      </TableCell>
                      <TableCell className="font-medium">{user.name || <span className="text-muted-foreground italic">No Name</span>}</TableCell>
                      <TableCell>{user.email}</TableCell>
                      <TableCell>
                         <Badge variant={user.role === 'admin' ? 'destructive' : 'secondary'} className="capitalize flex items-center gap-1 w-fit">
                           {user.role === 'admin' ? <ShieldCheck className="h-3.5 w-3.5" /> : <UserCog className="h-3.5 w-3.5"/>}
                           {user.role}
                         </Badge>
                      </TableCell>
                      <TableCell className="text-right">
                        <DropdownMenu>
                          <TooltipProvider>
                            <Tooltip>
                              <TooltipTrigger asChild>
                                <DropdownMenuTrigger asChild>
                                  <Button variant="ghost" size="icon">
                                    <MoreHorizontal className="h-4 w-4" />
                                    <span className="sr-only">User Actions</span>
                                  </Button>
                                </DropdownMenuTrigger>
                              </TooltipTrigger>
                              <TooltipContent><p>Actions</p></TooltipContent>
                            </Tooltip>
                          </TooltipProvider>
                          <DropdownMenuContent align="end">
                            <DropdownMenuLabel>Change Role</DropdownMenuLabel>
                            <DropdownMenuSeparator />
                            <DropdownMenuRadioGroup value={user.role} onValueChange={(newRole) => handleRoleChange(user.id, newRole as UserRole)}>
                              <DropdownMenuRadioItem value="user">User</DropdownMenuRadioItem>
                              <DropdownMenuRadioItem value="admin">Admin</DropdownMenuRadioItem>
                            </DropdownMenuRadioGroup>
                             {/* Add other actions like "Disable User", "Delete User" here */}
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
          {/* Add pagination if needed */}
        </CardContent>
      </Card>
    </AppShell>
  );
}