import logging
import mimetypes
from urllib.parse import urlparse
from pathlib import Path
from typing import Optional, NamedTuple
# import magic # python-magic library for more robust type detection from content

logger = logging.getLogger(__name__)

class FileMetadata(NamedTuple):
    name: str
    extension: str
    mime_type: Optional[str]
    # potential_actual_mime: Optional[str] # From magic numbers

def identify_file_type_and_name(
    url: str, 
    content_type_header: Optional[str] = None,
    file_content_bytes: Optional[bytes] = None # First few KB for magic number analysis
) -> FileMetadata:
    """
    Identifies file name, extension, and MIME type from URL and headers.
    Optionally uses file content for more accurate MIME type detection (magic numbers).
    """
    parsed_url = urlparse(url)
    path = Path(parsed_url.path)
    
    file_name = path.name
    file_extension = path.suffix.lstrip('.').lower()

    # MIME type from header
    mime_type_from_header = None
    if content_type_header:
        mime_type_from_header = content_type_header.split(';')[0].strip().lower()

    # MIME type from extension (fallback)
    mime_type_from_extension, _ = mimetypes.guess_type(url)
    
    # MIME type from content (magic numbers) - more reliable
    # potential_actual_mime_from_content = None
    # if file_content_bytes:
    #     try:
    #         potential_actual_mime_from_content = magic.from_buffer(file_content_bytes, mime=True)
    #         if potential_actual_mime_from_content == 'application/octet-stream' and mime_type_from_extension:
    #             # if magic returns generic, prefer extension's guess if available
    #             pass
    #         elif potential_actual_mime_from_content:
    #             # Potentially update file_extension if magic provides a more specific type
    #             # e.g. magic says application/zip but extension was .dat
    #             guessed_ext = mimetypes.guess_extension(potential_actual_mime_from_content)
    #             if guessed_ext and not file_extension: # Only if original extension was missing
    #                 file_extension = guessed_ext.lstrip('.').lower()
    #             elif guessed_ext and file_extension and guessed_ext.lstrip('.').lower() != file_extension:
    #                 logger.debug(f"MIME from content ({potential_actual_mime_from_content}, ext: {guessed_ext}) differs from URL ext ({file_extension}) for {url}")
    #                 # Decide on a priority or store both
    #     except Exception as e:
    #         logger.warning(f"Could not determine MIME type from content for {url} using python-magic: {e}")

    # Prioritize MIME: 1. From content (if reliable), 2. From header, 3. From extension
    final_mime_type = mime_type_from_header or mime_type_from_extension
    # if potential_actual_mime_from_content and potential_actual_mime_from_content != 'application/octet-stream':
    #    final_mime_type = potential_actual_mime_from_content
    # elif mime_type_from_header:
    #    final_mime_type = mime_type_from_header
    # else:
    #    final_mime_type = mime_type_from_extension

    # If extension is missing but MIME type implies one (and it's not generic)
    if not file_extension and final_mime_type and final_mime_type != 'application/octet-stream':
        guessed_ext = mimetypes.guess_extension(final_mime_type)
        if guessed_ext:
            file_extension = guessed_ext.lstrip('.').lower()
            # If filename didn't have an extension, append this one
            if not Path(file_name).suffix and file_extension:
                 file_name = f"{file_name}.{file_extension}"


    logger.debug(f"File identified for URL '{url}': name='{file_name}', ext='{file_extension}', mime='{final_mime_type}'")
    
    return FileMetadata(
        name=file_name, 
        extension=file_extension, 
        mime_type=final_mime_type
        # potential_actual_mime=potential_actual_mime_from_content
    )

# Example usage:
if __name__ == '__main__':
    test_url1 = "https://example.com/path/to/document.pdf?query=param"
    meta1 = identify_file_type_and_name(test_url1, "application/pdf")
    print(f"URL: {test_url1}, Meta: {meta1}")

    test_url2 = "https://example.com/archive.zip"
    meta2 = identify_file_type_and_name(test_url2, "application/zip")
    print(f"URL: {test_url2}, Meta: {meta2}")

    test_url3 = "https://example.com/data_file" # No extension in URL
    meta3 = identify_file_type_and_name(test_url3, "text/csv")
    print(f"URL: {test_url3}, Meta: {meta3}")
    
    test_url4 = "https://example.com/image.customext" # Custom extension
    # Simulate some image bytes (e.g., PNG header)
    png_header_bytes = b'\x89PNG\r\n\x1a\n' 
    # meta4 = identify_file_type_and_name(test_url4, "application/octet-stream", png_header_bytes)
    # print(f"URL: {test_url4}, Meta with content check: {meta4}")

    test_url5 = "https://cdn.example.com/file"
    meta5 = identify_file_type_and_name(test_url5, "application/sql") # Header says SQL
    print(f"URL: {test_url5}, Meta: {meta5}") # Extension will be 'sql'

    test_url6 = "https://cdn.example.com/file.custom"
    meta6 = identify_file_type_and_name(test_url6, "application/sql") # Header says SQL, ext is custom
    print(f"URL: {test_url6}, Meta: {meta6}") # Extension will be 'custom'
