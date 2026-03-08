"""SPSS dataset constants.

The unique smallest Simple Perfect Squared Square was discovered by
A. J. W. Duijvestijn (1978).
  - Order : 21  (21 distinct sub-squares)
  - Size  : 112 (the enclosing square has side length 112)

Bouwkamp code (from the original paper):
  (50,35,27)(8,19)(15,17,11)(6,24)(29,25,9,2)(7,18)(16)(42)(4,37)(33)
"""

from __future__ import annotations

DUIJVESTIJN_SIZE: int = 112

DUIJVESTIJN_BOUWKAMP: list[list[int]] = [
    [50, 35, 27],
    [8, 19],
    [15, 17, 11],
    [6, 24],
    [29, 25, 9, 2],
    [7, 18],
    [16],
    [42],
    [4, 37],
    [33],
]
