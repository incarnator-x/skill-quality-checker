"""
Report Generator Module
Generates markdown quality reports
"""

from datetime import datetime
from pathlib import Path
from typing import Dict, Optional


class ReportGenerator:
    def __init__(self):
        """Initialize ReportGenerator"""
        pass

    def generate_summary_section(self, overall_score: float, skill_name: str) -> str:
        """Generate summary section"""
        status = self.get_status_label(overall_score)
        stars = self.get_star_rating(overall_score)

        return f"""# 📊 Skill Quality Report: {skill_name}

## Summary
- **Overall Score**: {overall_score:.1f}/10 {stars}
- **Status**: {status}
- **Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M')}
"""

    def get_status_label(self, score: float) -> str:
        """Get status label based on score"""
        if score >= 9.0:
            return "⭐ Excellent"
        elif score >= 8.0:
            return "✅ Very Good"
        elif score >= 7.0:
            return "👍 Good"
        elif score >= 6.0:
            return "⚠️ Fair"
        else:
            return "❌ Needs Improvement"

    def get_star_rating(self, score: float) -> str:
        """Convert score to star rating"""
        stars = int(round(score / 2))
        return "⭐" * stars

    def generate_link_health_section(self, link_results: Dict) -> str:
        """Generate link health section"""
        if not link_results or 'error' in link_results:
            return "## Link Health\n⏭️ Skipped\n"

        total = link_results['total']
        valid = link_results['valid']
        percentage = link_results['percentage']

        status_icon = "✅" if percentage >= 95 else "⚠️" if percentage >= 80 else "❌"

        section = f"""## Link Health
{status_icon} **{valid}/{total}** links working ({percentage}%)
"""

        if link_results['broken']:
            section += f"\n❌ Broken links ({len(link_results['broken_links'])}):\n"
            for broken in link_results['broken_links'][:10]:
                section += f"  - {broken['url']} → {broken['error']}\n"
                if broken['archive_available']:
                    section += f"    ✓ Archive: {broken['archive_url']}\n"

            if len(link_results['broken_links']) > 10:
                remaining = len(link_results['broken_links']) - 10
                section += f"  ... and {remaining} more\n"

        return section

    def generate_code_quality_section(self, code_results: Dict) -> str:
        """Generate code quality section"""
        if not code_results or 'error' in code_results:
            return "## Code Quality\n⏭️ Skipped\n"

        validated = code_results['validated']
        valid = code_results['valid']
        percentage = code_results['percentage']
        total = code_results['total']

        status_icon = "✅" if percentage >= 95 else "⚠️" if percentage >= 80 else "❌"

        section = f"""## Code Quality
{status_icon} **{valid}/{validated}** code examples valid ({percentage}%)
"""

        if code_results['skipped'] > 0:
            section += f"⏭️ Skipped: {code_results['skipped']} (unsupported languages)\n"

        if code_results['invalid'] > 0:
            section += f"\n⚠️ Issues ({code_results['invalid']}):\n"
            for block in code_results['invalid_blocks'][:5]:
                rel_path = Path(block['file_path']).name
                section += f"  - {rel_path}:{block['line_number']} - {block['error']}\n"

            if code_results['invalid'] > 5:
                remaining = code_results['invalid'] - 5
                section += f"  ... and {remaining} more\n"

        return section

    def generate_content_analysis_section(self, content_results: Dict) -> str:
        """Generate content analysis section"""
        if not content_results or 'error' in content_results:
            return "## Content Analysis\n⏭️ Skipped\n"

        section = f"""## Content Analysis
- **Total Pages**: {content_results['pages']}
- **Total Words**: {content_results['words']:,}
- **Total Tokens**: {content_results['tokens']:,}
- **Code Examples**: {content_results['code_blocks']}
- **Images**: {content_results['images']}
- **Links**: {content_results['links']}
- **Reading Time**: ~{content_results['reading_time_min']} minutes
"""

        if 'avg_words_per_page' in content_results:
            section += f"""
### Density Metrics
- **Avg Words/Page**: {content_results['avg_words_per_page']}
- **Avg Tokens/Page**: {content_results['avg_tokens_per_page']}
- **Code Density**: {content_results.get('code_density', 0):.1f} examples/page
"""

        return section

    def generate_ai_assessment_section(self, ai_results: Dict) -> str:
        """Generate AI assessment section"""
        if not ai_results or 'error' in ai_results:
            error_msg = ai_results.get('error', 'Unknown error') if ai_results else 'No results'
            return f"## AI Assessment\n⏭️ Skipped ({error_msg})\n"

        overall = ai_results['overall_score']
        scores = ai_results['scores']

        section = f"""## AI Assessment
🤖 **Claude Score**: {overall:.1f}/10

### Detailed Scores
"""

        for metric in ['clarity', 'completeness', 'code_quality', 'structure', 'usefulness']:
            if metric in scores:
                score = scores[metric]
                section += f"- **{metric.replace('_', ' ').title()}**: {score}/10"

                if metric in ai_results.get('explanations', {}):
                    section += f" - {ai_results['explanations'][metric]}"

                section += "\n"

        return section

    def generate_recommendations_section(self, link_results: Dict, code_results: Dict, ai_results: Dict) -> str:
        """Generate recommendations section"""
        recommendations = []

        # Link recommendations
        if link_results and link_results.get('broken', 0) > 0:
            recommendations.append(f"Fix {len(link_results['broken_links'])} broken links")

        # Code recommendations
        if code_results and code_results.get('invalid', 0) > 0:
            recommendations.append(f"Fix {code_results['invalid']} invalid code examples")

        # AI recommendations
        if ai_results and 'recommendations' in ai_results:
            recommendations.extend(ai_results['recommendations'][:3])

        if not recommendations:
            return "## Recommendations\n✅ No major issues found!\n"

        section = "## Recommendations\n"
        for i, rec in enumerate(recommendations, 1):
            section += f"{i}. {rec}\n"

        return section

    def generate_report(self, skill_name: str, results: Dict) -> str:
        """
        Generate complete markdown report

        Args:
            skill_name: Name of the skill
            results: Dictionary containing all validation results

        Returns:
            Markdown report string
        """
        overall_score = results.get('overall_score', 0)

        report_parts = [
            self.generate_summary_section(overall_score, skill_name),
            self.generate_link_health_section(results.get('link_validation', {})),
            self.generate_code_quality_section(results.get('code_validation', {})),
            self.generate_content_analysis_section(results.get('content_analysis', {})),
            self.generate_ai_assessment_section(results.get('ai_assessment', {})),
            self.generate_recommendations_section(
                results.get('link_validation', {}),
                results.get('code_validation', {}),
                results.get('ai_assessment', {})
            )
        ]

        # Add auto-fix notice if applicable
        if results.get('auto_fix_available', False):
            report_parts.append("""
## Auto-Fix Available
Run with `--auto-fix` flag to automatically fix common issues:
```bash
python skill_quality_checker.py <skill_path> --auto-fix
```
""")

        return "\n".join(report_parts)


