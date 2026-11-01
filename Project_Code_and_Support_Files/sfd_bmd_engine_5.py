# Shon Parale | Vedant Patel
# SFD & BMD Mechanics Analysis Engine

import os
import csv
import math
import tkinter as tk
from tkinter import filedialog
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# Directory where the script resides
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else os.getcwd()

# ==============================================================================
# 1. FILE EXPLORER DIALOG HELPERS
# ==============================================================================

def open_csv_dialog():
    """Opens OS file explorer to select a CSV file."""
    root = tk.Tk()
    root.withdraw()
    root.attributes('-topmost', True)
    file_path = filedialog.askopenfilename(
        title="Select Beam Problem CSV File",
        initialdir=SCRIPT_DIR,
        filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")]
    )
    root.destroy()
    return file_path


def save_csv_dialog():
    """Opens OS file explorer to choose where to save a problem CSV."""
    root = tk.Tk()
    root.withdraw()
    root.attributes('-topmost', True)
    file_path = filedialog.asksaveasfilename(
        title="Save Problem Configuration as CSV",
        initialdir=SCRIPT_DIR,
        defaultextension=".csv",
        filetypes=[("CSV Files", "*.csv")]
    )
    root.destroy()
    return file_path


def save_image_dialog():
    """Opens OS file explorer to choose where to save the analysis figure."""
    root = tk.Tk()
    root.withdraw()
    root.attributes('-topmost', True)
    file_path = filedialog.asksaveasfilename(
        title="Save Analysis Diagram",
        initialdir=SCRIPT_DIR,
        defaultextension=".png",
        filetypes=[
            ("PNG Image", "*.png"),
            ("PDF Document", "*.pdf"),
            ("SVG Vector", "*.svg"),
            ("All Files", "*.*")
        ]
    )
    root.destroy()
    return file_path


# ==============================================================================
# 2. USER MANUAL & DOCUMENTATION
# ==============================================================================

def display_manual():
    """Prints the in-terminal user guide and CSV specification."""
    manual_text = """

BEAM ANALYSIS ENGINE: USER MANUAL
Shon Parale | Vedant Patel


1. OVERVIEW
   This tool computes:
   - Support reactions (Vertical, Horizontal, and Fixed moments).
   - Shear Force Diagram (SFD) with true step jumps.
   - Bending Moment Diagram (BMD) with peak cusp capture.
   - Zero-shear crossing points, global peak moments, and contraflexure points.
   - High-resolution Free Body Diagram (FBD) visualizer.

2. BOUNDARY CONDITIONS (Statically Determinate)
   - Simply Supported / Overhanging: Exactly 2 supports (Pinned + Roller).
   - Cantilever: Exactly 1 Fixed support (Left x=0 or Right x=L).

3. SIGN CONVENTIONS
   - Downward Forces: Positive (+) input; Upward Forces: Negative (-).
   - Axial Forces: Rightward is positive (+).
   - Moments: Clockwise is positive (+); Counter-Clockwise is negative (-).
   - BMD Plot: Sagging (tension at bottom) is positive (+); Hogging is negative (-).

4. CSV POSITION RULES (LEFT vs RIGHT)
   - You can enter either 'pos_from_left_m' or 'pos_from_right_m'.
   - If left is left blank, the solver automatically calculates: pos = length - right.
   - If right is left blank, the solver uses left directly.

5. FILE OPERATIONS
   - Selecting 'Load Problem from CSV File' launches your native file explorer.
   - Saving plots and configurations prompts a save window; no path typing needed.
"""
    print(manual_text)


# ==============================================================================
# 3. INTERACTIVE INPUT HELPERS
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
    """Displays numbered options and returns the selected key."""
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
    print("\n\nSTEP 1: BEAM GEOMETRY & SUPPORTS\n")
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
            print(f"\nSupport #{i+1}")
            stype_opts = {"1": "Pinned", "2": "Roller", "3": "Fixed"}
            stype_ch = get_choice("Support Type:", stype_opts)
            stype_map = {"1": "pinned", "2": "roller", "3": "fixed"}
            pos = get_position(length, f"Support #{i+1}")
            supports.append({'type': stype_map[stype_ch], 'pos': pos})
            
    return length, supports


