"""
Hybrid Quality Scoring Algorithm

Automatically calculates quality ratings (0-5) for flashcard reviews by combining:
- Time-based metrics (response time analysis)
- Answer similarity (lexical/structural/semantic comparison)
- Confidence indicators (behavioral patterns)

Classes:
    QualityScorer: Main quality scoring engine

Features:
    - Handles cold start problem progressively
    - Real-time performance (< 1ms)
    - Pure Python stdlib implementation
    - Supports numeric answer tolerance
"""

import math
import re
from typing import Dict, Optional, Tuple
from difflib import SequenceMatcher

from ..core.card import Card
from ..core.card import UserProgress

class QualityScorer:
    """
    Automatic quality scoring for spaced repetition reviews.
    
    Combines three signal components:
    1. Time (T): Response time relative to expected
    2. Answer (A): Similarity between user and correct answer
    3. Confidence (C): Behavioral confidence indicators
    
    Final quality: Q = round(5 × σ(w_t·T + w_a·A + w_c·C + b))
    where σ is sigmoid function
    
    Methods:
        score: Calculate quality rating 0-5
        _calculate_time_component: Compute time score T
        _calculate_answer_component: Compute answer similarity A
        _calculate_confidence_component: Compute confidence C
        _classify_scenario: Determine cold/warming/warm phase
        _get_weights: Get scenario-specific weights
        _apply_constraints: Apply quality constraints
    """

    def __init__(self):
        """Quality Scorer Initialization with default config"""
        # Time component parameters
        self.lambda_r = 1.8      # Retrieval decay rate
        self.kappa = 0.25        # Fluency sensitivity
        self.alpha = 0.75        # Retrieval weight
        self.beta = 0.15         # Fluency weight
        self.gamma = 0.10        # Consistency weight
        
        # Similarity weights
        self.w_lex = 0.4         # Lexical weight (was 0.5)
        self.w_str = 0.4         # Structural weight (was 0.3)
        self.w_sem = 0.2         # Semantic weight
        
        # Component weights (warm start)
        self.w_t = 0.35          # Time weight
        self.w_a = 0.40          # Answer weight
        self.w_c = 0.25          # Confidence weight
        self.bias = -0.5         # Sigmoid bias
        
        # Cold start weights
        self.cold_w_t = 0.25
        self.cold_w_a = 0.55
        self.cold_w_c = 0.20
        self.cold_bias = -0.3
        
        # Thresholds
        self.timeout_seconds = 60.0
        self.low_confidence_threshold = 0.4
        self.numeric_tolerance = 0.05

    
    def score(self, answer_user: str, answer_correct: str,
              response_times: Dict[str, float], card: Card, user: UserProgress,
              confidence_explicit: Optional[int] = None,
              editing_events: Optional[list] = None) -> int:
        """
        Calculate automatic quality rating for a review.
        
        Args:
            answer_user: User's submitted answer
            answer_correct: Correct answer from card
            response_times: Dict with 't_first', 't_typing', 't_total'
            card: Card object being reviewed
            user: UserProgress object for the user
            confidence_explicit: Optional explicit confidence rating 1-5
            editing_events: Optional typing dynamics data
        
        Returns:
            Quality rating 0-5
        
        Examples:
            >>> scorer = QualityScorer()
            >>> card = Card(card_id="c1", user_id="u1", front="Q", back="Paris")
            >>> user = UserProgress(user_id="u1", total_reviews=50)
            >>> quality = scorer.score("Paris", "Paris", 
            ...     {'t_first': 2.0, 't_typing': 0.5, 't_total': 2.5},
            ...     card, user)
            >>> 0 <= quality <= 5
            True
        """
        #Extracting timing data...
        t_first = response_times.get('t_first', 0.0)
        t_typing = response_times.get('t_typing', 0.0)
        t_total = response_times.get('t_total', 0.0)
        
        # Classify scenario
        scenario = self._classify_scenario(user, card)
        
        # Calculate expected time
        t_expected = self._estimate_expected_time(card, user)

        # Calculate components
        T = self._calculate_time_component(
            t_first, t_typing, t_total, t_expected, user, scenario
        )
        A = self._calculate_answer_component(answer_user, answer_correct)
        C = self._calculate_confidence_component(
            t_first, t_typing, t_total, user, confidence_explicit, editing_events
        )
        
        # Get weights for scenario
        w_t, w_a, w_c, b = self._get_weights(user, scenario)
        
        # Combine with weighted sum + sigmoid
        z = w_t * T + w_a * A + w_c * C + b
        P = self._sigmoid(z)
        
        # Convert to 0-5 scale
        Q = round(5 * P)
        
        # Apply constraints
        Q_final = self._apply_constraints(Q, C, t_total, scenario)
        
        # Update statistics (side effect)
        user.total_reviews += 1
        if Q_final >= 3:
            user.successful_reviews = getattr(user, 'successful_reviews', 0) + 1
        card.global_review_count += 1
        
        return int(Q_final)

    def _classify_scenario(self, user: UserProgress, card: Card) -> str:
        """
        Classify review scenario for weight selection.
        
        Scenarios:
        - 'cold_start': New user (0-5 reviews)
        - 'warming': User gaining data (6-20 reviews)
        - 'warm_start': Established user (21+ reviews)
        
        Args:
            user: UserProgress object
            card: Card object
        
        Returns:
            Scenario string
        """
        if user.total_reviews < 6:
            return 'cold_start'
        elif user.total_reviews < 21:
            return 'warming'
        else:
            return 'warm_start'
        
    def _get_weights(self, user: UserProgress, scenario: str) -> Tuple[float, float, float, float]:
        """
        Get component weights based on scenario.
        
        Args:
            user: UserProgress object
            scenario: Scenario classification
        
        Returns:
            Tuple of (w_t, w_a, w_c, bias)
        """
        if scenario == 'cold_start':
            return (self.cold_w_t, self.cold_w_a, self.cold_w_c, self.cold_bias)
        elif scenario == 'warming':
            # Interpolate between cold and warm
            progress = (user.total_reviews - 6) / (20 - 6)
            w_t = self.cold_w_t + progress * (self.w_t - self.cold_w_t)
            w_a = self.cold_w_a + progress * (self.w_a - self.cold_w_a)
            w_c = self.cold_w_c + progress * (self.w_c - self.cold_w_c)
            b = self.cold_bias + progress * (self.bias - self.cold_bias)
            return (w_t, w_a, w_c, b)
        else:
            return (self.w_t, self.w_a, self.w_c, self.bias)
    
    def _calculate_time_component(self, t_first: float, t_typing: float,
                                  t_total: float, t_expected: float,
                                  user: UserProgress, scenario: str) -> float:
        """
        Calculate time-based score T ∈ [0, 1].
        
        Combines:
        - Retrieval time (t_first vs t_expected)
        - Typing fluency (t_typing)
        - Overall consistency (t_total)
        
        Args:
            t_first: Time to first character (seconds)
            t_typing: Time spent typing (seconds)
            t_total: Total response time (seconds)
            t_expected: Expected response time (seconds)
            user: UserProgress object
            scenario: Review scenario
        
        Returns:
            Time score in [0, 1]
        """
        # Retrieval component: exponential decay
        T_retrieval = math.exp(-self.lambda_r * (t_first / max(t_expected, 1.0)))
        
        # Fluency component: penalty for slow typing
        mean_typing = getattr(user, 'mean_typing_speed', 3.5)
        T_fluency = math.exp(-self.kappa * max(0, t_typing - mean_typing))
        
        # Consistency component: total time vs expected
        ratio = t_total / max(t_expected, 1.0)
        T_consistency = math.exp(-abs(ratio - 1.0))
        
        # Weighted combination
        T = (self.alpha * T_retrieval + 
             self.beta * T_fluency + 
             self.gamma * T_consistency)
        
        return max(0.0, min(1.0, T))
    
    def _calculate_answer_component(self, answer_user: str, answer_correct: str) -> float:
        """
        Calculate answer similarity A ∈ [0, 1].
        
        Combines:
        - Lexical similarity (Levenshtein-based)
        - Structural similarity (LCS ratio)
        - Semantic similarity (Jaccard)
        
        Special handling for numeric answers.
        
        Args:
            answer_user: User's answer
            answer_correct: Correct answer
        
        Returns:
            Answer similarity in [0, 1]
        """
        # Normalize inputs
        user_norm = self._normalize_text(answer_user)
        correct_norm = self._normalize_text(answer_correct)
        
        # Check for numeric answers
        if self._is_numeric(user_norm) and self._is_numeric(correct_norm):
            return self._numeric_similarity(user_norm, correct_norm)
        
        # Lexical similarity (edit distance based)
        lex_sim = self._lexical_similarity(user_norm, correct_norm)
        
        # Structural similarity (LCS)
        str_sim = self._structural_similarity(user_norm, correct_norm)
        
        # Semantic similarity (Jaccard)
        sem_sim = self._semantic_similarity(user_norm, correct_norm)
        
        # Weighted combination
        A = (self.w_lex * lex_sim + 
             self.w_str * str_sim + 
             self.w_sem * sem_sim)
        
        return max(0.0, min(1.0, A))
    
    def _calculate_confidence_component(self, t_first: float, t_typing: float,
                                       t_total: float, user: UserProgress,
                                       confidence_explicit: Optional[int] = None,
                                       editing_events: Optional[list] = None) -> float:
        """
        Calculate confidence score C ∈ [0, 1].
        
        Combines:
        - Explicit confidence rating (if provided)
        - Implicit behavioral signals (editing patterns)
        - Historical performance
        
        Args:
            t_first: Time to first character
            t_typing: Time typing
            t_total: Total time
            user: UserProgress object
            confidence_explicit: Optional explicit rating 1-5
            editing_events: Optional editing data
        
        Returns:
            Confidence score in [0, 1]
        """
        # Start with neutral confidence
        C = 0.5
        
        # Explicit confidence (if provided)
        if confidence_explicit is not None:
            C_explicit = (confidence_explicit - 1) / 4.0  # Map 1-5 to 0-1
            C = 0.6 * C_explicit + 0.4 * C
        
        # Implicit signals from timing
        # Fast first response = higher confidence
        mean_first = getattr(user, 'mean_first_response', 5.2)
        if mean_first > 0:
            speed_factor = 1.0 - min(t_first / mean_first, 2.0) / 2.0
            C = 0.7 * C + 0.3 * speed_factor
        
        # Editing patterns (if provided)
        if editing_events:
            edit_penalty = len(editing_events) * 0.05
            C = max(0.0, C - edit_penalty)
        
        return max(0.0, min(1.0, C))
    
    def _apply_constraints(self, Q: int, C: float, t_total: float, 
                          scenario: str) -> int:
        """
        Apply constraints to quality score.
        
        Rules:
        - Timeout (>60s): Q = 0
        - Low confidence (<0.4): Q ≤ 3
        - Q must be in [0, 5]
        
        Args:
            Q: Initial quality score
            C: Confidence score
            t_total: Total response time
            scenario: Review scenario
        
        Returns:
            Constrained quality score
        """
        # Timeout constraint
        if t_total > self.timeout_seconds:
            return 0
        
        # Low confidence constraint
        if C < self.low_confidence_threshold and Q > 3:
            Q = 3
        
        # Clamp to valid range
        return max(0, min(5, Q))
    
    # Helper methods
    
    def _sigmoid(self, z: float) -> float:
        """Sigmoid activation function."""
        return 1.0 / (1.0 + math.exp(-z))
    
    def _normalize_text(self, text: str) -> str:
        """Normalize text for comparison."""
        # Convert to lowercase and strip whitespace
        text = text.lower().strip()
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        return text
    
    def _is_numeric(self, text: str) -> bool:
        """Check if text represents a number."""
        try:
            float(text.replace(',', ''))
            return True
        except ValueError:
            return False
    
    def _numeric_similarity(self, user: str, correct: str) -> float:
        """Calculate similarity for numeric answers."""
        try:
            user_val = float(user.replace(',', ''))
            correct_val = float(correct.replace(',', ''))
            
            if correct_val == 0:
                return 1.0 if user_val == 0 else 0.0
            
            # Check if within tolerance
            relative_diff = abs(user_val - correct_val) / abs(correct_val)
            if relative_diff <= self.numeric_tolerance:
                return 1.0
            else:
                return 0.0
        except ValueError:
            return 0.0
    
    def _lexical_similarity(self, s1: str, s2: str) -> float:
        """Calculate lexical similarity using SequenceMatcher."""
        if not s1 and not s2:
            return 1.0
        if not s1 or not s2:
            return 0.0
        
        return SequenceMatcher(None, s1, s2).ratio()
    
    def _structural_similarity(self, s1: str, s2: str) -> float:
        """Calculate structural similarity using LCS ratio."""
        if not s1 and not s2:
            return 1.0
        if not s1 or not s2:
            return 0.0
        
        # Use SequenceMatcher for LCS
        matcher = SequenceMatcher(None, s1, s2)
        matches = matcher.get_matching_blocks()
        lcs_length = sum(block.size for block in matches)
        
        max_len = max(len(s1), len(s2))
        return lcs_length / max_len if max_len > 0 else 0.0
    
    def _semantic_similarity(self, s1: str, s2: str) -> float:
        """Calculate semantic similarity using Jaccard."""
        if not s1 and not s2:
            return 1.0
        if not s1 or not s2:
            return 0.0
        
        # Split into word sets
        words1 = set(s1.split())
        words2 = set(s2.split())
        
        if not words1 and not words2:
            return 1.0
        
        # Jaccard similarity
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        
        return intersection / union if union > 0 else 0.0
    
    def _estimate_expected_time(self, card: Card, user: UserProgress) -> float:
        """
        Estimate expected response time.
        
        Uses global card statistics if available, otherwise user baseline.
        
        Args:
            card: Card object
            user: UserProgress object
        
        Returns:
            Expected time in seconds
        """
        # Try card-specific time
        if hasattr(card, 'global_mean_first_time'):
            return getattr(card, 'global_mean_first_time', 5.2)
        
        # Fall back to user mean
        if hasattr(user, 'mean_response_time'):
            return getattr(user, 'mean_response_time', 8.5)
        
        # Default baseline
        return 5.0