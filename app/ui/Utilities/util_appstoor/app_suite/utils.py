def format_indian_currency(value, with_symbol=True):
    """Formats a number in Indian currency notation (e.g., 45,45,454.5 style) with exactly one decimal place."""
    try:
        val = float(value)
    except (ValueError, TypeError):
        return str(value)

    is_negative = val < 0
    val = abs(val)

    # Format to exactly one decimal place
    formatted_float = f"{val:.1f}"
    parts = formatted_float.split(".")
    int_str = parts[0]
    dec_part = parts[1]

    if len(int_str) <= 3:
        formatted_int = int_str
    else:
        # Group from right: last 3 digits, then pairs of 2 digits
        last_three = int_str[-3:]
        remaining = int_str[:-3]

        groups = []
        while len(remaining) > 0:
            groups.append(remaining[-2:])
            remaining = remaining[:-2]

        groups.reverse()
        formatted_int = ",".join(groups) + "," + last_three

    result = f"{formatted_int}.{dec_part}"
    
    if with_symbol:
        result = "₹" + result
        
    if is_negative:
        result = "-" + result

    return result