def collect_point_loads(beam_length):
    point_loads = []
    print("\n\nCOLLECT POINT LOADS\n")
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
            angle_deg = get_float("Angle relative to horizontal axis (0 to 180 deg): ", min_val=0.1, max_val=179.9)
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
    udls = []
    print("\n\nCOLLECT UNIFORMLY DISTRIBUTED LOADS (UDL)\n")
    while input("Add a Uniformly Distributed Load (UDL)? (y/n): ").strip().lower() == 'y':
        w = get_float("Enter load intensity w (kN/m): ", min_val=0.01)
        start_x = get_position(beam_length, "UDL START position")
        end_x = get_position(beam_length, "UDL END position")
        if start_x > end_x:
            start_x, end_x = end_x, start_x
        udls.append({'intensity': w, 'start': start_x, 'end': end_x})
    return udls


def collect_uvls(beam_length):
    uvls = []
    print("\n\nCOLLECT UNIFORMLY VARYING LOADS (UVL)\n")
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
    point_moments = []
    print("\n\nCOLLECT CONCENTRATED MOMENTS\n")
    while input("Add a Concentrated Moment / Couple? (y/n): ").strip().lower() == 'y':
        mag = get_float("Enter moment magnitude (kNm): ", min_val=0.01)
        pos = get_position(beam_length, "Moment")
        m_opts = {"1": "Clockwise (+)", "2": "Counter-Clockwise (-)"}
        m_ch = get_choice("Direction:", m_opts)
        effective_m = mag if m_ch == "1" else -mag
        point_moments.append({'mag': effective_m, 'pos': pos})
    return point_moments


def review_and_verify(beam_length, supports, point_loads, udls, uvls, point_moments):
    """Allows user to inspect and add/modify loads before calculation."""
    while True:
        print("\n\nSTEP 6: REVIEW & VERIFY\n")
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
# 4. CSV IMPORT & EXPORT ENGINE (Robust Left/Right Handling)
# ==============================================================================

def resolve_position(left_str, right_str, beam_length, field_label="location"):
    """
    Resolves position whether left, right, or both are entered.
    - If left is entered, uses left.
    - If left is empty and right is entered, calculates: beam_length - right.
    """
    left_str = left_str.strip() if left_str else ""
    right_str = right_str.strip() if right_str else ""

    if left_str != "":
        return float(left_str)
    elif right_str != "":
        return beam_length - float(right_str)
    else:
        raise ValueError(f"Neither left nor right position was provided for {field_label}.")


