
import type { BreachData, NavItem, SettingsData } from '@/types';
import { LayoutDashboard, Settings, ShieldAlert, Info } from 'lucide-react';

export const APP_NAME = 'BreachWatch';

export const NAV_LINKS: NavItem[] = [
  {
    title: 'Dashboard',
    href: '/dashboard',
    icon: LayoutDashboard,
  },
  {
    title: 'Settings',
    href: '/settings',
    icon: Settings,
  },
  {
    title: 'Ethical Guidelines',
    href: '/guidelines',
    icon: Info,
  }
];

export const MOCK_BREACH_DATA: BreachData[] = [
  { 
    id: '1', 
    sourceUrl: 'https://example.com/forum/thread1', 
    fileUrl: 'https://cdn.example.com/data_dump.txt', 
    fileType: 'txt', 
    dateFound: new Date().toISOString(), 
    keywords: ['passwords', 'users', 'credentials'],
    status: 'new',
  },
  { 
    id: '2', 
    sourceUrl: 'https://another-site.org/leaks', 
    fileUrl: 'https://another-site.org/leaks/customer_db.sql.gz', 
    fileType: 'sql.gz', 
    dateFound: new Date(Date.now() - 86400000 * 2).toISOString(), // 2 days ago
    keywords: ['database', 'customer_info', 'backup'],
    status: 'reviewed',
  },
  { 
    id: '3', 
    sourceUrl: 'http://public-files.net/archive', 
    fileUrl: 'http://public-files.net/archive/full_backup_2023.zip', 
    fileType: 'zip', 
    dateFound: new Date(Date.now() - 86400000 * 5).toISOString(), // 5 days ago
    keywords: ['backup', 'archive', 'confidential_data'],
    status: 'new',
  },
  { 
    id: '4', 
    sourceUrl: 'https://pastebin.com/xyz123', 
    fileUrl: 'https://pastebin.com/raw/xyz123', 
    fileType: 'json', 
    dateFound: new Date(Date.now() - 86400000 * 1).toISOString(), // 1 day ago
    keywords: ['api_keys', 'tokens', 'credentials.json'],
    status: 'ignored',
  },
  { 
    id: '5', 
    sourceUrl: 'https://internal-docs.com/data', 
    fileUrl: 'https://internal-docs.com/data/employee_records.xlsx', 
    fileType: 'xlsx', 
    dateFound: new Date(Date.now() - 86400000 * 10).toISOString(), // 10 days ago
    keywords: ['employee_data', 'salary_info', 'PII'],
    status: 'new',
  },
   { 
    id: '6', 
    sourceUrl: 'https://s3.public-bucket.aws/data', 
    fileUrl: 'https://s3.public-bucket.aws/data/user_details.csv', 
    fileType: 'csv', 
    dateFound: new Date(Date.now() - 86400000 * 3).toISOString(), 
    keywords: ['user_details', 'email', 'address'],
    status: 'reviewed',
  },
  { 
    id: '7', 
    sourceUrl: 'ftp://ftp.company.com/backups', 
    fileUrl: 'ftp://ftp.company.com/backups/website_backup.tar.gz', 
    fileType: 'tar.gz', 
    dateFound: new Date(Date.now() - 86400000 * 7).toISOString(), 
    keywords: ['website_backup', 'source_code', 'database'],
    status: 'new',
  },
  {
    id: '8',
    sourceUrl: 'https://research-data.edu/public',
    fileUrl: 'https://research-data.edu/public/study_participants.db',
    fileType: 'db',
    dateFound: new Date(Date.now() - 86400000 * 15).toISOString(),
    keywords: ['participants', 'research_study', 'sensitive_data'],
    status: 'new',
  },
  {
    id: '9',
    sourceUrl: 'https://dev-server.com/tmp/',
    fileUrl: 'https://dev-server.com/tmp/old_config.bak',
    fileType: 'bak',
    dateFound: new Date(Date.now() - 86400000 * 4).toISOString(),
    keywords: ['config_backup', 'server_settings', 'credentials'],
    status: 'ignored',
  },
  {
    id: '10',
    sourceUrl: 'https://data-terbuka.go.id/expose/datawarga.csv',
    fileUrl: 'https://data-terbuka.go.id/expose/datawarga.csv',
    fileType: 'csv',
    dateFound: new Date(Date.now() - 86400000 * 2).toISOString(),
    keywords: ['NIK', 'nama_lengkap', 'alamat', 'no_ktp', 'data_penduduk'],
    status: 'new',
  },
  {
    id: '11',
    sourceUrl: 'https://kebocoran-data.web.id/files/kk_database.sql',
    fileUrl: 'https://kebocoran-data.web.id/files/kk_database.sql',
    fileType: 'sql',
    dateFound: new Date(Date.now() - 86400000 * 6).toISOString(),
    keywords: ['kartu_keluarga', 'nomor_kk', 'anggota_keluarga', 'database_warga'],
    status: 'reviewed',
  },
  {
    id: '12',
    sourceUrl: 'https://paste.leakedsource.info/view/randomidpaste',
    fileUrl: 'https://paste.leakedsource.info/raw/randomidpaste',
    fileType: 'txt',
    dateFound: new Date(Date.now() - 86400000 * 1).toISOString(),
    keywords: ['nomor_induk_kependudukan', 'tanggal_lahir', 'bpjs_kesehatan', 'npwp_pribadi'],
    status: 'new',
  }
];

