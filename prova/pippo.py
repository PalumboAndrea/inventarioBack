text = "ho comprato 3 mele"
entities = [
    [0, 11, "ACTION"],    # "ho comprato"
    [12, 13, "QUANTITY"], # "3"
    [14, 18, "ITEM"]     # "mele"
]

for start, end, label in entities:
    print(f"'{text[start:end]}' -> {label}")
