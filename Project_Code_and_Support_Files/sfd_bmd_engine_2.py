import math
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# ==============================================================================
# 1. USER INPUT HELPER FUNCTIONS (Robust & Error-Free)
# ==============================================================================

def get_float(prompt, min_val=None, max_val=None):
    """Gets a float input with error handling and optional range bounds."""
    while True:
        try:
            val = float(input(prompt))
            if min_val is not None and val < min_val:
                print(f"   [!] Value must be >= {min_val}.")
                continue
            if max_val is not None and val > max_val:
                print(f"   [!] Value must be <= {max_val}.")
                continue
            return val
        except ValueError:
            print("   [!] Invalid input. Enter a valid numerical value.")


def get_choice(prompt, options):
    """Displays a numbered options dictionary and returns selected key."""
    print(prompt)
    for key, val in options.items():
        print(f"   {key}. {val}")
    while True:
        choice = input("Select option number: ").strip()
        if choice in options:
            return choice
        print("   [!] Invalid choice. Try again.")


def get_position(beam_length, label="position"):
    """Gets position along beam, converting 'Right end' measurements to standard x from Left (x=0)."""
    ref_opts = {"1": "From LEFT end (x = 0)", "2": "From RIGHT end (x = L)"}
    ref_choice = get_choice(f"\nReference point for {label}:", ref_opts)
    
    pos_input = get_float(f"Enter distance for {label} (0 to {beam_length} m): ", min_val=0.0, max_val=beam_length)
    
    if ref_choice == "2":
        x_pos = beam_length - pos_input
        print(f"   --> Converted: {pos_input}m from right = {x_pos:.2f}m from left.")
    else:
        x_pos = pos_input
        
    return x_pos


# ==============================================================================
# 2. INTERACTIVE SETUP FUNCTIONS
# ==============================================================================

