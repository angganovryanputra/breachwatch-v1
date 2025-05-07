import type { LucideIcon } from 'lucide-react';
import { FileText, FileJson2, DatabaseZap, FileArchive, FileCode2, FileSpreadsheet, FileQuestion, FileImage, FileAudio, FileVideo } from 'lucide-react';
import { FILE_TYPE_EXTENSIONS } from '@/lib/constants';

interface FileTypeIconProps {
  fileTypeOrExt: string;
  className?: string;
}

const getIconForFileType = (typeOrExt: string): LucideIcon => {
  const normalizedType = typeOrExt.toLowerCase().replace('.', '');

  if (FILE_TYPE_EXTENSIONS.text.includes(normalizedType)) return FileText;
  if (FILE_TYPE_EXTENSIONS.json.includes(normalizedType)) return FileJson2;
  if (FILE_TYPE_EXTENSIONS.database.includes(normalizedType)) return DatabaseZap;
  if (FILE_TYPE_EXTENSIONS.archive.includes(normalizedType)) return FileArchive;
  if (FILE_TYPE_EXTENSIONS.code.includes(normalizedType)) return FileCode2;
  if (FILE_TYPE_EXTENSIONS.spreadsheet.includes(normalizedType)) return FileSpreadsheet;
  if (FILE_TYPE_EXTENSIONS.document.includes(normalizedType)) return FileText; // Using FileText for general documents
  if (FILE_TYPE_EXTENSIONS.config.includes(normalizedType)) return FileCode2; // Using FileCode for config files

  // Fallback for common extensions not explicitly listed
  if (['png', 'jpg', 'jpeg', 'gif', 'svg', 'webp'].includes(normalizedType)) return FileImage;
  if (['mp3', 'wav', 'ogg', 'aac'].includes(normalizedType)) return FileAudio;
  if (['mp4', 'mov', 'avi', 'mkv', 'webm'].includes(normalizedType)) return FileVideo;
  
  return FileQuestion;
};

export const FileTypeIcon: React.FC<FileTypeIconProps> = ({ fileTypeOrExt, className }) => {
  const IconComponent = getIconForFileType(fileTypeOrExt);
  return <IconComponent className={cn("h-5 w-5", className)} />;
};

// Helper function cn (similar to shadcn/ui)
function cn(...inputs: (string | undefined | null | false)[]): string {
  return inputs.filter(Boolean).join(' ');
}
