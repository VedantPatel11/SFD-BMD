"""
====================================================================================================
PROJECT: AUTOMATED SHEAR FORCE & BENDING MOMENT DIAGRAM (SFD & BMD) ENGINE
COURSE: 21CSO352T - Python Programming
STUDENTS:
  - Shon Parale   (Reg. No: RA2311072010002)
  - Vedant Patel  (Reg. No: RA2311072010009)
DEPARTMENT: Mechanical Engineering, College of Engineering and Technology,
            SRM Institute of Science and Technology, Kattankulathur - 603203

FILE: sfd_bmd_engine_4.py (Final Milestone Version)

SUMMARY OF CAPABILITIES:
  1. Static Equilibrium Solver for determinate beams (Cantilever and Simply Supported/Overhanging).
  2. Diverse Loading Conditions:
     - Concentrated Point Loads (Vertical down/up, or arbitrary inclination angles).
     - Uniformly Distributed Loads (UDL) over arbitrary spans.
     - Uniformly Varying Loads (UVL - linear trapezoidal/triangular profiles).
     - Concentrated Point Couples / Moments (Clockwise or Counter-Clockwise).
  3. Continuous Singularity-Function Numerical Integration for SFD and BMD curves.
  4. Exact Critical Point Analytics:
     - Zero-shear crossing detection via root-finding linear interpolation.
     - Global maximum bending moment evaluation.
     - Points of contraflexure (inflection points where Bending Moment = 0).
  5. Multi-format Data Ingestion & Persistence via structured CSV files.
  6. Dual-Coordinate System: Allows distance entry from Left (x=0) or Right (x=L).
  7. High-Resolution 3-Tier Visualizer (Free Body Diagram, SFD, BMD) with Matplotlib export.
====================================================================================================
"""

import os
import csv
import math
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# Directory where this script resides; ensures relative paths work consistently across all environments
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else os.getcwd()


# ==============================================================================
# 1. USER MANUAL & DOCUMENTATION
# ==============================================================================

def display_manual():
    """
    Displays an in-terminal user guide, theoretical background, sign conventions,
    and the structured CSV schema specification.
    """
    manual_text = """
================================================================================
                    BEAM ANALYSIS ENGINE: USER MANUAL
================================================================================

1. OVERVIEW
   This computational engine analyzes statically determinate structural beams and computes:
   - External support reactions (Fy vertical reactions and fixed-end clamping moments).
   - Shear Force Diagram (SFD) across the entire longitudinal axis.
   - Bending Moment Diagram (BMD) with continuous curve integration.
   - Exact zero-shear crossing locations (governing locations of local extrema for M).
   - Global peak bending moment magnitude and exact position.
   - Points of contraflexure (where bending moment crosses zero / inflection points).
   - High-resolution Free Body Diagram (FBD) visualizer with accurate mechanical annotations.

2. SUPPORTED BOUNDARY CONDITIONS (STATICALLY DETERMINATE)
   - Simply Supported / Overhanging: Exactly 2 supports (Pinned or Roller).
   - Cantilever Beam: Exactly 1 Fixed Clamping Support (at left x = 0 or right x = L).

3. SIGN CONVENTIONS
   - Transverse Forces: Downward loads (gravity) are positive internally for applied load sum;
     Support upward reaction forces are treated as positive reactions.
   - Moments / Couples: Clockwise (CW) = (+), Counter-Clockwise (CCW) = (-).
   - Shear Force (V): Upward force to the left of section creates POSITIVE shear.
   - Bending Moment (M): Sagging (concave upward / tension on bottom fibers) is POSITIVE (+);
     Hogging (convex upward / tension on top fibers) is NEGATIVE (-).

4. DUAL-REFERENCE COORDINATE ENTRY
   - Locations can be referenced either from the LEFT end (x = 0) or RIGHT end (x = L).
   - The engine automatically maps right-referenced inputs: x = L - distance_from_right.

5. CSV SPECIFICATION RULES
   - Files are stored in the current working directory beside this program.
   - Section headers: [BEAM], [SUPPORTS], [POINT_LOADS], [UDLS], [UVLS], [MOMENTS].
   - Blank rows or unused sections are ignored gracefully.
================================================================================
"""
    print(manual_text)


# ==============================================================================
# 2. INPUT HELPERS WITH ERROR HANDLING & COORDINATE TRANSFORMATIONS
# ==============================================================================

