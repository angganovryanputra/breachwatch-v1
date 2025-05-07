
import type { NavItem, SettingsData } from '@/types';
import { LayoutDashboard, Settings, ShieldAlert, Info, HardDriveDownload } from 'lucide-react';

export const APP_NAME = 'BreachWatch';
// DOWNLOADED_FILES_STORAGE_KEY is no longer primary source, but can be kept for other local preferences.
export const DOWNLOADED_FILES_STORAGE_KEY = 'breachWatchLocalPreferences'; 

export const NAV_LINKS: NavItem[] = [
  {
    title: 'Dashboard', // Shows files discovered by backend crawlers
    href: '/dashboard',
    icon: LayoutDashboard,
  },
  {
    title: 'File Records', // Shows all DownloadedFile entries from backend DB
    href: '/downloaded-files',
    icon: HardDriveDownload,
  },
  {
    title: 'Settings', // Configure new crawl jobs
    href: '/settings',
    icon: Settings,
  },
  {
    title: 'Ethical Guidelines',
    href: '/guidelines',
    icon: Info,
  }
];

// Default settings for the frontend form
export const DEFAULT_SETTINGS: SettingsData = {
  keywords: "password, secret, api_key, token, credential, private_key, backup, dump, leak, user, admin, config, NIK, no_ktp, nama_lengkap, nomor_induk_kependudukan, kartu_keluarga, nomor_kk, tempat_lahir, tanggal_lahir, alamat, bpjs, npwp, no_hp, email, rahasia, data_pribadi, identitas, pengguna, sandi, database, internal, konfidensial, data_nasabah, data_karyawan, data_mahasiswa, data_pasien",
  fileExtensions: "txt, csv, sql, json, xlsx, db, bak, zip, gz, tar.gz, 7z, rar, log, config, yml, yaml, env, pem, key, crt, p12, pfx, doc, docx, pdf, xls, ppt, pptx, mdb, sqlite", // Store without leading dots for form
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
            "https://satudata.go.id/\n" +
            "https://data.jakarta.go.id/\n" +
            "https://data.bandung.go.id/\n" +
            "https://data.surabaya.go.id/\n" +
            "https://data.jogjaprov.go.id/\n" +
            "https://data.semarangkota.go.id/\n" +
            "https://www.kaskus.co.id/forum/search?q=kebocoran%20data\n" +
            "https://www.kaskus.co.id/forum/search?q=data%20bocor\n" +
            "https://glasp.co/paste\n" +
            "https://textuploader.com/\n" +
            "https://paste.ee/\n" +
            "https://paste.myst.rs/\n" +
            "https://paste.gg/\n" +
            "https://paste.firnsy.com/\n" +
            "https://paste.centos.org/\n" +
            "https://paste.debian.net/\n" +
            "https://paste.opensuse.org/\n" +
            "https://github.com/search?q=indonesia+leak+database&type=code\n" +
            "https://gitlab.com/explore?scope=all&search=indonesia+data+bocor\n" +
            "https://bitbucket.org/dashboard/repositories?search_term=indonesia+confidential\n" +
            "https://sourceforge.net/directory/?q=indonesia%20database\n" +
            "https://archive.org/search.php?query=indonesia%20data%20leak\n" +
            "https://www.slideshare.net/search?q=data%20pribadi%20indonesia\n" +
            "https://www.scribd.com/search?content_type=documents&query=NIK%20KTP%20Indonesia\n" +
            "https://www.academia.edu/search?q=data%20penduduk%20indonesia\n" +
            "https://www.researchgate.net/search.Search.html?query=indonesian%20personal%20data\n" +
            "https://hub.docker.com/search?q=indonesia_database&type=image\n" +
            "https://search.censys.io/search?resource=hosts&q=services.http.response.html_title%3A%22Index%20of%22%20AND%20autonomous_system.country_code%3A%20ID%20AND%20services.http.response.body%3A%22backup%22\n" +
            "https://www.shodan.io/search?query=country%3A%22ID%22+http.title%3A%22Index+of%22+%22.sql%22\n" +
            "https://www.zoomeye.org/searchResult?q=country%3A%22Indonesia%22%20%2Btitle%3A%22Index%20of%22%20%2B%22.zip%22\n" +
            "https://fofa.info/result?qbase64=Y291bnRyeT0iSUQiICYmIHRpdGxlPSJJbmRleCBvZiIgJiYgYm9keT0iLmNzdignJw%3D%3D\n" +
            "https://repository.ui.ac.id/\n" +
            "https://repository.itb.ac.id/\n" +
            "https://repository.ugm.ac.id/\n" +
            "https://repository.ipb.ac.id/\n" +
            "https://repository.unair.ac.id/\n" +
            "https://repository.undip.ac.id/\n" +
            "https://repository.its.ac.id/\n" +
            "https://dspace.uii.ac.id/\n" +
            "https://mediafire.com/\n" +
            "https://zippyshare.com/\n" + 
            "https://mega.nz/\n" +
            "https://gofile.io/\n" +
            "https://anonfiles.com/\n" +
            "https://sendspace.com/\n" +
            "https://mirrored.to/\n" + 
            "https://filetransfer.io/\n" +
            "https://transfer.sh/\n" +
            "https://wetransfer.com/\n" + 
            "https://linktr.ee/search/indonesia%20data%20leak\n" + 
            "https://beacons.ai/search/indonesia%20data%20breach",
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
               'inurl:ftp -inurl:(http|https) site:*.id "backup" OR "confidential"\n' +
               'site:*.go.id filetype:env "DB_PASSWORD" OR "API_KEY" OR "SECRET_KEY"\n' +
               'site:*.ac.id intitle:"index of" "confidential" OR "private" OR "restricted"\n' +
               'site:*.co.id filetype:log "error" "password" OR "failed login"\n' +
               'site:*.go.id inurl:"/uploads/" ext:doc OR ext:docx OR ext:pdf "internal"\n' +
               'site:*.ac.id filetype:bak OR filetype:old "config" OR "database" OR "settings"\n' +
               'site:*.co.id intext:"client_secret" OR intext:"client_id" ext:json OR ext:config\n' +
               'site:*.go.id "phpinfo()" "mysql password" OR "pgsql password"\n' +
               'site:*.ac.id filetype:pem OR filetype:key "PRIVATE KEY" -github -gitlab\n' +
               'site:*.co.id intitle:"Directory Listing For /" "backup" OR "archive"\n' +
               'site:*.go.id ext:txt OR ext:csv "userlist" OR "memberlist" OR "emaillist"\n' +
               'site:*.ac.id filetype:mdb "tblUsers" OR "tblStudents" OR "tblLecturers"\n' +
               'site:*.co.id inurl:"/admin/backup" OR inurl:"/wp-content/backups/"\n' +
               'site:*.go.id filetype:pst OR filetype:ost "backup" OR "archive"\n' +
               'site:*.ac.id "student_records.zip" OR "academic_data.rar" intitle:"index of"\n' +
               'site:*.co.id filetype:xlsx OR filetype:xls "salary" OR "payroll" "internal"\n' +
               'site:*.go.id "Daftar Pemilih Tetap" OR "DPT" ext:pdf OR ext:csv OR ext:xls\n' +
               'site:*.ac.id intext:"research data" "confidential" filetype:zip OR filetype:rar\n' +
               'site:*.co.id "customer_database" OR "client_data" ext:sql OR ext:csv OR ext:db\n' +
               'site:*.go.id filetype:gitconfig "user" "email" "password"\n' +
               'site:*.ac.id "exam_results" OR "student_grades" ext:pdf OR ext:xls OR ext:xlsx\n' +
               'site:*.co.id ".env" "APP_DEBUG=true" "DB_PASSWORD"\n' +
               'site:*.go.id "Surat Keputusan" "Rahasia" OR "Terbatas" filetype:pdf OR filetype:doc\n' +
               'site:*.ac.id "Data Mahasiswa" OR "Biodata Dosen" filetype:csv OR filetype:xlsx OR filetype:json\n' +
               'site:*.co.id "Laporan Keuangan Internal" OR "Rencana Bisnis Rahasia" filetype:pdf OR filetype:xls\n' +
               'site:*.go.id inurl:"/_vti_bin/" OR inurl:"/_layouts/" "confidential" (SharePoint)\n' +
               'site:*.ac.id intitle:"index of" ".htpasswd" OR ".htaccess" "password"\n' +
               'site:*.co.id "wp-config.php" "DB_PASSWORD" OR "AUTH_KEY" -git\n' +
               'site:*.go.id "kartu keluarga scan" OR "ktp scan" filetype:jpg OR filetype:png OR filetype:pdf\n' +
               'site:*.ac.id "transkrip nilai" OR "ijazah scan" filetype:pdf OR filetype:jpg\n' +
               'site:*.co.id "nomor rekening" "nama bank" "saldo" filetype:xls OR filetype:csv\n' +
               'site:*.go.id "database error" "MySQL" OR "PostgreSQL" "dump" OR "backup"\n' +
               'site:*.ac.id filetype:sql.gz OR filetype:sql.zip "dump" OR "backup" "database"\n' +
               'site:*.co.id "secret_access_key" OR "aws_access_key_id" filetype:yml OR filetype:yaml OR filetype:json\n' +
               'site:*.go.id filetype:log "access_log" "admin" OR "login" "password"\n' +
               'site:*.ac.id intitle:"phpMyAdmin" "Export" "SQL" "database"\n' +
               'site:*.co.id inurl:"/backup/" "full_site_backup.zip" OR "website_archive.tar.gz"\n' +
               'site:*.go.id "data_bpjs.csv" OR "peserta_jamkesmas.xls" intitle:"index of"\n' +
               'site:*.ac.id filetype:json "student_id" "email" "phone_number" "address"\n' +
               'site:*.co.id "proprietary_source_code.zip" OR "internal_software.rar" intitle:"index of"\n' +
               'site:storage.googleapis.com "indonesia" "ktp" OR "nik" OR "database" ext:csv OR ext:sql OR ext:json\n' +
               'site:digitaloceanspaces.com "indonesia" "database_dump" OR "backup" ext:zip OR ext:sql.gz\n' +
               'site:*.blob.core.windows.net "indonesia" "backup" OR "confidential" filetype:zip OR filetype:bak\n' +
               'site:*.go.id "Rapat Internal" "Notulen" "Rahasia" filetype:pdf OR filetype:doc\n' +
               'site:*.ac.id "Surat Tugas" filetype:doc OR filetype:pdf "Rahasia" OR "Penting"\n' +
               'site:*.co.id "Daftar Gaji Karyawan" OR "Employee Salary" filetype:xls OR filetype:xlsx\n' +
               'site:*.go.id filetype:sh "backup.sh" "password" OR "API_TOKEN"\n' +
               'site:*.ac.id "sertifikat_tanah.pdf" OR "bukti_kepemilikan.jpg" "pribadi"\n' +
               'site:*.co.id "MOU_confidential.doc" OR "NDA_internal.pdf"\n' +
               'site:*.go.id inurl:/uploads/ "data_penerima_bantuan.csv" OR "list_beneficiary.xls"\n' +
               'site:*.ac.id filetype:sql "tbl_mahasiswa" OR "tabel_dosen" "password" OR "email"\n' +
               'site:*.co.id "database_pelanggan.bak" OR "customer_db.dump" intitle:"index of"\n' +
               'site:*.go.id "dokumen_tender_rahasia.pdf" OR "procurement_secret.doc"\n' +
               'site:*.ac.id "jadwal_ujian_privat.xlsx" OR "student_assessment_confidential.csv"\n' +
               'site:*.co.id "api_credentials.txt" OR "server_keys.json" intitle:"index of"\n' +
               'site:*.go.id inurl:"/secure_files/" "ktp_scan.jpg" OR "kk_scan.pdf"\n' +
               'site:*.ac.id "proposal_hibah_internal.doc" OR "research_grant_sensitive.pdf"\n' +
               'site:*.co.id "backup_config_server.zip" OR "network_topology_confidential.rar"\n' +
               'site:*.go.id filetype:pem OR filetype:key "private.key" OR "cert.key" "BEGIN RSA PRIVATE KEY"\n' +
               'site:*.ac.id "data_alumni_lengkap.csv" OR "graduate_database.xls" "kontak"\n' +
               'site:*.co.id "strategi_bisnis_rahasia.pptx" OR "marketing_plan_confidential.pdf"\n' +
               'site:*.go.id "log_audit_sistem.txt" OR "security_event.log" "critical" OR "failure"\n' +
               'site:*.ac.id "file_sharing_internal/" "data_riset" OR "student_projects" ext:zip\n' +
               'site:*.co.id "password_list.txt" OR "kredensial.xls" OR "credential_dump.sql"\n' +
               'site:*.go.id intext:"Nomor Kartu Keluarga" filetype:pdf OR filetype:jpg OR filetype:png "scan"\n' +
               'site:*.ac.id filetype:json "student_id" "email" "phone_number" "date_of_birth"\n' +
               'site:*.co.id "proprietary_source_code.zip" OR "internal_app_src.rar" "confidential"\n' +
               'site:github.com "indonesia" ".go.id" "password" OR "api_key" OR "secret"\n' +
               'site:gitlab.com "indonesia" ".ac.id" "database" "config" "password"\n' +
               'site:bitbucket.org "indonesia" ".co.id" "private_key" OR ".env"\n' +
               'site:*.go.id intitle:"index of" ".git" -github -gitlab -bitbucket (exposed .git repo)\n' +
               'site:*.ac.id intitle:"index of" "node_modules" "package.json" (exposed dev folders)\n' +
               'site:*.co.id intitle:"index of" "vendor" "composer.json" (PHP dependencies)\n' +
               'site:*.go.id ext:log "apache" "access" "error" "ip address"\n' +
               'site:*.ac.id ext:config "connectionstring" "password"\n' +
               'site:*.co.id ext:rdp "admin" "credentials" (Remote Desktop Files)\n' +
               'site:*.go.id inurl:jmx-console "jboss" "admin" (JBoss console)\n' +
               'site:*.ac.id filetype:ora "tnsnames.ora" "password" (Oracle DB config)\n' +
               'site:*.co.id "web.config" "connectionStrings" "password" (ASP.NET config)\n' +
               'site:*.go.id intitle:"Swagger UI" "API" "token" OR "key"\n' +
               'site:*.ac.id filetype:txt "dump" "database" "user" "password"\n' +
               'site:*.co.id inurl:"/api/debug" "trace" "stack" "password"\n' +
               'site:*.go.id filetype:csv "data_pegawai" "gaji" OR "tunjangan"\n' +
               'site:*.ac.id filetype:pdf "surat_keterangan_aktif_kuliah" "NIK"\n' +
               'site:*.co.id filetype:xls "daftar_nasabah" "nomor_rekening" "saldo"\n' +
               'site:*.go.id intitle:"index of /backup_db/" ext:sql OR ext:zip OR ext:gz\n' +
               'site:*.ac.id inurl:".aws/credentials" OR inurl:".aws/config"\n' +
               'site:*.co.id filetype:jks OR filetype:keystore "password" "alias"\n' +
               'site:*.go.id "Jenkins" "credentials.xml" "password"\n' +
               'site:*.ac.id intitle:"Grafana" "dashboard" "datasource" "password"\n' +
               'site:*.co.id filetype:kdbx "database" "password" (KeePass files)\n' +
               'site:*.go.id "ELK" "Kibana" "security" "password" (Elastic Stack)\n' +
               'site:*.ac.id filetype:csv "data_penelitian_ responden" "nama" "alamat" "kontak"\n' +
               'site:*.co.id intitle:"index of" ".ssh" "id_rsa" OR "known_hosts"\n' +
               'site:*.go.id "data_kependudukan_detail.xlsx" "NIK" "KK" "Nama"\n' +
               'site:*.ac.id "arsip_digital_kampus.zip" "dokumen_penting"\n' +
               'site:*.co.id "minutes_of_meeting_confidential.pdf" "internal"\n' +
               'site:*.go.id inurl:"/cgi-bin/" ext:pl OR ext:cgi "password"\n' +
               'site:*.ac.id filetype:ipynb "secret_key" OR "api_token" (Jupyter Notebooks)\n' +
               'site:*.co.id "docker-compose.yml" "environment" "PASSWORD"\n' +
               'site:*.go.id filetype:json "geojson" "batas_wilayah" "sensitif"\n' +
               'site:*.ac.id "data_ukt_mahasiswa.csv" "penghasilan_orang_tua"\n' +
               'site:*.co.id "shadow" OR "master.passwd" intitle:"index of" (System password files)\n' +
               'site:*.go.id "surat_perintah_tugas_rahasia.pdf"\n' +
               'site:*.ac.id "log_absensi_dosen_staff.xlsx"\n' +
               'site:*.co.id "source_code_internal_project.7z"\n' +
               'site:*.go.id intext:"NIP" intext:"GOLONGAN" intext:"JABATAN" filetype:xls OR filetype:pdf\n' +
               'site:*.ac.id filetype:bac "database_backup" (SQL Anywhere backup)\n' +
               'site:*.co.id intitle:"phpPgAdmin" "database" "PostgreSQL"\n' +
               'site:*.go.id "dokumen_aset_negara.pdf" "rahasia"\n' +
               'site:*.ac.id filetype:mdf OR filetype:ldf "database" "backup" (MS SQL files)\n' +
               'site:*.co.id "sales_report_confidential.xlsx" "target" "achievement"\n',
  crawlDepth: 2,
  respectRobotsTxt: true,
  requestDelay: 1,
};

