import numpy as np
from typing import *
from enum import Enum
from fractions import Fraction
import qiskit.aqua.operators


class PauliOperator(Enum):
    """
    Representation of a Pauli operator inside of a rotation block 

    """
    _ignore_ = ['_anticommute_tbl']
    _anticommute_tbl = {}

    I = "I"
    X = "X"
    Y = "Y"
    Z = "Z"

    def __str__(self) -> str:
        return self.name
    
    def __repr__(self) -> str:
        return str(self)


    @staticmethod
    def are_commuting(a: 'PauliOperator', b: 'PauliOperator') -> bool:
        """
        Returns True if a and b are commute and False if anti-commute.
    
        """
        if not isinstance(a, PauliOperator) or not isinstance(b, PauliOperator):
            raise Exception("Only supports PauliOperator")

        if (a,b) in PauliOperator._anticommute_tbl:
            return False
        
        else:
            return True

    
    @staticmethod
    def multiply_operators(a: 'PauliOperator', b: 'PauliOperator'):
        """
        Given 2 Pauli operators A and B, return the nearest Pauli operator as the product of A and B and
        the coefficient required for such product. 

        Returns:
            tuple: (coefficient, resultant Pauli operator). Coefficient is either 1, -i or i. 
        """

        if not isinstance(a, PauliOperator) or not isinstance(b, PauliOperator):
            raise Exception("Only supports PauliOperator")

        if (a,b) in PauliOperator._anticommute_tbl:
            return PauliOperator._anticommute_tbl[(a,b)]

        if a == b: 
            return (1, PauliOperator.I)

        if a == PauliOperator.I or b == PauliOperator.I:
            return (1, b if a == PauliOperator.I else a)



PauliOperator._anticommute_tbl = {
    (PauliOperator.Z, PauliOperator.X):     (1j, PauliOperator.Y),
    (PauliOperator.X, PauliOperator.Z):     (-1j, PauliOperator.Y),
    (PauliOperator.Z, PauliOperator.Y):     (1j, PauliOperator.X),
    (PauliOperator.Y, PauliOperator.Z):     (-1j, PauliOperator.X),
    (PauliOperator.Y, PauliOperator.X):     (1j, PauliOperator.Z),
    (PauliOperator.X, PauliOperator.Y):     (-1j, PauliOperator.Z)
}


def lattice_surgery_op_to_quiskit_op( op :PauliOperator) -> Optional[qiskit.aqua.operators.PrimitiveOp]:
    known_map : Dict[PauliOperator, qiskit.aqua.operators.PrimitiveOp] = {
        PauliOperator.I : qiskit.aqua.operators.I,
        PauliOperator.X : qiskit.aqua.operators.X,
        PauliOperator.Y : qiskit.aqua.operators.Y,
        PauliOperator.Z : qiskit.aqua.operators.Z
    }
    return known_map[op]


class PauliProductOperation(object):

    qubit_num:  int = None
    ops_list:   List[PauliOperator] = None

    def __str__(self) -> str:
        pass


    def __repr__(self) -> str:
        return str(self)

    
    def change_single_op(self, qubit: int, new_op: PauliOperator) -> None:
        """
        Modify a Pauli Operator

        Args:
            qubit (int): Targeted qubit
            new_op (PauliOperator): New operator type (I, X, Z, Y)
        """

        if not isinstance(new_op, PauliOperator):
            raise TypeError("Cannot add type", type(new_op), "to circuit")

        self.ops_list[qubit] = new_op

    
    def get_op(self, qubit: int) -> PauliOperator:
        """
        Return the current operator of qubit i. 

        Args:
            qubit (int): Targeted qubit

        Returns:
            PauliOperator: Pauli operator of targeted qubit.
        """
        return self.ops_list[qubit]


    def get_ops_map(self) -> Dict[int, PauliOperator]:
        """"
        Return a map of qubit_n -> operator
        """
        return dict([(qn, self.ops_list[qn]) for qn in range(self.qubit_num) if self.ops_list[qn] != PauliOperator.I])


    
class Rotation(PauliProductOperation):
    """
    Class for representing a Pauli Product Rotation Block 

    """
    def __init__(self, no_of_qubit: int, rotation_amount: Fraction) -> None:
        """
        Creating a Pauli Product Rotation Block. All operators are set to I (Identity). 
        A Pauli Product Rotation Block MUST span all qubits on the circuit. 

        Args:
            no_of_qubit (int): Number of qubits on the circuit
            rotation_amount (Fraction): Rotation amount (e.g. 1/4, 1/8). Implicitly multiplied by pi.
        """

        self.qubit_num:         int = no_of_qubit
        self.rotation_amount:   Fraction = rotation_amount
        self.ops_list:          List[PauliOperator] = [PauliOperator("I") for i in range(no_of_qubit)]
    
    
    def __str__(self) -> str:
        return '{}: {}'.format(self.rotation_amount, self.ops_list) 
            
        
    @staticmethod
    def from_list(pauli_ops: List[PauliOperator], rotation: Fraction) -> 'Rotation':
        r = Rotation(len(pauli_ops), rotation)
        for i,op in enumerate(pauli_ops):
            r.change_single_op(i,op)
        return r



class Measurement(PauliProductOperation):
    """
    Representing a Pauli Product Measurement Block

    """
    def __init__(self, no_of_qubit: int, isNegative: bool = False) -> None:
        """
        Generate a Pauli Product Measurement Block. All operators are set to I (Identity). 
        A Pauli Product Measurement Block MUST span all qubits in the circuit

        Args:
            no_of_qubit (int): Number of qubits in the circuit
            isNegative (bool, optional): Set to negative. Defaults to False.
        """
        self.qubit_num:     int = no_of_qubit
        self.isNegative:    bool = isNegative
        self.ops_list:      List[PauliOperator] = [PauliOperator("I") for i in range(no_of_qubit)]
        

    def __str__(self) -> str:
        return '{}M: {}'.format('-' if self.isNegative else '', self.ops_list) 


    @staticmethod
    def from_list(pauli_ops: List[PauliOperator], isNegative: bool = False) -> 'Measurement':
        m = Measurement(len(pauli_ops), isNegative)
        
        for i,op in enumerate(pauli_ops):
            m.change_single_op(i,op)
        
        return m