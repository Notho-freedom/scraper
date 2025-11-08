"""Grammar and spell checking module with LanguageTool integration"""

import logging
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from collections import Counter

# Optional imports with graceful fallback
try:
    import language_tool_python
    LANGUAGETOOL_AVAILABLE = True
except ImportError:
    LANGUAGETOOL_AVAILABLE = False
    logging.warning("LanguageTool not available. Install with: pip install language-tool-python")

try:
    from spellchecker import SpellChecker
    SPELLCHECKER_AVAILABLE = True
except ImportError:
    SPELLCHECKER_AVAILABLE = False
    logging.warning("SpellChecker not available. Install with: pip install pyspellchecker")


@dataclass
class GrammarError:
    """Represents a single grammar/spelling error"""
    error_type: str  # 'grammar', 'spelling', 'punctuation', 'style', 'typography'
    message: str
    context: str
    offset: int
    length: int
    suggestions: List[str]
    rule_id: str
    severity: str  # 'error', 'warning', 'info'
    original_text: str
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'type': self.error_type,
            'message': self.message,
            'context': self.context,
            'offset': self.offset,
            'length': self.length,
            'suggestions': self.suggestions,
            'rule_id': self.rule_id,
            'severity': self.severity,
            'original_text': self.original_text
        }


@dataclass
class GrammarCheckResult:
    """Results of grammar checking"""
    text: str
    errors: List[GrammarError]
    error_count: int
    errors_by_type: Dict[str, int]
    errors_by_severity: Dict[str, int]
    language: str
    checked: bool
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'text': self.text,
            'errors': [e.to_dict() for e in self.errors],
            'error_count': self.error_count,
            'errors_by_type': dict(self.errors_by_type),
            'errors_by_severity': dict(self.errors_by_severity),
            'language': self.language,
            'checked': self.checked
        }


