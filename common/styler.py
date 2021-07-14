import dataclasses
import pandas as pd
from typing import List


@dataclasses.dataclass
class Formatter:
    short_name: str
    rus_name: str
    format: str = None


def style_df(df: pd.DataFrame, style_dict: dict, return_only=True):
    styles = to_formatter(style_dict)
    cols = [f.short_name for f in styles]
    rename_cols = {f.short_name: f.rus_name for f in styles}
    format_cols = {f.rus_name: f.format for f in styles if f.format}
    styled_df = df[cols]\
        .rename(rename_cols, axis=1)\
        .style\
        .format(format_cols)
    return styled_df


def to_formatter(style_dict: dict) -> List[Formatter]:
    return [Formatter(k, v[0], v[1]) for k, v in style_dict.items()]