def get_float(prompt, min_val=None, max_val=None):
    """
    Prompts the user for a numerical floating-point input with comprehensive validation
    against invalid types and specified minimum/maximum mathematical bounds.
    """
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
    """
    Displays a structured menu of choices and ensures the user enters a valid selection key.
    """
    print(prompt)
    for key, val in options.items():
        print(f"   {key}. {val}")
    while True:
        choice = input("Select option number: ").strip()
        if choice in options:
            return choice
        print("   [!] Invalid choice. Try again.")


def get_position(beam_length, label="position"):
    """
    Reads a longitudinal position along the beam, offering the user the flexibility to
    measure from either the LEFT end (x = 0) or the RIGHT end (x = L).
    Automatically maps the input into canonical absolute coordinates measured from the left.
    """
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
# 3. INTERACTIVE LOAD COLLECTION MODULES
# ==============================================================================

def setup_beam_interactive():
    """
    Guides the user through setting up beam length and boundary supports.
    Validates static determinacy (either 1 fixed support or 2 pin/roller supports).
    """
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


def collect_point_loads(beam_length):
    """
    Collects concentrated point loads interactively.
    Supports downward, upward, and inclined/angled point forces with vector resolution:
        Vertical transverse component: Py = P * sin(theta)
        Horizontal axial component:    Px = P * cos(theta)
    """
    point_loads = []
    print("\n" + "="*65)
    print("                  COLLECT POINT LOADS")
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
            direction_str = "down"
        elif dir_ch == "2":
            vert_load = -mag
            axial_load = 0.0
            direction_str = "up"
        elif dir_ch == "3":
            angle_deg = get_float("Angle relative to horizontal beam axis (deg): ", min_val=0.1, max_val=179.9)
            angle_rad = math.radians(angle_deg)
            vert_load = mag * math.sin(angle_rad)
            axial_load = mag * math.cos(angle_rad)
            direction_str = "angled"
            print(f"   --> Transverse vertical component (Py): {vert_load:.3f} kN")
            print(f"   --> Axial horizontal component (Px): {axial_load:.3f} kN")
            
        point_loads.append({
            'mag': vert_load,
            'pos': pos,
            'orig_mag': mag,
            'axial': axial_load,
            'angle': angle_deg,
            'direction': direction_str
        })
    return point_loads


def collect_udls(beam_length):
    """
    Collects Uniformly Distributed Loads (UDL) of constant intensity w (kN/m)
    acting over a defined interval [start_x, end_x].
    """
    udls = []
    print("\n" + "="*65)
    print("           COLLECT UNIFORMLY DISTRIBUTED LOADS (UDL)")
    print("="*65)
    while input("Add a Uniformly Distributed Load (UDL)? (y/n): ").strip().lower() == 'y':
        w = get_float("Enter load intensity w (kN/m): ", min_val=0.01)
        start_x = get_position(beam_length, "UDL START position")
        end_x = get_position(beam_length, "UDL END position")
        if start_x > end_x:
            start_x, end_x = end_x, start_x
        udls.append({'intensity': w, 'start': start_x, 'end': end_x})
    return udls


def collect_uvls(beam_length):
    """
    Collects Uniformly Varying Loads (UVL - linear triangular or trapezoidal loads)
    defined by initial intensity w_start and terminal intensity w_end over [start_x, end_x].
    """
    uvls = []
    print("\n" + "="*65)
    print("           COLLECT UNIFORMLY VARYING LOADS (UVL)")
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
    return uvls


def collect_moments(beam_length):
    """
    Collects concentrated point moments (couples) with directional sign convention:
        Clockwise (+) or Counter-Clockwise (-).
    """
    point_moments = []
    print("\n" + "="*65)
    print("             COLLECT CONCENTRATED MOMENTS")
    print("="*65)
    while input("Add a Concentrated Moment / Couple? (y/n): ").strip().lower() == 'y':
        mag = get_float("Enter moment magnitude (kNm): ", min_val=0.01)
        pos = get_position(beam_length, "Moment")
        m_opts = {"1": "Clockwise (+)", "2": "Counter-Clockwise (-)"}
        m_ch = get_choice("Direction:", m_opts)
        effective_m = mag if m_ch == "1" else -mag
        point_moments.append({'mag': effective_m, 'pos': pos})
    return point_moments


