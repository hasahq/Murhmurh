"""
Unit tests for QualityScorer.

Coverage targets:
- Component calculations (T, A, C): 100%
- Cold start scenarios: 100%
- Edge cases: 95%
- Integration: 90%
"""

import unittest
from sp_quiz.algorithms import QualityScorer
from sp_quiz.core.card import Card, CardState
from sp_quiz.core.user import UserProgress

class TestQualityScorerColdStart(unittest.TestCase):
    """Tests Cold Start Handling"""

    def setUp(self):
        self.scorer = QualityScorer()
    
    def test_complete_cold_start(self):
        """Test scenario A: new user + new card."""
        user = UserProgress(user_id="user_new", total_reviews=0)
        card = Card(
            card_id="card_new",
            user_id="user_new",
            front="Q",
            back="A",
            global_review_count=0
        )
        
        quality = self.scorer.score(
            answer_user="A",
            answer_correct="A",
            response_times={
                't_first': 3.0,
                't_typing': 0.5,
                't_total': 3.5
            },
            card=card,
            user=user
        )
        
        # Should produce valid quality
        self.assertIn(quality, [0, 1, 2, 3, 4, 5])
    
    def test_new_user_known_card(self):
        """Test scenario B: new user + known card."""
        user = UserProgress(user_id="user_new", total_reviews=0)
        card = Card(
            card_id="card_known",
            user_id="user_new",
            front="Q",
            back="A",
            global_review_count=100,
            global_success_rate=0.75,
            difficulty_rating=0.25
        )
        
        quality = self.scorer.score(
            answer_user="A",
            answer_correct="A",
            response_times={
                't_first': 2.5,
                't_typing': 0.5,
                't_total': 3.0
            },
            card=card,
            user=user
        )
        
        self.assertIn(quality, [0, 1, 2, 3, 4, 5])
    
    def test_warming_phase_transition(self):
        """Test weight transition during warming (6-20 reviews)."""
        user = UserProgress(user_id="user_warming", total_reviews=15)
        card = Card(
            card_id="card_001",
            user_id="user_warming",
            front="Q",
            back="A"
        )
        
        # Weights should be transitioning
        scenario = self.scorer._classify_scenario(user, card)
        w_t, w_a, w_c, b = self.scorer._get_weights(user, scenario)
        
        # Should be between cold and warm weights
        self.assertGreater(w_t, 0.25)
        self.assertLess(w_t, 0.35)

class TestQualityScorerComponents(unittest.TestCase):
    """Test individual components."""
    
    def setUp(self):
        self.scorer = QualityScorer()
        self.user = UserProgress(
            user_id="user_test",
            total_reviews=50,
            mean_response_time=7.0,
            std_response_time=4.0
        )
        self.card = Card(
            card_id="card_test",
            user_id="user_test",
            front="Q",
            back="A",
            reviews_count=10
        )
    
    def test_time_component_fast_response(self):
        """Test time score for fast response."""
        T = self.scorer._calculate_time_component(
            t_first=1.0,
            t_typing=0.3,
            t_total=1.3,
            t_expected=5.0,
            user=self.user,
            scenario='warm_start'
        )
        
        # Fast response should score high
        self.assertGreater(T, 0.7)
    
    def test_time_component_slow_response(self):
        """Test time score for slow response."""
        T = self.scorer._calculate_time_component(
            t_first=15.0,
            t_typing=2.0,
            t_total=17.0,
            t_expected=5.0,
            user=self.user,
            scenario='warm_start'
        )
        
        # Slow response should score low
        self.assertLess(T, 0.5)
    
    def test_answer_component_exact_match(self):
        """Test answer similarity for exact match."""
        A = self.scorer._calculate_answer_component("Paris", "Paris")
        
        # Exact match should be perfect
        self.assertGreater(A, 0.95)
    
    def test_answer_component_partial_match(self):
        """Test answer similarity for partial match."""
        A = self.scorer._calculate_answer_component("Paris", "Paris, France")
        
        # Partial match should be moderate-high
        self.assertGreater(A, 0.5)
        self.assertLess(A, 1.0)
    
    def test_answer_component_no_match(self):
        """Test answer similarity for no match."""
        A = self.scorer._calculate_answer_component("London", "Paris")
        
        # No match should be low
        self.assertLess(A, 0.3)
    
    def test_numeric_answer_exact(self):
        """Test numeric answer with exact match."""
        A = self.scorer._calculate_answer_component("42", "42")
        self.assertEqual(A, 1.0)
    
    def test_numeric_answer_within_tolerance(self):
        """Test numeric answer within 5% tolerance."""
        A = self.scorer._calculate_answer_component("100", "102")
        self.assertEqual(A, 1.0)
    
    def test_numeric_answer_outside_tolerance(self):
        """Test numeric answer outside tolerance."""
        A = self.scorer._calculate_answer_component("100", "150")
        self.assertEqual(A, 0.0)

