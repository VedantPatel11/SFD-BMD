# Automated Beam Mechanics Solver: SFD & BMD Engine

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue.svg?logo=python&logoColor=white)](https://www.python.org/)
[![NumPy](https://img.shields.io/badge/NumPy-1.24%2B-013243.svg?logo=numpy&logoColor=white)](https://numpy.org/)
[![Matplotlib](https://img.shields.io/badge/Matplotlib-3.7%2B-11557c.svg)](https://matplotlib.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Course](https://img.shields.io/badge/Course-21CSO352T--Python--Programming-brightgreen)](https://www.srmist.edu.in/)
[![Status](https://img.shields.io/badge/Status-Complete-success)]()

A high-precision computational mechanics engine and visualizer for statically determinate structural beams. The engine evaluates support reactions, integrates continuous **Shear Force Diagrams (SFD)** and **Bending Moment Diagrams (BMD)**, calculates exact zero-shear crossing locations, identifies global peak bending moments, locates contraflexure points, and exports publication-grade 3-panel synchronized engineering graphics.

Developed as a major course project for **21CSO352T – Python Programming** in the **Department of Mechanical Engineering, College of Engineering and Technology, SRM Institute of Science and Technology, Kattankulathur**.

---

## 👥 Authors & Collaborators

- **Shon Parale** ([@ShonParale](https://github.com/ShonParale)) — Reg. No: `RA2311072010002`
- **Vedant Patel** — Reg. No: `RA2311072010009`

**Course Instructor / Faculty Guide**:  
**Dr. Raghavendra V**, Professor, Department of Computing Technologies, SRM Institute of Science and Technology.

---

## 📌 Project Overview & Key Capabilities

- **Statically Determinate Boundary Conditions**:
  - Simply Supported and Overhanging Beams (Pinned and Roller supports at arbitrary locations).
  - Cantilever Beams (Fixed clamping support at left $x=0$ or right $x=L$).
- **Complete Loading Spectrum**:
  - **Concentrated Point Loads**: Vertical (up/down) or inclined at arbitrary angles with automated orthogonal vector resolution ($P_y = P\sin\theta, P_x = P\cos\theta$).
  - **Uniformly Distributed Loads (UDL)**: Constant intensity $w$ ($\text{kN/m}$) spanning arbitrary segments.
  - **Uniformly Varying Loads (UVL)**: Linear triangular and trapezoidal profiles ($w_1 \to w_2$) with exact centroid calculus.
  - **Concentrated Couples / Moments**: Clockwise ($+$) and Counter-Clockwise ($-$) point couples.
- **Continuous Macaulay Singularity Integration**:
  - Longitudinal grid resolution over 5,000 points ($\Delta x \le 1.2\text{ mm}$ on a $6\text{ m}$ beam) for high numerical fidelity.
- **Sub-Grid Root-Finding Analytics**:
  - Linear interpolation bisection to pinpoint the exact coordinates where shear force crosses zero ($V(x) = 0$).
  - Precise determination of maximum bending moment ($M_{\max}$) and points of contraflexure ($M(x) = 0$).
- **Dual-Reference Coordinate Entry**:
  - Distances can be measured and entered from either the **LEFT end ($x = 0$)** or the **RIGHT end ($x = L$)**.
- **Persistent Multi-Section CSV Ingestion**:
  - Define, save, and reload complete beam problems using standard spreadsheet-compatible `.csv` files.
- **Synchronized 3-Panel Matplotlib Visualizer**:
  - **Top Panel**: Free Body Diagram (FBD) showing beam span, support fixtures, load patches, force vectors, and reaction vectors.
  - **Middle Panel**: Shear Force Diagram (SFD) with positive (blue) and negative (red) color grading and zero-shear callout markers.
  - **Bottom Panel**: Bending Moment Diagram (BMD) with sagging (green) and hogging (orange) shading and global peak moment callouts.
  - Automatic export of high-resolution 300 DPI figures (`.png`, `.pdf`, `.svg`).

---

## 📁 Repository Structure

```
├── Submission_Files/                      # Official Academic Submission Package
│   ├── Project_Report.docx               # Full academic project report with title page & derivations
│   ├── sfd_bmd_engine_4.ipynb            # Fully executed Jupyter Notebook with inline plots
│   ├── sfd_bmd_engine_4.py               # Final production-grade solver script (v4)
│   ├── beam.csv                          # Benchmark problem configuration file
│   ├── beam.png                          # Generated 300 DPI 3-panel visualization
│   └── Q1.jpg                            # Textbook problem diagram (R. K. Rajput)
│
├── Project_Code_and_Support_Files/       # Development History & Reference Assets
│   ├── sfd_bmd_engine_1.py               # Version 1: Initial point-load proof of concept
│   ├── sfd_bmd_engine_2.py               # Version 2: Extended loads (UDL, UVL, Moments) & 3-panel plot
│   ├── sfd_bmd_engine_3.py               # Version 3: CSV persistence & dual-coordinate system
│   ├── sfd_bmd_engine_4.py               # Version 4: Final engine with interactive review loop
│   ├── sfd_bmd_engine.py                 # Engine baseline
│   ├── sfd_bmd_engine_5.py               # Experimental version (archived)
│   ├── sfd_bmd_engine_6.py               # Experimental version (archived)
│   ├── sfd_bmd_engine_6_1.py             # Experimental version (archived)
│   ├── beam.csv                          # Benchmark CSV input
│   ├── Sample_Question Text.txt          # Problem description & segment measurements
│   ├── Q1.jpg                            # Textbook scan (RK Rajput)
│   ├── 1.pdf                             # High-res PDF generated by app
│   ├── beam.png                          # High-res PNG generated by app
│   ├── Figure_1.png                      # Reference diagram
│   └── Report Page 1.docx                # University title page template
│
├── Test_and_Generate_Scripts/            # Automation & Build Scripts
│   ├── test_and_generate_pipeline.py     # All-in-one consolidated generator & verification suite
│   ├── create_report.py                  # Script to build Project_Report.docx
│   ├── generate_notebook.py              # Script to build sfd_bmd_engine_4.ipynb
│   └── execute_notebook.py               # Headless Jupyter execution and verification script
│
├── .gitignore                            # Standard Python & Jupyter ignore rules
├── .gitattributes                        # Line endings & binary file specifications
├── LICENSE                               # MIT Open Source License
├── requirements.txt                      # Python dependencies list
└── README.md                             # Repository documentation
```

---

## 🚀 Quick Start & Installation

### 1. Prerequisites
Ensure you have Python 3.9+ installed on your system.

### 2. Clone the Repository
```bash
git clone https://github.com/ShonParale/SFD-BMD-Mechanics-Engine.git
cd SFD-BMD-Mechanics-Engine
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

---

## 💻 Usage Instructions

### Option A: Run the Final Python Engine (Interactive or CSV Mode)
Run the final submitted version [`sfd_bmd_engine_4.py`](Submission_Files/sfd_bmd_engine_4.py):
```bash
cd Submission_Files
python sfd_bmd_engine_4.py
```

The program will launch the main interactive menu:
```
=================================================================
          BEAM MECHANICS SOLVER: SFD & BMD ENGINE
=================================================================
Select an option:
   1. Start New Problem (Interactive Step-by-Step)
   2. Load Problem from CSV File
   3. Show User Manual & CSV Specification
   4. Exit
Select option number: 
```

- Choose **Option 1** to input a beam interactively with step-by-step guidance and a pre-flight verification review loop.
- Choose **Option 2** to instantly load a saved problem (e.g. type `beam.csv`).
- Choose **Option 3** to inspect sign conventions and CSV formatting rules in the terminal.

### Option B: Launch the Jupyter Notebook
Open the interactive Jupyter Notebook to explore step-by-step explanations, theory, and inline rendered visualizations:
```bash
cd Submission_Files
jupyter notebook sfd_bmd_engine_4.ipynb
```

---

## 🔬 Benchmark Validation: R. K. Rajput Example 4.7

To verify numerical accuracy, the engine was benchmarked against **Example 4.7** from the textbook *Strength of Materials* by Dr. R. K. Rajput:

### Problem Definition:
- **Beam Span**: $L = 6.0\text{ m}$ (Simply Supported: Pinned at $x=0$, Roller at $x=6\text{ m}$)
- **Loads**:
  - Concentrated load $P_C = 1.0\text{ kN}$ at $x = 1.0\text{ m}$
  - Uniformly Distributed Load $w = 2.0\text{ kN/m}$ from $x = 2.0\text{ m}$ to $x = 4.0\text{ m}$
  - Concentrated load $P_F = 4.0\text{ kN}$ at $x = 5.0\text{ m}$

### Quantitative Verification:

| Parameter | Analytical Solution (Rajput) | Python Engine v4 Output | Error (%) |
| :--- | :---: | :---: | :---: |
| **Left Reaction $R_A$ ($x = 0\text{ m}$)** | $3.500\text{ kN}$ | $3.500\text{ kN}$ | **0.00 %** |
| **Right Reaction $R_B$ ($x = 6\text{ m}$)** | $5.500\text{ kN}$ | $5.500\text{ kN}$ | **0.00 %** |
| **Zero Shear Coordinate ($x_{\text{zero}}$)** | $3.250\text{ m}$ | $3.250\text{ m}$ | **0.00 %** |
| **Distance of $V=0$ from Right Support** | $2.750\text{ m}$ | $2.750\text{ m}$ | **0.00 %** |
| **Maximum Bending Moment ($M_{\max}$)** | $7.5625\text{ kNm}$ | $7.562\text{ kNm}$ | **0.00 %** |
| **Bending Moment at Point D ($x = 2\text{ m}$)** | $6.000\text{ kNm}$ | $6.000\text{ kNm}$ | **0.00 %** |
| **Bending Moment at Point E ($x = 4\text{ m}$)** | $7.000\text{ kNm}$ | $7.000\text{ kNm}$ | **0.00 %** |

**Verification Result**: Exact **0.00% relative error**, confirming analytical accuracy and sub-millimeter precision.

---

## 📈 Evolutionary Development (v1 $\to$ v4)

1. **Version 1 (`sfd_bmd_engine_1.py`)**:
   - Proof-of-concept CLI calculator for simply supported and cantilever beams under concentrated vertical loads. Standard 2-panel plot.
2. **Version 2 (`sfd_bmd_engine_2.py`)**:
   - Added support for distributed loads (UDLs, UVLs) and moments. Integrated zero-shear and contraflexure analytics. Upgraded to a 3-panel synchronized visualizer (FBD, SFD, BMD) with `matplotlib.patches`.
3. **Version 3 (`sfd_bmd_engine_3.py`)**:
   - Implemented persistent multi-section CSV ingestion/export and dual-reference coordinates (left or right measurement). Added in-terminal documentation.
4. **Version 4 (`sfd_bmd_engine_4.py` - Final Submitted Milestone)**:
   - Modular load collectors, pre-flight review/verification loop (`review_and_verify`), directory-independent file resolution (`SCRIPT_DIR`), sub-grid root-finding interpolation, and 300 DPI publication graphics.

---

## 🔮 What is Next to Do

The primary future work for this project is to:
- **Make a GUI for the app.**

Developing an interactive desktop Graphical User Interface (using PyQt or CustomTkinter) with an interactive beam drafting canvas, real-time dynamic curve recalculation as loads are placed or dragged, and visual file dialogs for CSV management and PDF export.

---

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
