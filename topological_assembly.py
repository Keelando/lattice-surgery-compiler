from enum import Enum
from functools import reduce
from typing import *
import copy
from ast import literal_eval as make_tuple

import igraph

import patches




class LatticeLayoutInitializer:

    def singleSquarePatch(cell: Tuple[int,int], patch_type=patches.PatchType.Qubit, patch_state=patches.InitializeableState.Zero ):
        return patches.Patch(patch_type, patch_state, [cell],[
            patches.Edge(patches.EdgeType.Solid,  cell, patches.Orientation.Top),
            patches.Edge(patches.EdgeType.Solid,  cell, patches.Orientation.Bottom),
            patches.Edge(patches.EdgeType.Dashed, cell, patches.Orientation.Left),
            patches.Edge(patches.EdgeType.Dashed, cell, patches.Orientation.Right)
        ])

    def simpleRightFacingDistillery(top_left_corner: Tuple[int,int]) -> List[patches.Patch]:
        # Requires
        x,y = top_left_corner
        return [
            LatticeLayoutInitializer.singleSquarePatch((x+2,y), patches.PatchType.DistillationQubit, patches.InitializeableState.Magic),
            LatticeLayoutInitializer.singleSquarePatch((x+3,y), patches.PatchType.DistillationQubit, patches.InitializeableState.Magic),
            LatticeLayoutInitializer.singleSquarePatch((x+4,y+1), patches.PatchType.DistillationQubit, patches.InitializeableState.Plus),
            LatticeLayoutInitializer.singleSquarePatch((x+3,y+2), patches.PatchType.DistillationQubit, patches.InitializeableState.Magic),
            LatticeLayoutInitializer.singleSquarePatch((x+2,y+2), patches.PatchType.DistillationQubit, patches.InitializeableState.Magic),
            patches.Patch(patches.PatchType.DistillationQubit, patches.InitializeableState.Zero, [(x, y), (x, y+1)],
                          [
                              patches.Edge(patches.EdgeType.Solid, (x, y), patches.Orientation.Top),
                              patches.Edge(patches.EdgeType.Solid, (x, y), patches.Orientation.Left),
                              patches.Edge(patches.EdgeType.Dashed,(x, y), patches.Orientation.Right),
                              patches.Edge(patches.EdgeType.Dashed,(x, y+1), patches.Orientation.Left),
                              patches.Edge(patches.EdgeType.Dashed,(x, y+1), patches.Orientation.Bottom),
                              patches.Edge(patches.EdgeType.Solid, (x, y+1), patches.Orientation.Right),
                          ]),
            patches.Patch(patches.PatchType.DistillationQubit, patches.InitializeableState.Magic, [(x+1, y), (x+1, y+1)],
                          [
                              patches.Edge(patches.EdgeType.Dashed,  (x+1, y), patches.Orientation.Top),
                              patches.Edge(patches.EdgeType.Solid,  (x+1, y), patches.Orientation.Left),
                              patches.Edge(patches.EdgeType.Dashed, (x+1, y), patches.Orientation.Right),
                              patches.Edge(patches.EdgeType.Solid, (x+1, y+1), patches.Orientation.Left),
                              patches.Edge(patches.EdgeType.Dashed, (x+1, y+1), patches.Orientation.Bottom),
                              patches.Edge(patches.EdgeType.Solid,  (x+1, y+1), patches.Orientation.Right),
                          ]),
        ]



    def simpleLayout(num_logical_qubits: int) -> patches.Lattice: # a linear array of one spaced square patches with a distillery on one side
        # TODO distillery
        return patches.Lattice([
            LatticeLayoutInitializer.singleSquarePatch((j*2,0)) for j in range(num_logical_qubits)
        ] + LatticeLayoutInitializer.simpleRightFacingDistillery((2*num_logical_qubits,0))
        ,2,0)






