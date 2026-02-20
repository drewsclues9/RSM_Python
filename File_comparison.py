import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
import math
import os
from functools import partial

# ---------- Utility functions ----------
def read_excel_with_header_picker(path, sheet_name=0, max_preview_rows=20):
    """
    Read the first max_preview_rows rows with header=None so user can pick header row index (1-based).
    Returns dataframe (header=None) and a best_guess_header_row (1-based).
    """
    # read without header
    try:
        df_none = pd.read_excel(path, sheet_name=sheet_name, header=None, nrows=max_preview_rows, engine=None)
    except Exception:
        # fallback explicit engines
        if path.lower().endswith('.xls'):
            df_none = pd.read_excel(path, sheet_name=sheet_name, header=None, nrows=max_preview_rows, engine='xlrd')
        else:
            df_none = pd.read_excel(path, sheet_name=sheet_name, header=None, nrows=max_preview_rows, engine='openpyxl')

    # heuristic: choose row with most non-null string-like entries as header
    non_null_counts = df_none.apply(lambda col: col.notna().astype(int)).sum(axis=1)
    # choose row with max non-null, break ties by earliest
    best_idx = int(non_null_counts.idxmax())  # 0-based
    # return df_none and header candidate as 1-based
    return df_none, best_idx + 1

def full_read_excel(path, header_row_1based, sheet_name=0):
    """
    Read full sheet applying header row (1-based).
    """
    header_idx = header_row_1based - 1 if header_row_1based is not None else None
    try:
        df = pd.read_excel(path, sheet_name=sheet_name, header=header_idx, engine=None)
    except Exception:
        if path.lower().endswith('.xls'):
            df = pd.read_excel(path, sheet_name=sheet_name, header=header_idx, engine='xlrd')
        else:
            df = pd.read_excel(path, sheet_name=sheet_name, header=header_idx, engine='openpyxl')
    # normalize column names to strings
    df.columns = [str(c).strip() for c in df.columns]
    return df

def normalize_value(v):
    if pd.isna(v):
        return None
    if isinstance(v, str):
        return v.strip()
    return v

def values_equal(a, b, float_tol=1e-6, case_insensitive_strings=True):
    # treat None/NaN equal
    if a is None and b is None:
        return True
    if a is None or b is None:
        return False
    # numeric compare
    try:
        # if both are numeric-like
        if (isinstance(a, (int, float)) or (isinstance(a, str) and a.replace('.', '', 1).isdigit())) and \
           (isinstance(b, (int, float)) or (isinstance(b, str) and b.replace('.', '', 1).isdigit())):
            a_f = float(a)
            b_f = float(b)
            if math.isfinite(a_f) and math.isfinite(b_f):
                return abs(a_f - b_f) <= float_tol
    except Exception:
        pass
    # string compare
    if isinstance(a, str) and isinstance(b, str) and case_insensitive_strings:
        return a.strip().lower() == b.strip().lower()
    return str(a) == str(b)

