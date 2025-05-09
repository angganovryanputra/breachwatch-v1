
'use client';

import { useState, useEffect, useMemo } from 'react';
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
import type { SettingsFormData, ScheduleData } from '@/types';
import { Save, RotateCcw, Settings as SettingsIcon, HelpCircle, AlertTriangle, CalendarClock, Repeat, Server } from 'lucide-react';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { useForm, Controller, useWatch } from 'react-hook-form';
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { createCrawlJob, parseSettingsForBackend, CreateCrawlJobPayload } from '@/services/breachwatch-api';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import { Calendar } from '@/components/ui/calendar';
import { format } from 'date-fns';
import { cn } from '@/lib/utils';
import Link from 'next/link';

// Zod schema for frontend form validation
const settingsFormValidationSchema = z.object({
  keywords: z.string().min(1, { message: "Keywords are required." }),
  fileExtensions: z.string().min(1, { message: "File extensions are required." }),
  seedUrls: z.string().min(1, { message: "Seed URLs are required." })
    .refine(value => {
      const urls = value.split('\n').map(url => url.trim()).filter(url => url);
      if (urls.length === 0) return false; 
      try {
        return urls.every(url => new URL(url).protocol.startsWith('http'));
      } catch (e) {
        return false;
      }
    }, { message: "Please provide valid URLs (http/https), one per line." }),
  searchDorks: z.string().min(1, { message: "Search dorks are required." }),
  crawlDepth: z.number().min(0).max(10),
  respectRobotsTxt: z.boolean(),
  requestDelay: z.number().min(0).max(60), 
  customUserAgent: z.string().optional(),
  maxResultsPerDork: z.number().min(1).max(100),
  maxConcurrentRequestsPerDomain: z.number().min(1).max(10),
  proxies: z.string().optional().refine(value => { // Optional proxy list
    if (!value || value.trim() === '') return true; // Allow empty
    const proxyList = value.split('\n').map(p => p.trim()).filter(p => p);
    // Basic validation for proxy format (can be enhanced)
    return proxyList.every(p => /^(http|https|socks5):\/\/.+/.test(p) || /^[a-zA-Z0-9.-]+:[0-9]+$/.test(p) ); //scheme://host:port or host:port for http
  }, { message: "Invalid proxy format. Expected format: scheme://[user:password@]host:port, one per line." }),
  scheduleEnabled: z.boolean(),
  scheduleType: z.enum(['one-time', 'recurring']),
  scheduleCronExpression: z.string().optional(), 
  scheduleRunAtDate: z.string().optional(), 
  scheduleRunAtTime: z.string().regex(/^([01]\d|2[0-3]):([0-5]\d)$/, { message: "Invalid time format (HH:MM)" }).optional(),
  scheduleTimezone: z.string().optional(),
}).refine(data => {
    if (data.scheduleEnabled && data.scheduleType === 'recurring') {
        return !!data.scheduleCronExpression && data.scheduleCronExpression.trim() !== '';
    }
    return true;
}, {
    message: "Cron expression is required for recurring schedules.",
    path: ["scheduleCronExpression"],
}).refine(data => {
    if (data.scheduleEnabled && data.scheduleType === 'one-time') {
        return !!data.scheduleRunAtDate && !!data.scheduleRunAtTime;
    }
    return true;
}, {
    message: "Date and Time are required for one-time schedules.",
    path: ["scheduleRunAtDate"], 
});


