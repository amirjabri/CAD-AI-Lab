import math

def simulate_zigzag(flow_rate_lpm, W_mm, H_mm, segments):
    # Constants
    mu = 1.81e-5
    rho_p = 1000
    
    Q = (flow_rate_lpm / 1000) / 60
    A = (W_mm / 1000) * (H_mm / 1000)
    U = Q / A
    
    # Each sharp turn in a zigzag is pi/2
    theta = segments * (math.pi / 2)
    
    # d50 formula
    W_m = W_mm / 1000
    d50_m = math.sqrt((9 * mu * W_m) / (rho_p * U * theta))
    d50_um = d50_m * 1e6
    
    return d50_um

if __name__ == "__main__":
    flow_08 = 0.8
    h = 2.0
    n = 10 
    print(f"{'W (mm)':<8} | {'Turns':<8} | {'Cutpoint (um)':<12}")
    print("-" * 35)
    for w in [3.2]:
        cp = simulate_zigzag(flow_08, w, h, n)
        print(f"{w:<8} | {n:<8} | {cp:.2f} um")
