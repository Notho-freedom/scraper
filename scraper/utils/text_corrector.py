"""Automatic text correction module"""

import logging
import re
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from .grammar_checker import GrammarChecker, GrammarError, GrammarCheckResult


@dataclass
class Correction:
    """Represents a single correction made"""
    original: str
    corrected: str
    error_type: str
    position: int
    length: int
    rule_id: str
    confidence: float  # 0.0 to 1.0
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'original': self.original,
            'corrected': self.corrected,
            'type': self.error_type,
            'position': self.position,
            'length': self.length,
            'rule_id': self.rule_id,
            'confidence': self.confidence
        }


@dataclass
class CorrectionResult:
    """Results of text correction"""
    original_text: str
    corrected_text: str
    corrections: List[Correction]
    correction_count: int
    corrections_by_type: Dict[str, int]
    quality_score: float  # 0-100
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'original_text': self.original_text,
            'corrected_text': self.corrected_text,
            'corrections': [c.to_dict() for c in self.corrections],
            'correction_count': self.correction_count,
            'corrections_by_type': self.corrections_by_type,
            'quality_score': self.quality_score
        }


class TextCorrector:
    """Automatic text correction engine"""
    
    # Confidence thresholds for auto-correction
    AUTO_CORRECT_THRESHOLD = 0.7  # Only auto-correct if confidence >= 70%
    
    def __init__(self, language: str = 'french', auto_correct: bool = True):
        """
        Initialize text corrector.
        
        Args:
            language: Language code
            auto_correct: Enable automatic corrections
        """
        self.language = language
        self.auto_correct = auto_correct
        self.checker = GrammarChecker(language=language)
    
    def correct_text(self, text: str, aggressive: bool = False) -> CorrectionResult:
        """
        Correct text automatically.
        
        Args:
            text: Text to correct
            aggressive: If True, correct even low-confidence issues
            
        Returns:
            CorrectionResult with original and corrected text
        """
        if not text or not text.strip():
            return CorrectionResult(
                original_text=text,
                corrected_text=text,
                corrections=[],
                correction_count=0,
                corrections_by_type={},
                quality_score=100.0
            )
        
        # Check for errors
        check_result = self.checker.check_text(text)
        
        if not check_result.errors:
            return CorrectionResult(
                original_text=text,
                corrected_text=text,
                corrections=[],
                correction_count=0,
                corrections_by_type={},
                quality_score=100.0
            )
        
        # Apply corrections
        corrected_text = text
        corrections = []
        offset_adjustment = 0  # Track position changes
        
        # Sort errors by position (reverse order to maintain positions)
        sorted_errors = sorted(check_result.errors, key=lambda e: e.offset, reverse=True)
        
        for error in sorted_errors:
            if not error.suggestions:
                continue
            
            # Calculate confidence
            confidence = self._calculate_confidence(error)
            
            # Skip low-confidence corrections unless aggressive mode
            threshold = 0.5 if aggressive else self.AUTO_CORRECT_THRESHOLD
            if confidence < threshold:
                continue
            
            # Get best suggestion
            suggestion = error.suggestions[0]
            
            # Calculate actual position with adjustment
            actual_offset = error.offset
            
            # Apply correction
            before = corrected_text[:actual_offset]
            after = corrected_text[actual_offset + error.length:]
            corrected_text = before + suggestion + after
            
            # Record correction
            correction = Correction(
                original=error.original_text,
                corrected=suggestion,
                error_type=error.error_type,
                position=error.offset,
                length=error.length,
                rule_id=error.rule_id,
                confidence=confidence
            )
            corrections.append(correction)
        
        # Reverse corrections list to show in original order
        corrections.reverse()
        
        # Calculate statistics
        corrections_by_type = {}
        for corr in corrections:
            corrections_by_type[corr.error_type] = corrections_by_type.get(corr.error_type, 0) + 1
        
        # Calculate quality score
        quality_score = self._calculate_quality_score(text, check_result, corrections)
        
        return CorrectionResult(
            original_text=text,
            corrected_text=corrected_text,
            corrections=corrections,
            correction_count=len(corrections),
            corrections_by_type=corrections_by_type,
            quality_score=quality_score
        )
    
    def correct_sentences(self, sentences: List[str], aggressive: bool = False) -> List[CorrectionResult]:
        """
        Correct multiple sentences.
        
        Args:
            sentences: List of sentences
            aggressive: Use aggressive correction
            
        Returns:
            List of CorrectionResult objects
        """
        results = []
        for sentence in sentences:
            result = self.correct_text(sentence, aggressive=aggressive)
            results.append(result)
        return results
    
    def correct_paragraphs(self, paragraphs: List[str], aggressive: bool = False) -> List[CorrectionResult]:
        """
        Correct multiple paragraphs.
        
        Args:
            paragraphs: List of paragraphs
            aggressive: Use aggressive correction
            
        Returns:
            List of CorrectionResult objects
        """
        return self.correct_sentences(paragraphs, aggressive=aggressive)
    
    def _calculate_confidence(self, error: GrammarError) -> float:
        """
        Calculate confidence score for a correction.
        
        Args:
            error: Grammar error
            
        Returns:
            Confidence score (0.0 to 1.0)
        """
        confidence = 0.5  # Base confidence
        
        # Increase confidence for certain error types
        if error.error_type == 'spelling':
            confidence += 0.3
        elif error.error_type == 'grammar':
            confidence += 0.2
        elif error.error_type == 'punctuation':
            confidence += 0.25
        
        # Increase confidence for high severity
        if error.severity == 'error':
            confidence += 0.2
        
        # Decrease if multiple suggestions (ambiguous)
        if len(error.suggestions) > 3:
            confidence -= 0.15
        
        # Increase if short suggestion (likely simple fix)
        if error.suggestions and len(error.suggestions[0]) <= 3:
            confidence += 0.1
        
        return min(1.0, max(0.0, confidence))
    
    def _calculate_quality_score(self, text: str, check_result: GrammarCheckResult, 
                                 corrections: List[Correction]) -> float:
        """
        Calculate text quality score after corrections.
        
        Args:
            text: Original text
            check_result: Grammar check result
            corrections: Applied corrections
            
        Returns:
            Quality score (0-100)
        """
        if not text:
            return 100.0
        
        # Start with 100
        score = 100.0
        
        # Deduct for remaining errors
        remaining_errors = check_result.error_count - len(corrections)
        
        # Severe penalty for errors
        error_penalty = remaining_errors * 2.0
        
        # Additional penalty by error type
        for error in check_result.errors:
            if error.severity == 'error':
                error_penalty += 1.5
            elif error.severity == 'warning':
                error_penalty += 0.5
        
        # Calculate word count for normalization
        word_count = len(text.split())
        if word_count > 0:
            # Normalize by word count (penalty per 100 words)
            normalized_penalty = (error_penalty / word_count) * 100
            score -= min(normalized_penalty, 50)  # Cap at 50 points
        else:
            score -= min(error_penalty, 50)
        
        # Bonus for making corrections
        if corrections:
            correction_bonus = min(len(corrections) * 0.5, 10)
            score += correction_bonus
        
        return max(0.0, min(100.0, score))
    
    def get_correction_summary(self, results: List[CorrectionResult]) -> Dict:
        """
        Get summary of corrections across multiple results.
        
        Args:
            results: List of correction results
            
        Returns:
            Dictionary with correction statistics
        """
        total_corrections = sum(r.correction_count for r in results)
        
        # Aggregate by type
        all_types = {}
        for result in results:
            for etype, count in result.corrections_by_type.items():
                all_types[etype] = all_types.get(etype, 0) + count
        
        # Average quality score
        avg_quality = sum(r.quality_score for r in results) / len(results) if results else 0
        
        return {
            'total_corrections': total_corrections,
            'corrections_by_type': all_types,
            'average_quality_score': round(avg_quality, 2),
            'texts_corrected': len(results),
            'texts_with_corrections': sum(1 for r in results if r.correction_count > 0)
        }


def correct_text(text: str, language: str = 'french', aggressive: bool = False) -> Dict:
    """
    Convenience function to correct text.
    
    Args:
        text: Text to correct
        language: Language code
        aggressive: Use aggressive correction
        
    Returns:
        Dictionary with correction results
    """
    corrector = TextCorrector(language=language, auto_correct=True)
    result = corrector.correct_text(text, aggressive=aggressive)
    return result.to_dict()
