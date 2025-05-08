import type { NavItem, SettingsFormData } from '@/types';
import { LayoutDashboard, FileText, Settings, Info, Users, HardDriveDownload, GanttChartSquare, UserCog } from 'lucide-react';
import { format } from 'date-fns';


export const APP_NAME = 'BreachWatch';

export const NAV_LINKS: NavItem[] = [
  { title: 'Dashboard', href: '/dashboard', icon: LayoutDashboard, category: 'main' },
  { title: 'Downloaded Files', href: '/downloaded-files', icon: HardDriveDownload, category: 'main' },
  { title: 'Crawl Jobs', href: '/jobs', icon: GanttChartSquare, category: 'main' },
  { title: 'Settings', href: '/settings', icon: Settings, category: 'main' },
  { title: 'Ethical Guidelines', href: '/guidelines', icon: Info, category: 'main' },
  { title: 'Documentation', href: '/documentation', icon: FileText, category: 'main'},
  { title: 'User Management', href: '/admin/users', icon: Users, adminOnly: true, category: 'main' },
  { title: 'User Preferences', href: '/profile/preferences', icon: UserCog, category: 'account' },
];


export const DEFAULT_KEYWORDS = [
  "password", "secret", "confidential", "private key", "api_key", "token", "credentials", "backup",
  "NIK", "no_ktp", "nomor_ktp", "nama_lengkap", "ktp", "kartu_keluarga", "kk", "no_kk",
  "ijazah", "transkrip_nilai", "cv", "lamaran_kerja", "gaji", "slip_gaji",
  "rekening_koran", "mutasi_rekening", "kartu_kredit", "nomor_rekening", "bank_statement",
  "database_dump", ".sql", ".bak", ".env", "config", "prod.config", "staging.config",
  "internal", "rahasia_perusahaan", "dokumen_rahasia", "notulen_rapat", "SOP",
  "data_pelanggan", "data_nasabah", "data_karyawan", "user_list", "member_data",
  "site:pastebin.com", "site:justpaste.it", "site:throwbin.io", "site:scribd.com",
  "inurl:admin", "inurl:login", "intitle:index.of", "intitle:dashboard",
  "\"Powered by WHM/cPanel\"", "\"phpmyadmin\"",
  "filetype:log", "filetype:env", "filetype:bak", "filetype:sql", "filetype:json", "filetype:csv", "filetype:txt", "filetype:xls", "filetype:xlsx", "filetype:doc", "filetype:docx", "filetype:pdf", "filetype:zip", "filetype:rar", "filetype:tar.gz", "filetype:tgz", "filetype:7z",
  
  // Indonesian specific
  "bocoran_data", "kebocoran_data", "data_pribadi", "informasi_sensitif", "data_penduduk",
  "nomor_induk_kependudukan", "nomor_identitas", "bpjs", "npwp", "surat_tanah", "sertifikat_rumah",
  "intitle:\"direktori data\" site:.go.id", "intext:\"rahasia negara\" site:.mil.id",
  "filetype:pdf site:.go.id \"surat keputusan\"", "filetype:xls site:.go.id \"daftar nama\"",
  "site:.ac.id filetype:sql username password", "site:.co.id inurl:backup database",
  "\"alamat email\" \"nomor telepon\" filetype:csv site:.id",
  "\"rapat internal\" filetype:docx site:.go.id",
  "\"daftar hadir\" \"NIK\" filetype:pdf site:.go.id",
  // Common sensitive files
  "wp-config.php", "settings.php", "local.xml", "credentials.json", "id_rsa", "id_dsa",
  // Cloud storage related
  "s3.amazonaws.com", "storage.googleapis.com", "blob.core.windows.net", "digitaloceanspaces.com"
].join('\n');


