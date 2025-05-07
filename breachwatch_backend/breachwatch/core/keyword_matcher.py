import logging
import re
from typing import List, Set

logger = logging.getLogger(__name__)

def match_keywords_in_text(text: str, keywords: List[str]) -> Set[str]:
    """
    Matches a list of keywords in a given text. Case-insensitive.
    Returns a set of keywords that were found.
    Uses regex for whole word matching to reduce false positives.
    """
    if not text or not keywords:
        return set()

    found_keywords = set()
    normalized_text = text.lower() # Normalize text once

    for keyword in keywords:
        # Normalize keyword and prepare regex for whole word match
        # \b matches word boundaries
        # re.escape to handle special characters in keywords
        try:
            pattern = r"\b" + re.escape(keyword.lower()) + r"\b"
            if re.search(pattern, normalized_text):
                found_keywords.add(keyword) # Add original keyword case
        except re.error as e:
            logger.warning(f"Regex error for keyword '{keyword}': {e}. Skipping this keyword for this text.")
            continue
            
    if found_keywords:
        logger.debug(f"Keywords found: {found_keywords} in text snippet: '{text[:100]}...'")
    return found_keywords

# Example usage:
if __name__ == '__main__':
    sample_text_1 = "This is a test for Password and nik values. Also NIK-123."
    keywords_list_1 = ["password", "NIK", "secret", "ktp"]
    found1 = match_keywords_in_text(sample_text_1, keywords_list_1)
    print(f"Text 1: '{sample_text_1}'\nKeywords: {keywords_list_1}\nFound: {found1}") # Expected: {'password', 'NIK'}

    sample_text_2 = "User_database_dump.sql.gz contains user credentials."
    keywords_list_2 = ["database", "credentials", "user"]
    found2 = match_keywords_in_text(sample_text_2, keywords_list_2)
    print(f"Text 2: '{sample_text_2}'\nKeywords: {keywords_list_2}\nFound: {found2}") # Expected: {'database', 'credentials', 'user'}

    sample_text_3 = "archive_data.zip"
    keywords_list_3 = ["data", "zip"]
    found3 = match_keywords_in_text(sample_text_3, keywords_list_3)
    print(f"Text 3: '{sample_text_3}'\nKeywords: {keywords_list_3}\nFound: {found3}") # Expected: {'data', 'zip'}
    
    sample_text_4 = "Nonikname"
    keywords_list_4 = ["NIK"]
    found4 = match_keywords_in_text(sample_text_4, keywords_list_4)
    print(f"Text 4: '{sample_text_4}'\nKeywords: {keywords_list_4}\nFound: {found4}") # Expected: {} (due to \b word boundary)

    sample_text_5 = "API_KEY_VALUE"
    keywords_list_5 = ["api_key"]
    found5 = match_keywords_in_text(sample_text_5, keywords_list_5)
    print(f"Text 5: '{sample_text_5}'\nKeywords: {keywords_list_5}\nFound: {found5}") # Expected: {'api_key'}
    
    sample_text_6 = "this has my_api_key."
    keywords_list_6 = ["my_api_key"]
    found6 = match_keywords_in_text(sample_text_6, keywords_list_6)
    print(f"Text 6: '{sample_text_6}'\nKeywords: {keywords_list_6}\nFound: {found6}")

    sample_text_7 = "special+char_keyword example"
    keywords_list_7 = ["special+char_keyword", "example"]
    found7 = match_keywords_in_text(sample_text_7, keywords_list_7)
    print(f"Text 7: '{sample_text_7}'\nKeywords: {keywords_list_7}\nFound: {found7}")
    
    sample_text_8 = "data_ktp_warga.xlsx"
    keywords_list_8 = ["ktp", "data", "warga", "xlsx"]
    found8 = match_keywords_in_text(sample_text_8, keywords_list_8)
    print(f"Text 8: '{sample_text_8}'\nKeywords: {keywords_list_8}\nFound: {found8}")

