
import type { NavItem, SettingsFormData } from '@/types';
import {
  LayoutDashboard,
  Download,
  Settings,
  Info,
  BookOpen,
  Users,
  UserCircle,
  Cog, // Changed from UserCog to Cog as UserCog might not be available or intended
} from 'lucide-react';
import { format } from 'date-fns';

export const APP_NAME = 'BreachWatch';

// Navigation links for the sidebar
export const NAV_LINKS: NavItem[] = [
  { title: 'Dashboard', href: '/dashboard', icon: LayoutDashboard, category: 'main' },
  { title: 'Downloaded Files', href: '/downloaded-files', icon: Download, category: 'main' },
  { title: 'Crawl Jobs', href: '/jobs', icon: BookOpen, category: 'main' }, // Using BookOpen as placeholder, consider GanttChartSquare if available
  { title: 'Settings', href: '/settings', icon: Settings, category: 'main' },
  { title: 'Ethical Guidelines', href: '/guidelines', icon: Info, category: 'main' },
  { title: 'Documentation', href: '/documentation', icon: BookOpen, category: 'main' },
  { title: 'User Management', href: '/admin/users', icon: Users, adminOnly: true, category: 'main' },
  // Account related links could be grouped differently or stay in main
  { title: 'Profile', href: '/profile', icon: UserCircle, category: 'account' },
  { title: 'Preferences', href: '/profile/preferences', icon: Cog, category: 'account'}, // Changed to Cog
];

// Default settings for the crawl configuration form
export const DEFAULT_SETTINGS: SettingsFormData = {
  keywords: 'password, secret, confidential, NIK, no_ktp, nama_lengkap, alamat',
  fileExtensions: 'txt, csv, sql, json, zip, log, env, pem, key',
  seedUrls: 'https://pastebin.com\nhttps://sita.bpdas-sjd.id', // Example seed URLs
  searchDorks: 'filetype:sql "password"\nintitle:"index of" "backup"\nsite:.go.id filetype:xls "gaji"',
  crawlDepth: 2,
  respectRobotsTxt: true,
  requestDelay: 1.5,
  customUserAgent: '',
  maxResultsPerDork: 20,
  maxConcurrentRequestsPerDomain: 2,
  proxies: '',
  scheduleEnabled: false,
  scheduleType: 'one-time',
  scheduleCronExpression: '0 0 * * *', // Default to daily at midnight
  scheduleRunAtDate: format(new Date(), 'yyyy-MM-dd'), // Default to today
  scheduleRunAtTime: '09:00', // Default to 09:00 AM
  scheduleTimezone: Intl.DateTimeFormat().resolvedOptions().timeZone || 'UTC', // Default to user's browser timezone or UTC
};


// For FileTypeIcon component
export const FILE_TYPE_EXTENSIONS: Record<string, string[]> = {
  text: ["txt", "log", "csv", "md", "rtf", "tsv", "ini", "conf", "cfg", "pem", "key", "crt", "cer", "env"],
  json: ["json", "jsonl", "geojson"],
  database: ["sql", "db", "sqlite", "sqlite3", "mdb", "accdb", "dump", "bak"],
  archive: ["zip", "tar", "gz", "bz2", "7z", "rar", "tgz"],
  code: ["py", "js", "java", "c", "cpp", "cs", "php", "rb", "go", "html", "css", "sh", "ps1", "bat", "xml", "yaml", "yml", "config"],
  spreadsheet: ["xls", "xlsx", "ods"],
  document: ["doc", "docx", "odt", "pdf", "ppt", "pptx", "odp"],
  // Config was overlapping with text/code, refined it here.
  // It's often better to categorize by specific extension rather than a broad "config" category
  // if more specific icons are desired.

  // For generic fallback (used in FileTypeIcon.tsx)
  image: ['png', 'jpg', 'jpeg', 'gif', 'svg', 'webp', 'bmp', 'ico'],
  audio: ['mp3', 'wav', 'ogg', 'aac', 'flac', 'm4a'],
  video: ['mp4', 'mov', 'avi', 'mkv', 'webm', 'flv'],
  // Specific sensitive types (can be expanded)
  security: ["kdbx", "ovpn", "rdp", "p12", "pfx", "jks"],
};
