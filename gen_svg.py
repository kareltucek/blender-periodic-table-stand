#!/usr/bin/env python3
"""Generate per-column SVGs of the 3D periodic table (text converted to paths by Inkscape)."""

import subprocess
import tempfile
from pathlib import Path

CELL = 20.0  # mm
RING = 1.0  # mm, width of the relief frame
FONT = "Nimbus Sans"
SYMBOL_SIZE = 9.0  # mm
SYMBOL_BASELINE = 15.5  # mm from cell top
NUMBER_SIZE = 4.0  # mm
NUMBER_X = 2.0
NUMBER_BASELINE = 5.5

OUT = Path(__file__).parent / "svg"

SYMBOLS = """n H He Li Be B C N O F Ne Na Mg Al Si P S Cl Ar K Ca Sc Ti V Cr Mn Fe Co Ni Cu Zn Ga Ge As Se Br Kr
Rb Sr Y Zr Nb Mo Tc Ru Rh Pd Ag Cd In Sn Sb Te I Xe Cs Ba La Ce Pr Nd Pm Sm Eu Gd Tb Dy Ho Er Tm Yb Lu
Hf Ta W Re Os Ir Pt Au Hg Tl Pb Bi Po At Rn Fr Ra Ac Th Pa U Np Pu Am Cm Bk Cf Es Fm Md No Lr
Rf Db Sg Bh Hs Mt Ds Rg Cn Nh Fl Mc Lv Ts Og""".split()

# Columns as lists of atomic numbers, top to bottom.
TOWER = [[0, 2, 10, 18, 36, 54, 86, 118], [1]]
MAIN = [[3, 11, 19, 37, 55, 87], [4, 12, 20, 38, 56, 88], [5, 13]] + [[z, z + 8, z + 26, z + 44, z + 76, z + 108] for z in range(6, 10)]
TRANSITION = [[21, 39]] + [[z, z + 18, z + 50, z + 82] for z in range(22, 32)]
FBLOCK = [[z, z + 32] for z in range(57, 72)]
COLUMNS = TOWER + MAIN + TRANSITION + FBLOCK


def svg(height, body):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{CELL}mm" height="{height}mm" viewBox="0 0 {CELL} {height}">\n'
        f"{body}\n</svg>\n"
    )


def square(y):
    return f'<path d="M0,{y} H{CELL} V{y + CELL} H0 Z"/>'


def ring(y):
    a, b = RING, CELL - RING
    return f'<path fill-rule="evenodd" d="M0,{y} H{CELL} V{y + CELL} H0 Z M{a},{y + a} V{y + b} H{b} V{y + a} Z"/>'


def text(z, y):
    style = f"font-family:'{FONT}';font-weight:bold"
    return (
        f'<text x="{NUMBER_X}" y="{y + NUMBER_BASELINE}" style="{style};font-size:{NUMBER_SIZE}px">{z}</text>\n'
        f'<text x="{CELL / 2}" y="{y + SYMBOL_BASELINE}" text-anchor="middle" style="{style};font-size:{SYMBOL_SIZE}px">{SYMBOLS[z]}</text>'
    )


def main():
    assert len(SYMBOLS) == 119 and sorted(z for c in COLUMNS for z in c) == list(range(119))
    OUT.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        for i, column in enumerate(COLUMNS, 1):
            name = f"col-{i:02d}-{SYMBOLS[column[0]]}"
            height = CELL * len(column)
            ys = [CELL * row for row in range(len(column))]
            (OUT / f"{name}-frame.svg").write_text(svg(height, "\n".join(square(y) for y in ys)))
            raw = Path(tmp) / f"{name}.svg"
            raw.write_text(svg(height, "\n".join(ring(y) + "\n" + text(z, y) for z, y in zip(column, ys))))
            subprocess.run(
                ["inkscape", str(raw), "--export-text-to-path", "--export-plain-svg", f"--export-filename={OUT / f'{name}-text.svg'}"],
                check=True,
            )
            print(name)


if __name__ == "__main__":
    main()