class TopologicalAssemblyComposer:
    def __init__(self, initial_layout: patches.Lattice):
        self.qubit_patch_slices : List[patches.Lattice] = [initial_layout] #initialize lattice here

    def initQubit(self, patch_idx:int, state: patches.InitializeableState): # Only initialization of |0> and |+> is predictable
        self.qubit_patch_slices.append(self.qubit_patch_slices[-1])

    def measureSinglePatch(self, patch_idx:int, basisMatrix: patches.PauliMatrix):
        if basisMatrix not in [patches.PauliMatrix.X, patches.PauliMatrix.Z]:
            raise Exception("can't measure with basis matrix "+basisMatrix+" yet")
        self.qubit_patches[patch_idx] = None

    def newTimeSlice(self):
        self.qubit_patch_slices.append(copy.deepcopy(self.qubit_patch_slices[-1]))

    def measureMultiPatch(self, patch_pauli_operator_map: Dict[Tuple[int, int], patches.PauliMatrix]):
        # TODO refactor this method

        # Break down Y measurements into an simultaneous X and Y measurement, as specified by Litnski's Game of
        # Surface codes in Fig.2.

        def replace_operator(operator_map,old,new) -> Dict[Tuple[int, int], patches.PauliMatrix]:
            new_operator_map = {}
            for cell, operator in operator_map.items():
                if operator == old:
                    new_operator_map[cell] = new
                else:
                    new_operator_map[cell] = operator
            return new_operator_map

        compute_ancilla_cells(self.qubit_patch_slices[-1], patch_pauli_operator_map)

        # TODO fix removal of y operators
        # if 1: return "FIX BELOW using compute_ancilla_cells directly on the lattice"
        # # Try first without replacing the operator and then with replacing the operator
        # ancilla_cells = compute_ancilla_cells(
        #     self.qubit_patch_slices[-1],
        #     replace_operator(patch_pauli_operator_map,patches.PauliMatrix.Y,patches.PauliMatrix.Z)
        # )
        # ancilla_cells.extend(compute_ancilla_cells(
        #     self.qubit_patch_slices[-1],
        #     replace_operator(patch_pauli_operator_map,patches.PauliMatrix.Y,patches.PauliMatrix.X)
        # ))
        #
        # if len(ancilla_cells) > 0:
        #     ancilla_cells = list(set(ancilla_cells)) # Eliminate duplicates
        #     self.qubit_patch_slices[-1].patches.append(patches.Patch(patches.PatchType.Ancilla, None, ancilla_cells,[] ))
        # else:
        #     print("WARNING: no ancilla patch generated for measurement:")
        #     print(patch_pauli_operator_map)






    def clearAncilla(self):
        for j, patch in enumerate(self.qubit_patch_slices[-1].patches):
            for i, edge in enumerate(patch.edges):
                self.qubit_patch_slices[-1].patches[j].edges[i].border_type = edge.border_type.unstitched_type()

        self.qubit_patch_slices[-1].patches = list(filter(
            lambda patch: patch.patch_type != patches.PatchType.Ancilla, self.qubit_patch_slices[-1].patches))

    def clearLattice(self):
        self.qubit_patch_slices[-1].clear()

    def rotateSquarePatch(self, patch_idx: int):
        # assumes: The patch is square, there is room to rotate it
        # TODO make multiple rotations possible at the same time
       pass



    def getSlices(self) -> List[patches.Lattice]:
        return self.qubit_patch_slices



# TODO from here and bleow move to ancilla_routing.py

# TODO reference to paper explaining this part of the algorithm

def get_pauli_op_listing(
        cell: Tuple[int,int],
        lattice: patches.Lattice,
        patch_pauli_operator_map: Dict[Tuple[int, int], patches.PauliMatrix]):

    # TODO check overlapping with representative and document
    l = list(filter(
        lambda cell: cell in patch_pauli_operator_map,
        lattice.getPatchOfCell(cell).cells))

    if len(l) == 0: return None
    r=lattice.getPatchRepresentative(cell)
    if l[0] != r:
        raise Exception(
            "Non patch repr cell associated with operator: " + str(l[0]) + ". Repr is " + str(r))
    return l[0] if len(l) > 0 else None



def make_graph_of_free_cells(lattice: patches.Lattice)->igraph.Graph:
    """The vertex labels are the coordinates as a string.
        E.g. "(12,9)"
    """
    g = igraph.Graph(directed=True)
    for row in range(lattice.getRows()):
        for col in range(lattice.getCols()):
            if lattice.cellIsFree((col, row)):
                g.add_vertex(str((col, row)))

    nrows = lattice.getRows()
    ncols = lattice.getCols()
    for row in range(nrows):
        for col in range(ncols):
            for neighbour_col, neighbour_row in [(col, row + 1), (col, row - 1), (col + 1, row), (col - 1, row)]:
                if neighbour_col in range(ncols) and neighbour_row in range(nrows) \
                        and lattice.cellIsFree((col, row)) and lattice.cellIsFree((neighbour_col, neighbour_row)):
                    g.add_edges([(str((col, row)), str((neighbour_col, neighbour_row)))])
    
    return g