def review_and_verify(beam_length, supports, point_loads, udls, uvls, point_moments):
    """
    Interactive review and verification loop.
    Allows the user to inspect all entered data, review summaries, add further loads,
    or restart the configuration before committing to solver computation.
    """
    while True:
        print("\n" + "="*65)
        print("                 STEP 6: REVIEW & VERIFY")
        print("="*65)
        print(f"Beam Length: {beam_length:.2f} m")
        print("Supports: " + ", ".join([f"{s['type']} @ {s['pos']:.2f}m" for s in supports]))
        
        pl_strs = [f"{pl.get('orig_mag', abs(pl['mag'])):.2f}kN ({pl.get('direction','load')}) @ {pl['pos']:.2f}m" for pl in point_loads]
        print(f"Point Loads ({len(point_loads)}): " + (", ".join(pl_strs) if pl_strs else "None"))
        
        udl_strs = [f"{u['intensity']}kN/m ({u['start']:.2f}m -> {u['end']:.2f}m)" for u in udls]
        print(f"UDLs ({len(udls)}): " + (", ".join(udl_strs) if udl_strs else "None"))
        
        uvl_strs = [f"{uv['start_w']}->{uv['end_w']}kN/m ({uv['start']:.2f}m -> {uv['end']:.2f}m)" for uv in uvls]
        print(f"UVLs ({len(uvls)}): " + (", ".join(uvl_strs) if uvl_strs else "None"))
        
        m_strs = [f"{abs(pm['mag']):.2f}kNm ({'CW' if pm['mag']>=0 else 'CCW'}) @ {pm['pos']:.2f}m" for pm in point_moments]
        print(f"Moments ({len(point_moments)}): " + (", ".join(m_strs) if m_strs else "None"))

        chk = input("\nIs there anything left to add or modify? (y/n): ").strip().lower()
        if chk != 'y':
            break

        menu = {
            "1": "Add more Point Loads",
            "2": "Add more UDLs",
            "3": "Add more UVLs",
            "4": "Add more Concentrated Moments",
            "5": "Redo entire setup from Step 1 to Last",
            "6": "Proceed to Calculation"
        }
        choice = get_choice("\nSelect what to modify:", menu)

        if choice == "1":
            point_loads.extend(collect_point_loads(beam_length))
        elif choice == "2":
            udls.extend(collect_udls(beam_length))
        elif choice == "3":
            uvls.extend(collect_uvls(beam_length))
        elif choice == "4":
            point_moments.extend(collect_moments(beam_length))
        elif choice == "5":
            beam_length, supports = setup_beam_interactive()
            point_loads = collect_point_loads(beam_length)
            udls = collect_udls(beam_length)
            uvls = collect_uvls(beam_length)
            point_moments = collect_moments(beam_length)
        elif choice == "6":
            break

    return beam_length, supports, point_loads, udls, uvls, point_moments


# ==============================================================================
# 4. CSV IMPORT & EXPORT ENGINE
# ==============================================================================

