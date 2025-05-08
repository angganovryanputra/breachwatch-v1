
'use client';

import { useState, useEffect, useCallback, useMemo } from 'react';
import { AppShell } from '@/components/layout/app-shell';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import { RefreshCcw, GanttChartSquare, ServerCrash, Play, Pause, StopCircle, Eye, ChevronLeft, ChevronRight, Clock, CheckCircle, AlertCircle, XCircle, Loader2, Trash2 } from 'lucide-react';
import type { CrawlJob } from '@/types';
import { format, parseISO, formatDistanceToNow } from 'date-fns';
import { useToast } from "@/hooks/use-toast";
import { getCrawlJobs } from '@/services/breachwatch-api'; // Assuming deleteCrawlJob will be added to services
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
import { Progress } from "@/components/ui/progress"; // For potential progress display


const ITEMS_PER_PAGE = 10;

const getStatusBadgeVariant = (status: CrawlJob['status']): "default" | "secondary" | "destructive" | "outline" => {
  switch (status) {
    case 'completed':
      return 'default'; // Using primary color for completed
    case 'running':
      return 'secondary'; // A less prominent color for running
    case 'pending':
      return 'outline';
    case 'failed':
      return 'destructive';
    case 'completed_empty':
      return 'outline'; // Similar to pending, but distinct
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
    case 'failed':
      return <XCircle className="h-4 w-4 text-red-500" />;
    case 'completed_empty':
        return <AlertCircle className="h-4 w-4 text-orange-500" />;
    default:
      return <Clock className="h-4 w-4 text-muted-foreground" />;
  }
};