export const DEFAULT_FILE_EXTENSIONS = [
  "txt", "csv", "sql", "json", "xml", "yaml", "yml", "ini", "conf", "config", "cfg",
  "log", "env", "pem", "key", "cer", "crt", "p12", "pfx", "jks",
  "doc", "docx", "xls", "xlsx", "ppt", "pptx", "odt", "ods", "odp", "pdf",
  "zip", "rar", "tar", "gz", "7z", "bz2", "tgz",
  "db", "sqlite", "mdb", "bak", "dump", "sqlitedb", "backup", "bkf", "bkp",
  "php", "asp", "aspx", "jsp", "rb", "py", "sh", "bat", "ps1",
  // Image files are generally less likely to contain text data breaches, but could be metadata or specific cases
  // "jpg", "jpeg", "png", "gif", "bmp", "tif", "tiff", "svg"
  // Source code files might contain hardcoded credentials
  "java", "cs", "c", "cpp", "h", "hpp", "js", "ts", "html", "css", "scss", "less"
].join('\n');


export const DEFAULT_SEED_URLS = [
  // Popular paste sites (use with caution and respect ToS)
  "https://pastebin.com",
  "https://justpaste.it",
  "https://throwbin.io",
  "https://pastes.io",
  "https://hastebin.com",
  "https://ghostbin.co",
  "https://dumpz.org",

  // Code sharing platforms (often have public gists/snippets)
  "https://gist.github.com/discover",
  "https://gitlab.com/explore/snippets",
  "https://bitbucket.org/repo/snippets", // Check current URL for public snippets

  // Forums known for tech discussions / potential leaks (general, not specific Indonesian)
  "https://raidforums.com", // (Be aware of the nature of this site)
  "https://breached.vc", // (Successor/related to RaidForums)
  "https://forum.exploit.in", // Russian-speaking forum
  "https://stackoverflow.com", // For finding misconfigured code snippets
  "https://github.com/search?q=泄露&type=code", // GitHub search for "leak" in Chinese, example for specific language searches

  // Indonesian specific (examples, needs refinement and verification)
  // These are generic and might not be ideal seed URLs without more context.
  // Crawling government/academic sites directly as seed URLs needs extreme caution and authorization.
  // "https://*.go.id", // Too broad, not a good seed. Dorks are better for .go.id
  // "https://*.ac.id", // Too broad
  // "https://*.co.id", // Too broad

  // Publicly known Indonesian forums or communities where tech discussions happen or data might be shared
  // (Replace with actual, relevant, and ethically sound URLs)
  // "https://www.kaskus.co.id/forum/21" // Example: Kaskus Computer Stuff (verify relevance)
  // "https://www.bersatulawancovid.id/forum" // Example, check for public data sections
  
  // Sites for public document sharing
  "https://www.scribd.com",
  "https://www.slideshare.net",
  "https://issuu.com",
  "https://dokumen.tips", // Indonesian document sharing site
  "https://pdfcoffee.com",
  "https://id.scribd.com/", // Scribd Indonesian

  // Public cloud storage buckets (use dorks for these usually, but listing a few known patterns)
  // These are not direct seed URLs but represent types of URLs that dorks might find
  // "http://s3.amazonaws.com/", // Base for dorks
  // "http://storage.googleapis.com/", // Base for dorks

  // Search engines can sometimes list open directories if dorked correctly.
  // These are not seed URLs but concepts for dorking.

  // It is crucial to ensure these URLs are ethically appropriate to crawl.
  // For sensitive domains like .go.id, direct deep crawling from a base URL is generally not advised without permission.
  // Dorks are a more targeted approach.
].join('\n');