def load_from_csv(filename):
    """
    Parses a beam mechanics configuration from a CSV file.
    Supports reading locations from left or right coordinate references, handles
    case-insensitive headers, trims whitespace, and validates the presence of critical parameters.
    """
    clean_name = filename.strip().strip('"').strip("'")
    if not clean_name.lower().endswith('.csv'):
        clean_name += '.csv'
    
    filepath = os.path.join(SCRIPT_DIR, clean_name)
    if not os.path.exists(filepath):
        if os.path.exists(clean_name):
            filepath = clean_name
        else:
            raise FileNotFoundError(f"'{clean_name}' not found beside program.")

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

            if first_cell.startswith("[") and first_cell.endswith("]"):
                current_section = first_cell.upper()
                continue

            if current_section == "[BEAM]":
                if first_cell.lower() == 'length_m':
                    continue
                length = float(first_cell)

            elif current_section == "[SUPPORTS]":
                if first_cell.lower() in ['type', 'support_type']:
                    continue
                stype = first_cell.lower()
                left_str = row[1].strip() if len(row) > 1 else ""
                right_str = row[2].strip() if len(row) > 2 else ""

                if left_str != "":
                    pos = float(left_str)
                elif right_str != "":
                    pos = length - float(right_str)
                else:
                    continue
                supports.append({'type': stype, 'pos': pos})

            elif current_section == "[POINT_LOADS]":
                if first_cell.lower() in ['mag', 'mag_kn', 'magnitude']:
                    continue
                raw_mag = float(first_cell)
                direction = row[1].strip().lower() if len(row) > 1 else 'down'
                left_str = row[2].strip() if len(row) > 2 else ""
                right_str = row[3].strip() if len(row) > 3 else ""
                angle = float(row[4].strip()) if (len(row) > 4 and row[4].strip()) else 90.0

                if left_str != "":
                    pos = float(left_str)
                elif right_str != "":
                    pos = length - float(right_str)
                else:
                    continue

                angle_rad = math.radians(angle)
                vert_mag = raw_mag * math.sin(angle_rad)
                axial_mag = raw_mag * math.cos(angle_rad)
                effective_mag = -vert_mag if direction == 'up' else vert_mag

                point_loads.append({
                    'mag': effective_mag,
                    'pos': pos,
                    'orig_mag': raw_mag,
                    'axial': axial_mag,
                    'angle': angle,
                    'direction': direction
                })

            elif current_section == "[UDLS]":
                if first_cell.lower() in ['intensity', 'intensity_kn_per_m']:
                    continue
                w = float(first_cell)
                left_s = row[1].strip() if len(row) > 1 else ""
                left_e = row[2].strip() if len(row) > 2 else ""
                right_s = row[3].strip() if len(row) > 3 else ""
                right_e = row[4].strip() if len(row) > 4 else ""

                start_x = float(left_s) if left_s != "" else (length - float(right_s))
                end_x = float(left_e) if left_e != "" else (length - float(right_e))
                if start_x > end_x:
                    start_x, end_x = end_x, start_x
                udls.append({'intensity': w, 'start': start_x, 'end': end_x})

            elif current_section == "[UVLS]":
                if first_cell.lower() in ['start_w', 'start_w_kn_per_m']:
                    continue
                w1 = float(first_cell)
                w2 = float(row[1].strip())
                left_s = row[2].strip() if len(row) > 2 else ""
                left_e = row[3].strip() if len(row) > 3 else ""
                right_s = row[4].strip() if len(row) > 4 else ""
                right_e = row[5].strip() if len(row) > 5 else ""

                start_x = float(left_s) if left_s != "" else (length - float(right_s))
                end_x = float(left_e) if left_e != "" else (length - float(right_e))
                if start_x > end_x:
                    start_x, end_x = end_x, start_x
                    w1, w2 = w2, w1
                uvls.append({'start_w': w1, 'end_w': w2, 'start': start_x, 'end': end_x})

            elif current_section == "[MOMENTS]":
                if first_cell.lower() in ['mag', 'magnitude', 'mag_knm']:
                    continue
                if len(row) >= 3 and row[1].strip().lower() in ['clockwise', 'counter-clockwise', 'cw', 'ccw', '+', '-']:
                    mag = abs(float(first_cell))
                    direction = row[1].strip().lower()
                    left_str = row[2].strip()
                    right_str = row[3].strip() if len(row) > 3 else ""
                    pos = float(left_str) if left_str != "" else (length - float(right_str))
                    effective_m = mag if direction in ['clockwise', 'cw', '+'] else -mag
                else:
                    effective_m = float(first_cell)
                    pos = float(row[1].strip())
                point_moments.append({'mag': effective_m, 'pos': pos})

    if length is None or length <= 0:
        raise ValueError("Invalid or missing beam length in CSV.")
    if not supports:
        raise ValueError("No supports defined in CSV.")

    return length, supports, point_loads, udls, uvls, point_moments


def save_to_csv(filename, length, supports, point_loads, udls, uvls, point_moments):
    """
    Serializes and exports the full beam configuration to a clean, human-readable CSV format.
    Includes both left and right dimension coordinates for clear review in spreadsheet viewers.
    """
    clean_name = filename.strip().strip('"').strip("'")
    if not clean_name.lower().endswith('.csv'):
        clean_name += '.csv'
    
    filepath = os.path.join(SCRIPT_DIR, clean_name)

    with open(filepath, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)

        # Beam Geometry
        writer.writerow(["[BEAM]"])
        writer.writerow(["length_m"])
        writer.writerow([round(length, 3)])
        writer.writerow([])

        # Support Boundary Conditions
        writer.writerow(["[SUPPORTS]"])
        writer.writerow(["type", "pos_from_left_m", "pos_from_right_m"])
        for s in supports:
            writer.writerow([s['type'], round(s['pos'], 3), round(length - s['pos'], 3)])
        writer.writerow([])

        # Concentrated Loads
        writer.writerow(["[POINT_LOADS]"])
        writer.writerow(["mag_kN", "direction", "pos_from_left_m", "pos_from_right_m", "angle_deg"])
        for pl in point_loads:
            mag_val = round(pl.get('orig_mag', abs(pl['mag'])), 3)
            dir_str = pl.get('direction', 'down' if pl['mag'] >= 0 else 'up')
            writer.writerow([mag_val, dir_str, round(pl['pos'], 3), round(length - pl['pos'], 3), pl.get('angle', 90.0)])
        writer.writerow([])

        # Uniformly Distributed Loads
        writer.writerow(["[UDLS]"])
        writer.writerow(["intensity_kN_per_m", "start_from_left_m", "end_from_left_m", "start_from_right_m", "end_from_right_m"])
        for u in udls:
            writer.writerow([round(u['intensity'], 3), round(u['start'], 3), round(u['end'], 3),
                             round(length - u['start'], 3), round(length - u['end'], 3)])
        writer.writerow([])

        # Uniformly Varying Loads
        writer.writerow(["[UVLS]"])
        writer.writerow(["start_w_kN_per_m", "end_w_kN_per_m", "start_from_left_m", "end_from_left_m", "start_from_right_m", "end_from_right_m"])
        for uv in uvls:
            writer.writerow([round(uv['start_w'], 3), round(uv['end_w'], 3), round(uv['start'], 3), round(uv['end'], 3),
                             round(length - uv['start'], 3), round(length - uv['end'], 3)])
        writer.writerow([])

        # Concentrated Couples / Moments
        writer.writerow(["[MOMENTS]"])
        writer.writerow(["mag_kNm", "direction", "pos_from_left_m", "pos_from_right_m"])
        for pm in point_moments:
            dir_str = "clockwise" if pm['mag'] >= 0 else "counter-clockwise"
            writer.writerow([round(abs(pm['mag']), 3), dir_str, round(pm['pos'], 3), round(length - pm['pos'], 3)])

    return clean_name


