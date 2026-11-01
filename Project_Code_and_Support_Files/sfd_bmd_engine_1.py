import math
import numpy as np
import matplotlib.pyplot as plt

# ==============================================================================
# 1. USER-FRIENDLY CLI INPUT HELPERS
# ==============================================================================

def get_float(prompt, min_val=None, max_val=None):
    """Prompts for a float number with error handling and range bounds."""
    while True:
        try:
            val = float(input(prompt))
            if min_val is not None and val < min_val:
                print(f"   [!] Value must be greater than or equal to {min_val}.")
                continue
            if max_val is not None and val > max_val:
                print(f"   [!] Value cannot exceed {max_val}.")
                continue
            return val
        except ValueError:
            print("   [!] Invalid input. Please enter a valid number.")


def get_choice(prompt, options):
    """Prompts user to pick an option from a numbered list."""
    print(prompt)
    for key, val in options.items():
        print(f"   {key}. {val}")
    while True:
        choice = input("Select option number: ").strip()
        if choice in options:
            return choice
        print("   [!] Invalid choice. Try again.")


def get_position(beam_length):
    """Gets position along the beam, allowing input from Left or Right end."""
    ref_options = {"1": "Measured from LEFT end (x = 0)", "2": "Measured from RIGHT end (x = L)"}
    ref_choice = get_choice("\nChoose reference point for position:", ref_options)
    
    pos_input = get_float(f"Enter distance ({'0 to ' + str(beam_length)} m): ", min_val=0.0, max_val=beam_length)
    
    # Convert position to standard x coordinate from Left (x = 0)
    if ref_choice == "2":
        x_pos = beam_length - pos_input
        print(f"   --> Converted: {pos_input}m from right = {x_pos:.2f}m from left.")
    else:
        x_pos = pos_input
        
    return x_pos


# ==============================================================================
# 2. BEAM SETUP INTERFACE
# ==============================================================================

def setup_beam():
    """Interactively configures beam length and support conditions."""
    print("\n" + "="*50)
    print("           STEP 1: BEAM GEOMETRY & SUPPORTS")
    print("="*50)
    
    length = get_float("Enter total beam length in meters (L): ", min_val=0.1)
    
    beam_types = {
        "1": "Simply Supported (Pinned at Left, Roller at Right)",
        "2": "Cantilever (Fixed at Left end)",
        "3": "Cantilever (Fixed at Right end)",
        "4": "Custom Supports (Specify exact locations)"
    }
    
    choice = get_choice("\nSelect Beam Type:", beam_types)
    supports = []
    
    if choice == "1":
        supports.append({'type': 'pinned', 'pos': 0.0})
        supports.append({'type': 'roller', 'pos': length})
    elif choice == "2":
        supports.append({'type': 'fixed', 'pos': 0.0})
    elif choice == "3":
        supports.append({'type': 'fixed', 'pos': length})
    elif choice == "4":
        num_supp = int(get_float("How many supports? ", min_val=1, max_val=5))
        for i in range(num_supp):
            print(f"\n--- Support #{i+1} ---")
            stype_opts = {"1": "Pinned", "2": "Roller", "3": "Fixed"}
            stype_ch = get_choice("Support Type:", stype_opts)
            stype_map = {"1": "pinned", "2": "roller", "3": "fixed"}
            
            pos = get_position(length)
            supports.append({'type': stype_map[stype_ch], 'pos': pos})
            
    return length, supports


# ==============================================================================
# 3. LOAD ENTRY INTERFACE
# ==============================================================================

def collect_point_loads(beam_length):
    """Interactively collects point loads (magnitude, position, direction/angle)."""
    print("\n" + "="*50)
    print("              STEP 2: POINT LOAD INPUTS")
    print("="*50)
    
    point_loads = []
    add_load = input("Do you want to add a Concentrated/Point Load? (y/n): ").strip().lower()
    
    load_count = 1
    while add_load == 'y':
        print(f"\n--- Point Load #{load_count} ---")
        mag = get_float("Enter force magnitude (kN): ", min_val=0.01)
        pos = get_position(beam_length)
        
        # Force orientation/direction
        dir_opts = {
            "1": "Downward (Standard vertical force)",
            "2": "Upward (Vertical lift force)",
            "3": "Angled / Inclined Load"
        }
        dir_choice = get_choice("Force Direction:", dir_opts)
        
        if dir_choice == "1":
            effective_vertical_load = mag  # Positive magnitude = downward in solver
        elif dir_choice == "2":
            effective_vertical_load = -mag # Negative magnitude = upward in solver
        elif dir_choice == "3":
            angle_deg = get_float("Enter angle relative to horizontal beam axis (degrees, e.g., 90 for vertical): ", min_val=0.1, max_val=179.9)
            angle_rad = math.radians(angle_deg)
            
            # Vertical component Py = P * sin(theta)
            effective_vertical_load = mag * math.sin(angle_rad)
            axial_component = mag * math.cos(angle_rad)
            
            print(f"   --> Vertical transverse load component (Py): {effective_vertical_load:.3f} kN")
            print(f"   --> Horizontal axial load component (Px): {axial_component:.3f} kN")

        point_loads.append({'mag': effective_vertical_load, 'pos': pos})
        
        load_count += 1
        add_load = input("\nAdd another Point Load? (y/n): ").strip().lower()
        
    return point_loads


