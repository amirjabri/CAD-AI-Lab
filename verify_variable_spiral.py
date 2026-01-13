
import math

# CONFIG
Q_LPM = 0.8
H_MM = 2.0
W_START_MM = 5.0
W_END_MM = 2.0
R_START_MM = 18.0
R_END_MM = 4.0 # Center exit radius
TURNS = 2.5

# CONSTANTS
RHO_P = 1000 # kg/m3
MU = 1.81e-5 # Pa*s

def simulate_tornado():
    print(f"--- VARIABLE WIDTH SPIRAL SIMULATION ---")
    print(f"Flow: {Q_LPM} LPM")
    print(f"Channel: {W_START_MM}->{W_END_MM}mm Width, {H_MM}mm Height")
    print(f"Radius: {R_START_MM}->{R_END_MM}mm")
    print("-" * 60)
    print(f"{'Pos':<8} | {'Rad(mm)':<8} | {'Wid(mm)':<8} | {'Vel(m/s)':<10} | {'G-Force':<10} | {'d50(um)':<10}")
    print("-" * 60)
    
    steps = 10
    for i in range(steps + 1):
        t = i / steps
        # Linear Interpolation
        r = R_START_MM + t * (R_END_MM - R_START_MM)
        w = W_START_MM + t * (W_END_MM - W_START_MM)
        
        # Velocity
        area_m2 = (w/1000) * (H_MM/1000)
        q_m3s = (Q_LPM/1000)/60
        vel = q_m3s / area_m2
        
        # G-Force (Centrifugal Accel / g)
        r_m = r / 1000
        accel = vel**2 / r_m
        g_force = accel / 9.81
        
        # Local Cutpoint Estimate (Simplified)
        # d50 proportional to sqrt(width / velocity)
        # Assuming local drift dominates:
        # d50 = sqrt( (9 * MU * w_m) / (RHO_P * vel * theta_eff) )
        # Theta is tricky locally. Let's use instantaneous force metric?
        # Better: Stoke's Cutoff. d_star = sqrt( (18*MU*width) / (2*PI*vel*(rho_p)*TurnTime) )
        # Let's just output the relative "Separation Power" (Vel^2/R) to see the trend.
        
        # Re-using the d50 formula approx:
        theta_total = TURNS * 2 * math.pi
        # Effective theta "remaining" or "passed"? 
        # For a full spiral, we use total theta. 
        # Let's estimate local d50 based on the local width and velocity if it persisted for 1 turn.
        theta_local = 2 * math.pi
        width_m = w / 1000
        d50_local = math.sqrt( (9 * MU * width_m) / (RHO_P * vel * theta_local) ) * 1e6
        
        pos_str = "Inlet" if i==0 else ("Exit" if i==steps else f"{int(t*100)}%")
        print(f"{pos_str:<8} | {r:<8.1f} | {w:<8.1f} | {vel:<10.2f} | {g_force:<10.1f} | ~{d50_local:<10.2f}")

if __name__ == "__main__":
    simulate_tornado()