export const DEFAULT_SEARCH_DORKS = [
  // General Sensitive File Dorks
  'filetype:sql "password" OR "username"',
  'filetype:env "DB_PASSWORD" OR "API_KEY"',
  'filetype:log "error" "user_id" "ip_address"',
  'filetype:bak inurl:backup OR inurl:dump',
  'filetype:config "prod" "credentials"',
  'intitle:"index of" "backup"',
  'intitle:"index of" "database"',
  'intitle:"index of" "confidential"',
  'intext:"BEGIN RSA PRIVATE KEY" filetype:key',
  'intext:"-----BEGIN CERTIFICATE-----" filetype:pem OR filetype:crt',
  'site:docs.google.com "confidential" OR "private" "shareable_link=anyone"', // Misconfigured Google Docs
  'site:drive.google.com "confidential" OR "private" "shareable_link=anyone"', // Misconfigured Google Drive
  'site:onedrive.live.com "confidential" OR "private" "sharing_link"', // Misconfigured OneDrive
  'site:dropbox.com/s/ "confidential" OR "private"', // Misconfigured Dropbox
  'site:trello.com "password" OR "api_key"', // Public Trello boards
  'site:*.s3.amazonaws.com intitle:"index of" OR intext:"bucket"', // Open S3 Buckets
  'site:storage.googleapis.com intitle:"index of" OR intext:"bucket"', // Open Google Cloud Storage
  'site:blob.core.windows.net intitle:"index of" OR intext:"container"', // Open Azure Blob Storage
  'site:digitaloceanspaces.com intitle:"index of"', // Open DigitalOcean Spaces

  // Indonesian Specific Dorks (.go.id - Government)
  'site:.go.id filetype:pdf "rahasia" OR "sulit"',
  'site:.go.id filetype:xls "daftar nama" OR "gaji" OR "NIK"',
  'site:.go.id filetype:docx "surat keputusan" OR "notulen rapat"',
  'site:.go.id intitle:"index of" "data" OR "backup" OR "archive"',
  'site:.go.id inurl:admin OR inurl:login "username" "password"', // Risky, check for exposed login pages
  'site:.go.id filetype:sql "database" OR "users"',
  'site:.go.id intext:"Nomor Induk Kependudukan" OR intext:"No. KTP"',
  'site:.go.id filetype:csv "data penduduk" OR "kontak"',
  'site:.go.id "Powered by WHM" OR "cPanel Login" inurl:/cpanel', // Exposed control panels
  'site:.go.id inurl:/phpmyadmin/', // Exposed phpMyAdmin
  'site:.go.id filetype:log "user activity" OR "access log"',
  'site:.go.id inurl:.zip OR inurl:.rar "backup_data"',
  'site:.go.id ext:txt confidential OR private',
  'site:.go.id "kata sandi" OR "nama pengguna" intext:"login"',
  'site:.go.id filetype:env -example', // .env files not explicitly examples
  'site:.go.id intext:"API_SECRET" OR intext:"SECRET_KEY"',
  'site:.go.id intitle:"dashboard" "statistik" -login', // Dashboards that might not require login
  'site:.go.id filetype:json "user_data" OR "employee_records"',
  'site:.go.id inurl:uploads "internal_document"', // Check for exposed upload directories
  'site:.go.id "surat edaran internal" filetype:pdf',
  'site:.go.id "daftar peserta" "NIK" filetype:xlsx',
  'site:.go.id intitle:"directory listing" "database_dumps"',
  'site:.go.id intext:"kartu keluarga" filetype:pdf',
  'site:.go.id intext:"nomor pokok wajib pajak" OR intext:"NPWP"',
  'site:.go.id filetype:txt "username" "password" "host"',

  // Indonesian Specific Dorks (.ac.id - Academic)
  'site:.ac.id filetype:pdf "transkrip nilai" OR "data mahasiswa"',
  'site:.ac.id filetype:xls "daftar mahasiswa" OR "NIM" OR "IPK"',
  'site:.ac.id intitle:"index of" "skripsi" OR "tesis" OR "backup_kuliah"',
  'site:.ac.id inurl:dosen "cv" OR "penelitian" filetype:doc',
  'site:.ac.id filetype:sql "mahasiswa" OR "users" OR "jadwal_kuliah"',
  'site:.ac.id intext:"Nomor Induk Mahasiswa" OR intext:"NPM"',
  'site:.ac.id filetype:csv "kontak dosen" OR "email mahasiswa"',
  'site:.ac.id inurl:phpmyadmin/setup/', // phpMyAdmin setup pages
  'site:.ac.id "database dump" filetype:zip OR filetype:sql.gz',
  'site:.ac.id "backup server" ext:tar.gz',
  'site:.ac.id filetype:xlsx "absensi" OR "kehadiran"',
  'site:.ac.id intext:"kartu rencana studi" OR intext:"KRS"',
  'site:.ac.id intitle:"Sistem Informasi Akademik" "login"',
  'site:.ac.id filetype:json "student_data" OR "lecture_notes"',
  'site:.ac.id inurl:repo "confidential_research"', // Check exposed repositories

  // Indonesian Specific Dorks (.co.id, .id, .or.id - Commercial/General/Organization)
  'site:.co.id filetype:csv "customer data" OR "daftar pelanggan" OR "email" "phone"',
  'site:.id filetype:xls "employee list" OR "daftar karyawan" OR "gaji"',
  'site:.or.id filetype:pdf "member list" OR "data anggota" OR "donasi"',
  'site:.co.id intitle:"index of" "backup_website" OR "database_backup"',
  'site:.id inurl:api "token" OR "secret" filetype:json', // Check for exposed API tokens
  'site:.co.id filetype:sql "users" OR "orders" OR "products"',
  'site:.id intext:"private document" OR "confidential report"',
  'site:.co.id "internal memo" filetype:docx',
  'site:.id "financial statement" filetype:pdf OR filetype:xlsx',
  'site:.or.id inurl:/wp-admin/ "debug.log"', // WordPress debug logs
  'site:.co.id filetype:env "AWS_ACCESS_KEY_ID" -template -example',
  'site:.id "invoice" "pelanggan" filetype:pdf',
  'site:.co.id intitle:"admin panel" -demo -sample',
  'site:.id filetype:txt "list_user" "password"',
  'site:.or.id "database connection string" intext:password',

  // Advanced Dorks using operators
  'allintitle: "admin login" OR "control panel" site:.go.id',
  'allinurl: backup/db site:.co.id OR site:.id',
  'intext:"password specified for user" filetype:log site:.ac.id',
  'related:pastebin.com "data pribadi" OR "NIK"', // Find sites similar to pastebin discussing Indonesian data
  '"index of /" + "database" site:.go.id',
  '"index of /" + "confidential" site:.co.id',
  'filetype:config intext:username intext:password site:.id',
  'ext:sql intext:wp_users phpmyadmin site:.co.id', // WordPress user table dumps
  'inurl:/proc/self/cwd site:.go.id', // Exposes current working directory, potential vulns
  'site:.go.id OR site:.ac.id "error establishing a database connection"', // Database connection errors
  'site:github.com "go.id" "api_key" OR "password"', // Search GitHub for hardcoded credentials related to .go.id
  'site:gitlab.com "ac.id" "SECRET_KEY" OR "DB_PASSWORD"',
  'site:bitbucket.org "co.id" "internal" "credentials"',
  'site:glitch.com "go.id" ".env"', // Check Glitch for exposed .env files
  'site:repl.it "ac.id" "config.json" "secret"', // Check Replit
  'site:codepen.io "co.id" "api" "token"', // Check CodePen
  'site:.sharepoint.com "internal document" "go.id" - Anfrage', // SharePoint leaks (adjust language if needed)
  'site:box.com/s/ "confidential" "ac.id"', // Box.com leaks
  'ext:aspx inurl:export OR inurl:download "data" site:.go.id', // ASPX specific export pages
  'inurl:_ignition/execute-solution site:.co.id', // Laravel ignition debug mode

  // Dorks targeting specific CMS/Platforms
  'inurl:/wp-content/uploads/ site:.go.id "daftar" filetype:xls OR filetype:pdf',
  'inurl:/sites/default/files/ site:.ac.id "internal" filetype:doc', // Drupal
  'ext:jps inurl:/portal/ "user" site:.go.id', // Liferay portal
  'inurl:/owa/ site:.go.id', // Outlook Web Access

  // More Indonesian keywords and combinations
  'filetype:pdf "surat perjanjian" OR "kontrak" site:.co.id',
  'filetype:xlsx "data keuangan" OR "laporan anggaran" site:.go.id',
  'site:.id "nomor hp" "alamat" filetype:csv',
  'intitle:"backup" "database" "sql" site:.ac.id',
  'site:.go.id intext:"untuk kalangan terbatas"',
  'site:.co.id "username" "password" "login" inurl:.txt',
  'site:.ac.id "daftar dosen" "email" "nomor telepon" filetype:pdf',
  'site:.go.id inurl:ftp "pub" "archive"', // FTP directories
  'site:.co.id "SOP Keamanan" filetype:pdf',
  'site:.id intitle:"Data Center" "credentials"',

  // Searching for error messages that expose paths or config
  'Warning: pg_connect(): Unable to connect to PostgreSQL server: FATAL site:.go.id',
  'mysql_connect error site:.ac.id',
  '"failed to open stream: No such file or directory in" "config" site:.co.id',
  
  // Specific sensitive documents with common Indonesian naming
  'filetype:pdf "Surat Keterangan Catatan Kepolisian" OR "SKCK" site:.go.id OR site:.id',
  'filetype:pdf "Akta Kelahiran" site:.go.id OR site:.id',
  'filetype:pdf "Kartu Tanda Penduduk" site:.go.id OR site:.id',
  'filetype:pdf "Nomor Pokok Wajib Pajak" OR "NPWP" site:.go.id OR site:.id',
  'filetype:pdf "Buku Pemilik Kendaraan Bermotor" OR "BPKB" site:.id',
  'filetype:xlsx "Daftar Inventaris Barang Milik Negara" OR "Daftar Aset" site:.go.id',
  'filetype:docx "Rancangan Undang-Undang" OR "RUU" site:.go.id',
  'filetype:pdf "Hasil Audit Internal" site:.go.id OR site:.co.id',
  'filetype:xls "Data Rekam Medis Pasien" site:.rs OR site:.co.id', // Assuming .rs for Rumah Sakit
  'filetype:pdf "Laporan Keuangan Tahunan" site:.co.id OR site:.go.id "confidential"',
].join('\n');