# ---------- GUI app ----------
class CompareApp:
    def __init__(self, root):
        self.root = root
        root.title("Excel Row Comparator")
        root.geometry("1100x700")
        self.style = ttk.Style()
        self.style.theme_use('clam')

        # state
        self.src_path = None
        self.tgt_path = None
        self.src_preview = None
        self.tgt_preview = None
        self.src_df = None
        self.tgt_df = None
        self.src_header_row = tk.IntVar(value=1)
        self.tgt_header_row = tk.IntVar(value=1)
        self.mapping = {}  # target_col -> source_col or "<skip>"
        self.sheet_name_src = tk.StringVar(value="0")
        self.sheet_name_tgt = tk.StringVar(value="0")

        # Top frame: file selection
        self._build_top_frame()
        # Middle: previews and mapping
        self._build_middle_frame()
        # Bottom: compare controls & summary
        self._build_bottom_frame()
        # Right: progress & summary box
        self._build_right_frame()

    def _build_top_frame(self):
        frm = ttk.Frame(self.root, padding=(8,8))
        frm.pack(fill='x')

        # Source
        src_frame = ttk.Labelframe(frm, text="Source File", padding=(8,8))
        src_frame.pack(side='left', fill='x', expand=True, padx=4)
        ttk.Button(src_frame, text="Select Source Excel...", command=self.select_src).pack(anchor='w')
        ttk.Label(src_frame, text="Sheet (name or 0-index):").pack(anchor='w', pady=(6,0))
        ttk.Entry(src_frame, textvariable=self.sheet_name_src, width=20).pack(anchor='w')
        ttk.Label(src_frame, text="Header row (1-based):").pack(anchor='w', pady=(6,0))
        row_fr = ttk.Frame(src_frame)
        row_fr.pack(anchor='w')
        ttk.Entry(row_fr, textvariable=self.src_header_row, width=6).pack(side='left')
        ttk.Button(row_fr, text="Auto-detect preview", command=self.detect_src_header).pack(side='left', padx=6)

        # Target
        tgt_frame = ttk.Labelframe(frm, text="Target File", padding=(8,8))
        tgt_frame.pack(side='left', fill='x', expand=True, padx=4)
        ttk.Button(tgt_frame, text="Select Target Excel...", command=self.select_tgt).pack(anchor='w')
        ttk.Label(tgt_frame, text="Sheet (name or 0-index):").pack(anchor='w', pady=(6,0))
        ttk.Entry(tgt_frame, textvariable=self.sheet_name_tgt, width=20).pack(anchor='w')
        ttk.Label(tgt_frame, text="Header row (1-based):").pack(anchor='w', pady=(6,0))
        row_fr2 = ttk.Frame(tgt_frame)
        row_fr2.pack(anchor='w')
        ttk.Entry(row_fr2, textvariable=self.tgt_header_row, width=6).pack(side='left')
        ttk.Button(row_fr2, text="Auto-detect preview", command=self.detect_tgt_header).pack(side='left', padx=6)

    def _build_middle_frame(self):
        mf = ttk.Frame(self.root)
        mf.pack(fill='both', expand=True, padx=8, pady=6)

        # Left: previews
        left = ttk.Frame(mf)
        left.pack(side='left', fill='both', expand=True)

        # Source preview
        s_preview_frame = ttk.Labelframe(left, text="Source Preview (first 20 rows)", padding=6)
        s_preview_frame.pack(fill='both', expand=True, padx=2, pady=2)
        self.src_preview_box = tk.Text(s_preview_frame, height=10, wrap='none')
        self.src_preview_box.pack(fill='both', expand=True)
        self.src_preview_box.configure(state='disabled')

        # Target preview
        t_preview_frame = ttk.Labelframe(left, text="Target Preview (first 20 rows)", padding=6)
        t_preview_frame.pack(fill='both', expand=True, padx=2, pady=2)
        self.tgt_preview_box = tk.Text(t_preview_frame, height=10, wrap='none')
        self.tgt_preview_box.pack(fill='both', expand=True)
        self.tgt_preview_box.configure(state='disabled')

        # Right: mapping controls
        right = ttk.Frame(mf, width=420)
        right.pack(side='right', fill='y', padx=4)
        map_frame = ttk.Labelframe(right, text="Field Mapping (Target -> Source)", padding=6)
        map_frame.pack(fill='both', expand=True, pady=2)
        self.map_canvas = tk.Canvas(map_frame)
        self.map_canvas.pack(side='left', fill='both', expand=True)
        self.map_scroll = ttk.Scrollbar(map_frame, orient='vertical', command=self.map_canvas.yview)
        self.map_scroll.pack(side='right', fill='y')
        self.map_canvas.configure(yscrollcommand=self.map_scroll.set)
        self.map_inner = ttk.Frame(self.map_canvas)
        self.map_canvas.create_window((0,0), window=self.map_inner, anchor='nw')
        self.map_inner.bind("<Configure>", lambda e: self.map_canvas.configure(scrollregion=self.map_canvas.bbox("all")))
        # mapping widgets stored for reading
        self.mapping_widgets = {}

        # lower mapping control buttons
        ctrl_fr = ttk.Frame(right)
        ctrl_fr.pack(fill='x', pady=(6,0))
        ttk.Button(ctrl_fr, text="Auto-match identical names", command=self.automatch_columns).pack(side='left')
        ttk.Button(ctrl_fr, text="Clear mapping", command=self.clear_mapping).pack(side='left', padx=4)
        ttk.Button(ctrl_fr, text="Refresh mapping UI", command=self.refresh_mapping_ui).pack(side='left', padx=4)

        # Primary key selection
        pk_frame = ttk.Labelframe(right, text="Primary Key(s) (select one or more)", padding=6)
        pk_frame.pack(fill='both', pady=6, expand=False)
        self.pk_listbox = tk.Listbox(pk_frame, selectmode='multiple', height=6, exportselection=False)
        self.pk_listbox.pack(fill='both', expand=True)

    def _build_bottom_frame(self):
        bf = ttk.Frame(self.root, padding=8)
        bf.pack(fill='x')

        compare_btn = ttk.Button(bf, text="Compare Now", command=self.compare_run)
        compare_btn.pack(side='left')

        ttk.Button(bf, text="Save Last Detailed Diff...", command=self.save_last_diff).pack(side='left', padx=6)

        instructions = (
            "Steps:\n"
            "1) Select source & target files and sheets.\n"
            "2) Use Auto-detect or set Header row (1-based) then press 'Refresh mapping UI'.\n"
            "3) Auto-match names or manually select mapping for each target column.\n"
            "4) Select PK(s) from the list (must be mapped columns).\n"
            "5) Click 'Compare Now'.\n"
            "6) Save detailed diff to Excel with 'Save Last Detailed Diff...'."
        )
        lbl = ttk.Label(bf, text=instructions, justify='left')
        lbl.pack(side='left', padx=12)

    def _build_right_frame(self):
        rf = ttk.Frame(self.root, padding=(6,8))
        rf.pack(side='right', fill='y')

        self.progress = ttk.Progressbar(rf, orient='horizontal', mode='determinate', length=220)
        self.progress.pack(pady=6)
        self.summary_box = tk.Text(rf, width=40, height=20, wrap='word')
        self.summary_box.pack(fill='y', expand=True)
        self.summary_box.configure(state='disabled')

        # storage for last diff
        self.last_diff = None
        self.last_summary = None

    # ---------- file actions ----------
    def select_src(self):
        path = filedialog.askopenfilename(title="Select source Excel file", filetypes=[("Excel files","*.xlsx *.xls"),("All files","*.*")])
        if not path:
            return
        self.src_path = path
        self.detect_src_header()
        self.refresh_mapping_ui()

    def select_tgt(self):
        path = filedialog.askopenfilename(title="Select target Excel file", filetypes=[("Excel files","*.xlsx *.xls"),("All files","*.*")])
        if not path:
            return
        self.tgt_path = path
        self.detect_tgt_header()
        self.refresh_mapping_ui()

    def detect_src_header(self):
        if not self.src_path:
            messagebox.showinfo("No source file", "Please select a source file first.")
            return
        try:
            preview_none, guess = read_excel_with_header_picker(self.src_path, sheet_name=self._parse_sheet(self.sheet_name_src.get()))
            self.src_preview = preview_none
            # show preview
            self._show_preview(self.src_preview_box, preview_none)
            self.src_header_row.set(guess)
            messagebox.showinfo("Header detected", f"Suggested header row for source: {guess} (1-based). Adjust if wrong.")
        except Exception as e:
            messagebox.showerror("Error reading source", str(e))

    def detect_tgt_header(self):
        if not self.tgt_path:
            messagebox.showinfo("No target file", "Please select a target file first.")
            return
        try:
            preview_none, guess = read_excel_with_header_picker(self.tgt_path, sheet_name=self._parse_sheet(self.sheet_name_tgt.get()))
            self.tgt_preview = preview_none
            self._show_preview(self.tgt_preview_box, preview_none)
            self.tgt_header_row.set(guess)
            messagebox.showinfo("Header detected", f"Suggested header row for target: {guess} (1-based). Adjust if wrong.")
        except Exception as e:
            messagebox.showerror("Error reading target", str(e))

    def _show_preview(self, text_widget, df_preview):
        text_widget.configure(state='normal')
        text_widget.delete('1.0','end')
        if df_preview is None:
            text_widget.insert('end', "(no preview)")
        else:
            # present as tab-separated
            for i, row in df_preview.iterrows():
                row_str = "\t".join([str(x) if not pd.isna(x) else "" for x in row.tolist()])
                text_widget.insert('end', f"{i+1}\t{row_str}\n")
        text_widget.configure(state='disabled')

    def refresh_mapping_ui(self):
        # read full df's using header rows
        if not self.src_path or not self.tgt_path:
            # clear mapping UI
            for w in self.map_inner.winfo_children():
                w.destroy()
            self.mapping_widgets = {}
            self.pk_listbox.delete(0,'end')
            return

        try:
            src_df = full_read_excel(self.src_path, header_row_1based=self.src_header_row.get(), sheet_name=self._parse_sheet(self.sheet_name_src.get()))
            tgt_df = full_read_excel(self.tgt_path, header_row_1based=self.tgt_header_row.get(), sheet_name=self._parse_sheet(self.sheet_name_tgt.get()))
        except Exception as e:
            messagebox.showerror("Error reading files", str(e))
            return

        self.src_df = src_df
        self.tgt_df = tgt_df

        src_cols = list(src_df.columns)
        tgt_cols = list(tgt_df.columns)

        # default mapping: by identical names
        self.mapping = {}
        for tc in tgt_cols:
            if tc in src_cols:
                self.mapping[tc] = tc
            else:
                self.mapping[tc] = "<skip>"

        # build UI list: each row shows target col label and combobox with source cols
        for w in self.map_inner.winfo_children():
            w.destroy()
        self.mapping_widgets = {}
        idx = 0
        for tc in tgt_cols:
            row = ttk.Frame(self.map_inner)
            row.grid(row=idx, column=0, sticky='we', pady=1, padx=2)
            ttk.Label(row, text=tc, width=30).pack(side='left')
            cb = ttk.Combobox(row, values=["<skip>"] + src_cols, width=30)
            cb.pack(side='left', padx=4)
            cb.set(self.mapping.get(tc, "<skip>"))
            self.mapping_widgets[tc] = cb
            idx += 1

        # populate PK listbox with mapped columns (target side)
        self.pk_listbox.delete(0,'end')
        for tc in tgt_cols:
            # only allow those that are mapped to something
            self.pk_listbox.insert('end', tc)

    def automatch_columns(self):
        if not self.src_df or not self.tgt_df:
            messagebox.showinfo("Missing files", "Load both files and Refresh mapping UI first.")
            return
        src_cols = list(self.src_df.columns)
        for tc, cb in self.mapping_widgets.items():
            # try case-insensitive exact match
            match = next((s for s in src_cols if s.strip().lower() == tc.strip().lower()), None)
            if match:
                cb.set(match)

    def clear_mapping(self):
        for tc, cb in self.mapping_widgets.items():
            cb.set("<skip>")

    def _parse_sheet(self, sheet_str):
        # if input is digit-like return int else pass string
        if sheet_str is None:
            return 0
        s = sheet_str.strip()
        if s == "":
            return 0
        if s.isdigit():
            return int(s)
        return s

    # ---------- compare ----------
    def compare_run(self):
        """
        Robust compare runner with per-field summary:
        - Ensures src_df and tgt_df are loaded (attempts refresh if not).
        - Builds mapping from mapping_widgets (defensive).
        - Validates PK selection and mapping.
        - Performs outer merge and per-cell comparison, updating progress.
        - Collects per-field match/mismatch counts and stores as DataFrame
        in self.last_field_summary for UI display and saving.
        """
        # --- Ensure dataframes are loaded; try auto-refresh if needed ---
        need_refresh = False
        if not isinstance(self.src_df, pd.DataFrame) or not isinstance(self.tgt_df, pd.DataFrame):
            need_refresh = True

        if need_refresh:
            try:
                # This will attempt to read the Excel files into self.src_df/self.tgt_df
                self.refresh_mapping_ui()
            except Exception as e:
                messagebox.showerror("Load error", f"Could not load files: {e}")
                return

        # Re-check explicitly after attempted refresh
        if not isinstance(self.src_df, pd.DataFrame) or not isinstance(self.tgt_df, pd.DataFrame):
            messagebox.showinfo("Missing files", "Please select source and target files, set header rows, and click 'Refresh mapping UI' before comparing.")
            return

        # --- Build mapping from UI widgets (defensive) ---
        if not hasattr(self, "mapping_widgets") or not self.mapping_widgets:
            messagebox.showinfo("Mapping missing", "No mapping UI found. Click 'Refresh mapping UI' to load columns and create mappings.")
            return

        mapping = {}
        for tc, cb in self.mapping_widgets.items():
            # cb may be a ttk.Combobox or similar; guard against None
            val = "<skip>"
            try:
                val = cb.get().strip() if cb.get() is not None else "<skip>"
            except Exception:
                val = "<skip>"
            mapping[tc] = val

        # --- Primary key selection validation ---
        sel = self.pk_listbox.curselection()
        if not sel:
            messagebox.showinfo("Primary key required", "Please select one or more primary key columns from the PK list.")
            return
        pk_target_cols = [self.pk_listbox.get(i) for i in sel]

        # ensure PKs are mapped to source columns
        unmapped_pks = [pk for pk in pk_target_cols if mapping.get(pk, "<skip>") in ("", "<skip>", None)]
        if unmapped_pks:
            messagebox.showerror("PK mapping missing", f"The following PK(s) are not mapped to source columns: {', '.join(unmapped_pks)}.\nMap them and try again.")
            return

        # --- Build src_renamed (target-named) DataFrame based on mapping ---
        src_renamed = pd.DataFrame(index=self.src_df.index)  # start with same index (will be re-merged)
        for tgt_col, src_col in mapping.items():
            if src_col and src_col != "<skip>" and src_col in self.src_df.columns:
                src_renamed[tgt_col] = self.src_df[src_col]
            else:
                # keep column present but filled with NA to preserve target universe
                src_renamed[tgt_col] = pd.NA

        # Build target subset with the same target columns universe
        tgt_keep = list(mapping.keys())
        try:
            tgt_only_df = self.tgt_df.copy()[tgt_keep]
        except Exception as e:
            messagebox.showerror("Target read error", f"Could not select target columns: {e}")
            return

        # --- Merge on PK(s) with indicator ---
        try:
            merged = tgt_only_df.merge(src_renamed, on=pk_target_cols, how='outer', suffixes=('_tgt','_src'), indicator=True)
        except Exception as e:
            messagebox.showerror("Merge error", f"Could not merge on PK(s): {pk_target_cols}\nError: {e}")
            return

        # Determine columns to compare (exclude skipped)
        compare_cols = [c for c in mapping.keys() if mapping.get(c) and mapping.get(c) != "<skip>"]
        if not compare_cols:
            messagebox.showinfo("Nothing to compare", "No mapped columns to compare. Map at least one column and try again.")
            return

        # --- Initialize per-field stats ---
        per_field_stats = {}
        for col in compare_cols:
            per_field_stats[col] = {"matches": 0, "mismatches": 0, "total": 0}

        # --- Setup progress ---
        total_rows = len(merged)
        total_work = max(1, total_rows) * len(compare_cols)
        self.progress['maximum'] = total_work
        self.progress['value'] = 0

        details = []
        total_mismatch_cells = 0

        # --- Row-by-row compare ---
        for idx, row in merged.iterrows():
            row_detail = {}
            # include pk values
            for pk in pk_target_cols:
                row_detail[pk] = row.get(pk)
            row_detail['_merge'] = row.get('_merge')
            row_mismatch_count = 0

            for col in compare_cols:
                val_tgt = row.get(f"{col}_tgt")
                val_src = row.get(f"{col}_src")
                n_tgt = normalize_value(val_tgt)
                n_src = normalize_value(val_src)
                equal = values_equal(n_src, n_tgt)

                # update details
                row_detail[f"{col}__tgt"] = val_tgt
                row_detail[f"{col}__src"] = val_src
                row_detail[f"{col}__match"] = bool(equal)

                # update per-field stats
                per_field_stats[col]["total"] += 1
                if equal:
                    per_field_stats[col]["matches"] += 1
                else:
                    per_field_stats[col]["mismatches"] += 1
                    row_mismatch_count += 1

                # advance progress one cell
                try:
                    self.progress['value'] += 1
                except Exception:
                    pass

            row_detail['_mismatch_count'] = row_mismatch_count
            total_mismatch_cells += row_mismatch_count
            details.append(row_detail)

            # allow UI redraw
            self.root.update_idletasks()

        # --- Build results ---
        details_df = pd.DataFrame(details)

        only_in_tgt = int((merged['_merge'] == 'left_only').sum())
        only_in_src = int((merged['_merge'] == 'right_only').sum())
        in_both = int((merged['_merge'] == 'both').sum())
        total_cells_compared = total_rows * len(compare_cols)
        percent_matching_cells = 100.0 * (1 - total_mismatch_cells / total_cells_compared) if total_cells_compared > 0 else 100.0

        summary = {
            "total_rows_merged": int(total_rows),
            "rows_only_in_target": only_in_tgt,
            "rows_only_in_source": only_in_src,
            "rows_in_both": in_both,
            "fields_compared_per_row": len(compare_cols),
            "total_cells_compared": int(total_cells_compared),
            "total_mismatch_cells": int(total_mismatch_cells),
            "percent_matching_cells": float(percent_matching_cells),
            "primary_keys": pk_target_cols,
            "mapped_fields_count": len(compare_cols)
        }

        # --- Build field-level summary DataFrame ---
        rows = []
        for col, stats in per_field_stats.items():
            total = stats["total"]
            matches = stats["matches"]
            mismatches = stats["mismatches"]
            pct = (100.0 * matches / total) if total > 0 else None
            rows.append({
                "field": col,
                "matches": int(matches),
                "mismatches": int(mismatches),
                "total_compared": int(total),
                "percent_match": round(pct, 2) if pct is not None else None
            })
        field_summary_df = pd.DataFrame(rows).sort_values(by="percent_match", ascending=False).reset_index(drop=True)

        # store last results and show summary
        self.last_diff = details_df
        self.last_summary = summary
        self.last_field_summary = field_summary_df

        # show summary in UI (top-level + per-field)
        self._show_summary(summary)

        # append per-field summary to summary box
        try:
            self.summary_box.configure(state='normal')
            self.summary_box.insert('end', "\n\nField-level match percentages:\n")
            for _, r in field_summary_df.iterrows():
                pf = f"{r['field']}: {r['percent_match'] if r['percent_match'] is not None else 'N/A'}% ({r['matches']}/{r['total_compared']})"
                self.summary_box.insert('end', pf + "\n")
            self.summary_box.configure(state='disabled')
        except Exception:
            pass

        messagebox.showinfo("Compare finished", f"Completed compare. {total_mismatch_cells} mismatched cells found. See summary at right and save details if needed.")



    def _show_summary(self, summary):
        self.summary_box.configure(state='normal')
        self.summary_box.delete('1.0','end')
        lines = [
            f"Total merged rows: {summary['total_rows_merged']}",
            f"Rows only in target: {summary['rows_only_in_target']}",
            f"Rows only in source: {summary['rows_only_in_source']}",
            f"Rows in both: {summary['rows_in_both']}",
            f"Mapped fields compared: {summary['mapped_fields_count']}",
            f"Total cells compared: {summary['total_cells_compared']}",
            f"Total mismatched cells: {summary['total_mismatch_cells']}",
            f"Percent matching cells: {summary['percent_matching_cells']:.2f}%",
            "",
            f"Primary keys: {', '.join(summary['primary_keys'])}"
        ]
        self.summary_box.insert('end', "\n".join(lines))
        self.summary_box.configure(state='disabled')

    def save_last_diff(self):
        if self.last_diff is None:
            messagebox.showinfo("No results", "No comparison results to save. Run a compare first.")
            return
        path = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel workbook","*.xlsx")], title="Save detailed diff as")
        if not path:
            return
        try:
            with pd.ExcelWriter(path, engine='openpyxl') as writer:
                # summary as dataframe
                sum_df = pd.DataFrame(list(self.last_summary.items()), columns=['metric','value'])
                sum_df.to_excel(writer, sheet_name='Summary', index=False)
                # details
                self.last_diff.to_excel(writer, sheet_name='Details', index=False)
                # field-level summary (new sheet)
                if hasattr(self, "last_field_summary") and self.last_field_summary is not None:
                    # write as-is
                    self.last_field_summary.to_excel(writer, sheet_name='FieldSummary', index=False)
            messagebox.showinfo("Saved", f"Detailed diff and field summary saved to {path}")
        except Exception as e:
            messagebox.showerror("Save error", str(e))



# ---------- main ----------
def main():
    root = tk.Tk()
    app = CompareApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
