
'use client';

import { useState, useEffect, useCallback } from 'react';
import { AppShell } from '@/components/layout/app-shell';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { useToast } from '@/hooks/use-toast';
import type { UserPreferences as UserPreferencesType } from '@/types';
import { Save, UserCog, RotateCcw, Loader2 } from 'lucide-react';
import { useAuth } from '@/context/auth-context';
import { getUserPreferences, updateUserPreferences } from '@/services/breachwatch-api'; 

const DEFAULT_PREFERENCES_VALUES: Omit<UserPreferencesType, 'user_id' | 'updated_at'> = {
  default_items_per_page: 10,
  receive_email_notifications: true,
};

export default function UserPreferencesPage() {
  const { user, isLoading: isAuthLoading } = useAuth();
  const [preferences, setPreferences] = useState<Omit<UserPreferencesType, 'user_id' | 'updated_at'>>(DEFAULT_PREFERENCES_VALUES);
  const [isLoadingPage, setIsLoadingPage] = useState(true); // Page specific loading state
  const [isSaving, setIsSaving] = useState(false);
  const { toast } = useToast();

  const fetchPreferences = useCallback(async () => {
      setIsLoadingPage(true);
      try {
        // API now infers user ID from token
        const data = await getUserPreferences();
        if (data) {
          setPreferences({
            default_items_per_page: data.default_items_per_page,
            receive_email_notifications: data.receive_email_notifications,
          });
        } else {
          // If backend returns null (e.g., no preferences yet), set defaults
          setPreferences(DEFAULT_PREFERENCES_VALUES);
        }
      } catch (error) {
        console.error("Failed to fetch user preferences:", error);
        toast({
          title: "Error Loading Preferences",
          description: "Could not load your preferences. Using default values.",
          variant: "destructive",
        });
        setPreferences(DEFAULT_PREFERENCES_VALUES);
      } finally {
        setIsLoadingPage(false);
      }
  }, [toast]);

  useEffect(() => {
    // Fetch preferences only if user is authenticated
    if (user && !isAuthLoading) {
        fetchPreferences();
    } else if (!isAuthLoading && !user) {
      // User not logged in, stop loading, AppShell should handle redirect
      setIsLoadingPage(false);
    }
  }, [user, isAuthLoading, fetchPreferences]);


  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value, type, checked } = e.target;
    setPreferences(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : type === 'number' ? parseInt(value, 10) || 0 : value,
    }));
  };
  
  const handleSwitchChange = (checked: boolean, name: keyof Omit<UserPreferencesType, 'user_id' | 'updated_at'>) => {
    setPreferences(prev => ({
      ...prev,
      [name]: checked,
    }));
  };


  const handleSavePreferences = async () => {
    if (!user) { // Check if user object exists from auth context
      toast({ title: "Error", description: "User not authenticated. Cannot save preferences.", variant: "destructive" });
      return;
    }
    setIsSaving(true);
    try {
      const payload: Omit<UserPreferencesType, 'user_id' | 'updated_at'> = {
        default_items_per_page: preferences.default_items_per_page,
        receive_email_notifications: preferences.receive_email_notifications,
      };
      // API now infers user ID from token
      await updateUserPreferences(payload); 
      toast({
        title: "Preferences Saved",
        description: "Your preferences have been successfully updated.",
      });
    } catch (error) {
      console.error("Failed to save user preferences:", error);
      toast({
        title: "Error Saving Preferences",
        description: error instanceof Error ? error.message : "Could not save your preferences. Please try again.",
        variant: "destructive",
      });
    } finally {
      setIsSaving(false);
    }
  };

  const handleResetDefaults = () => {
    setPreferences(DEFAULT_PREFERENCES_VALUES);
    toast({
      title: "Preferences Reset",
      description: "Settings have been reset to defaults. Click 'Save Preferences' to apply.",
      variant: "default",
    });
  };

  // Combined loading state from auth and page-specific loading
  const pageIsEffectivelyLoading = isLoadingPage || isAuthLoading;

  if (pageIsEffectivelyLoading) {
    return (
      <AppShell>
        <div className="flex items-center justify-center h-full">
          <Loader2 className="h-8 w-8 animate-spin text-accent" />
          <p className="ml-2">Loading preferences...</p>
        </div>
      </AppShell>
    );
  }
  
  if (!user && !isAuthLoading) { // Ensure auth loading is finished before showing this
     return (
      <AppShell>
        <div className="flex items-center justify-center h-full">
          <p>Please log in to manage your preferences.</p>
        </div>
      </AppShell>
    );
  }


  return (
    <AppShell>
      <Card className="max-w-2xl mx-auto shadow-xl">
        <CardHeader>
          <CardTitle className="text-2xl flex items-center">
            <UserCog className="h-7 w-7 mr-2 text-accent" />
            User Preferences
          </CardTitle>
          <CardDescription>
            Customize your application experience. Changes are saved per user.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="space-y-2">
            <Label htmlFor="default_items_per_page">Default Items Per Page</Label>
            <Input
              id="default_items_per_page"
              name="default_items_per_page"
              type="number"
              value={preferences.default_items_per_page}
              onChange={handleInputChange}
              min="5"
              max="100"
              className="w-32"
              disabled={isSaving}
            />
            <p className="text-sm text-muted-foreground">
              Set the default number of items displayed in tables (e.g., Dashboard, File Records).
            </p>
          </div>

          <div className="flex items-center space-x-3">
            <Switch
              id="receive_email_notifications"
              name="receive_email_notifications"
              checked={preferences.receive_email_notifications}
              onCheckedChange={(checked) => handleSwitchChange(checked, "receive_email_notifications")}
              disabled={isSaving}
            />
            <Label htmlFor="receive_email_notifications">Receive Email Notifications</Label>
          </div>
           <p className="text-sm text-muted-foreground -mt-4 ml-[3.25rem]">
              Enable or disable email notifications for critical findings or job completions. (Note: Email functionality backend is not yet implemented).
            </p>

        </CardContent>
        <CardFooter className="flex justify-end space-x-3 border-t pt-6">
          <Button type="button" variant="outline" onClick={handleResetDefaults} disabled={isSaving}>
            <RotateCcw className="mr-2 h-4 w-4" />
            Reset to Defaults
          </Button>
          <Button type="button" onClick={handleSavePreferences} disabled={isSaving}>
            {isSaving ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Save className="mr-2 h-4 w-4" />}
            {isSaving ? 'Saving...' : 'Save Preferences'}
          </Button>
        </CardFooter>
      </Card>
    </AppShell>
  );
}
