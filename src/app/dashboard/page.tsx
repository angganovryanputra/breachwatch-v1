

'use client';

import { useState, useEffect, useMemo } from 'react';
import { AppShell } from '@/components/layout/app-shell';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { FileTypeIcon } from '@/components/common/file-type-icon';
import { Eye, Trash2, RefreshCcw, FileDown, Filter, Search, AlertTriangle, FileQuestion, HardDriveDownload } from 'lucide-react';
import type { BreachData, DownloadedFileEntry } from '@/types';
import { MOCK_BREACH_DATA, DOWNLOADED_FILES_STORAGE_KEY, generateNewMockEntry } from '@/lib/constants';
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
import { ToastAction } from '@/components/ui/toast';


const ITEMS_PER_PAGE = 10;

export default function DashboardPage() {
  const [breachData, setBreachData] = useState<BreachData[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterFileType, setFilterFileType] = useState<string>('all');
  const [filterStatus, setFilterStatus] = useState<string>('all');
  const { toast } = useToast();

  useEffect(() => {
    // Simulate API call
    setTimeout(() => {
      setBreachData(MOCK_BREACH_DATA);
      setIsLoading(false);
    }, 1000);
  }, []);

  const handleRefresh = () => {
    setIsRefreshing(true);
    // Simulate API call to fetch new data
    setTimeout(() => {
      const newEntries: BreachData[] = Array.from({ length: 3 }, generateNewMockEntry);
      setBreachData(prevData => [...newEntries, ...prevData]);
      setIsRefreshing(false);
      toast({ title: "Data Refreshed", description: `${newEntries.length} new potential breaches found.` });
    }, 1500);
  };

  const handleDownload = (item: BreachData) => {
    toast({
      title: "Processing Download (Simulated)",
      description: `Adding ${item.fileUrl.split('/').pop() || 'file'} to downloaded list.`,
    });

    // Simulate processing and adding to a "downloaded" list in localStorage
    try {
      const existingDownloadsRaw = localStorage.getItem(DOWNLOADED_FILES_STORAGE_KEY);
      const existingDownloads: DownloadedFileEntry[] = existingDownloadsRaw ? JSON.parse(existingDownloadsRaw) : [];
      
      // Check if already downloaded
      if (existingDownloads.some(download => download.id === item.id)) {
        toast({
          title: "Already Processed",
          description: `${item.fileUrl.split('/').pop() || 'File'} is already in your downloaded list.`,
          variant: "default",
        });
        return;
      }

      const newDownloadEntry: DownloadedFileEntry = {
        ...item,
        downloadedAt: new Date().toISOString(),
      };
      
      const updatedDownloads = [newDownloadEntry, ...existingDownloads];
      localStorage.setItem(DOWNLOADED_FILES_STORAGE_KEY, JSON.stringify(updatedDownloads));

      toast({
        title: "File Processed for Download",
        description: `${item.fileUrl.split('/').pop() || 'File'} added to Downloaded Files page.`,
        action: <ToastAction altText="View Downloads" onClick={() => window.location.href = '/downloaded-files'}>View Downloads</ToastAction>,
      });

    } catch (error) {
      console.error("Failed to process download:", error);
      toast({
        title: "Error Processing Download",
        description: "Could not add file to the downloaded list. See console for details.",
        variant: "destructive",
      });
    }
  };

  const handleDelete = (id: string) => {
    setBreachData(prevData => prevData.filter(item => item.id !== id));
    toast({ title: "Item Removed from Dashboard", description: `Item with ID ${id} has been removed from this view.`, variant: "default" });
  };

  const filteredData = useMemo(() => {
    return breachData
      .filter(item => {
        const searchTermLower = searchTerm.toLowerCase();
        return (
          item.sourceUrl.toLowerCase().includes(searchTermLower) ||
          item.fileUrl.toLowerCase().includes(searchTermLower) ||
          item.keywords.some(kw => kw.toLowerCase().includes(searchTermLower))
        );
      })
      .filter(item => filterFileType === 'all' || item.fileType === filterFileType)
      .filter(item => filterStatus === 'all' || item.status === filterStatus);
  }, [breachData, searchTerm, filterFileType, filterStatus]);

  const totalPages = Math.ceil(filteredData.length / ITEMS_PER_PAGE);
  const paginatedData = filteredData.slice(
    (currentPage - 1) * ITEMS_PER_PAGE,
    currentPage * ITEMS_PER_PAGE
  );

  const uniqueFileTypes = useMemo(() => {
    const types = new Set(MOCK_BREACH_DATA.map(item => item.fileType)); // Base on initial mock to keep consistent
    return ['all', ...Array.from(types)];
  }, []);

  const uniqueStatuses = useMemo(() => {
    const statuses = new Set(MOCK_BREACH_DATA.map(item => item.status).filter(Boolean) as string[]);  // Base on initial mock
    return ['all', ...Array.from(statuses)];
  }, []);

  if (isLoading && breachData.length === 0) {
    return (
      <AppShell>
        <div className="flex items-center justify-center h-full">
          <RefreshCcw className="h-12 w-12 animate-spin text-accent" />
          <p className="ml-4 text-xl">Loading breach data...</p>
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
                <AlertTriangle className="h-7 w-7 mr-2 text-accent" />
                Real-time Breach Dashboard
              </CardTitle>
              <CardDescription>
                Identified potential data breaches. Review and process for download.
              </CardDescription>
            </div>
            <Button onClick={handleRefresh} disabled={isRefreshing} variant="outline">
              <RefreshCcw className={`mr-2 h-4 w-4 ${isRefreshing ? 'animate-spin' : ''}`} />
              {isRefreshing ? 'Refreshing...' : 'Refresh Data'}
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <div className="mb-6 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 items-end">
            <div className="relative">
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

            <Select value={filterStatus} onValueChange={(value) => { setFilterStatus(value); setCurrentPage(1); }}>
              <SelectTrigger className="w-full">
                <SelectValue placeholder="Filter by Status" />
              </SelectTrigger>
              <SelectContent>
                {uniqueStatuses.map(status => (
                  <SelectItem key={status} value={status}>
                    {status === 'all' ? 'All Statuses' : status.charAt(0).toUpperCase() + status.slice(1)}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            
            <Button variant="outline" className="w-full sm:w-auto justify-start sm:justify-center">
              <Filter className="mr-2 h-4 w-4" />
              Advanced Filters
            </Button>
          </div>

          {paginatedData.length === 0 ? (
            <div className="text-center py-10">
              <FileQuestion className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
              <p className="text-xl font-semibold">No breaches found.</p>
              <p className="text-muted-foreground">Try adjusting your search or filter criteria, or check your settings. New data might be discovered upon refresh.</p>
            </div>
          ) : (
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-[50px]"></TableHead>
                  <TableHead>Source URL</TableHead>
                  <TableHead>File URL</TableHead>
                  <TableHead>File Type</TableHead>
                  <TableHead>Date Found</TableHead>
                  <TableHead>Keywords</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="text-right w-[150px]">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {paginatedData.map((item) => (
                  <TableRow key={item.id} className="hover:bg-muted/50">
                    <TableCell>
                      <FileTypeIcon fileTypeOrExt={item.fileType} />
                    </TableCell>
                    <TableCell className="max-w-xs truncate">
                       <TooltipProvider>
                        <Tooltip>
                          <TooltipTrigger asChild>
                            <a href={item.sourceUrl} target="_blank" rel="noopener noreferrer" className="hover:underline text-accent hover:text-accent/80">
                              {item.sourceUrl}
                            </a>
                          </TooltipTrigger>
                          <TooltipContent side="bottom">
                            <p>{item.sourceUrl}</p>
                          </TooltipContent>
                        </Tooltip>
                      </TooltipProvider>
                    </TableCell>
                    <TableCell className="max-w-xs truncate">
                      <TooltipProvider>
                        <Tooltip>
                          <TooltipTrigger asChild>
                             <a href={item.fileUrl} target="_blank" rel="noopener noreferrer" className="hover:underline text-accent hover:text-accent/80">
                              {item.fileUrl}
                            </a>
                          </TooltipTrigger>
                          <TooltipContent side="bottom">
                            <p>{item.fileUrl}</p>
                          </TooltipContent>
                        </Tooltip>
                      </TooltipProvider>
                    </TableCell>
                    <TableCell>
                      <Badge variant="secondary">{item.fileType.toUpperCase()}</Badge>
                    </TableCell>
                    <TableCell>{format(parseISO(item.dateFound), 'MMM dd, yyyy HH:mm')}</TableCell>
                    <TableCell className="max-w-sm">
                      <div className="flex flex-wrap gap-1">
                        {item.keywords.slice(0,3).map(kw => <Badge key={kw} variant="outline">{kw}</Badge>)}
                        {item.keywords.length > 3 && <Badge variant="outline">+{item.keywords.length - 3} more</Badge>}
                      </div>
                    </TableCell>
                    <TableCell>
                      {item.status && <Badge variant={item.status === 'new' ? 'default' : item.status === 'reviewed' ? 'outline' : 'destructive'}>
                        {item.status.charAt(0).toUpperCase() + item.status.slice(1)}
                      </Badge>}
                    </TableCell>
                    <TableCell className="text-right">
                      <TooltipProvider>
                        <Tooltip>
                          <TooltipTrigger asChild>
                            <Button variant="ghost" size="icon" onClick={() => alert(`Viewing details for ${item.fileUrl}`)}>
                              <Eye className="h-4 w-4" />
                            </Button>
                          </TooltipTrigger>
                          <TooltipContent><p>View Details</p></TooltipContent>
                        </Tooltip>
                        <Tooltip>
                          <TooltipTrigger asChild>
                            <Button variant="ghost" size="icon" onClick={() => handleDownload(item)}>
                              <HardDriveDownload className="h-4 w-4" />
                            </Button>
                          </TooltipTrigger>
                          <TooltipContent><p>Process for Download</p></TooltipContent>
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
                            <TooltipContent><p>Remove from Dashboard</p></TooltipContent>
                          </Tooltip>
                          <AlertDialogContent>
                            <AlertDialogHeader>
                              <AlertDialogTitle>Are you sure?</AlertDialogTitle>
                              <AlertDialogDescription>
                                This will remove the item from this dashboard view. It will not delete it from the "Downloaded Files" list if already processed.
                              </AlertDialogDescription>
                            </AlertDialogHeader>
                            <AlertDialogFooter>
                              <AlertDialogCancel>Cancel</AlertDialogCancel>
                              <AlertDialogAction onClick={() => handleDelete(item.id)} className="bg-destructive hover:bg-destructive/90">
                                Remove
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
              >
                Previous
              </Button>
              <span className="text-sm text-muted-foreground">
                Page {currentPage} of {totalPages}
              </span>
              <Button
                variant="outline"
                onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                disabled={currentPage === totalPages}
              >
                Next
              </Button>
            </div>
          )}
        </CardContent>
      </Card>
    </AppShell>
  );
}


    
