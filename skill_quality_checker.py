#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Skill Quality Checker
Analyzes Claude AI skills and provides quality scores with auto-fix capabilities

Usage:
    python skill_quality_checker.py <skill_path>
    python skill_quality_checker.py <skill_path> --auto-fix
    python skill_quality_checker.py <skill_path> --report output/report.md
    python skill_quality_checker.py <skill_path> --skip-ai
"""

import argparse
import sys
import os
from pathlib import Path
import time

# Fix Windows console encoding for Unicode (emojis)
if sys.platform == 'win32':
    import codecs
    if sys.stdout.encoding != 'utf-8':
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'ignore')
    if sys.stderr.encoding != 'utf-8':
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'ignore')

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from validators.link_validator import validate_skill_links
from validators.code_validator import validate_skill_code_blocks
from validators.content_analyzer import analyze_skill_content
from utils.claude_api import get_ai_quality_score
from utils.report_generator import generate_quality_report


class SkillQualityChecker:
    def __init__(self, skill_path: str, skip_ai: bool = False):
        """
        Initialize Skill Quality Checker

        Args:
            skill_path: Path to skill directory
            skip_ai: Skip AI scoring (useful for testing without API key)
        """
        self.skill_path = Path(skill_path)
        self.skip_ai = skip_ai
        self.results = {}

        if not self.skill_path.exists():
            raise ValueError(f"Skill path does not exist: {skill_path}")

        # Get skill name from path
        self.skill_name = self.skill_path.name

    def run_all_checks(self) -> dict:
        """
        Run all quality checks

        Returns:
            Complete results dictionary
        """
        print(f"\n{'='*70}")
        print(f"🔍 Skill Quality Checker")
        print(f"{'='*70}")
        print(f"📁 Skill: {self.skill_name}")
        print(f"📂 Path: {self.skill_path}")
        print(f"{'='*70}\n")

        start_time = time.time()

        # 1. Link Validation
        print("🔗 [1/4] Validating links...")
        try:
            link_results = validate_skill_links(str(self.skill_path))
            self.results['link_validation'] = link_results
            print(f"   ✓ Completed in {time.time() - start_time:.1f}s")
        except Exception as e:
            print(f"   ✗ Error: {e}")
            self.results['link_validation'] = {'error': str(e)}

        # 2. Code Validation
        print("\n💻 [2/4] Validating code blocks...")
        code_start = time.time()
        try:
            code_results = validate_skill_code_blocks(str(self.skill_path))
            self.results['code_validation'] = code_results
            print(f"   ✓ Completed in {time.time() - code_start:.1f}s")
        except Exception as e:
            print(f"   ✗ Error: {e}")
            self.results['code_validation'] = {'error': str(e)}

        # 3. Content Analysis
        print("\n📊 [3/4] Analyzing content...")
        content_start = time.time()
        try:
            content_results = analyze_skill_content(str(self.skill_path))
            self.results['content_analysis'] = content_results
            print(f"   ✓ Completed in {time.time() - content_start:.1f}s")
        except Exception as e:
            print(f"   ✗ Error: {e}")
            self.results['content_analysis'] = {'error': str(e)}

        # 4. AI Quality Score
        if not self.skip_ai:
            print("\n🤖 [4/4] Getting AI quality score...")
            ai_start = time.time()
            try:
                ai_results = get_ai_quality_score(str(self.skill_path))
                self.results['ai_assessment'] = ai_results
                print(f"   ✓ Completed in {time.time() - ai_start:.1f}s")
            except Exception as e:
                print(f"   ✗ Error: {e}")
                self.results['ai_assessment'] = {'error': str(e)}
        else:
            print("\n🤖 [4/4] AI quality score skipped")
            self.results['ai_assessment'] = {'error': 'Skipped by user'}

        # Calculate overall score
        self.results['overall_score'] = self.calculate_overall_score()

        total_time = time.time() - start_time
        print(f"\n{'='*70}")
        print(f"✅ All checks completed in {total_time:.1f}s")
        print(f"{'='*70}\n")

        return self.results

    def calculate_overall_score(self) -> float:
        """
        Calculate overall quality score from all checks

        Returns:
            Overall score (0-10)
        """
        scores = []
        weights = []

        # Link health (weight: 2)
        link_results = self.results.get('link_validation', {})
        if link_results and 'percentage' in link_results:
            link_score = link_results['percentage'] / 10  # Convert 0-100 to 0-10
            scores.append(link_score)
            weights.append(2)

        # Code quality (weight: 2)
        code_results = self.results.get('code_validation', {})
        if code_results and 'percentage' in code_results:
            code_score = code_results['percentage'] / 10
            scores.append(code_score)
            weights.append(2)

        # Content completeness (weight: 1)
        content_results = self.results.get('content_analysis', {})
        if content_results and 'pages' in content_results:
            # Simple heuristic: score based on content volume
            pages = content_results['pages']
            code_blocks = content_results['code_blocks']

            content_score = min(10, (pages / 100) * 5 + (code_blocks / 50) * 5)
            scores.append(content_score)
            weights.append(1)

        # AI assessment (weight: 5) - most important
        ai_results = self.results.get('ai_assessment', {})
        if ai_results and 'overall_score' in ai_results and ai_results['overall_score'] > 0:
            scores.append(ai_results['overall_score'])
            weights.append(5)

        # Calculate weighted average
        if scores:
            weighted_sum = sum(s * w for s, w in zip(scores, weights))
            total_weight = sum(weights)
            return round(weighted_sum / total_weight, 1)

        return 0.0

    def print_summary(self):
        """Print summary of results to console"""
        print("\n" + "="*70)
        print("📊 QUALITY SUMMARY")
        print("="*70)

        # Overall score
        overall = self.results.get('overall_score', 0)
        stars = "⭐" * int(round(overall / 2))
        print(f"\n🎯 Overall Score: {overall:.1f}/10 {stars}")

        # Link health
        link_results = self.results.get('link_validation', {})
        if link_results and 'total' in link_results:
            valid = link_results['valid']
            total = link_results['total']
            pct = link_results['percentage']
            icon = "✅" if pct >= 95 else "⚠️" if pct >= 80 else "❌"
            print(f"\n{icon} Link Health: {valid}/{total} working ({pct}%)")

        # Code quality
        code_results = self.results.get('code_validation', {})
        if code_results and 'validated' in code_results:
            valid = code_results['valid']
            validated = code_results['validated']
            pct = code_results['percentage']
            icon = "✅" if pct >= 95 else "⚠️" if pct >= 80 else "❌"
            print(f"{icon} Code Quality: {valid}/{validated} valid ({pct}%)")

        # Content metrics
        content_results = self.results.get('content_analysis', {})
        if content_results and 'pages' in content_results:
            pages = content_results['pages']
            tokens = content_results['tokens']
            code_blocks = content_results['code_blocks']
            print(f"\n📄 Content: {pages} pages, {tokens:,} tokens, {code_blocks} examples")

        # AI score
        ai_results = self.results.get('ai_assessment', {})
        if ai_results and 'overall_score' in ai_results and ai_results['overall_score'] > 0:
            ai_score = ai_results['overall_score']
            print(f"🤖 AI Score: {ai_score:.1f}/10")

        print("\n" + "="*70)

    def auto_fix(self):
        """
        Automatically fix common issues

        Returns:
            Number of fixes applied
        """
        print("\n🔧 Auto-Fix Mode")
        print("="*70)

        fixes_applied = 0

        # Fix broken links with archive.org
        link_results = self.results.get('link_validation', {})
        if link_results and 'broken_links' in link_results:
            broken_with_archive = [
                b for b in link_results['broken_links']
                if b['archive_available']
            ]

            if broken_with_archive:
                print(f"\n📎 Fixing {len(broken_with_archive)} broken links with archive.org...")

                for broken in broken_with_archive:
                    original_url = broken['url']
                    archive_url = broken['archive_url']

                    for file_path, line_num in broken['locations']:
                        try:
                            # Read file
                            with open(file_path, 'r', encoding='utf-8') as f:
                                content = f.read()

                            # Replace URL
                            new_content = content.replace(original_url, archive_url)

                            # Write back
                            with open(file_path, 'w', encoding='utf-8') as f:
                                f.write(new_content)

                            print(f"   ✓ Fixed: {Path(file_path).name}:{line_num}")
                            fixes_applied += 1

                        except Exception as e:
                            print(f"   ✗ Error fixing {file_path}: {e}")

        # Fix code block formatting
        code_results = self.results.get('code_validation', {})
        if code_results and 'results' in code_results:
            # Find code blocks without language tags
            blocks_without_lang = [
                r for r in code_results['results']
                if r['language'] == 'unknown'
            ]

            if blocks_without_lang:
                print(f"\n💻 Found {len(blocks_without_lang)} code blocks without language tags")
                print("   (Manual review recommended)")

        print(f"\n✅ Applied {fixes_applied} fixes")
        print("="*70)

        return fixes_applied


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Analyze Claude AI skill quality and provide scores',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic check
  python skill_quality_checker.py output/react/

  # With auto-fix
  python skill_quality_checker.py output/react/ --auto-fix

  # Generate report
  python skill_quality_checker.py output/react/ --report quality_report.md

  # Skip AI scoring (for testing)
  python skill_quality_checker.py output/react/ --skip-ai
        """
    )

    parser.add_argument('skill_path', help='Path to skill directory')
    parser.add_argument('--auto-fix', action='store_true',
                       help='Automatically fix common issues')
    parser.add_argument('--report', type=str, metavar='PATH',
                       help='Save detailed report to markdown file')
    parser.add_argument('--skip-ai', action='store_true',
                       help='Skip AI quality scoring')

    args = parser.parse_args()

    try:
        # Initialize checker
        checker = SkillQualityChecker(args.skill_path, skip_ai=args.skip_ai)

        # Run all checks
        results = checker.run_all_checks()

        # Print summary
        checker.print_summary()

        # Auto-fix if requested
        if args.auto_fix:
            fixes = checker.auto_fix()

            # Re-run checks after fixes
            if fixes > 0:
                print("\n🔄 Re-running checks after fixes...\n")
                results = checker.run_all_checks()
                checker.print_summary()

        # Generate report if requested
        if args.report:
            print(f"\n📝 Generating report...")
            report = generate_quality_report(checker.skill_name, results, args.report)
            print(f"✅ Report saved to: {args.report}")

        # Exit code based on overall score
        overall_score = results.get('overall_score', 0)
        if overall_score >= 8.0:
            sys.exit(0)  # Success
        elif overall_score >= 6.0:
            sys.exit(1)  # Warning
        else:
            sys.exit(2)  # Error

    except KeyboardInterrupt:
        print("\n\n⚠️ Interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
