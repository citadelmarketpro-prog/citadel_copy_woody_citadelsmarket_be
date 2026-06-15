import humanize

def humanize_compact(value):
    """
    Convert numbers into compact form (1k, 1.5M, 2B).
    """
    text = humanize.intword(value)

    # Replace words with symbols
    text = (
        text.replace(" thousand", "k")
            .replace(" million", "M")
            .replace(" billion", "B")
            .replace(" trillion", "T")
    )
    return text


