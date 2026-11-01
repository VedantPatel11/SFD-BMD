# Shon Parale | Vedant Patel
# SFD & BMD Mechanics Analysis Engine v6.0 (GUI)

import os
import csv
import math
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import matplotlib.patches as patches

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else os.getcwd()

# ==============================================================================
# 1. CORE NUMERICAL SOLVER & PIECEWISE MESH ENGINE
# ==============================================================================

def resolve_pos(left_val, right_val, beam_length):
    """Resolves position from left or right input."""
    if left_val is not None:
        return float(left_val)
    elif right_val is not None:
        return beam_length - float(right_val)
    raise ValueError("Neither left nor right position was provided.")


def solve_reactions(length, supports, point_loads, udls, uvls, point_moments):
    """Calculates support reactions using static equilibrium (Fy, Fx, M)."""
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
            raise ValueError("Supports cannot be at the exact same location.")
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
        raise ValueError(
            "System is statically indeterminate or under-constrained.\n"
            "Provide exactly 1 Fixed support OR 2 Pinned/Roller supports."
        )

    return reactions


def build_piecewise_mesh(length, supports, point_loads, udls, uvls, point_moments, base_samples=2500):
    """Builds a mesh with dual boundary nodes to capture true step jumps."""
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
    mesh_points = list(np.linspace(0.0, length, base_samples))
    for cp in critical_pts:
        if 0.0 < cp < length:
            mesh_points.extend([cp - eps, cp, cp + eps])
        elif cp == 0.0:
            mesh_points.extend([0.0, eps])
        elif cp == length:
            mesh_points.extend([length - eps, length])

    return np.unique(np.array(mesh_points))


def calculate_sfd_bmd(length, supports, point_loads, udls, uvls, point_moments):
    """Vectorized calculation of shear force and bending moment."""
    reactions = solve_reactions(length, supports, point_loads, udls, uvls, point_moments)
    x = build_piecewise_mesh(length, supports, point_loads, udls, uvls, point_moments)
    
    V = np.zeros_like(x)
    M = np.zeros_like(x)

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

    for pl in point_loads:
        mask = x >= pl['pos']
        V[mask] -= pl['mag']
        M[mask] -= pl['mag'] * (x[mask] - pl['pos'])

    for udl in udls:
        a, b, w = udl['start'], udl['end'], udl['intensity']
        dx = np.clip(x - a, 0.0, b - a)
        V -= w * dx
        M -= w * ((x - a) * dx - 0.5 * (dx ** 2))

    for uvl in uvls:
        a, b = uvl['start'], uvl['end']
        w1, w2 = uvl['start_w'], uvl['end_w']
        L_span = b - a
        k = (w2 - w1) / L_span
        dx = np.clip(x - a, 0.0, L_span)
        F_dx = w1 * dx + 0.5 * k * (dx ** 2)
        V -= F_dx
        M -= (x - a) * F_dx - (0.5 * w1 * (dx ** 2) + (1.0 / 3.0) * k * (dx ** 3))

    for pm in point_moments:
        mask = x >= pm['pos']
        M[mask] -= pm['mag']

    return x, V, M, reactions


def find_critical_points(x, V, M):
    """Finds exact zero-shear coordinates, peak moment, and contraflexure points."""
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
# 2. CSV PERSISTENCE MODULE
# ==============================================================================