export const FILE_TYPE_EXTENSIONS: { [key: string]: string[] } = {
  text: ['txt', 'md', 'log', 'conf', 'cfg', 'ini', 'rtf', 'yaml', 'yml'],
  json: ['json', 'geojson', 'jsonl'],
  database: ['sql', 'db', 'sqlite', 'mdb', 'bak', 'dump', 'mdf', 'ldf', 'bac'],
  archive: ['zip', 'tar', 'gz', 'tar.gz', 'bz2', 'tar.bz2', '7z', 'rar'],
  code: ['py', 'js', 'java', 'php', 'rb', 'c', 'cpp', 'cs', 'go', 'sh', 'bat', 'ps1', 'html', 'css', 'xml', 'ipynb', 'pl', 'cgi'],
  spreadsheet: ['csv', 'xls', 'xlsx', 'ods'],
  document: ['doc', 'docx', 'pdf', 'odt', 'ppt', 'pptx'],
  config: ['env', 'pem', 'key', 'crt', 'p12', 'pfx', 'gitconfig', 'ora', 'web.config', 'jks', 'keystore', 'kdbx', 'htpasswd', 'htaccess'],
  image: ['png', 'jpg', 'jpeg', 'gif', 'svg', 'webp', 'bmp', 'tiff'], // Added more image types
  audio: ['mp3', 'wav', 'ogg', 'aac', 'flac', 'm4a'], // Added more audio types
  video: ['mp4', 'mov', 'avi', 'mkv', 'webm', 'flv', 'wmv'], // Added more video types
  unknown: [], // For files where type couldn't be determined
};