def load_from_csv(filepath):
    """Loads problem from CSV file selected via file dialog."""
    if not filepath or not os.path.exists(filepath):
        raise FileNotFoundError("Selected CSV file could not be found.")

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
            elif first_cell.startswith("#"):
                continue

            if current_section == "[BEAM]":
                try:
                    length = float(first_cell)
                except ValueError:
                    continue

            elif current_section == "[SUPPORTS]":
                if first_cell.lower() in ['type', 'support_type']:
                    continue
                stype = first_cell.lower()
                left_str = row[1] if len(row) > 1 else ""
                right_str = row[2] if len(row) > 2 else ""
                pos = resolve_position(left_str, right_str, length, "support")
                supports.append({'type': stype, 'pos': pos})

            elif current_section == "[POINT_LOADS]":
                if first_cell.lower() in ['mag', 'magnitude', 'mag_kn']:
                    continue
                
                # Format: mag_kN, direction, pos_from_left_m, pos_from_right_m, angle_deg
                if len(row) >= 4 and row[1].strip().lower() in ['down', 'up', 'downward', 'upward', 'angled', '+', '-']:
                    mag = abs(float(first_cell))
                    direction = row[1].strip().lower()
                    left_str = row[2]
                    right_str = row[3] if len(row) > 3 else ""
                    pos = resolve_position(left_str, right_str, length, "point load")
                    angle_deg = float(row[4].strip()) if len(row) > 4 and row[4].strip() else 90.0
                else:
                    # Legacy 3-column fallback: mag, pos, angle
                    mag = abs(float(first_cell))
                    pos = float(row[1].strip())
                    angle_deg = float(row[2].strip()) if len(row) > 2 and row[2].strip() else 90.0
                    direction = 'down' if float(first_cell) >= 0 else 'up'

                angle_rad = math.radians(angle_deg)
                vert_load = mag * math.sin(angle_rad)
                if direction in ['up', 'upward', '-']:
                    vert_load = -vert_load
                axial_load = mag * math.cos(angle_rad)

                point_loads.append({
                    'mag': vert_load,
                    'pos': pos,
                    'orig_mag': mag,
                    'axial': axial_load,
                    'angle': angle_deg,
                    'direction': 'up' if vert_load < 0 else ('angled' if angle_deg != 90.0 else 'down')
                })

            elif current_section == "[UDLS]":
                if first_cell.lower() in ['intensity', 'w', 'intensity_kn_per_m']:
                    continue
                w = float(first_cell)
                left_s = row[1] if len(row) > 1 else ""
                left_e = row[2] if len(row) > 2 else ""
                right_s = row[3] if len(row) > 3 else ""
                right_e = row[4] if len(row) > 4 else ""

                start_x = resolve_position(left_s, right_s, length, "UDL start")
                end_x = resolve_position(left_e, right_e, length, "UDL end")
                if start_x > end_x:
                    start_x, end_x = end_x, start_x
                udls.append({'intensity': w, 'start': start_x, 'end': end_x})

            elif current_section == "[UVLS]":
                if first_cell.lower() in ['start_w', 'start_w_kn_per_m']:
                    continue
                w1 = float(first_cell)
                w2 = float(row[1].strip())
                left_s = row[2] if len(row) > 2 else ""
                left_e = row[3] if len(row) > 3 else ""
                right_s = row[4] if len(row) > 4 else ""
                right_e = row[5] if len(row) > 5 else ""

                start_x = resolve_position(left_s, right_s, length, "UVL start")
                end_x = resolve_position(left_e, right_e, length, "UVL end")
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
                    left_str = row[2]
                    right_str = row[3] if len(row) > 3 else ""
                    pos = resolve_position(left_str, right_str, length, "moment")
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


def save_to_csv(filepath, length, supports, point_loads, udls, uvls, point_moments):
    """Exports problem configuration to chosen CSV path."""
    with open(filepath, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)

        writer.writerow(["[BEAM]"])
        writer.writerow(["length_m"])
        writer.writerow([round(length, 3)])
        writer.writerow([])

        writer.writerow(["[SUPPORTS]"])
        writer.writerow(["type", "pos_from_left_m", "pos_from_right_m"])
        for s in supports:
            writer.writerow([s['type'], round(s['pos'], 3), round(length - s['pos'], 3)])
        writer.writerow([])

        writer.writerow(["[POINT_LOADS]"])
        writer.writerow(["mag_kN", "direction", "pos_from_left_m", "pos_from_right_m", "angle_deg"])
        for pl in point_loads:
            mag_val = round(pl.get('orig_mag', abs(pl['mag'])), 3)
            dir_str = pl.get('direction', 'down' if pl['mag'] >= 0 else 'up')
            writer.writerow([mag_val, dir_str, round(pl['pos'], 3), round(length - pl['pos'], 3), pl.get('angle', 90.0)])
        writer.writerow([])

        writer.writerow(["[UDLS]"])
        writer.writerow(["intensity_kN_per_m", "start_from_left_m", "end_from_left_m", "start_from_right_m", "end_from_right_m"])
        for u in udls:
            writer.writerow([round(u['intensity'], 3), round(u['start'], 3), round(u['end'], 3),
                             round(length - u['start'], 3), round(length - u['end'], 3)])
        writer.writerow([])

        writer.writerow(["[UVLS]"])
        writer.writerow(["start_w_kN_per_m", "end_w_kN_per_m", "start_from_left_m", "end_from_left_m", "start_from_right_m", "end_from_right_m"])
        for uv in uvls:
            writer.writerow([round(uv['start_w'], 3), round(uv['end_w'], 3), round(uv['start'], 3), round(uv['end'], 3),
                             round(length - uv['start'], 3), round(length - uv['end'], 3)])
        writer.writerow([])

        writer.writerow(["[MOMENTS]"])
        writer.writerow(["mag_kNm", "direction", "pos_from_left_m", "pos_from_right_m"])
        for pm in point_moments:
            dir_str = "clockwise" if pm['mag'] >= 0 else "counter-clockwise"
            writer.writerow([round(abs(pm['mag']), 3), dir_str, round(pm['pos'], 3), round(length - pm['pos'], 3)])


