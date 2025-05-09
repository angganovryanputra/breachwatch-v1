
import { SettingsFormData, NavItem } from '@/types';
import { LayoutDashboard, FileDown, Cog, Info, BookOpen, Users, UserCircle } from 'lucide-react';
import { format } from 'date-fns';

export const APP_NAME = 'BreachWatch';

export const NAV_LINKS: NavItem[] = [
  { title: 'Dashboard', href: '/dashboard', icon: LayoutDashboard, category: 'main' },
  { title: 'Downloaded Files', href: '/downloaded-files', icon: FileDown, category: 'main' },
  { title: 'Crawl Jobs', href: '/jobs', icon: Cog, category: 'main' }, // Changed from Settings to Cog (more appropriate for "Jobs")
  { title: 'Settings', href: '/settings', icon: Cog, category: 'main' }, // Kept Settings icon for actual settings page
  { title: 'Ethical Guidelines', href: '/guidelines', icon: Info, category: 'main' },
  { title: 'Documentation', href: '/documentation', icon: BookOpen, category: 'main' },
  { title: 'User Management', href: '/admin/users', icon: Users, adminOnly: true, category: 'main' }, // Admin only
  // Account related links could be grouped differently or stay in main
  { title: 'Profile', href: '/profile', icon: UserCircle, category: 'account' },
  { title: 'Preferences', href: '/profile/preferences', icon: UserCog, category: 'account'},
];

export const DEFAULT_SETTINGS: SettingsFormData = {
  keywords: 'password, secret, NIK, no_ktp, nama_lengkap, tanggal_lahir, email',
  fileExtensions: 'txt, csv, sql, json, env, bak, log, pdf, docx, xlsx',
  seedUrls: 'https://pastebin.com\nhttps://sso.ui.ac.id/\nhttps://sso.undip.ac.id/',
  searchDorks: 'site:pastebin.com "password"\nfiletype:sql site:go.id "database"\nintitle:"index of" "backup.zip" site:ac.id',
  crawlDepth: 1,
  respectRobotsTxt: true,
  requestDelay: 1.5,
  customUserAgent: '',
  maxResultsPerDork: 20,
  maxConcurrentRequestsPerDomain: 2,
  proxies: '', // Newline separated list of proxies
  scheduleEnabled: false,
  scheduleType: 'one-time',
  scheduleCronExpression: '0 0 * * *', // Default: daily at midnight
  scheduleRunAtDate: format(new Date(), 'yyyy-MM-dd'), // Default to today
  scheduleRunAtTime: '09:00', // Default to 9 AM
  scheduleTimezone: Intl.DateTimeFormat().resolvedOptions().timeZone || 'UTC',
};


// File type categories and their common extensions
export const FILE_TYPE_EXTENSIONS: Record<string, string[]> = {
  text: ["txt", "log", "csv", "md", "rtf", "tsv", "ini", "conf", "cfg", "pem", "key", "env"],
  json: ["json", "jsonl", "geojson"],
  database: ["sql", "db", "sqlite", "sqlite3", "mdb", "accdb", "dump", "kdbx"],
  archive: ["zip", "tar", "gz", "bz2", "7z", "rar", "tgz"],
  code: ["py", "js", "java", "c", "cpp", "cs", "php", "rb", "go", "html", "css", "sh", "ps1", "bat", "xml", "yaml", "yml"],
  spreadsheet: ["xls", "xlsx", "ods"],
  document: ["doc", "docx", "odt", "pdf", "ppt", "pptx", "odp"],
  config: ["config", "conf", "cfg", "ini", "xml", "yaml", "yml", "env", "pem", "key", "crt", "cer", "ovpn"],
  // Add more specific categories if needed
  image: ['png', 'jpg', 'jpeg', 'gif', 'svg', 'webp', 'bmp', 'tiff'],
  audio: ['mp3', 'wav', 'ogg', 'aac', 'flac', 'm4a'],
  video: ['mp4', 'mov', 'avi', 'mkv', 'webm', 'flv', 'wmv'],
  executable: ['exe', 'dmg', 'app', 'msi', 'deb', 'rpm'],
  font: ['ttf', 'otf', 'woff', 'woff2'],
  other: [], // Fallback category
};


