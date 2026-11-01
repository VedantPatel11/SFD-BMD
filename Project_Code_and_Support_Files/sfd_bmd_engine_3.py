import os
import csv
import math
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# ==============================================================================
# 1. USER MANUAL & DOCUMENTATION
# ==============================================================================

def display_manual():
    """Prints a detailed in-terminal user guide and CSV specification."""
    manual_text = """
================================================================================
                    BEAM ANALYSIS ENGINE: USER MANUAL
================================================================================

1. OVERVIEW
   This tool analyzes statically determinate beams and computes:
   - Support reactions (Fy and fixed-end moments).
   - Shear Force Diagram (SFD) and Bending Moment Diagram (BMD).
   - Zero-shear crossing points, global peak moments, and contraflexure points.
   - High-resolution Free Body Diagram (FBD) visualizer.

2. SUPPORTED BOUNDARY CONDITIONS (Statically Determinate)
   - Simply Supported / Overhanging: Exactly 2 supports (pinned or roller).
   - Cantilever: Exactly 1 fixed support (at x = 0 or x = L).

3. SIGN CONVENTIONS
   - Downward Forces: Positive (+) input; Upward Forces: Negative (-) input.
   - Clockwise Moments: Positive (+); Counter-Clockwise Moments: Negative (-).
   - Bending Moment Diagram: Sagging is positive (+), Hogging is negative (-).

4. CSV FILE SPECIFICATION
   Problems can be stored in a single '.csv' file divided into section blocks.
   Headers or empty lines within blocks are permitted.

   Example CSV Layout:
   ----------------------------------------------------------------------
   [BEAM]
   length
   10.0

   [SUPPORTS]
   type,pos
   pinned,0.0
   roller,10.0

   [POINT_LOADS]
   mag,pos,angle
   25.0,4.0,90

   [UDLS]
   intensity,start,end
   12.0,0.0,5.0

   [UVLS]
   start_w,end_w,start,end
   0.0,20.0,5.0,10.0

   [MOMENTS]
   mag,pos
   -30.0,7.0
   ----------------------------------------------------------------------
   * Note: 'angle' in POINT_LOADS is in degrees relative to beam horizontal (default: 90).

5. EXPORT FEATURES
   - Save figures directly as .png, .pdf, or .svg with custom resolutions (dpi).
   - Save any interactive session to a CSV file to reuse or batch process later.
================================================================================
"""
    print(manual_text)


# ==============================================================================
# 2. INPUT HELPERS & INTERACTIVE SETUP
# ==============================================================================

def get_float(prompt, min_val=None, max_val=None):
    """Gets a float input with range validation."""
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
    """Displays a numbered options dictionary and returns the selected key."""
    print(prompt)
    for key, val in options.items():
        print(f"   {key}. {val}")
    while True:
        choice = input("Select option number: ").strip()
        if choice in options:
            return choice
        print("   [!] Invalid choice. Try again.")


def get_position(beam_length, label="position"):
    """Reads beam position, converting right-hand reference to distance from left."""
    ref_opts = {"1": "From LEFT end (x = 0)", "2": "From RIGHT end (x = L)"}
    ref_choice = get_choice(f"\nReference point for {label}:", ref_opts)
    pos_input = get_float(f"Enter distance for {label} (0 to {beam_length} m): ", min_val=0.0, max_val=beam_length)
    if ref_choice == "2":
        x_pos = beam_length - pos_input
        print(f"   --> Converted: {pos_input}m from right = {x_pos:.2f}m from left.")
    else:
        x_pos = pos_input
    return x_pos