export default function SettingsPage() {
  const [isSubmitting, setIsSubmittingState] = useState(false);
  const { toast } = useToast();

  const form = useForm<SettingsFormData>({
    resolver: zodResolver(settingsFormValidationSchema),
    defaultValues: DEFAULT_SETTINGS,
    mode: "onChange",
  });

  const { handleSubmit, control, reset, formState: { errors, isValid }, watch } = form;
  const scheduleEnabled = watch("scheduleEnabled");
  const scheduleType = watch("scheduleType");


  useEffect(() => {
    const storedSettings = localStorage.getItem('breachWatchSettings');
    if (storedSettings) {
      try {
        const parsedSettings = JSON.parse(storedSettings);
        if (parsedSettings.scheduleRunAtDate && typeof parsedSettings.scheduleRunAtDate === 'string') {
            if (!/^\d{4}-\d{2}-\d{2}$/.test(parsedSettings.scheduleRunAtDate)) {
                 parsedSettings.scheduleRunAtDate = format(new Date(parsedSettings.scheduleRunAtDate), 'yyyy-MM-dd');
            }
        } else if (parsedSettings.scheduleRunAtDate instanceof Date){
             parsedSettings.scheduleRunAtDate = format(parsedSettings.scheduleRunAtDate, 'yyyy-MM-dd');
        }
        reset(parsedSettings);
      } catch (e) {
        console.error("Failed to parse stored settings:", e);
        localStorage.removeItem('breachWatchSettings');
        reset(DEFAULT_SETTINGS);
      }
    } else {
        reset(DEFAULT_SETTINGS); 
    }
  }, [reset]);


  const handleResetDefaults = () => {
    localStorage.removeItem('breachWatchSettings');
    const defaultsWithFormattedDate = {
        ...DEFAULT_SETTINGS,
        scheduleRunAtDate: format(new Date(DEFAULT_SETTINGS.scheduleRunAtDate || new Date()), 'yyyy-MM-dd') // Handle undefined case for date
    };
    reset(defaultsWithFormattedDate);
    toast({
      title: 'Settings Reset',
      description: 'Configuration has been reset to default values.',
      variant: 'default'
    });
  }

  const onSubmit = async (values: SettingsFormData) => {
    setIsSubmittingState(true);
    try {
      localStorage.setItem('breachWatchSettings', JSON.stringify(values));

      const backendSettingsPayload = parseSettingsForBackend(values);
      const payload: CreateCrawlJobPayload = {
        name: `Crawl Job - ${new Date().toLocaleString()}`, 
        settings: backendSettingsPayload,
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
  
  const timezones = useMemo(() => {
    try {
      return Intl.supportedValuesOf('timeZone');
    } catch (e) { 
      return [
        'UTC', 'GMT', 'America/New_York', 'America/Los_Angeles', 'Europe/London', 'Europe/Paris', 
        'Asia/Tokyo', 'Asia/Shanghai', 'Asia/Dubai', 'Asia/Jakarta', 'Australia/Sydney'
      ].sort();
    }
  }, []);


  return (
    <AppShell>
      <form onSubmit={handleSubmit(onSubmit)}>
        <Card className="shadow-xl mb-6">
          <CardHeader>
            <CardTitle className="text-2xl flex items-center">
              <SettingsIcon className="h-7 w-7 mr-2 text-accent" />
              Crawl Configuration
            </CardTitle>
            <CardDescription>
              Define parameters for a new crawl job. Saving these settings will initiate a new crawl on the backend.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-8">
             <Alert variant="default" className="bg-primary/10 border-primary/30">
              <AlertTriangle className="h-5 w-5 text-primary" />
              <AlertTitle className="text-primary">Important Note</AlertTitle>
              <AlertDescription>
                Saving these settings will create and start a new crawl job.
                Monitor the <Link href="/jobs" className="text-accent hover:underline font-semibold">Crawl Jobs</Link> page for progress.
                Current settings are saved locally in your browser for convenience.
              </AlertDescription>
            </Alert>
            
            <Card>
              <CardHeader><CardTitle className="text-lg">Targeting Parameters</CardTitle></CardHeader>
              <CardContent className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-2">
                    <Label htmlFor="keywords" className="flex items-center">Keywords <TooltipProvider><Tooltip><TooltipTrigger asChild><HelpCircle className="h-4 w-4 ml-1.5 text-muted-foreground cursor-help" /></TooltipTrigger><TooltipContent side="top"><p className="max-w-xs">Comma or newline-separated keywords.</p></TooltipContent></Tooltip></TooltipProvider></Label>
                    <Controller name="keywords" control={control} render={({ field }) => (<Textarea id="keywords" placeholder="e.g., leak, dump, database, NIK" rows={4} className={`resize-y ${errors.keywords ? 'border-destructive' : ''}`} {...field} />)} />
                    {errors.keywords && <p className="text-sm text-destructive">{errors.keywords.message}</p>}
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="fileExtensions" className="flex items-center">File Extensions <TooltipProvider><Tooltip><TooltipTrigger asChild><HelpCircle className="h-4 w-4 ml-1.5 text-muted-foreground cursor-help" /></TooltipTrigger><TooltipContent side="top"><p className="max-w-xs">Comma or newline-separated, without dot. E.g., txt, csv, sql.</p></TooltipContent></Tooltip></TooltipProvider></Label>
                    <Controller name="fileExtensions" control={control} render={({ field }) => (<Textarea id="fileExtensions" placeholder="e.g., txt, csv, sql" rows={4} className={`resize-y ${errors.fileExtensions ? 'border-destructive' : ''}`} {...field} />)} />
                    {errors.fileExtensions && <p className="text-sm text-destructive">{errors.fileExtensions.message}</p>}
                  </div>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="seedUrls" className="flex items-center">Seed URLs <TooltipProvider><Tooltip><TooltipTrigger asChild><HelpCircle className="h-4 w-4 ml-1.5 text-muted-foreground cursor-help" /></TooltipTrigger><TooltipContent side="top"><p className="max-w-xs">Starting URLs, one per line.</p></TooltipContent></Tooltip></TooltipProvider></Label>
                  <Controller name="seedUrls" control={control} render={({ field }) => (<Textarea id="seedUrls" placeholder="e.g., https://example.com (one URL per line)" rows={5} className={`resize-y ${errors.seedUrls ? 'border-destructive' : ''}`} {...field} />)} />
                  {errors.seedUrls && <p className="text-sm text-destructive">{errors.seedUrls.message}</p>}
                </div>
                <div className="space-y-2">
                  <Label htmlFor="searchDorks" className="flex items-center">Search Engine Dorks <TooltipProvider><Tooltip><TooltipTrigger asChild><HelpCircle className="h-4 w-4 ml-1.5 text-muted-foreground cursor-help" /></TooltipTrigger><TooltipContent side="top"><p className="max-w-xs">Advanced search queries, one per line.</p></TooltipContent></Tooltip></TooltipProvider></Label>
                  <Controller name="searchDorks" control={control} render={({ field }) => (<Textarea id="searchDorks" placeholder='e.g., filetype:csv "password" (one dork per line)' rows={5} className={`resize-y ${errors.searchDorks ? 'border-destructive' : ''}`} {...field} />)} />
                  {errors.searchDorks && <p className="text-sm text-destructive">{errors.searchDorks.message}</p>}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader><CardTitle className="text-lg">Advanced Crawler Settings</CardTitle></CardHeader>
              <CardContent className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 items-start">
                  <div className="space-y-3">
                    <Label htmlFor="crawlDepth" className="flex items-center">Crawl Depth: {form.watch("crawlDepth")} <TooltipProvider><Tooltip><TooltipTrigger asChild><HelpCircle className="h-4 w-4 ml-1.5 text-muted-foreground cursor-help" /></TooltipTrigger><TooltipContent side="top"><p className="max-w-xs">How many links deep (0-10). 0 for seed URLs only.</p></TooltipContent></Tooltip></TooltipProvider></Label>
                    <Controller name="crawlDepth" control={control} render={({ field }) => (<Slider id="crawlDepth" min={0} max={10} step={1} onValueChange={(value) => field.onChange(value[0])} value={[field.value]} />)} />
                    {errors.crawlDepth && <p className="text-sm text-destructive">{errors.crawlDepth.message}</p>}
                  </div>
                  <div className="space-y-3">
                    <Label htmlFor="requestDelay" className="flex items-center">Request Delay: {form.watch("requestDelay")}s <TooltipProvider><Tooltip><TooltipTrigger asChild><HelpCircle className="h-4 w-4 ml-1.5 text-muted-foreground cursor-help" /></TooltipTrigger><TooltipContent side="top"><p className="max-w-xs">Delay between requests per domain (0-60s).</p></TooltipContent></Tooltip></TooltipProvider></Label>
                    <Controller name="requestDelay" control={control} render={({ field }) => (<Slider id="requestDelay" min={0} max={60} step={0.5} onValueChange={(value) => field.onChange(value[0])} value={[field.value]} />)} />
                    {errors.requestDelay && <p className="text-sm text-destructive">{errors.requestDelay.message}</p>}
                  </div>
                   <div className="space-y-3">
                    <Label htmlFor="maxResultsPerDork" className="flex items-center">Max Results Per Dork: {form.watch("maxResultsPerDork")} <TooltipProvider><Tooltip><TooltipTrigger asChild><HelpCircle className="h-4 w-4 ml-1.5 text-muted-foreground cursor-help" /></TooltipTrigger><TooltipContent side="top"><p className="max-w-xs">Max results from search engine per dork (1-100).</p></TooltipContent></Tooltip></TooltipProvider></Label>
                    <Controller name="maxResultsPerDork" control={control} render={({ field }) => (<Slider id="maxResultsPerDork" min={1} max={100} step={1} onValueChange={(value) => field.onChange(value[0])} value={[field.value ?? 20]} />)} />
                    {errors.maxResultsPerDork && <p className="text-sm text-destructive">{errors.maxResultsPerDork.message}</p>}
                  </div>
                  <div className="space-y-3">
                    <Label htmlFor="maxConcurrentRequestsPerDomain" className="flex items-center">Max Concurrent Requests/Domain: {form.watch("maxConcurrentRequestsPerDomain")} <TooltipProvider><Tooltip><TooltipTrigger asChild><HelpCircle className="h-4 w-4 ml-1.5 text-muted-foreground cursor-help" /></TooltipTrigger><TooltipContent side="top"><p className="max-w-xs">Max parallel requests to a single domain (1-10).</p></TooltipContent></Tooltip></TooltipProvider></Label>
                    <Controller name="maxConcurrentRequestsPerDomain" control={control} render={({ field }) => (<Slider id="maxConcurrentRequestsPerDomain" min={1} max={10} step={1} onValueChange={(value) => field.onChange(value[0])} value={[field.value ?? 2]} />)} />
                    {errors.maxConcurrentRequestsPerDomain && <p className="text-sm text-destructive">{errors.maxConcurrentRequestsPerDomain.message}</p>}
                  </div>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="customUserAgent" className="flex items-center">Custom User Agent (Optional) <TooltipProvider><Tooltip><TooltipTrigger asChild><HelpCircle className="h-4 w-4 ml-1.5 text-muted-foreground cursor-help" /></TooltipTrigger><TooltipContent side="top"><p className="max-w-xs">Leave blank to use default. Provide a specific User-Agent string.</p></TooltipContent></Tooltip></TooltipProvider></Label>
                  <Controller name="customUserAgent" control={control} render={({ field }) => (<Input id="customUserAgent" placeholder="e.g., Mozilla/5.0 (Windows NT 10.0; Win64; x64)..." className={`${errors.customUserAgent ? 'border-destructive' : ''}`} {...field} value={field.value ?? ''} />)} />
                  {errors.customUserAgent && <p className="text-sm text-destructive">{errors.customUserAgent.message}</p>}
                </div>
                 {/* Proxy List Input */}
                <div className="space-y-2">
                    <Label htmlFor="proxies" className="flex items-center">
                        Proxy List (Optional) <Server className="h-4 w-4 ml-1.5 text-muted-foreground" />
                        <TooltipProvider>
                            <Tooltip>
                                <TooltipTrigger asChild><HelpCircle className="h-4 w-4 ml-1.5 text-muted-foreground cursor-help" /></TooltipTrigger>
                                <TooltipContent side="top" className="max-w-md">
                                    <p>Enter proxy URLs, one per line. Format: `scheme://[user:password@]host:port`.</p>
                                    <p>Examples: `http://proxy.example.com:8080`, `https://user:pass@secureproxy.net:443`, `socks5://localhost:1080`</p>
                                    <p>If provided, the crawler will randomly rotate through these proxies for requests.</p>
                                </TooltipContent>
                            </Tooltip>
                        </TooltipProvider>
                    </Label>
                    <Controller
                        name="proxies"
                        control={control}
                        render={({ field }) => (
                            <Textarea
                                id="proxies"
                                placeholder="e.g., http://proxy.example.com:8080 (one proxy per line)"
                                rows={4}
                                className={`resize-y ${errors.proxies ? 'border-destructive' : ''}`}
                                {...field}
                                value={field.value ?? ''}
                            />
                        )}
                    />
                    {errors.proxies && <p className="text-sm text-destructive">{errors.proxies.message}</p>}
                </div>
                <div className="flex items-center space-x-3 pt-2">
                  <Controller name="respectRobotsTxt" control={control} render={({ field }) => (<Switch id="respectRobotsTxt" checked={field.value} onCheckedChange={field.onChange} />)} />
                  <Label htmlFor="respectRobotsTxt" className="flex items-center">Respect robots.txt <TooltipProvider><Tooltip><TooltipTrigger asChild><HelpCircle className="h-4 w-4 ml-1.5 text-muted-foreground cursor-help" /></TooltipTrigger><TooltipContent side="top"><p className="max-w-xs">Attempt to follow rules in robots.txt. Disabling may be impolite or violate ToS.</p></TooltipContent></Tooltip></TooltipProvider></Label>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                    <CardTitle className="text-lg flex items-center"><CalendarClock className="mr-2 h-5 w-5"/>Job Scheduling (Optional)</CardTitle>
                    <Controller
                        name="scheduleEnabled"
                        control={control}
                        render={({ field }) => (
                            <Switch
                            id="scheduleEnabled"
                            checked={field.value}
                            onCheckedChange={field.onChange}
                            aria-label="Enable job scheduling"
                            />
                        )}
                    />
                </div>
                <CardDescription>Configure the job to run at a specific time or on a recurring basis.</CardDescription>
              </CardHeader>
              {scheduleEnabled && (
                <CardContent className="space-y-6 pt-4">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div className="space-y-2">
                            <Label htmlFor="scheduleType">Schedule Type</Label>
                            <Controller
                                name="scheduleType"
                                control={control}
                                render={({ field }) => (
                                <Select onValueChange={field.onChange} defaultValue={field.value}>
                                    <SelectTrigger id="scheduleType">
                                    <SelectValue placeholder="Select schedule type" />
                                    </SelectTrigger>
                                    <SelectContent>
                                    <SelectItem value="one-time">One-time</SelectItem>
                                    <SelectItem value="recurring">Recurring</SelectItem>
                                    </SelectContent>
                                </Select>
                                )}
                            />
                        </div>
                        <div className="space-y-2">
                            <Label htmlFor="scheduleTimezone">Timezone</Label>
                             <Controller
                                name="scheduleTimezone"
                                control={control}
                                render={({ field }) => (
                                    <Select onValueChange={field.onChange} value={field.value || ''}>
                                        <SelectTrigger id="scheduleTimezone">
                                            <SelectValue placeholder="Select timezone"/>
                                        </SelectTrigger>
                                        <SelectContent className="max-h-60">
                                            {timezones.map(tz => <SelectItem key={tz} value={tz}>{tz}</SelectItem>)}
                                        </SelectContent>
                                    </Select>
                                )}
                            />
                            {errors.scheduleTimezone && <p className="text-sm text-destructive">{errors.scheduleTimezone.message}</p>}
                        </div>
                    </div>

                    {scheduleType === 'one-time' && (
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                            <div className="space-y-2">
                                <Label htmlFor="scheduleRunAtDate">Run Date</Label>
                                <Controller
                                name="scheduleRunAtDate"
                                control={control}
                                render={({ field }) => (
                                    <Popover>
                                    <PopoverTrigger asChild>
                                        <Button
                                        variant={"outline"}
                                        className={cn(
                                            "w-full justify-start text-left font-normal",
                                            !field.value && "text-muted-foreground",
                                            errors.scheduleRunAtDate ? "border-destructive" : ""
                                        )}
                                        >
                                        <CalendarClock className="mr-2 h-4 w-4" />
                                        {field.value ? format(new Date(field.value), "PPP") : <span>Pick a date</span>}
                                        </Button>
                                    </PopoverTrigger>
                                    <PopoverContent className="w-auto p-0">
                                        <Calendar
                                        mode="single"
                                        selected={field.value ? new Date(field.value) : undefined}
                                        onSelect={(date) => field.onChange(date ? format(date, 'yyyy-MM-dd') : '')}
                                        initialFocus
                                        />
                                    </PopoverContent>
                                    </Popover>
                                )}
                                />
                                {errors.scheduleRunAtDate && <p className="text-sm text-destructive">{errors.scheduleRunAtDate.message}</p>}
                            </div>
                            <div className="space-y-2">
                                <Label htmlFor="scheduleRunAtTime">Run Time (HH:MM)</Label>
                                <Controller name="scheduleRunAtTime" control={control} render={({ field }) => (<Input id="scheduleRunAtTime" type="time" className={`${errors.scheduleRunAtTime ? 'border-destructive' : ''}`} {...field} value={field.value || ''}/>)} />
                                {errors.scheduleRunAtTime && <p className="text-sm text-destructive">{errors.scheduleRunAtTime.message}</p>}
                            </div>
                        </div>
                    )}

                    {scheduleType === 'recurring' && (
                        <div className="space-y-2">
                            <Label htmlFor="scheduleCronExpression" className="flex items-center">Cron Expression <TooltipProvider><Tooltip><TooltipTrigger asChild><HelpCircle className="h-4 w-4 ml-1.5 text-muted-foreground cursor-help" /></TooltipTrigger><TooltipContent side="top"><p className="max-w-xs">Standard cron format. E.g., "0 0 * * *" for daily at midnight. Use <a href="https://crontab.guru/" target="_blank" rel="noopener noreferrer" className="text-accent underline">crontab.guru</a> to build expressions.</p></TooltipContent></Tooltip></TooltipProvider></Label>
                            <Controller name="scheduleCronExpression" control={control} render={({ field }) => (<Input id="scheduleCronExpression" placeholder="e.g., 0 0 * * *" className={`${errors.scheduleCronExpression ? 'border-destructive' : ''}`} {...field} value={field.value ?? ''}/>)} />
                            {errors.scheduleCronExpression && <p className="text-sm text-destructive">{errors.scheduleCronExpression.message}</p>}
                        </div>
                    )}
                </CardContent>
              )}
            </Card>


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
        </Card>
      </form>
    </AppShell>
  );
}

    