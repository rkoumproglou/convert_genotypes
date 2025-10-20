from shiny import App, ui, render, reactive
import pandas as pd
import io

# ---- Helper function: convert genotypes ----
def convert_genotypes(df: pd.DataFrame) -> pd.DataFrame:
    result = df.copy()
    parent1 = df.iloc[:, 0].astype(str)
    parent2 = df.iloc[:, 1].astype(str)
        
    for col in df.columns[2:]:
        new_col = []
        for i, val in enumerate(df[col]):
            if pd.isna(val) or str(val).strip() in ["-", ".", ""]:
                new_col.append("X")
                continue

            val_clean = (
                str(val)
                .replace("/", "")
                .replace("-", "")
                .replace("|", "")
                .replace(" ", "")
                .upper()
            )

            p1 = str(parent1[i]).replace("/", "").replace("-", "").replace("|", "").strip().upper()
            p2 = str(parent2[i]).replace("/", "").replace("-", "").replace("|", "").strip().upper()

            # Sort letters to handle reversed SNPs (e.g., AT == TA)
            val_sorted = "".join(sorted(val_clean))
            parents_sorted = "".join(sorted(p1 + p2))

            # Case 1: heterozygote (both alleles, any order)
            if val_sorted == parents_sorted and p1 != p2:
                new_col.append("H")

            # Case 2: homozygote for Parent 1 or Parent 2
            elif val_clean == p1:
                new_col.append("A")
            elif val_clean == p2:
                new_col.append("B")

            # Case 3: missing or unrecognized
            else:
                new_col.append("X")

        result[col] = new_col

    return result


# ---- UI ----
app_ui = ui.page_fluid(
    ui.h2("Genotype Encoder (A/B/H/X)"),

    ui.input_text_area(
        "paste_data",
        ui.HTML(
            "Paste your tab-separated data here<br>"
            "<span style='font-size: 0.9em; color: gray;'>(The 1st column is the Marker_ID, 2nd and 3rd columns are the genotypes of parent P1 and P2)</span>"
        ),
        "",
        rows=10,
        placeholder='''Marker_ID\tP1\tP2\tInd1\tInd2\tInd3\tInd4\tInd5
SSR1\t230\t200\t230\t230/200\t230/200\t230\t200
SNP1\tA\tT\tA/T\tT\tAT\tA\tT''',
        width="100%",
    ),
    ui.input_action_button("convert_btn", "Convert"),
    ui.hr(),
    ui


 