export const DEFAULT_SETTINGS: SettingsFormData = {
  keywords: DEFAULT_KEYWORDS,
  fileExtensions: DEFAULT_FILE_EXTENSIONS,
  seedUrls: DEFAULT_SEED_URLS,
  searchDorks: DEFAULT_SEARCH_DORKS,
  crawlDepth: 2,
  respectRobotsTxt: true,
  requestDelay: 1.0,
  customUserAgent: '',
  maxResultsPerDork: 20,
  maxConcurrentRequestsPerDomain: 2,
  scheduleEnabled: false,
  scheduleType: 'one-time',
  scheduleCronExpression: '0 0 * * *', // Daily at midnight
  scheduleRunAtDate: format(new Date(), 'yyyy-MM-dd'),
  scheduleRunAtTime: format(new Date(), 'HH:mm'),
  scheduleTimezone: Intl.DateTimeFormat().resolvedOptions().timeZone || 'UTC',
};

// File type categorization for icons and filtering (can be expanded)
export const FILE_TYPE_EXTENSIONS = {
  text: ['txt', 'log', 'md', 'csv', 'tsv', 'rtf', 'srt', 'sub', 'asc'],
  json: ['json', 'geojson', 'jsonl'],
  database: ['sql', 'db', 'sqlite', 'mdb', 'sqlite3', 'dump'],
  archive: ['zip', 'rar', 'tar', 'gz', '7z', 'bz2', 'tgz', 'tar.gz', 'tar.bz2'],
  code: ['php', 'js', 'ts', 'py', 'java', 'c', 'cpp', 'h', 'hpp', 'cs', 'rb', 'go', 'swift', 'kt', 'sh', 'bat', 'ps1', 'html', 'htm', 'css', 'scss', 'less', 'xml', 'yaml', 'yml', 'ini', 'conf', 'config', 'cfg', 'env'],
  spreadsheet: ['xls', 'xlsx', 'ods'],
  document: ['doc', 'docx', 'pdf', 'odt', 'ppt', 'pptx', 'odp', 'pages', 'key'],
  config: ['ini', 'conf', 'config', 'cfg', 'env', 'yaml', 'yml', 'toml', 'xml', 'json'], // some overlap with code/json
  image: ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'svg', 'webp', 'ico', 'tif', 'tiff'],
  audio: ['mp3', 'wav', 'ogg', 'aac', 'flac', 'm4a'],
  video: ['mp4', 'mov', 'avi', 'mkv', 'webm', 'flv', 'wmv']
};