# ==============================================================================
# 5. STATIC EQUILIBRIUM SOLVER & COMPUTATION ENGINE
# ==============================================================================

def solve_reactions(length, supports, point_loads, udls, uvls, point_moments):
    """
    Computes external reaction forces and moments using Newton's laws of static equilibrium:
        Sum of Vertical Forces:  Sigma(Fy) = 0
        Sum of Moments at x = 0: Sigma(M_0) = 0
    
    Supports:
        - Cantilever (1 Fixed Support): Solves vertical reaction R_y and clamping moment M_fixed.
        - Simply Supported / Overhanging (2 Pinned/Roller Supports): Solves linear system for R1, R2.
    """
    # 1. Accumulate total applied vertical forces and moments about x = 0
    total_F = sum(pl['mag'] for pl in point_loads)
    total_M_zero = sum(pl['mag'] * pl['pos'] for pl in point_loads)

    # 2. Add contribution of Uniformly Distributed Loads (UDL)
    for udl in udls:
        span = udl['end'] - udl['start']
        force = udl['intensity'] * span
        centroid = udl['start'] + span / 2.0
        total_F += force
        total_M_zero += force * centroid

    # 3. Add contribution of Uniformly Varying Loads (UVL - linear profile)
    for uvl in uvls:
        span = uvl['end'] - uvl['start']
        force = 0.5 * (uvl['start_w'] + uvl['end_w']) * span
        # Calculate centroid distance from start of UVL
        if (uvl['start_w'] + uvl['end_w']) > 0:
            rel_centroid = (span / 3.0) * ((uvl['start_w'] + 2 * uvl['end_w']) / (uvl['start_w'] + uvl['end_w']))
        else:
            rel_centroid = span / 2.0
        centroid = uvl['start'] + rel_centroid
        total_F += force
        total_M_zero += force * centroid

    # 4. Add concentrated point moments
    for pm in point_moments:
        total_M_zero += pm['mag']

    fixed = [s for s in supports if s['type'] == 'fixed']
    pin_roller = [s for s in supports if s['type'] in ['pinned', 'roller']]

    reactions = {}

    # Case A: Cantilever Beam (Single Fixed Support)
    if len(fixed) == 1 and len(pin_roller) == 0:
        x_s = fixed[0]['pos']
        R_y = total_F
        # Moment equilibrium about fixed support location: M_fixed + M_applied - F_applied * x_s = 0
        M_fixed = -(total_M_zero - total_F * x_s)
        reactions[f"R_{x_s:.2f}"] = R_y
        reactions[f"M_{x_s:.2f}"] = M_fixed

    # Case B: Simply Supported / Overhanging Beam (Two Pin/Roller Supports)
    elif len(pin_roller) == 2 and len(fixed) == 0:
        pin_roller.sort(key=lambda s: s['pos'])
        x1, x2 = pin_roller[0]['pos'], pin_roller[1]['pos']
        if abs(x2 - x1) < 1e-5:
            raise ValueError("Supports cannot be placed at the exact same location.")
        
        # Take moments about support 1: Sigma(M_at_x1) = 0
        M_about_x1 = total_M_zero - total_F * x1
        R2 = M_about_x1 / (x2 - x1)
        R1 = total_F - R2
        reactions[f"R_{x1:.2f}"] = R1
        reactions[f"R_{x2:.2f}"] = R2
    else:
        raise ValueError("System indeterminate. Provide exactly 1 Fixed or 2 Pinned/Roller supports.")

    return reactions


