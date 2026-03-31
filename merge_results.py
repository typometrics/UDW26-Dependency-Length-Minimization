import pandas as pd
import os
import glob

OUTPUT_DIR = "udw2026_paper"

def merge_csvs(pattern, output_filename):
    files = glob.glob(os.path.join(OUTPUT_DIR, pattern))
    # Filter out the output file itself if it exists
    files = [f for f in files if os.path.basename(f) != output_filename]
    
    if not files:
        print(f"No files found for {pattern}")
        return
    
    print(f"Merging {len(files)} files for {output_filename}...")
    dfs = []
    for f in files:
        try:
            df = pd.read_csv(f)
            dfs.append(df)
        except Exception as e:
            print(f"Error reading {f}: {e}")
    
    if dfs:
        merged_df = pd.concat(dfs, ignore_index=True)
        # Sort if possible
        if "MDD" in merged_df.columns and "Framework" in merged_df.columns:
             merged_df = merged_df.sort_values(["Framework", "MDD"])
        
        out_path = os.path.join(OUTPUT_DIR, output_filename)
        merged_df.to_csv(out_path, index=False)
        print(f"Saved merged file to {out_path} ({len(merged_df)} rows)")
    else:
        print("Empty dataframe list")

if __name__ == "__main__":
    merge_csvs("results_all_[0-9]*.csv", "results_all.csv")
    merge_csvs("results_all_relations_[0-9]*.csv", "results_all_relations.csv")
    merge_csvs("results_all_funlex_[0-9]*.csv", "results_all_funlex.csv")