def add_directed_edges(
        ancilla_search_graph: igraph.Graph,
        lattice: patches.Lattice,
        patch_pauli_operator_map: Dict[Tuple[int, int], patches.PauliMatrix],
        source_patch_vertex: str,
        tagret_patch_vertex: str
        ):

    for j, patch in enumerate(lattice.patches):
        patch_representative = str(patch.getRepresentative())

        # Skip inactive patches
        if patch_representative != source_patch_vertex and patch_representative not in tagret_patch_vertex: continue

        # Add the directed edges
        requested_edge_type = patches.PAULI_OPERATOR_TO_EDGE_MAP[patch_pauli_operator_map[patch.getRepresentative()]]
        for edge in patch.edges:
            neighbour = str(edge.getNeighbouringCell())

            if edge.border_type == requested_edge_type and neighbour in ancilla_search_graph.vs["name"]:
                # Add the corresponding directed edge
                if patch.getRepresentative() == source_patch_vertex:
                    ancilla_search_graph.add_edge(patch_representative, neighbour)
                else:
                    ancilla_search_graph.add_edge(neighbour, patch_representative)



def add_ancilla_to_lattice_from_paths(
        lattice: patches,
        paths: List[List[Tuple[int,int]]] # Lists of cells
    ) -> None:

    all_ancilla_cells = set()

    for path in paths:
        source_patch = lattice.getPatchOfCell(path[0])
        for edge in source_patch.edges:
            if edge.getNeighbouringCell() == path[1]:
                edge.border_type = edge.border_type.stitched_type()

        target_patch = lattice.getPatchOfCell(path[-1])
        for edge in target_patch.edges:
            if edge.getNeighbouringCell() == path[-2]:
                edge.border_type = edge.border_type.stitched_type()

        all_ancilla_cells = all_ancilla_cells.union(set(path[1:-1]))

    lattice.patches.append(patches.Patch(patches.PatchType.Ancilla, None, list(all_ancilla_cells),[] ))



def compute_ancilla_cells(
        lattice: patches.Lattice,
        patch_pauli_operator_map: Dict[Tuple[int, int], patches.PauliMatrix]
    ) -> None:

    assert(all(map(lambda cell: lattice.getPatchRepresentative(cell)==cell, patch_pauli_operator_map.keys())))

    # Join all neighbouring free cells with bi directional edges along the lattice
    g = make_graph_of_free_cells(lattice)

    active_qubits = list(map(str, patch_pauli_operator_map.keys()))
    g.add_vertices(active_qubits)

    # For path finding purposes separate take one qubit to be the source and the others to be the targets
    source_qubit : str = active_qubits[0]
    target_qubits : str = active_qubits[1:]

    # Connect the active patches each with a single directed edge along the border of the desired operator
    add_directed_edges(
        g,
        lattice,
        patch_pauli_operator_map,
        source_qubit,
        target_qubits)

    # Now find the paths that join al the patches through the desired operators
    shortest_paths_raw = g.get_shortest_paths(source_qubit, target_qubits, mode='all', output='vpath')
    shortest_paths = [[make_tuple(g.vs[v_idx]["name"]) for v_idx in path] for path in shortest_paths_raw]

    add_ancilla_to_lattice_from_paths(lattice, shortest_paths)




# FROM here and below is ond code only for reference


def ancilla_from_cells__old(
        lattice: patches.Lattice,
        selected_cells_paths: List[str],  # TODO remove the invariant of the cells having to be in a path
        patch_pauli_operator_map: Dict[Tuple[int, int], patches.PauliMatrix]
):
    def is_edge_active__(egde: patches.Edge):
        v1, v2 = patches.Orientation.get_graph_edge(edge)
        v1 = str(edge.cell)
        v2 = str(edge.getNeighbouringCell())
        for j in range(len(selected_cells_paths) - 1):
            if {str(v1), str(v2)} == {selected_cells_paths[j], selected_cells_paths[j + 1]}:
                return True
        return False

    # Mark the active edges
    for j, patch in enumerate(lattice.patches):
        for i, edge in enumerate(patch.edges):
            # if get_pauli_op_listing(edge.cell) in patch_pauli_operator_map and is_edge_on_path(edge):
            v1 = str(edge.cell)
            v2 = str(edge.getNeighbouringCell())
            if v1 in selected_cells_paths and v2 in selected_cells_paths:
                if lattice.getPatchRepresentative(edge.cell) in patch_pauli_operator_map:
                    lattice.patches[j].edges[i].border_type = edge.border_type.stitched_type()

    ancilla_cells = [make_tuple(v) for v in selected_cells_paths if v not in map(str, patch_pauli_operator_map.keys())]
    return ancilla_cells