export const DEFAULT_SETTINGS: SettingsData = {
  keywords: "password, secret, api_key, token, credential, private_key, backup, dump, leak, user, admin, config, NIK, no_ktp, nama_lengkap, nomor_induk_kependudukan, kartu_keluarga, nomor_kk, tempat_lahir, tanggal_lahir, alamat, bpjs, npwp, no_hp, email",
  fileExtensions: ".txt, .csv, .sql, .json, .xlsx, .db, .bak, .zip, .gz, .tar.gz, .7z, .rar, .log, .config, .yml, .yaml, .env",
  seedUrls: "https://pastebin.com\n" +
            "https://gist.github.com\n" +
            "https://sitedata.web.id/records/\n" +
            "https://ghostbin.co/\n" +
            "https://throwbin.io/\n" +
            "https://pastelink.net/\n" +
            "https://justpaste.it/\n" +
            "https://controlc.com/\n" +
            "https://0bin.net/\n" +
            "https://dev.to/search?q=leak%20indonesia\n" +
            "https://medium.com/search?q=data%20breach%20indonesia\n" +
            "https://anonfiles.com/\n" +
            "https://bayfiles.com/\n" +
            "https://data.go.id/\n" +
            "https://www.kaskus.co.id/forum/search?q=kebocoran%20data\n" +
            "https://glasp.co/paste",
  searchDorks: 'intitle:"index of" "backup"\n' +
               'filetype:sql "passwords"\n' +
               'site:*.s3.amazonaws.com "dump.sql"\n' +
               'filetype:csv "NIK" OR "no_ktp"\n' +
               'intitle:"index of" "database" "indonesia"\n' +
               'site:pastebin.com intext:"NIK" OR intext:"No. KTP" OR intext:"Kartu Tanda Penduduk" "Indonesia"\n' +
               'site:scribd.com "NIK" OR "KTP" "Indonesia" filetype:pdf OR filetype:doc OR filetype:xls\n' +
               'filetype:xls OR filetype:xlsx "daftar nama" "NIK" "Indonesia"\n' +
               'inurl:.go.id filetype:csv OR filetype:xls "data penduduk" OR "data pemilih"\n' +
               'site:drive.google.com "share" "NIK" OR "KTP" "Indonesia"\n' +
               'site:*.id intitle:"index of" "database" OR "backup" OR "data"\n' +
               'intext:"Nomor Induk Kependudukan" OR intext:"Kartu Keluarga" filetype:pdf OR filetype:doc site:*.id\n' +
               'filetype:json "nama_lengkap" "alamat" "no_hp" site:*.id\n' +
               '"Rahasia Negara" OR "Dokumen Rahasia" filetype:pdf site:.go.id\n' +
               'site:*.cloud.google.com OR site:*.digitaloceanspaces.com "backup.zip" OR "database.sql" "indonesia"\n' +
               'site:storage.googleapis.com "data_sensitif" "indonesia"\n' +
               'ext:bkf OR ext:dat OR ext:sql OR ext:zip "backup" "database" "indonesia"\n' +
               '"DATABASE DUMP" "user" "password" site:*.id\n' +
               'site:glasp.co intext:"username" intext:"password" "indonesia"\n' +
               'inurl:ftp -inurl:(http|https) site:*.id "backup" OR "confidential"',
  crawlDepth: 2,
  respectRobotsTxt: true,
  requestDelay: 1,
};

export const FILE_TYPE_EXTENSIONS: { [key: string]: string[] } = {
  text: ['txt', 'md', 'log', 'conf', 'cfg', 'ini', 'rtf', 'yaml', 'yml'],
  json: ['json', 'geojson', 'jsonl'],
  database: ['sql', 'db', 'sqlite', 'mdb', 'bak', 'dump'],
  archive: ['zip', 'tar', 'gz', 'tar.gz', 'bz2', 'tar.bz2', '7z', 'rar'],
  code: ['py', 'js', 'java', 'php', 'rb', 'c', 'cpp', 'cs', 'go', 'sh', 'bat', 'ps1', 'html', 'css', 'xml'],
  spreadsheet: ['csv', 'xls', 'xlsx', 'ods'],
  document: ['doc', 'docx', 'pdf', 'odt', 'ppt', 'pptx'],
  config: ['env', 'pem', 'key', 'crt', 'cer', 'p12', 'pfx'],
  unknown: [],
};


    
