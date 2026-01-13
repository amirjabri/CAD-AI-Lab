
import math

# --- CONFIGURATION ---
FLOW_RATE_LPM = 4.0
CHANNEL_WIDTH_MM = 4.0
CHANNEL_HEIGHT_MM = 10.0
TURNS = 2.5

# Constants (STP Air)
AIR_VISCOSITY = 1.81e-5  # Pa*s
RHO_P = 1000             # kg/m^3 (Particle Density)

# --- CALCULATIONS ---
def simulate_spiral():
    # 1. Flow Properties
    Q_m3s = (FLOW_RATE_LPM / 1000) / 60
    area_m2 = (CHANNEL_WIDTH_MM / 1000) * (CHANNEL_HEIGHT_MM / 1000)
    velocity_U = Q_m3s / area_m2  # m/s
    
    theta_rad = TURNS * 2 * math.pi
    width_m = CHANNEL_WIDTH_MM / 1000

    print(f"--- SPIRAL IMPACTOR SIMULATION ---")
    print(f"Flow Rate:      {FLOW_RATE_LPM} LPM")
    print(f"Channel:        {CHANNEL_WIDTH_MM}mm W x {CHANNEL_HEIGHT_MM}mm H")
    print(f"Turns:          {TURNS} ({math.degrees(theta_rad):.1f} deg)")
    print(f"Flow Velocity:  {velocity_U:.2f} m/s")
    print("-" * 40)
    
    # 2. Cut-Point Calculation (d50)
    # d50 = sqrt( (9 * mu * W) / (rho_p * U * theta) )
    numerator = 9 * AIR_VISCOSITY * width_m
    denominator = RHO_P * velocity_U * theta_rad
    d50_m = math.sqrt(numerator / denominator)
    d50_um = d50_m * 1e6

    print(f"Predicted d50 (Cut-Point): {d50_um:.2f} microns")
    print("-" * 40)
    
    # 3. Efficiency Curve
    print(f"{'Particle (um)':<15} | {'Drift / Width Eff (%)':<20}")
    print("-" * 40)
    
    sizes = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 8.0, 10.0]
    for d_um in sizes:
        d_m = d_um * 1e-6
        tau = (RHO_P * d_m**2) / (18 * AIR_VISCOSITY)
        
        # Drift Distance S = tau * U * theta
        drift_S = tau * velocity_U * theta_rad
        
        # Efficiency = S / W (Assuming uniform inlet distribution)
        eff = min(1.0, drift_S / width_m)
        
        marker = "<-- d50" if abs(eff - 0.5) < 0.1 else ""
        if eff == 1.0: marker = "** 100% **"
        
        print(f"{d_um:<15} | {eff*100:6.2f} %              {marker}")

if __name__ == "__main__":
    simulate_spiral()