export default function CrawlJobsPage() {
  const [jobs, setJobs] = useState<CrawlJob[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const [error, setError] = useState<string | null>(null);
  const { toast } = useToast();

  const fetchData = useCallback(async () => {
    setIsRefreshing(true);
    setError(null);
    try {
      const data = await getCrawlJobs(0, 100); // Fetch a larger set for client-side pagination for now
      // Sort by creation date descending
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
  }, [toast]);

  useEffect(() => {
    setIsLoading(true);
    fetchData();
    // Optional: set up polling for job statuses
    const intervalId = setInterval(fetchData, 30000); // Refresh every 30 seconds
    return () => clearInterval(intervalId);
  }, [fetchData]);

  const handleRefresh = () => {
    fetchData();
    if (!isRefreshing) {
        toast({ title: "Refreshing Jobs", description: "Fetching latest crawl job statuses..." });
    }
  };

  // Placeholder for job actions - these would call backend APIs
  const handlePauseJob = (jobId: string) => {
    toast({ title: "Action Not Implemented", description: `Pausing job ${jobId} is not yet supported.`});
    console.log("Pause job:", jobId);
  };
  const handleResumeJob = (jobId: string) => {
    toast({ title: "Action Not Implemented", description: `Resuming job ${jobId} is not yet supported.`});
    console.log("Resume job:", jobId);
  };
  const handleStopJob = (jobId: string) => {
     toast({ title: "Action Not Implemented", description: `Stopping job ${jobId} is not yet supported.`});
    console.log("Stop job:", jobId);
  };
   const handleDeleteJob = (jobId: string) => {
    // TODO: Implement API call to delete job in services/breachwatch-api.ts and backend
    toast({ title: "Action Not Implemented", description: `Deleting job ${jobId} record is not yet supported.`});
    console.log("Delete job:", jobId);
    // Optimistically remove from UI or refetch after API call
    // setJobs(prevJobs => prevJobs.filter(job => job.id !== jobId));
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
                Monitor and manage backend crawl jobs. New jobs are created from the Settings page.
              </CardDescription>
            </div>
            <Button onClick={handleRefresh} disabled={isRefreshing || isLoading} variant="outline">
              <RefreshCcw className={`mr-2 h-4 w-4 ${isRefreshing || isLoading ? 'animate-spin' : ''}`} />
              {isRefreshing || isLoading ? 'Refreshing...' : 'Refresh Jobs'}
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {paginatedJobs.length === 0 && !isLoading ? (
             <div className="text-center py-10 min-h-[300px] flex flex-col justify-center items-center">
              <GanttChartSquare className="mx-auto h-16 w-16 text-muted-foreground mb-4" />
              <p className="text-xl font-semibold">No Crawl Jobs Found.</p>
              <p className="text-muted-foreground">
                Create new crawl jobs from the Settings page.
              </p>
            </div>
          ) : (
            <div className="overflow-x-auto rounded-md border">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Name</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Created</TableHead>
                    <TableHead>Last Updated</TableHead>
                    <TableHead>Total Keywords</TableHead>
                    <TableHead>Total File Exts</TableHead>
                    <TableHead>Depth</TableHead>
                    <TableHead className="text-right w-[180px]">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {paginatedJobs.map((job) => (
                    <TableRow key={job.id} className="hover:bg-muted/50">
                      <TableCell className="font-medium max-w-xs truncate">
                        <TooltipProvider>
                          <Tooltip>
                            <TooltipTrigger asChild>
                              <span>{job.name || `Job ${job.id.substring(0,8)}...`}</span>
                            </TooltipTrigger>
                            <TooltipContent side="bottom" className="max-w-md">
                               <p className="font-semibold">{job.name || `Job ID: ${job.id}`}</p>
                               <p className="text-xs text-muted-foreground">ID: {job.id}</p>
                            </TooltipContent>
                          </Tooltip>
                        </TooltipProvider>
                      </TableCell>
                      <TableCell>
                        <Badge variant={getStatusBadgeVariant(job.status)} className="flex items-center gap-1.5 w-fit">
                           {getStatusIcon(job.status)}
                           <span className="capitalize">{job.status.replace('_', ' ')}</span>
                        </Badge>
                         {job.status === 'running' && (
                            <Progress value={50} className="h-1 w-full mt-1 bg-primary/20" /> // Placeholder progress
                         )}
                      </TableCell>
                      <TableCell>
                        <TooltipProvider>
                          <Tooltip>
                            <TooltipTrigger>
                                {formatDistanceToNow(parseISO(job.created_at), { addSuffix: true })}
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
                                {formatDistanceToNow(parseISO(job.updated_at), { addSuffix: true })}
                            </TooltipTrigger>
                            <TooltipContent>
                                {format(parseISO(job.updated_at), 'MMM dd, yyyy HH:mm:ss')}
                            </TooltipContent>
                          </Tooltip>
                        </TooltipProvider>
                      </TableCell>
                      <TableCell className="text-center">{job.settings.keywords.length}</TableCell>
                      <TableCell className="text-center">{job.settings.file_extensions.length}</TableCell>
                      <TableCell className="text-center">{job.settings.crawl_depth}</TableCell>
                      <TableCell className="text-right space-x-1">
                        <TooltipProvider>
                          <Tooltip>
                            <TooltipTrigger asChild>
                              <Button variant="ghost" size="icon" onClick={() => alert(`View details for Job ID: ${job.id}`)} disabled>
                                <Eye className="h-4 w-4" />
                              </Button>
                            </TooltipTrigger>
                            <TooltipContent><p>View Details (Not Implemented)</p></TooltipContent>
                          </Tooltip>
                          {/* {job.status === 'running' && (
                            <Tooltip>
                                <TooltipTrigger asChild>
                                <Button variant="ghost" size="icon" onClick={() => handlePauseJob(job.id)} className="text-yellow-500 hover:text-yellow-400" disabled>
                                    <Pause className="h-4 w-4" />
                                </Button>
                                </TooltipTrigger>
                                <TooltipContent><p>Pause Job (Not Implemented)</p></TooltipContent>
                            </Tooltip>
                          )}
                          {job.status === 'pending' && ( // Or paused
                            <Tooltip>
                                <TooltipTrigger asChild>
                                <Button variant="ghost" size="icon" onClick={() => handleResumeJob(job.id)}  className="text-green-500 hover:text-green-400" disabled>
                                    <Play className="h-4 w-4" />
                                </Button>
                                </TooltipTrigger>
                                <TooltipContent><p>Resume/Start Job (Not Implemented)</p></TooltipContent>
                            </Tooltip>
                          )}
                           {(job.status === 'running' || job.status === 'pending') && (
                            <Tooltip>
                                <TooltipTrigger asChild>
                                <Button variant="ghost" size="icon" onClick={() => handleStopJob(job.id)} className="text-orange-500 hover:text-orange-400" disabled>
                                    <StopCircle className="h-4 w-4" />
                                </Button>
                                </TooltipTrigger>
                                <TooltipContent><p>Stop Job (Not Implemented)</p></TooltipContent>
                            </Tooltip>
                          )} */}
                           <AlertDialog>
                            <Tooltip>
                                <TooltipTrigger asChild>
                                <AlertDialogTrigger asChild>
                                    <Button variant="ghost" size="icon" className="text-destructive hover:text-destructive/80 hover:bg-destructive/10" disabled>
                                    <Trash2 className="h-4 w-4" />
                                    </Button>
                                </AlertDialogTrigger>
                                </TooltipTrigger>
                                <TooltipContent><p>Delete Job (Not Implemented)</p></TooltipContent>
                            </Tooltip>
                            <AlertDialogContent>
                                <AlertDialogHeader>
                                <AlertDialogTitle>Are you absolutely sure?</AlertDialogTitle>
                                <AlertDialogDescription>
                                    This action will attempt to delete the crawl job record and potentially associated data.
                                    This action cannot be undone. (Backend functionality for full deletion might be pending).
                                </AlertDialogDescription>
                                </AlertDialogHeader>
                                <AlertDialogFooter>
                                <AlertDialogCancel>Cancel</AlertDialogCancel>
                                <AlertDialogAction onClick={() => handleDeleteJob(job.id)} className="bg-destructive hover:bg-destructive/90">
                                    Delete Job Record
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
            </div>
          )}

          {totalPages > 1 && (
            <div className="mt-6 flex items-center justify-between">
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
                Page {currentPage} of {totalPages}
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