def load_csv_data(filepath):
    length = None
    supports, point_loads, udls, uvls, point_moments = [], [], [], [], []
    current_section = None

    with open(filepath, mode='r', encoding='utf-8') as f:
        reader = csv.reader(f)
        for row in reader:
            if not row or not any(c.strip() for c in row):
                continue
            first = row[0].strip()
            if first.startswith("[") and first.endswith("]"):
                current_section = first.upper()
                continue
            if first.startswith("#"):
                continue

            if current_section == "[BEAM]":
                try:
                    length = float(first)
                except ValueError:
                    pass
            elif current_section == "[SUPPORTS]":
                if first.lower() in ['type', 'support_type']:
                    continue
                stype = first.lower()
                l_str = row[1].strip() if len(row) > 1 and row[1].strip() else None
                r_str = row[2].strip() if len(row) > 2 and row[2].strip() else None
                pos = resolve_pos(l_str, r_str, length)
                supports.append({'type': stype, 'pos': pos})
            elif current_section == "[POINT_LOADS]":
                if first.lower() in ['mag', 'mag_kn']:
                    continue
                if len(row) >= 4 and row[1].strip().lower() in ['down', 'up', 'downward', 'upward', 'angled', '+', '-']:
                    mag = abs(float(first))
                    direction = row[1].strip().lower()
                    l_str = row[2].strip() if row[2].strip() else None
                    r_str = row[3].strip() if len(row) > 3 and row[3].strip() else None
                    pos = resolve_pos(l_str, r_str, length)
                    angle = float(row[4].strip()) if len(row) > 4 and row[4].strip() else 90.0
                else:
                    mag = abs(float(first))
                    pos = float(row[1].strip())
                    angle = float(row[2].strip()) if len(row) > 2 and row[2].strip() else 90.0
                    direction = 'down' if float(first) >= 0 else 'up'

                rad = math.radians(angle)
                vert_load = mag * math.sin(rad)
                if direction in ['up', 'upward', '-']:
                    vert_load = -vert_load
                axial = mag * math.cos(rad)

                point_loads.append({
                    'mag': vert_load, 'pos': pos, 'orig_mag': mag,
                    'axial': axial, 'angle': angle,
                    'direction': 'up' if vert_load < 0 else ('angled' if angle != 90.0 else 'down')
                })
            elif current_section == "[UDLS]":
                if first.lower() in ['intensity', 'w', 'intensity_kn_per_m']:
                    continue
                w = float(first)
                s_l = row[1].strip() if len(row) > 1 and row[1].strip() else None
                e_l = row[2].strip() if len(row) > 2 and row[2].strip() else None
                s_r = row[3].strip() if len(row) > 3 and row[3].strip() else None
                e_r = row[4].strip() if len(row) > 4 and row[4].strip() else None
                start_x = resolve_pos(s_l, s_r, length)
                end_x = resolve_pos(e_l, e_r, length)
                if start_x > end_x:
                    start_x, end_x = end_x, start_x
                udls.append({'intensity': w, 'start': start_x, 'end': end_x})
            elif current_section == "[UVLS]":
                if first.lower() in ['start_w', 'start_w_kn_per_m']:
                    continue
                w1, w2 = float(first), float(row[1].strip())
                s_l = row[2].strip() if len(row) > 2 and row[2].strip() else None
                e_l = row[3].strip() if len(row) > 3 and row[3].strip() else None
                s_r = row[4].strip() if len(row) > 4 and row[4].strip() else None
                e_r = row[5].strip() if len(row) > 5 and row[5].strip() else None
                start_x = resolve_pos(s_l, s_r, length)
                end_x = resolve_pos(e_l, e_r, length)
                if start_x > end_x:
                    start_x, end_x = end_x, start_x
                    w1, w2 = w2, w1
                uvls.append({'start_w': w1, 'end_w': w2, 'start': start_x, 'end': end_x})
            elif current_section == "[MOMENTS]":
                if first.lower() in ['mag', 'mag_knm']:
                    continue
                if len(row) >= 3 and row[1].strip().lower() in ['clockwise', 'counter-clockwise', 'cw', 'ccw', '+', '-']:
                    mag = abs(float(first))
                    direction = row[1].strip().lower()
                    l_str = row[2].strip() if row[2].strip() else None
                    r_str = row[3].strip() if len(row) > 3 and row[3].strip() else None
                    pos = resolve_pos(l_str, r_str, length)
                    eff_m = mag if direction in ['clockwise', 'cw', '+'] else -mag
                else:
                    eff_m = float(first)
                    pos = float(row[1].strip())
                point_moments.append({'mag': eff_m, 'pos': pos})

    if length is None:
        raise ValueError("Missing beam length in CSV.")
    return length, supports, point_loads, udls, uvls, point_moments


