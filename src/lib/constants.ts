// src/lib/constants.ts
import type { SettingsFormData, NavItem } from '@/types';
import { 
    LayoutDashboard, 
    Database, 
    Settings as SettingsIcon, 
    Info, 
    BookOpen, 
    GanttChartSquare, 
    UserCircle, 
    Users,
    UserCog // Added for preferences
} from 'lucide-react';

export const APP_NAME = "BreachWatch";

// Default settings for the Settings page form
export const DEFAULT_SETTINGS: SettingsFormData = {
  keywords: 'password, admin, backup, confidential, private, secret, credentials, user, username, pwd, pass, nik, no_ktp, nama_lengkap, gaji, salary, bank, account, cc, card, token, api_key',
  fileExtensions: 'txt, csv, sql, json, zip, tar.gz, 7z, rar, db, sqlite, bak, log, config, xlsx, docx, pdf, env, pem, key, dat, dump',
  seedUrls: 'https://pastebin.com\nhttps://gist.github.com',
  searchDorks: `filetype:sql "passwords" site:pastebin.com
filetype:txt "nik" | "no_ktp" | "nama_lengkap" site:.go.id
intitle:"index of" "backup.zip" site:.co.id
filetype:env "DB_PASSWORD" -github.com site:.ac.id
inurl:"/admin/config.php" filetype:php "DB_PASSWORD"
filetype:log username password site:*.go.id
intitle:"phpinfo()" "mysql_connect"
intext:"BEGIN RSA PRIVATE KEY" filetype:key`,
  crawlDepth: 2,
  respectRobotsTxt: true,
  requestDelay: 1.0,
  customUserAgent: '',
  maxResultsPerDork: 20,
  maxConcurrentRequestsPerDomain: 2,
  // Scheduling defaults
  scheduleEnabled: false,
  scheduleType: 'recurring',
  scheduleCronExpression: '0 0 * * SUN', // Weekly on Sunday midnight
  scheduleRunAtDate: new Date().toISOString().split('T')[0], // Default to today
  scheduleRunAtTime: '00:00', 
  scheduleTimezone: Intl.DateTimeFormat().resolvedOptions().timeZone || 'UTC', // Default to browser timezone or UTC
};

// Navigation links for the sidebar
export const NAV_LINKS: NavItem[] = [
  { title: 'Dashboard', href: '/dashboard', icon: LayoutDashboard, category: 'main' },
  { title: 'Downloaded Files', href: '/downloaded-files', icon: Database, category: 'main' },
  { title: 'Crawl Jobs', href: '/jobs', icon: GanttChartSquare, category: 'main' },
  { title: 'Settings', href: '/settings', icon: SettingsIcon, category: 'main' },
  { title: 'User Management', href: '/admin/users', icon: Users, category: 'main', adminOnly: true }, // Admin only
  { title: 'Profile', href: '/profile', icon: UserCircle, category: 'account' }, // Moved Profile here
  { title: 'Preferences', href: '/profile/preferences', icon: UserCog, category: 'account' }, // Added Preferences
  { title: 'Ethical Guidelines', href: '/guidelines', icon: Info, category: 'account' },
  { title: 'Documentation', href: '/documentation', icon: BookOpen, category: 'account' },
];

// Mapping file extensions to categories for icons or display
export const FILE_TYPE_EXTENSIONS: Record<string, string[]> = {
  text: ['txt', 'md', 'log', 'csv', 'tsv', 'rtf', 'xml', 'yaml', 'yml', 'ini', 'conf', 'config', 'pem', 'key'],
  json: ['json'],
  database: ['sql', 'db', 'sqlite', 'mdb', 'dump', 'bak'],
  archive: ['zip', 'rar', '7z', 'tar', 'gz', 'bz2', 'xz'],
  code: ['js', 'jsx', 'ts', 'tsx', 'py', 'java', 'c', 'cpp', 'h', 'cs', 'php', 'rb', 'go', 'html', 'css', 'scss', 'less', 'sh', 'bat', 'ps1', 'env'],
  spreadsheet: ['xlsx', 'xls', 'ods'],
  document: ['pdf', 'docx', 'doc', 'odt', 'ppt', 'pptx', 'odp'],
  config: ['config', 'cfg', 'conf', 'properties', 'toml'] // Added config category
};
