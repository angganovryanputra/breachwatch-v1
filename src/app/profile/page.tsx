
'use client';

import { useState } from 'react';
import { AppShell } from '@/components/layout/app-shell';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useToast } from '@/hooks/use-toast';
import { Save, Lock, UserCircle, Loader2, ShieldQuestion } from 'lucide-react';
import { useAuth } from '@/context/auth-context';
import { changePassword } from '@/services/breachwatch-api'; // Assuming API function exists
import { useForm, SubmitHandler } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';

// Zod schema for password change validation
const passwordChangeSchema = z.object({
  currentPassword: z.string().min(1, "Current password is required"),
  newPassword: z.string().min(8, "New password must be at least 8 characters long"),
  confirmPassword: z.string(),
}).refine((data) => data.newPassword === data.confirmPassword, {
  message: "New passwords don't match",
  path: ["confirmPassword"], // Set error on confirm password field
});

type PasswordChangeFormData = z.infer<typeof passwordChangeSchema>;

export default function ProfilePage() {
  const { user, isLoading: isAuthLoading } = useAuth();
  const [isSaving, setIsSaving] = useState(false);
  const { toast } = useToast();
  
  const { register, handleSubmit, formState: { errors }, reset } = useForm<PasswordChangeFormData>({
    resolver: zodResolver(passwordChangeSchema),
  });

  const handlePasswordChange: SubmitHandler<PasswordChangeFormData> = async (data) => {
    if (!user?.id) {
      toast({ title: "Error", description: "User not identified.", variant: "destructive" });
      return;
    }
    setIsSaving(true);
    try {
      await changePassword(user.id, data.currentPassword, data.newPassword);
      toast({
        title: "Password Updated",
        description: "Your password has been successfully changed.",
      });
      reset(); // Clear form fields after successful change
    } catch (error) {
      console.error("Failed to change password:", error);
      toast({
        title: "Error Changing Password",
        description: error instanceof Error ? error.message : "Could not change password. Please check your current password and try again.",
        variant: "destructive",
      });
    } finally {
      setIsSaving(false);
    }
  };

  if (isAuthLoading) {
    return (
      <AppShell>
        <div className="flex items-center justify-center h-full">
          <Loader2 className="h-8 w-8 animate-spin text-accent" />
          <p className="ml-2">Loading profile...</p>
        </div>
      </AppShell>
    );
  }
  
   if (!user) {
     return (
      <AppShell>
        <div className="flex items-center justify-center h-full">
          <p>Please log in to view your profile.</p>
        </div>
      </AppShell>
    );
  }


  return (
    <AppShell>
      <div className="grid gap-6 md:grid-cols-1 lg:grid-cols-3">
        {/* Profile Info Card */}
        <Card className="lg:col-span-1 shadow-lg">
           <CardHeader>
            <CardTitle className="text-xl flex items-center">
                <UserCircle className="h-6 w-6 mr-2 text-accent" />
                Your Profile
            </CardTitle>
            <CardDescription>
                Basic account information.
            </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
                 <div className="space-y-1">
                    <Label>Full Name</Label>
                    <p className="text-muted-foreground">{user.name || 'Not Provided'}</p>
                </div>
                 <div className="space-y-1">
                    <Label>Email Address</Label>
                    <p className="text-muted-foreground">{user.email}</p>
                </div>
                 <div className="space-y-1">
                    <Label>Role</Label>
                    <p className="text-muted-foreground capitalize">{user.role}</p>
                </div>
                {/* Add more profile details if available */}
            </CardContent>
        </Card>

        {/* Change Password Card */}
        <Card className="lg:col-span-2 shadow-lg">
          <CardHeader>
            <CardTitle className="text-xl flex items-center">
              <Lock className="h-6 w-6 mr-2 text-accent" />
              Change Password
            </CardTitle>
            <CardDescription>
              Update your account password. Choose a strong, unique password.
            </CardDescription>
          </CardHeader>
          <form onSubmit={handleSubmit(handlePasswordChange)}>
            <CardContent className="space-y-6">
              <div className="space-y-2">
                <Label htmlFor="currentPassword">Current Password</Label>
                <Input
                  id="currentPassword"
                  type="password"
                  {...register("currentPassword")}
                  disabled={isSaving}
                  placeholder="Enter your current password"
                  className={errors.currentPassword ? 'border-destructive' : ''}
                />
                 {errors.currentPassword && <p className="text-sm text-destructive">{errors.currentPassword.message}</p>}
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                    <Label htmlFor="newPassword">New Password</Label>
                    <Input
                    id="newPassword"
                    type="password"
                    {...register("newPassword")}
                    disabled={isSaving}
                    placeholder="Enter new password"
                    className={errors.newPassword ? 'border-destructive' : ''}
                    />
                    {errors.newPassword && <p className="text-sm text-destructive">{errors.newPassword.message}</p>}
                </div>
                <div className="space-y-2">
                    <Label htmlFor="confirmPassword">Confirm New Password</Label>
                    <Input
                    id="confirmPassword"
                    type="password"
                    {...register("confirmPassword")}
                    disabled={isSaving}
                    placeholder="Confirm new password"
                    className={errors.confirmPassword ? 'border-destructive' : ''}
                    />
                    {errors.confirmPassword && <p className="text-sm text-destructive">{errors.confirmPassword.message}</p>}
                </div>
              </div>
               {/* Add password strength indicator if desired */}
            </CardContent>
            <CardFooter className="flex justify-end border-t pt-6">
              <Button type="submit" disabled={isSaving}>
                {isSaving ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Save className="mr-2 h-4 w-4" />}
                {isSaving ? 'Saving...' : 'Update Password'}
              </Button>
            </CardFooter>
          </form>
        </Card>
      </div>
    </AppShell>
  );
}
