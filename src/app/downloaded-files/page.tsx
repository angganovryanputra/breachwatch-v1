
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
import { Trash2, Search, Filter, FileQuestion, HardDriveDownload, Eye, FileDown, ExternalLink } from 'lucide-react';
import type { DownloadedFileEntry } from '@/types';
import { DOWNLOADED_FILES_STORAGE_KEY, FILE_TYPE_EXTENSIONS } from '@/lib/constants';
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

const ITEMS_PER_PAGE = 10;

export default function DownloadedFilesPage() {
  const [downloadedFiles, setDownloadedFiles] = useState<DownloadedFileEntry[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [currentPage, setCurrentPage] = useState(1);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterFileType, setFilterFileType] = useState<string>('all');
  const { toast } = useToast();

  useEffect(() => {
    try {
      const storedFilesRaw = localStorage.getItem(DOWNLOADED_FILES_STORAGE_KEY);
      if (storedFilesRaw) {
        const parsedFiles: DownloadedFileEntry[] = JSON.parse(storedFilesRaw);
        // Sort by downloadedAt descending
        parsedFiles.sort((a, b) => parseISO(b.downloadedAt).getTime() - parseISO(a.downloadedAt).getTime());
        setDownloadedFiles(parsedFiles);
      }
    } catch (error) {
      console.error("Error loading downloaded files from localStorage:", error);
      toast({
        title: "Error Loading Files",
        description: "Could not retrieve downloaded files. See console for details.",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  }, [toast]);

  const handleDelete = (id: string) => {
    const updatedFiles = downloadedFiles.filter(item => item.id !== id);
    setDownloadedFiles(updatedFiles);
    localStorage.setItem(DOWNLOADED_FILES_STORAGE_KEY, JSON.stringify(updatedFiles));
    toast({ title: "File Record Deleted", description: `Record for file ID ${id} has been removed from this list.` });
  };
  
  const handleSimulatedDownload = (fileUrl: string) => {
     toast({
        title: "Download Simulation",
        description: `This would typically initiate a download for: ${fileUrl}. In this demo, no actual download occurs.`,
      });
      // In a real app, this might open a new tab or trigger a browser download
      window.open(fileUrl, '_blank');
  };

  const filteredData = useMemo(() => {
    return downloadedFiles
      .filter(item => {
        const searchTermLower = searchTerm.toLowerCase();
        return (
          item.sourceUrl.toLowerCase().includes(searchTermLower) ||
          item.fileUrl.toLowerCase().includes(searchTermLower) ||
          item.keywords.some(kw => kw.toLowerCase().includes(searchTermLower))
        );
      })
      .filter(item => filterFileType === 'all' || item.fileType === filterFileType);
  }, [downloadedFiles, searchTerm, filterFileType]);

  const totalPages = Math.ceil(filteredData.length / ITEMS_PER_PAGE);
  const paginatedData = filteredData.slice(
    (currentPage - 1) * ITEMS_PER_PAGE,
    currentPage * ITEMS_PER_PAGE
  );

  const uniqueFileTypes = useMemo(() => {
    const types = new Set(downloadedFiles.map(item => item.fileType));
    return ['all', ...Array.from(types)];
  }, [downloadedFiles]);


  if (isLoading) {
    return (
      <AppShell>
        <div className="flex items-center justify-center h-full">
          <HardDriveDownload className="h-12 w-12 animate-pulse text-accent" />
          <p className="ml-4 text-xl">Loading downloaded files...</p>
        </div>
      </AppShell>
    );
  }

  return (
    <AppShell>
      <Card className="shadow-xl">
        <CardHeader>
          <CardTitle className="text-2xl flex items-center">
            <HardDriveDownload className="h-7 w-7 mr-2 text-accent" />
            Processed & Downloaded Files
          </CardTitle>
          <CardDescription>
            List of files that have been processed for download from the dashboard. (Simulated downloads)
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="mb-6 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 items-end">
            <div className="relative col-span-1 sm:col-span-2 lg:col-span-1">
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
            
            {/* Placeholder for potential future advanced filters */}
            {/* <Button variant="outline" className="w-full sm:w-auto justify-start sm:justify-center">
              <Filter className="mr-2 h-4 w-4" />
              Advanced Filters
            </Button> */}
          </div>

          {paginatedData.length === 0 ? (
            <div className="text-center py-10">
              <FileQuestion className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
              <p className="text-xl font-semibold">No Downloaded Files Found.</p>
              <p className="text-muted-foreground">
                {downloadedFiles.length > 0 ? "Try adjusting your search or filter criteria." : "Files processed for download from the dashboard will appear here."}
              </p>
            </div>
          ) : (
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-[50px]"></TableHead>
                  <TableHead>File URL</TableHead>
                  <TableHead>File Type</TableHead>
                  <TableHead>Original Source</TableHead>
                  <TableHead>Downloaded At</TableHead>
                  <TableHead>Keywords</TableHead>
                  <TableHead className="text-right w-[120px]">Actions</TableHead>
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
                             <a href={item.fileUrl} target="_blank" rel="noopener noreferrer" className="hover:underline text-accent hover:text-accent/80">
                              {item.fileUrl.split('/').pop() || item.fileUrl}
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
                     <TableCell className="max-w-xs truncate">
                       <TooltipProvider>
                        <Tooltip>
                          <TooltipTrigger asChild>
                            <a href={item.sourceUrl} target="_blank" rel="noopener noreferrer" className="hover:underline text-muted-foreground hover:text-accent/80">
                              {item.sourceUrl}
                            </a>
                          </TooltipTrigger>
                          <TooltipContent side="bottom">
                            <p>Original Source: {item.sourceUrl}</p>
                          </TooltipContent>
                        </Tooltip>
                      </TooltipProvider>
                    </TableCell>
                    <TableCell>{format(parseISO(item.downloadedAt), 'MMM dd, yyyy HH:mm')}</TableCell>
                    <TableCell className="max-w-sm">
                      <div className="flex flex-wrap gap-1">
                        {item.keywords.slice(0,3).map(kw => <Badge key={kw} variant="outline">{kw}</Badge>)}
                        {item.keywords.length > 3 && <Badge variant="outline">+{item.keywords.length - 3} more</Badge>}
                      </div>
                    </TableCell>
                    <TableCell className="text-right">
                      <TooltipProvider>
                        <Tooltip>
                          <TooltipTrigger asChild>
                            <Button variant="ghost" size="icon" onClick={() => handleSimulatedDownload(item.fileUrl)}>
                              <FileDown className="h-4 w-4" />
                            </Button>
                          </TooltipTrigger>
                          <TooltipContent><p>Download Again (Simulated)</p></TooltipContent>
                        </Tooltip>
                        <Tooltip>
                          <TooltipTrigger asChild>
                             <Button variant="ghost" size="icon" onClick={() => window.open(item.fileUrl, '_blank')}>
                              <ExternalLink className="h-4 w-4" />
                            </Button>
                          </TooltipTrigger>
                          <TooltipContent><p>Open File URL in New Tab</p></TooltipContent>
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
                              <AlertDialogTitle>Are you absolutely sure?</AlertDialogTitle>
                              <AlertDialogDescription>
                                This action will remove the record of this downloaded file from this list.
                                It does not delete the actual file from its source. This cannot be undone.
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
