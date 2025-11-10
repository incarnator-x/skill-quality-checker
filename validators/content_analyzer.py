"""
Content Analyzer Module
Analyzes skill content metrics (pages, tokens, examples, etc.)
"""

import re
from pathlib import Path
from typing import Dict, List
import tiktoken


class ContentAnalyzer:
    def __init__(self):
        """Initialize ContentAnalyzer"""
        try:
            # Use cl100k_base encoding (used by GPT-4 and Claude)
            self.encoding = tiktoken.get_encoding("cl100k_base")
        except Exception:
            self.encoding = None

    def count_tokens(self, text: str) -> int:
        """
        Count tokens in text

        Args:
            text: Text to count tokens for

        Returns:
            Number of tokens
        """
        if self.encoding:
            return len(self.encoding.encode(text))
        else:
            # Fallback: rough estimate (1 token ≈ 4 characters)
            return len(text) // 4

    def analyze_file(self, file_path: Path) -> Dict:
        """
        Analyze a single markdown file

        Args:
            file_path: Path to markdown file

        Returns:
            Analysis dictionary
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Count basic metrics
            lines = content.split('\n')
            words = len(content.split())
            chars = len(content)
            tokens = self.count_tokens(content)

            # Count code blocks
            code_blocks = len(re.findall(r'```.*?```', content, re.DOTALL))

            # Count images
            images = len(re.findall(r'!\[.*?\]\(.*?\)', content))

            # Count links
            links = len(re.findall(r'\[.*?\]\(.*?\)', content))

            # Count headings
            headings = len(re.findall(r'^#{1,6}\s', content, re.MULTILINE))

            # Count lists
            lists = len(re.findall(r'^\s*[-*+]\s', content, re.MULTILINE))
            numbered_lists = len(re.findall(r'^\s*\d+\.\s', content, re.MULTILINE))

            # Count tables
            tables = len(re.findall(r'\|.*\|', content))

            # Estimate reading time (average 200 words per minute)
            reading_time_min = max(1, words // 200)

            return {
                'file_path': str(file_path),
                'lines': len(lines),
                'words': words,
                'chars': chars,
                'tokens': tokens,
                'code_blocks': code_blocks,
                'images': images,
                'links': links,
                'headings': headings,
                'lists': lists + numbered_lists,
                'tables': tables,
                'reading_time_min': reading_time_min
            }

        except Exception as e:
            print(f"Error analyzing {file_path}: {e}")
            return None

    def analyze_skill(self, skill_path: Path) -> Dict:
        """
        Analyze all content in a skill

        Args:
            skill_path: Path to skill directory

        Returns:
            Analysis results dictionary
        """
        total_stats = {
            'pages': 0,
            'lines': 0,
            'words': 0,
            'chars': 0,
            'tokens': 0,
            'code_blocks': 0,
            'images': 0,
            'links': 0,
            'headings': 0,
            'lists': 0,
            'tables': 0,
            'reading_time_min': 0,
            'file_analyses': []
        }

        # Analyze SKILL.md
        skill_md = skill_path / "SKILL.md"
        if skill_md.exists():
            analysis = self.analyze_file(skill_md)
            if analysis:
                total_stats['pages'] += 1
                for key in ['lines', 'words', 'chars', 'tokens', 'code_blocks',
                           'images', 'links', 'headings', 'lists', 'tables', 'reading_time_min']:
                    total_stats[key] += analysis[key]
                total_stats['file_analyses'].append(analysis)

        # Analyze references directory
        references_dir = skill_path / "references"
        if references_dir.exists():
            for md_file in sorted(references_dir.rglob("*.md")):
                analysis = self.analyze_file(md_file)
                if analysis:
                    total_stats['pages'] += 1
                    for key in ['lines', 'words', 'chars', 'tokens', 'code_blocks',
                               'images', 'links', 'headings', 'lists', 'tables', 'reading_time_min']:
                        total_stats[key] += analysis[key]
                    total_stats['file_analyses'].append(analysis)

        # Calculate derived metrics
        if total_stats['pages'] > 0:
            total_stats['avg_words_per_page'] = round(total_stats['words'] / total_stats['pages'])
            total_stats['avg_tokens_per_page'] = round(total_stats['tokens'] / total_stats['pages'])

        # Calculate content density (code-to-text ratio)
        if total_stats['words'] > 0:
            total_stats['code_density'] = round(total_stats['code_blocks'] / total_stats['pages'], 2)

        return total_stats


def analyze_skill_content(skill_path: str) -> Dict:
    """
    Main function to analyze skill content

    Args:
        skill_path: Path to skill directory

    Returns:
        Analysis results dictionary
    """
    skill_path = Path(skill_path)

    if not skill_path.exists():
        return {'error': f"Path does not exist: {skill_path}"}

    analyzer = ContentAnalyzer()
    results = analyzer.analyze_skill(skill_path)

    return results


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python content_analyzer.py <skill_path>")
        sys.exit(1)

    skill_path = sys.argv[1]
    results = analyze_skill_content(skill_path)

    if 'error' in results:
        print(f"❌ Error: {results['error']}")
        sys.exit(1)

    # Print results
    print(f"\n{'='*60}")
    print(f"📊 Content Analysis Results")
    print(f"{'='*60}")
    print(f"📄 Total Pages: {results['pages']}")
    print(f"📝 Total Words: {results['words']:,}")
    print(f"🔢 Total Tokens: {results['tokens']:,}")
    print(f"💻 Code Examples: {results['code_blocks']}")
    print(f"🖼️  Images: {results['images']}")
    print(f"🔗 Links: {results['links']}")
    print(f"📑 Headings: {results['headings']}")
    print(f"📋 Lists: {results['lists']}")
    print(f"📊 Tables: {results['tables']}")
    print(f"⏱️  Estimated Reading Time: {results['reading_time_min']} minutes")

    if 'avg_words_per_page' in results:
        print(f"\n📈 Averages:")
        print(f"   Words per page: {results['avg_words_per_page']}")
        print(f"   Tokens per page: {results['avg_tokens_per_page']}")
        print(f"   Code density: {results['code_density']} blocks/page")
