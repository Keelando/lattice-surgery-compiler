from rotation import *
from lattice_surgery_computation_composer import LatticeSurgeryComputationComposer, PatchInitializer
from typing import *
import patches
from fractions import Fraction


class Rotation:
    def __init__(self, pauli_operators : List[patches.PauliMatrix], angle: Fraction):
        self.pauli_operators = pauli_operators
        self.angle = angle

class Measurement:
    def __init__(self, pauli_operators : List[patches.PauliMatrix]):
        self.pauli_operators = pauli_operators


def pauli_rotation_to_lattice_surgery(circuit : List[Union[Rotation,Measurement]]) -> LatticeSurgeryComputationComposer:

    lscc = LatticeSurgeryComputationComposer(PatchInitializer.simpleLayout(5));

    for op in circuit:
        if isinstance(op,Rotation):
            # Section 1.1 of Litinski's Game of Surface Codes
            if op.angle == Fraction(1,2):
                # exp(P*pi/2*i) = I*cos(pi/2) + P*i*sin(pi/2) = P*i ~ P up to gl. ph.
                # Commute into the circuit
                pass
            elif op.angle == Fraction(1, 4):
                # use the reduction with |+> state
                pass
            elif op.angle == Fraction(1, 8):
                # use Litinski reduction with magic state
                pass
            else:
                raise Exception("Unsupported pauli rotation angle")

        else:
            assert isinstance(op,Measurement)


    return lscc


