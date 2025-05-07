
import type { LucideIcon } from 'lucide-react';

export interface BreachData {
  id: string;
  sourceUrl: string;
  fileUrl: string;
  fileType: string; // e.g., "txt", "csv", "sql", "json", "xlsx", "db", "bak", "zip", "gz"
  dateFound: string; // ISO string format
  keywords: string[];
  status?: 'new' | 'reviewed' | 'ignored'; // Optional
}

export interface NavItem {
  title: string;
  href: string;
  icon: LucideIcon;
  label?: string;
  disabled?: boolean;
}

export interface SettingsData {
  keywords: string;
  fileExtensions: string;
  seedUrls: string;
  searchDorks: string;
  crawlDepth: number;
  respectRobotsTxt: boolean;
  requestDelay: number; // in seconds
}
