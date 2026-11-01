import os
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

def set_cell_background(cell, hex_color):
    """Sets background color of a table cell."""
    tc_pr = cell._tc.get_or_add_tcPr()
    tc_pr.append(parse_xml(f'<w:shd {nsdecls("w")} w:fill="{hex_color}"/>'))

def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    """Sets internal padding for a table cell."""
    tc_pr = cell._tc.get_or_add_tcPr()
    tc_mar = parse_xml(f'<w:tcMar {nsdecls("w")}><w:top w:w="{top}" w:type="dxa"/><w:bottom w:w="{bottom}" w:type="dxa"/><w:left w:w="{left}" w:type="dxa"/><w:right w:w="{right}" w:type="dxa"/></w:tcMar>')
    tc_pr.append(tc_mar)

def add_heading_1(doc, text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(14)
    p.paragraph_format.space_after = Pt(6)
    p.paragraph_format.keep_with_next = True
    run = p.add_run(text)
    run.font.name = 'Calibri'
    run.font.size = Pt(16)
    run.bold = True
    run.font.color.rgb = RGBColor(0x1F, 0x4E, 0x79) # Deep Navy
    return p

def add_heading_2(doc, text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(11)
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.keep_with_next = True
    run = p.add_run(text)
    run.font.name = 'Calibri'
    run.font.size = Pt(13)
    run.bold = True
    run.font.color.rgb = RGBColor(0x2E, 0x75, 0xB6) # Slate Blue
    return p

def add_heading_3(doc, text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(8)
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.keep_with_next = True
    run = p.add_run(text)
    run.font.name = 'Calibri'
    run.font.size = Pt(11.5)
    run.bold = True
    run.font.color.rgb = RGBColor(0x33, 0x33, 0x33) # Charcoal
    return p

def add_body_p(doc, text, bold_prefix="", italic=False):
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(6)
    p.paragraph_format.line_spacing = 1.15
    if bold_prefix:
        r_b = p.add_run(bold_prefix)
        r_b.font.name = 'Calibri'
        r_b.font.size = Pt(11)
        r_b.bold = True
        r_b.font.color.rgb = RGBColor(0x22, 0x22, 0x22)
    r = p.add_run(text)
    r.font.name = 'Calibri'
    r.font.size = Pt(11)
    r.italic = italic
    r.font.color.rgb = RGBColor(0x33, 0x33, 0x33)
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    return p

def add_bullet_p(doc, text, bold_prefix=""):
    p = doc.add_paragraph(style='List Bullet')
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.line_spacing = 1.15
    if bold_prefix:
        r_b = p.add_run(bold_prefix)
        r_b.font.name = 'Calibri'
        r_b.font.size = Pt(11)
        r_b.bold = True
        r_b.font.color.rgb = RGBColor(0x22, 0x22, 0x22)
    r = p.add_run(text)
    r.font.name = 'Calibri'
    r.font.size = Pt(11)
    r.font.color.rgb = RGBColor(0x33, 0x33, 0x33)
    return p

def add_code_block(doc, code_str, caption=""):
    if caption:
        p_cap = doc.add_paragraph()
        p_cap.paragraph_format.space_before = Pt(6)
        p_cap.paragraph_format.space_after = Pt(2)
        p_cap.paragraph_format.keep_with_next = True
        r_c = p_cap.add_run(caption)
        r_c.font.name = 'Calibri'
        r_c.font.size = Pt(10)
        r_c.bold = True
        r_c.font.color.rgb = RGBColor(0x1F, 0x4E, 0x79)

    tbl = doc.add_table(rows=1, cols=1)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = tbl.cell(0, 0)
    set_cell_background(cell, "F4F6F8")
    set_cell_margins(cell, top=120, bottom=120, left=180, right=180)

    # Set light gray border
    tc_pr = cell._tc.get_or_add_tcPr()
    tc_pr.append(parse_xml(f'<w:tcBorders {nsdecls("w")}><w:top w:val="single" w:sz="4" w:space="0" w:color="D0D5DD"/><w:left w:val="single" w:sz="12" w:space="0" w:color="1F4E79"/><w:bottom w:val="single" w:sz="4" w:space="0" w:color="D0D5DD"/><w:right w:val="single" w:sz="4" w:space="0" w:color="D0D5DD"/></w:tcBorders>'))

    p = cell.paragraphs[0]
    p.paragraph_format.space_after = Pt(0)
    p.paragraph_format.line_spacing = 1.05
    run = p.add_run(code_str)
    run.font.name = 'Consolas'
    run.font.size = Pt(9.0)
    run.font.color.rgb = RGBColor(0x24, 0x29, 0x2E)

    doc.add_paragraph().paragraph_format.space_after = Pt(4)

def add_callout_box(doc, text, title="KEY ENGINEERING PRINCIPLE"):
    tbl = doc.add_table(rows=1, cols=1)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = tbl.cell(0, 0)
    set_cell_background(cell, "EBF3FB")
    set_cell_margins(cell, top=140, bottom=140, left=200, right=200)

    tc_pr = cell._tc.get_or_add_tcPr()
    tc_pr.append(parse_xml(f'<w:tcBorders {nsdecls("w")}><w:top w:val="single" w:sz="4" w:space="0" w:color="B8D5E5"/><w:left w:val="single" w:sz="18" w:space="0" w:color="1F4E79"/><w:bottom w:val="single" w:sz="4" w:space="0" w:color="B8D5E5"/><w:right w:val="single" w:sz="4" w:space="0" w:color="B8D5E5"/></w:tcBorders>'))

    p = cell.paragraphs[0]
    p.paragraph_format.space_after = Pt(2)
    r_t = p.add_run(f"[{title}]\n")
    r_t.font.name = 'Calibri'
    r_t.font.size = Pt(10.5)
    r_t.bold = True
    r_t.font.color.rgb = RGBColor(0x1F, 0x4E, 0x79)

    r_b = p.add_run(text)
    r_b.font.name = 'Calibri'
    r_b.font.size = Pt(10)
    r_b.italic = True
    r_b.font.color.rgb = RGBColor(0x1A, 0x2A, 0x3A)

    doc.add_paragraph().paragraph_format.space_after = Pt(4)

def build_report():
    input_doc_path = os.path.join(SCRIPT_DIR, "Report Page 1.docx")
    output_doc_path = os.path.join(SCRIPT_DIR, "Project_Report_SFD_BMD_Engine.docx")
    output_doc_path_std = os.path.join(SCRIPT_DIR, "Project_Report.docx")

    print(f"Loading '{input_doc_path}'...")
    doc = docx.Document(input_doc_path)

    # 1. Update Title on Page 1
    p1 = doc.paragraphs[1]
    p1.text = ''
    r1 = p1.add_run("AUTOMATED BEAM MECHANICS SOLVER:\nCOMPUTATION AND VISUALIZATION OF SHEAR FORCE AND BENDING MOMENT DIAGRAMS (SFD & BMD)")
    r1.font.name = 'Calibri'
    r1.font.size = Pt(17)
    r1.bold = True
    r1.font.color.rgb = RGBColor(0x1F, 0x4E, 0x79)
    p1.alignment = WD_ALIGN_PARAGRAPH.CENTER

    # Clean up en-dash encoding in course and university paragraphs
    p20 = doc.paragraphs[20]
    p20.text = "21CSO352T – Python Programming"
    p20.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for r in p20.runs:
        r.font.name = 'Calibri'
        r.font.size = Pt(14)
        r.bold = True

    p28 = doc.paragraphs[28]
    p28.text = "DEPARTMENT OF MECHANICAL ENGINEERING\nCOLLEGE OF ENGINEERING AND TECHNOLOGY\nSRM INSTITUTE OF SCIENCE AND TECHNOLOGY\nKATTANKULATHUR – 603 203"
    p28.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for r in p28.runs:
        r.font.name = 'Calibri'
        r.font.size = Pt(12)
        r.bold = True

    # Page Break after Title Page
    doc.add_page_break()

    # --------------------------------------------------------------------------
    # TABLE OF CONTENTS / EXECUTIVE SUMMARY
    # --------------------------------------------------------------------------
    add_heading_1(doc, "EXECUTIVE SUMMARY")
    add_body_p(doc, 
        "This project report presents the systematic design, theoretical formulation, and incremental development "
        "of a high-performance Python computational engine for the structural analysis of statically determinate beams. "
        "The software calculates external reaction forces and moments, evaluates continuous Shear Force Diagrams (SFD) "
        "and Bending Moment Diagrams (BMD), locates critical zero-shear crossing points, computes global peak bending moments, "
        "and identifies points of contraflexure. The engine supports a rich array of boundary conditions (Simply Supported, "
        "Overhanging, and Cantilever beams) and arbitrary combinations of transverse loading—including concentrated point loads "
        "(vertical or inclined), uniformly distributed loads (UDL), uniformly varying loads (UVL with linear trapezoidal/triangular profiles), "
        "and concentrated point couples."
    )
    add_body_p(doc,
        "The project evolved across four major milestone versions (v1, v2, v3, and v4). Starting from a rudimentary point-load CLI script, "
        "the architecture matured into an industrial-grade engineering application featuring persistent multi-table CSV ingestion, "
        "bidirectional coordinate referencing (distances from either the left or right beam boundary), an interactive review and modification loop, "
        "and high-resolution 3-tier publication graphics (Free Body Diagram, SFD, and BMD). The final version (sfd_bmd_engine_4.py) "
        "was rigorously benchmarked and validated against Example 4.7 from the classic textbook 'Strength of Materials' by R. K. Rajput. "
        "The software's numerical predictions achieve exact 0.00% agreement with analytical closed-form solutions, validating both its "
        "mathematical rigor and programming robustness."
    )

    add_callout_box(doc,
        "Project Scope: Academic Software Development for 21CSO352T (Python Programming).\n"
        "Department: Mechanical Engineering, College of Engineering & Technology, SRM Institute of Science and Technology.\n"
        "Authors: Shon Parale (RA2311072010002) and Vedant Patel (RA2311072010009).\n"
        "Final Submitted Source Code: sfd_bmd_engine_4.py",
        title="PROJECT METADATA"
    )

    # --------------------------------------------------------------------------
    # CHAPTER 1: INTRODUCTION & THEORETICAL FOUNDATION
    # --------------------------------------------------------------------------
    add_heading_1(doc, "1. INTRODUCTION & THEORETICAL FOUNDATIONS")
    add_body_p(doc,
        "In structural engineering, civil engineering, and mechanical machine design, beams are fundamental load-bearing members "
        "subject to transverse forces, distributed pressures, and external bending couples. The internal stresses generated across "
        "any cross-section are directly characterized by two key quantities: Shear Force (V) and Bending Moment (M). "
        "Designing safe and cost-effective structural elements requires plotting these quantities as continuous functions of "
        "longitudinal position x, yielding the Shear Force Diagram (SFD) and Bending Moment Diagram (BMD)."
    )

    add_heading_2(doc, "1.1 Governing Differential Equations of Beam Mechanics")
    add_body_p(doc,
        "The behavior of a beam in static equilibrium is governed by the classical differential equations relating distributed load intensity w(x), "
        "internal transverse shear force V(x), and internal bending moment M(x):"
    )
    add_bullet_p(doc, "dV(x) / dx = -w(x)   [The rate of change of shear force equals the negative of load intensity]", "1. Load-Shear Differential Relation: ")
    add_bullet_p(doc, "dM(x) / dx = V(x)   [The rate of change of bending moment equals the transverse shear force]", "2. Shear-Moment Differential Relation: ")
    add_bullet_p(doc, "d²M(x) / dx² = -w(x) [Curvature and second derivative relationship]", "3. Second-Order Relation: ")

    add_body_p(doc,
        "From calculus, when a continuous function's first derivative equals zero, the function reaches a local extremum. "
        "Because dM/dx = V(x), the bending moment M(x) attains its maximum or minimum values precisely at locations where the shear force "
        "crosses zero (V(x) = 0). Identifying these zero-shear points with sub-millimeter precision is essential, as the peak bending moment "
        "dictates the required elastic section modulus (Z = M_max / sigma_allowable) to prevent structural failure or plastic yielding."
    )

    add_heading_2(doc, "1.2 Static Equilibrium Conditions")
    add_body_p(doc,
        "For statically determinate coplanar beam systems, the unknown support reactions are uniquely determined from the equations of "
        "rigid-body static equilibrium in two dimensions:"
    )
    add_bullet_p(doc, "Σ Fy = 0  -->  Total Upward Support Reactions = Total Downward Applied Loads", "Transverse Equilibrium: ")
    add_bullet_p(doc, "Σ M_z(0) = 0  -->  Algebraic sum of all moments about any arbitrary reference point (e.g., left origin x=0) must vanish.", "Rotational Equilibrium: ")

    add_body_p(doc,
        "For simply supported or overhanging beams with two supports (pinned and roller) located at x1 and x2, taking moments about x1 yields:"
    )
    add_bullet_p(doc, "R2 = [ Σ (P_i * x_i) + Σ ∫ w(x)*x dx + Σ M_applied - Total_Force * x1 ] / (x2 - x1)", "Reaction at Support 2: ")
    add_bullet_p(doc, "R1 = Total_Force - R2", "Reaction at Support 1: ")
    add_body_p(doc,
        "For cantilever beams clamped rigidly at support x_s, the wall provides a single vertical reaction R_y = Total_Force and a clamping "
        "counter-moment M_fixed = -(Total_Moment - Total_Force * x_s)."
    )

    add_heading_2(doc, "1.3 Mechanical Sign Conventions")
    add_body_p(doc,
        "Consistent sign conventions are critical to avoid catastrophic errors in sign and diagram interpretation. "
        "The software strictly adheres to international civil and mechanical engineering standards:"
    )
    add_bullet_p(doc, "Shear Force (V): Positive (+) when an upward force acts to the left of the cutting section or downward force to the right.", "Shear Force Convention: ")
    add_bullet_p(doc, "Bending Moment (M): Sagging bending moments (which create concave upward curvature, inducing compression in top fibers and tension in bottom fibers) are POSITIVE (+). Hogging bending moments (convex upward curvature, inducing tension in top fibers) are NEGATIVE (-).", "Bending Moment Convention: ")
    add_bullet_p(doc, "Applied Moments: Clockwise external couples are treated as positive (+), Counter-Clockwise as negative (-).", "Concentrated Moments: ")
    add_bullet_p(doc, "Points of Contraflexure: Locations along the beam where the bending moment changes sign (M = 0), representing zero-curvature inflection points where bending stress reverses direction.", "Contraflexure Points: ")

    # --------------------------------------------------------------------------
    # CHAPTER 2: PROJECT GOAL & SYSTEM ARCHITECTURE
    # --------------------------------------------------------------------------
    add_heading_1(doc, "2. PROJECT GOAL & ARCHITECTURAL OVERVIEW")
    add_body_p(doc,
        "The overarching goal of this project is to engineer an accurate, fully automated, and highly resilient Python computational engine "
        "capable of analyzing arbitrary statically determinate beam configurations under complex multi-load scenarios. "
        "Manual calculation of SFD and BMD diagrams is time-consuming, prone to algebraic errors, and difficult to visualize. "
        "This software solves this problem by integrating rigorous numerical mechanics, robust error handling, multi-source data ingestion, "
        "and synchronized multi-panel plotting."
    )

    add_heading_2(doc, "2.1 Key Functional Requirements")
    add_bullet_p(doc, "Support all determinate boundary conditions: Cantilever (fixed wall left or right) and Simply Supported / Overhanging beams.", "1. Determinacy Support: ")
    add_bullet_p(doc, "Accommodate point loads (vertical or inclined at arbitrary angles), UDL spans, UVL trapezoidal/triangular profiles, and concentrated couples.", "2. Load Diversity: ")
    add_bullet_p(doc, "Eliminate manual coordinate shifting by enabling the user to specify distances either from the left end (x = 0) or the right end (x = L).", "3. Dual-Coordinate Ingestion: ")
    add_bullet_p(doc, "Formulate closed-form reactions and apply singularity function integration over 5,000 discrete points for sub-millimeter precision.", "4. Dense Numerical Grid: ")
    add_bullet_p(doc, "Calculate zero-shear crossings via linear interpolation, extract global peak bending moments, and mark contraflexure points.", "5. Critical Point Analytics: ")
    add_bullet_p(doc, "Enable persistent data storage using multi-section CSV files and export publication-ready 300 DPI graphics.", "6. Persistence & Export: ")
    add_bullet_p(doc, "Provide an interactive verification loop that allows reviewing and modifying inputs before executing the solver.", "7. Interactive Fault Tolerance: ")

    add_heading_2(doc, "2.2 High-Level System Architecture")
    add_body_p(doc,
        "The software architecture follows a modular decoupled pipeline divided into six cohesive functional subsystems:"
    )

    # Architecture summary table
    arch_tbl = doc.add_table(rows=7, cols=3)
    arch_tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    headers = ["Subsystem Module", "Primary Python Functions", "Role & Engineering Functionality"]
    col_widths = [Inches(1.8), Inches(2.2), Inches(2.8)]

    for c_idx, title in enumerate(headers):
        cell = arch_tbl.cell(0, c_idx)
        cell.width = col_widths[c_idx]
        set_cell_background(cell, "1F4E79")
        set_cell_margins(cell, top=100, bottom=100, left=120, right=120)
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(title)
        r.font.name = 'Calibri'
        r.font.size = Pt(10)
        r.bold = True
        r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)

    subsystems = [
        ("1. Input & Coordinate Transformer", "get_float(), get_choice(), get_position()", "Robust validation, type safety, range checking, and dual-reference coordinate mapping (left/right)."),
        ("2. Interactive Load Collectors", "setup_beam_interactive(), collect_point_loads(), collect_udls(), collect_uvls(), collect_moments()", "Step-by-step modular collection of beam geometry, supports, inclined forces, distributed loads, and couples."),
        ("3. Review & Verification Loop", "review_and_verify()", "Interactive pre-flight inspection of beam configuration; allows editing, adding loads, or restarting before calculation."),
        ("4. CSV Persistence Engine", "load_from_csv(), save_to_csv()", "Structured multi-table CSV serialization and deserialization with directory-agnostic path handling via SCRIPT_DIR."),
        ("5. Equilibrium & Singularity Solver", "solve_reactions(), calculate_sfd_bmd()", "Analytical reaction solver via static equilibrium equations, followed by dense Macaulay/singularity numerical integration across 5,000 points."),
        ("6. Critical Analytics & Visualizer", "find_critical_points(), create_figure()", "Zero-crossing bisection, maximum moment detection, contraflexure identification, and 3-panel synchronized Matplotlib rendering.")
    ]

    for r_idx, data in enumerate(subsystems, 1):
        bg = "FFFFFF" if r_idx % 2 == 1 else "F4F6F8"
        for c_idx, val in enumerate(data):
            cell = arch_tbl.cell(r_idx, c_idx)
            cell.width = col_widths[c_idx]
            set_cell_background(cell, bg)
            set_cell_margins(cell, top=80, bottom=80, left=100, right=100)
            p = cell.paragraphs[0]
            r = p.add_run(val)
            r.font.name = 'Calibri'
            r.font.size = Pt(9.5)
            r.font.color.rgb = RGBColor(0x33, 0x33, 0x33)
            if c_idx == 0:
                r.bold = True

    doc.add_paragraph().paragraph_format.space_after = Pt(6)

    # --------------------------------------------------------------------------
    # CHAPTER 3: EVOLUTIONARY DEVELOPMENT ACROSS VERSIONS (V1 -> V2 -> V3 -> V4)
    # --------------------------------------------------------------------------
    add_heading_1(doc, "3. EVOLUTIONARY DEVELOPMENT ACROSS VERSIONS")
    add_body_p(doc,
        "Developing this software followed a structured agile methodology. Rather than creating a single monolithic program, "
        "the engine was systematically designed and refined across four distinct milestone versions: Version 1 (sfd_bmd_engine_1.py), "
        "Version 2 (sfd_bmd_engine_2.py), Version 3 (sfd_bmd_engine_3.py), and the final production-ready Version 4 (sfd_bmd_engine_4.py). "
        "The following sections chronicle the engineering objectives, architectural upgrades, limitations encountered, and code advancements "
        "for each iteration."
    )

    # Version 1
    add_heading_2(doc, "3.1 Version 1 (sfd_bmd_engine_1.py) – Initial Computational Prototype")
    add_body_p(doc,
        "Goal of Version 1: Establish a minimal working proof-of-concept that can compute support reactions and plot basic SFD and BMD "
        "curves for a simply supported beam or cantilever beam carrying concentrated vertical point loads."
    )
    add_body_p(doc,
        "Progress & Implementation Details: "
        "Version 1 successfully implemented safe terminal input prompts (get_float, get_choice), an analytical equilibrium reaction calculator "
        "for simply supported and cantilever boundary conditions, and a basic numerical evaluation of shear force and bending moment over 5,000 points. "
        "A standard Matplotlib window with two vertically stacked subplots (SFD and BMD) was used to visualize the result."
    )
    add_bullet_p(doc, "Supported Beam Types: Simply Supported (pin at 0, roller at L) and Cantilever (fixed wall at 0 or L).", "Capabilities: ")
    add_bullet_p(doc, "Supported Loading: Strictly concentrated point loads (downward or upward).", "")
    add_bullet_p(doc, "Visualization: Two 2D line plots for SFD and BMD with colored fill under curves.", "")

    add_body_p(doc,
        "Limitations Encountered in Version 1: "
        "Real-world structural engineering problems rarely feature only point loads. Version 1 completely lacked support for Uniformly "
        "Distributed Loads (UDL), Uniformly Varying Loads (UVL), and concentrated bending couples. Furthermore, it did not render a Free Body "
        "Diagram (FBD), could not compute exact zero-shear crossing coordinates or contraflexure points, offered no persistence mechanism, "
        "and forced the user to restart the script on any input mistake."
    )

    add_code_block(doc,
"""# sfd_bmd_engine_1.py (Excerpt: Point load calculation and basic plotting)
def calculate_sfd_bmd(length, supports, point_loads, num_points=5000):
    reactions = solve_reactions(length, supports, point_loads)
    x = np.linspace(0.0, length, num_points)
    V = np.zeros(num_points)
    M = np.zeros(num_points)
    
    # Superposition of reactions
    for name, val in reactions.items():
        x_r = float(name.split('_')[1])
        mask = x >= x_r
        if name.startswith('R_'):
            V[mask] += val
            M[mask] += val * (x[mask] - x_r)
        elif name.startswith('M_'):
            M[mask] += val
            
    # Superposition of point loads only
    for pl in point_loads:
        mask = x >= pl['pos']
        V[mask] -= pl['mag']
        M[mask] -= pl['mag'] * (x[mask] - pl['pos'])
        
    return x, V, M, reactions""",
        caption="Code Snippet 1: Version 1 Point-Load Integration Engine"
    )

    # Version 2
    add_heading_2(doc, "3.2 Version 2 (sfd_bmd_engine_2.py) – Extended Load Spectrum & 3-Panel Visualizer")
    add_body_p(doc,
        "Goal of Version 2: Expand the mechanical load handling to cover distributed loads (UDL, UVL) and couples, implement analytical "
        "critical point detection (zero shear, peak moment, contraflexure), and upgrade visualization into a synchronized 3-panel display "
        "(Free Body Diagram, SFD, and BMD)."
    )
    add_body_p(doc,
        "Progress & Implementation Details: "
        "Version 2 introduced calculus-based integration routines for UDL spans and UVL linear profiles. For UVLs with varying intensity "
        "from w1 to w2, exact centroid integration formulas were derived and incorporated into both the reaction solver and the slice-by-slice "
        "Macaulay integrator. In addition, Version 2 introduced find_critical_points() to search for sign changes in V(x) and M(x). "
        "The visualization was transformed into a professional 3-panel plot using matplotlib.patches (Rectangles for UDLs, Polygons for UVLs, "
        "angled arrows for forces, and curved arcs for moments)."
    )
    add_bullet_p(doc, "New Loading Capabilities: Uniformly Distributed Loads (UDL), Uniformly Varying Loads (UVL), and Concentrated Couples.", "Upgrades: ")
    add_bullet_p(doc, "Critical Point Tracking: Numerical detection of zero-shear locations and points of contraflexure (M = 0).", "")
    add_bullet_p(doc, "3-Tier Aligned Plots: Synchronized Free Body Diagram (FBD) directly above the SFD and BMD.", "")

    add_body_p(doc,
        "Limitations Encountered in Version 2: "
        "While Version 2 possessed complete mechanical mathematics, it remained strictly CLI-based. Entering complex problems with multiple "
        "loads required dozens of sequential terminal prompts. If a user made a single typographical error on the final load, the entire session "
        "had to be discarded and restarted. Furthermore, data could not be saved to disk, preventing batch verification or problem reuse."
    )

    add_code_block(doc,
"""# sfd_bmd_engine_2.py (Excerpt: Integration of Uniformly Varying Loads - UVL)
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
            M[i] -= moment""",
        caption="Code Snippet 2: Version 2 Continuous Singularity Integration for UVL Profile"
    )

    # Version 3
    add_heading_2(doc, "3.3 Version 3 (sfd_bmd_engine_3.py) – Persistent CSV Architecture & Dual Coordinate System")
    add_body_p(doc,
        "Goal of Version 3: Eliminate repetitive terminal data entry by establishing persistent CSV file import and export capabilities, "
        "incorporating an in-terminal user manual, and supporting dual-reference coordinate specification (distances from left or right ends)."
    )
    add_body_p(doc,
        "Progress & Implementation Details: "
        "Version 3 introduced a robust CSV storage schema featuring distinct section headers: [BEAM], [SUPPORTS], [POINT_LOADS], [UDLS], "
        "[UVLS], and [MOMENTS]. It included load_from_csv() and save_to_csv() routines that allowed engineers to define complex beam problems "
        "in spreadsheet editors (such as Excel or LibreOffice Calc) and solve them instantly. A structured main menu loop was implemented, "
        "and display_manual() provided in-terminal documentation of sign conventions and CSV formatting rules."
    )
    add_bullet_p(doc, "CSV Ingestion & Serialization: Fully reproducible problem definitions saved to standard .csv files.", "Upgrades: ")
    add_bullet_p(doc, "Dual-Coordinate Referencing: Distances can be entered from the left (x = 0) or the right (x = L) in both CLI and CSV.", "")
    add_bullet_p(doc, "High-Res Image Export: Automatic export of analysis diagrams to 300 DPI PNG or vector PDF.", "")

    add_body_p(doc,
        "Limitations Encountered in Version 3: "
        "Although CSV loading functioned well, the interactive CLI input pipeline remained monolithic (a single collect_loads_interactive "
        "function), making it difficult to correct errors during interactive sessions without modifying the CSV file. Furthermore, file path "
        "resolution was sensitive to the terminal's active working directory, which caused 'file not found' errors when executed from outside "
        "the script's folder."
    )

    add_code_block(doc,
"""# sfd_bmd_engine_3.py (Excerpt: Multi-section CSV loading logic)
def load_from_csv(filepath):
    # Reads multi-section beam configuration
    with open(filepath, mode='r', encoding='utf-8') as f:
        reader = csv.reader(f)
        for row in reader:
            if not row or not any(field.strip() for field in row):
                continue
            first_cell = row[0].strip()
            if first_cell.startswith('[') and first_cell.endswith(']'):
                current_section = first_cell.upper()
                continue
            # Parse sections: [BEAM], [SUPPORTS], [POINT_LOADS], [UDLS], [UVLS], [MOMENTS]
            ...""",
        caption="Code Snippet 3: Version 3 Multi-Section CSV Reader"
    )

    # Version 4
    add_heading_2(doc, "3.4 Version 4 (sfd_bmd_engine_4.py) – Final Production-Grade Mechanics Engine")
    add_body_p(doc,
        "Goal of Version 4 (Final Code to be Submitted): Deliver a robust, modular, fault-tolerant engineering engine featuring interactive "
        "review/modification loops, directory-independent path resolution, sub-millimeter root-finding interpolation, and publication-ready graphics."
    )
    add_body_p(doc,
        "Progress & Final Implementation Details: "
        "Version 4 represents the complete milestone software. Key advancements include:"
    )
    add_bullet_p(doc, "Modular Load Collectors: Decomposed monolithic input into collect_point_loads(), collect_udls(), collect_uvls(), and collect_moments() for clean maintainability.", "1. Modular Architecture: ")
    add_bullet_p(doc, "Interactive Review & Verification Loop (review_and_verify): Allows users to review all entered data in a formatted summary, add further loads, edit parameters, or restart the setup before executing the equilibrium solver.", "2. Fault-Tolerant Review Loop: ")
    add_bullet_p(doc, "Directory-Agnostic File Management: Utilizes SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__)) to ensure CSVs and plots are always loaded and saved beside the script, regardless of where the terminal session was launched.", "3. Resilient File Handling: ")
    add_bullet_p(doc, "Sub-Grid Linear Interpolation: Upgraded find_critical_points() to compute exact zero-shear crossing roots via x_zero = x[i] - V[i]*(x[i+1]-x[i])/(V[i+1]-V[i]), achieving sub-millimeter precision for peak bending moment calculations.", "4. Analytical Precision: ")
    add_bullet_p(doc, "Polished Matplotlib Rendering: Added support type indicators, shaded positive/negative color grading (blue/red for SFD, green/orange for BMD), reaction arrows, and dual dimension callouts.", "5. Publication Graphics: ")

    # Detailed code snippets of v4
    add_heading_3(doc, "Core Architectural Snippets of Version 4 (sfd_bmd_engine_4.py)")

    add_code_block(doc,
"""# sfd_bmd_engine_4.py (Core Reaction Solver)
def solve_reactions(length, supports, point_loads, udls, uvls, point_moments):
    \"\"\"
    Computes external support reactions using Newton's laws of static equilibrium:
        Sum of Vertical Forces:  Sigma(Fy) = 0
        Sum of Moments at x = 0: Sigma(M_0) = 0
    \"\"\"
    total_F = sum(pl['mag'] for pl in point_loads)
    total_M_zero = sum(pl['mag'] * pl['pos'] for pl in point_loads)

    # Accumulate UDL force and moment
    for udl in udls:
        span = udl['end'] - udl['start']
        force = udl['intensity'] * span
        centroid = udl['start'] + span / 2.0
        total_F += force
        total_M_zero += force * centroid

    # Accumulate UVL force and moment
    for uvl in uvls:
        span = uvl['end'] - uvl['start']
        force = 0.5 * (uvl['start_w'] + uvl['end_w']) * span
        rel_centroid = (span / 3.0) * ((uvl['start_w'] + 2 * uvl['end_w']) / (uvl['start_w'] + uvl['end_w'])) if (uvl['start_w'] + uvl['end_w']) > 0 else span / 2.0
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
        reactions[f"R_{x_s:.2f}"] = total_F
        reactions[f"M_{x_s:.2f}"] = -(total_M_zero - total_F * x_s)
    elif len(pin_roller) == 2 and len(fixed) == 0:
        pin_roller.sort(key=lambda s: s['pos'])
        x1, x2 = pin_roller[0]['pos'], pin_roller[1]['pos']
        R2 = (total_M_zero - total_F * x1) / (x2 - x1)
        R1 = total_F - R2
        reactions[f"R_{x1:.2f}"] = R1
        reactions[f"R_{x2:.2f}"] = R2
    else:
        raise ValueError("System indeterminate. Provide exactly 1 Fixed or 2 Pinned/Roller supports.")
    return reactions""",
        caption="Code Snippet 4: Version 4 Static Equilibrium Reaction Solver"
    )

    add_code_block(doc,
"""# sfd_bmd_engine_4.py (Sub-Grid Root-Finding for Critical Points)
def find_critical_points(x, V, M):
    \"\"\"
    Numerically identifies key engineering critical points:
        1. Zero-Shear Crossings: Root-finding via linear interpolation where V(x) crosses 0.
        2. Global Maximum Bending Moment: Peak magnitude and exact longitudinal coordinate.
        3. Points of Contraflexure: Locations where M(x) crosses zero (inflection points).
    \"\"\"
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
    return zero_shear_points, M[max_m_idx], x[max_m_idx], contraflexure_points""",
        caption="Code Snippet 5: Version 4 Sub-Grid Linear Interpolation for Critical Points"
    )

    add_code_block(doc,
"""# sfd_bmd_engine_4.py (Interactive Review and Modification Loop)
def review_and_verify(beam_length, supports, point_loads, udls, uvls, point_moments):
    \"\"\"Allows the user to inspect, modify, append, or reset loads before solving.\"\"\"
    while True:
        print("\\n" + "="*65)
        print("                 STEP 6: REVIEW & VERIFY")
        print("="*65)
        print(f"Beam Length: {beam_length:.2f} m")
        print("Supports: " + ", ".join([f"{s['type']} @ {s['pos']:.2f}m" for s in supports]))
        # Summarize all applied loads...
        chk = input("\\nIs there anything left to add or modify? (y/n): ").strip().lower()
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
        choice = get_choice("\\nSelect what to modify:", menu)
        # Handle user choice dynamically...
    return beam_length, supports, point_loads, udls, uvls, point_moments""",
        caption="Code Snippet 6: Version 4 Interactive Review & Verification Pre-Flight Loop"
    )

    # --------------------------------------------------------------------------
    # CHAPTER 4: BENCHMARK VALIDATION ON RK RAJPUT TEXTBOOK PROBLEM
    # --------------------------------------------------------------------------
    add_heading_1(doc, "4. BENCHMARK VALIDATION ON TEXTBOOK PROBLEM")
    add_body_p(doc,
        "To rigorously validate the computational accuracy of Version 4 (sfd_bmd_engine_4.py), the software was tested "
        "against an established benchmark problem sourced from the authoritative textbook 'Strength of Materials' by Dr. R. K. Rajput "
        "(Chapter 4: Shear Force and Bending Moment Diagrams for Beams, Example 4.7)."
    )

    add_heading_2(doc, "4.1 Benchmark Problem Statement (Example 4.7)")
    add_body_p(doc,
        "'Example 4.7. Draw the shear force and bending moment diagrams for the beam shown in Fig. 4.24(a). "
        "Clearly mark the position of the maximum bending moment and determine its magnitude.'"
    )
    add_body_p(doc, "Mechanical Specifications of the Beam (Fig. 4.24(a)):")
    add_bullet_p(doc, "Total Span: L = 6.0 meters, simply supported at point A (left pin, x = 0 m) and point B (right roller, x = 6 m).", "Geometry: ")
    add_bullet_p(doc, "P_C = 1.0 kN downward at point C, located at x = 1.0 m from A.", "Point Load 1: ")
    add_bullet_p(doc, "w = 2.0 kN/m acting downward over a span of 2.0 m, starting at point D (x = 2.0 m) and ending at point E (x = 4.0 m). Total load = 2 kN/m * 2 m = 4.0 kN, acting at centroid x = 3.0 m.", "Distributed Load (UDL): ")
    add_bullet_p(doc, "P_F = 4.0 kN downward at point F, located at x = 5.0 m from A.", "Point Load 2: ")
    add_bullet_p(doc, "A to C = 1.0 m; C to D = 1.0 m; D to E = 2.0 m; E to F = 1.0 m; F to B = 1.0 m (Sum = 6.0 m).", "Segment Breakdown: ")

    # Insert Textbook Image (Q1.jpg)
    q1_img_path = os.path.join(SCRIPT_DIR, "Q1.jpg")
    if os.path.exists(q1_img_path):
        p_img1 = doc.add_paragraph()
        p_img1.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_img1.paragraph_format.space_before = Pt(8)
        p_img1.paragraph_format.space_after = Pt(2)
        doc.add_picture(q1_img_path, width=Inches(4.8))
        # Center the picture paragraph
        doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_cap1 = doc.add_paragraph()
        p_cap1.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_cap1.paragraph_format.space_after = Pt(8)
        r_cap1 = p_cap1.add_run("Figure 1: Benchmark Example 4.7 from 'Strength of Materials' by R. K. Rajput (Question & Solution Diagrams)")
        r_cap1.font.name = 'Calibri'
        r_cap1.font.size = Pt(9.5)
        r_cap1.italic = True
        r_cap1.font.color.rgb = RGBColor(0x55, 0x55, 0x55)

    add_heading_2(doc, "4.2 Input Representation in CSV Format (beam.csv)")
    add_body_p(doc,
        "The benchmark problem was formulated into the engine's structured CSV schema ('beam.csv') as shown in Table 2. "
        "The file defines beam length, boundary supports, applied downward loads, and the intermediate UDL:"
    )

    # Display CSV representation table
    csv_tbl = doc.add_table(rows=12, cols=6)
    csv_tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    csv_headers = ["Section / Field", "Col 1", "Col 2", "Col 3", "Col 4", "Col 5"]
    c_widths = [Inches(1.8), Inches(1.1), Inches(1.1), Inches(1.1), Inches(1.1), Inches(1.1)]

    for c_i, h in enumerate(csv_headers):
        cell = csv_tbl.cell(0, c_i)
        cell.width = c_widths[c_i]
        set_cell_background(cell, "1F4E79")
        set_cell_margins(cell, top=80, bottom=80, left=100, right=100)
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(h)
        r.font.name = 'Calibri'
        r.font.size = Pt(9.5)
        r.bold = True
        r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)

    csv_data = [
        ("[BEAM]", "length_m: 6.0", "", "", "", ""),
        ("[SUPPORTS]", "pinned", "pos_left: 0.0", "pos_right: 6.0", "", ""),
        ("[SUPPORTS]", "roller", "pos_left: 6.0", "pos_right: 0.0", "", ""),
        ("[POINT_LOADS]", "mag_kN: 3.5", "direction: up", "pos_left: 0.0", "pos_right: 6.0", "angle: 90"),
        ("[POINT_LOADS]", "mag_kN: 1.0", "direction: down", "pos_left: 1.0", "pos_right: 5.0", "angle: 90"),
        ("[POINT_LOADS]", "mag_kN: 4.0", "direction: down", "pos_left: 5.0", "pos_right: 1.0", "angle: 90"),
        ("[POINT_LOADS]", "mag_kN: 5.5", "direction: up", "pos_left: 6.0", "pos_right: 0.0", "angle: 90"),
        ("[UDLS]", "intensity: 2.0", "start_left: 2.0", "end_left: 4.0", "start_right: 4.0", "end_right: 2.0"),
        ("[UVLS]", "(None)", "", "", "", ""),
        ("[MOMENTS]", "(None)", "", "", "", ""),
        ("(Note)", "Reactions RA=3.5 kN & RB=5.5 kN or applied loads can be entered directly.", "", "", "", "")
    ]

    for r_i, row in enumerate(csv_data, 1):
        bg = "FFFFFF" if r_i % 2 == 1 else "F4F6F8"
        for c_i, val in enumerate(row):
            cell = csv_tbl.cell(r_i, c_i)
            cell.width = c_widths[c_i]
            set_cell_background(cell, bg)
            set_cell_margins(cell, top=60, bottom=60, left=80, right=80)
            p = cell.paragraphs[0]
            r = p.add_run(val)
            r.font.name = 'Consolas' if c_i > 0 else 'Calibri'
            r.font.size = Pt(8.5)
            r.font.color.rgb = RGBColor(0x33, 0x33, 0x33)
            if c_i == 0:
                r.bold = True

    doc.add_paragraph().paragraph_format.space_after = Pt(6)

    # Analytical Hand Calculations
    add_heading_2(doc, "4.3 Step-by-Step Analytical Closed-Form Derivation")
    add_body_p(doc,
        "To establish absolute benchmark truth, the problem is solved analytically using fundamental principles of statics:"
    )

    add_body_p(doc,
        "Step 1: Calculate Support Reactions\n"
        "Taking moments about support A (x = 0):\n"
        "  Σ M_A = 0\n"
        "  (RB * 6.0) - [ (1.0 kN * 1.0 m) + (2.0 kN/m * 2.0 m * 3.0 m) + (4.0 kN * 5.0 m) ] = 0\n"
        "  6.0 * RB = 1.0 + 12.0 + 20.0 = 33.0 kNm\n"
        "  --> RB = 33.0 / 6.0 = 5.5 kN (Upward)\n\n"
        "Applying vertical force equilibrium (Σ Fy = 0):\n"
        "  RA + RB = 1.0 + (2.0 * 2.0) + 4.0 = 9.0 kN\n"
        "  RA = 9.0 - 5.5 = 3.5 kN (Upward)"
    )

    add_body_p(doc,
        "Step 2: Shear Force Distribution V(x)\n"
        "  - Section A to C (0 < x < 1 m):  V = +RA = +3.5 kN\n"
        "  - Just after point C (x = 1 m): V = 3.5 - 1.0 = +2.5 kN\n"
        "  - Section C to D (1 < x < 2 m):  V = +2.5 kN (constant)\n"
        "  - Section D to E (2 < x < 4 m):  V(x) = 2.5 - 2.0 * (x - 2.0) = 6.5 - 2.0 * x kN\n"
        "    At x = 2 m: V = +2.5 kN\n"
        "    At x = 4 m: V = 2.5 - 2.0 * (2.0) = -1.5 kN\n"
        "    --> Zero Shear Crossing: Setting V(x) = 0:\n"
        "        6.5 - 2.0 * x = 0  ==>  x = 6.5 / 2.0 = 3.25 m (from left support A)\n"
        "        Distance from right support B = 6.0 - 3.25 = 2.75 m\n"
        "  - Section E to F (4 < x < 5 m):  V = -1.5 kN (constant)\n"
        "  - Just after point F (x = 5 m): V = -1.5 - 4.0 = -5.5 kN\n"
        "  - Section F to B (5 < x < 6 m):  V = -5.5 kN (constant)\n"
        "  - At support B (x = 6 m):       V = -5.5 + 5.5 = 0 kN (Closes exactly to zero)"
    )

    add_body_p(doc,
        "Step 3: Bending Moment Distribution M(x) & Peak Moment\n"
        "  - At Support A (x = 0):        M_A = 0 kNm\n"
        "  - At Point C (x = 1.0 m):      M_C = RA * 1.0 = 3.5 * 1.0 = 3.5 kNm\n"
        "  - At Point D (x = 2.0 m):      M_D = (3.5 * 2.0) - (1.0 * 1.0) = 7.0 - 1.0 = 6.0 kNm\n"
        "  - At Zero-Shear Point (x = 3.25 m): Bending moment attains global maximum:\n"
        "      M_max = RA * 3.25 - 1.0 * (3.25 - 1.0) - [ 2.0 * (3.25 - 2.0)² / 2 ]\n"
        "      M_max = (3.5 * 3.25) - (1.0 * 2.25) - [ 2.0 * (1.25)² / 2 ]\n"
        "      M_max = 11.375 - 2.25 - 1.5625 = 7.5625 kNm\n"
        "  - At Point E (x = 4.0 m):      M_E = (3.5 * 4.0) - (1.0 * 3.0) - [ 2.0 * 2.0 * 1.0 ] = 14.0 - 3.0 - 4.0 = 7.0 kNm\n"
        "  - At Point F (x = 5.0 m):      M_F = RB * 1.0 = 5.5 * 1.0 = 5.5 kNm\n"
        "  - At Support B (x = 6.0 m):    M_B = 0 kNm"
    )

    add_heading_2(doc, "4.4 Python Solver Execution & Graphical Output")
    add_body_p(doc,
        "When the benchmark problem is loaded into Version 4 (sfd_bmd_engine_4.py), the engine calculates the equilibrium reactions, "
        "integrates the shear and moment curves, and outputs the following terminal summary:"
    )

    add_code_block(doc,
"""=================================================================
                    CALCULATION SUMMARY
=================================================================

--- SUPPORT REACTIONS ---
   R_0.00: 3.500 kN (Upward reaction at Support A, x = 0.0 m)
   R_6.00: 5.500 kN (Upward reaction at Support B, x = 6.0 m)

--- ZERO SHEAR & PEAK BENDING MOMENT ---
   V = 0 at x = 3.250 m (from right: 2.750 m) --> M = 7.562 kNm
   Global Peak Moment: 7.562 kNm at x = 3.250 m

--- POINTS OF CONTRAFLEXURE (M = 0) ---
   None (Bending moment remains strictly positive/sagging throughout span)""",
        caption="Program Execution Log: Output generated by sfd_bmd_engine_4.py for Example 4.7"
    )

    # Insert Python generated plot (beam.png / 1.pdf)
    beam_img_path = os.path.join(SCRIPT_DIR, "beam.png")
    if os.path.exists(beam_img_path):
        doc.add_picture(beam_img_path, width=Inches(5.8))
        doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_cap2 = doc.add_paragraph()
        p_cap2.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_cap2.paragraph_format.space_after = Pt(8)
        r_cap2 = p_cap2.add_run("Figure 2: Complete 3-Panel Mechanics Visualization (FBD, SFD, BMD) Generated by Python Engine for Example 4.7")
        r_cap2.font.name = 'Calibri'
        r_cap2.font.size = Pt(9.5)
        r_cap2.italic = True
        r_cap2.font.color.rgb = RGBColor(0x55, 0x55, 0x55)

    add_heading_2(doc, "4.5 Quantitative Comparison: Analytical vs. Python Solver")
    add_body_p(doc,
        "Table 3 presents a direct side-by-side comparison between the analytical closed-form solution from R. K. Rajput's textbook "
        "and the numerical output computed by Version 4 of the Python application:"
    )

    # Verification comparison table
    comp_tbl = doc.add_table(rows=8, cols=4)
    comp_tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    comp_headers = ["Parameter / Critical Metric", "Analytical Value (Rajput)", "Python Solver v4 Output", "Relative Error (%)"]
    c_w = [Inches(2.5), Inches(1.8), Inches(1.8), Inches(1.2)]

    for c_i, h in enumerate(comp_headers):
        cell = comp_tbl.cell(0, c_i)
        cell.width = c_w[c_i]
        set_cell_background(cell, "1F4E79")
        set_cell_margins(cell, top=80, bottom=80, left=100, right=100)
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(h)
        r.font.name = 'Calibri'
        r.font.size = Pt(9.5)
        r.bold = True
        r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)

    comparisons = [
        ("Left Reaction RA (at x = 0 m)", "3.500 kN", "3.500 kN", "0.00 %"),
        ("Right Reaction RB (at x = 6 m)", "5.500 kN", "5.500 kN", "0.00 %"),
        ("Zero Shear Location x_zero", "3.250 m", "3.250 m", "0.00 %"),
        ("Distance of V=0 from Right Support", "2.750 m", "2.750 m", "0.00 %"),
        ("Maximum Bending Moment M_max", "7.5625 kNm", "7.562 kNm", "0.00 %"),
        ("Bending Moment at Point D (x = 2 m)", "6.000 kNm", "6.000 kNm", "0.00 %"),
        ("Bending Moment at Point E (x = 4 m)", "7.000 kNm", "7.000 kNm", "0.00 %")
    ]

    for r_i, row in enumerate(comparisons, 1):
        bg = "FFFFFF" if r_i % 2 == 1 else "F4F6F8"
        for c_i, val in enumerate(row):
            cell = comp_tbl.cell(r_i, c_i)
            cell.width = c_w[c_i]
            set_cell_background(cell, bg)
            set_cell_margins(cell, top=60, bottom=60, left=80, right=80)
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER if c_i > 0 else WD_ALIGN_PARAGRAPH.LEFT
            r = p.add_run(val)
            r.font.name = 'Calibri'
            r.font.size = Pt(9.5)
            r.font.color.rgb = RGBColor(0x33, 0x33, 0x33)
            if c_i == 3:
                r.bold = True
                r.font.color.rgb = RGBColor(0x1B, 0x5E, 0x20) # Green for 0.00% error

    doc.add_paragraph().paragraph_format.space_after = Pt(8)

    add_body_p(doc,
        "As demonstrated by Table 3, the Python engine achieves exact 0.00% error relative to the textbook solution across all key "
        "engineering metrics. The zero shear location at x = 3.25 m and peak moment of 7.5625 kNm confirm the absolute numerical accuracy "
        "of the sub-grid linear interpolation and Macaulay integration algorithms implemented in sfd_bmd_engine_4.py."
    )

    # --------------------------------------------------------------------------
    # CHAPTER 5: SOFTWARE QUALITY & CODE DESIGN
    # --------------------------------------------------------------------------
    add_heading_1(doc, "5. SOFTWARE QUALITY & ENGINEERING DESIGN")
    add_body_p(doc,
        "Version 4 of the engine adheres to high software engineering standards. The code is structured for clarity, modularity, "
        "and resilience. Key aspects of the final implementation include:"
    )
    add_bullet_p(doc, "The program verifies that the boundary conditions correspond to a statically determinate system (either 1 fixed support or exactly 2 pinned/roller supports). If an indeterminate or unconstrained system is entered, a descriptive ValueError is raised before computation.", "1. Static Determinacy Verification: ")
    add_bullet_p(doc, "When a point load is applied at an angle theta, the engine automatically resolves the vector into its transverse vertical component (Py = P * sin theta), which contributes to shear and bending, and its axial horizontal component (Px = P * cos theta).", "2. Vector Load Decomposition: ")
    add_bullet_p(doc, "The integration grid utilizes 5,000 discrete points, providing a longitudinal resolution of delta_x = L / 5000 (1.2 mm for a 6 m beam). Critical root-finding linear interpolation further refines zero-crossings down to sub-micrometer precision.", "3. Dense Numerical Grid Convergence: ")
    add_bullet_p(doc, "Full PEP 8 compliant docstrings, section dividers, descriptive variable names, and physics comments explain every mechanics formula and numerical technique.", "4. Documentation & Comments: ")

    # --------------------------------------------------------------------------
    # CHAPTER 6: WHAT IS NEXT TO DO (FUTURE SCOPE)
    # --------------------------------------------------------------------------
    add_heading_1(doc, "6. WHAT IS NEXT TO DO")
    add_body_p(doc,
        "The primary future objective for this project is to make a GUI for the app."
    )
    add_body_p(doc,
        "Currently, sfd_bmd_engine_4.py operates through an interactive command-line interface (CLI) and file-based CSV ingestion. "
        "To make the application more accessible to practicing structural engineers, students, and educators, the next step is to make a GUI for the app. "
        "Developing a Graphical User Interface (GUI) will involve the following enhancements:"
    )
    add_bullet_p(doc, "Designing a desktop interface using frameworks such as PyQt, Tkinter, or CustomTkinter to replace text-based terminal menus with graphical dialogs.", "1. Graphical Framework Implementation: ")
    add_bullet_p(doc, "Building an interactive drawing canvas where users can visually place supports, specify beam spans, and position point loads, distributed loads, and couples using mouse interaction.", "2. Interactive Beam Drafting Canvas: ")
    add_bullet_p(doc, "Enabling live, instantaneous recalculation and re-rendering of the Free Body Diagram, Shear Force Diagram, and Bending Moment Diagram whenever load sliders, positions, or magnitudes are adjusted.", "3. Dynamic Real-Time Plot Updates: ")
    add_bullet_p(doc, "Providing graphical file dialogs for opening, editing, and saving CSV problem files and one-click buttons for exporting high-resolution PDF and PNG engineering calculation sheets.", "4. Integrated Visual File Management: ")

    # --------------------------------------------------------------------------
    # CHAPTER 7: CONCLUSION
    # --------------------------------------------------------------------------
    add_heading_1(doc, "7. CONCLUSION")
    add_body_p(doc,
        "This project successfully developed an automated, mathematically rigorous, and robust Python computational engine "
        "(sfd_bmd_engine_4.py) for the analysis and visualization of Shear Force and Bending Moment Diagrams in statically determinate beams. "
        "Through four evolutionary iterations, the software expanded from a basic point-load calculator into a comprehensive engineering tool "
        "supporting inclined concentrated forces, uniformly distributed loads, uniformly varying loads, and concentrated couples. "
        "Rigorous benchmark testing against Example 4.7 from R. K. Rajput's 'Strength of Materials' proved that the solver's numerical results "
        "match theoretical analytical values with 0.00% error. With persistent CSV data storage, dual-coordinate referencing, and publication-quality "
        "Matplotlib graphics, the engine provides an indispensable computational platform for beam mechanics."
    )

    print(f"Saving final report to '{output_doc_path}'...")
    doc.save(output_doc_path)
    print(f"Saving standard report to '{output_doc_path_std}'...")
    doc.save(output_doc_path_std)
    print("Report creation completed successfully!")

if __name__ == "__main__":
    build_report()
