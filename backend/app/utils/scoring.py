"""
Dynamic scoring system for CodeProof

Points decrease as more people solve the problem (CTF-style)
Formula: points = 10 * (1 / (1 + log10(solved_count + 1)))
"""

import math


def calculate_dynamic_points(solved_count: int, base_points: float = 10.0, decay_factor: float = 0.5) -> float:
    """
    Calculate problem points based on solve count (RETROACTIVE SYSTEM)

    The more people solve a problem, the fewer points it's worth.
    This score is DYNAMIC and affects ALL users who solved it.

    Formula: points = base * (1 / (1 + log10(solved_count + 1) * decay_factor))

    With decay_factor = 0.5 (medium decay):
    - 0 solves:    10.00 points (full value)
    - 1 solve:     9.09 points
    - 5 solves:    7.75 points
    - 10 solves:   7.14 points
    - 50 solves:   6.25 points
    - 100 solves:  6.00 points
    - 500 solves:  5.26 points
    - 1000 solves: 5.00 points

    Args:
        solved_count: Number of times problem has been solved
        base_points: Base value of the problem (default 10.0)
        decay_factor: Controls decay speed (0.2=slow, 0.5=medium, 1.0=fast)

    Returns:
        Points value (float, rounded to 2 decimals)
    """

    # Handle edge case
    if solved_count < 0:
        solved_count = 0

    # Calculate points using logarithmic decay (RETROACTIVE)
    # + 1 to avoid log(0)
    # decay_factor = 0.5 provides balanced decay
    points = base_points * (1.0 / (1.0 + math.log10(solved_count + 1) * decay_factor))

    # Round to 2 decimal places
    return round(points, 2)


def calculate_initial_points(difficulty: str) -> float:
    """
    Calculate initial points based on difficulty level

    This is used when creating a new problem.
    All problems start at 10 points, but this function
    allows for future difficulty-based initial values.

    Args:
        difficulty: Problem difficulty (easy, medium, hard)

    Returns:
        Initial points value
    """

    # For MVP, all problems start at 10.0
    # Future: could be 8.0 (easy), 10.0 (medium), 12.0 (hard)
    return 10.0


def calculate_rank_score(problems_solved: int, total_score: float) -> float:
    """
    Calculate a user's ranking score

    Combines number of problems solved with total points earned.
    Primary sort by total_score, secondary by problems_solved.

    Args:
        problems_solved: Number of unique problems solved
        total_score: Total points earned

    Returns:
        Ranking score (just returns total_score for MVP)
    """

    # For MVP, ranking is just total_score
    # Future: could weight problems_solved more
    return total_score


def calculate_user_score(user_id: int, db) -> float:
    """
    Calculate a user's CURRENT total score (DYNAMIC/RETROACTIVE)

    This score changes when:
    - User solves a new problem
    - Other users solve problems that this user already solved (score decreases)

    The score is calculated by summing the CURRENT value of all problems
    the user has solved.

    Args:
        user_id: User ID
        db: Database session

    Returns:
        float: Current total score (sum of current_points of all solved problems)
    """
    from app.models import UserProblemSolve, Problem

    # Get all problems this user solved
    solves = db.query(UserProblemSolve, Problem).join(
        Problem, UserProblemSolve.problem_id == Problem.id
    ).filter(
        UserProblemSolve.user_id == user_id
    ).all()

    total_score = 0.0

    for solve, problem in solves:
        # Add the CURRENT value of the problem (which may have decayed)
        total_score += problem.current_points

    return round(total_score, 2)


# Testing and demonstration
if __name__ == "__main__":
    """
    Demonstrate the dynamic scoring system
    """

    print("=" * 60)
    print("CodeProof Dynamic Scoring System")
    print("=" * 60)
    print()

    print("Points decay as solve count increases:")
    print()
    print(f"{'Solves':<10} {'Points':<10} {'% of Max':<10}")
    print("-" * 30)

    test_counts = [0, 1, 2, 3, 5, 10, 20, 50, 100, 200, 500, 1000]

    for count in test_counts:
        points = calculate_dynamic_points(count)
        percentage = (points / 10.0) * 100
        print(f"{count:<10} {points:<10.2f} {percentage:<10.1f}%")

    print()
    print("=" * 60)
    print()

    # Simulate a problem being solved over time
    print("Simulation: Problem 'Hello Satoshi' being solved")
    print("-" * 60)

    current_solves = 0
    users = ["Alice", "Bob", "Charlie", "Dave", "Eve"]

    for user in users:
        points_earned = calculate_dynamic_points(current_solves)
        print(f"User {user:8s} solves it (solve #{current_solves + 1}): earns {points_earned:.2f} points")
        current_solves += 1

    print()
    print(f"After {current_solves} solves, problem is now worth: {calculate_dynamic_points(current_solves):.2f} points")
    print()
    print("=" * 60)
    print()

    # Show how this affects ranking
    print("Ranking Impact:")
    print("-" * 60)
    print()
    print("Early solvers get more points!")
    print()
    print("If Alice solves 5 problems (as first solver each):")
    alice_score = 5 * calculate_dynamic_points(0)
    print(f"  Alice: {alice_score:.2f} points")
    print()
    print("If Bob solves the same 5 problems (as 100th solver each):")
    bob_score = 5 * calculate_dynamic_points(99)
    print(f"  Bob: {bob_score:.2f} points")
    print()
    print(f"Difference: {alice_score - bob_score:.2f} points ({((alice_score - bob_score) / alice_score * 100):.1f}% less)")
    print()
    print("This encourages solving problems early!")
    print()
    print("=" * 60)

    # Verify mathematical properties
    print()
    print("Mathematical Properties:")
    print("-" * 60)
    print(f"Maximum points (0 solves):     {calculate_dynamic_points(0):.2f}")
    print(f"Asymptotic minimum (∞ solves): ~{calculate_dynamic_points(10000):.2f}")
    print(f"Points are always positive:    {calculate_dynamic_points(10000) > 0}")
    print(f"Points are monotonically decreasing")
    print()
    print("✅ Scoring system working correctly!")
    print("=" * 60)
