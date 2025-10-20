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
            if pd.isna(val) or val in ["-", "."]:
                new_col.append("X")
                continue

            val_clean = str(val).replace("/", "").replace("-", "")
            if parent1[i] in val_clean and parent2[i] in val_clean:
                new_col.append("H")
            elif parent1[i] in val_clean:
                new_col.append("A")
            elif parent2[i] in val_clean:
                new_col.append("B")
            else:
                new_col.append("X")
        result[col] = new_col

    return result


# ---- UI ----
app_ui = ui.page_fluid(
    ui.h2("Genotype Encoder (A/B/H/X)"),

    ui.input_text_area("paste_data", ui.HTML(
        "Paste your tab-separated data here<br>"
        "<span style='font-size: 0.9em; color: gray;'>(1st iss the Marker_ID, 2nd and 3rd columns are the genotypes of parent P1 and P2)</span>"
    ),
    "", rows=10, placeholder='''Marker_ID    P1	P2	Ind1	Ind2	Ind3	Ind4	Ind5
SSR1    230	200	230	230/200	230/200	230	200
SSR2    150	122	150	150/122	122	150/122	122''',
                           width="100%"),
    ui.input_action_button("convert_btn", "Convert"),
    ui.hr(),
    ui.output_table("result_table")
)


# ---- Server ----
def server(input, output, session):
    @reactive.Calc
    def data_input():
        
        # If data pasted
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