# ==============================================================================
# 5. EQUILIBRIUM SOLVER & VECTORIZED ENGINE
# ==============================================================================

def solve_reactions(length, supports, point_loads, udls, uvls, point_moments):
    """Computes support reactions with full 2D static equilibrium."""
    total_Fy = sum(pl['mag'] for pl in point_loads)
    total_Fx = sum(pl.get('axial', 0.0) for pl in point_loads)
    total_M_zero = sum(pl['mag'] * pl['pos'] for pl in point_loads)

    for udl in udls:
        span = udl['end'] - udl['start']
        force = udl['intensity'] * span
        centroid = udl['start'] + span / 2.0
        total_Fy += force
        total_M_zero += force * centroid

    for uvl in uvls:
        span = uvl['end'] - uvl['start']
        force = 0.5 * (uvl['start_w'] + uvl['end_w']) * span
        if (uvl['start_w'] + uvl['end_w']) > 0:
            rel_centroid = (span / 3.0) * ((uvl['start_w'] + 2 * uvl['end_w']) / (uvl['start_w'] + uvl['end_w']))
        else:
            rel_centroid = span / 2.0
        centroid = uvl['start'] + rel_centroid
        total_Fy += force
        total_M_zero += force * centroid

    for pm in point_moments:
        total_M_zero += pm['mag']

    fixed = [s for s in supports if s['type'] == 'fixed']
    pin_roller = [s for s in supports if s['type'] in ['pinned', 'roller']]

    reactions = {}
    if len(fixed) == 1 and len(pin_roller) == 0:
        x_s = fixed[0]['pos']
        R_y = total_Fy
        R_x = -total_Fx
        M_fixed = -(total_M_zero - total_Fy * x_s)
        reactions[f"R_{x_s:.2f}"] = R_y
        reactions[f"M_{x_s:.2f}"] = M_fixed
        if abs(R_x) > 1e-4:
            reactions[f"Rx_{x_s:.2f}"] = R_x
    elif len(pin_roller) == 2 and len(fixed) == 0:
        pin_roller.sort(key=lambda s: s['pos'])
        x1, x2 = pin_roller[0]['pos'], pin_roller[1]['pos']
        if abs(x2 - x1) < 1e-5:
            raise ValueError("Supports cannot be placed at the exact same location.")
        M_about_x1 = total_M_zero - total_Fy * x1
        R2 = M_about_x1 / (x2 - x1)
        R1 = total_Fy - R2
        reactions[f"R_{x1:.2f}"] = R1
        reactions[f"R_{x2:.2f}"] = R2
        
        pinned_supports = [s for s in pin_roller if s['type'] == 'pinned']
        if pinned_supports and abs(total_Fx) > 1e-4:
            x_pin = pinned_supports[0]['pos']
            reactions[f"Rx_{x_pin:.2f}"] = -total_Fx
    else:
        raise ValueError("System indeterminate. Provide exactly 1 Fixed or 2 Pinned/Roller supports.")

    return reactions


def build_piecewise_mesh(length, supports, point_loads, udls, uvls, point_moments, base_samples=2000):
    """Constructs mesh with dual boundary nodes (x-, x+) at discontinuities."""
    critical_pts = {0.0, length}
    for s in supports:
        critical_pts.add(s['pos'])
    for pl in point_loads:
        critical_pts.add(pl['pos'])
    for u in udls:
        critical_pts.add(u['start'])
        critical_pts.add(u['end'])
    for uv in uvls:
        critical_pts.add(uv['start'])
        critical_pts.add(uv['end'])
    for pm in point_moments:
        critical_pts.add(pm['pos'])

    eps = 1e-8
    mesh_points = []
    base_x = np.linspace(0.0, length, base_samples)
    mesh_points.extend(base_x)

    for cp in critical_pts:
        if 0.0 < cp < length:
            mesh_points.extend([cp - eps, cp, cp + eps])
        elif cp == 0.0:
            mesh_points.extend([0.0, eps])
        elif cp == length:
            mesh_points.extend([length - eps, length])

    return np.unique(np.array(mesh_points))


