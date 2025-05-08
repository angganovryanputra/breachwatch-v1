'use client';

import { useState, useEffect, useCallback, useMemo } from 'react';
import { AppShell } from '@/components/layout/app-shell';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import { RefreshCcw, GanttChartSquare, ServerCrash, Play, Pause, StopCircle, Eye, ChevronLeft, ChevronRight, Clock, CheckCircle, AlertCircle, XCircle, Loader2, Trash2, Files, Settings, CalendarClock, Repeat } from 'lucide-react';
import type { CrawlJob } from '@/types';
import { format, parseISO, formatDistanceToNow } from 'date-fns';
import { useToast } from "@/hooks/use-toast";
import { getCrawlJobs, stopCrawlJob, deleteCrawlJob, manuallyRunJob } from '@/services/breachwatch-api'; 
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import { Progress } from "@/components/ui/progress"; 
import Link from 'next/link';
import { ScrollArea, ScrollBar } from '@/components/ui/scroll-area';

const ITEMS_PER_PAGE = 10;

const getStatusBadgeVariant = (status: CrawlJob['status']): "default" | "secondary" | "destructive" | "outline" => {
  switch (status) {
    case 'completed':
      return 'default'; // Using Shadcn default (like primary)
    case 'running':
      return 'secondary'; // Active/in-progress
    case 'pending':
    case 'scheduled': // Group pending/scheduled visually
      return 'outline'; // Less prominent
    case 'failed':
    case 'stopping': // Group failure/stopping visually
      return 'destructive';
    case 'completed_empty':
      return 'outline'; // Less prominent, indicate completion but no results
    default:
      return 'outline';
  }
};

const getStatusIcon = (status: CrawlJob['status']): JSX.Element => {
  switch (status) {
    case 'completed':
      return <CheckCircle className="h-4 w-4 text-green-500" />;
    case 'running':
      return <Loader2 className="h-4 w-4 animate-spin text-blue-500" />;
    case 'pending':
      return <Clock className="h-4 w-4 text-yellow-500" />;
    case 'scheduled':
      return <CalendarClock className="h-4 w-4 text-purple-500" />;
    case 'failed':
      return <XCircle className="h-4 w-4 text-red-500" />;
    case 'stopping':
      return <StopCircle className="h-4 w-4 text-orange-600" />;
    case 'completed_empty':
        return <AlertCircle className="h-4 w-4 text-orange-500" />;
    default:
      return <Clock className="h-4 w-4 text-muted-foreground" />;
  }
};

// Helper to truncate arrays/strings for display
const truncateList = (list: string[] | undefined, maxItems: number = 3): string => {
    if (!list) return 'N/A';
    if (list.length <= maxItems) return list.join(', ');
    return `${list.slice(0, maxItems).join(', ')}, +${list.length - maxItems} more`;
}

