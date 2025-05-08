
import type { LucideIcon } from 'lucide-react';
import { LayoutDashboard, HardDriveDownload, Settings, BookOpen, Info, GanttChartSquare } from 'lucide-react';
import type { SettingsData, NavItem } from '@/types';


export const APP_NAME = 'BreachWatch';

export const NAV_LINKS: NavItem[] = [
  { title: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
  { title: 'Downloaded Files', href: '/downloaded-files', icon: HardDriveDownload },
  { title: 'Crawl Jobs', href: '/jobs', icon: GanttChartSquare }, // New Crawl Jobs link
  { title: 'Settings', href: '/settings', icon: Settings },
  { title: 'Documentation', href: '/documentation', icon: BookOpen },
  { title: 'Ethical Guidelines', href: '/guidelines', icon: Info },
];

export const DEFAULT_KEYWORDS = [
  'rahasia', 'sulit', 'penting', 'privasi', 'database', 'backup', 'config', 'confidential',
  'password', 'secret', 'api_key', 'credential', 'private_key', 'token', 'auth_token',
  'NIK', 'no_ktp', 'nomor_ktp', 'ktp', 'kk', 'nomor_kk', 'kartu_keluarga', 'nama_lengkap',
  'username', 'users', 'user_data', 'client_data', 'customer_data', 'employee_data',
  'financial_data', 'rekening', 'nomor_rekening', 'gaji', 'slip_gaji', 'medical_records', 'rekam_medis',
  'ijazah', 'sertifikat', 'transkrip_nilai', 'sk_pegawai', 'npwp', 'nomor_npwp', 'bpjs', 'nomor_bpjs',
  'kartu_kredit', 'nomor_kartu_kredit', 'cvv', 'kadaluarsa_kartu', 'alamat_email', 'email_address',
  'nomor_telepon', 'phone_number', 'data_pribadi', 'personal_data', 'dump', 'export', 'backup_db',
  'admin_pass', 'root_pass', 'internal', 'restricted', 'sensitive_data', 'ssn', 'social_security_number',
  'passport_number', 'nomor_paspor', 'driver_license', 'nomor_sim', 'sim_c', 'sim_a',
  'bank_statement', 'laporan_keuangan', 'kontrak_kerja', 'perjanjian_kerahasiaan', 'nda',
  'daftar_hadir', 'absensi', 'data_karyawan', 'data_nasabah', 'data_mahasiswa', 'data_siswa',
  'data_pasien', 'billing_statement', 'tagihan', 'invoice', 'faktur', 'purchase_order',
  'laporan_audit', 'investigation_report', 'source_code', 'kode_sumber', 'algoritma',
  'blueprint', 'desain_produk', 'strategi_bisnis', 'rencana_pemasaran', 'minutes_of_meeting', 'notulen_rapat',
  'surat_keputusan', 'sk_direksi', 'akta_pendirian', 'company_registration', 'siup', 'tdp',
  'dokumen_hukum', 'legal_document', 'somasi', 'litigation', 'arbitration_documents',
  'voter_data', 'data_pemilih', 'dpt', 'daftar_pemilih_tetap', 'survey_results', 'hasil_survei_internal',
  'security_vulnerability', 'celah_keamanan', 'exploit_code', 'penetration_test_report',
  'incident_response_plan', 'disaster_recovery_plan', 'log_server', 'access_log', 'error_log',
  'data_kependudukan', 'sensus_penduduk', 'pajak_bumi_bangunan', 'sppt_pbb',
  'nomor_induk_mahasiswa', 'nim', 'nomor_induk_pegawai', 'nip', 'nomor_ujian_nasional', 'nun'
].join(', ');

export const DEFAULT_FILE_EXTENSIONS = [
  'txt', 'csv', 'sql', 'json', 'xml', 'yaml', 'yml', 'ini', 'conf', 'config', 'cfg',
  'log', 'md', 'rtf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'odt', 'ods', 'odp', 'pdf',
  'zip', 'rar', '7z', 'tar', 'gz', 'bz2', 'tgz', 'tbz',
  'db', 'sqlite', 'mdb', 'accdb', 'bak', 'dump', 'sqlitedb', 'sqlite3',
  'pem', 'key', 'crt', 'p12', 'pfx', 'asc', 'gpg', 'pgp',
  'sh', 'bat', 'ps1', 'py', 'rb', 'php', 'java', 'js', 'ts', 'cs', 'cpp', 'c', 'h', 'hpp',
  'env', 'kdbx', 'properties', 'cer', 'der', 'jks', 'keystore', 'p7b', 'p7c', 'pub', 'pem'
].join(', ');


export const DEFAULT_SEED_URLS = [
  'https://pastebin.com',
  'https://gist.github.com',
  'https://jsfiddle.net',
  'https://codepen.io',
  'https://ideone.com',
  'https://controlc.com',
  'https://throwbin.io',
  'http://dpaste.com',
  'https://justpaste.it',
  'https://rentry.co',
  'https://ghostbin.co',
  'https://slexy.org',
  'https://pastie.io', // check domain availability
  // Indonesian specific paste sites or forums if any are known and public
  'https://www.kaskus.co.id/forum/64/pemrograman', // Example forum section
  'https://www.kaskus.co.id/forum/269/data-center-hosting-domain-name',
  'https://forum.detik.com/',
  // Public cloud storage buckets often misconfigured (use with caution and ethically)
  // These are not direct URLs but concepts for dorks:
  // e.g., site:s3.amazonaws.com intitle:"index of" "backup"
  // e.g., site:storage.googleapis.com intitle:"index of" "confidential"
  // e.g., site:blob.core.windows.net intitle:"index of" "database"
  // Public Trello boards (dork: site:trello.com "password" OR "username")
  // Public Jira instances (dork: intitle:"Dashboard - Jira" "Project") - needs very specific keywords
  // Developer forums
  'https://stackoverflow.com',
  'https://github.com/search?q=token+language%3AJSON&type=code', // Example conceptual search
  'https://gitlab.com/explore',
  // File sharing services (use dorks for these)
  // e.g., site:mega.nz "confidential" OR "database"
  // e.g., site:mediafire.com "backup" OR "sql"
  // Publicly accessible FTP servers (dork: intitle:"index of" "ftp" "backup")
].join('\n');


export const DEFAULT_SEARCH_DORKS = [
  // General Sensitive Data Dorks
  'filetype:sql "username" "password" site:*.id',
  'filetype:csv "email" "phone" "nama_lengkap" site:*.id',
  'filetype:json "api_key" OR "secret_key" site:*.id',
  'filetype:log "login" "password" "error" site:*.id',
  'filetype:txt "confidential" "internal" "rahasia" site:*.id',
  'inurl:backup intitle:"index of" "database" OR "db" site:*.id',
  'inurl:config intitle:"index of" "*.conf" OR "*.ini" site:*.id',
  'filetype:pem OR filetype:key "private key" site:*.id',
  'filetype:env "DB_PASSWORD" OR "AWS_SECRET_ACCESS_KEY" site:*.id',
  'intitle:"phpinfo()" "mysql" OR "pgsql" site:*.id',

  // Indonesian Government (.go.id) Specific Dorks
  'site:*.go.id filetype:pdf "surat keputusan" OR "notulen rapat"',
  'site:*.go.id filetype:xlsx "daftar pegawai" OR "absensi" OR "gaji"',
  'site:*.go.id filetype:docx "kontrak" OR "perjanjian"',
  'site:*.go.id intitle:"index of" "backup" OR "data" OR "dokumen"',
  'site:*.go.id inurl:/uploads/ "NIK" OR "KTP" OR "KK"',
  'site:*.go.id filetype:sql "database_backup" OR "dump"',
  'site:*.go.id filetype:zip OR filetype:rar "archive" "confidential"',
  'site:*.go.id intext:"username" intext:"password" ext:log',
  'site:*.go.id filetype:xls "nomor_rekening" OR "rincian_biaya"',
  'site:*.go.id intitle:"dashboard" inurl:admin "login"', // Look for admin panels

  // Indonesian Academic (.ac.id) Specific Dorks
  'site:*.ac.id filetype:pdf "transkrip nilai" OR "ijazah" OR "NIM"',
  'site:*.ac.id filetype:xlsx "data mahasiswa" OR "daftar dosen"',
  'site:*.ac.id filetype:sql "db_akademik" OR "user_mahasiswa"',
  'site:*.ac.id intitle:"index of" "penelitian" OR "skripsi" OR "tesis"',
  'site:*.ac.id inurl:/files/ "absensi_kuliah" OR "nilai_ujian"',
  'site:*.ac.id filetype:csv "email_dosen" "kontak_mahasiswa"',
  'site:*.ac.id intext:"SIAKAD" OR "Sistem Informasi Akademik" "password"', // University Information Systems
  'site:*.ac.id filetype:docx "surat_tugas" OR "laporan_penelitian"',
  'site:*.ac.id intitle:"Moodle" "user list" OR "backup"', // Moodle LMS
  'site:*.ac.id inurl:ojs "submission" "reviewer comments"', // Open Journal Systems

  // Indonesian Commercial (.co.id, .id) Specific Dorks
  'site:*.co.id filetype:csv "customer_data" OR "daftar_pelanggan" OR "nomor_telepon"',
  'site:*.id filetype:xlsx "laporan_keuangan" OR "invoice" OR "purchase_order"',
  'site:*.co.id filetype:sql "backup_toko_online" OR "user_credentials"',
  'site:*.id intitle:"index of" "marketing_data" OR "sales_report"',
  'site:*.co.id inurl:/wp-content/uploads/ "confidential" OR "internal_document"', // WordPress sites
  'site:*.id filetype:txt "api_secret" OR "payment_gateway_key"',
  'site:*.co.id intext:"username" intext:"password" ext:log "error"',
  'site:*.id filetype:json "user_profile" "transaction_history"',
  'site:*.co.id intitle:"CRM login" OR "Customer Portal"',
  'site:*.id inurl:admin "backup.zip" OR "backup.sql"',

  // Additional Advanced Dorks
  'site:drive.google.com "rahasia perusahaan" OR "data penting" share:public', // Misconfigured Google Drive
  'site:docs.google.com/spreadsheets "daftar karyawan" OR "gaji" "confidential" publish OR share', // Public Google Sheets
  'site:trello.com "internal project" "passwords" OR "api keys"', // Public Trello boards
  'site:*.firebaseio.com ".json?auth=null" -jobs -samples -examples', // Unsecured Firebase DBs
  'inurl:"/phpmyadmin/setup/index.php" site:*.id', // phpMyAdmin setup exposed
  'intitle:"Index of /" "backup.tar.gz" OR "backup.sql.gz" site:*.id',
  'filetype:env "MAIL_PASSWORD" OR "STRIPE_SECRET_KEY" site:*.id',
  'intext:"BEGIN RSA PRIVATE KEY" ext:key OR ext:pem site:*.id',
  'inurl:"/.git/config" intitle:"index of" site:*.id', // Exposed .git config
  'filetype:rdp intext:"authentication" site:*.id', // RDP files (can contain creds)

  // Dorks for finding exposed network devices or services
  'intitle:"webcamXP 5" inurl:":8080" site:*.id', // Exposed webcams
  'intitle:"NetBotz Appliance" "Log In" site:*.id', // Network monitoring devices
  'inurl:/cgi-bin/mainfunction.cgi?video_ συγκεκριμένα site:*.id', // Specific camera models
  'intitle:"SonicWALL" "SSL-VPN" site:*.id', // SonicWALL VPNs
  'intitle:"BIG-IP" "Logout" site:*.id', // F5 BIG-IP load balancers

  // More specific Indonesian context
  'site:*.go.id filetype:pdf "surat edaran internal" "rahasia"',
  'site:*.go.id filetype:xlsx "anggaran belanja" "tahun 2023" OR "tahun 2024"', // Budget documents
  'site:*.ac.id filetype:pdf "proposal penelitian" "dana hibah"',
  'site:*.ac.id filetype:docx "absensi dosen" "rekapitulasi"',
  'site:*.co.id filetype:csv "database_pelanggan_lengkap" "export"',
  'site:*.id filetype:sql "backup_data_transaksi_harian"',
  'site:lpse.*.go.id filetype:xlsx "daftar pemenang tender" OR "rincian HPS"', // LPSE (e-procurement)
  'site:*.kominfo.go.id filetype:pdf "laporan internal" OR "evaluasi kinerja"',
  'site:*.pajak.go.id filetype:xls "data wajib pajak" "restitusi"', // Tax related (highly sensitive, hypothetical)
  'site:*.bps.go.id filetype:csv "data sensus mentah" "mikrodata"', // Statistics Indonesia

  'inurl:".aws/credentials" site:github.com OR site:gitlab.com', // AWS credentials on code platforms
  'filename:.npmrc _auth OR //registry.npmjs.org/:_authToken site:github.com OR site:gitlab.com', // npm tokens
  'filename:.s3cfg password site:github.com OR site:gitlab.com', // S3 config with passwords
  'site:*.atlassian.net intitle:"Jira" "CONFIDENTIAL" OR "INTERNAL"', // Jira Cloud
  'site:*.atlassian.net intitle:"Confluence" "Restricted" "Meeting Notes"', // Confluence Cloud
  'ext:txt | ext:log | ext:ini intext:password user OR username site:*.id',
  'intitle:"index of" "htpasswd" OR ".htpasswd" site:*.id',
  'intitle:"index of" "secret_stuff" OR "private_docs" site:*.id',
  'filetype:bak inurl:admin OR inurl:backup "sql" OR "mdb" site:*.id',
  'inurl:"_profiler/config" site:*.id', // Symfony profiler config

  'site:*.go.id inurl:/assets/file/ "surat_dinas" filetype:pdf',
  'site:*.go.id inurl:/download/ "laporan_tahunan" filetype:xlsx',
  'site:*.ac.id intitle:"Direktori File" "materi_kuliah" filetype:ppt',
  'site:*.ac.id inurl:/repository/ "skripsi_full_text" filetype:pdf',
  'site:*.co.id filetype:sql "dump_database_client" confidential',
  'site:*.id intitle:"index of" "user_backups" filetype:zip',
  'site:pastebin.com "api.go.id" OR "sso.go.id" "password"',
  'site:gist.github.com "Authorization: Bearer" "go.id" OR "ac.id"',
  'filetype:jks OR filetype:keystore "password" "alias" site:*.id', // Java Keystores
  'intext:"PGP PRIVATE KEY BLOCK" filetype:asc site:*.id',

  'site:*.go.id intitle:"CCTV Login" OR "Network Camera"',
  'site:*.ac.id inurl:/phpinfo.php "environment variables"',
  'site:*.co.id filetype:config "database_connection_string"',
  'site:*.id "MySQL dump" filetype:sql text:"CREATE TABLE"',
  'site:sharepoint.com /*/Forms/AllItems.aspx "Dokumen Internal" "go.id" OR "ac.id"', // SharePoint (needs refinement)
  'site:onedrive.live.com "Confidential" "Indonesia" filetype:xlsx OR filetype:docx', // Public OneDrive
  'intitle:"rsync" "Index of /" site:*.id', // Exposed rsync directories
  'inurl:/proc/self/cwd site:*.id', // Exposed /proc/self/cwd (Linux server misconfig)
  'filetype:ovpn "BEGIN CERTIFICATE" "private key" site:*.id', // OpenVPN profiles
  'site:*.go.id ext:log "failed login attempt" "user" "ip address"',
  'site:*.ac.id filetype:csv "student_grades" "final_exam"',
  'site:*.co.id inurl:"/api/users" "email" "password_hash"', // Exposed user APIs
  'site:*.id intitle:"Grafana" "Dashboard" "Anonymous"', // Public Grafana dashboards
  'filetype:txt intext:"ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC" site:*.id', // Exposed SSH public keys (could lead to private)
  'inurl:"/.well-known/" "security.txt" site:*.id', // Security.txt files for contact info
  'site:*.go.id filetype:bac "backup database" OR "cadangan data"', // .bac common for MS SQL backups
  'site:*.go.id filetype:mdf OR filetype:ldf "database file"', // MS SQL data/log files
  'site:*.ac.id intitle:"eLearning Portal" "user export" filetype:csv',
  'site:*.co.id inurl:"_debugbar/open" "request" "response"', // Laravel Debugbar
  'site:*.id filetype:p12 OR filetype:pfx "private key password" OR "keystore password"',

  // More recent patterns
  'site:*.id intext:"access_token" intext:"refresh_token" filetype:json OR filetype:txt',
  'site:*.go.id inurl:"/exports/" intitle:"index of" "csv" OR "xlsx"',
  'site:*.ac.id inurl:"/files/private/" intitle:"index of" "student_records"',
  'site:*.co.id "MongoDB URI" filetype:env OR filetype:config',
  'site:*.id "Redis password" filetype:conf OR filetype:config',
  'site:*.go.id inurl:"api/v1/internal" "secret" OR "token"',
  'site:*.ac.id inurl:"/_next/static/" "build-manifest.json" -intext:"_app.js"', // Find Next.js build manifests
  'site:*.co.id "X-API-KEY" intext:"Authorization" filetype:log',
  'site:*.id "BEGIN OPENSSH PRIVATE KEY" filetype:pem OR filetype:key',
  'site:*.go.id "Elasticsearch dump" filetype:json OR filetype:tar.gz',

].join('\n');


export const DEFAULT_SETTINGS: SettingsData = {
  keywords: DEFAULT_KEYWORDS,
  fileExtensions: DEFAULT_FILE_EXTENSIONS,
  seedUrls: DEFAULT_SEED_URLS,
  searchDorks: DEFAULT_SEARCH_DORKS,
  crawlDepth: 2,
  respectRobotsTxt: true,
  requestDelay: 1, // seconds
};

// Define a map for file types to icons
// FILE_TYPE_EXTENSIONS maps categories to lists of extensions
export const FILE_TYPE_EXTENSIONS: Record<string, string[]> = {
  text: ['txt', 'md', 'log', 'csv', 'tsv', 'rtf', 'readme', 'text'],
  json: ['json', 'jsonl', 'geojson'],
  database: ['sql', 'db', 'sqlite', 'mdb', 'accdb', 'dump', 'bak', 'sqlitedb', 'sqlite3', 'mdf', 'ldf', 'bac'],
  archive: ['zip', 'rar', '7z', 'tar', 'gz', 'bz2', 'tgz', 'tbz', 'arj', 'iso'],
  code: ['js', 'jsx', 'ts', 'tsx', 'py', 'java', 'c', 'cpp', 'cs', 'go', 'rb', 'php', 'swift', 'kt', 'html', 'css', 'scss', 'less', 'sh', 'bat', 'ps1', 'xml', 'yaml', 'yml', 'ini', 'cfg'],
  spreadsheet: ['xls', 'xlsx', 'ods', 'numbers'],
  document: ['doc', 'docx', 'odt', 'pdf', 'pages', 'tex', 'epub', 'mobi'],
  config: ['conf', 'config', 'env', 'properties', 'toml', 'htpasswd', 'htaccess'],
  image: ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff', 'webp', 'svg', 'ico'],
  audio: ['mp3', 'wav', 'aac', 'ogg', 'flac', 'm4a'],
  video: ['mp4', 'mkv', 'avi', 'mov', 'wmv', 'flv', 'webm'],
  certificate: ['pem', 'key', 'crt', 'cer', 'der', 'p12', 'pfx', 'jks', 'keystore', 'p7b', 'p7c', 'pub', 'asc', 'gpg', 'pgp'],
  font: ['ttf', 'otf', 'woff', 'woff2', 'eot'],
  executable: ['exe', 'dll', 'so', 'dylib', 'app', 'msi', 'dmg'],
  presentation: ['ppt', 'pptx', 'odp', 'key'],
  kdbx: ['kdbx'], // KeePass database
  rdp: ['rdp'], // Remote Desktop Protocol
  ovpn: ['ovpn'], // OpenVPN configuration
};

export const getFileTypeCategory = (extension: string): string => {
  const ext = extension.toLowerCase().replace('.', '');
  for (const category in FILE_TYPE_EXTENSIONS) {
    if (FILE_TYPE_EXTENSIONS[category].includes(ext)) {
      return category;
    }
  }
  return 'unknown'; // Default category if not found
};