class GrammarChecker:
    """Advanced grammar and spelling checker"""
    
    # Error type mapping from LanguageTool categories
    ERROR_TYPE_MAP = {
        'misspelling': 'spelling',
        'grammar': 'grammar',
        'typographical': 'typography',
        'punctuation': 'punctuation',
        'style': 'style',
        'uncategorized': 'other',
        'confused_words': 'grammar',
        'redundancy': 'style',
        'nonstandard': 'style',
        'semantics': 'grammar',
        'compounding': 'typography'
    }
    
    def __init__(self, language: str = 'fr'):
        """
        Initialize grammar checker.
        
        Args:
            language: Language code ('fr', 'en', etc.)
        """
        self.language = language
        self.tool = None
        self.spell_checker = None
        
        # Initialize LanguageTool
        if LANGUAGETOOL_AVAILABLE:
            try:
                # Map language codes
                lang_map = {'french': 'fr', 'english': 'en'}
                lang_code = lang_map.get(language.lower(), language.lower())
                
                self.tool = language_tool_python.LanguageTool(lang_code)
                logging.info(f"LanguageTool initialized for language: {lang_code}")
            except Exception as e:
                logging.warning(f"Could not initialize LanguageTool: {e}")
                self.tool = None
        
        # Initialize SpellChecker as backup
        if SPELLCHECKER_AVAILABLE and not self.tool:
            try:
                self.spell_checker = SpellChecker(language=language[:2])
                logging.info(f"SpellChecker initialized for language: {language[:2]}")
            except Exception as e:
                logging.warning(f"Could not initialize SpellChecker: {e}")
                self.spell_checker = None
    
    def check_text(self, text: str, max_errors: int = 100) -> GrammarCheckResult:
        """
        Check text for grammar, spelling, and style errors.
        
        Args:
            text: Text to check
            max_errors: Maximum number of errors to return
            
        Returns:
            GrammarCheckResult with detected errors
        """
        errors = []
        
        if not text or not text.strip():
            return GrammarCheckResult(
                text=text,
                errors=[],
                error_count=0,
                errors_by_type={},
                errors_by_severity={},
                language=self.language,
                checked=False
            )
        
        # Use LanguageTool if available
        if self.tool:
            try:
                matches = self.tool.check(text)
                
                for match in matches[:max_errors]:
                    # Determine error type
                    category = match.category.lower() if hasattr(match, 'category') else 'other'
                    error_type = self.ERROR_TYPE_MAP.get(category, 'other')
                    
                    # Determine severity
                    if hasattr(match, 'issueType'):
                        issue_type = match.issueType.lower()
                        if 'misspelling' in issue_type or 'grammar' in category:
                            severity = 'error'
                        elif 'style' in category or 'typography' in category:
                            severity = 'warning'
                        else:
                            severity = 'info'
                    else:
                        severity = 'warning'
                    
                    error = GrammarError(
                        error_type=error_type,
                        message=match.message,
                        context=match.context,
                        offset=match.offset,
                        length=match.errorLength,
                        suggestions=match.replacements[:5] if match.replacements else [],
                        rule_id=match.ruleId,
                        severity=severity,
                        original_text=text[match.offset:match.offset + match.errorLength]
                    )
                    errors.append(error)
                
            except Exception as e:
                logging.error(f"LanguageTool check failed: {e}")
        
        # Fallback to SpellChecker if no tool available
        elif self.spell_checker:
            try:
                words = text.split()
                for i, word in enumerate(words):
                    # Clean word
                    clean_word = ''.join(c for c in word if c.isalnum())
                    if not clean_word or len(clean_word) < 3:
                        continue
                    
                    # Check spelling
                    if clean_word.lower() not in self.spell_checker:
                        suggestions = list(self.spell_checker.candidates(clean_word))[:5]
                        
                        error = GrammarError(
                            error_type='spelling',
                            message=f"Possible spelling error: '{clean_word}'",
                            context=' '.join(words[max(0, i-2):min(len(words), i+3)]),
                            offset=text.find(word),
                            length=len(word),
                            suggestions=suggestions,
                            rule_id='SPELL_CHECK',
                            severity='error',
                            original_text=word
                        )
                        errors.append(error)
                        
                        if len(errors) >= max_errors:
                            break
            
            except Exception as e:
                logging.error(f"SpellChecker failed: {e}")
        
        # Compute statistics
        errors_by_type = Counter(e.error_type for e in errors)
        errors_by_severity = Counter(e.severity for e in errors)
        
        return GrammarCheckResult(
            text=text,
            errors=errors,
            error_count=len(errors),
            errors_by_type=dict(errors_by_type),
            errors_by_severity=dict(errors_by_severity),
            language=self.language,
            checked=bool(self.tool or self.spell_checker)
        )
    
    def check_sentences(self, sentences: List[str], max_errors_per_sentence: int = 20) -> List[GrammarCheckResult]:
        """
        Check multiple sentences.
        
        Args:
            sentences: List of sentences to check
            max_errors_per_sentence: Max errors per sentence
            
        Returns:
            List of GrammarCheckResult objects
        """
        results = []
        for sentence in sentences:
            result = self.check_text(sentence, max_errors=max_errors_per_sentence)
            results.append(result)
        return results
    
    def get_error_summary(self, results: List[GrammarCheckResult]) -> Dict:
        """
        Get summary of errors across multiple results.
        
        Args:
            results: List of check results
            
        Returns:
            Dictionary with error statistics
        """
        total_errors = sum(r.error_count for r in results)
        
        # Aggregate by type
        all_types = Counter()
        all_severities = Counter()
        
        for result in results:
            all_types.update(result.errors_by_type)
            all_severities.update(result.errors_by_severity)
        
        return {
            'total_errors': total_errors,
            'errors_by_type': dict(all_types),
            'errors_by_severity': dict(all_severities),
            'checked_texts': len(results),
            'texts_with_errors': sum(1 for r in results if r.error_count > 0)
        }
    
    def __del__(self):
        """Cleanup"""
        if self.tool:
            try:
                self.tool.close()
            except:
                pass


def check_grammar(text: str, language: str = 'french', max_errors: int = 100) -> Dict:
    """
    Convenience function to check grammar.
    
    Args:
        text: Text to check
        language: Language code
        max_errors: Maximum errors to return
        
    Returns:
        Dictionary with check results
    """
    checker = GrammarChecker(language=language)
    result = checker.check_text(text, max_errors=max_errors)
    return result.to_dict()
