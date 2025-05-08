
'use client';

import { AppShell } from '@/components/layout/app-shell';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
import { Badge } from '@/components/ui/badge';
import { BookOpen, Cog, SearchCode, DatabaseZap, AlertTriangle, PlayCircle, FileText, ListChecks, ShieldCheck, ArrowRightCircle, HardDrive, Terminal, Network } from 'lucide-react';
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
                A comprehensive guide to understanding, installing, and using the BreachWatch application for data exposure research.
              </CardDescription>
            </CardHeader>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center text-xl"><PlayCircle className="mr-2 h-6 w-6 text-primary" />Getting Started</CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
               {/* Installation Section */}
              <div>
                <h3 className="font-semibold text-lg mb-2 flex items-center"><HardDrive className="mr-2 h-5 w-5" />Local Installation</h3>
                 <p className="text-muted-foreground mb-4">
                  Follow these steps to set up and run the complete BreachWatch application (Frontend + Backend) on your local machine using Docker.
                </p>
                 <h4 className="font-medium text-base mb-1">1. Prerequisites:</h4>
                 <ul className="list-disc list-inside text-muted-foreground ml-4 space-y-1 text-sm mb-3">
                    <li><strong>Docker & Docker Compose:</strong> Required to run the backend, database, and cache containers. Install from <a href="https://docs.docker.com/get-docker/" target="_blank" rel="noopener noreferrer" className="text-accent hover:underline">Docker's official website</a>.</li>
                    <li><strong>Node.js & npm:</strong> Required for the Next.js frontend. Install from <a href="https://nodejs.org/" target="_blank" rel="noopener noreferrer" className="text-accent hover:underline">Node.js official website</a> (LTS version recommended).</li>
                    <li><strong>Git:</strong> Required to clone the repository.</li>
                     <li><strong>Shell Environment:</strong> A bash-compatible shell (like Git Bash on Windows, or standard Linux/macOS terminal) to run the setup script.</li>
                 </ul>

                 <h4 className="font-medium text-base mb-1">2. Clone the Repository:</h4>
                  <p className="text-muted-foreground text-sm mb-1">Open your terminal and run:</p>
                  <pre className="bg-muted p-3 my-2 rounded-md text-sm overflow-x-auto">
                    <code>git clone &lt;repository-url&gt; breachwatch{'\n'}cd breachwatch</code>
                  </pre>
                  <p className="text-muted-foreground text-sm mb-3">Replace `&lt;repository-url&gt;` with the actual URL of the Git repository.</p>

                 <h4 className="font-medium text-base mb-1">3. Configure Backend Environment:</h4>
                   <p className="text-muted-foreground text-sm mb-1">The backend requires an environment file (`.env`). Navigate to the backend directory and copy the example file:</p>
                  <pre className="bg-muted p-3 my-2 rounded-md text-sm overflow-x-auto">
                    <code>cd breachwatch_backend{'\n'}cp .env.example .env{'\n'}cd ..</code>
                  </pre>
                  <p className="text-muted-foreground text-sm mb-3">The default values in `.env.example` are suitable for the Docker setup. You might want to review `breachwatch_backend/.env` to set a custom `SECRET_KEY` or `REDIS_PASSWORD` for better security, even locally.</p>

                  <h4 className="font-medium text-base mb-1">4. Run the Local Setup Script:</h4>
                   <p className="text-muted-foreground text-sm mb-1">From the **project root directory** (`breachwatch`), execute the setup script:</p>
                   <pre className="bg-muted p-3 my-2 rounded-md text-sm overflow-x-auto">
                    <code>sh run-local.sh</code>
                   </pre>
                   <p className="text-muted-foreground text-sm mb-1">This script automates the following:</p>
                    <ul className="list-disc list-inside text-muted-foreground ml-4 space-y-1 text-sm mb-3">
                        <li>Checks for Docker and Node.js dependencies.</li>
                        <li>Confirms the backend `.env` file exists (it might create it from the example if missing, although step 3 is recommended).</li>
                        <li>Starts the PostgreSQL database, Redis cache, and Python backend service using `docker-compose up --build -d`.</li>
                        <li>Installs frontend dependencies using `npm install`.</li>
                        <li>Starts the Next.js frontend development server (typically on port 9002).</li>
                    </ul>
                   <p className="text-muted-foreground text-sm mb-3">The first run might take some time as Docker images are downloaded and built.</p>

                   <h4 className="font-medium text-base mb-1">5. Access the Application:</h4>
                   <p className="text-muted-foreground text-sm mb-1">Once the script finishes, you can access:</p>
                    <ul className="list-disc list-inside text-muted-foreground ml-4 space-y-1 text-sm mb-3">
                       <li><strong>Frontend Application:</strong> <a href="http://localhost:9002" target="_blank" rel="noopener noreferrer" className="text-accent hover:underline">http://localhost:9002</a></li>
                       <li><strong>Backend API Root:</strong> <a href="http://localhost:8000" target="_blank" rel="noopener noreferrer" className="text-accent hover:underline">http://localhost:8000</a></li>
                       <li><strong>Backend API Docs (Swagger):</strong> <a href="http://localhost:8000/docs" target="_blank" rel="noopener noreferrer" className="text-accent hover:underline">http://localhost:8000/docs</a></li>
                    </ul>

                   <h4 className="font-medium text-base mb-1">6. Stopping the Application:</h4>
                    <p className="text-muted-foreground text-sm mb-1">Press `Ctrl+C` in the terminal where `run-local.sh` is running. The script is designed to trap this signal and execute `docker-compose down` to stop the backend, database, and cache containers gracefully.</p>


                 <h4 className="font-medium text-base mt-4 mb-1 flex items-center"><Network className="mr-2 h-5 w-5" /> Troubleshooting Common Issues:</h4>
                  <ul className="list-disc list-inside text-muted-foreground ml-4 space-y-1 text-sm mb-3">
                       <li><strong>NetworkError when fetching resource:</strong> This usually means the frontend cannot connect to the backend API.
                           <ul className="list-circle list-inside ml-6 space-y-1 text-xs">
                               <li>Verify the backend is running: `docker ps` should show `breachwatch_backend_service`, `breachwatch_db`, `breachwatch_redis` running. Check logs: `docker-compose logs -f backend`.</li>
                               <li>Verify `NEXT_PUBLIC_BACKEND_API_URL` in the frontend's `.env` file (if you created one) matches the backend URL (`http://localhost:8000` by default).</li>
                               <li>Check CORS configuration in `breachwatch_backend/breachwatch/main.py` allows the frontend origin (`http://localhost:9002`). The default setup should work locally.</li>
                           </ul>
                       </li>
                       <li><strong>Database/Redis Connection Errors in Backend Logs:</strong> Ensure the `db` and `redis` containers are healthy (`docker ps`). Check credentials and hostnames (`db`, `redis`) in `breachwatch_backend/.env` match the `docker-compose.yml` service names.</li>
                       <li><strong>Frontend Errors:</strong> Check the output of `npm run dev` (or the `frontend_dev.log` file created by `run-local.sh`) for build or runtime errors. Ensure `npm install` completed successfully.</li>
                   </ul>


              </div>

               <Separator />

              <div>
                <h3 className="font-semibold text-lg mb-2">Navigating the UI</h3>
                <p className="text-muted-foreground">
                  The application features a sidebar for navigation:
                </p>
                <ul className="list-disc list-inside text-muted-foreground ml-4 space-y-1 text-sm">
                  <li><strong>Dashboard:</strong> Displays files discovered by backend crawlers that are suspected to be part of a data breach.</li>
                  <li><strong>Downloaded Files:</strong> Lists metadata records for files processed and stored by the backend.</li>
                  <li><strong>Crawl Jobs:</strong> Monitor the status and results of backend crawl jobs.</li>
                  <li><strong>Settings:</strong> Configure parameters for new crawl jobs.</li>
                  <li><strong>Ethical Guidelines:</strong> Important information on responsible usage.</li>
                  <li><strong>Documentation:</strong> This current page.</li>
                  <li><strong>User Management (Admin only):</strong> Manage user roles and statuses.</li>
                   <li><strong>User Profile & Preferences:</strong> Manage your own profile and application settings.</li>
                </ul>
              </div>
            </CardContent>
          </Card>

          {/* Workflow Section */}
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
                  Users define crawl parameters on the <Link href="/settings" className="text-accent hover:underline">Settings</Link> page, including:
                </p>
                <ul className="list-disc list-inside text-muted-foreground ml-12 space-y-1 text-sm">
                  <li>Keywords, File Extensions, Seed URLs, Search Dorks</li>
                  <li>Crawl Depth, Request Delay, User Agent</li>
                   <li>Scheduling options (one-time or recurring).</li>
                </ul>
                <div className="text-muted-foreground pl-8 mt-1 text-sm">
                  <Badge variant="outline" className="border-accent text-accent mr-1">Action:</Badge>
                  <span>Saving settings initiates a new crawl job on the backend.</span>
                </div>
              </div>

              <Separator />

              <div className="space-y-2">
                <h4 className="font-medium text-lg flex items-center">
                  <span className="bg-primary text-primary-foreground rounded-full h-6 w-6 flex items-center justify-center text-sm mr-2">2</span>
                  Crawl Job Execution (Backend)
                </h4>
                <p className="text-muted-foreground pl-8">
                  The Python backend receives the job configuration and starts processing:
                </p>
                 <ul className="list-disc list-inside text-muted-foreground ml-12 space-y-1 text-sm">
                   <li>Job status changes: `pending` -> `running`.</li>
                   <li>**URL Collection:** Gathers starting points from Seed URLs and Search Dork results.</li>
                   <li>**Deep Crawling:** Recursively follows links from collected URLs up to the specified depth, respecting politeness settings (delay, concurrency, robots.txt if enabled).</li>
                   <li>**File Identification & Analysis:** Fetches content, identifies file types, checks against target extensions, and matches keywords in metadata/content.</li>
                   <li>**Downloading & Storage:** Downloads relevant files matching criteria to the server's local storage (`breachwatch_backend/data/downloaded_files/[job_id]/`).</li>
                   <li>**Database Recording:** Stores metadata about the job and each downloaded file (URLs, type, keywords, timestamps, local path, size, checksum, etc.) in the PostgreSQL database.</li>
                   <li>**Completion:** Updates job status to `completed`, `completed_empty`, or `failed`. Handles rescheduling for recurring jobs.</li>
                </ul>
              </div>

              <Separator />

               <div className="space-y-2">
                <h4 className="font-medium text-lg flex items-center">
                  <ListChecks className="mr-2 h-5 w-5 text-primary" />
                  <span className="bg-primary text-primary-foreground rounded-full h-6 w-6 flex items-center justify-center text-sm mr-2">3</span>
                  Monitoring & Review (Frontend)
                </h4>
                <p className="text-muted-foreground pl-8">
                  The frontend allows users to:
                </p>
                 <ul className="list-disc list-inside text-muted-foreground ml-12 space-y-1 text-sm">
                   <li>View discovered files potentially related to breaches on the <Link href="/dashboard" className="text-accent hover:underline">Dashboard</Link>.</li>
                   <li>See a complete list of all processed/downloaded file records on the <Link href="/downloaded-files" className="text-accent hover:underline">Downloaded Files</Link> page.</li>
                   <li>Track the status, progress, and settings of active and past jobs on the <Link href="/jobs" className="text-accent hover:underline">Crawl Jobs</Link> page.</li>
                   <li>Manage jobs (stop, delete, run manually) and file records.</li>
                 </ul>
              </div>
            </CardContent>
          </Card>

          {/* Data Model Section */}
           <Card>
            <CardHeader>
              <CardTitle className="flex items-center text-xl"><FileText className="mr-2 h-6 w-6 text-primary" />Data Model Overview</CardTitle>
               <CardDescription>Key tables in the PostgreSQL database managed by the backend.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <ul className="list-disc list-inside text-muted-foreground ml-4 space-y-2 text-sm">
                <li>
                  <strong>`crawl_jobs` Table:</strong> Stores information about each crawl task, including its unique ID, name, status (`pending`, `running`, `completed`, etc.), configuration settings (keywords, extensions, URLs, depth, schedule details), timestamps (`created_at`, `updated_at`, `last_run_at`, `next_run_at`), and a summary of results.
                </li>
                <li>
                  <strong>`downloaded_files` Table:</strong> Records metadata for each file identified and processed by a crawl job. Includes file ID, source URL, direct file URL, file type, keywords found, timestamps (`date_found`, `downloaded_at`), server-side `local_path`, file size, checksum, and a foreign key linking back to the `crawl_jobs` table.
                </li>
                <li>
                  <strong>`users` Table:</strong> Contains user account details like ID, email, hashed password, full name, role (`user` or `admin`), activation status, and timestamps.
                </li>
                 <li>
                  <strong>`user_preferences` Table:</strong> Stores user-specific settings (e.g., items per page), linked to the `users` table via the user ID.
                </li>
              </ul>
               <p className="text-xs text-muted-foreground pt-2 border-t mt-4">Refer to `breachwatch_backend/breachwatch/storage/models.py` for the detailed SQLAlchemy model definitions.</p>
            </CardContent>
          </Card>

          {/* Ethical Guidelines Link */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center text-xl"><ShieldCheck className="mr-2 h-6 w-6 text-primary" />Ethical Guidelines & Responsible Use</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-muted-foreground">
                Using BreachWatch comes with significant ethical and legal responsibilities. It is crucial to use this tool **only for legitimate research on publicly accessible data** and in compliance with all applicable laws and terms of service.
              </p>
              <p className="text-muted-foreground mt-2">
                Please review the detailed{' '}
                <Link href="/guidelines" className="text-accent hover:underline font-semibold">
                  Ethical Guidelines page
                </Link>
                {' '}thoroughly before initiating any crawls. Misuse can lead to severe consequences.
              </p>
            </CardContent>
          </Card>

          {/* Technology Stack Section */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center text-xl"><Terminal className="mr-2 h-6 w-6 text-primary" />Technology Stack</CardTitle>
            </CardHeader>
            <CardContent className="grid grid-cols-1 md:grid-cols-2 gap-6 text-sm">
               <div>
                 <h4 className="font-medium mb-1">Frontend:</h4>
                 <ul className="list-disc list-inside text-muted-foreground ml-4 space-y-1">
                  <li>Next.js (React Framework)</li>
                  <li>TypeScript</li>
                  <li>Tailwind CSS</li>
                  <li>Shadcn UI / Radix UI (Components)</li>
                   <li>React Hook Form / Zod (Forms & Validation)</li>
                 </ul>
               </div>
               <div>
                 <h4 className="font-medium mb-1">Backend:</h4>
                 <ul className="list-disc list-inside text-muted-foreground ml-4 space-y-1">
                   <li>Python</li>
                   <li>FastAPI (API Framework)</li>
                   <li>SQLAlchemy (ORM)</li>
                   <li>PostgreSQL (Database)</li>
                   <li>Pydantic (Data Validation)</li>
                   <li>Httpx (HTTP Client)</li>
                   <li>BeautifulSoup4 (HTML Parsing)</li>
                   <li>Passlib, python-jose (Authentication)</li>
                   <li>SlowAPI, FastAPI-Cache2 (Rate Limiting, Caching)</li>
                   <li>Redis (Cache Backend)</li>
                   <li>Docker / Docker Compose (Containerization)</li>
                 </ul>
               </div>
            </CardContent>
          </Card>

           {/* Future Development Section */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center text-xl"><ArrowRightCircle className="mr-2 h-6 w-6 text-primary" />Future Development Ideas</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-muted-foreground">
                Potential enhancements for BreachWatch:
              </p>
              <ul className="list-disc list-inside text-muted-foreground ml-4 space-y-1 text-sm mt-2">
                <li>Advanced content analysis (NLP/AI) for PII detection and risk scoring.</li>
                <li>Direct file preview within the application (for safe file types).</li>
                <li>Automated reporting features (PDF/CSV export).</li>
                <li>Enhanced notification system (in-app, email).</li>
                <li>Proxy/VPN management for crawling.</li>
                <li>More sophisticated task queue management (e.g., using Celery).</li>
                 <li>Integration with external threat intelligence feeds.</li>
                 <li>More granular RBAC and permissions.</li>
                 <li>Comprehensive test suite (unit, integration, e2e).</li>
              </ul>
            </CardContent>
          </Card>

          <div className="text-center text-sm text-muted-foreground py-4">
            Always conduct your research responsibly and ethically.
          </div>
        </div>
      </ScrollArea>
    </AppShell>
  );
}

    