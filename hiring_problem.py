import random
import math

def run_hiring_simulation(num_candidates, num_trials):
    """
    Simulates the hiring problem to find the expected number of hires.

    Args:
        num_candidates (int): The number of candidates in the pool (n).
        num_trials (int): The number of times to run the full simulation.
    """
    print(f"Running {num_trials:,} trials with {num_candidates} candidates each...")
    
    total_hires = 0
    
    # --- Main Simulation Loop ---
    for _ in range(num_trials):
        # 1. Initialize candidates with monotonically increasing skill levels.
        #    Skill levels are from 1 (worst) to num_candidates (best).
        candidates = list(range(1, num_candidates + 1))
        
        # 2. Permute them randomly to simulate random arrival order.
        random.shuffle(candidates)
        
        # --- Single Trial of the Hiring Process ---
        hires_in_this_trial = 0
        best_skill_so_far = 0  # No one has been seen yet.
        
        for candidate_skill in candidates:
            if candidate_skill > best_skill_so_far:
                # This candidate is the best seen so far, so we hire them.
                hires_in_this_trial += 1
                best_skill_so_far = candidate_skill
                
        total_hires += hires_in_this_trial
        
    # --- Calculate and Display Results ---
    expected_hires = total_hires / num_trials
    
    # The theoretical expectation is the nth Harmonic Number, approximated by ln(n) + gamma
    gamma = 0.57721
    theoretical_hires = math.log(num_candidates) + gamma if num_candidates > 0 else 0
    
    print(f"\n--- Simulation Results ---")
    print(f"Average (expected) number of hires per trial: {expected_hires:.4f}")
    print(f"Theoretical expected number of hires:       {theoretical_hires:.4f}")

if __name__ == "__main__":
    # You can change these values to experiment
    CANDIDATES = 100
    TRIALS = 100000
    run_hiring_simulation(num_candidates=CANDIDATES, num_trials=TRIALS)