export default function CrawlJobsPage() {
  const [jobs, setJobs] = useState<CrawlJob[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const [error, setError] = useState<string | null>(null);
  const { toast } = useToast();

  const fetchData = useCallback(async () => {
    // Only set refreshing state if not initially loading
    if(!isLoading) setIsRefreshing(true);
    setError(null);
    try {
      const data = await getCrawlJobs(0, 100); // Fetch a larger number initially
      data.sort((a, b) => parseISO(b.created_at).getTime() - parseISO(a.created_at).getTime());
      setJobs(data);
    } catch (err) {
      console.error("Failed to fetch crawl jobs:", err);
      setError(err instanceof Error ? err.message : 'Failed to load crawl jobs from backend.');
      toast({
        title: "Error Fetching Jobs",
        description: err instanceof Error ? err.message : "Could not load crawl jobs.",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  }, [toast, isLoading]); // Include isLoading

  useEffect(() => {
    setIsLoading(true);
    fetchData(); // Initial fetch
    const intervalId = setInterval(fetchData, 30000); // Refresh every 30 seconds
    return () => clearInterval(intervalId); // Cleanup interval on unmount
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // Empty dependency array ensures this runs only once on mount for initial load and interval setup


  const handleRefresh = () => {
    fetchData(); // Manual refresh
    if (!isRefreshing) {
        toast({ title: "Refreshing Jobs", description: "Fetching latest crawl job statuses..." });
    }
  };
  
  const handleStopJob = async (jobId: string) => {
    toast({ title: "Attempting to Stop Job", description: `Sending stop signal for job ${jobId}...`});
    try {
      const response = await stopCrawlJob(jobId);
      toast({ title: "Stop Signal Sent", description: response.message });
      fetchData(); // Refresh job list to reflect status change
    } catch (err) {
      console.error("Failed to stop job:", err);
      toast({
        title: "Error Stopping Job",
        description: err instanceof Error ? err.message : "Could not stop the job.",
        variant: "destructive",
      });
    }
  };

  const handleDeleteJob = async (jobId: string) => {
    toast({ title: "Deleting Job", description: `Attempting to delete job ${jobId}...`});
    try {
      await deleteCrawlJob(jobId);
      toast({ title: "Job Deleted", description: `Job ${jobId} and its associated data have been deleted.` });
      setJobs(prevJobs => prevJobs.filter(job => job.id !== jobId)); // Optimistic update
      // Adjust pagination if needed
      if (paginatedJobs.length === 1 && currentPage > 1) {
        setCurrentPage(currentPage - 1);
      }
    } catch (err) {
      console.error("Failed to delete job:", err);
      toast({
        title: "Error Deleting Job",
        description: err instanceof Error ? err.message : "Could not delete the job.",
        variant: "destructive",
      });
    }
  };

  const handleRunJobNow = async (jobId: string) => {
    toast({ title: "Triggering Manual Run", description: `Attempting to run job ${jobId} now...` });
    try {
      const updatedJob = await manuallyRunJob(jobId);
      toast({ title: "Job Run Triggered", description: `Job ${updatedJob.name || jobId} added to processing queue.` });
      fetchData(); // Refresh list
    } catch (err) {
       console.error("Failed to manually run job:", err);
       toast({
         title: "Error Running Job",
         description: err instanceof Error ? err.message : "Could not manually trigger the job run.",
         variant: "destructive",
       });
    }
  };


  const paginatedJobs = useMemo(() => {
    return jobs.slice(
      (currentPage - 1) * ITEMS_PER_PAGE,
      currentPage * ITEMS_PER_PAGE
    );
  }, [jobs, currentPage]);

  const totalPages = Math.ceil(jobs.length / ITEMS_PER_PAGE);

  if (isLoading && jobs.length === 0 && !error) {
    return (
      <AppShell>
        <div className="flex flex-col items-center justify-center h-full">
          <GanttChartSquare className="h-12 w-12 animate-pulse text-accent" />
          <p className="ml-4 text-xl mt-4">Loading crawl jobs...</p>
        </div>
      </AppShell>
    );
  }

  if (error && jobs.length === 0) {
    return (
      <AppShell>
        <div className="flex flex-col items-center justify-center h-full text-center">
          <ServerCrash className="h-16 w-16 text-destructive mb-4" />
          <h2 className="text-2xl font-semibold mb-2 text-destructive">Failed to Load Crawl Jobs</h2>
          <p className="text-muted-foreground mb-4 max-w-md">{error}</p>
          <Button onClick={handleRefresh} disabled={isRefreshing}>
            <RefreshCcw className={`mr-2 h-4 w-4 ${isRefreshing ? 'animate-spin' : ''}`} />
            Try Again
          </Button>
        </div>
      </AppShell>
    );
  }

  return (
    <AppShell>
      <Card className="shadow-xl">
        <CardHeader>
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
            <div>
              <CardTitle className="text-2xl flex items-center">
                <GanttChartSquare className="h-7 w-7 mr-2 text-accent" />
                Crawl Job Management
              </CardTitle>
              <CardDescription>
                Monitor and manage backend crawl jobs. New jobs are created from the Settings page. Data refreshes automatically.
              </CardDescription>
            </div>
            <Button onClick={handleRefresh} disabled={isRefreshing || isLoading} variant="outline">
              <RefreshCcw className={`mr-2 h-4 w-4 ${isRefreshing || isLoading ? 'animate-spin' : ''}`} />
              {isRefreshing || isLoading ? 'Refreshing...' : 'Refresh Now'}
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {paginatedJobs.length === 0 && !isLoading ? (
             <div className="text-center py-10 min-h-[300px] flex flex-col justify-center items-center">
              <GanttChartSquare className="mx-auto h-16 w-16 text-muted-foreground mb-4" />
              <p className="text-xl font-semibold">No Crawl Jobs Found.</p>
              <p className="text-muted-foreground">
                Create new crawl jobs from the <Link href="/settings" className="text-accent hover:underline">Settings</Link> page.
              </p>
            </div>
          ) : (
            <ScrollArea className="w-full whitespace-nowrap rounded-md border">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-[250px]">Name</TableHead>
                    <TableHead className="w-[150px]">Status</TableHead>
                    <TableHead className="text-center w-[100px]">Files Found</TableHead>
                    <TableHead className="w-[180px]">Created</TableHead>
                    <TableHead className="w-[180px]">Last Updated</TableHead>
                    <TableHead className="w-[180px]">Next Run</TableHead>
                    <TableHead className="w-[200px]">Settings Summary</TableHead>
                    <TableHead className="text-right w-[150px]">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {paginatedJobs.map((job) => (
                    <TableRow key={job.id} className="hover:bg-muted/50">
                      <TableCell className="font-medium max-w-[250px] truncate">
                        <TooltipProvider>
                          <Tooltip>
                            <TooltipTrigger asChild>
                               <Link href={`/dashboard?job_id=${job.id}`} className="hover:underline text-accent">
                                {job.name || `Job ${job.id.substring(0,8)}...`}
                               </Link>
                            </TooltipTrigger>
                            <TooltipContent side="bottom" align="start">
                               <p className="font-semibold">{job.name || `Job ID: ${job.id}`}</p>
                               <p className="text-xs text-muted-foreground">ID: {job.id}</p>
                               <p className="text-xs mt-1">Click to view discovered files for this job.</p>
                            </TooltipContent>
                          </Tooltip>
                        </TooltipProvider>
                      </TableCell>
                      <TableCell>
                        <TooltipProvider>
                          <Tooltip>
                             <TooltipTrigger asChild>
                                <Badge variant={getStatusBadgeVariant(job.status)} className="flex items-center gap-1.5 w-fit cursor-default">
                                  {getStatusIcon(job.status)}
                                  <span className="capitalize">{job.status.replace('_', ' ')}</span>
                                </Badge>
                            </TooltipTrigger>
                            <TooltipContent>
                              <p>Current job status: {job.status.replace('_', ' ')}</p>
                            </TooltipContent>
                          </Tooltip>
                        </TooltipProvider>
                         {(job.status === 'running') && (
                            <Progress value={undefined} className="h-1 w-full mt-1 bg-primary/20 animate-pulse" /> 
                         )}
                      </TableCell>
                      <TableCell className="text-center">
                        <TooltipProvider>
                          <Tooltip>
                            <TooltipTrigger asChild>
                              <span className="flex items-center justify-center">
                                <Files className="h-4 w-4 mr-1 text-muted-foreground"/>
                                {job.results_summary?.files_found ?? 0}
                              </span>
                            </TooltipTrigger>
                            <TooltipContent>
                              <p>{job.results_summary?.files_found ?? 0} files found by this job.</p>
                            </TooltipContent>
                          </Tooltip>
                        </TooltipProvider>
                      </TableCell>
                      <TableCell>
                        <TooltipProvider>
                          <Tooltip>
                            <TooltipTrigger>
                                <span className="text-xs">{formatDistanceToNow(parseISO(job.created_at), { addSuffix: true })}</span>
                            </TooltipTrigger>
                            <TooltipContent>
                                {format(parseISO(job.created_at), 'MMM dd, yyyy HH:mm:ss')}
                            </TooltipContent>
                          </Tooltip>
                        </TooltipProvider>
                      </TableCell>
                      <TableCell>
                        <TooltipProvider>
                          <Tooltip>
                            <TooltipTrigger>
                                <span className="text-xs">{formatDistanceToNow(parseISO(job.updated_at), { addSuffix: true })}</span>
                            </TooltipTrigger>
                            <TooltipContent>
                                {format(parseISO(job.updated_at), 'MMM dd, yyyy HH:mm:ss')}
                            </TooltipContent>
                          </Tooltip>
                        </TooltipProvider>
                      </TableCell>
                      <TableCell>
                         <TooltipProvider>
                          <Tooltip>
                            <TooltipTrigger>
                                <span className="text-xs">
                                    {job.status === 'scheduled' && job.next_run_at 
                                     ? formatDistanceToNow(parseISO(job.next_run_at), { addSuffix: true })
                                     : job.settings.schedule ? (job.settings.schedule.type === 'recurring' ? `Recurring (${job.settings.schedule.cronExpression || 'N/A'})` : 'One-time (Completed/Run)') : 'Not Scheduled'}
                                </span>
                            </TooltipTrigger>
                            <TooltipContent>
                                {job.status === 'scheduled' && job.next_run_at ? `Scheduled for: ${format(parseISO(job.next_run_at), 'MMM dd, yyyy HH:mm')}` :
                                 job.settings.schedule?.type === 'recurring' ? `Recurring schedule: ${job.settings.schedule.cronExpression}` : 
                                 job.settings.schedule?.type === 'one-time' ? `One-time job. Last run: ${job.last_run_at ? format(parseISO(job.last_run_at), 'PPp') : 'Never'}` :
                                 'Job is not scheduled.'}
                                {job.settings.schedule?.timezone && ` (${job.settings.schedule.timezone})`}
                            </TooltipContent>
                          </Tooltip>
                        </TooltipProvider>
                      </TableCell>
                      <TableCell className="max-w-[200px] truncate text-xs">
                          <TooltipProvider>
                            <Tooltip>
                                <TooltipTrigger asChild>
                                    <div className="flex items-center gap-1 text-muted-foreground cursor-default">
                                        <Settings className="h-3 w-3"/>
                                        <span>
                                            {job.settings.keywords.length} kw, {job.settings.file_extensions.length} ext, D:{job.settings.crawl_depth}
                                            {job.settings.schedule && <CalendarClock className="inline h-3 w-3 ml-1" />}
                                        </span>
                                    </div>
                                </TooltipTrigger>
                                <TooltipContent align="start">
                                    <p><strong>Keywords:</strong> {truncateList(job.settings.keywords)}</p>
                                    <p><strong>Extensions:</strong> {truncateList(job.settings.file_extensions)}</p>
                                    <p><strong>Depth:</strong> {job.settings.crawl_depth}</p>
                                    <p><strong>Delay:</strong> {job.settings.request_delay_seconds}s</p>
                                    {job.settings.custom_user_agent && <p><strong>User Agent:</strong> Custom</p>}
                                    {job.settings.schedule && <p><strong>Schedule:</strong> {job.settings.schedule.type === 'recurring' ? `Recurring (${job.settings.schedule.cronExpression})` : `One-time ${job.settings.schedule.run_at ? format(parseISO(job.settings.schedule.run_at), 'PPp') : '(Date N/A)'}`}{job.settings.schedule.timezone ? ` [${job.settings.schedule.timezone}]` : ''}</p>}
                                </TooltipContent>
                            </Tooltip>
                          </TooltipProvider>
                      </TableCell>
                      <TableCell className="text-right space-x-1">
                        <TooltipProvider>
                          {/* Run Now Button */}
                          {(job.status === 'completed' || job.status === 'failed' || job.status === 'completed_empty' || job.status === 'scheduled') && (
                             <AlertDialog>
                              <Tooltip>
                                <TooltipTrigger asChild>
                                  <AlertDialogTrigger asChild>
                                      <Button variant="ghost" size="icon" className="text-green-500 hover:text-green-400">
                                        <Play className="h-4 w-4" />
                                      </Button>
                                    </AlertDialogTrigger>
                                </TooltipTrigger>
                                <TooltipContent><p>Run Job Now</p></TooltipContent>
                              </Tooltip>
                              <AlertDialogContent>
                                <AlertDialogHeader>
                                  <AlertDialogTitle>Run Job Manually?</AlertDialogTitle>
                                  <AlertDialogDescription>
                                    This will immediately queue the job &quot;{job.name || job.id}&quot; to run with its saved settings, regardless of its current status or schedule. Are you sure?
                                  </AlertDialogDescription>
                                </AlertDialogHeader>
                                <AlertDialogFooter>
                                  <AlertDialogCancel>Cancel</AlertDialogCancel>
                                  <AlertDialogAction onClick={() => handleRunJobNow(job.id)} className="bg-green-600 hover:bg-green-700">
                                    Run Now
                                  </AlertDialogAction>
                                </AlertDialogFooter>
                              </AlertDialogContent>
                            </AlertDialog>
                          )}
                           {/* Stop Button */}
                           {(job.status === 'running' || job.status === 'pending' || job.status === 'scheduled') && (
                             <AlertDialog>
                                <Tooltip>
                                    <TooltipTrigger asChild>
                                     <AlertDialogTrigger asChild>
                                        <Button variant="ghost" size="icon" className="text-orange-500 hover:text-orange-400">
                                            <StopCircle className="h-4 w-4" />
                                        </Button>
                                      </AlertDialogTrigger>
                                    </TooltipTrigger>
                                    <TooltipContent><p>Stop Job</p></TooltipContent>
                                </Tooltip>
                                <AlertDialogContent>
                                    <AlertDialogHeader>
                                        <AlertDialogTitle>Stop Crawl Job?</AlertDialogTitle>
                                        <AlertDialogDescription>
                                            Are you sure you want to stop the job &quot;{job.name || job.id}&quot;? Running processes will be halted, and scheduled runs will be cancelled.
                                        </AlertDialogDescription>
                                    </AlertDialogHeader>
                                    <AlertDialogFooter>
                                        <AlertDialogCancel>Cancel</AlertDialogCancel>
                                        <AlertDialogAction onClick={() => handleStopJob(job.id)} className="bg-orange-600 hover:bg-orange-700">
                                            Stop Job
                                        </AlertDialogAction>
                                    </AlertDialogFooter>
                                </AlertDialogContent>
                             </AlertDialog>
                          )}
                           {/* Delete Button */}
                           <AlertDialog>
                            <Tooltip>
                                <TooltipTrigger asChild>
                                <AlertDialogTrigger asChild>
                                    <Button variant="ghost" size="icon" className="text-destructive hover:text-destructive/80 hover:bg-destructive/10">
                                    <Trash2 className="h-4 w-4" />
                                    </Button>
                                </AlertDialogTrigger>
                                </TooltipTrigger>
                                <TooltipContent><p>Delete Job</p></TooltipContent>
                            </Tooltip>
                            <AlertDialogContent>
                                <AlertDialogHeader>
                                <AlertDialogTitle>Delete Job Permanently?</AlertDialogTitle>
                                <AlertDialogDescription>
                                    This action will permanently delete the crawl job &quot;{job.name || job.id}&quot;, 
                                    all its associated downloaded file records from the database, and 
                                    all physical files downloaded by this job from the server. This cannot be undone.
                                </AlertDialogDescription>
                                </AlertDialogHeader>
                                <AlertDialogFooter>
                                <AlertDialogCancel>Cancel</AlertDialogCancel>
                                <AlertDialogAction onClick={() => handleDeleteJob(job.id)} className="bg-destructive hover:bg-destructive/90">
                                    Delete Job and All Data
                                </AlertDialogAction>
                                </AlertDialogFooter>
                            </AlertDialogContent>
                            </AlertDialog>
                        </TooltipProvider>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
              <ScrollBar orientation="horizontal" />
            </ScrollArea>
          )}

          {totalPages > 1 && (
            <div className="mt-6 flex items-center justify-between px-2">
              <Button
                variant="outline"
                onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                disabled={currentPage === 1}
                size="sm"
              >
                <ChevronLeft className="mr-1 h-4 w-4" />
                Previous
              </Button>
              <span className="text-sm text-muted-foreground">
                Page {currentPage} of {totalPages} ({jobs.length} total jobs)
              </span>
              <Button
                variant="outline"
                onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                disabled={currentPage === totalPages}
                size="sm"
              >
                Next
                <ChevronRight className="ml-1 h-4 w-4" />
              </Button>
            </div>
          )}
        </CardContent>
      </Card>
    </AppShell>
  );
}