import re
from typing import List, Dict, Any
from utils.logger import logger

class ChapterSplitter:
    """
    Splits book pages into chapters based on detected start page indices.
    """
    def split(self, pages: List[str], detected_chapters: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Splits pages list into chapter-wise contents.
        
        Args:
            pages: List of cleaned pages.
            detected_chapters: List of dicts representing detected chapters with start page indices.
            
        Returns:
            List of dicts representing chapter content and metadata.
        """
        chapters_content = []
        num_chapters = len(detected_chapters)

        for i, ch in enumerate(detected_chapters):
            start_idx = ch["start_page_idx"]
            # End index is start of next chapter, or end of pages list
            end_idx = detected_chapters[i + 1]["start_page_idx"] if i + 1 < num_chapters else len(pages)
            
            # Combine pages for this chapter
            chapter_pages = pages[start_idx:end_idx]
            combined_content = "\n\n".join(chapter_pages).strip()
            
            # Count words
            # Simple whitespace-based word count is standard
            words = combined_content.split()
            word_count = len(words)

            logger.info(f"Split Chapter {ch['chapter_number']}: {ch['chapter_name']} with {word_count} words")
            
            chapters_content.append({
                "chapter_number": ch["chapter_number"],
                "chapter_name": ch["chapter_name"],
                "content": combined_content,
                "word_count": word_count
            })

        return chapters_content