def calculate_sfd_bmd(length, supports, point_loads, udls, uvls, point_moments, num_points=5000):
    """
    Evaluates continuous Shear Force V(x) and Bending Moment M(x) along the beam using
    Macaulay / Singularity Function formulation evaluated across a dense grid of 5,000 points.
    
    Differential Governing Relations:
        dV/dx = -w(x)
        dM/dx = V(x)
    """
    reactions = solve_reactions(length, supports, point_loads, udls, uvls, point_moments)
    x = np.linspace(0.0, length, num_points)
    V = np.zeros(num_points)
    M = np.zeros(num_points)

    # Superposition of support reactions
    for name, val in reactions.items():
        x_r = float(name.split("_")[1])
        mask = x >= x_r
        if name.startswith("R_"):
            # Upward reaction contributes positive shear and positive sagging moment
            V[mask] += val
            M[mask] += val * (x[mask] - x_r)
        elif name.startswith("M_"):
            # Fixed clamping moment
            M[mask] += val

    # Superposition of concentrated point loads
    for pl in point_loads:
        mask = x >= pl['pos']
        # Downward load causes downward step in shear, hogging curvature
        V[mask] -= pl['mag']
        M[mask] -= pl['mag'] * (x[mask] - pl['pos'])

    # Superposition of Uniformly Distributed Loads (UDL)
    for udl in udls:
        for i, xi in enumerate(x):
            if xi > udl['start']:
                eff_end = min(xi, udl['end'])
                len_left = eff_end - udl['start']
                force = udl['intensity'] * len_left
                centroid = udl['start'] + len_left / 2.0
                V[i] -= force
                M[i] -= force * (xi - centroid)

    # Superposition of Uniformly Varying Loads (UVL)
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

    # Superposition of concentrated moments
    for pm in point_moments:
        mask = x >= pm['pos']
        M[mask] -= pm['mag']

    return x, V, M, reactions


def find_critical_points(x, V, M):
    """
    Numerically identifies key engineering critical points:
        1. Zero-Shear Crossings: Points where V(x) changes sign. Since dM/dx = V,
           these points correspond to the local mathematical extrema of Bending Moment M(x).
           Uses linear interpolation root-finding for sub-millimeter precision.
        2. Global Maximum Bending Moment: Magnitude and exact coordinate.
        3. Points of Contraflexure: Points where M(x) crosses zero (inflection points).
    """
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
# 6. VISUALIZATION ENGINE (3 ALIGNED PANELS: FBD, SFD, BMD)
# ==============================================================================

