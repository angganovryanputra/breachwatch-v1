import type { NavItem, SettingsFormData } from '@/types';
import { LayoutDashboard, FileText, Settings, ShieldQuestion, BookOpen, GanttChartSquare, Users } from 'lucide-react';

export const APP_NAME = 'BreachWatch';

export const NAV_LINKS: NavItem[] = [
  { title: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
  { title: 'Crawl Jobs', href: '/jobs', icon: GanttChartSquare },
  { title: 'File Records', href: '/downloaded-files', icon: FileText },
  { title: 'Settings', href: '/settings', icon: Settings },
  { title: 'User Management', href: '/admin/users', icon: Users, adminOnly: true },
  { title: 'Documentation', href: '/documentation', icon: BookOpen },
  { title: 'Ethical Guidelines', href: '/guidelines', icon: ShieldQuestion },
];

export const DEFAULT_SETTINGS: SettingsFormData = {
  keywords: 'password, secret, NIK, no_ktp, nama_lengkap, kk, kartu_keluarga, database, backup, dump, admin, login, username, email, gaji, salary, private_key, api_key, confidential, internal, classified, ".php?id=", ".asp?id=", ".aspx?id=", ".jsp?id=", ".cfm?id="',
  fileExtensions: 'txt, csv, sql, json, zip, tar.gz, rar, 7z, db, bak, log, config, xls, xlsx, doc, docx, pdf, mdb, accdb, sqlite, eml, pst, ovpn, conf, ini, yml, yaml, kdbx, pfx, pem, key, crt, cer, p12, jks',
  seedUrls: 'https://pastebin.com\nhttps://gist.github.com\nhttps://slexy.org\nhttps://pastie.io\nhttp://dpaste.com\nhttps://rentry.co\nhttps://justpaste.it',
  searchDorks: `site:pastebin.com "password"
site:trello.com "password"
site:*.s3.amazonaws.com "database_dump"
site:docs.google.com "confidential"
inurl:".env" "DB_PASSWORD" -github.com
inurl:"/wp-content/uploads/" "backup.zip" OR "backup.sql"
intitle:"index of /" "backup" OR "database"
filetype:sql "CREATE TABLE" "password"
filetype:log "Error" "Exception" "Stack Trace"
filetype:config "username" "password"
site:*.go.id filetype:pdf "rahasia" OR "internal"
site:*.ac.id filetype:xls "data mahasiswa" OR "nilai"
site:*.co.id intitle:"index of /" "backup"
inurl:admin login site:*.go.id
inurl:backup intitle:"index of /" site:*.mil.id
site:*.s3.amazonaws.com "confidential" OR "internal_data"
site:drive.google.com "company_confidential" OR "internal_report"
site:sharepoint.com "Project Files" "Internal Use Only"
site:box.com "Sensitive_Data"
site:dropbox.com "backup_db"
intitle:"phpinfo()" "PHP Version" -github
intext:"index of /" "parent directory" "backup.tar.gz"
site:*.go.id filetype:sql "INSERT INTO" OR "PASSWORD"
site:*.ac.id filetype:csv "students" OR "grades"
site:*.co.id filetype:json "API_KEY" OR "credentials"
site:*.go.id intitle:"index of" "database" OR "backup"
site:*.ac.id inurl:/uploads/ "confidential"
site:*.co.id inurl:admin "login.php" OR "admin.php"
site:*.go.id filetype:log "error log" OR "debug log"
site:*.ac.id filetype:config "db_password" OR "secret_key"
site:*.co.id filetype:bak "database_backup"
site:*.go.id inurl:/backup/ "db.sql"
site:*.ac.id inurl:/files/ "internal_document.pdf"
site:*.co.id intitle:"Directory Listing" ".git"
site:*.go.id ext:env "APP_KEY"
site:*.ac.id ext:log "PHP Fatal error"
site:*.co.id ext:bak "dump.sql"
site:*.go.id intext:"Powered by phpMyAdmin"
site:*.ac.id intext:"Version Information" "MySQL"
site:*.co.id intext:"Welcome to nginx!" "403 Forbidden" -stackoverflow.com
site:*.go.id filetype:txt "username" "password"
site:*.ac.id filetype:docx "surat keputusan" "internal"
site:*.co.id inurl:/_profiler/ "Symfony Profiler"
site:gitlab.*.* intext:"api_key" intext:"PRIVATE-TOKEN"
site:*.atlassian.net "API token"
site:s3-external-1.amazonaws.com OR site:s3.amazonaws.com
site:blob.core.windows.net
site:storage.googleapis.com
site:digitaloceanspaces.com
site:*.go.id filetype:env "DATABASE_URL" OR "AWS_ACCESS_KEY_ID"
site:*.ac.id filetype:bak "backup" OR "dump"
site:*.co.id filetype:csv "customer_data" OR "user_list"
site:*.go.id intitle:"Index of /" "confidential" OR "private"
site:*.ac.id inurl:admin "dashboard" OR "settings"
site:*.co.id filetype:log "access.log" OR "error.log"
site:*.go.id intext:"phpinfo()" "environment" OR "configuration"
site:*.ac.id filetype:pem "PRIVATE KEY"
site:*.co.id inurl:"/api/" "users" "password"
site:*.go.id filetype:xlsx "data_pegawai" OR "gaji"
site:*.ac.id filetype:json "credentials" OR "token"
site:*.co.id intitle:"cPanel" "File Manager"
site:*.go.id inurl:".git" "config" -github.com
site:*.ac.id inurl:"/storage/" "logs" OR "backups"
site:*.co.id filetype:pem "BEGIN RSA PRIVATE KEY"
site:osf.io "password"
site:figshare.com "api_key"
site:data.world "confidential"
site:*.medium.com "internal" "password"
site:slack.com "oauth token" "xoxp-"
site:*.sharepoint.com "confidential" filetype:xlsx
site:*.box.com "internal" filetype:pdf
site:dev.azure.com "secrets"
site:*.firebaseio.com ".json?auth="
site:*.cloudfunctions.net "token"
site:*.supabase.co "service_key"
site:*.go.id inurl:/tmp/ "backup.sql.gz"
site:*.ac.id inurl:/old/ "database.bak"
site:*.co.id inurl:/includes/ "config.php"
site:*.go.id filetype:sh "export AWS_SECRET_ACCESS_KEY"
site:*.ac.id filetype:sql "pg_dump" "user"
site:*.co.id filetype:txt "BEGIN PGP PRIVATE KEY BLOCK"
site:*.go.id intitle:"Index of /" "secret_files"
site:*.ac.id inurl:"/api/v1/users" "email"
site:*.co.id filetype:json "Authorization: Bearer"
site:*.go.id filetype:csv "data_sensitif"
site:*.ac.id inurl:"/_ignition/execute-solution" "Solution"
site:*.co.id filetype:log "failed login" "ip_address"
site:*.go.id filetype:config "ldap_password"
site:*.ac.id filetype:yml "docker-compose" "environment"
site:*.co.id filetype:txt "ssh-rsa" "PRIVATE KEY"
site:paste.ee "password"
site:ghostbin.co "API_SECRET"
site:ideone.com "credentials"
site:codepen.io "private_token"
site:jsfiddle.net "db_password"
site:repl.it "secret_key" -docs
site:glitch.com ".env"
site:bitbucket.org "password" "pipeline"
site:sourceforge.net "dump.sql"
site:codeberg.org "config.ini" "secret"`,
  crawlDepth: 2,
  respectRobotsTxt: true,
  requestDelay: 1.0,
  customUserAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 BreachWatchResearchBot/1.1',
  maxResultsPerDork: 20,
  maxConcurrentRequestsPerDomain: 2,
  scheduleEnabled: false,
  scheduleType: 'one-time',
  scheduleCronExpression: '0 0 * * *', // Default to daily at midnight if recurring
  scheduleRunAtDate: new Date().toISOString().split('T')[0], // Today's date
  scheduleRunAtTime: '00:00', // Midnight
  scheduleTimezone: Intl.DateTimeFormat().resolvedOptions().timeZone, // User's current timezone
};


// For FileTypeIcon component
export const FILE_TYPE_EXTENSIONS: Record<string, string[]> = {
    text: ['txt', 'md', 'log', 'csv', 'tsv', 'rtf', 'xml', 'html', 'htm', 'css', 'js', 'conf', 'cfg', 'ini', 'out', 'asc', 'pem', 'key', 'crt', 'cer', 'pem', 'ca-bundle', 'csr', 'pub'],
    json: ['json', 'jsonl', 'geojson'],
    database: ['sql', 'db', 'sqlite', 'mdb', 'accdb', 'dump', 'bak'],
    archive: ['zip', 'tar', 'gz', 'bz2', '7z', 'rar', 'tgz', 'xz'],
    code: ['py', 'java', 'c', 'cpp', 'cs', 'go', 'rb', 'php', 'swift', 'kt', 'scala', 'pl', 'sh', 'bat', 'ps1', 'ipynb', 'env', 'yml', 'yaml', 'toml', 'dockerfile', 'kdbx'],
    spreadsheet: ['xls', 'xlsx', 'ods', 'csv'], // CSV is also text, but can be primarily spreadsheet
    document: ['pdf', 'doc', 'docx', 'odt', 'ppt', 'pptx', 'odp'],
    config: ['config', 'ini', 'conf', 'cfg', 'cnf', 'properties', 'prefs', 'settings', 'reg', 'plist', 'ovpn'],
    image: ['png', 'jpg', 'jpeg', 'gif', 'svg', 'webp', 'bmp', 'ico', 'tiff'],
    audio: ['mp3', 'wav', 'ogg', 'aac', 'flac', 'm4a'],
    video: ['mp4', 'mov', 'avi', 'mkv', 'webm', 'flv', 'wmv'],
};