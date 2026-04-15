import os

import pandas as pd


def load_dataset(input_path: str) -> pd.DataFrame:
    input_ext = os.path.splitext(input_path)[1].lower()
    read_kwargs = {"dtype": str, "keep_default_na": False}

    if input_ext in [".xlsx", ".xls"]:
        return pd.read_excel(input_path, **read_kwargs)

    try:
        return pd.read_csv(input_path, encoding="utf-8", **read_kwargs)
    except UnicodeDecodeError:
        return pd.read_csv(input_path, encoding="latin1", **read_kwargs)

