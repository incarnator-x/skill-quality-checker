"""
Claude API Integration Module
Uses Claude API to provide AI-based quality scoring
"""

import os
from pathlib import Path
from typing import Dict, Optional
try:
    from anthropic import Anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False


class ClaudeQualityScorer:
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Claude Quality Scorer

        Args:
            api_key: Anthropic API key (defaults to ANTHROPIC_API_KEY env var)
        """
        if not ANTHROPIC_AVAILABLE:
            raise ImportError("anthropic package not installed. Run: pip install anthropic")

        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment or provided")

        self.client = Anthropic(api_key=self.api_key)
        self.model = "claude-sonnet-4-20250514"

    def read_skill_content(self, skill_path: Path, max_tokens: int = 100000) -> str:
        """
        Read skill content with token limit

        Args:
            skill_path: Path to skill directory
            max_tokens: Maximum tokens to read (approx)

        Returns:
            Concatenated skill content
        """
        content_parts = []
        current_length = 0
        max_chars = max_tokens * 4  # Rough estimate

        # Read SKILL.md first
        skill_md = skill_path / "SKILL.md"
        if skill_md.exists():
            try:
                with open(skill_md, 'r', encoding='utf-8') as f:
                    skill_content = f.read()
                    content_parts.append(f"# SKILL.md\n\n{skill_content}")
                    current_length += len(skill_content)
            except Exception as e:
                print(f"Error reading SKILL.md: {e}")

        # Read some reference files
        references_dir = skill_path / "references"
        if references_dir.exists() and current_length < max_chars:
            for md_file in sorted(references_dir.rglob("*.md"))[:10]:  # Limit to 10 files
                if current_length >= max_chars:
                    break

                try:
                    with open(md_file, 'r', encoding='utf-8') as f:
                        file_content = f.read()
                        if current_length + len(file_content) > max_chars:
                            # Truncate
                            remaining = max_chars - current_length
                            file_content = file_content[:remaining] + "\n\n[TRUNCATED]"

                        content_parts.append(f"# {md_file.name}\n\n{file_content}")
                        current_length += len(file_content)

                except Exception as e:
                    print(f"Error reading {md_file}: {e}")

        return "\n\n---\n\n".join(content_parts)

    def score_skill(self, skill_path: Path) -> Dict:
        """
        Score a skill using Claude API

        Args:
            skill_path: Path to skill directory

        Returns:
            Scoring results dictionary
        """
        print("🤖 Reading skill content...")
        content = self.read_skill_content(skill_path)

        if not content:
            return {
                'error': 'No content found to score',
                'overall_score': 0,
                'scores': {}
            }

        print(f"   Analyzing ~{len(content)//4:,} tokens...")

        # Create scoring prompt
        prompt = f"""You are an expert technical documentation reviewer. Please analyze this Claude AI skill documentation and provide detailed quality scores.

<skill_documentation>
{content}
</skill_documentation>

Rate the following aspects on a scale of 1-10:

1. **Clarity** (1-10): How clear, well-written, and easy to understand is the documentation?
2. **Completeness** (1-10): How comprehensive is the coverage? Are there missing sections?
3. **Code Quality** (1-10): Are code examples well-written, practical, and properly formatted?
4. **Structure** (1-10): Is the documentation well-organized with good navigation?
5. **Usefulness** (1-10): How practical and valuable is this skill for real-world use?

Provide your response in this exact format:

CLARITY: [score]
[1-2 sentence explanation]

COMPLETENESS: [score]
[1-2 sentence explanation]

CODE_QUALITY: [score]
[1-2 sentence explanation]

STRUCTURE: [score]
[1-2 sentence explanation]

USEFULNESS: [score]
[1-2 sentence explanation]

OVERALL: [average score]
[2-3 sentence summary of strengths and weaknesses]