export const ADVANCED_SEARCH_DORKS_ID = [
  // Specific Indonesian Government and Academic Domains
  'site:go.id intitle:"index of" "database" OR "backup" OR "confidential"',
  'site:ac.id filetype:sql OR filetype:csv "students" OR "mahasiswa" OR "nilai"',
  'site:go.id filetype:pdf "Rahasia Negara" OR "Sangat Rahasia"',
  'site:go.id inurl:admin OR inurl:login "password" OR "username"',
  'site:ac.id intitle:"Login" "default password"',
  'site:*.go.id intext:"Nomor Induk Kependudukan" OR intext:"NIK" filetype:xls OR filetype:xlsx OR filetype:csv',
  'site:*.ac.id intext:"data pribadi" OR intext:"biodata mahasiswa" filetype:pdf OR filetype:doc',
  'site:*.co.id intitle:"index of /" "backup.zip" OR "database.sql.gz"',
  'site:go.id inurl:/uploads/ "sensitif" OR "internal" filetype:docx OR filetype:xlsx',
  'site:ac.id inurl:/files/ "data_penelitian" OR "hasil_riset" ext:zip OR ext:rar',
  
  // Common Data Leak Patterns (Indonesia Context)
  'intext:"Powered by WHM" site:co.id "backup" OR "cpanel"',
  'intitle:"phpMyAdmin" intext:"Create new database" site:id',
  'inurl:/backup/ site:id filetype:zip OR filetype:tar.gz',
  'site:drive.google.com "PT *" OR "CV *" "database" OR "client_data" "Indonesia"',
  'site:trello.com "Internal Project" OR "Company Confidential" "Indonesia"',
  'site:*.firebaseio.com "users" OR "data" "Indonesia" -docs -support -firebase', // Check for open Firebase DBs
  'intext:"MongoDB server information" port:27017 -sharding site:id', // Exposed MongoDB
  'intext:"elastic search head" port:9200 site:id', // Exposed Elasticsearch
  'inurl:ftp site:go.id OR site:ac.id "confidential" OR "private"', // Exposed FTP servers
  'filetype:env DB_PASSWORD site:id -github.com -gitlab.com', // .env files with DB passwords

  // Dorks targeting specific potential vulnerabilities or misconfigurations
  'inurl:"/proc/self/cwd" site:id', // Path traversal
  'intitle:"index of /" "wp-config.php"', // Exposed WordPress config
  'intitle:"index of /" ".git" -github -gitlab', // Exposed .git directories
  'inurl:"/api/v1/users" site:id intitle:"Swagger UI" OR intitle:"API Documentation"', // Exposed user APIs
  'site:go.id intext:"API Key" OR intext:"Secret Key" filetype:json OR filetype:txt',
  'site:ac.id inurl:"_debugbar/open" OR inurl:"phpinfo.php"', // Debugging interfaces
  'filetype:log "Error:ORA-" OR "password" site:id', // Oracle DB errors or passwords in logs
  'inurl:"/admin/config.php" "DB_PASSWORD" site:co.id', // Admin config files
  'site:*.s3.amazonaws.com "indonesia" "backup" OR "database" OR "confidential"', // Public S3 buckets
  'site:storage.googleapis.com "indonesia" "data" OR "users" OR "private"', // Public Google Cloud Storage

  // More creative dorks for Indonesian context
  'intext:"Daftar Nama" AND intext:"NIK" filetype:xlsx OR filetype:pdf site:go.id', // List of names and NIKs
  'intext:"Data Karyawan" AND intext:"Gaji" filetype:csv OR filetype:xls site:co.id', // Employee data with salary
  'site:readthedocs.io "internal" "Indonesia" "API Key"', // Internal docs on ReadTheDocs
  'site:pastes.io OR site:paste.ee "Indonesia" "password" OR "database dump"', // Paste sites
  'inurl:"/uploads/ktp/" OR inurl:"/uploads/kk/" site:id', // Uploads of KTP/KK (ID cards)
  'filetype:log "login attempt failed" "admin" site:go.id OR site:ac.id', // Failed admin login attempts in logs
  'site:id intitle:"Rapat Internal" filetype:docx OR filetype:pdf "Notulen"', // Internal meeting notes
  'intext:"Surat Keputusan" AND intext:"Pengangkatan" filetype:pdf site:go.id', // Official appointment letters
  // Add up to 100 dorks here
];

export const ADVANCED_SEED_URLS_ID = [
    // Government Portals & Subdomains
    "https://*.go.id/", // Wildcard for all go.id subdomains (conceptual, actual crawling needs specific subdomains)
    "https://*.kemdikbud.go.id/",
    "https://*.kemenkeu.go.id/",
    "https://*.kominfo.go.id/",
    "https://*.bps.go.id/",
    "https://lpse.jakarta.go.id/", // Example e-procurement
    // Academic Institutions
    "https://*.ac.id/", // Wildcard for all ac.id subdomains
    "https://*.ui.ac.id/",
    "https://*.ugm.ac.id/",
    "https://*.itb.ac.id/",
    "https://*.unpad.ac.id/",
    "https://*.undip.ac.id/",
    // Indonesian Company Domains (Examples)
    "https://*.co.id/", // General Indonesian company domain
    // Specific well-known (but potentially sensitive, use ethically) domains for research could be listed if authorized
    // E-commerce, Financial Institutions, etc.
    // Paste Sites & Code Repositories (Often sources of leaks)
    "https://pastebin.com",
    "https://gist.github.com", // Search within Gist for Indonesian keywords
    "https://gitlab.com/explore", // Explore public projects
    // Cloud Storage (Conceptual - dorks are better for these)
    // Specific public S3 buckets or Google Cloud Storage URLs if known from other sources
    // Forum & Community Sites (Indonesia-specific if possible)
    "https://www.kaskus.co.id/", // Large Indonesian forum
    // File Sharing Services (use dorks to target Indonesian content)
    "https://docs.google.com/spreadsheets/", 
    "https://docs.google.com/document/",
    "https://drive.google.com/",
    // Job Portals & Professional Networks (for publicly exposed resumes/CVs)
    "https://www.jobstreet.co.id/",
    "https://id.linkedin.com/pub/dir/", // Public LinkedIn profiles (respect ToS)
    // Add more specific, relevant URLs based on research focus
];

    