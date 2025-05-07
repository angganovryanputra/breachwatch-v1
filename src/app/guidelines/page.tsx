
'use client';

import { AppShell } from '@/components/layout/app-shell';
import { EthicalDisclosure } from '@/components/common/ethical-disclosure';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Info, FileText, ShieldCheck, Users, Globe, Lightbulb, DatabaseZap, ArrowRightCircle, SearchCode, Workflow } from 'lucide-react';

export default function GuidelinesPage() {
  return (
    <AppShell>
      <div className="space-y-8">
        <Card className="shadow-xl">
          <CardHeader>
            <CardTitle className="text-2xl flex items-center">
              <Info className="h-7 w-7 mr-2 text-accent" />
              Ethical & Legal Guidelines for Using BreachWatch
            </CardTitle>
            <CardDescription>
              Understanding your responsibilities when using this tool for research purposes.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <p className="text-lg">
              BreachWatch is a powerful tool intended for legitimate research into publicly accessible data.
              Its purpose is to help identify potential data exposures for academic, security research, or public interest reporting.
              However, with great power comes great responsibility.
            </p>

            <div className="grid md:grid-cols-2 gap-6">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center text-xl"><FileText className="mr-2 h-5 w-5 text-primary" />Scope of Use</CardTitle>
                </CardHeader>
                <CardContent className="space-y-2 text-sm">
                  <p><strong>Public Data Only:</strong> Focus your research strictly on data that is demonstrably public. This means data that is accessible without authentication, hacking, or circumventing security measures.</p>
                  <p><strong>Authorized Access:</strong> If you are researching specific systems, ensure you have explicit, written authorization from the system owners.</p>
                  <p><strong>No Malicious Intent:</strong> This tool must not be used for any malicious activities, including but not limited to, unauthorized access, data theft, identity theft, or causing harm to individuals or organizations.</p>
                </CardContent>
              </Card>
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center text-xl"><ShieldCheck className="mr-2 h-5 w-5 text-primary" />Responsible Disclosure</CardTitle>
                </CardHeader>
                <CardContent className="space-y-2 text-sm">
                  <p><strong>Notify Owners:</strong> If you discover a sensitive data exposure, prioritize notifying the affected organization or data owner responsibly. Allow them reasonable time to address the issue before any public disclosure.</p>
                  <p><strong>Minimize Harm:</strong> Handle any discovered data with extreme care. Avoid downloading or storing sensitive PII unless absolutely necessary for your research and legally permissible. Anonymize or aggregate data where possible.</p>
                  <p><strong>Consult Experts:</strong> If unsure about the ethical or legal implications of a discovery, consult with legal counsel or ethics advisors before taking action.</p>
                </CardContent>
              </Card>
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center text-xl"><Users className="mr-2 h-5 w-5 text-primary" />Respect for Privacy</CardTitle>
                </CardHeader>
                <CardContent className="space-y-2 text-sm">
                  <p><strong>PII Handling:</strong> Be extremely cautious with Personally Identifiable Information (PII). Its collection, storage, and use are heavily regulated (e.g., GDPR, CCPA).</p>
                  <p><strong>Data Minimization:</strong> Only collect and retain data that is essential for your research. Securely delete any data that is no longer needed.</p>
                  <p><strong>Anonymity:</strong> While the tool may offer features for anonymity (e.g., Tor considerations), remember that true anonymity is difficult to achieve and does not absolve you of legal or ethical responsibilities.</p>
                </CardContent>
              </Card>
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center text-xl"><Globe className="mr-2 h-5 w-5 text-primary" />Legal Compliance</CardTitle>
                </CardHeader>
                <CardContent className="space-y-2 text-sm">
                  <p><strong>Know The Law:</strong> Familiarize yourself with relevant laws in your jurisdiction and the jurisdiction of the data/systems you are researching. This includes laws on computer fraud and abuse, data protection, and privacy.</p>
                  <p><strong>Terms of Service:</strong> Respect the Terms of Service of websites and platforms you interact with. Crawling or data extraction may be prohibited by some ToS.</p>
                  <p><strong>International Considerations:</strong> Data protection laws vary significantly across countries. Be mindful of cross-border data implications.</p>
                </CardContent>
              </Card>
            </div>
          </CardContent>
        </Card>
        
        <EthicalDisclosure />

        <Card className="shadow-lg">
          <CardHeader>
            <CardTitle className="text-2xl flex items-center">
              <Lightbulb className="h-7 w-7 mr-2 text-accent" />
              Rekomendasi Pengembangan (Further Development)
            </CardTitle>
            <CardDescription>
              Ideas for enhancing BreachWatch capabilities and user experience.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="grid md:grid-cols-2 gap-6">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center text-xl"><DatabaseZap className="mr-2 h-5 w-5 text-primary" />Backend Integration & Real Crawling</CardTitle>
                </CardHeader>
                <CardContent className="space-y-2 text-sm">
                  <p><strong>Python Backend:</strong> Develop the conceptualized Python backend for actual web crawling, dork execution, and file analysis. This is the most critical next step for real functionality.</p>
                  <p><strong>Task Queue:</strong> Implement a task queue (e.g., Celery with Redis/RabbitMQ) to manage crawling jobs asynchronously, allowing the UI to remain responsive.</p>
                  <p><strong>Database Storage:</strong> Use a robust database (e.g., PostgreSQL, MongoDB) to store findings, crawl metadata, and user settings instead of relying solely on browser localStorage.</p>
                   <p><strong>Persistent "Downloaded Files":</strong> Store downloaded file metadata in the backend database. The "Downloaded Files" page should then fetch from this database. Actual file storage could be local (server-side) or cloud-based (e.g., S3-compatible).</p>
                </CardContent>
              </Card>
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center text-xl"><ArrowRightCircle className="mr-2 h-5 w-5 text-primary" />Automation & Workflow</CardTitle>
                </CardHeader>
                <CardContent className="space-y-2 text-sm">
                  <p><strong>Scheduled Crawls:</strong> Allow users to schedule recurring crawls based on their settings.</p>
                  <p><strong>Automated File Processing:</strong> Once a file is identified, automatically queue it for download (to a secure server location) and basic metadata extraction (e.g., file size, content snippet for PII check).</p>
                  <p><strong>Notification System:</strong> Implement email or in-app notifications for new critical findings or completed crawls.</p>
                </CardContent>
              </Card>
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center text-xl"><SearchCode className="mr-2 h-5 w-5 text-primary" />Advanced Analysis & Features</CardTitle>
                </CardHeader>
                <CardContent className="space-y-2 text-sm">
                  <p><strong>Content Analysis (NLP/AI):</strong> Integrate Natural Language Processing (NLP) or GenAI models to analyze file contents for sensitive information (PII, keywords, context) beyond simple string matching. This can help score severity.</p>
                  <p><strong>Duplicate Detection:</strong> Implement mechanisms to identify and flag duplicate files or data entries.</p>
                  <p><strong>IOC Extraction:</strong> Automatically extract Indicators of Compromise (IOCs) like IP addresses, domains, hashes from identified files.</p>
                  <p><strong>Reporting:</strong> Allow users to generate reports (CSV, PDF) of their findings.</p>
                </CardContent>
              </Card>
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center text-xl"><Workflow className="mr-2 h-5 w-5 text-primary" />User Experience & Security</CardTitle>
                </CardHeader>
                <CardContent className="space-y-2 text-sm">
                  <p><strong>User Authentication:</strong> Implement user accounts to save settings and results server-side.</p>
                  <p><strong>Role-Based Access Control (RBAC):</strong> If multiple users are envisioned, implement RBAC for different levels of access.</p>
                  <p><strong>Dark Web Monitoring Integration (Advanced):</strong> Explore possibilities of integrating with services that monitor dark web forums/marketplaces for mentions of targeted keywords or domains (requires careful ethical and legal consideration).</p>
                  <p><strong>Proxy/VPN Integration:</strong> Allow configuration of proxies or VPNs for crawling to enhance anonymity and bypass some IP-based restrictions (again, with ethical use reminders).</p>
                </CardContent>
              </Card>
            </div>
            <p className="text-sm text-muted-foreground pt-4 border-t mt-6">
              These recommendations aim to transform BreachWatch from a conceptual UI into a fully functional and robust data breach monitoring and research platform. Prioritization should be based on core functionality (backend crawling) first.
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Project Structure & Conceptual Python Outline (For User)</CardTitle>
            <CardDescription>This section is a conceptual guide for the Python backend requested by the user, not implemented in this Next.js frontend.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4 text-sm">
            <div>
              <h3 className="font-semibold text-base mb-2">Suggested Project Directory Layout:</h3>
              <pre className="bg-muted p-3 rounded-md text-xs overflow-x-auto">
{`breachwatch_backend/
├── breachwatch/
│   ├── __init__.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── crawler.py        # Core crawling logic
│   │   ├── file_identifier.py # File type and content analysis
│   │   ├── keyword_matcher.py # Keyword matching logic
│   │   └── downloader.py     # File download utilities (server-side)
│   ├── strategies/
│   │   ├── __init__.py
│   │   ├── search_engine_driver.py  # Search engine dork execution
│   │   ├── direct_probe.py   # Direct URL probing
│   │   └── recursive.py      # Recursive link following
│   ├── api/                  # FastAPI or Flask API endpoints
│   │   ├── __init__.py
│   │   ├── routes.py         # API routes for dashboard interaction
│   │   └── schemas.py        # Pydantic schemas for API
│   ├── tasks/                # Celery tasks for async operations
│   │   ├── __init__.py
│   │   └── crawl_tasks.py
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── config_loader.py
│   │   ├── logger.py
│   │   └── network.py        # HTTP request helpers, politeness
│   ├── storage/
│   │   ├── __init__.py
│   │   ├── database.py       # Database models and session management (e.g., SQLAlchemy)
│   │   └── file_handler.py   # Saving downloaded files to server/cloud
│   └── main.py               # Main script execution logic / API runner
├── config/
│   └── default_config.yml    # Configuration file
├── data/                     # For persistent data (if not using cloud storage)
│   ├── downloaded_files/     # Where downloaded files are stored (server-side)
│   └── metadata_db/          # SQLite DB file or similar if not using full RDBMS
├── tests/                    # Unit and integration tests
├── venv/                     # Virtual environment
├── requirements.txt          # Python dependencies
└── README.md                 # Project documentation
`}
              </pre>
            </div>
            <div>
              <h3 className="font-semibold text-base mb-2">Conceptual Python Snippets (Illustrative):</h3>
              <p className="mb-1"><strong>Making a request (<code>requests</code>):</strong></p>
              <pre className="bg-muted p-3 rounded-md text-xs overflow-x-auto">
{`import requests

def fetch_url(url, timeout=10):
    try:
        response = requests.get(url, timeout=timeout, headers={'User-Agent': 'BreachWatchResearchBot/1.0'})
        response.raise_for_status()  # Raises HTTPError for bad responses (4XX or 5XX)
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return None`}
              </pre>
              <p className="mt-3 mb-1"><strong>Parsing links (<code>BeautifulSoup4</code>):</strong></p>
              <pre className="bg-muted p-3 rounded-md text-xs overflow-x-auto">
{`from bs4 import BeautifulSoup
import urllib.parse

def extract_links(html_content, base_url):
    soup = BeautifulSoup(html_content, 'html.parser')
    links = set()
    for a_tag in soup.find_all('a', href=True):
        href = a_tag['href']
        # Join relative URLs with base_url
        full_url = urllib.parse.urljoin(base_url, href)
        links.add(full_url)
    return links`}
              </pre>
              <p className="mt-3 mb-1"><strong>Checking file extensions:</strong></p>
              <pre className="bg-muted p-3 rounded-md text-xs overflow-x-auto">
{`def is_target_file(url, target_extensions):
    # target_extensions = ['.txt', '.csv', '.sql.gz']
    parsed_url = urllib.parse.urlparse(url)
    path = parsed_url.path.lower()
    for ext in target_extensions:
        if path.endswith(ext.lower()):
            return True
    return False`}
              </pre>
            </div>
             <div>
              <h3 className="font-semibold text-base mb-2">Challenges & Limitations:</h3>
              <ul className="list-disc pl-5 space-y-1">
                <li><strong>"Crawling the entire internet"</strong> is practically impossible due to its vastness, dynamic nature, and resource requirements. Focus is on targeted crawling via dorks and seed URLs.</li>
                <li><strong>Anti-bot measures:</strong> Websites employ techniques (CAPTCHAs, IP blocking, rate limiting) to prevent automated crawling. Requires robust error handling, user-agent rotation, and potentially proxy usage.</li>
                <li><strong>JavaScript-rendered content:</strong> Standard HTTP requests may not capture links embedded by JavaScript. Selenium or Playwright might be needed for specific targets, increasing complexity and resource use.</li>
                <li><strong>Ethical and Legal Boundaries:</strong> Constantly navigating what is permissible and ethical is crucial and challenging. Responsible disclosure protocols are paramount.</li>
                <li><strong>False Positives/Negatives:</strong> Keyword and extension matching can lead to incorrect identifications. Content analysis can help but is not foolproof.</li>
                <li><strong>Resource Intensive:</strong> Large-scale crawling and downloading consume significant bandwidth, CPU, and storage. Efficient coding and resource management are key.</li>
                <li><strong>Dynamic Content & Paywalls:</strong> Accessing content behind logins or paywalls is generally out of scope for public data research without authorization and adds significant complexity.</li>
              </ul>
            </div>
          </CardContent>
        </Card>
      </div>
    </AppShell>
  );
}