RECOMMENDATIONS:
1. [Specific actionable recommendation]
2. [Specific actionable recommendation]
3. [Specific actionable recommendation]"""

        try:
            # Call Claude API
            message = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )

            response_text = message.content[0].text

            # Parse response
            scores = self.parse_scores(response_text)

            return scores

        except Exception as e:
            return {
                'error': f"API error: {str(e)}",
                'overall_score': 0,
                'scores': {}
            }

    def parse_scores(self, response: str) -> Dict:
        """
        Parse Claude's scoring response

        Args:
            response: Claude's response text

        Returns:
            Parsed scores dictionary
        """
        import re

        scores = {}
        explanations = {}
        recommendations = []

        # Extract scores
        score_pattern = r'(CLARITY|COMPLETENESS|CODE_QUALITY|STRUCTURE|USEFULNESS|OVERALL):\s*(\d+(?:\.\d+)?)'
        matches = re.finditer(score_pattern, response)

        for match in matches:
            metric = match.group(1).lower()
            score = float(match.group(2))
            scores[metric] = score

        # Extract explanations
        explanation_pattern = r'(CLARITY|COMPLETENESS|CODE_QUALITY|STRUCTURE|USEFULNESS|OVERALL):\s*\d+(?:\.\d+)?\s*\n(.+?)(?=\n\n|\n[A-Z_]+:|\nRECOMMENDATIONS:|$)'
        exp_matches = re.finditer(explanation_pattern, response, re.DOTALL)

        for match in exp_matches:
            metric = match.group(1).lower()
            explanation = match.group(2).strip()
            explanations[metric] = explanation

        # Extract recommendations
        rec_pattern = r'RECOMMENDATIONS:\s*\n(.+?)(?=\n\n[A-Z_]+:|$)'
        rec_match = re.search(rec_pattern, response, re.DOTALL)

        if rec_match:
            rec_text = rec_match.group(1)
            rec_items = re.findall(r'\d+\.\s*(.+?)(?=\n\d+\.|\n*$)', rec_text, re.DOTALL)
            recommendations = [r.strip() for r in rec_items]

        return {
            'overall_score': scores.get('overall', 0),
            'scores': scores,
            'explanations': explanations,
            'recommendations': recommendations,
            'raw_response': response
        }


def get_ai_quality_score(skill_path: str, api_key: Optional[str] = None) -> Dict:
    """
    Main function to get AI quality score for a skill

    Args:
        skill_path: Path to skill directory
        api_key: Optional API key

    Returns:
        Scoring results dictionary
    """
    skill_path = Path(skill_path)

    if not skill_path.exists():
        return {'error': f"Path does not exist: {skill_path}"}

    if not ANTHROPIC_AVAILABLE:
        return {
            'error': 'anthropic package not installed',
            'message': 'Run: pip install anthropic',
            'overall_score': 0,
            'scores': {}
        }

    try:
        scorer = ClaudeQualityScorer(api_key)
        results = scorer.score_skill(skill_path)
        return results

    except ValueError as e:
        return {
            'error': str(e),
            'message': 'Set ANTHROPIC_API_KEY environment variable',
            'overall_score': 0,
            'scores': {}
        }
    except Exception as e:
        return {
            'error': f"Unexpected error: {str(e)}",
            'overall_score': 0,
            'scores': {}
        }


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python claude_api.py <skill_path>")
        sys.exit(1)

    skill_path = sys.argv[1]
    results = get_ai_quality_score(skill_path)

    if 'error' in results:
        print(f"❌ Error: {results['error']}")
        if 'message' in results:
            print(f"   {results['message']}")
        sys.exit(1)

    # Print results
    print(f"\n{'='*60}")
    print(f"🤖 AI Quality Score")
    print(f"{'='*60}")
    print(f"Overall Score: {results['overall_score']:.1f}/10")
    print()

    for metric, score in results['scores'].items():
        if metric != 'overall':
            print(f"{metric.upper()}: {score}/10")
            if metric in results['explanations']:
                print(f"  {results['explanations'][metric]}")
            print()

    if results['recommendations']:
        print("📋 Recommendations:")
        for i, rec in enumerate(results['recommendations'], 1):
            print(f"{i}. {rec}")
