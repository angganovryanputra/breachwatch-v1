
'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { AppShell } from '@/components/layout/app-shell';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuLabel, DropdownMenuSeparator, DropdownMenuRadioGroup, DropdownMenuRadioItem, DropdownMenuTrigger } from '@/components/ui/dropdown-menu';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import { Users, MoreHorizontal, ShieldCheck, UserCog, UserX, UserCheck, Trash2, Ban, Loader2 } from 'lucide-react';
import type { User, UserRole } from '@/types';
import { useToast } from "@/hooks/use-toast";
import { useAuth } from '@/context/auth-context'; // Import useAuth
import { getUsers, updateUserStatus, updateUserRole, deleteUser } from '@/services/breachwatch-api'; // Import user management API functions
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";

export default function UserManagementPage() {
  const [users, setUsers] = useState<User[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isUpdating, setIsUpdating] = useState<Record<string, boolean>>({}); // Track loading state per user action
  const { toast } = useToast();
  const { user: loggedInUser } = useAuth(); // Get logged-in user info for checks

  const fetchUsers = useCallback(async () => {
    setIsLoading(true);
    try {
      const fetchedUsers = await getUsers();
      setUsers(fetchedUsers);
    } catch (error) {
      console.error("Failed to fetch users:", error);
      toast({
        title: "Error Fetching Users",
        description: error instanceof Error ? error.message : "Could not load user data.",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  }, [toast]);

  useEffect(() => {
    // Ensure only admins can access this page (handled by AppShell, but double-check)
    if (loggedInUser?.role !== 'admin') {
      // Redirect logic is in AppShell, can add fallback here if needed
      return;
    }
    fetchUsers();
  }, [loggedInUser, fetchUsers]);

  const handleAction = async (userId: string, action: 'enable' | 'disable' | 'delete' | 'changeRole', payload?: any) => {
     if (userId === loggedInUser?.id && (action === 'disable' || action === 'delete' || (action === 'changeRole' && payload !== 'admin'))) {
      toast({ title: "Action Not Allowed", description: "Administrators cannot disable, delete, or demote their own account.", variant: "destructive" });
      return;
    }

    setIsUpdating(prev => ({ ...prev, [userId]: true }));
    let successMessage = "";
    let actionFunc: Promise<any>;

    switch (action) {
      case 'enable':
        actionFunc = updateUserStatus(userId, { is_active: true });
        successMessage = `User ${userId} enabled successfully.`;
        break;
      case 'disable':
        actionFunc = updateUserStatus(userId, { is_active: false });
        successMessage = `User ${userId} disabled successfully.`;
        break;
      case 'delete':
        actionFunc = deleteUser(userId);
        successMessage = `User ${userId} deleted successfully.`;
        break;
       case 'changeRole':
         actionFunc = updateUserRole(userId, { role: payload as UserRole });
         successMessage = `User ${userId}'s role updated to ${payload}.`;
         break;
      default:
        setIsUpdating(prev => ({ ...prev, [userId]: false }));
        return; // Should not happen
    }

    try {
      await actionFunc;
      toast({ title: "Success", description: successMessage });
      // Refetch users or update state optimistically
      if (action === 'delete') {
        setUsers(prevUsers => prevUsers.filter(user => user.id !== userId));
      } else {
        fetchUsers(); // Refetch for role/status changes
      }
    } catch (error) {
      console.error(`Failed to ${action} user ${userId}:`, error);
      toast({
        title: `Error ${action.charAt(0).toUpperCase() + action.slice(1)} User`,
        description: error instanceof Error ? error.message : `Could not perform action on user ${userId}.`,
        variant: "destructive",
      });
    } finally {
      setIsUpdating(prev => ({ ...prev, [userId]: false }));
    }
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
                View and manage user roles and statuses within the application.
              </CardDescription>
            </div>
            {/* Add Button for inviting/adding new users could go here */}
          </div>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="text-center py-10 flex items-center justify-center">
              <Loader2 className="h-6 w-6 mr-2 animate-spin"/> Loading users...
            </div>
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
                    <TableHead className="w-[80px]"></TableHead>{/* Avatar */}
                    <TableHead>Name</TableHead>
                    <TableHead>Email</TableHead>
                    <TableHead>Role</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead className="text-right w-[100px]">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {users.map((user) => (
                    <TableRow key={user.id} className={`hover:bg-muted/50 ${!user.is_active ? 'opacity-60' : ''}`}>
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
                      <TableCell>
                         <Badge variant={user.is_active ? 'default' : 'outline'} className="capitalize flex items-center gap-1 w-fit">
                           {user.is_active ? <UserCheck className="h-3.5 w-3.5 text-green-500" /> : <UserX className="h-3.5 w-3.5 text-red-500"/>}
                           {user.is_active ? 'Active' : 'Disabled'}
                         </Badge>
                      </TableCell>
                      <TableCell className="text-right">
                        {isUpdating[user.id] ? (
                            <Loader2 className="h-4 w-4 animate-spin mx-auto"/>
                        ) : (
                        <DropdownMenu>
                          <TooltipProvider>
                            <Tooltip>
                              <TooltipTrigger asChild>
                                <DropdownMenuTrigger asChild>
                                  <Button variant="ghost" size="icon" disabled={isUpdating[user.id]}>
                                    <MoreHorizontal className="h-4 w-4" />
                                    <span className="sr-only">User Actions</span>
                                  </Button>
                                </DropdownMenuTrigger>
                              </TooltipTrigger>
                              <TooltipContent><p>Actions</p></TooltipContent>
                            </Tooltip>
                          </TooltipProvider>
                          <DropdownMenuContent align="end">
                            <DropdownMenuLabel>Manage User</DropdownMenuLabel>
                            <DropdownMenuSeparator />
                            {/* Change Role */}
                             <DropdownMenuLabel className="text-xs px-2 pt-2">Change Role</DropdownMenuLabel>
                             <DropdownMenuRadioGroup 
                                value={user.role} 
                                onValueChange={(newRole) => handleAction(user.id, 'changeRole', newRole as UserRole)}
                                // Disable changing own role if admin
                                disabled={user.id === loggedInUser?.id && user.role === 'admin'} 
                            >
                                <DropdownMenuRadioItem value="user">User</DropdownMenuRadioItem>
                                <DropdownMenuRadioItem value="admin">Admin</DropdownMenuRadioItem>
                            </DropdownMenuRadioGroup>
                            
                            <DropdownMenuSeparator />
                            {/* Enable/Disable User */}
                            {user.is_active ? (
                              <DropdownMenuItem 
                                onClick={() => handleAction(user.id, 'disable')} 
                                disabled={user.id === loggedInUser?.id} // Prevent disabling self
                                className="text-orange-600 focus:bg-orange-100 focus:text-orange-700"
                              >
                                <Ban className="mr-2 h-4 w-4" /> Disable User
                              </DropdownMenuItem>
                            ) : (
                              <DropdownMenuItem onClick={() => handleAction(user.id, 'enable')} className="text-green-600 focus:bg-green-100 focus:text-green-700">
                                <UserCheck className="mr-2 h-4 w-4" /> Enable User
                              </DropdownMenuItem>
                            )}
                            
                            {/* Delete User */}
                             <DropdownMenuSeparator />
                             <AlertDialog>
                                <AlertDialogTrigger asChild>
                                    <DropdownMenuItem 
                                        onSelect={(e) => e.preventDefault()} // Prevent closing dropdown
                                        disabled={user.id === loggedInUser?.id} // Prevent deleting self
                                        className="text-destructive focus:bg-destructive/10 focus:text-destructive"
                                    >
                                        <Trash2 className="mr-2 h-4 w-4" /> Delete User
                                    </DropdownMenuItem>
                                </AlertDialogTrigger>
                                <AlertDialogContent>
                                    <AlertDialogHeader>
                                    <AlertDialogTitle>Confirm Deletion</AlertDialogTitle>
                                    <AlertDialogDescription>
                                        Are you sure you want to permanently delete user {user.email}? This action cannot be undone.
                                    </AlertDialogDescription>
                                    </AlertDialogHeader>
                                    <AlertDialogFooter>
                                    <AlertDialogCancel>Cancel</AlertDialogCancel>
                                    <AlertDialogAction onClick={() => handleAction(user.id, 'delete')} className="bg-destructive hover:bg-destructive/90">
                                        Delete User
                                    </AlertDialogAction>
                                    </AlertDialogFooter>
                                </AlertDialogContent>
                            </AlertDialog>

                          </DropdownMenuContent>
                        </DropdownMenu>
                        )}
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