def write_csv_data(filepath, length, supports, point_loads, udls, uvls, point_moments):
    with open(filepath, mode='w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(["[BEAM]"])
        w.writerow(["length_m"])
        w.writerow([round(length, 3)])
        w.writerow([])

        w.writerow(["[SUPPORTS]"])
        w.writerow(["type", "pos_from_left_m", "pos_from_right_m"])
        for s in supports:
            w.writerow([s['type'], round(s['pos'], 3), round(length - s['pos'], 3)])
        w.writerow([])

        w.writerow(["[POINT_LOADS]"])
        w.writerow(["mag_kN", "direction", "pos_from_left_m", "pos_from_right_m", "angle_deg"])
        for pl in point_loads:
            orig = round(pl.get('orig_mag', abs(pl['mag'])), 3)
            d = pl.get('direction', 'down' if pl['mag'] >= 0 else 'up')
            w.writerow([orig, d, round(pl['pos'], 3), round(length - pl['pos'], 3), pl.get('angle', 90.0)])
        w.writerow([])

        w.writerow(["[UDLS]"])
        w.writerow(["intensity_kN_per_m", "start_from_left_m", "end_from_left_m", "start_from_right_m", "end_from_right_m"])
        for u in udls:
            w.writerow([round(u['intensity'], 3), round(u['start'], 3), round(u['end'], 3),
                        round(length - u['start'], 3), round(length - u['end'], 3)])
        w.writerow([])

        w.writerow(["[UVLS]"])
        w.writerow(["start_w_kN_per_m", "end_w_kN_per_m", "start_from_left_m", "end_from_left_m", "start_from_right_m", "end_from_right_m"])
        for uv in uvls:
            w.writerow([round(uv['start_w'], 3), round(uv['end_w'], 3), round(uv['start'], 3), round(uv['end'], 3),
                        round(length - uv['start'], 3), round(length - uv['end'], 3)])
        w.writerow([])

        w.writerow(["[MOMENTS]"])
        w.writerow(["mag_kNm", "direction", "pos_from_left_m", "pos_from_right_m"])
        for pm in point_moments:
            d = "clockwise" if pm['mag'] >= 0 else "counter-clockwise"
            w.writerow([round(abs(pm['mag']), 3), d, round(pm['pos'], 3), round(length - pm['pos'], 3)])


# ==============================================================================
# 3. GRAPHICAL USER INTERFACE (LIGHTWEIGHT TKINTER + MATPLOTLIB)
# ==============================================================================

class BeamApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Beam Mechanics Engine - Shon Parale | Vedant Patel")
        self.root.geometry("1300x820")
        self.root.minsize(1050, 700)

        # Style configuration
        self.style = ttk.Style()
        self.style.theme_use('clam')

        # Left / Right Layout Split
        self.main_pane = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        self.main_pane.pack(fill=tk.BOTH, expand=True)

        self.left_frame = ttk.Frame(self.main_pane, padding=8)
        self.right_frame = ttk.Frame(self.main_pane, padding=4)
        self.main_pane.add(self.left_frame, weight=0)
        self.main_pane.add(self.right_frame, weight=1)

        self.build_left_deck()
        self.build_right_canvas()

        # Load default demonstration structure
        self.populate_default_problem()
        self.compute_and_draw()

    # ------------------ LEFT DECK CONSTRUCTION ------------------
    def build_left_deck(self):
        # Header
        hdr = ttk.Label(self.left_frame, text="Shon Parale | Vedant Patel", font=('Helvetica', 12, 'bold'))
        hdr.pack(anchor=tk.W, pady=(0, 2))
        sub = ttk.Label(self.left_frame, text="Beam Analysis Engine (SFD & BMD)", font=('Helvetica', 9))
        sub.pack(anchor=tk.W, pady=(0, 6))

        # Command Buttons Row
        btn_bar = ttk.Frame(self.left_frame)
        btn_bar.pack(fill=tk.X, pady=4)
        ttk.Button(btn_bar, text="Load CSV", command=self.load_csv).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_bar, text="Save CSV", command=self.save_csv).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_bar, text="Export Plot", command=self.export_image).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_bar, text="Manual", command=self.show_manual).pack(side=tk.LEFT, padx=2)

        # Beam Length Frame
        geom_frame = ttk.LabelFrame(self.left_frame, text=" Beam Geometry ", padding=6)
        geom_frame.pack(fill=tk.X, pady=6)
        ttk.Label(geom_frame, text="Total Length L (m):").pack(side=tk.LEFT, padx=4)
        self.length_var = tk.StringVar(value="6.0")
        ttk.Entry(geom_frame, textvariable=self.length_var, width=10).pack(side=tk.LEFT, padx=4)

        # Tabbed Input System for Boundary Conditions & Loads
        self.notebook = ttk.Notebook(self.left_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=4)

        self.build_supports_tab()
        self.build_point_loads_tab()
        self.build_udls_tab()
        self.build_uvls_tab()
        self.build_moments_tab()

        # Compute Action Button
        self.calc_btn = tk.Button(
            self.left_frame, text="COMPUTE & PLOT", bg="#1976D2", fg="white",
            font=('Helvetica', 11, 'bold'), relief=tk.RAISED, pady=6, command=self.compute_and_draw
        )
        self.calc_btn.pack(fill=tk.X, pady=6)

        # Results Text Display Box
        res_frame = ttk.LabelFrame(self.left_frame, text=" Calculation Summary ", padding=4)
        res_frame.pack(fill=tk.BOTH, expand=True, pady=4)

        self.res_text = tk.Text(res_frame, height=9, font=('Consolas', 9), wrap=tk.WORD)
        self.res_text.pack(fill=tk.BOTH, expand=True)

    def build_supports_tab(self):
        tab = ttk.Frame(self.notebook, padding=6)
        self.notebook.add(tab, text="Supports")

        in_f = ttk.Frame(tab)
        in_f.pack(fill=tk.X, pady=2)
        ttk.Label(in_f, text="Type:").grid(row=0, column=0, sticky=tk.W)
        self.sup_type_var = tk.StringVar(value="pinned")
        ttk.Combobox(in_f, textvariable=self.sup_type_var, values=["pinned", "roller", "fixed"], width=8, state="readonly").grid(row=0, column=1, padx=2)

        ttk.Label(in_f, text="From Left (m):").grid(row=0, column=2, sticky=tk.W)
        self.sup_pos_var = tk.StringVar(value="0.0")
        ttk.Entry(in_f, textvariable=self.sup_pos_var, width=7).grid(row=0, column=3, padx=2)

        btn_f = ttk.Frame(tab)
        btn_f.pack(fill=tk.X, pady=4)
        ttk.Button(btn_f, text="Add Support", command=self.add_support).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_f, text="Delete Selected", command=lambda: self.del_item(self.tree_sup)).pack(side=tk.LEFT, padx=2)

        self.tree_sup = ttk.Treeview(tab, columns=("Type", "Pos"), show='headings', height=4)
        self.tree_sup.heading("Type", text="Type")
        self.tree_sup.heading("Pos", text="Position (m)")
        self.tree_sup.column("Type", width=100)
        self.tree_sup.column("Pos", width=120)
        self.tree_sup.pack(fill=tk.BOTH, expand=True)

    def build_point_loads_tab(self):
        tab = ttk.Frame(self.notebook, padding=6)
        self.notebook.add(tab, text="Point Loads")

        in_f = ttk.Frame(tab)
        in_f.pack(fill=tk.X, pady=2)
        ttk.Label(in_f, text="Mag (kN):").grid(row=0, column=0)
        self.pl_mag_var = tk.StringVar(value="4.0")
        ttk.Entry(in_f, textvariable=self.pl_mag_var, width=6).grid(row=0, column=1, padx=2)

        ttk.Label(in_f, text="Dir:").grid(row=0, column=2)
        self.pl_dir_var = tk.StringVar(value="down")
        ttk.Combobox(in_f, textvariable=self.pl_dir_var, values=["down", "up"], width=6, state="readonly").grid(row=0, column=3, padx=2)

        ttk.Label(in_f, text="Pos (m):").grid(row=1, column=0, pady=2)
        self.pl_pos_var = tk.StringVar(value="2.0")
        ttk.Entry(in_f, textvariable=self.pl_pos_var, width=6).grid(row=1, column=1, padx=2)

        ttk.Label(in_f, text="Angle (°):").grid(row=1, column=2, pady=2)
        self.pl_ang_var = tk.StringVar(value="90.0")
        ttk.Entry(in_f, textvariable=self.pl_ang_var, width=6).grid(row=1, column=3, padx=2)

        btn_f = ttk.Frame(tab)
        btn_f.pack(fill=tk.X, pady=4)
        ttk.Button(btn_f, text="Add Point Load", command=self.add_point_load).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_f, text="Delete Selected", command=lambda: self.del_item(self.tree_pl)).pack(side=tk.LEFT, padx=2)

        self.tree_pl = ttk.Treeview(tab, columns=("Mag", "Dir", "Pos", "Angle"), show='headings', height=4)
        for col in ("Mag", "Dir", "Pos", "Angle"):
            self.tree_pl.heading(col, text=col)
            self.tree_pl.column(col, width=65)
        self.tree_pl.pack(fill=tk.BOTH, expand=True)

    def build_udls_tab(self):
        tab = ttk.Frame(self.notebook, padding=6)
        self.notebook.add(tab, text="UDL")

        in_f = ttk.Frame(tab)
        in_f.pack(fill=tk.X, pady=2)
        ttk.Label(in_f, text="w (kN/m):").grid(row=0, column=0)
        self.udl_w_var = tk.StringVar(value="2.0")
        ttk.Entry(in_f, textvariable=self.udl_w_var, width=6).grid(row=0, column=1, padx=2)

        ttk.Label(in_f, text="Start (m):").grid(row=0, column=2)
        self.udl_s_var = tk.StringVar(value="2.0")
        ttk.Entry(in_f, textvariable=self.udl_s_var, width=6).grid(row=0, column=3, padx=2)

        ttk.Label(in_f, text="End (m):").grid(row=0, column=4)
        self.udl_e_var = tk.StringVar(value="4.0")
        ttk.Entry(in_f, textvariable=self.udl_e_var, width=6).grid(row=0, column=5, padx=2)

        btn_f = ttk.Frame(tab)
        btn_f.pack(fill=tk.X, pady=4)
        ttk.Button(btn_f, text="Add UDL", command=self.add_udl).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_f, text="Delete Selected", command=lambda: self.del_item(self.tree_udl)).pack(side=tk.LEFT, padx=2)

        self.tree_udl = ttk.Treeview(tab, columns=("w", "Start", "End"), show='headings', height=4)
        for col in ("w", "Start", "End"):
            self.tree_udl.heading(col, text=col)
            self.tree_udl.column(col, width=80)
        self.tree_udl.pack(fill=tk.BOTH, expand=True)

    def build_uvls_tab(self):
        tab = ttk.Frame(self.notebook, padding=6)
        self.notebook.add(tab, text="UVL")

        in_f = ttk.Frame(tab)
        in_f.pack(fill=tk.X, pady=2)
        ttk.Label(in_f, text="w1:").grid(row=0, column=0)
        self.uvl_w1_var = tk.StringVar(value="0.0")
        ttk.Entry(in_f, textvariable=self.uvl_w1_var, width=5).grid(row=0, column=1, padx=1)

        ttk.Label(in_f, text="w2:").grid(row=0, column=2)
        self.uvl_w2_var = tk.StringVar(value="5.0")
        ttk.Entry(in_f, textvariable=self.uvl_w2_var, width=5).grid(row=0, column=3, padx=1)

        ttk.Label(in_f, text="Start:").grid(row=0, column=4)
        self.uvl_s_var = tk.StringVar(value="4.0")
        ttk.Entry(in_f, textvariable=self.uvl_s_var, width=5).grid(row=0, column=5, padx=1)

        ttk.Label(in_f, text="End:").grid(row=0, column=6)
        self.uvl_e_var = tk.StringVar(value="6.0")
        ttk.Entry(in_f, textvariable=self.uvl_e_var, width=5).grid(row=0, column=7, padx=1)

        btn_f = ttk.Frame(tab)
        btn_f.pack(fill=tk.X, pady=4)
        ttk.Button(btn_f, text="Add UVL", command=self.add_uvl).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_f, text="Delete Selected", command=lambda: self.del_item(self.tree_uvl)).pack(side=tk.LEFT, padx=2)

        self.tree_uvl = ttk.Treeview(tab, columns=("w1", "w2", "Start", "End"), show='headings', height=4)
        for col in ("w1", "w2", "Start", "End"):
            self.tree_uvl.heading(col, text=col)
            self.tree_uvl.column(col, width=65)
        self.tree_uvl.pack(fill=tk.BOTH, expand=True)

    def build_moments_tab(self):
        tab = ttk.Frame(self.notebook, padding=6)
        self.notebook.add(tab, text="Moments")

        in_f = ttk.Frame(tab)
        in_f.pack(fill=tk.X, pady=2)
        ttk.Label(in_f, text="Mag (kNm):").grid(row=0, column=0)
        self.m_mag_var = tk.StringVar(value="5.0")
        ttk.Entry(in_f, textvariable=self.m_mag_var, width=6).grid(row=0, column=1, padx=2)

        ttk.Label(in_f, text="Dir:").grid(row=0, column=2)
        self.m_dir_var = tk.StringVar(value="clockwise")
        ttk.Combobox(in_f, textvariable=self.m_dir_var, values=["clockwise", "counter-clockwise"], width=14, state="readonly").grid(row=0, column=3, padx=2)

        ttk.Label(in_f, text="Pos (m):").grid(row=1, column=0, pady=2)
        self.m_pos_var = tk.StringVar(value="3.0")
        ttk.Entry(in_f, textvariable=self.m_pos_var, width=6).grid(row=1, column=1, padx=2)

        btn_f = ttk.Frame(tab)
        btn_f.pack(fill=tk.X, pady=4)
        ttk.Button(btn_f, text="Add Moment", command=self.add_moment).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_f, text="Delete Selected", command=lambda: self.del_item(self.tree_m)).pack(side=tk.LEFT, padx=2)

        self.tree_m = ttk.Treeview(tab, columns=("Mag", "Dir", "Pos"), show='headings', height=4)
        for col in ("Mag", "Dir", "Pos"):
            self.tree_m.heading(col, text=col)
            self.tree_m.column(col, width=80)
        self.tree_m.pack(fill=tk.BOTH, expand=True)

    # ------------------ RIGHT CANVAS CONSTRUCTION ------------------
    def build_right_canvas(self):
        self.fig, (self.ax0, self.ax1, self.ax2) = plt.subplots(3, 1, figsize=(8, 9), sharex=True)
        self.fig.subplots_adjust(left=0.1, right=0.96, top=0.94, bottom=0.06, hspace=0.35)

        self.canvas = FigureCanvasTkAgg(self.fig, master=self.right_frame)
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.pack(fill=tk.BOTH, expand=True)

        self.toolbar = NavigationToolbar2Tk(self.canvas, self.right_frame)
        self.toolbar.update()

    # ------------------ DATA EDITING OPERATIONS ------------------
    def add_support(self):
        st = self.sup_type_var.get()
        try:
            pos = float(self.sup_pos_var.get())
            self.tree_sup.insert('', tk.END, values=(st, pos))
        except ValueError:
            messagebox.showerror("Input Error", "Support position must be a numerical value.")

    def add_point_load(self):
        try:
            mag = float(self.pl_mag_var.get())
            d = self.pl_dir_var.get()
            pos = float(self.pl_pos_var.get())
            ang = float(self.pl_ang_var.get())
            self.tree_pl.insert('', tk.END, values=(mag, d, pos, ang))
        except ValueError:
            messagebox.showerror("Input Error", "Point load inputs must be numbers.")

    def add_udl(self):
        try:
            w = float(self.udl_w_var.get())
            s = float(self.udl_s_var.get())
            e = float(self.udl_e_var.get())
            self.tree_udl.insert('', tk.END, values=(w, min(s, e), max(s, e)))
        except ValueError:
            messagebox.showerror("Input Error", "UDL inputs must be numbers.")

    def add_uvl(self):
        try:
            w1 = float(self.uvl_w1_var.get())
            w2 = float(self.uvl_w2_var.get())
            s = float(self.uvl_s_var.get())
            e = float(self.uvl_e_var.get())
            self.tree_uvl.insert('', tk.END, values=(w1, w2, min(s, e), max(s, e)))
        except ValueError:
            messagebox.showerror("Input Error", "UVL inputs must be numbers.")

    def add_moment(self):
        try:
            mag = float(self.m_mag_var.get())
            d = self.m_dir_var.get()
            pos = float(self.m_pos_var.get())
            self.tree_m.insert('', tk.END, values=(mag, d, pos))
        except ValueError:
            messagebox.showerror("Input Error", "Moment inputs must be numbers.")

    def del_item(self, tree):
        selected = tree.selection()
        for item in selected:
            tree.delete(item)

    def populate_default_problem(self):
        """Pre-populates an initial Simply Supported beam."""
        self.tree_sup.insert('', tk.END, values=("pinned", 0.0))
        self.tree_sup.insert('', tk.END, values=("roller", 6.0))
        self.tree_pl.insert('', tk.END, values=(3.5, "up", 0.0, 90.0))
        self.tree_pl.insert('', tk.END, values=(1.0, "down", 1.0, 90.0))
        self.tree_pl.insert('', tk.END, values=(4.0, "down", 5.0, 90.0))
        self.tree_pl.insert('', tk.END, values=(5.5, "up", 6.0, 90.0))
        self.tree_udl.insert('', tk.END, values=(2.0, 2.0, 4.0))

    # ------------------ EXTRACTORS ------------------
    def get_problem_data(self):
        length = float(self.length_var.get())
        if length <= 0:
            raise ValueError("Beam length must be greater than zero.")

        supports = []
        for item in self.tree_sup.get_children():
            row = self.tree_sup.item(item)['values']
            supports.append({'type': str(row[0]).lower(), 'pos': float(row[1])})

        point_loads = []
        for item in self.tree_pl.get_children():
            row = self.tree_pl.item(item)['values']
            mag = float(row[0])
            direction = str(row[1]).lower()
            pos = float(row[2])
            angle = float(row[3]) if len(row) > 3 else 90.0
            rad = math.radians(angle)
            v = mag * math.sin(rad)
            if direction in ['up', '-']:
                v = -v
            point_loads.append({
                'mag': v, 'pos': pos, 'orig_mag': mag,
                'axial': mag * math.cos(rad), 'angle': angle,
                'direction': 'up' if v < 0 else ('angled' if angle != 90.0 else 'down')
            })

        udls = []
        for item in self.tree_udl.get_children():
            row = self.tree_udl.item(item)['values']
            udls.append({'intensity': float(row[0]), 'start': float(row[1]), 'end': float(row[2])})

        uvls = []
        for item in self.tree_uvl.get_children():
            row = self.tree_uvl.item(item)['values']
            uvls.append({'start_w': float(row[0]), 'end_w': float(row[1]), 'start': float(row[2]), 'end': float(row[3])})

        point_moments = []
        for item in self.tree_m.get_children():
            row = self.tree_m.item(item)['values']
            mag = float(row[0])
            eff = mag if str(row[1]).lower() in ['clockwise', 'cw', '+'] else -mag
            point_moments.append({'mag': eff, 'pos': float(row[2])})

        return length, supports, point_loads, udls, uvls, point_moments

    # ------------------ SOLVER & DRAW EXECUTION ------------------
    def compute_and_draw(self):
        try:
            length, supports, point_loads, udls, uvls, point_moments = self.get_problem_data()
            x, V, M, reactions = calculate_sfd_bmd(length, supports, point_loads, udls, uvls, point_moments)
            zero_points, max_m_val, max_m_pos, contraflexure = find_critical_points(x, V, M)
        except Exception as e:
            messagebox.showerror("Computation Error", str(e))
            return

        # Update Text Summary
        self.res_text.delete('1.0', tk.END)
        self.res_text.insert(tk.END, "SUPPORT REACTIONS:\n")
        for r_name, r_val in reactions.items():
            self.res_text.insert(tk.END, f"  {r_name}: {r_val:.3f}\n")

        self.res_text.insert(tk.END, "\nZERO SHEAR CROSSINGS (V = 0):\n")
        if zero_points:
            for x_z, m_z in zero_points:
                self.res_text.insert(tk.END, f"  x = {x_z:.3f} m  ->  M = {m_z:.3f} kNm\n")
        else:
            self.res_text.insert(tk.END, "  None detected\n")

        self.res_text.insert(tk.END, f"\nPEAK BENDING MOMENT:\n  Max M = {max_m_val:.3f} kNm at x = {max_m_pos:.3f} m\n")

        if contraflexure:
            self.res_text.insert(tk.END, "\nPOINTS OF CONTRAFLEXURE (M = 0):\n")
            for x_cf in contraflexure:
                self.res_text.insert(tk.END, f"  x = {x_cf:.3f} m\n")

        # Refresh Canvas Axes
        self.ax0.cla()
        self.ax1.cla()
        self.ax2.cla()

        # FBD PANEL
        self.ax0.plot([0, length], [0, 0], color='black', linewidth=5)
        self.ax0.set_ylim(-2.2, 2.2)
        self.ax0.set_ylabel('FBD', fontweight='bold')
        self.ax0.grid(True, linestyle='--', alpha=0.4)

        for s in supports:
            pos = s['pos']
            if s['type'] in ['pinned', 'roller']:
                self.ax0.plot(pos, -0.15, '^', markersize=12, color='black')
                self.ax0.text(pos, -0.55, f"{s['type'].capitalize()}\nx={pos:.2f}m", ha='center', fontsize=7)
            elif s['type'] == 'fixed':
                self.ax0.plot([pos, pos], [-0.7, 0.7], color='black', linewidth=6)
                self.ax0.text(pos, 0.9, f"Fixed\nx={pos:.2f}m", ha='center', fontsize=7)

        for u in udls:
            self.ax0.add_patch(patches.Rectangle((u['start'], 0.05), u['end'] - u['start'], 0.35, color='orange', alpha=0.5))
            self.ax0.text((u['start'] + u['end'])/2.0, 0.5, f"UDL: {u['intensity']} kN/m", ha='center', fontweight='bold', color='darkorange', fontsize=8)

        for uv in uvls:
            h1 = 0.08 + (uv['start_w'] / (max(uv['start_w'], uv['end_w']) + 1e-5)) * 0.35
            h2 = 0.08 + (uv['end_w'] / (max(uv['start_w'], uv['end_w']) + 1e-5)) * 0.35
            pts = [[uv['start'], 0.05], [uv['end'], 0.05], [uv['end'], h2], [uv['start'], h1]]
            self.ax0.add_patch(patches.Polygon(pts, color='purple', alpha=0.4))
            self.ax0.text((uv['start'] + uv['end'])/2.0, max(h1, h2) + 0.15, f"UVL: {uv['start_w']}->{uv['end_w']}", ha='center', color='purple', fontsize=8)

        for pl in point_loads:
            pos, mag = pl['pos'], pl['mag']
            lbl = f"{pl.get('orig_mag', abs(mag)):.2f} kN"
            ang = pl.get('angle', 90.0)
            if ang != 90.0:
                lbl += f" @ {ang:.0f}°"
                rad = math.radians(ang)
                dx, dy = 0.5 * math.cos(rad), 0.9 * math.sin(rad)
                self.ax0.annotate(lbl, xy=(pos, 0.05), xytext=(pos - dx, dy + 0.25),
                                  arrowprops=dict(facecolor='blue', edgecolor='blue', shrink=0.05, width=1.5, headwidth=5),
                                  ha='center', fontweight='bold', color='blue', fontsize=8)
            else:
                y_txt = 1.25 if mag >= 0 else -1.25
                y_tgt = 0.05 if mag >= 0 else -0.05
                self.ax0.annotate(lbl, xy=(pos, y_tgt), xytext=(pos, y_txt),
                                  arrowprops=dict(facecolor='blue', edgecolor='blue', shrink=0.05, width=1.8, headwidth=6),
                                  ha='center', fontweight='bold', color='blue', fontsize=8)

        for pm in point_moments:
            sym = "↻" if pm['mag'] > 0 else "↺"
            self.ax0.plot(pm['pos'], 0, 'mo', markersize=6)
            self.ax0.annotate(f"{sym} {abs(pm['mag']):.2f} kNm", xy=(pm['pos'], 0.1), xytext=(pm['pos'], 0.7),
                              arrowprops=dict(arrowstyle="->", connectionstyle="arc3,rad=.3", color="magenta", lw=1.5),
                              ha='center', fontweight='bold', color='darkmagenta', fontsize=8)

        for name, val in reactions.items():
            pos = float(name.split("_")[1])
            if name.startswith("R_"):
                y_arr = -1.6 if val >= 0 else 1.6
                y_tgt = -0.05 if val >= 0 else 0.05
                self.ax0.annotate(f"{name} = {val:.2f} kN", xy=(pos, y_tgt), xytext=(pos, y_arr),
                                  arrowprops=dict(facecolor='red', edgecolor='red', shrink=0.05, width=1.8, headwidth=5),
                                  ha='center', fontweight='bold', color='darkred', fontsize=8)
            elif name.startswith("Rx_"):
                dx = 0.4 if val >= 0 else -0.4
                self.ax0.annotate(f"{name} = {val:.2f} kN", xy=(pos, 0.0), xytext=(pos - dx, 0.0),
                                  arrowprops=dict(facecolor='darkred', edgecolor='darkred', shrink=0.05, width=1.5, headwidth=5),
                                  ha='center', fontweight='bold', color='darkred', fontsize=7)
            elif name.startswith("M_"):
                self.ax0.text(pos, -1.0, f"{name} = {val:.2f} kNm", color='darkred', fontweight='bold', ha='center', fontsize=8)

        # SFD PANEL
        self.ax1.plot(x, V, color='blue', linewidth=2)
        self.ax1.fill_between(x, 0, V, where=(V >= 0), color='blue', alpha=0.3)
        self.ax1.fill_between(x, 0, V, where=(V < 0), color='red', alpha=0.3)
        self.ax1.axhline(0, color='black', linewidth=1)
        self.ax1.set_ylabel('Shear V (kN)', fontweight='bold')
        self.ax1.grid(True, linestyle='--', alpha=0.5)

        for x_z, _ in zero_points:
            self.ax1.plot(x_z, 0, 'ro', markersize=6)
            self.ax1.annotate(f"V=0\nx={x_z:.2f}m", xy=(x_z, 0),
                              xytext=(x_z, max(V)*0.4 if max(V) != 0 else 1.0),
                              arrowprops=dict(facecolor='black', arrowstyle='->'),
                              fontweight='bold', fontsize=7,
                              bbox=dict(boxstyle='round,pad=0.2', facecolor='yellow', alpha=0.7))

        # BMD PANEL
        self.ax2.plot(x, M, color='green', linewidth=2)
        self.ax2.fill_between(x, 0, M, where=(M >= 0), color='green', alpha=0.3)
        self.ax2.fill_between(x, 0, M, where=(M < 0), color='orange', alpha=0.3)
        self.ax2.axhline(0, color='black', linewidth=1)
        self.ax2.set_ylabel('Moment M (kNm)', fontweight='bold')
        self.ax2.set_xlabel('Beam Position x (m)', fontweight='bold')
        self.ax2.grid(True, linestyle='--', alpha=0.5)

        self.ax2.plot(max_m_pos, max_m_val, 'go', markersize=7)
        self.ax2.annotate(f"Max M = {max_m_val:.2f} kNm\nat x = {max_m_pos:.2f}m",
                          xy=(max_m_pos, max_m_val),
                          xytext=(max_m_pos, max_m_val * 0.6 if max_m_val != 0 else 1.0),
                          arrowprops=dict(facecolor='green', arrowstyle='->', lw=1.5),
                          fontweight='bold', fontsize=7,
                          bbox=dict(boxstyle='round,pad=0.2', facecolor='lightgreen', alpha=0.8))

        for x_cf in contraflexure:
            self.ax2.plot(x_cf, 0, 'mo', markersize=6)
            self.ax2.annotate(f"Contraflexure\nx = {x_cf:.2f}m", xy=(x_cf, 0),
                              xytext=(x_cf, -max_m_val * 0.4 if max_m_val != 0 else -1.0),
                              arrowprops=dict(facecolor='purple', arrowstyle='->'),
                              fontweight='bold', fontsize=7,
                              bbox=dict(boxstyle='round,pad=0.2', facecolor='plum', alpha=0.8))

        self.fig.suptitle('Shon Parale | Vedant Patel - Beam Mechanics Engine', fontsize=12, fontweight='bold')
        self.canvas.draw_idle()

    # ------------------ FILE COMMAND HANDLERS ------------------
    def load_csv(self):
        f = filedialog.askopenfilename(
            title="Load Problem from CSV",
            initialdir=SCRIPT_DIR,
            filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")]
        )
        if not f:
            return

        try:
            length, supports, point_loads, udls, uvls, point_moments = load_csv_data(f)
            self.length_var.set(str(length))

            for tree in (self.tree_sup, self.tree_pl, self.tree_udl, self.tree_uvl, self.tree_m):
                for item in tree.get_children():
                    tree.delete(item)

            for s in supports:
                self.tree_sup.insert('', tk.END, values=(s['type'], s['pos']))
            for pl in point_loads:
                self.tree_pl.insert('', tk.END, values=(pl.get('orig_mag', abs(pl['mag'])), pl.get('direction', 'down'), pl['pos'], pl.get('angle', 90.0)))
            for u in udls:
                self.tree_udl.insert('', tk.END, values=(u['intensity'], u['start'], u['end']))
            for uv in uvls:
                self.tree_uvl.insert('', tk.END, values=(uv['start_w'], uv['end_w'], uv['start'], uv['end']))
            for pm in point_moments:
                self.tree_m.insert('', tk.END, values=(abs(pm['mag']), 'clockwise' if pm['mag'] >= 0 else 'counter-clockwise', pm['pos']))

            self.compute_and_draw()
            messagebox.showinfo("Success", f"Loaded problem from {os.path.basename(f)}")
        except Exception as e:
            messagebox.showerror("CSV Load Error", str(e))

    def save_csv(self):
        try:
            length, supports, point_loads, udls, uvls, point_moments = self.get_problem_data()
        except Exception as e:
            messagebox.showerror("Error", f"Cannot export invalid data: {e}")
            return

        f = filedialog.asksaveasfilename(
            title="Save Problem Configuration",
            initialdir=SCRIPT_DIR,
            defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv")]
        )
        if not f:
            return

        try:
            write_csv_data(f, length, supports, point_loads, udls, uvls, point_moments)
            messagebox.showinfo("Success", f"Saved configuration to {os.path.basename(f)}")
        except Exception as e:
            messagebox.showerror("CSV Save Error", str(e))

    def export_image(self):
        f = filedialog.asksaveasfilename(
            title="Export High-Resolution Figure",
            initialdir=SCRIPT_DIR,
            defaultextension=".png",
            filetypes=[("PNG Image", "*.png"), ("PDF Document", "*.pdf"), ("SVG Vector", "*.svg")]
        )
        if not f:
            return

        try:
            self.fig.savefig(f, dpi=300, bbox_inches='tight')
            messagebox.showinfo("Success", f"Exported diagram to {os.path.basename(f)}")
        except Exception as e:
            messagebox.showerror("Export Error", str(e))

    def show_manual(self):
        win = tk.Toplevel(self.root)
        win.title("User Manual - Shon Parale | Vedant Patel")
        win.geometry("640x520")

        txt = tk.Text(win, font=('Helvetica', 10), wrap=tk.WORD, padx=10, pady=10)
        txt.pack(fill=tk.BOTH, expand=True)

        manual_content = """Shon Parale | Vedant Patel
Beam Mechanics Solver v6.0: Quick Manual

1. OVERVIEW
This application solves statically determinate beams and renders:
- Free Body Diagram (FBD) with supports, loads, and reactions.
- Shear Force Diagram (SFD) with exact vertical step jumps.
- Bending Moment Diagram (BMD) with peak moment cusp capture.
- Critical points (V = 0 crossings, max bending moments, points of contraflexure).

2. DETERMINATE BOUNDARY CONDITIONS
- Simply Supported / Overhanging: Exactly 2 supports (Pinned + Roller).
- Cantilever: Exactly 1 support (Fixed).

3. SIGN CONVENTIONS
- Forces: 'down' (downward gravity) or 'up'.
- Moments: 'clockwise' (+) or 'counter-clockwise' (-).
- Bending Moment: Sagging is (+); Hogging is (-).

4. WORKFLOW & CSV FILES
- Edit fields using the tabs on the left, then click 'COMPUTE & PLOT'.
- Use 'Load CSV' / 'Save CSV' to store and retrieve reusable problems.
- Use 'Export Plot' to save a publication-quality diagram (PNG, PDF, SVG).
"""
        txt.insert(tk.END, manual_content)
        txt.config(state=tk.DISABLED)


# ==============================================================================
# MAIN ENTRY POINT
# ==============================================================================
if __name__ == "__main__":
    app_root = tk.Tk()
    app = BeamApp(app_root)
    app_root.mainloop()