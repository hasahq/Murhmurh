"""
Mathematical Utilities for SP-Quiz Algorithm Components

This module provides mathematical functions used by the SM-2+ algorithm
and scheduler, including forgetting curve calculations, interval computations,
and data conversion utilities.

Functions:
    forgetting_curve: Calculate recall probability over time
    clamp: Constrain value to range
    ease_factor_delta: Calculate EF adjustment for quality rating
    calculate_interval: Compute next review interval
    days_to_timedelta: Convert days to timedelta
    timedelta_to_days: Convert timedelta to days
    retention_from_interval: Calculate expected retention
    stability_from_reviews: Estimate memory stability
"""

import math
from datetime import timedelta
from typing import Union

# Constants from design specification
MIN_INTERVAL_DAYS = 60 / 86400  # 1 minute in days
MAX_INTERVAL_DAYS = 365.0       # 365 days maximum


def forgetting_curve(t: float, stability: float) -> float:
    """
    Calculate recall probability using exponential forgetting curve.
    
    Based on Ebbinghaus forgetting curve: R(t) = e^(-t/S)
    where R is recall probability, t is time, and S is stability.
    
    Args:
        t: Time elapsed since learning (in same units as stability)
        stability: Memory stability (higher = slower forgetting)
    
    Returns:
        Recall probability in range [0, 1]
    
    Examples:
        >>> forgetting_curve(0, 10)  # Immediately after learning
        1.0
        >>> forgetting_curve(10, 10)  # At t = stability
        0.36787944117144233  # ≈ 1/e
    """
    if t < 0:
        return 1.0  # Negative time returns full recall
    return math.exp(-t / stability) if stability > 0 else 0.0


def clamp(value: Union[int, float], min_val: Union[int, float], 
          max_val: Union[int, float]) -> Union[int, float]:
    """
    Constrain value to specified range [min_val, max_val].
    
    Args:
        value: Value to clamp
        min_val: Minimum allowed value
        max_val: Maximum allowed value
    
    Returns:
        Value constrained to [min_val, max_val]
    
    Examples:
        >>> clamp(5, 1, 10)
        5
        >>> clamp(0, 1, 10)
        1
        >>> clamp(15, 1, 10)
        10
    """
    return max(min_val, min(value, max_val))


def ease_factor_delta(quality: int) -> float:
    """
    Calculate ease factor adjustment based on quality rating.
    
    Formula from SM-2+: Δ = 0.1 - (5-q)*(0.08 + (5-q)*0.02)
    
    This creates a curve where:
    - q=5: positive delta (EF increases)
    - q=4: near-zero delta (EF stable)
    - q≤3: negative delta (EF decreases)
    
    Args:
        quality: Quality rating 0-5
    
    Returns:
        Delta to add to current ease factor
    
    Examples:
        >>> ease_factor_delta(5)  # Perfect recall
        0.1
        >>> ease_factor_delta(4)  # Good recall
        0.0
        >>> ease_factor_delta(0)  # Complete failure
        -0.8
    """
    return 0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02)


def calculate_interval(previous_interval: float, ease_factor: float,
                      difficulty_factor: float = 1.0) -> float:
    """
    Calculate next review interval.
    
    Formula: I(n) = max(MIN_INTERVAL, min(MAX_INTERVAL, I(n-1) × EF × DF))
    
    Args:
        previous_interval: Previous interval in days
        ease_factor: Ease factor (typically 1.3-2.5)
        difficulty_factor: User-specific difficulty adjustment (0.7-1.3)
    
    Returns:
        Next interval in days, clamped to [MIN_INTERVAL, MAX_INTERVAL]
    
    Examples:
        >>> calculate_interval(1.0, 2.5, 1.0)
        2.5
        >>> calculate_interval(0.0001, 0.01, 0.01)  # Below minimum
        0.0006944444444444445  # MIN_INTERVAL
    """
    new_interval = previous_interval * ease_factor * difficulty_factor
    return clamp(new_interval, MIN_INTERVAL_DAYS, MAX_INTERVAL_DAYS)


def days_to_timedelta(days: float) -> timedelta:
    """
    Convert fractional days to timedelta object.
    
    Args:
        days: Number of days (can be fractional)
    
    Returns:
        timedelta object representing the duration
    
    Examples:
        >>> days_to_timedelta(1.0)
        datetime.timedelta(days=1)
        >>> days_to_timedelta(0.5)
        datetime.timedelta(seconds=43200)  # 12 hours
    """
    return timedelta(days=days)


def timedelta_to_days(td: timedelta) -> float:
    """
    Convert timedelta to fractional days.
    
    Args:
        td: timedelta object
    
    Returns:
        Number of days as float
    
    Examples:
        >>> timedelta_to_days(timedelta(days=1))
        1.0
        >>> timedelta_to_days(timedelta(hours=12))
        0.5
    """
    return td.total_seconds() / 86400.0


def retention_from_interval(interval_days: float, stability: float) -> float:
    """
    Calculate expected retention probability at given interval.
    
    This is an alias for forgetting_curve with interval as time parameter.
    
    Args:
        interval_days: Review interval in days
        stability: Memory stability
    
    Returns:
        Expected retention probability [0, 1]
    
    Examples:
        >>> retention_from_interval(1.0, 5.0)
        0.8187307530779818
    """
    return forgetting_curve(interval_days, stability)


def stability_from_reviews(reviews_count: int, average_quality: float) -> float:
    """
    Estimate memory stability based on review history.
    
    Stability increases with:
    - More reviews (practice effect)
    - Higher average quality (better encoding)
    
    Formula: S = (1 + reviews_count^0.5) × (1 + average_quality/5)
    
    Args:
        reviews_count: Number of times reviewed
        average_quality: Mean quality rating across reviews
    
    Returns:
        Estimated stability (positive float)
    
    Examples:
        >>> stability_from_reviews(10, 4.0)
        4.422166387140533
        >>> stability_from_reviews(0, 0.0)
        1.0
    """
    if reviews_count <= 0:
        return 1.0  # Baseline stability for new items
    
    # Practice effect: square root of review count
    practice_factor = 1.0 + math.sqrt(reviews_count)
    
    # Quality effect: normalized quality contribution
    quality_factor = 1.0 + (average_quality / 5.0)
    
    return practice_factor * quality_factor
