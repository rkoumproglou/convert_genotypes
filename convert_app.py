# ---- Helper function: convert genotypes ----
def convert_genotypes(df: pd.DataFrame) -> pd.DataFrame:
    result = df.copy()
    parent1 = df.iloc[:, 0].astype(str)
    parent2 = df.iloc[:, 1].astype(str)
        
    for col in df.columns[2:]:
        new_col = []
        for i, val in enumerate(df[col]):
            if pd.isna(val) or val in ["-", "."]:
                new_col.append("X")
                continue

            val_clean = str(val).replace("/", "").replace("-", "").strip()

            p1 = str(parent1[i]).strip()
            p2 = str(parent2[i]).strip()

            # Normalize both alleles by sorting letters for SNPs (e.g., AT == TA)
            val_sorted = "".join(sorted(val_clean))
            parents_sorted = "".join(sorted(p1 + p2))

            # Case 1: heterozygote (contains both alleles, in any order)
            if val_sorted == parents_sorted and p1 != p2:
                new_col.append("H")

            # Case 2: homozygotes for parent 1 or 2
            elif val_clean == p1:
                new_col.append("A")
            elif val_clean == p2:
                new_col.append("B")

            # Case 3: missing or unrecognized
            else:
                new_col.append("X")

        result[col] = new_col

    return result