def generate_quality_report(skill_name: str, results: Dict, output_path: Optional[str] = None) -> str:
    """
    Main function to generate quality report

    Args:
        skill_name: Name of the skill
        results: Validation results
        output_path: Optional path to save report

    Returns:
        Generated report markdown
    """
    generator = ReportGenerator()
    report = generator.generate_report(skill_name, results)

    if output_path:
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(report)
            print(f"✅ Report saved to: {output_path}")
        except Exception as e:
            print(f"⚠️ Could not save report: {e}")

    return report


if __name__ == "__main__":
    # Test report generation
    test_results = {
        'overall_score': 8.5,
        'link_validation': {
            'total': 250,
            'valid': 245,
            'broken': 5,
            'percentage': 98.0,
            'broken_links': [
                {'url': 'https://example.com/old', 'error': '404', 'archive_available': True,
                 'archive_url': 'https://web.archive.org/example'}
            ]
        },
        'code_validation': {
            'total': 125,
            'validated': 120,
            'valid': 115,
            'invalid': 5,
            'skipped': 5,
            'percentage': 95.8,
            'invalid_blocks': []
        },
        'content_analysis': {
            'pages': 850,
            'words': 250000,
            'tokens': 2300000,
            'code_blocks': 120,
            'images': 45,
            'links': 1234,
            'reading_time_min': 1250
        },
        'ai_assessment': {
            'overall_score': 8.7,
            'scores': {
                'clarity': 9.0,
                'completeness': 8.5,
                'code_quality': 8.5,
                'usefulness': 9.0
            }
        }
    }

    report = generate_quality_report("React", test_results)
    print(report)