# ==============================================================================
# 4. ENGINE SOLVER & PLOTTER
# ==============================================================================

def solve_reactions(length, supports, point_loads):
    """Calculates static reactions."""
    total_F = sum(pl['mag'] for pl in point_loads)
    total_M_zero = sum(pl['mag'] * pl['pos'] for pl in point_loads)

    fixed = [s for s in supports if s['type'] == 'fixed']
    pin_roller = [s for s in supports if s['type'] in ['pinned', 'roller']]

    reactions = {}
    if fixed:
        x_s = fixed[0]['pos']
        R_y = total_F
        M_fixed = -(total_M_zero - total_F * x_s)
        reactions[f"R_{x_s:.2f}"] = R_y
        reactions[f"M_{x_s:.2f}"] = M_fixed
    elif len(pin_roller) == 2:
        pin_roller.sort(key=lambda s: s['pos'])
        x1, x2 = pin_roller[0]['pos'], pin_roller[1]['pos']
        M1 = total_M_zero - total_F * x1
        R2 = M1 / (x2 - x1)
        R1 = total_F - R2
        reactions[f"R_{x1:.2f}"] = R1
        reactions[f"R_{x2:.2f}"] = R2
    else:
        raise ValueError("System needs either 1 Fixed support OR 2 Pinned/Roller supports.")

    return reactions


def calculate_sfd_bmd(length, supports, point_loads, num_points=5000):
    """Calculates SFD V(x) and BMD M(x)."""
    reactions = solve_reactions(length, supports, point_loads)
    
    x = np.linspace(0.0, length, num_points)
    V = np.zeros(num_points)
    M = np.zeros(num_points)

    # Reaction contributions
    for name, val in reactions.items():
        x_r = float(name.split("_")[1])
        mask = x >= x_r
        if name.startswith("R_"):
            V[mask] += val
            M[mask] += val * (x[mask] - x_r)
        elif name.startswith("M_"):
            M[mask] += val

    # Point Load contributions
    for pl in point_loads:
        mask = x >= pl['pos']
        V[mask] -= pl['mag']
        M[mask] -= pl['mag'] * (x[mask] - pl['pos'])

    return x, V, M, reactions


def plot_results(length, x, V, M, supports, reactions):
    """Plots SFD & BMD graphs."""
    fig, (ax0, ax1, ax2) = plt.subplots(3, 1, figsize=(10, 8), sharex=True)
    fig.suptitle('Interactive SFD & BMD Output', fontsize=14, fontweight='bold')

    # Beam Schematic
    ax0.plot([0, length], [0, 0], color='black', linewidth=4)
    ax0.set_ylim(-1.5, 1.5)
    ax0.set_ylabel('Beam', fontweight='bold')
    ax0.grid(True, linestyle='--', alpha=0.5)

    for s in supports:
        if s['type'] in ['pinned', 'roller']:
            ax0.plot(s['pos'], -0.15, '^', markersize=12, color='red')
        elif s['type'] == 'fixed':
            ax0.plot([s['pos'], s['pos']], [-0.5, 0.5], color='red', linewidth=6)

    for name, val in reactions.items():
        if name.startswith("R_"):
            pos = float(name.split("_")[1])
            ax0.annotate(f"{name} = {val:.2f} kN", xy=(pos, -0.4), ha='center', color='darkred', fontweight='bold')

    # SFD
    ax1.plot(x, V, color='blue', linewidth=2)
    ax1.fill_between(x, 0, V, where=(V >= 0), color='blue', alpha=0.3)
    ax1.fill_between(x, 0, V, where=(V < 0), color='red', alpha=0.3)
    ax1.axhline(0, color='black', linewidth=1)
    ax1.set_ylabel('Shear Force (kN)', fontweight='bold')
    ax1.grid(True, linestyle='--', alpha=0.6)

    # BMD
    ax2.plot(x, M, color='green', linewidth=2)
    ax2.fill_between(x, 0, M, where=(M >= 0), color='green', alpha=0.3)
    ax2.fill_between(x, 0, M, where=(M < 0), color='orange', alpha=0.3)
    ax2.axhline(0, color='black', linewidth=1)
    ax2.set_ylabel('Moment (kNm)', fontweight='bold')
    ax2.set_xlabel('Position x (m)', fontweight='bold')
    ax2.grid(True, linestyle='--', alpha=0.6)

    plt.tight_layout()
    plt.show()


# ==============================================================================
# MAIN PROGRAM EXECUTION
# ==============================================================================
if __name__ == "__main__":
    # 1. Setup Beam & Supports
    beam_length, supports = setup_beam()
    
    # 2. Collect Point Loads
    point_loads = collect_point_loads(beam_length)
    
    # 3. Solve & Plot
    print("\nSolving equilibrium equations...")
    x, V, M, reactions = calculate_sfd_bmd(beam_length, supports, point_loads)
    
    print("\n--- SUPPORT REACTIONS ---")
    for r_name, r_val in reactions.items():
        print(f"{r_name}: {r_val:.3f}")
        
    plot_results(beam_length, x, V, M, supports, reactions)
