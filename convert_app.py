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
            if pd.isna(val) or val in ["-", ".", ""]:
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

            # Normalize by sorting (so AT == TA, 230/200 == 200/230)
            val_sorted = "".join(sorted(val_clean))
            parents_sorted = "".join(sorted(p1 + p2))

            # Case 1: heterozygote (contains both alleles, in any order)
            if (
                (p1 != p2)
                and (p1 in val_clean or p2 in val_clean)
                and val_sorted == parents_sorted
            ):
                new_col.append("H")

            # Case 2: homozygote for parent 1
            elif val_clean == p1:
                new_col.append("A")

            # Case 3: homozygote for parent 2
            elif val_clean == p2:
                new_col.append("B")

            # Case 4: if contains one parental allele but not matching both — still A or B
            elif p1 in val_clean and p2 not in val_clean:
                new_col.append("A")
            elif p2 in val_clean and p1 not in val_clean:
                new_col.append("B")

            # Case 5: unrecognized or missing
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
SNP1\tA\tT\tA\tA/T\tT/A\tA\tT''',
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

