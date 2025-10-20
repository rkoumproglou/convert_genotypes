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
            if pd.isna(val) or str(val).strip() in ["-", ".", "", "NA"]:
                new_col.append("X")
                continue

            # Clean genotype string
            val_clean = (
                str(val)
                .replace("/", "")
                .replace("-", "")
                .replace("|", "")
                .strip()
                .upper()
            )

            p1 = str(parent1[i]).strip().upper()
            p2 = str(parent2[i]).strip().upper()

            # Clean parental alleles (remove separators if any)
            p1_clean = p1.replace("/", "").replace("-", "").replace("|", "")
            p2_clean = p2.replace("/", "").replace("-", "").replace("|", "")

            # Handle missing parents
            if p1_clean == "" or p2_clean == "":
                new_col.append("X")
                continue

            # Sort alleles so order doesn’t matter (AT == TA, 230200 == 200230)
            val_sorted = "".join(sorted(val_clean))
            p1_sorted = "".join(sorted(p1_clean))
            p2_sorted = "".join(sorted(p2_clean))

            # Distinguish heterozygotes (H)
            # If offspring genotype contains both parental alleles, mark as H
            if p1_clean != p2_clean and all(allele in val_clean for allele in (p1_clean, p2_clean)):
                new_col.append("H")

            # Homozygotes for parent 1 or parent 2
            elif val_sorted == p1_sorted:
                new_col.append("A")
            elif val_sorted == p2_sorted:
                new_col.append("B")

            # If partial match (e.g., one allele)
            elif any(allele in val_clean for allele in p1_clean) and not any(allele in val_clean for allele in p2_clean):
                new_col.append("A")
            elif any(allele in val_clean for allele in p2_clean) and not any(allele in val_clean for allele in p1_clean):
                new_col.append("B")

            # Unrecognized genotype
            else:
                new_col.append("X")

        result[col] = new_col

    return result


# ---- UI ----
app_ui = ui.page_fluid(
    ui.h2("Genotype Encoder (A / B / H / X)"),

    ui.input_text_area(
        "paste_data",
        ui.HTML(
            "Paste your tab-separated data here<br>"
            "<span style='font-size: 0.9em; color: gray;'>"
            "(The 1st column is the Marker_ID, 2nd and 3rd columns are the genotypes of parent P1 and P2)"
            "</span>"
        ),
        "",
        rows=10,
        placeholder='''Marker_ID\tP1\tP2\tInd1\tInd2\tInd3\tInd4\tInd5
SSR1\t230\t200\t230\t230/200\t230/200\t230\t200
SNP1\tA\tT\tA\tA/T\tT/A\tA\tT
SNP2\tA\tC\tA\tAC\tCC\tC\tAA''',
        width="100%",
    ),

    ui.input_action_button("convert_btn", "Convert"),
    ui.hr(),
    ui.output_table("result_table"),
    ui.download_button("download", "Download CSV")
)


# ---- Server ----
def server(input, output, session):
    @reactive.Calc
    def data_input():
        pasted = input.paste_data()
        if pasted.strip():
            try:
                df = pd.read_csv(io.StringIO(pasted), sep="\t", header=0, dtype=str, index_col=0)
                return df
            except Exception:
                return None
        return None

    @reactive.Calc
    @reactive.event(input.convert_btn)
    def converted():
        df = data_input()
        if df is None:
            return None
        return convert_genotypes(df)

    @output
    @render.table
    def result_table():
        df = converted()
        if df is None:
            return pd.DataFrame({"Message": ["Please paste valid tab-separated data."]})
        df.reset_index(inplace=True)
        return df

    @output
    @render.download(filename="encoded_genotypes.csv")
    def download():
        df = converted()
        if df is None:
            yield b""
        else:
            yield df.to_csv(index=False).encode("utf-8")


# ---- Run App ----
app = App(app_ui, server)