class TestQualityScorerConstraints(unittest.TestCase):
    """Test constraint application."""
    
    def setUp(self):
        self.scorer = QualityScorer()
    
    def test_low_confidence_cap(self):
        """Test quality capped at 3 for low confidence."""
        Q = 5  # High initial quality
        C = 0.3  # Low confidence
        
        Q_constrained = self.scorer._apply_constraints(
            Q, C, t_total=10.0, scenario='warm_start'
        )
        
        self.assertLessEqual(Q_constrained, 3)
    
    def test_timeout_automatic_fail(self):
        """Test timeout results in quality 0."""
        Q = 5
        C = 0.8
        
        Q_constrained = self.scorer._apply_constraints(
            Q, C, t_total=70.0, scenario='warm_start'
        )
        
        self.assertEqual(Q_constrained, 0)

class TestQualityScorerIntegration(unittest.TestCase):
    """Integration tests."""
    
    def setUp(self):
        self.scorer = QualityScorer()
    
    def test_end_to_end_correct_fast(self):
        """Test correct answer with fast response."""
        user = UserProgress(
            user_id="user_001",
            total_reviews=50,
            mean_response_time=8.0,
            std_response_time=5.0
        )
        card = Card(
            card_id="card_001",
            user_id="user_001",
            front="Capital of France?",
            back="Paris"
        )
        
        quality = self.scorer.score(
            answer_user="Paris",
            answer_correct="Paris",
            response_times={
                't_first': 2.0,
                't_typing': 0.5,
                't_total': 2.5
            },
            card=card,
            user=user
        )
        
        # Should be high quality
        self.assertGreaterEqual(quality, 4)
    
    def test_end_to_end_incorrect(self):
        """Test incorrect answer."""
        user = UserProgress(
            user_id="user_001",
            total_reviews=50
        )
        card = Card(
            card_id="card_001",
            user_id="user_001",
            front="Capital of France?",
            back="Paris"
        )
        
        quality = self.scorer.score(
            answer_user="London",
            answer_correct="Paris",
            response_times={
                't_first': 5.0,
                't_typing': 1.0,
                't_total': 6.0
            },
            card=card,
            user=user
        )
        
        # Should be low quality
        self.assertLessEqual(quality, 2)
    
    def test_statistics_update(self):
        """Test user/card statistics are updated."""
        user = UserProgress(
            user_id="user_001",
            total_reviews=10,
            successful_reviews=8
        )
        card = Card(
            card_id="card_001",
            user_id="user_001",
            front="Q",
            back="A",
            global_review_count=5
        )
        
        initial_reviews = user.total_reviews
        initial_global_count = card.global_review_count
        
        self.scorer.score(
            answer_user="A",
            answer_correct="A",
            response_times={
                't_first': 3.0,
                't_typing': 0.5,
                't_total': 3.5
            },
            card=card,
            user=user
        )
        
        # Statistics should be updated
        self.assertEqual(user.total_reviews, initial_reviews + 1)
        self.assertEqual(card.global_review_count, initial_global_count + 1)


if __name__ == '__main__':
    unittest.main()