def setup_beam_interactive():
    """Interactively gathers beam length and boundary supports."""
    print("\n" + "="*65)
    print("               STEP 1: BEAM GEOMETRY & SUPPORTS")
    print("="*65)
    length = get_float("Enter total beam length L (meters): ", min_val=0.1)
    
    beam_types = {
        "1": "Simply Supported (Pinned at Left x=0, Roller at Right x=L)",
        "2": "Cantilever (Fixed Wall at Left x=0, Free at Right x=L)",
        "3": "Cantilever (Free at Left x=0, Fixed Wall at Right x=L)",
        "4": "Custom Support Locations (Statically Determinate)"
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
        num_supp = int(get_float("Number of supports (1 for Cantilever, 2 for Overhang/Simple): ", min_val=1, max_val=2))
        for i in range(num_supp):
            print(f"\n--- Support #{i+1} ---")
            stype_opts = {"1": "Pinned", "2": "Roller", "3": "Fixed"}
            stype_ch = get_choice("Support Type:", stype_opts)
            stype_map = {"1": "pinned", "2": "roller", "3": "fixed"}
            pos = get_position(length, f"Support #{i+1}")
            supports.append({'type': stype_map[stype_ch], 'pos': pos})
            
    return length, supports


def collect_loads_interactive(beam_length):
    """Interactively collects all external load distributions."""
    point_loads, udls, uvls, point_moments = [], [], [], []

    # Point Loads
    print("\n" + "="*65)
    print("                  STEP 2: POINT LOADS")
    print("="*65)
    while input("Add a Concentrated / Point Load? (y/n): ").strip().lower() == 'y':
        mag = get_float("Enter force magnitude (kN): ", min_val=0.01)
        pos = get_position(beam_length, "Point Load")
        dir_opts = {"1": "Downward (Standard)", "2": "Upward", "3": "Angled"}
        dir_ch = get_choice("Direction:", dir_opts)
        
        angle_deg = 90.0
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
            
        point_loads.append({'mag': vert_load, 'pos': pos, 'orig_mag': mag, 'axial': axial_load, 'angle': angle_deg})

    # UDLs
    print("\n" + "="*65)
    print("           STEP 3: UNIFORMLY DISTRIBUTED LOADS (UDL)")
    print("="*65)
    while input("Add a Uniformly Distributed Load (UDL)? (y/n): ").strip().lower() == 'y':
        w = get_float("Enter load intensity w (kN/m): ", min_val=0.01)
        start_x = get_position(beam_length, "UDL START position")
        end_x = get_position(beam_length, "UDL END position")
        if start_x > end_x:
            start_x, end_x = end_x, start_x
        udls.append({'intensity': w, 'start': start_x, 'end': end_x})

    # UVLs
    print("\n" + "="*65)
    print("           STEP 4: UNIFORMLY VARYING LOADS (UVL)")
    print("="*65)
    while input("Add a Uniformly Varying Load (UVL)? (y/n): ").strip().lower() == 'y':
        w_start = get_float("Enter load intensity at START (kN/m): ", min_val=0.0)
        w_end = get_float("Enter load intensity at END (kN/m): ", min_val=0.0)
        start_x = get_position(beam_length, "UVL START position")
        end_x = get_position(beam_length, "UVL END position")
        if start_x > end_x:
            start_x, end_x = end_x, start_x
            w_start, w_end = w_end, w_start
        uvls.append({'start_w': w_start, 'end_w': w_end, 'start': start_x, 'end': end_x})

    # Moments
    print("\n" + "="*65)
    print("             STEP 5: CONCENTRATED MOMENTS")
    print("="*65)
    while input("Add a Concentrated Moment / Couple? (y/n): ").strip().lower() == 'y':
        mag = get_float("Enter moment magnitude (kNm): ", min_val=0.01)
        pos = get_position(beam_length, "Moment")
        m_opts = {"1": "Clockwise (+)", "2": "Counter-Clockwise (-)"}
        m_ch = get_choice("Direction:", m_opts)
        effective_m = mag if m_ch == "1" else -mag
        point_moments.append({'mag': effective_m, 'pos': pos})

    return point_loads, udls, uvls, point_moments


# ==============================================================================
# 3. CSV IMPORT & EXPORT ENGINE
# ==============================================================================

def load_from_csv(filepath):
    """Loads a beam problem definition from a sectioned CSV file."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")

    length = None
    supports = []
    point_loads = []
    udls = []
    uvls = []
    point_moments = []

    current_section = None

    with open(filepath, mode='r', encoding='utf-8') as f:
        reader = csv.reader(f)
        for row in reader:
            if not row or not any(field.strip() for field in row):
                continue
            first_cell = row[0].strip()
            
            # Detect section header
            if first_cell.startswith("[") and first_cell.endswith("]"):
                current_section = first_cell.upper()
                continue
            elif first_cell.startswith("#"):
                continue

            # Process row by active section
            if current_section == "[BEAM]":
                try:
                    length = float(first_cell)
                except ValueError:
                    continue  # Skip text header row
            elif current_section == "[SUPPORTS]":
                if first_cell.lower() in ['type', 'support_type']:
                    continue
                stype = first_cell.lower()
                pos = float(row[1].strip())
                supports.append({'type': stype, 'pos': pos})
            elif current_section == "[POINT_LOADS]":
                if first_cell.lower() in ['mag', 'magnitude']:
                    continue
                mag = float(first_cell)
                pos = float(row[1].strip())
                angle_deg = float(row[2].strip()) if len(row) > 2 and row[2].strip() else 90.0
                angle_rad = math.radians(angle_deg)
                vert_load = mag * math.sin(angle_rad)
                axial_load = mag * math.cos(angle_rad)
                point_loads.append({'mag': vert_load, 'pos': pos, 'orig_mag': mag, 'axial': axial_load, 'angle': angle_deg})
            elif current_section == "[UDLS]":
                if first_cell.lower() in ['intensity', 'w']:
                    continue
                w = float(first_cell)
                s_x = float(row[1].strip())
                e_x = float(row[2].strip())
                if s_x > e_x:
                    s_x, e_x = e_x, s_x
                udls.append({'intensity': w, 'start': s_x, 'end': e_x})
            elif current_section == "[UVLS]":
                if first_cell.lower() in ['start_w', 'w_start']:
                    continue
                w1 = float(first_cell)
                w2 = float(row[1].strip())
                s_x = float(row[2].strip())
                e_x = float(row[3].strip())
                if s_x > e_x:
                    s_x, e_x = e_x, s_x
                    w1, w2 = w2, w1
                uvls.append({'start_w': w1, 'end_w': w2, 'start': s_x, 'end': e_x})
            elif current_section == "[MOMENTS]":
                if first_cell.lower() in ['mag', 'magnitude']:
                    continue
                mag = float(first_cell)
                pos = float(row[1].strip())
                point_moments.append({'mag': mag, 'pos': pos})

    if length is None or length <= 0:
        raise ValueError("Invalid or missing beam length in CSV [BEAM] section.")
    if not supports:
        raise ValueError("No supports defined in CSV [SUPPORTS] section.")

    return length, supports, point_loads, udls, uvls, point_moments


def save_to_csv(filepath, length, supports, point_loads, udls, uvls, point_moments):
    """Exports the current beam problem configuration into a sectioned CSV file."""
    with open(filepath, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        
        # Beam Length
        writer.writerow(["[BEAM]"])
        writer.writerow(["length"])
        writer.writerow([length])
        writer.writerow([])

        # Supports
        writer.writerow(["[SUPPORTS]"])
        writer.writerow(["type", "pos"])
        for s in supports:
            writer.writerow([s['type'], s['pos']])
        writer.writerow([])

        # Point Loads
        writer.writerow(["[POINT_LOADS]"])
        writer.writerow(["mag", "pos", "angle"])
        for pl in point_loads:
            writer.writerow([pl.get('orig_mag', pl['mag']), pl['pos'], pl.get('angle', 90.0)])
        writer.writerow([])

        # UDLs
        writer.writerow(["[UDLS]"])
        writer.writerow(["intensity", "start", "end"])
        for u in udls:
            writer.writerow([u['intensity'], u['start'], u['end']])
        writer.writerow([])

        # UVLs
        writer.writerow(["[UVLS]"])
        writer.writerow(["start_w", "end_w", "start", "end"])
        for uv in uvls:
            writer.writerow([uv['start_w'], uv['end_w'], uv['start'], uv['end']])
        writer.writerow([])

        # Moments
        writer.writerow(["[MOMENTS]"])
        writer.writerow(["mag", "pos"])
        for pm in point_moments:
            writer.writerow([pm['mag'], pm['pos']])


# ==============================================================================
# 4. STATIC EQUILIBRIUM SOLVER
# ==============================================================================

def solve_reactions(length, supports, point_loads, udls, uvls, point_moments):
    """Solves reactions using static equilibrium."""
    total_F = sum(pl['mag'] for pl in point_loads)
    total_M_zero = sum(pl['mag'] * pl['pos'] for pl in point_loads)

    for udl in udls:
        span = udl['end'] - udl['start']
        force = udl['intensity'] * span
        centroid = udl['start'] + span / 2.0
        total_F += force
        total_M_zero += force * centroid

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

    for pm in point_moments:
        total_M_zero += pm['mag']

    fixed = [s for s in supports if s['type'] == 'fixed']
    pin_roller = [s for s in supports if s['type'] in ['pinned', 'roller']]

    reactions = {}
    if len(fixed) == 1 and len(pin_roller) == 0:
        x_s = fixed[0]['pos']
        R_y = total_F
        M_fixed = -(total_M_zero - total_F * x_s)
        reactions[f"R_{x_s:.2f}"] = R_y
        reactions[f"M_{x_s:.2f}"] = M_fixed
    elif len(pin_roller) == 2 and len(fixed) == 0:
        pin_roller.sort(key=lambda s: s['pos'])
        x1, x2 = pin_roller[0]['pos'], pin_roller[1]['pos']
        if abs(x2 - x1) < 1e-5:
            raise ValueError("Supports cannot be placed at the exact same location.")
        M_about_x1 = total_M_zero - total_F * x1
        R2 = M_about_x1 / (x2 - x1)
        R1 = total_F - R2
        reactions[f"R_{x1:.2f}"] = R1
        reactions[f"R_{x2:.2f}"] = R2
    else:
        raise ValueError(
            "System configuration is unsupported or statically indeterminate.\n"
            "Ensure the beam has either exactly 1 fixed support or exactly 2 pinned/roller supports."
        )

    return reactions


def calculate_sfd_bmd(length, supports, point_loads, udls, uvls, point_moments, num_points=5000):
    """Computes shear force and bending moment arrays."""
    reactions = solve_reactions(length, supports, point_loads, udls, uvls, point_moments)
    x = np.linspace(0.0, length, num_points)
    V = np.zeros(num_points)
    M = np.zeros(num_points)

    # Reactions
    for name, val in reactions.items():
        x_r = float(name.split("_")[1])
        mask = x >= x_r
        if name.startswith("R_"):
            V[mask] += val
            M[mask] += val * (x[mask] - x_r)
        elif name.startswith("M_"):
            M[mask] += val

    # Point Loads
    for pl in point_loads:
        mask = x >= pl['pos']
        V[mask] -= pl['mag']
        M[mask] -= pl['mag'] * (x[mask] - pl['pos'])

    # UDLs
    for udl in udls:
        for i, xi in enumerate(x):
            if xi > udl['start']:
                eff_end = min(xi, udl['end'])
                len_left = eff_end - udl['start']
                force = udl['intensity'] * len_left
                centroid = udl['start'] + len_left / 2.0
                V[i] -= force
                M[i] -= force * (xi - centroid)

    # UVLs
    for uvl in uvls:
        span = uvl['end'] - uvl['start']
        slope = (uvl['end_w'] - uvl['start_w']) / span
        for i, xi in enumerate(x):
            if xi > uvl['start']:
                x_eff = min(xi, uvl['end']) - uvl['start']
                w0 = uvl['start_w']
                force = w0 * x_eff + 0.5 * slope * (x_eff ** 2)
                dist = xi - uvl['start']
                moment = (w0 * dist * x_eff - 0.5 * w0 * (x_eff ** 2)
                          + 0.5 * slope * dist * (x_eff ** 2) - (1.0 / 3.0) * slope * (x_eff ** 3))
                V[i] -= force
                M[i] -= moment

    # Moments
    for pm in point_moments:
        mask = x >= pm['pos']
        M[mask] -= pm['mag']

    return x, V, M, reactions


def find_critical_points(x, V, M, length):
    """Finds zero shear points, maximum moment, and points of contraflexure."""
    zero_shear_points = []
    for i in range(len(V) - 1):
        if V[i] == 0 or (V[i] * V[i+1] < 0):
            if V[i+1] != V[i]:
                x_zero = x[i] - V[i] * (x[i+1] - x[i]) / (V[i+1] - V[i])
            else:
                x_zero = x[i]
            m_at_zero = float(np.interp(x_zero, x, M))
            zero_shear_points.append((x_zero, m_at_zero))

    contraflexure_points = []
    for i in range(len(M) - 1):
        if M[i] * M[i+1] < 0:
            x_cf = x[i] - M[i] * (x[i+1] - x[i]) / (M[i+1] - M[i])
            contraflexure_points.append(x_cf)

    max_m_idx = np.argmax(np.abs(M))
    return zero_shear_points, M[max_m_idx], x[max_m_idx], contraflexure_points


# ==============================================================================
# 5. VISUALIZATION ENGINE
# ==============================================================================

def create_figure(length, x, V, M, supports, point_loads, udls, uvls, point_moments, reactions, zero_points, max_m_val, max_m_pos, contraflexure):
    """Builds and returns the Matplotlib figure object."""
    fig, (ax0, ax1, ax2) = plt.subplots(3, 1, figsize=(12, 11), sharex=True)
    fig.suptitle('Mechanics Analysis Engine: Free Body Diagram, SFD & BMD', fontsize=14, fontweight='bold')

    # Panel 0: FBD
    ax0.plot([0, length], [0, 0], color='black', linewidth=6)
    ax0.set_ylim(-2.2, 2.2)
    ax0.set_ylabel('Free Body\nDiagram', fontweight='bold')
    ax0.grid(True, linestyle='--', alpha=0.4)

    # Supports
    for s in supports:
        pos = s['pos']
        if s['type'] in ['pinned', 'roller']:
            ax0.plot(pos, -0.15, '^', markersize=14, color='black')
            lbl = "Pinned" if s['type'] == 'pinned' else "Roller"
            ax0.text(pos, -0.5, f"{lbl}\nx={pos:.2f}m", ha='center', fontsize=8)
        elif s['type'] == 'fixed':
            ax0.plot([pos, pos], [-0.7, 0.7], color='black', linewidth=7)
            ax0.text(pos, 0.9, f"Fixed Wall\nx={pos:.2f}m", ha='center', fontsize=8)

    # UDLs
    for udl in udls:
        s_x, e_x, w = udl['start'], udl['end'], udl['intensity']
        ax0.add_patch(patches.Rectangle((s_x, 0.05), e_x - s_x, 0.4, color='orange', alpha=0.5))
        ax0.text((s_x + e_x)/2.0, 0.55, f"UDL: {w} kN/m", ha='center', fontweight='bold', color='darkorange', fontsize=9)

    # UVLs
    for uvl in uvls:
        s_x, e_x, w1, w2 = uvl['start'], uvl['end'], uvl['start_w'], uvl['end_w']
        h1 = 0.1 + (w1 / (max(w1, w2) + 1e-5)) * 0.4
        h2 = 0.1 + (w2 / (max(w1, w2) + 1e-5)) * 0.4
        poly_pts = [[s_x, 0.05], [e_x, 0.05], [e_x, h2], [s_x, h1]]
        ax0.add_patch(patches.Polygon(poly_pts, color='purple', alpha=0.4))
        ax0.text((s_x + e_x)/2.0, max(h1, h2) + 0.15, f"UVL: {w1}->{w2} kN/m", ha='center', fontweight='bold', color='purple', fontsize=9)

    # Point Loads
    for pl in point_loads:
        pos, mag = pl['pos'], pl['mag']
        label = f"{pl.get('orig_mag', mag):.2f} kN"
        if pl.get('angle', 90.0) != 90.0:
            label += f" @ {pl['angle']}°"
        if mag > 0:
            ax0.annotate(label, xy=(pos, 0.05), xytext=(pos, 1.3),
                         arrowprops=dict(facecolor='blue', edgecolor='blue', shrink=0.05, width=2.5, headwidth=7),
                         ha='center', fontweight='bold', color='blue', fontsize=9)
        else:
            ax0.annotate(label, xy=(pos, -0.05), xytext=(pos, -1.3),
                         arrowprops=dict(facecolor='blue', edgecolor='blue', shrink=0.05, width=2.5, headwidth=7),
                         ha='center', fontweight='bold', color='blue', fontsize=9)

    # Applied Point Moments
    for pm in point_moments:
        pos, m_val = pm['pos'], pm['mag']
        symbol = "↻" if m_val > 0 else "↺"
        ax0.plot(pos, 0, 'mo', markersize=7)
        ax0.annotate(f"{symbol} {abs(m_val):.2f} kNm", xy=(pos, 0.1), xytext=(pos, 0.75),
                     arrowprops=dict(arrowstyle="->", connectionstyle="arc3,rad=.3", color="magenta", lw=2),
                     ha='center', fontweight='bold', color='darkmagenta', fontsize=9)

    # Reactions
    for name, val in reactions.items():
        pos = float(name.split("_")[1])
        if name.startswith("R_"):
            y_arr = -1.6 if val >= 0 else 1.6
            y_tgt = -0.05 if val >= 0 else 0.05
            ax0.annotate(f"{name} = {val:.2f} kN", xy=(pos, y_tgt), xytext=(pos, y_arr),
                         arrowprops=dict(facecolor='red', edgecolor='red', shrink=0.05, width=2, headwidth=6),
                         ha='center', fontweight='bold', color='darkred', fontsize=9)
        elif name.startswith("M_"):
            ax0.text(pos, -1.0, f"{name} = {val:.2f} kNm", color='darkred', fontweight='bold', ha='center', fontsize=9)

    # Panel 1: SFD
    ax1.plot(x, V, color='blue', linewidth=2)
    ax1.fill_between(x, 0, V, where=(V >= 0), color='blue', alpha=0.3)
    ax1.fill_between(x, 0, V, where=(V < 0), color='red', alpha=0.3)
    ax1.axhline(0, color='black', linewidth=1)
    ax1.set_ylabel('Shear Force (kN)', fontweight='bold')
    ax1.grid(True, linestyle='--', alpha=0.6)

    for x_z, _ in zero_points:
        ax1.plot(x_z, 0, 'ro', markersize=7)
        ax1.annotate(f"V=0\nx={x_z:.2f}m", xy=(x_z, 0),
                     xytext=(x_z, max(V)*0.4 if max(V) != 0 else 1.0),
                     arrowprops=dict(facecolor='black', arrowstyle='->'),
                     fontweight='bold', fontsize=8,
                     bbox=dict(boxstyle='round,pad=0.2', facecolor='yellow', alpha=0.7))

    # Panel 2: BMD
    ax2.plot(x, M, color='green', linewidth=2)
    ax2.fill_between(x, 0, M, where=(M >= 0), color='green', alpha=0.3)
    ax2.fill_between(x, 0, M, where=(M < 0), color='orange', alpha=0.3)
    ax2.axhline(0, color='black', linewidth=1)
    ax2.set_ylabel('Moment (kNm)', fontweight='bold')
    ax2.set_xlabel('Position x (m)', fontweight='bold')
    ax2.grid(True, linestyle='--', alpha=0.6)

    ax2.plot(max_m_pos, max_m_val, 'go', markersize=8)
    ax2.annotate(f"Max M = {max_m_val:.2f} kNm\nat x = {max_m_pos:.2f}m",
                 xy=(max_m_pos, max_m_val),
                 xytext=(max_m_pos, max_m_val * 0.6 if max_m_val != 0 else 1.0),
                 arrowprops=dict(facecolor='green', arrowstyle='->', lw=2),
                 fontweight='bold', fontsize=8,
                 bbox=dict(boxstyle='round,pad=0.2', facecolor='lightgreen', alpha=0.8))

    for x_cf in contraflexure:
        ax2.plot(x_cf, 0, 'mo', markersize=7)
        ax2.annotate(f"Contraflexure\nx = {x_cf:.2f}m", xy=(x_cf, 0),
                     xytext=(x_cf, -max_m_val * 0.4 if max_m_val != 0 else -1.0),
                     arrowprops=dict(facecolor='purple', arrowstyle='->'),
                     fontweight='bold', fontsize=8,
                     bbox=dict(boxstyle='round,pad=0.2', facecolor='plum', alpha=0.8))

    plt.tight_layout()
    return fig


# ==============================================================================
# MAIN PROGRAM PIPELINE
# ==============================================================================

def main():
    while True:
        print("\n" + "="*65)
        print("          BEAM MECHANICS SOLVER: SFD & BMD ENGINE")
        print("="*65)
        main_opts = {
            "1": "Start New Problem (Interactive Step-by-Step)",
            "2": "Load Problem from CSV File",
            "3": "Show User Manual & CSV Specification",
            "4": "Exit"
        }
        choice = get_choice("Select an option:", main_opts)

        if choice == "3":
            display_manual()
            continue
        elif choice == "4":
            print("\nExiting program.")
            break

        # Load or enter data
        if choice == "1":
            beam_length, supports = setup_beam_interactive()
            point_loads, udls, uvls, point_moments = collect_loads_interactive(beam_length)
        elif choice == "2":
            csv_path = input("\nEnter the CSV file path: ").strip().strip('"').strip("'")
            try:
                beam_length, supports, point_loads, udls, uvls, point_moments = load_from_csv(csv_path)
                print(f"\n[+] Successfully loaded problem from '{csv_path}'.")
                print(f"    Beam Length: {beam_length} m")
                print(f"    Supports: {len(supports)} | Point Loads: {len(point_loads)} | UDLs: {len(udls)} | UVLs: {len(uvls)} | Moments: {len(point_moments)}")
            except Exception as e:
                print(f"\n[!] Failed to load CSV file: {e}")
                continue

        # Solve system
        print("\nSolving equilibrium equations...")
        try:
            x, V, M, reactions = calculate_sfd_bmd(beam_length, supports, point_loads, udls, uvls, point_moments)
            zero_points, max_m_val, max_m_pos, contraflexure = find_critical_points(x, V, M, beam_length)
        except Exception as err:
            print(f"\n[!] Calculation Error: {err}")
            continue

        # Print Output Summary
        print("\n" + "="*65)
        print("                    CALCULATION SUMMARY")
        print("="*65)
        print("\n--- SUPPORT REACTIONS ---")
        for r_name, r_val in reactions.items():
            print(f"   {r_name}: {r_val:.3f}")

        print("\n--- ZERO SHEAR & PEAK BENDING MOMENT ---")
        for x_z, m_z in zero_points:
            print(f"   V = 0 at x = {x_z:.3f} m (from right end: {beam_length - x_z:.3f} m) --> M = {m_z:.3f} kNm")
        print(f"   Global Peak Moment: {max_m_val:.3f} kNm at x = {max_m_pos:.3f} m")

        if contraflexure:
            print("\n--- POINTS OF CONTRAFLEXURE (M = 0) ---")
            for x_cf in contraflexure:
                print(f"   Contraflexure at x = {x_cf:.3f} m")

        # Build Graph Object
        fig = create_figure(beam_length, x, V, M, supports, point_loads, udls, uvls, point_moments, reactions, zero_points, max_m_val, max_m_pos, contraflexure)

        # Post-Calculation Export Options
        print("\n" + "="*65)
        print("                       EXPORT OPTIONS")
        print("="*65)

        # 1. Save Figure
        save_fig_opt = input("Save analysis figure to disk? (y/n): ").strip().lower()
        if save_fig_opt == 'y':
            target_fig = input("Enter output path (e.g., beam_result.png or .pdf): ").strip().strip('"').strip("'")
            if not target_fig:
                target_fig = "beam_analysis.png"
            try:
                fig.savefig(target_fig, dpi=300, bbox_inches='tight')
                print(f"   [+] Figure saved successfully to: {os.path.abspath(target_fig)}")
            except Exception as e:
                print(f"   [!] Error saving figure: {e}")

        # 2. Save Problem Configuration to CSV
        save_csv_opt = input("\nSave problem configuration as a reusable CSV? (y/n): ").strip().lower()
        if save_csv_opt == 'y':
            target_csv = input("Enter output CSV path (e.g., beam_problem.csv): ").strip().strip('"').strip("'")
            if not target_csv:
                target_csv = "beam_problem.csv"
            try:
                save_to_csv(target_csv, beam_length, supports, point_loads, udls, uvls, point_moments)
                print(f"   [+] Configuration saved successfully to: {os.path.abspath(target_csv)}")
            except Exception as e:
                print(f"   [!] Error saving CSV: {e}")

        # Display Figure Window
        print("\nDisplaying interactive plot window (close window to return to menu)...")
        plt.show()


if __name__ == "__main__":
    main()