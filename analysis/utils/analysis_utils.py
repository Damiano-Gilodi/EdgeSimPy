def build_sla_summary(df, group_cols):
    if isinstance(group_cols, str):
        group_cols = [group_cols]

    summary = (
        df.groupby(group_cols)
        .agg(
            Runs=("Run", "count"),
            Violations=("SLA_Violation", "sum"),
            Violation_Rate=("SLA_Violation", "mean"),
            Mean_Total_Delay=("Total Delay", "mean"),
            Median_Total_Delay=("Total Delay", "median"),
            Max_Total_Delay=("Total Delay", "max"),
            Mean_SLA_Margin_Perc=("SLA_Margin_Perc", "mean"),
            Median_SLA_Margin_Perc=("SLA_Margin_Perc", "median"),
            Min_SLA_Margin_Perc=("SLA_Margin_Perc", "min"),
            Max_SLA_Margin_Perc=("SLA_Margin_Perc", "max"),
            Mean_Violation_Amount=("Violation_Amount", "mean"),
            Max_Violation_Amount=("Violation_Amount", "max"),
        )
        .reset_index()
    )

    summary["Violation_Rate"] = summary["Violation_Rate"] * 100

    safe_summary = (
        df[~df["SLA_Violation"]]
        .groupby(group_cols)
        .agg(
            Mean_Safe_Margin_Perc=("SLA_Margin_Perc", "mean"),
            Median_Safe_Margin_Perc=("SLA_Margin_Perc", "median"),
            Max_Safe_Margin_Perc=("SLA_Margin_Perc", "max"),
        )
        .reset_index()
    )

    viol_summary = (
        df[df["SLA_Violation"]]
        .groupby(group_cols)
        .agg(
            Mean_Violating_Margin_Perc=("SLA_Margin_Perc", "mean"),
            Median_Violating_Margin_Perc=("SLA_Margin_Perc", "median"),
        )
        .reset_index()
    )

    summary = summary.merge(safe_summary, on=group_cols, how="left")
    summary = summary.merge(viol_summary, on=group_cols, how="left")

    summary[["Mean_Violating_Margin_Perc", "Median_Violating_Margin_Perc"]] = summary[["Mean_Violating_Margin_Perc", "Median_Violating_Margin_Perc"]].fillna(0)

    return summary.round(3)


def get_padded_ylim(series, padding_ratio=0.05):
    y_min = series.min()
    y_max = series.max()
    y_range = y_max - y_min
    padding = y_range * padding_ratio if y_range > 0 else 1
    return y_min - padding, y_max + padding
