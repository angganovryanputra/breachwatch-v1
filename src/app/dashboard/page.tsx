
'use client';

import { useState, useEffect, useMemo, useCallback } from 'react';
import { AppShell } from '@/components/layout/app-shell';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { FileTypeIcon } from '@/components/common/file-type-icon';
import { Eye, Trash2, RefreshCcw, Filter, Search, AlertTriangle, FileQuestion, ExternalLink, ServerCrash, ListChecks, Shapes, ChevronLeft, ChevronRight } from 'lucide-react';
import type { DownloadedFileEntry } from '@/types';
import { format, parseISO } from 'date-fns';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
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
import { useToast } from "@/hooks/use-toast";
import { getDownloadedFiles, deleteDownloadedFileRecord } from '@/services/breachwatch-api';
import { FILE_TYPE_EXTENSIONS } from '@/lib/constants';


const ITEMS_PER_PAGE = 10;

export default function DashboardPage() {
  const [downloadedFiles, setDownloadedFiles] = useState<DownloadedFileEntry[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterFileType, setFilterFileType] = useState<string>('all');
  const [error, setError] = useState<string | null>(null);
  const { toast } = useToast();

  const fetchData = useCallback(async () => {
    setIsRefreshing(true);
    setError(null);
    try {
      const data = await getDownloadedFiles(undefined, 0, 500); 
      data.sort((a, b) => parseISO(b.date_found).getTime() - parseISO(a.date_found).getTime());
      setDownloadedFiles(data);
    } catch (err) {
      console.error("Failed to fetch downloaded files:", err);
      setError(err instanceof Error ? err.message : 'Failed to load data from backend. Ensure the backend service is running.');
      toast({
        title: "Error Fetching Data",
        description: err instanceof Error ? err.message : "Could not load files from the backend.",
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
  }, [fetchData]);

  const handleRefresh = () => {
    fetchData();
    if (!isRefreshing) {
        toast({ title: "Data Refresh Requested", description: "Fetching latest files from the backend..." });
    }
  };
  
  const handleViewOriginalFile = (fileUrl: string) => {
    window.open(fileUrl, '_blank', 'noopener,noreferrer');
    toast({
      title: "Opening Original File URL",
      description: `Attempting to open: ${fileUrl}`,
    });
  };

  const handleDelete = async (id: string) => {
    const originalFile = downloadedFiles.find(item => item.id === id);
    setDownloadedFiles(prevData => prevData.filter(item => item.id !== id)); 
    try {
      await deleteDownloadedFileRecord(id);
      toast({ title: "File Record Deleted", description: `Record for file ID ${id} has been removed.` });
    } catch (err) {
      console.error("Failed to delete file record:", err);
      if (originalFile) setDownloadedFiles(prevData => [...prevData, originalFile].sort((a, b) => parseISO(b.date_found).getTime() - parseISO(a.date_found).getTime()));
      toast({
        title: "Error Deleting Record",
        description: err instanceof Error ? err.message : "Could not delete the file record from the backend.",
        variant: "destructive",
      });
    }
  };

  const filteredData = useMemo(() => {
    return downloadedFiles
      .filter(item => {
        const searchTermLower = searchTerm.toLowerCase();
        const keywordsMatch = item.keywords_found?.some(kw => kw.toLowerCase().includes(searchTermLower));
        const sourceUrlMatch = item.source_url?.toLowerCase().includes(searchTermLower);
        const fileUrlMatch = item.file_url?.toLowerCase().includes(searchTermLower);
        return (
          sourceUrlMatch ||
          fileUrlMatch ||
          keywordsMatch
        );
      })
      .filter(item => filterFileType === 'all' || item.file_type === filterFileType);
  }, [downloadedFiles, searchTerm, filterFileType]);

  const totalPages = Math.ceil(filteredData.length / ITEMS_PER_PAGE);
  const paginatedData = filteredData.slice(
    (currentPage - 1) * ITEMS_PER_PAGE,
    currentPage * ITEMS_PER_PAGE
  );

  const uniqueFileTypes = useMemo(() => {
    const types = new Set(downloadedFiles.map(item => item.file_type).filter(Boolean) as string[]);
    const allKnownTypes = Object.values(FILE_TYPE_EXTENSIONS).flat();
    const combinedTypes = new Set([...Array.from(types), ...allKnownTypes.filter(t => !types.has(t) && downloadedFiles.some(df => df.file_type && df.file_type.includes(t)))]);
    return ['all', ...Array.from(combinedTypes).sort()];
  }, [downloadedFiles]);

  const summaryStats = useMemo(() => {
    return {
      totalFiles: filteredData.length,
      uniqueTypesCount: uniqueFileTypes.length > 1 ? uniqueFileTypes.length -1 : 0, // -1 for 'all'
    };
  }, [filteredData, uniqueFileTypes]);


  if (isLoading && downloadedFiles.length === 0 && !error) {
    return (
      <AppShell>
        <div className="flex flex-col items-center justify-center h-full">
          <RefreshCcw className="h-12 w-12 animate-spin text-accent" />
          <p className="ml-4 text-xl mt-4">Loading discovered files from backend...</p>
        </div>
      </AppShell>
    );
  }
  
  if (error && downloadedFiles.length === 0) {
    return (
      <AppShell>
        <div className="flex flex-col items-center justify-center h-full text-center">
          <ServerCrash className="h-16 w-16 text-destructive mb-4" />
          <h2 className="text-2xl font-semibold mb-2 text-destructive">Failed to Load Data</h2>
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
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4 mb-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Discovered Files</CardTitle>
            <ListChecks className="h-5 w-5 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{summaryStats.totalFiles}</div>
            <p className="text-xs text-muted-foreground">files matching filters</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Unique File Types Found</CardTitle>
            <Shapes className="h-5 w-5 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{summaryStats.uniqueTypesCount}</div>
            <p className="text-xs text-muted-foreground">distinct types in dataset</p>
          </CardContent>
        </Card>
      </div>

      <Card className="shadow-xl">
        <CardHeader>
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
            <div>
              <CardTitle className="text-2xl flex items-center">
                <AlertTriangle className="h-7 w-7 mr-2 text-accent" />
                Discovered Files Dashboard
              </CardTitle>
              <CardDescription>
                Files identified by backend crawlers. Review and manage findings.
              </CardDescription>
            </div>
            <Button onClick={handleRefresh} disabled={isRefreshing || isLoading} variant="outline">
              <RefreshCcw className={`mr-2 h-4 w-4 ${isRefreshing || isLoading ? 'animate-spin' : ''}`} />
              {isRefreshing || isLoading ? 'Refreshing...' : 'Refresh Data'}
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <div className="mb-6 grid grid-cols-1 sm:grid-cols-2 gap-4 items-end">
            <div className="relative col-span-1 sm:col-span-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground" />
              <Input
                type="search"
                placeholder="Search URLs or keywords..."
                value={searchTerm}
                onChange={(e) => {
                  setSearchTerm(e.target.value);
                  setCurrentPage(1);
                }}
                className="pl-10 w-full"
              />
            </div>
            
            <Select value={filterFileType} onValueChange={(value) => { setFilterFileType(value); setCurrentPage(1); }}>
              <SelectTrigger className="w-full">
                <Filter className="mr-2 h-4 w-4 text-muted-foreground" />
                <SelectValue placeholder="Filter by File Type" />
              </SelectTrigger>
              <SelectContent>
                {uniqueFileTypes.map(type => (
                  <SelectItem key={type} value={type}>
                    {type === 'all' ? 'All File Types' : type.toUpperCase()}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {paginatedData.length === 0 && !isLoading ? (
            <div className="text-center py-10 min-h-[300px] flex flex-col justify-center items-center">
              <FileQuestion className="mx-auto h-16 w-16 text-muted-foreground mb-4" />
              <p className="text-xl font-semibold">No Files Found Matching Criteria.</p>
              <p className="text-muted-foreground">
                {downloadedFiles.length > 0 ? "Try adjusting your search or filter criteria." : "No files have been discovered by the backend crawlers yet, or there was an issue fetching data."}
              </p>
              {downloadedFiles.length === 0 && !error && (
                <Button onClick={handleRefresh} disabled={isRefreshing || isLoading} className="mt-6">
                    <RefreshCcw className={`mr-2 h-4 w-4 ${isRefreshing || isLoading ? 'animate-spin' : ''}`} />
                    Check for New Data
                </Button>
              )}
            </div>
          ) : (
          <div className="overflow-x-auto rounded-md border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-[50px] text-center"></TableHead>
                  <TableHead>Source URL</TableHead>
                  <TableHead>File URL</TableHead>
                  <TableHead>File Type</TableHead>
                  <TableHead>Date Found</TableHead>
                  <TableHead>Keywords</TableHead>
                  <TableHead>File Size</TableHead>
                  <TableHead className="text-right w-[120px]">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {paginatedData.map((item) => (
                  <TableRow key={item.id} className="hover:bg-muted/50">
                    <TableCell className="text-center">
                      <FileTypeIcon fileTypeOrExt={item.file_type || ""} />
                    </TableCell>
                    <TableCell className="max-w-xs truncate">
                       <TooltipProvider>
                        <Tooltip>
                          <TooltipTrigger asChild>
                            <a href={item.source_url} target="_blank" rel="noopener noreferrer" className="hover:underline text-accent hover:text-accent/80">
                              {item.source_url}
                            </a>
                          </TooltipTrigger>
                          <TooltipContent side="bottom" className="max-w-md">
                            <p>Source: {item.source_url}</p>
                          </TooltipContent>
                        </Tooltip>
                      </TooltipProvider>
                    </TableCell>
                    <TableCell className="max-w-xs truncate">
                      <TooltipProvider>
                        <Tooltip>
                          <TooltipTrigger asChild>
                             <a href={item.file_url} target="_blank" rel="noopener noreferrer" className="hover:underline text-accent hover:text-accent/80">
                              {item.file_url}
                            </a>
                          </TooltipTrigger>
                          <TooltipContent side="bottom" className="max-w-md">
                            <p>File: {item.file_url}</p>
                          </TooltipContent>
                        </Tooltip>
                      </TooltipProvider>
                    </TableCell>
                    <TableCell>
                      <Badge variant="secondary">{item.file_type?.toUpperCase() || 'N/A'}</Badge>
                    </TableCell>
                    <TableCell>{format(parseISO(item.date_found), 'MMM dd, yyyy HH:mm')}</TableCell>
                    <TableCell className="max-w-sm">
                      <div className="flex flex-wrap gap-1">
                        {item.keywords_found?.slice(0, 3).map(kw => <Badge key={kw} variant="outline" className="truncate max-w-[100px]">{kw}</Badge>)}
                        {item.keywords_found && item.keywords_found.length > 3 && (
                          <TooltipProvider>
                            <Tooltip>
                              <TooltipTrigger asChild>
                                <Badge variant="outline" className="cursor-help">+{item.keywords_found.length - 3} more</Badge>
                              </TooltipTrigger>
                              <TooltipContent side="top" className="max-w-xs">
                                <p className="text-sm text-popover-foreground">
                                  Additional keywords: {item.keywords_found.slice(3).join(', ')}
                                </p>
                              </TooltipContent>
                            </Tooltip>
                          </TooltipProvider>
                        )}
                        {(!item.keywords_found || item.keywords_found.length === 0) && <Badge variant="outline">N/A</Badge>}
                      </div>
                    </TableCell>
                    <TableCell>
                      {item.file_size_bytes != null ? `${(item.file_size_bytes / (1024*1024)).toFixed(2)} MB` : 'N/A'}
                    </TableCell>
                    <TableCell className="text-right">
                      <TooltipProvider>
                         <Tooltip>
                          <TooltipTrigger asChild>
                            <Button variant="ghost" size="icon" onClick={() => handleViewOriginalFile(item.file_url)}>
                              <ExternalLink className="h-4 w-4" />
                            </Button>
                          </TooltipTrigger>
                          <TooltipContent><p>Open Original File URL</p></TooltipContent>
                        </Tooltip>
                         <AlertDialog>
                          <Tooltip>
                            <TooltipTrigger asChild>
                               <AlertDialogTrigger asChild>
                                <Button variant="ghost" size="icon" className="text-destructive hover:text-destructive/80 hover:bg-destructive/10">
                                  <Trash2 className="h-4 w-4" />
                                </Button>
                              </AlertDialogTrigger>
                            </TooltipTrigger>
                            <TooltipContent><p>Delete Record</p></TooltipContent>
                          </Tooltip>
                          <AlertDialogContent>
                            <AlertDialogHeader>
                              <AlertDialogTitle>Are you sure?</AlertDialogTitle>
                              <AlertDialogDescription>
                                This will remove the record of this file from the BreachWatch database.
                                It does NOT delete the actual file from its original source URL or the server's local storage (if downloaded).
                              </AlertDialogDescription>
                            </AlertDialogHeader>
                            <AlertDialogFooter>
                              <AlertDialogCancel>Cancel</AlertDialogCancel>
                              <AlertDialogAction onClick={() => handleDelete(item.id)} className="bg-destructive hover:bg-destructive/90">
                                Delete Record
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

