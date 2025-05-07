
'use client';

import { AppShell } from '@/components/layout/app-shell';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
import { Badge } from '@/components/ui/badge';
import { BookOpen, Cog, SearchCode, DatabaseZap, AlertTriangle, PlayCircle, FileText, ListChecks, ShieldCheck, ArrowRightCircle } from 'lucide-react';
import Link from 'next/link';

export default function DocumentationPage() {
  return (
    <AppShell>
      <ScrollArea className="h-[calc(100vh-5rem)]">
        <div className="p-2 md:p-6 space-y-8">
          <Card className="shadow-xl">
            <CardHeader>
              <CardTitle className="text-3xl flex items-center font-semibold">
                <BookOpen className="h-8 w-8 mr-3 text-accent" />
                BreachWatch Documentation
              </CardTitle>
              <CardDescription className="text-lg">
                A comprehensive guide to understanding and using the BreachWatch application for data exposure research.
              </CardDescription>
            </CardHeader>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center text-xl"><PlayCircle className="mr-2 h-6 w-6 text-primary" />Getting Started</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <h3 className="font-semibold text-lg mb-2">1. Local Setup</h3>
                <p className="text-muted-foreground">
                  BreachWatch consists of a Next.js frontend and a Python (FastAPI) backend with a PostgreSQL database.
                  The easiest way to run the entire stack locally is using the provided shell script:
                </p>
                <pre className="bg-muted p-3 my-2 rounded-md text-sm overflow-x-auto">
                  <code>sh run-local.sh</code>
                </pre>
                <p className="text-muted-foreground">
                  This script will:
                </p>
                <ul className="list-disc list-inside text-muted-foreground ml-4 space-y-1">
                  <li>Check for Docker and Node.js dependencies.</li>
                  <li>Set up the backend environment file (`breachwatch_backend/.env`).</li>
                  <li>Start the PostgreSQL database and the Python backend service using Docker Compose.</li>
                  <li>Install frontend dependencies (npm install).</li>
                  <li>Start the Next.js frontend development server.</li>
                </ul>
                <p className="text-muted-foreground mt-2">
                  Ensure you have Docker, Docker Compose, Node.js, and npm installed on your system.
                  The frontend will typically run on `http://localhost:9002` and the backend API on `http://localhost:8000`.
                </p>
              </div>
              <div>
                <h3 className="font-semibold text-lg mb-2">2. Navigating the UI</h3>
                <p className="text-muted-foreground">
                  The application features a sidebar for navigation:
                </p>
                <ul className="list-disc list-inside text-muted-foreground ml-4 space-y-1">
                  <li><strong>Dashboard:</strong> Displays files discovered by backend crawlers that are suspected to be part of a data breach.</li>
                  <li><strong>File Records:</strong> Lists all files whose metadata has been processed and recorded by the backend, indicating they were downloaded or analyzed.</li>
                  <li><strong>Settings:</strong> Configure parameters for new crawl jobs.</li>
                  <li><strong>Ethical Guidelines:</strong> Important information on responsible usage.</li>
                  <li><strong>Documentation:</strong> This current page.</li>
                </ul>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center text-xl"><Cog className="mr-2 h-6 w-6 text-primary" />Core Workflow</CardTitle>
              <CardDescription>
                Understanding how BreachWatch identifies and processes potential data exposures.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="space-y-2">
                <h4 className="font-medium text-lg flex items-center">
                  <span className="bg-primary text-primary-foreground rounded-full h-6 w-6 flex items-center justify-center text-sm mr-2">1</span>
                  Configuration (Settings Page)
                </h4>
                <p className="text-muted-foreground pl-8">
                  Users start by defining the parameters for a crawl job on the <Link href="/settings" className="text-accent hover:underline">Settings</Link> page. This includes:
                </p>
                <ul className="list-disc list-inside text-muted-foreground ml-12 space-y-1">
                  <li><strong>Keywords:</strong> Specific terms to search for within file contents or metadata (e.g., "password", "NIK", "confidential").</li>
                  <li><strong>File Extensions:</strong> Target file types (e.g., "txt", "sql", "zip").</li>
                  <li><strong>Seed URLs:</strong> Initial URLs to begin crawling from (e.g., specific forums, paste sites).</li>
                  <li><strong>Search Dorks:</strong> Advanced search engine queries to find relevant publicly accessible files.</li>
                  <li><strong>Crawl Depth:</strong> How many links deep the crawler should follow from the seed URLs or dork results.</li>
                  <li><strong>Other Parameters:</strong> Such as request delays and whether to respect `robots.txt`.</li>
                </ul>
                <p className="text-muted-foreground pl-8 mt-1">
                  <Badge variant="outline" className="border-accent text-accent">Important:</Badge> Saving these settings initiates a new crawl job on the backend.
                </p>
              </div>

              <Separator />

              <div className="space-y-2">
                <h4 className="font-medium text-lg flex items-center">
                  <span className="bg-primary text-primary-foreground rounded-full h-6 w-6 flex items-center justify-center text-sm mr-2">2</span>
                  Crawl Job Creation
                </h4>
                <p className="text-muted-foreground pl-8">
                  When settings are saved, the frontend sends the configuration to the Python backend API.
                  The backend then creates a new `CrawlJob` entry in the PostgreSQL database with a "pending" status.
                </p>
              </div>
              
              <Separator />

              <div className="space-y-2">
                <h4 className="font-medium text-lg flex items-center">
                  <SearchCode className="mr-2 h-5 w-5 text-primary" />
                  <span className="bg-primary text-primary-foreground rounded-full h-6 w-6 flex items-center justify-center text-sm mr-2">3</span>
                  Backend Processing (Deep Crawling & Analysis)
                </h4>
                <p className="text-muted-foreground pl-8">
                  A background task (managed by FastAPI's BackgroundTasks or a Celery worker) picks up the "pending" crawl job. The backend then performs the following:
                </p>
                <ul className="list-disc list-inside text-muted-foreground ml-12 space-y-1">
                  <li><strong>Status Update:</strong> The job status is updated to "running".</li>
                  <li><strong>URL Collection:</strong>
                    <ul className="list-circle list-inside ml-6 space-y-1">
                        <li>Seed URLs are added to the processing queue.</li>
                        <li>Search dorks are executed using search engine drivers (e.g., DuckDuckGo) to find initial target URLs.</li>
                    </ul>
                  </li>
                  <li><strong>Recursive Crawling:</strong> For each URL:
                    <ul className="list-circle list-inside ml-6 space-y-1">
                        <li>The content is fetched respecting domain-specific rate limits and politeness (request delay, max concurrent requests).</li>
                        <li>If the content is HTML, links are extracted. New links are added to the queue to be processed up to the specified `crawl_depth`.</li>
                        <li>Visited URLs are tracked to avoid redundant processing.</li>
                    </ul>
                  </li>
                  <li><strong>File Identification:</strong>
                    <ul className="list-circle list-inside ml-6 space-y-1">
                        <li>The system attempts to identify the file type based on URL extension, `Content-Type` header, and potentially magic numbers (file content signature).</li>
                        <li>It checks if the identified file extension matches the target extensions configured for the job.</li>
                    </ul>
                  </li>
                  <li><strong>Keyword Matching:</strong>
                    <ul className="list-circle list-inside ml-6 space-y-1">
                        <li>If a file is a target type, its name and potentially its content (for text-based files) are scanned for the configured keywords.</li>
                    </ul>
                  </li>
                  <li><strong>File Downloading & Storage:</strong>
                    <ul className="list-circle list-inside ml-6 space-y-1">
                        <li>If a target file type contains relevant keywords (or matches other criteria), it is downloaded by the backend.</li>
                        <li>Downloaded files are stored in a designated local directory on the server (e.g., `breachwatch_backend/data/downloaded_files/[job_id]/filename`).</li>
                        <li>Metadata about the downloaded file (source URL, file URL, file type, keywords found, local path, size, checksum, etc.) is saved as a `DownloadedFile` record in the PostgreSQL database, linked to the `CrawlJob`.</li>
                    </ul>
                  </li>
                  <li><strong>Job Completion:</strong> Once all URLs in the queue are processed, the job status is updated to "completed" (or "completed_empty" if no files were found, or "failed" if an error occurred).</li>
                </ul>
                 <p className="text-muted-foreground pl-8 mt-1">
                  <Badge variant="outline" className="border-accent text-accent">Note:</Badge> The "deep crawler" functionality involves recursively following links found on pages, fetching content from those links, and repeating the identification and analysis process.
                </p>
              </div>
              
              <Separator />

              <div className="space-y-2">
                <h4 className="font-medium text-lg flex items-center">
                  <ListChecks className="mr-2 h-5 w-5 text-primary" />
                  <span className="bg-primary text-primary-foreground rounded-full h-6 w-6 flex items-center justify-center text-sm mr-2">4</span>
                  Viewing Results
                </h4>
                <p className="text-muted-foreground pl-8">
                  The frontend provides two main views for results:
                </p>
                <ul className="list-disc list-inside text-muted-foreground ml-12 space-y-1">
                  <li>
                    <strong>Dashboard Page:</strong> Displays a table of `DownloadedFile` entries that are considered potential breach indicators. This page typically fetches all `DownloadedFile` records and allows filtering and searching. It's the primary interface for reviewing findings.
                  </li>
                  <li>
                    <strong>Downloaded File Records Page:</strong> Shows a comprehensive list of all files whose metadata has been stored by the backend. This can include files that were downloaded for further analysis. Users can view details like local storage path (on the server), file size, and checksum.
                  </li>
                </ul>
                <p className="text-muted-foreground pl-8">
                    Users can refresh these pages to fetch the latest data from the backend. Actions like deleting a record (which removes the database entry but not necessarily the physical file) are available.
                </p>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center text-xl"><FileText className="mr-2 h-6 w-6 text-primary" />Data Model Overview</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <p className="text-muted-foreground">
                The backend uses PostgreSQL to store data. Key models include:
              </p>
              <ul className="list-disc list-inside text-muted-foreground ml-4 space-y-2">
                <li>
                  <strong>CrawlJob:</strong> Represents a single crawl task initiated by the user. Stores the configuration settings for that job (keywords, extensions, URLs, depth, etc.) and its current status (pending, running, completed, failed). Each job has a unique ID.
                </li>
                <li>
                  <strong>DownloadedFile:</strong> Represents a file that has been identified, downloaded, and/or analyzed by the crawler. It contains metadata such as:
                  <ul className="list-circle list-inside ml-6 space-y-1 mt-1">
                    <li>Original source URL (where the link to the file was found).</li>
                    <li>Direct file URL.</li>
                    <li>Identified file type.</li>
                    <li>Keywords found that triggered interest.</li>
                    <li>Timestamp of discovery (`date_found`) and download (`downloaded_at`).</li>
                    <li>Local path on the server where the file is stored.</li>
                    <li>File size and MD5 checksum.</li>
                    <li>A foreign key linking it back to the `CrawlJob` that found it.</li>
                  </ul>
                </li>
              </ul>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center text-xl"><ShieldCheck className="mr-2 h-6 w-6 text-primary" />Ethical Guidelines & Responsible Use</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-muted-foreground">
                It is crucial to use BreachWatch responsibly and ethically. Please review the detailed{' '}
                <Link href="/guidelines" className="text-accent hover:underline">
                  Ethical Guidelines
                </Link>
                {' '}page before conducting any crawls. Misuse of this tool can have serious legal and ethical consequences.
              </p>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center text-xl"><DatabaseZap className="mr-2 h-6 w-6 text-primary" />Backend Technology Stack</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              <p className="text-muted-foreground">The backend is built with:</p>
              <ul className="list-disc list-inside text-muted-foreground ml-4 space-y-1">
                <li><strong>Python:</strong> Primary programming language.</li>
                <li><strong>FastAPI:</strong> Modern, fast web framework for building APIs.</li>
                <li><strong>SQLAlchemy:</strong> SQL toolkit and Object-Relational Mapper (ORM) for database interaction.</li>
                <li><strong>PostgreSQL:</strong> Robust open-source relational database.</li>
                <li><strong>Pydantic:</strong> Data validation and settings management.</li>
                <li><strong>Httpx:</strong> Asynchronous HTTP client for making web requests.</li>
                <li><strong>BeautifulSoup4:</strong> Library for parsing HTML and XML documents.</li>
                <li><strong>Docker & Docker Compose:</strong> For containerization and easy local deployment of the backend and database.</li>
              </ul>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center text-xl"><ArrowRightCircle className="mr-2 h-6 w-6 text-primary" />Future Development Considerations</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-muted-foreground">
                BreachWatch is an evolving tool. Potential future enhancements include:
              </p>
              <ul className="list-disc list-inside text-muted-foreground ml-4 space-y-1">
                <li>User authentication and authorization.</li>
                <li>Scheduled and recurring crawl jobs.</li>
                <li>Advanced content analysis using NLP/AI for PII detection and risk scoring.</li>
                <li>Direct file preview within the application (for safe file types).</li>
                <li>Automated reporting features.</li>
                <li>Enhanced notification system.</li>
                <li>Integration with proxy/VPN services for crawling.</li>
                <li>More robust error handling and retry mechanisms for crawling.</li>
                <li>A dedicated "Crawl Jobs" management page in the UI.</li>
              </ul>
              <p className="text-muted-foreground mt-2">
                Refer to the "Rekomendasi Pengembangan" section on the <Link href="/guidelines" className="text-accent hover:underline">Ethical Guidelines</Link> page for more ideas.
              </p>
            </CardContent>
          </Card>

          <div className="text-center text-sm text-muted-foreground py-4">
            Thank you for using BreachWatch. Always conduct your research responsibly.
          </div>
        </div>
      </ScrollArea>
    </AppShell>
  );
}

    