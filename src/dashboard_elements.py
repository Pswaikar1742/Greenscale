def display_metric_card(label, value, delta=None, icon=None):
    """
    Generate an HTML-based metric card for the GreenScale dashboard.

    Args:
        label (str): The label for the metric.
        value (str|int|float): The value to display.
        delta (str, optional): The change in value to display. Defaults to None.
        icon (str, optional): An optional icon to display next to the label. Defaults to None.

    Returns:
        str: An HTML string representing the metric card.
    """
    icon_html = f"<span style='font-size: 1.5em; margin-right: 8px;'>{icon}</span>" if icon else ""
    delta_html = f"<div style='color: #81c784; font-size: 0.9em; margin-top: 4px;'>Δ {delta}</div>" if delta else ""

    html = f"""
    <div style="
        background-color: #1e1e1e;
        border-left: 5px solid #4caf50;
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
        box-shadow: 0px 4px 6px rgba(0, 0, 0, 0.3);
        color: #e0e0e0;
        font-family: 'Arial', sans-serif;
    ">
        <div style="display: flex; align-items: center;">
            {icon_html}
            <div style="font-size: 1.2em; color: #b0bec5;">{label}</div>
        </div>
        <div style="font-size: 2em; color: #4caf50; font-weight: bold;">{value}</div>
        {delta_html}
    </div>
    """
    return html
