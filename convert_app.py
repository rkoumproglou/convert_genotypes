from shiny import App, ui, render, reactive
import pandas as pd
import io
import re

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

            # Clean genotype string (remove separators)
            val_clean = re.sub(r"[/|\-]", "", str(val).strip().upper())

            # Extract parental alleles (e.g., AA -> A)
            p1_alleles = list(set(re.sub(r"[/|\-]", "", parent1[i].strip().upper())))
            p2_alleles = list(set(re.sub(r"[/|\-]", "", parent2[i].strip().upper())))

            # Handle missing or invalid parents
            if len(p1_alleles) == 0 or len(p2_alleles) == 0:
                new_col.append("X")
                continue

            # Offspring alleles
            val_alleles = list(set(val_clean))

            # Heterozygote if offspring has one allele from each parent
            if any(a in val_alleles for a in p1_alleles) and any(a in val_alleles for a in p2_alleles) and p1_alleles != p2_alleles:
                new_col.append("H")
            # Homozygote for parent 1
            elif all(a in p1_alleles for a in val_alleles):
                new_col.append("A")
            # Homozygote for parent 2
            elif all(a in p2_alleles for a in val_alleles):
                new_col.append("B")
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
            "(1st column: Marker ID, 2nd and 3rd columns: parental genotypes P1 and P2)"
            "</span>"
        ),
        "",
        rows=10,
        placeholder='''SNP\tP1\tP2\tInd1\tInd2\tInd3\tInd4
Gm01_138835\tAA\tGG\tAA\tAG\tAG\tAG
Gm01_565991\tAA\tCC\tAA\tAC\tAC\tAC
Gm01_901691\tCC\tTT\tCC\tTC\tTC\tTC''',
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