def setup_beam():
    """Interactively configures beam length and support conditions."""
    print("\n" + "="*65)
    print("               STEP 1: BEAM GEOMETRY & SUPPORTS")
    print("="*65)
    
    length = get_float("Enter total beam length L (meters): ", min_val=0.1)
    
    beam_types = {
        "1": "Simply Supported (Pinned at Left x=0, Roller at Right x=L)",
        "2": "Cantilever (Fixed Wall at Left x=0, Free at Right x=L)",
        "3": "Cantilever (Free at Left x=0, Fixed Wall at Right x=L)",
        "4": "Custom / Overhanging Beam (Specify exact support locations)"
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
            pos = get_position(length, f"Support #{i+1}")
            supports.append({'type': stype_map[stype_ch], 'pos': pos})
            
    return length, supports


def collect_loads(beam_length):
    """Collects Point Loads, UDLs, UVLs, and Concentrated Moments interactively."""
    point_loads = []
    udls = []
    uvls = []
    point_moments = []
    
    # --- 1. Point Loads ---
    print("\n" + "="*65)
    print("                  STEP 2: POINT LOADS")
    print("="*65)
    add_pl = input("Add a Concentrated / Point Load? (y/n): ").strip().lower()
    count = 1
    while add_pl == 'y':
        print(f"\n--- Point Load #{count} ---")
        mag = get_float("Enter force magnitude (kN): ", min_val=0.01)
        pos = get_position(beam_length, f"Point Load #{count}")
        
        dir_opts = {"1": "Downward (Standard)", "2": "Upward", "3": "Angled"}
        dir_ch = get_choice("Direction:", dir_opts)
        
        if dir_ch == "1":
            vert_load = mag
            axial_load = 0.0
        elif dir_ch == "2":
            vert_load = -mag
            axial_load = 0.0
        elif dir_ch == "3":
            angle_deg = get_float("Angle relative to horizontal beam axis (deg): ", min_val=0.1, max_val=179.9)
            angle_rad = math.radians(angle_deg)
            vert_load = mag * math.sin(angle_rad)
            axial_load = mag * math.cos(angle_rad)
            print(f"   --> Transverse vertical component (Py): {vert_load:.3f} kN")
            print(f"   --> Axial horizontal component (Px): {axial_load:.3f} kN")
            
        point_loads.append({'mag': vert_load, 'pos': pos, 'orig_mag': mag, 'axial': axial_load})
        count += 1
        add_pl = input("\nAdd another Point Load? (y/n): ").strip().lower()

    # --- 2. Uniformly Distributed Loads (UDL) ---
    print("\n" + "="*65)
    print("           STEP 3: UNIFORMLY DISTRIBUTED LOADS (UDL)")
    print("="*65)
    add_udl = input("Add a Uniformly Distributed Load (UDL)? (y/n): ").strip().lower()
    count = 1
    while add_udl == 'y':
        print(f"\n--- UDL #{count} ---")
        w = get_float("Enter load intensity w (kN/m): ", min_val=0.01)
        start_x = get_position(beam_length, f"UDL #{count} START position")
        end_x = get_position(beam_length, f"UDL #{count} END position")
        
        if start_x > end_x:
            start_x, end_x = end_x, start_x
            
        udls.append({'intensity': w, 'start': start_x, 'end': end_x})
        count += 1
        add_udl = input("\nAdd another UDL? (y/n): ").strip().lower()

    # --- 3. Uniformly Varying Loads (UVL) ---
    print("\n" + "="*65)
    print("           STEP 4: UNIFORMLY VARYING LOADS (UVL / Triangular)")
    print("="*65)
    add_uvl = input("Add a Uniformly Varying Load (UVL)? (y/n): ").strip().lower()
    count = 1
    while add_uvl == 'y':
        print(f"\n--- UVL #{count} ---")
        w_start = get_float("Enter load intensity at START (kN/m): ", min_val=0.0)
        w_end = get_float("Enter load intensity at END (kN/m): ", min_val=0.0)
        start_x = get_position(beam_length, f"UVL #{count} START position")
        end_x = get_position(beam_length, f"UVL #{count} END position")
        
        if start_x > end_x:
            start_x, end_x = end_x, start_x
            w_start, w_end = w_end, w_start
            
        uvls.append({'start_w': w_start, 'end_w': w_end, 'start': start_x, 'end': end_x})
        count += 1
        add_uvl = input("\nAdd another UVL? (y/n): ").strip().lower()

    # --- 4. Concentrated Moments / Couples ---
    print("\n" + "="*65)
    print("             STEP 5: CONCENTRATED MOMENTS / COUPLES")
    print("="*65)
    add_pm = input("Add a Concentrated Moment / Couple? (y/n): ").strip().lower()
    count = 1
    while add_pm == 'y':
        print(f"\n--- Point Moment #{count} ---")
        mag = get_float("Enter moment magnitude (kNm): ", min_val=0.01)
        pos = get_position(beam_length, f"Moment #{count}")
        
        m_opts = {"1": "Clockwise (+)", "2": "Counter-Clockwise (-)"}
        m_ch = get_choice("Direction:", m_opts)
        effective_m = mag if m_ch == "1" else -mag
        
        point_moments.append({'mag': effective_m, 'pos': pos})
        count += 1
        add_pm = input("\nAdd another Point Moment? (y/n): ").strip().lower()

    return point_loads, udls, uvls, point_moments


# ==============================================================================
# 3. STATIC EQUILIBRIUM SOLVER & COMPUTATION ENGINE
# ==============================================================================

def solve_reactions(length, supports, point_loads, udls, uvls, point_moments):
    """Calculates support reactions using static equilibrium: sum(Fy)=0 and sum(M)=0."""
    total_F = sum(pl['mag'] for pl in point_loads)
    total_M_zero = sum(pl['mag'] * pl['pos'] for pl in point_loads)

    # UDL equivalent forces
    for udl in udls:
        span = udl['end'] - udl['start']
        force = udl['intensity'] * span
        centroid = udl['start'] + span / 2.0
        total_F += force
        total_M_zero += force * centroid

    # UVL equivalent forces
    for uvl in uvls:
        span = uvl['end'] - uvl['start']
        force = 0.5 * (uvl['start_w'] + uvl['end_w']) * span
        if (uvl['start_w'] + uvl['end_w']) > 0:
            rel_centroid = (span / 3.0) * ((uvl['start_w'] + 2 * uvl['end_w']) / (uvl['start_w'] + uvl['end_w']))
        else:
            rel_centroid = span / 2.0
        centroid = uvl['start'] + rel_centroid
        total_F += force
        total_M_zero += force * centroid

    # Point Moments
    for pm in point_moments:
        total_M_zero += pm['mag']

    fixed = [s for s in supports if s['type'] == 'fixed']
    pin_roller = [s for s in supports if s['type'] in ['pinned', 'roller']]

    reactions = {}
    if fixed:
        # Cantilever Beam Case
        x_s = fixed[0]['pos']
        R_y = total_F
        M_fixed = -(total_M_zero - total_F * x_s)
        reactions[f"R_{x_s:.2f}"] = R_y
        reactions[f"M_{x_s:.2f}"] = M_fixed
    elif len(pin_roller) == 2:
        # Simply Supported or Overhanging Beam Case
        pin_roller.sort(key=lambda s: s['pos'])
        x1, x2 = pin_roller[0]['pos'], pin_roller[1]['pos']
        
        # Taking moment about support 1 (x1): sum(M_x1) = 0
        M_about_x1 = total_M_zero - total_F * x1
        R2 = M_about_x1 / (x2 - x1)
        R1 = total_F - R2
        reactions[f"R_{x1:.2f}"] = R1
        reactions[f"R_{x2:.2f}"] = R2
    else:
        raise ValueError("System is not statically determinate. Enter 1 Fixed support OR 2 Pinned/Roller supports.")

    return reactions


def calculate_sfd_bmd(length, supports, point_loads, udls, uvls, point_moments, num_points=5000):
    """Evaluates spatial grid x, Shear Force V(x), and Bending Moment M(x)."""
    reactions = solve_reactions(length, supports, point_loads, udls, uvls, point_moments)
    
    x = np.linspace(0.0, length, num_points)
    V = np.zeros(num_points)
    M = np.zeros(num_points)

    # 1. Reactions
    for name, val in reactions.items():
        x_r = float(name.split("_")[1])
        mask = x >= x_r
        if name.startswith("R_"):
            V[mask] += val
            M[mask] += val * (x[mask] - x_r)
        elif name.startswith("M_"):
            M[mask] += val

    # 2. Point Loads
    for pl in point_loads:
        mask = x >= pl['pos']
        V[mask] -= pl['mag']
        M[mask] -= pl['mag'] * (x[mask] - pl['pos'])

    # 3. UDLs
    for udl in udls:
        for i, xi in enumerate(x):
            if xi > udl['start']:
                eff_end = min(xi, udl['end'])
                len_left = eff_end - udl['start']
                force = udl['intensity'] * len_left
                centroid = udl['start'] + len_left / 2.0
                V[i] -= force
                M[i] -= force * (xi - centroid)

    # 4. UVLs
    for uvl in uvls:
        span = uvl['end'] - uvl['start']
        slope = (uvl['end_w'] - uvl['start_w']) / span
        for i, xi in enumerate(x):
            if xi > uvl['start']:
                x_eff = min(xi, uvl['end']) - uvl['start']
                w0 = uvl['start_w']
                
                # Integrals for shear force and moment
                force = w0 * x_eff + 0.5 * slope * (x_eff ** 2)
                dist = xi - uvl['start']
                moment = (w0 * dist * x_eff - 0.5 * w0 * (x_eff ** 2)
                          + 0.5 * slope * dist * (x_eff ** 2) - (1.0 / 3.0) * slope * (x_eff ** 3))
                
                V[i] -= force
                M[i] -= moment

    # 5. Point Moments
    for pm in point_moments:
        mask = x >= pm['pos']
        M[mask] -= pm['mag']

    return x, V, M, reactions


def find_critical_points(x, V, M, length):
    """Finds exact coordinates for zero shear crossing points, peak moments, and points of contraflexure."""
    zero_shear_points = []
    for i in range(len(V) - 1):
        if V[i] == 0 or (V[i] * V[i+1] < 0):
            if V[i+1] != V[i]:
                x_zero = x[i] - V[i] * (x[i+1] - x[i]) / (V[i+1] - V[i])
            else:
                x_zero = x[i]
            m_at_zero = float(np.interp(x_zero, x, M))
            zero_shear_points.append((x_zero, m_at_zero))

    # Contraflexure (M = 0 points)
    contraflexure_points = []
    for i in range(len(M) - 1):
        if M[i] * M[i+1] < 0:
            x_cf = x[i] - M[i] * (x[i+1] - x[i]) / (M[i+1] - M[i])
            contraflexure_points.append(x_cf)

    max_m_idx = np.argmax(np.abs(M))
    max_m_val = M[max_m_idx]
    max_m_pos = x[max_m_idx]

    return zero_shear_points, max_m_val, max_m_pos, contraflexure_points


# ==============================================================================
# 4. VISUALIZATION ENGINE (3 ALIGNED PANELS: FBD, SFD, BMD)
# ==============================================================================

def plot_results(length, x, V, M, supports, point_loads, udls, uvls, point_moments, reactions, zero_points, max_m_val, max_m_pos, contraflexure):
    """Plots 3 aligned subplots: Free Body Diagram, SFD, and BMD."""
    fig, (ax0, ax1, ax2) = plt.subplots(3, 1, figsize=(12, 10), sharex=True)
    fig.suptitle('Mechanics Analysis Engine: Free Body Diagram, SFD & BMD', fontsize=14, fontweight='bold')

    # --------------------------------------------------------------------------
    # PANEL 0: FREE BODY DIAGRAM (FBD)
    # --------------------------------------------------------------------------
    ax0.plot([0, length], [0, 0], color='black', linewidth=6)
    ax0.set_ylim(-2.0, 2.0)
    ax0.set_ylabel('Free Body\nDiagram', fontweight='bold')
    ax0.grid(True, linestyle='--', alpha=0.4)

    # Draw Physical Supports
    for s in supports:
        pos = s['pos']
        if s['type'] in ['pinned', 'roller']:
            ax0.plot(pos, -0.15, '^', markersize=14, color='black')
        elif s['type'] == 'fixed':
            ax0.plot([pos, pos], [-0.7, 0.7], color='black', linewidth=7)

    # Draw UDL Blocks
    for udl in udls:
        s_x, e_x, w = udl['start'], udl['end'], udl['intensity']
        ax0.add_patch(patches.Rectangle((s_x, 0.05), e_x - s_x, 0.4, color='orange', alpha=0.5))
        ax0.text((s_x + e_x)/2.0, 0.55, f"UDL: {w} kN/m", ha='center', fontweight='bold', color='darkorange')

    # Draw UVL Blocks
    for uvl in uvls:
        s_x, e_x, w1, w2 = uvl['start'], uvl['end'], uvl['start_w'], uvl['end_w']
        h1 = 0.1 + (w1 / (max(w1, w2) + 1e-5)) * 0.4
        h2 = 0.1 + (w2 / (max(w1, w2) + 1e-5)) * 0.4
        poly_pts = [[s_x, 0.05], [e_x, 0.05], [e_x, h2], [s_x, h1]]
        ax0.add_patch(patches.Polygon(poly_pts, color='purple', alpha=0.4))
        ax0.text((s_x + e_x)/2.0, max(h1, h2) + 0.15, f"UVL: {w1}->{w2} kN/m", ha='center', fontweight='bold', color='purple')

    # Draw Point Loads
    for pl in point_loads:
        pos, mag = pl['pos'], pl['mag']
        if mag > 0:
            ax0.annotate(f"{mag:.2f} kN", xy=(pos, 0.05), xytext=(pos, 1.2),
                         arrowprops=dict(facecolor='blue', edgecolor='blue', shrink=0.05, width=2.5, headwidth=8),
                         ha='center', fontweight='bold', color='blue')
        else:
            ax0.annotate(f"{abs(mag):.2f} kN", xy=(pos, -0.05), xytext=(pos, -1.2),
                         arrowprops=dict(facecolor='blue', edgecolor='blue', shrink=0.05, width=2.5, headwidth=8),
                         ha='center', fontweight='bold', color='blue')

    # Draw Support Reactions
    for name, val in reactions.items():
        if name.startswith("R_"):
            pos = float(name.split("_")[1])
            if val >= 0:
                ax0.annotate(f"{name} = {val:.2f} kN", xy=(pos, -0.05), xytext=(pos, -1.5),
                             arrowprops=dict(facecolor='red', edgecolor='red', shrink=0.05, width=2.5, headwidth=8),
                             ha='center', fontweight='bold', color='darkred')
            else:
                ax0.annotate(f"{name} = {val:.2f} kN", xy=(pos, 0.05), xytext=(pos, 1.5),
                             arrowprops=dict(facecolor='red', edgecolor='red', shrink=0.05, width=2.5, headwidth=8),
                             ha='center', fontweight='bold', color='darkred')
        elif name.startswith("M_"):
            pos = float(name.split("_")[1])
            ax0.text(pos, 0.4, f"{name} = {val:.2f} kNm", color='darkred', fontweight='bold', ha='center')

    # --------------------------------------------------------------------------
    # PANEL 1: SHEAR FORCE DIAGRAM (SFD)
    # --------------------------------------------------------------------------
    ax1.plot(x, V, color='blue', linewidth=2)
    ax1.fill_between(x, 0, V, where=(V >= 0), color='blue', alpha=0.3)
    ax1.fill_between(x, 0, V, where=(V < 0), color='red', alpha=0.3)
    ax1.axhline(0, color='black', linewidth=1)
    ax1.set_ylabel('Shear Force (kN)', fontweight='bold')
    ax1.grid(True, linestyle='--', alpha=0.6)

    # Highlight V = 0 crossing points
    for x_z, m_z in zero_points:
        ax1.plot(x_z, 0, 'ro', markersize=8)
        ax1.annotate(f"V = 0 at x = {x_z:.2f}m\n(Right dist = {length - x_z:.2f}m)",
                     xy=(x_z, 0), xytext=(x_z, max(V)*0.5 if max(V) != 0 else 1.0),
                     arrowprops=dict(facecolor='black', arrowstyle='->'),
                     fontweight='bold', bbox=dict(boxstyle='round,pad=0.3', facecolor='yellow', alpha=0.7))

    # --------------------------------------------------------------------------
    # PANEL 2: BENDING MOMENT DIAGRAM (BMD)
    # --------------------------------------------------------------------------
    ax2.plot(x, M, color='green', linewidth=2)
    ax2.fill_between(x, 0, M, where=(M >= 0), color='green', alpha=0.3)
    ax2.fill_between(x, 0, M, where=(M < 0), color='orange', alpha=0.3)
    ax2.axhline(0, color='black', linewidth=1)
    ax2.set_ylabel('Moment (kNm)', fontweight='bold')
    ax2.set_xlabel('Position x (m)', fontweight='bold')
    ax2.grid(True, linestyle='--', alpha=0.6)

    # Highlight Peak Bending Moment
    ax2.plot(max_m_pos, max_m_val, 'go', markersize=9)
    ax2.annotate(f"Max M = {max_m_val:.3f} kNm\nat x = {max_m_pos:.2f}m",
                 xy=(max_m_pos, max_m_val), xytext=(max_m_pos, max_m_val*0.6 if max_m_val != 0 else 1.0),
                 arrowprops=dict(facecolor='green', arrowstyle='->', lw=2),
                 fontweight='bold', bbox=dict(boxstyle='round,pad=0.3', facecolor='lightgreen', alpha=0.8))

    # Highlight Points of Contraflexure
    for x_cf in contraflexure:
        ax2.plot(x_cf, 0, 'mo', markersize=8)
        ax2.annotate(f"Contraflexure\nx = {x_cf:.2f}m", xy=(x_cf, 0), xytext=(x_cf, -max_m_val*0.4 if max_m_val != 0 else -1.0),
                     arrowprops=dict(facecolor='purple', arrowstyle='->'),
                     fontweight='bold', bbox=dict(boxstyle='round,pad=0.3', facecolor='plum', alpha=0.8))

    plt.tight_layout()
    plt.show()


# ==============================================================================
# MAIN EXECUTION
# ==============================================================================
if __name__ == "__main__":
    # 1. Geometry and Support Setup
    beam_length, supports = setup_beam()
    
    # 2. Collect All Load Types
    point_loads, udls, uvls, point_moments = collect_loads(beam_length)
    
    # 3. Calculate SFD & BMD
    print("\nSolving equilibrium equations...")
    x, V, M, reactions = calculate_sfd_bmd(beam_length, supports, point_loads, udls, uvls, point_moments)
    
    # 4. Critical Points Analysis
    zero_points, max_m_val, max_m_pos, contraflexure = find_critical_points(x, V, M, beam_length)
    
    # 5. Output Text Summary
    print("\n" + "="*65)
    print("                    CALCULATION SUMMARY")
    print("="*65)
    print("\n--- SUPPORT REACTIONS ---")
    for r_name, r_val in reactions.items():
        print(f"   {r_name}: {r_val:.3f}")

    print("\n--- ZERO SHEAR & MAXIMUM BENDING MOMENT ---")
    for x_z, m_z in zero_points:
        dist_from_right = beam_length - x_z
        print(f"   Shear Force V = 0 at x = {x_z:.3f} m from left (or {dist_from_right:.3f} m from right end)")
        print(f"   Bending Moment at this position = {m_z:.3f} kNm")

    print(f"\n   Global Peak Bending Moment: {max_m_val:.3f} kNm at x = {max_m_pos:.3f} m")

    if contraflexure:
        print("\n--- POINTS OF CONTRAFLEXURE (M = 0) ---")
        for x_cf in contraflexure:
            print(f"   Point of Contraflexure at x = {x_cf:.3f} m")

    # 6. Display Graphs
    plot_results(beam_length, x, V, M, supports, point_loads, udls, uvls, point_moments, reactions, zero_points, max_m_val, max_m_pos, contraflexure)