def create_figure(length, x, V, M, supports, point_loads, udls, uvls, point_moments, reactions, zero_points, max_m_val, max_m_pos, contraflexure):
    """
    Generates a synchronized 3-panel publication-grade mechanics plot:
        Panel 1 (Top):    Free Body Diagram (FBD) showing beam span, supports, applied loads, and reaction vectors.
        Panel 2 (Middle): Shear Force Diagram (SFD) with shaded regions and zero-shear callouts.
        Panel 3 (Bottom): Bending Moment Diagram (BMD) with peak moment and contraflexure points.
    """
    fig, (ax0, ax1, ax2) = plt.subplots(3, 1, figsize=(12, 11), sharex=True)
    fig.suptitle('Mechanics Analysis Engine: Free Body Diagram, SFD & BMD', fontsize=14, fontweight='bold')

    # --------------------------------------------------------------------------
    # Panel 1: Free Body Diagram (FBD)
    # --------------------------------------------------------------------------
    ax0.plot([0, length], [0, 0], color='black', linewidth=6)
    ax0.set_ylim(-2.2, 2.2)
    ax0.set_ylabel('Free Body\nDiagram', fontweight='bold')
    ax0.grid(True, linestyle='--', alpha=0.4)

    # Render Supports (Pinned, Roller, Fixed)
    for s in supports:
        pos = s['pos']
        if s['type'] in ['pinned', 'roller']:
            ax0.plot(pos, -0.15, '^', markersize=14, color='black')
            lbl = "Pinned" if s['type'] == 'pinned' else "Roller"
            ax0.text(pos, -0.5, f"{lbl}\nx={pos:.2f}m", ha='center', fontsize=8)
        elif s['type'] == 'fixed':
            ax0.plot([pos, pos], [-0.7, 0.7], color='black', linewidth=7)
            ax0.text(pos, 0.9, f"Fixed Wall\nx={pos:.2f}m", ha='center', fontsize=8)

    # Render UDL Patches
    for udl in udls:
        s_x, e_x, w = udl['start'], udl['end'], udl['intensity']
        ax0.add_patch(patches.Rectangle((s_x, 0.05), e_x - s_x, 0.4, color='orange', alpha=0.5))
        ax0.text((s_x + e_x)/2.0, 0.55, f"UDL: {w} kN/m", ha='center', fontweight='bold', color='darkorange', fontsize=9)

    # Render UVL Polygonal Patches
    for uvl in uvls:
        s_x, e_x, w1, w2 = uvl['start'], uvl['end'], uvl['start_w'], uvl['end_w']
        h1 = 0.1 + (w1 / (max(w1, w2) + 1e-5)) * 0.4
        h2 = 0.1 + (w2 / (max(w1, w2) + 1e-5)) * 0.4
        poly_pts = [[s_x, 0.05], [e_x, 0.05], [e_x, h2], [s_x, h1]]
        ax0.add_patch(patches.Polygon(poly_pts, color='purple', alpha=0.4))
        ax0.text((s_x + e_x)/2.0, max(h1, h2) + 0.15, f"UVL: {w1}->{w2} kN/m", ha='center', fontweight='bold', color='purple', fontsize=9)

    # Render Applied Point Loads
    for pl in point_loads:
        pos, mag = pl['pos'], pl['mag']
        label = f"{pl.get('orig_mag', abs(mag)):.2f} kN"
        if mag > 0:
            ax0.annotate(label, xy=(pos, 0.05), xytext=(pos, 1.3),
                         arrowprops=dict(facecolor='blue', edgecolor='blue', shrink=0.05, width=2.5, headwidth=7),
                         ha='center', fontweight='bold', color='blue', fontsize=9)
        else:
            ax0.annotate(label, xy=(pos, -0.05), xytext=(pos, -1.3),
                         arrowprops=dict(facecolor='blue', edgecolor='blue', shrink=0.05, width=2.5, headwidth=7),
                         ha='center', fontweight='bold', color='blue', fontsize=9)

    # Render Concentrated Moments (Couples)
    for pm in point_moments:
        pos, m_val = pm['pos'], pm['mag']
        symbol = "↻" if m_val > 0 else "↺"
        ax0.plot(pos, 0, 'mo', markersize=7)
        ax0.annotate(f"{symbol} {abs(m_val):.2f} kNm", xy=(pos, 0.1), xytext=(pos, 0.75),
                     arrowprops=dict(arrowstyle="->", connectionstyle="arc3,rad=.3", color="magenta", lw=2),
                     ha='center', fontweight='bold', color='darkmagenta', fontsize=9)

    # Render Support Reaction Vectors (Red Arrows)
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

    # --------------------------------------------------------------------------
    # Panel 2: Shear Force Diagram (SFD)
    # --------------------------------------------------------------------------
    ax1.plot(x, V, color='blue', linewidth=2)
    ax1.fill_between(x, 0, V, where=(V >= 0), color='blue', alpha=0.3)
    ax1.fill_between(x, 0, V, where=(V < 0), color='red', alpha=0.3)
    ax1.axhline(0, color='black', linewidth=1)
    ax1.set_ylabel('Shear Force (kN)', fontweight='bold')
    ax1.grid(True, linestyle='--', alpha=0.6)

    # Annotate Zero-Shear Points
    for x_z, _ in zero_points:
        ax1.plot(x_z, 0, 'ro', markersize=7)
        ax1.annotate(f"V=0\nx={x_z:.2f}m", xy=(x_z, 0),
                     xytext=(x_z, max(V)*0.4 if max(V) != 0 else 1.0),
                     arrowprops=dict(facecolor='black', arrowstyle='->'),
                     fontweight='bold', fontsize=8,
                     bbox=dict(boxstyle='round,pad=0.2', facecolor='yellow', alpha=0.7))

    # --------------------------------------------------------------------------
    # Panel 3: Bending Moment Diagram (BMD)
    # --------------------------------------------------------------------------
    ax2.plot(x, M, color='green', linewidth=2)
    ax2.fill_between(x, 0, M, where=(M >= 0), color='green', alpha=0.3)
    ax2.fill_between(x, 0, M, where=(M < 0), color='orange', alpha=0.3)
    ax2.axhline(0, color='black', linewidth=1)
    ax2.set_ylabel('Moment (kNm)', fontweight='bold')
    ax2.set_xlabel('Position x (m)', fontweight='bold')
    ax2.grid(True, linestyle='--', alpha=0.6)

    # Annotate Global Peak Bending Moment
    ax2.plot(max_m_pos, max_m_val, 'go', markersize=8)
    ax2.annotate(f"Max M = {max_m_val:.2f} kNm\nat x = {max_m_pos:.2f}m",
                 xy=(max_m_pos, max_m_val),
                 xytext=(max_m_pos, max_m_val * 0.6 if max_m_val != 0 else 1.0),
                 arrowprops=dict(facecolor='green', arrowstyle='->', lw=2),
                 fontweight='bold', fontsize=8,
                 bbox=dict(boxstyle='round,pad=0.2', facecolor='lightgreen', alpha=0.8))

    # Annotate Contraflexure Points
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
# 7. MAIN PROGRAM EXECUTION PIPELINE
# ==============================================================================

