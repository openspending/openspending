from itertools import cycle 

DEFAULT_PALETTE = [
    "#CA221D",
    "#C22769",
    "#3F93E1",
    "#481B79",
    "#6AAC32",
    "#42928F",
    "#D32645",
    "#CD531C",
    "#EDC92D",
    "#A5B425",
    "#211D79",
    "#449256",
    "#7A2077",
    "#CA221D",
    "#E29826",
    "#44913D",
    "#2458A3",
    "#2458A3",
    "#14388C"
]

DEFAULT_COLOR = "#607890"

def palette_colors(num):
    colors = []
    for i, color in enumerate(cycle(DEFAULT_PALETTE)):
        if i >= num:
            return colors
        colors.append(color)

def tuple_to_hex(tup):
    return "#" + "%02x%02x%02x" % (int(tup[0]), int(tup[1]), int(tup[2]))
