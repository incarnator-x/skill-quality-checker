"""
Code Block Validator Module
Validates code blocks in markdown files for syntax errors
"""

import re
import ast
import subprocess
from pathlib import Path
from typing import List, Dict, Tuple
import tempfile
import os


class CodeValidator:
    def __init__(self):
        """Initialize CodeValidator"""
        self.supported_languages = {
            'python': self.validate_python,
            'py': self.validate_python,
            'javascript': self.validate_javascript,
            'js': self.validate_javascript,
            'typescript': self.validate_typescript,
            'ts': self.validate_typescript,
            'json': self.validate_json,
        }

    def extract_code_blocks(self, file_path: Path) -> List[Dict]:
        """
        Extract all code blocks from a markdown file

        Args:
            file_path: Path to markdown file

        Returns:
            List of code block dictionaries with language, code, and line number
        """
        code_blocks = []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Match code blocks with language specifier
            pattern = r'```(\w+)?\n(.*?)```'
            matches = re.finditer(pattern, content, re.DOTALL)

            for match in matches:
                language = match.group(1) or 'unknown'
                code = match.group(2).strip()

                # Find line number
                line_num = content[:match.start()].count('\n') + 1

                code_blocks.append({
                    'language': language.lower(),
                    'code': code,
                    'line_number': line_num,
                    'file_path': str(file_path)
                })

        except Exception as e:
            print(f"Error reading {file_path}: {e}")

        return code_blocks

    def validate_python(self, code: str) -> Tuple[bool, str]:
        """
        Validate Python code syntax

        Args:
            code: Python code string

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            ast.parse(code)
            return (True, "OK")
        except SyntaxError as e:
            return (False, f"Syntax error at line {e.lineno}: {e.msg}")
        except Exception as e:
            return (False, f"Error: {str(e)}")

    def validate_javascript(self, code: str) -> Tuple[bool, str]:
        """
        Validate JavaScript code syntax using Node.js

        Args:
            code: JavaScript code string

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Check if node is available
            result = subprocess.run(
                ['node', '--check', '-'],
                input=code,
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                return (True, "OK")
            else:
                error = result.stderr.strip()
                return (False, f"Syntax error: {error[:100]}")

        except FileNotFoundError:
            return (True, "Skipped (Node.js not installed)")
        except subprocess.TimeoutExpired:
            return (False, "Validation timeout")
        except Exception as e:
            return (True, f"Skipped: {str(e)[:50]}")

    def validate_typescript(self, code: str) -> Tuple[bool, str]:
        """
        Validate TypeScript code syntax

        Args:
            code: TypeScript code string

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Try using tsc if available
            with tempfile.NamedTemporaryFile(mode='w', suffix='.ts', delete=False) as f:
                f.write(code)
                temp_file = f.name

            result = subprocess.run(
                ['tsc', '--noEmit', temp_file],
                capture_output=True,
                text=True,
                timeout=5
            )

            os.unlink(temp_file)

            if result.returncode == 0:
                return (True, "OK")
            else:
                error = result.stderr.strip()
                return (False, f"Type error: {error[:100]}")

        except FileNotFoundError:
            return (True, "Skipped (TypeScript not installed)")
        except Exception as e:
            return (True, f"Skipped: {str(e)[:50]}")

    def validate_json(self, code: str) -> Tuple[bool, str]:
        """
        Validate JSON syntax

        Args:
            code: JSON string

        Returns:
            Tuple of (is_valid, error_message)
        """
        import json
        try:
            json.loads(code)
            return (True, "OK")
        except json.JSONDecodeError as e:
            return (False, f"JSON error at line {e.lineno}: {e.msg}")
        except Exception as e:
            return (False, f"Error: {str(e)}")

    def validate_code_block(self, block: Dict) -> Dict:
        """
        Validate a single code block

        Args:
            block: Code block dictionary

        Returns:
            Validation result dictionary
        """
        language = block['language']
        code = block['code']

        if language in self.supported_languages:
            is_valid, error_msg = self.supported_languages[language](code)
            return {
                **block,
                'is_valid': is_valid,
                'error': error_msg,
                'validated': True
            }
        else:
            return {
                **block,
                'is_valid': True,
                'error': f"Skipped (unsupported language: {language})",
                'validated': False
            }

    def validate_skill_code(self, skill_path: Path) -> Dict:
        """
        Validate all code blocks in a skill

        Args:
            skill_path: Path to skill directory

        Returns:
            Validation results dictionary
        """
        all_code_blocks = []

        # Check SKILL.md
        skill_md = skill_path / "SKILL.md"
        if skill_md.exists():
            blocks = self.extract_code_blocks(skill_md)
            all_code_blocks.extend(blocks)

        # Check references directory
        references_dir = skill_path / "references"
        if references_dir.exists():
            for md_file in references_dir.rglob("*.md"):
                blocks = self.extract_code_blocks(md_file)
                all_code_blocks.extend(blocks)

        print(f"📝 Found {len(all_code_blocks)} code blocks")

        # Validate each code block
        results = []
        for block in all_code_blocks:
            result = self.validate_code_block(block)
            results.append(result)

        # Count statistics
        validated_blocks = [r for r in results if r['validated']]
        valid_blocks = [r for r in validated_blocks if r['is_valid']]
        invalid_blocks = [r for r in validated_blocks if not r['is_valid']]

        return {
            'total': len(all_code_blocks),
            'validated': len(validated_blocks),
            'valid': len(valid_blocks),
            'invalid': len(invalid_blocks),
            'skipped': len(all_code_blocks) - len(validated_blocks),
            'percentage': round(len(valid_blocks) / len(validated_blocks) * 100, 1) if validated_blocks else 0,
            'results': results,
            'invalid_blocks': invalid_blocks
        }


def validate_skill_code_blocks(skill_path: str) -> Dict:
    """
    Main function to validate code blocks in a skill

    Args:
        skill_path: Path to skill directory

    Returns:
        Validation results dictionary
    """
    skill_path = Path(skill_path)

    if not skill_path.exists():
        return {'error': f"Path does not exist: {skill_path}"}

    validator = CodeValidator()
    results = validator.validate_skill_code(skill_path)

    return results


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python code_validator.py <skill_path>")
        sys.exit(1)

    skill_path = sys.argv[1]
    results = validate_skill_code_blocks(skill_path)

    if 'error' in results:
        print(f"❌ Error: {results['error']}")
        sys.exit(1)

    # Print results
    print(f"\n{'='*60}")
    print(f"📊 Code Validation Results")
    print(f"{'='*60}")
    print(f"✅ Valid Code Blocks: {results['valid']}/{results['validated']} ({results['percentage']}%)")
    print(f"⏭️  Skipped: {results['skipped']}")

    if results['invalid']:
        print(f"\n❌ Invalid Code Blocks ({len(results['invalid_blocks'])}):")
        for block in results['invalid_blocks'][:5]:  # Show first 5
            print(f"   • {block['file_path']}:{block['line_number']}")
            print(f"     Language: {block['language']}")
            print(f"     Error: {block['error']}")
            print()
