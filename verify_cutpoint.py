
import math

from physics_solver import PhysicsSolver

# --- 1. CONFIGURATION ---
FLOW_RATE_LPM = 0.8     # Current Desgin Flow Rate
TARGET_CUTPOINT = 4.0   # Current Design Target (microns)
NOZZLE_COUNT = 1

# Calculate Nozzle Diameter using the same logic as the design script
solver = PhysicsSolver()
# We want to verify if the nozzle diameter we *use* gives the correct Stk50.
# The design script *calculates* the nozzle diameter to force Stk50=0.24.
# So mathematically it should pass, but we will confirm.
NOZZLE_DIAM_MM = solver.calculate_nozzle_diameter(FLOW_RATE_LPM, TARGET_CUTPOINT) * 1000.0

# Physics Constants (STP)
AIR_VISCOSITY = 1.81e-5         # Pa*s
RHO_P = 1000                    # Particle density (kg/m^3)
STK_50_IDEAL = 0.24             # Ideal Stokes number for 50% cut (Round Jet)

# --- 2. CALCULATIONS ---
Q_m3s = (FLOW_RATE_LPM / 1000) / 60
nozzle_diam_m = NOZZLE_DIAM_MM / 1000
jet_area_m2 = NOZZLE_COUNT * math.pi * (nozzle_diam_m / 2)**2
jet_velocity = Q_m3s / jet_area_m2

def calculate_stk(d_p_microns):
    d_p_m = d_p_microns * 1e-6
    # Cunningham Slip Correction (Approximate for >1um)
    # C = 1 + (2 * lambda / d) * ... 
    # For simplification in >2um range at STP, C ~ 1.0 to 1.1. 
    # Let's use a simplified C=1.0 for this "back-of-napkin" verification 
    # or a slightly better approximation if possible.
    C = 1.0 
    
    # Stk = (Rho_p * d_p^2 * C * U) / (9 * mu * D_jet)
    numerator = RHO_P * (d_p_m**2) * C * jet_velocity
    denominator = 9 * AIR_VISCOSITY * nozzle_diam_m
    return numerator / denominator

def calculate_efficiency(stk):
    # Generalized Hill Equation for Impactor Efficiency
    # E = 1 / (1 + (Stk50/Stk)^s)
    # s is the sharpness parameter. Ideal round jets have s ~ 2 to 3.
    # We'll use s=2 for a conservative curve.
    s = 2.0
    if stk <= 0: return 0.0
    return 1.0 / (1.0 + (STK_50_IDEAL / stk)**2)

# --- 3. SIMULATION ---
print(f"--- IMPACTOR VERIFICATION ---")
print(f"Nozzle Diameter: {NOZZLE_DIAM_MM} mm")
print(f"Flow Rate:       {FLOW_RATE_LPM} LPM")
print(f"Jet Velocity:    {jet_velocity:.2f} m/s")
print(f"Target Cut-Point: {TARGET_CUTPOINT} microns (Stk50 = {STK_50_IDEAL})")
print("-" * 40)
print("Particle Size (um)   | Stokes Num | Efficiency (%) ")
print("-" * 40)

# Calculate efficiency for a range of particle sizes
test_sizes = [1.0, 2.0, 3.0, 4.0, 4.5, 5.0, 5.5, 6.0, 7.0, 8.0, 10.0]
stk_at_target = 0

for dp in test_sizes:
    stk = calculate_stk(dp)
    
    if dp == TARGET_CUTPOINT:
        stk_at_target = stk

    eff = calculate_efficiency(stk)
    
    cutoff_mark = "<-- CUT POINT" if dp == TARGET_CUTPOINT else ""
    print(f"{dp:<20} | {stk:<10.4f} | {eff*100:6.2f} %       {cutoff_mark}")

print("-" * 40)

# Verification
tolerance = 0.01
if abs(stk_at_target - STK_50_IDEAL) < tolerance:
    print(f"RESULT: PASS. Stk at {TARGET_CUTPOINT}um is {stk_at_target:.4f} (Target {STK_50_IDEAL})")
else:
    print(f"RESULT: FAIL. Stk at {TARGET_CUTPOINT}um is {stk_at_target} (Target {STK_50_IDEAL})")