def calculate_sfd_bmd(length, supports, point_loads, udls, uvls, point_moments):
    """Evaluates SFD and BMD using vectorized operations."""
    reactions = solve_reactions(length, supports, point_loads, udls, uvls, point_moments)
    x = build_piecewise_mesh(length, supports, point_loads, udls, uvls, point_moments)
    
    V = np.zeros_like(x)
    M = np.zeros_like(x)

    # Reactions
    for name, val in reactions.items():
        if name.startswith("R_"):
            x_r = float(name.split("_")[1])
            mask = x >= x_r
            V[mask] += val
            M[mask] += val * (x[mask] - x_r)
        elif name.startswith("M_"):
            x_r = float(name.split("_")[1])
            mask = x >= x_r
            M[mask] += val

    # Point Loads
    for pl in point_loads:
        mask = x >= pl['pos']
        V[mask] -= pl['mag']
        M[mask] -= pl['mag'] * (x[mask] - pl['pos'])

    # UDLs
    for udl in udls:
        a = udl['start']
        b = udl['end']
        w = udl['intensity']
        dx = np.clip(x - a, 0.0, b - a)
        V -= w * dx
        M -= w * ((x - a) * dx - 0.5 * (dx ** 2))

    # UVLs
    for uvl in uvls:
        a = uvl['start']
        b = uvl['end']
        w1 = uvl['start_w']
        w2 = uvl['end_w']
        L_span = b - a
        k = (w2 - w1) / L_span
        dx = np.clip(x - a, 0.0, L_span)
        F_dx = w1 * dx + 0.5 * k * (dx ** 2)
        V -= F_dx
        M -= (x - a) * F_dx - (0.5 * w1 * (dx ** 2) + (1.0 / 3.0) * k * (dx ** 3))

    # Point Moments
    for pm in point_moments:
        mask = x >= pm['pos']
        M[mask] -= pm['mag']

    return x, V, M, reactions


def find_critical_points(x, V, M):
    """Finds zero shear crossings, peak moment, and points of contraflexure."""
    zero_shear_points = []
    for i in range(len(V) - 1):
        if V[i] == 0.0 or (V[i] * V[i+1] < 0):
            if abs(x[i+1] - x[i]) < 1e-6:
                x_zero = x[i]
                m_at_zero = float(M[i])
            else:
                x_zero = x[i] - V[i] * (x[i+1] - x[i]) / (V[i+1] - V[i])
                m_at_zero = float(np.interp(x_zero, x, M))
                
            if not any(abs(x_zero - p[0]) < 1e-3 for p in zero_shear_points):
                zero_shear_points.append((x_zero, m_at_zero))

    contraflexure_points = []
    for i in range(len(M) - 1):
        if M[i] * M[i+1] < 0:
            if abs(x[i+1] - x[i]) < 1e-6:
                x_cf = x[i]
            else:
                x_cf = x[i] - M[i] * (x[i+1] - x[i]) / (M[i+1] - M[i])
            if not any(abs(x_cf - p) < 1e-3 for p in contraflexure_points):
                contraflexure_points.append(x_cf)

    max_m_idx = np.argmax(np.abs(M))
    return zero_shear_points, M[max_m_idx], x[max_m_idx], contraflexure_points


# ==============================================================================
# 6. VISUALIZATION ENGINE
# ==============================================================================

def create_figure(length, x, V, M, supports, point_loads, udls, uvls, point_moments, reactions, zero_points, max_m_val, max_m_pos, contraflexure):
    fig, (ax0, ax1, ax2) = plt.subplots(3, 1, figsize=(12, 11), sharex=True)
    fig.suptitle('Shon Parale | Vedant Patel\nMechanics Analysis Engine: Free Body Diagram, SFD & BMD', fontsize=13, fontweight='bold')

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
        label = f"{pl.get('orig_mag', abs(mag)):.2f} kN"
        angle = pl.get('angle', 90.0)
        
        if angle != 90.0:
            label += f" @ {angle:.0f}°"
            rad = math.radians(angle)
            dx = 0.6 * math.cos(rad)
            dy = 1.0 * math.sin(rad)
            ax0.annotate(label, xy=(pos, 0.05), xytext=(pos - dx, dy + 0.3),
                         arrowprops=dict(facecolor='blue', edgecolor='blue', shrink=0.05, width=2, headwidth=6),
                         ha='center', fontweight='bold', color='blue', fontsize=9)
        else:
            if mag >= 0:
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
        elif name.startswith("Rx_"):
            dx = 0.5 if val >= 0 else -0.5
            ax0.annotate(f"{name} = {val:.2f} kN", xy=(pos, 0.0), xytext=(pos - dx, 0.0),
                         arrowprops=dict(facecolor='darkred', edgecolor='darkred', shrink=0.05, width=2, headwidth=6),
                         ha='center', fontweight='bold', color='darkred', fontsize=8)
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
# 7. MAIN PROGRAM PIPELINE
# ==============================================================================

