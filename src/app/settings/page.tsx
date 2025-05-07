
'use client';

import { useState, useEffect } from 'react';
import { AppShell } from '@/components/layout/app-shell';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input'; // Kept for potential future use
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Switch } from '@/components/ui/switch';
import { Slider } from '@/components/ui/slider';
import { useToast } from '@/hooks/use-toast';
import { DEFAULT_SETTINGS } from '@/lib/constants';
import type { SettingsData } from '@/types';
import { Save, RotateCcw, Settings as SettingsIcon, HelpCircle, AlertTriangle } from 'lucide-react';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { useForm, Controller } from 'react-hook-form';
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { createCrawlJob, parseSettingsForBackend, CreateCrawlJobPayload } from '@/services/breachwatch-api';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';

// Zod schema for frontend form validation
const settingsSchema = z.object({
  keywords: z.string().min(1, { message: "Keywords are required." }),
  fileExtensions: z.string().min(1, { message: "File extensions are required." }),
  seedUrls: z.string().min(1, { message: "Seed URLs are required." })
    .refine(value => {
      const urls = value.split('\n').map(url => url.trim()).filter(url => url);
      if (urls.length === 0) return false; // Must have at least one URL
      // Basic URL validation (can be enhanced)
      return urls.every(url => /^https?:\/\/[^\s/$.?#].[^\s]*$/i.test(url));
    }, { message: "Please provide valid URLs, one per line." }),
  searchDorks: z.string().min(1, { message: "Search dorks are required." }),
  crawlDepth: z.number().min(0).max(10),
  respectRobotsTxt: z.boolean(),
  requestDelay: z.number().min(0).max(10),
});

type SettingsFormValues = z.infer<typeof settingsSchema>;

export default function SettingsPage() {
  const [isSubmitting, setIsSubmittingState] = useState(false); // Renamed to avoid conflict
  const { toast } = useToast();

  const form = useForm<SettingsFormValues>({
    resolver: zodResolver(settingsSchema),
    defaultValues: DEFAULT_SETTINGS,
    mode: "onChange", // Validate on change for better UX
  });

  const { handleSubmit, control, reset, formState: { errors, isValid } } = form;

  // Load settings from localStorage on mount (optional, could also fetch from backend if global settings exist)
  useEffect(() => {
    const storedSettings = localStorage.getItem('breachWatchSettings');
    if (storedSettings) {
      try {
        const parsedSettings = JSON.parse(storedSettings);
        reset(parsedSettings); // Use reset from react-hook-form
      } catch (e) {
        console.error("Failed to parse stored settings:", e);
        // Fallback to default if parsing fails
        localStorage.removeItem('breachWatchSettings');
        reset(DEFAULT_SETTINGS);
      }
    }
  }, [reset]);


  const handleResetDefaults = () => {
    localStorage.removeItem('breachWatchSettings');
    reset(DEFAULT_SETTINGS);
    toast({
      title: 'Settings Reset',
      description: 'Configuration has been reset to default values.',
      variant: 'default'
    });
  }

  const onSubmit = async (values: SettingsFormValues) => {
    setIsSubmittingState(true);
    try {
      // Save current form values to localStorage (for persistence across sessions)
      localStorage.setItem('breachWatchSettings', JSON.stringify(values));

      const backendSettings = parseSettingsForBackend(values);
      const payload: CreateCrawlJobPayload = {
        name: `Crawl Job - ${new Date().toLocaleString()}`, // Optional: make name configurable
        settings: backendSettings,
      };
      
      const newJob = await createCrawlJob(payload);
      toast({
        title: 'Crawl Job Created Successfully',
        description: `Job "${newJob.name}" (ID: ${newJob.id}) started with status: ${newJob.status}.`,
      });
    } catch (error) {
      console.error('Failed to create crawl job:', error);
      toast({
        title: 'Error Creating Crawl Job',
        description: error instanceof Error ? error.message : 'An unexpected error occurred. Please try again.',
        variant: 'destructive',
      });
    } finally {
      setIsSubmittingState(false);
    }
  };

  return (
    <AppShell>
      <Card className="shadow-xl">
        <CardHeader>
          <CardTitle className="text-2xl flex items-center">
            <SettingsIcon className="h-7 w-7 mr-2 text-accent" />
            Crawl Configuration
          </CardTitle>
          <CardDescription>
            Define parameters for a new crawl job. Saving these settings will initiate a new crawl.
          </CardDescription>
        </CardHeader>
        <form onSubmit={handleSubmit(onSubmit)}>
          <CardContent className="space-y-8">
             <Alert variant="default" className="bg-accent/10 border-accent/30">
              <AlertTriangle className="h-5 w-5 text-accent" />
              <AlertTitle className="text-accent">Important Note</AlertTitle>
              <AlertDescription>
                Saving these settings will create and start a new crawl job on the backend.
                Monitor the dashboard or a dedicated 'Jobs' page (future enhancement) for progress.
                Current settings are also saved locally in your browser for convenience.
              </AlertDescription>
            </Alert>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-2">
                <Label htmlFor="keywords" className="flex items-center">
                  Keywords
                  <TooltipProvider>
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <HelpCircle className="h-4 w-4 ml-1.5 text-muted-foreground cursor-help" />
                      </TooltipTrigger>
                      <TooltipContent side="top">
                        <p className="max-w-xs">Comma or newline-separated keywords. E.g., leak, dump, database, NIK.</p>
                      </TooltipContent>
                    </Tooltip>
                  </TooltipProvider>
                </Label>
                <Controller
                  name="keywords"
                  control={control}
                  render={({ field }) => (
                    <Textarea
                      id="keywords"
                      placeholder="e.g., leak, dump, database, NIK (comma or newline separated)"
                      rows={3}
                      className={`resize-y ${errors.keywords ? 'border-destructive' : ''}`}
                      {...field}
                    />
                  )}
                />
                {errors.keywords && (
                  <p className="text-sm text-destructive">
                    {errors.keywords.message}
                  </p>
                )}
              </div>
              <div className="space-y-2">
                <Label htmlFor="fileExtensions" className="flex items-center">
                  File Extensions (without dot)
                  <TooltipProvider>
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <HelpCircle className="h-4 w-4 ml-1.5 text-muted-foreground cursor-help" />
                      </TooltipTrigger>
                      <TooltipContent side="top">
                        <p className="max-w-xs">Comma or newline-separated file extensions. E.g., txt, csv, sql, json, zip.</p>
                      </TooltipContent>
                    </Tooltip>
                  </TooltipProvider>
                </Label>
                <Controller
                  name="fileExtensions"
                  control={control}
                  render={({ field }) => (
                    <Textarea
                      id="fileExtensions"
                      placeholder="e.g., txt, csv, sql (comma or newline separated)"
                      rows={3}
                      className={`resize-y ${errors.fileExtensions ? 'border-destructive' : ''}`}
                      {...field}
                    />
                  )}
                />
                {errors.fileExtensions && (
                  <p className="text-sm text-destructive">
                    {errors.fileExtensions.message}
                  </p>
                )}
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="seedUrls" className="flex items-center">
                Seed URLs
                <TooltipProvider>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <HelpCircle className="h-4 w-4 ml-1.5 text-muted-foreground cursor-help" />
                    </TooltipTrigger>
                      <TooltipContent side="top">
                        <p className="max-w-xs">Starting URLs for crawling, one per line. E.g., https://example.com.</p>
                      </TooltipContent>
                    </Tooltip>
                  </TooltipProvider>
                </Label>
                <Controller
                  name="seedUrls"
                  control={control}
                  render={({ field }) => (
                    <Textarea
                      id="seedUrls"
                      placeholder="e.g., https://example.com (one URL per line)"
                      rows={4}
                      className={`resize-y ${errors.seedUrls ? 'border-destructive' : ''}`}
                      {...field}
                    />
                  )}
                />
                {errors.seedUrls && (
                  <p className="text-sm text-destructive">
                    {errors.seedUrls.message}
                  </p>
                )}
              </div>

            <div className="space-y-2">
              <Label htmlFor="searchDorks" className="flex items-center">
                Search Engine Dorks
                <TooltipProvider>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <HelpCircle className="h-4 w-4 ml-1.5 text-muted-foreground cursor-help" />
                    </TooltipTrigger>
                    <TooltipContent side="top">
                      <p className="max-w-xs">Advanced search queries, one per line. E.g., filetype:csv "password".</p>
                    </TooltipContent>
                  </Tooltip>
                </TooltipProvider>
              </Label>
              <Controller
                name="searchDorks"
                control={control}
                render={({ field }) => (
                  <Textarea
                    id="searchDorks"
                    placeholder='e.g., filetype:csv "password" (one dork per line)'
                    rows={4}
                    className={`resize-y ${errors.searchDorks ? 'border-destructive' : ''}`}
                    {...field}
                  />
                )}
              />
              {errors.searchDorks && (
                <p className="text-sm text-destructive">
                  {errors.searchDorks.message}
                </p>
              )}
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 items-start">
              <div className="space-y-3">
                <Label htmlFor="crawlDepth" className="flex items-center">
                  Crawl Depth: {form.watch("crawlDepth")}
                  <TooltipProvider>
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <HelpCircle className="h-4 w-4 ml-1.5 text-muted-foreground cursor-help" />
                      </TooltipTrigger>
                      <TooltipContent side="top">
                        <p className="max-w-xs">How many links deep to follow (0-10). 0 for seed URLs only.</p>
                      </TooltipContent>
                    </Tooltip>
                  </TooltipProvider>
                </Label>
                <Controller
                  name="crawlDepth"
                  control={control}
                  render={({ field }) => (
                    <Slider
                      id="crawlDepth"
                      min={0} max={10} step={1}
                      onValueChange={(value) => field.onChange(value[0])}
                      value={[field.value]}
                    />
                  )}
                />
                {errors.crawlDepth && (
                  <p className="text-sm text-destructive">
                    {errors.crawlDepth.message}
                  </p>
                )}
              </div>
              <div className="space-y-3">
                <Label htmlFor="requestDelay" className="flex items-center">
                  Request Delay: {form.watch("requestDelay")}s
                  <TooltipProvider>
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <HelpCircle className="h-4 w-4 ml-1.5 text-muted-foreground cursor-help" />
                      </TooltipTrigger>
                      <TooltipContent side="top">
                        <p className="max-w-xs">Delay in seconds between requests per domain (0-10s).</p>
                      </TooltipContent>
                    </Tooltip>
                  </TooltipProvider>
                </Label>
                <Controller
                  name="requestDelay"
                  control={control}
                  render={({ field }) => (
                    <Slider
                      id="requestDelay"
                      min={0} max={10} step={0.5}
                      onValueChange={(value) => field.onChange(value[0])}
                      value={[field.value]}
                    />
                  )}
                />
                {errors.requestDelay && (
                  <p className="text-sm text-destructive">
                    {errors.requestDelay.message}
                  </p>
                )}
              </div>
            </div>

            <div className="flex items-center space-x-3">
              <Controller
                name="respectRobotsTxt"
                control={control}
                render={({ field }) => (
                  <Switch
                    id="respectRobotsTxt"
                    checked={field.value}
                    onCheckedChange={field.onChange}
                  />
                )}
              />
              <Label htmlFor="respectRobotsTxt" className="flex items-center">
                Respect robots.txt
                <TooltipProvider>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <HelpCircle className="h-4 w-4 ml-1.5 text-muted-foreground cursor-help" />
                    </TooltipTrigger>
                      <TooltipContent side="top">
                        <p className="max-w-xs">Attempt to follow rules in robots.txt. Disabling may be impolite or violate ToS.</p>
                      </TooltipContent>
                    </Tooltip>
                  </TooltipProvider>
                </Label>
              </div>
            </CardContent>
            <CardFooter className="flex justify-end space-x-3 border-t pt-6">
              <Button type="button" variant="outline" onClick={handleResetDefaults} disabled={isSubmitting}>
                <RotateCcw className="mr-2 h-4 w-4" />
                Reset to Defaults
              </Button>
              <Button type="submit" disabled={isSubmitting || !isValid}>
                <Save className={`mr-2 h-4 w-4 ${isSubmitting ? 'animate-spin' : ''}`} />
                {isSubmitting ? 'Starting Crawl...' : 'Save & Start Crawl'}
              </Button>
            </CardFooter>
          </form>
        </Card>
      </AppShell>
    );
  }
