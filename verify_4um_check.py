import math

# --- 1. CONFIGURATION ---
FLOW_RATE_LPM = 4.0     
TARGET_CUTPOINT = 4.0   
(NOZZLE_DIAM_MM) = (3.263) # From design output

# Physics Constants (STP)
AIR_VISCOSITY = 1.81e-5         # Pa*s
RHO_P = 1000                    # Particle density (kg/m^3)
STK_50_IDEAL = 0.24             # Ideal Stokes number 

# --- 2. CALCULATIONS ---
Q_m3s = (FLOW_RATE_LPM / 1000) / 60
nozzle_diam_m = NOZZLE_DIAM_MM / 1000
NOZZLE_COUNT = 1
jet_area_m2 = NOZZLE_COUNT * math.pi * (nozzle_diam_m / 2)**2
jet_velocity = Q_m3s / jet_area_m2

def calculate_stk(d_p_microns):
    d_p_m = d_p_microns * 1e-6
    C = 1.0 
    numerator = RHO_P * (d_p_m**2) * C * jet_velocity
    denominator = 9 * AIR_VISCOSITY * nozzle_diam_m
    return numerator / denominator

stk = calculate_stk(TARGET_CUTPOINT)
print(f"Calculated Stokes for {TARGET_CUTPOINT}um at {FLOW_RATE_LPM}LPM with {NOZZLE_DIAM_MM}mm nozzle:")
print(f"Stk = {stk:.4f}")
if abs(stk - STK_50_IDEAL) < 0.01:
    print("MATCH: This confirms the Cut Point.")
else:
    print("MISMATCH.")
