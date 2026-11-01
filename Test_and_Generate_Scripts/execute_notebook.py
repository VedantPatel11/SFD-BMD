import os
import sys
import io
import contextlib
import base64
import nbformat
import matplotlib
matplotlib.use('Agg') # Headless execution for saving figures
import matplotlib.pyplot as plt

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ipynb_path = os.path.join(SCRIPT_DIR, "sfd_bmd_engine_4.ipynb")

print(f"Reading '{ipynb_path}'...")
with open(ipynb_path, "r", encoding="utf-8") as f:
    nb = nbformat.read(f, as_version=4)

# Global execution namespace
exec_globals = {
    '__file__': os.path.join(SCRIPT_DIR, "sfd_bmd_engine_4.py"),
    '__name__': '__main__'
}

execution_count = 1

for idx, cell in enumerate(nb.cells):
    if cell.cell_type == "code":
        code = cell.source
        # Filter out %matplotlib inline for standard exec
        clean_lines = []
        for line in code.splitlines():
            if line.strip().startswith("%"):
                continue
            clean_lines.append(line)
        exec_code = "\n".join(clean_lines)

        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()

        print(f"Executing Code Cell #{execution_count} (index {idx})...")
        cell.outputs = []
        plt.close('all') # Reset plots before cell execution

        try:
            with contextlib.redirect_stdout(stdout_capture), contextlib.redirect_stderr(stderr_capture):
                exec(exec_code, exec_globals)
            
            out_text = stdout_capture.getvalue()
            err_text = stderr_capture.getvalue()

            if out_text:
                cell.outputs.append(nbformat.v4.new_output(
                    output_type="stream",
                    name="stdout",
                    text=out_text
                ))
            if err_text:
                cell.outputs.append(nbformat.v4.new_output(
                    output_type="stream",
                    name="stderr",
                    text=err_text
                ))

            # Check if any matplotlib figures were generated
            fig_nums = plt.get_fignums()
            for fnum in fig_nums:
                fig = plt.figure(fnum)
                img_buf = io.BytesIO()
                fig.savefig(img_buf, format='png', dpi=150, bbox_inches='tight')
                img_buf.seek(0)
                img_b64 = base64.b64encode(img_buf.read()).decode('utf-8')
                cell.outputs.append(nbformat.v4.new_output(
                    output_type="display_data",
                    data={
                        "image/png": img_b64,
                        "text/plain": "<Figure size ...>"
                    },
                    metadata={}
                ))
                plt.close(fig)

            cell.execution_count = execution_count
            execution_count += 1

        except Exception as e:
            print(f"Error in Cell {idx}: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)

with open(ipynb_path, "w", encoding="utf-8") as f:
    nbformat.write(nb, f)

print(f"\nAll {execution_count - 1} code cells executed successfully with 0 errors!")
print(f"Updated '{ipynb_path}' with complete cell outputs and rendered inline figures.")
