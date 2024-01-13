#!/usr/bin/python3

from typing import Dict, Tuple

FLAT: str = "♭"
SHARP: str = "♯"

KEY_NAMES: Dict[Tuple[int,str], str] = {
    (0, 'major'): 'C',
    (0, 'minor'): 'Am',
    (1, 'major'): 'G',
    (1, 'minor'): 'Em',
    (2, 'major'): 'D',
    (2, 'minor'): 'Bm',
    (3, 'major'): 'A',
    (3, 'minor'): f'F♯m',
    (4, 'major'): 'E',
    (4, 'minor'): 'C♯m',
    (5, 'major'): 'B',
    (5, 'minor'): f'G♯m',
    (6, 'major'): f'F♯',
    (6, 'minor'): f'D♯m',
    (-1, 'major'): 'F',
    (-1, 'minor'): 'Dm',
    (-2, 'major'): 'Bb',
    (-2, 'minor'): 'Gm',
    (-3, 'major'): 'Eb',
    (-3, 'minor'): 'Cm',
    (-4, 'major'): 'Ab',
    (-4, 'minor'): 'Fm',
    (-5, 'major'): 'Db',
    (-5, 'minor'): 'Bbm',
    (-6, 'major'): 'Gb',
    (-6, 'minor'): 'Ebm',
}
