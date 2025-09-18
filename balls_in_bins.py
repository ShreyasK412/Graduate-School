import random
import math

def run_balls_and_bins_simulation(num_bins, num_trials):
    """
    Simulates the balls and bins (or coupon collector's) problem.

    Args:
        num_bins (int): The number of bins to fill (b).
        num_trials (int): The number of times to run the full simulation.
    """
    print(f"Running {num_trials:,} trials with {num_bins} bins each...")
    
    total_tosses = 0
    
    # --- Main Simulation Loop ---
    for _ in range(num_trials):
        # A set is an efficient way to track which bins have at least one ball.
        filled_bins = set()
        tosses_in_this_trial = 0
        
        # --- Single Trial: Keep tossing until all bins are full ---
        while len(filled_bins) < num_bins:
            tosses_in_this_trial += 1
            # Toss a ball into a random bin (from 0 to num_bins-1)
            landed_bin = random.randint(0, num_bins - 1)
            # Add the bin to our set. If it's already there, the set doesn't change.
            filled_bins.add(landed_bin)
            
        total_tosses += tosses_in_this_trial
        
    # --- Calculate and Display Results ---
    expected_tosses = total_tosses / num_trials
    
    # The theoretical expectation is b * H_b, where H_b is the b-th Harmonic Number.
    # H_b can be approximated by ln(b) + gamma for large b.
    gamma = 0.57721
    harmonic_b = math.log(num_bins) + gamma if num_bins > 0 else 0
    theoretical_tosses = num_bins * harmonic_b
    
    print(f"\n--- Simulation Results ---")
    print(f"Average (expected) number of tosses to fill all bins: {expected_tosses:.4f}")
    print(f"Theoretical expected number of tosses:              {theoretical_tosses:.4f}")

if __name__ == "__main__":
    # You can change these values to experiment
    BINS = 10
    TRIALS = 100000
    run_balls_and_bins_simulation(num_bins=BINS, num_trials=TRIALS)