def main():
    """
    Main orchestrator driving interactive user selection, CSV loading,
    solver execution, summary reporting, export, and visualization.
    """
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

        if choice == "1":
            beam_length, supports = setup_beam_interactive()
            point_loads = collect_point_loads(beam_length)
            udls = collect_udls(beam_length)
            uvls = collect_uvls(beam_length)
            point_moments = collect_moments(beam_length)
            
            # Interactive review and verification loop
            beam_length, supports, point_loads, udls, uvls, point_moments = review_and_verify(
                beam_length, supports, point_loads, udls, uvls, point_moments
            )

        elif choice == "2":
            csv_name = input("\nEnter CSV file name (e.g. beam): ").strip()
            try:
                beam_length, supports, point_loads, udls, uvls, point_moments = load_from_csv(csv_name)
                print(f"\n[+] Successfully loaded '{csv_name}'.")
            except Exception as e:
                print(f"\n[!] Failed to load CSV file: {e}")
                continue

        print("\nSolving equilibrium equations...")
        try:
            x, V, M, reactions = calculate_sfd_bmd(beam_length, supports, point_loads, udls, uvls, point_moments)
            zero_points, max_m_val, max_m_pos, contraflexure = find_critical_points(x, V, M)
        except Exception as err:
            print(f"\n[!] Calculation Error: {err}")
            continue

        print("\n" + "="*65)
        print("                    CALCULATION SUMMARY")
        print("="*65)
        print("\n--- SUPPORT REACTIONS ---")
        for r_name, r_val in reactions.items():
            print(f"   {r_name}: {r_val:.3f}")

        print("\n--- ZERO SHEAR & PEAK BENDING MOMENT ---")
        for x_z, m_z in zero_points:
            print(f"   V = 0 at x = {x_z:.3f} m (from right: {beam_length - x_z:.3f} m) --> M = {m_z:.3f} kNm")
        print(f"   Global Peak Moment: {max_m_val:.3f} kNm at x = {max_m_pos:.3f} m")

        if contraflexure:
            print("\n--- POINTS OF CONTRAFLEXURE (M = 0) ---")
            for x_cf in contraflexure:
                print(f"   Contraflexure at x = {x_cf:.3f} m")

        fig = create_figure(beam_length, x, V, M, supports, point_loads, udls, uvls, point_moments, reactions, zero_points, max_m_val, max_m_pos, contraflexure)

        print("\n" + "="*65)
        print("                       EXPORT OPTIONS")
        print("="*65)

        if input("Save analysis figure? (y/n): ").strip().lower() == 'y':
            img_name = input("Enter image file name (e.g. beam): ").strip().strip('"').strip("'")
            if not img_name:
                img_name = "beam_analysis"
            if not img_name.lower().endswith(('.png', '.pdf', '.svg')):
                img_name += '.png'
            out_img_path = os.path.join(SCRIPT_DIR, img_name)
            try:
                fig.savefig(out_img_path, dpi=300, bbox_inches='tight')
                print(f"   [+] Figure saved successfully as: {img_name}")
            except Exception as e:
                print(f"   [!] Error saving figure: {e}")

        if input("\nSave problem configuration as CSV? (y/n): ").strip().lower() == 'y':
            csv_name = input("Enter CSV file name (e.g. beam): ").strip()
            if not csv_name:
                csv_name = "beam_problem"
            try:
                saved_as = save_to_csv(csv_name, beam_length, supports, point_loads, udls, uvls, point_moments)
                print(f"   [+] Problem saved successfully as: {saved_as}")
            except Exception as e:
                print(f"   [!] Error saving CSV: {e}")

        print("\nDisplaying interactive plot window (close window to return to menu)...")
        plt.show()


if __name__ == "__main__":
    main()
