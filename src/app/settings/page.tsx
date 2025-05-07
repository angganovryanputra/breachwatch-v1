'use client';

import { useState, useEffect } from 'react';
import { AppShell } from '@/components/layout/app-shell';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Switch } from '@/components/ui/switch';
import { Slider } from '@/components/ui/slider';
import { useToast } from '@/hooks/use-toast';
import { DEFAULT_SETTINGS } from '@/lib/constants';
import type { SettingsData } from '@/types';
import { Save, RotateCcw, Settings as SettingsIcon, HelpCircle } from 'lucide-react';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { useForm, Controller } from 'react-hook-form';
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";

const settingsSchema = z.object({
  keywords: z.string().min(1, { message: "Keywords are required." }),
  fileExtensions: z.string().min(1, { message: "File extensions are required." }),
  seedUrls: z.string().min(1, { message: "Seed URLs are required." }),
  searchDorks: z.string().min(1, { message: "Search dorks are required." }),
  crawlDepth: z.number().min(0).max(10),
  respectRobotsTxt: z.boolean(),
  requestDelay: z.number().min(0).max(10),
});

type SettingsFormValues = z.infer<typeof settingsSchema>;

export default function SettingsPage() {
  const [isLoading, setIsLoading] = useState(false);
  const { toast } = useToast();

  const form = useForm<SettingsFormValues>({
    resolver: zodResolver(settingsSchema),
    defaultValues: DEFAULT_SETTINGS,
    mode: "onChange",
  });

  const { handleSubmit, control, reset, formState: { isSubmitting, isValid } } = form;

  // In a real app, you'd fetch existing settings from a backend or localStorage
  useEffect(() => {
    const storedSettings = localStorage.getItem('breachWatchSettings');
    if (storedSettings) {
      form.reset(JSON.parse(storedSettings));
    }
  }, [form]);


  const handleResetDefaults = () => {
    localStorage.removeItem('breachWatchSettings');
    form.reset(DEFAULT_SETTINGS);
    toast({
      title: 'Settings Reset',
      description: 'Configuration has been reset to default values.',
      variant: 'default'
    });
  }

  const onSubmit = async (values: SettingsFormValues) => {
    setIsLoading(true);
    // Simulate saving settings
    setTimeout(() => {
      localStorage.setItem('breachWatchSettings', JSON.stringify(values));
      setIsLoading(false);
      toast({
        title: 'Settings Saved',
        description: 'Your configuration has been updated successfully.',
      });
    }, 1000);
  };


  return (
    
      <AppShell>
        <Card className="shadow-xl">
          <CardHeader>
            <CardTitle className="text-2xl flex items-center">
              <SettingsIcon className="h-7 w-7 mr-2 text-accent" />
              Configuration Settings
            </CardTitle>
            <CardDescription>
              Adjust parameters for web crawling, file identification, and keyword matching.
              Changes will take effect on the next crawl.
            </CardDescription>
          </CardHeader>
          <form onSubmit={handleSubmit(onSubmit)}>
            <CardContent className="space-y-8">
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
                          <p className="max-w-xs">Comma-separated keywords to search for within URLs, page titles, link text, and potentially file content. E.g., leak, dump, database, users, passwords.</p>
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
                        placeholder="e.g., leak, dump, database, users, passwords"
                        rows={3}
                        className="resize-y"
                        {...field}
                      />
                    )}
                  />
                  {form.formState.errors.keywords && (
                    <p className="text-sm text-destructive">
                      {form.formState.errors.keywords.message}
                    </p>
                  )}
                </div>
                <div className="space-y-2">
                  <Label htmlFor="fileExtensions" className="flex items-center">
                    File Extensions
                    <TooltipProvider>
                      <Tooltip>
                        <TooltipTrigger asChild>
                          <HelpCircle className="h-4 w-4 ml-1.5 text-muted-foreground cursor-help" />
                        </TooltipTrigger>
                        <TooltipContent side="top">
                          <p className="max-w-xs">Comma-separated file extensions to identify. E.g., .txt, .csv, .sql, .json, .zip.</p>
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
                        placeholder="e.g., .txt, .csv, .sql, .json, .zip"
                        rows={3}
                        className="resize-y"
                        {...field}
                      />
                    )}
                  />
                  {form.formState.errors.fileExtensions && (
                    <p className="text-sm text-destructive">
                      {form.formState.errors.fileExtensions.message}
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
                        <p className="max-w-xs">Starting URLs for crawling, one per line. E.g., https://example.com, https://forum.example.org.</p>
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
                      className="resize-y"
                      {...field}
                    />
                  )}
                />
                {form.formState.errors.seedUrls && (
                  <p className="text-sm text-destructive">
                    {form.formState.errors.seedUrls.message}
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
                        <p className="max-w-xs">Advanced search queries for search engines, one per line. E.g., filetype:csv "password", intitle:"index of" "backup.sql".</p>
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
                      className="resize-y"
                      {...field}
                    />
                  )}
                />
                {form.formState.errors.searchDorks && (
                  <p className="text-sm text-destructive">
                    {form.formState.errors.searchDorks.message}
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
                          <p className="max-w-xs">How many links deep to follow from seed URLs. 0 means only scan the seed URLs themselves.</p>
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
                        min={0}
                        max={10}
                        step={1}
                        onValueChange={(value) => field.onChange(value[0])}
                        value={[field.value]}
                      />
                    )}
                  />
                  {form.formState.errors.crawlDepth && (
                    <p className="text-sm text-destructive">
                      {form.formState.errors.crawlDepth.message}
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
                          <p className="max-w-xs">Delay in seconds between HTTP requests to be polite to servers.</p>
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
                        min={0}
                        max={10}
                        step={0.5}
                        onValueChange={(value) => field.onChange(value[0])}
                        value={[field.value]}
                      />
                    )}
                  />
                  {form.formState.errors.requestDelay && (
                    <p className="text-sm text-destructive">
                      {form.formState.errors.requestDelay.message}
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
                        <p className="max-w-xs">If enabled, the crawler will attempt to follow rules specified in a website's robots.txt file. Disabling this may be impolite or violate terms of service.</p>
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
                {isSubmitting ? 'Saving...' : 'Save Settings'}
              </Button>
            </CardFooter>
          </form>
        </Card>
      </AppShell>
    
  );
}