def main():
    while True:
        print("\n\nBEAM MECHANICS SOLVER: SFD & BMD ENGINE")
        print("Shon Parale | Vedant Patel\n")
        
        main_opts = {
            "1": "Start New Problem (Interactive Step-by-Step)",
            "2": "Load Problem from CSV File (Opens File Explorer)",
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
            
            beam_length, supports, point_loads, udls, uvls, point_moments = review_and_verify(
                beam_length, supports, point_loads, udls, uvls, point_moments
            )

        elif choice == "2":
            print("\nOpening file explorer to select CSV...")
            csv_path = open_csv_dialog()
            if not csv_path:
                print("   [!] File selection cancelled.")
                continue
            try:
                beam_length, supports, point_loads, udls, uvls, point_moments = load_from_csv(csv_path)
                print(f"   [+] Successfully loaded: {os.path.basename(csv_path)}")
            except Exception as e:
                print(f"   [!] Failed to load CSV file: {e}")
                continue

        print("\nSolving equilibrium equations with vectorized engine...")
        try:
            x, V, M, reactions = calculate_sfd_bmd(beam_length, supports, point_loads, udls, uvls, point_moments)
            zero_points, max_m_val, max_m_pos, contraflexure = find_critical_points(x, V, M)
        except Exception as err:
            print(f"   [!] Calculation Error: {err}")
            continue

        print("\n\nCALCULATION SUMMARY\n")
        print("SUPPORT REACTIONS")
        for r_name, r_val in reactions.items():
            print(f"   {r_name}: {r_val:.3f}")

        print("\nZERO SHEAR & PEAK BENDING MOMENT")
        for x_z, m_z in zero_points:
            print(f"   V = 0 at x = {x_z:.3f} m (from right: {beam_length - x_z:.3f} m) --> M = {m_z:.3f} kNm")
        print(f"   Global Peak Moment: {max_m_val:.3f} kNm at x = {max_m_pos:.3f} m")

        if contraflexure:
            print("\nPOINTS OF CONTRAFLEXURE (M = 0)")
            for x_cf in contraflexure:
                print(f"   Contraflexure at x = {x_cf:.3f} m")

        fig = create_figure(beam_length, x, V, M, supports, point_loads, udls, uvls, point_moments, reactions, zero_points, max_m_val, max_m_pos, contraflexure)

        print("\n\nEXPORT OPTIONS\n")

        if input("Save analysis figure? (y/n): ").strip().lower() == 'y':
            print("Opening file explorer to choose figure save location...")
            save_img_path = save_image_dialog()
            if save_img_path:
                try:
                    fig.savefig(save_img_path, dpi=300, bbox_inches='tight')
                    print(f"   [+] Figure saved successfully to: {save_img_path}")
                except Exception as e:
                    print(f"   [!] Error saving figure: {e}")
            else:
                print("   [!] Figure export cancelled.")

        if input("\nSave problem configuration as CSV? (y/n): ").strip().lower() == 'y':
            print("Opening file explorer to choose CSV save location...")
            save_c_path = save_csv_dialog()
            if save_c_path:
                try:
                    save_to_csv(save_c_path, beam_length, supports, point_loads, udls, uvls, point_moments)
                    print(f"   [+] Configuration saved successfully to: {save_c_path}")
                except Exception as e:
                    print(f"   [!] Error saving CSV: {e}")
            else:
                print("   [!] CSV export cancelled.")

        print("\nDisplaying interactive plot window (close window to return to menu)...")
        plt.show()
        plt.close(fig)


if __name__ == "__main__":
    main()