def compute_ancilla_cells_old(lattice: patches.Lattice, patch_pauli_operator_map: Dict[Tuple[int, int], patches.PauliMatrix]):
    if not patch_pauli_operator_map:
        return []

    get_patch_repr = lambda v: lattice.getPatchRepresentative(v)

    def get_pauli_op_listing(cell):  # TODO check overlapping with representative and document
        l = list(filter(
            lambda cell: cell in patch_pauli_operator_map,
            lattice.getPatchOfCell(cell).cells))

        if len(l) == 0: return None
        if l[0] != get_patch_repr(cell):
            raise Exception(
                "Non patch repr cell associated with operator: " + str(l[0]) + ". Repr is " + str(get_patch_repr(cell)))
        return l[0] if len(l) > 0 else None

    # Mark edges that need stitching
    stitched_graph_edges: List[Tuple[Tuple[str], Tuple[str]]] = []
    active_qubit_cells = set()
    for j, patch in enumerate(lattice.patches):
        for i, edge in enumerate(patch.edges):
            maybe_cell_associated_with_operator = get_pauli_op_listing(edge.cell)
            if maybe_cell_associated_with_operator is not None:

                requested_edge_type = patches.PAULI_OPERATOR_TO_EDGE_MAP[
                    patch_pauli_operator_map[maybe_cell_associated_with_operator]]
                active_qubit_cells.add(str(get_patch_repr(edge.cell)))

                if requested_edge_type == edge.border_type:
                    active_vertex, external_vertex = patches.Orientation.get_graph_edge(edge)
                    edge_with_representative = (
                        get_patch_repr(active_vertex), external_vertex)
                    stitched_graph_edges.append(tuple(map(str, edge_with_representative)))

    active_qubit_cells = list(active_qubit_cells)

    # Compute the ancilla patches

    g = igraph.Graph()
    for row in range(lattice.getRows()):
        for col in range(lattice.getCols()):
            g.add_vertex(str((col, row)))

    nrows = lattice.getRows()
    ncols = lattice.getCols()
    for row in range(nrows):
        for col in range(ncols):
            for neighbour_col, neighbour_row in [(col, row + 1), (col, row - 1), (col + 1, row), (col - 1, row)]:
                if neighbour_col in range(ncols) and neighbour_row in range(nrows):
                    g.add_edges([(str((col, row)), str((neighbour_col, neighbour_row)))])

    for patch in lattice.patches:
        if patch.patch_type in [patches.PatchType.Qubit, patches.PatchType.DistillationQubit]:
            for cell in patch.cells:
                g.delete_vertices([str(cell)])

    g.add_vertices(active_qubit_cells)

    # Now we add the corresponding to the active cell borders. To avoid finding paths that cross a patch
    # we give a direction to the edges going in and out the active patches.

    g.to_directed(mutual=True)  # Exisiting egses are bidirectional

    # Filter out the edges that are not connected to patches in the graph
    def edge_in_graph(e):
        v1, v2 = e
        return str(v1) in g.vs.get_attribute_values("name") and str(v2) in g.vs.get_attribute_values("name")

    good_edges = filter(edge_in_graph, stitched_graph_edges)

    # Edges from the first patch are outward, the rest inward
    outward_cells = lattice.getPatchOfCell(list(patch_pauli_operator_map.keys())[0]).cells
    for v1, v2 in good_edges:
        if v1 in outward_cells:
            g.add_edge(get_patch_repr(v1), get_patch_repr(v2))
        else:
            g.add_edge(get_patch_repr(v2), get_patch_repr(v1))

    shortest_paths = g.get_shortest_paths(active_qubit_cells[0], active_qubit_cells[1:], mode='all', output='vpath')
    shortest_paths_union = [g.vs[v_idx]["name"] for v_idx in reduce(lambda a, b: a + b, shortest_paths)]

    def is_edge_on_path(egde: patches.Edge):
        v1, v2 = patches.Orientation.get_graph_edge(edge)
        v1 = get_patch_repr(v1)
        v2 = get_patch_repr(v2)
        for j in range(len(shortest_paths_union) - 1):
            if {str(v1), str(v2)} == {shortest_paths_union[j], shortest_paths_union[j + 1]}:
                return True
        return False

    # Mark the active edges
    for j, patch in enumerate(lattice.patches):
        for i, edge in enumerate(patch.edges):
            if get_pauli_op_listing(edge.cell) in patch_pauli_operator_map and is_edge_on_path(edge):
                lattice.patches[j].edges[i].border_type = edge.border_type.stitched_type()

    ancilla_cells = [make_tuple(v) for v in shortest_paths_union if v not in active_qubit_cells]
    return ancilla_cells