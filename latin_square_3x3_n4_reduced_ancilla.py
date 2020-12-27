from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister, Aer, execute
from qiskit.providers.aer import QasmSimulator
from qiskit.visualization import plot_histogram

import matplotlib.pyplot as plt

# simulator = Aer.get_backend('qasm_simulator')
simulator = QasmSimulator(method='matrix_product_state')


# Triplet of cells which all have to be differently pairwise
row_constraints = [(0, 1, 2), (3, 4, 5), (6, 7, 8)]
column_constraints = [(0, 3, 6), (1, 4, 7), (2, 5, 8)]

clause_list = row_constraints + column_constraints


def oracle(qc, clause_list, cells, ancilla, clauses, output):
    # Compute output of all clauses
    for (a, b, c), clause in zip(clause_list, clauses):
        qc.append(compare_triplet(reverse=False), [*cells[a], *cells[b], *cells[c], *ancilla, clause])
        qc.append(compare_triplet(reverse=True), [*cells[a], *cells[b], *cells[c], *ancilla, clause])

    # And all clauses together to check if latin square is valid
    qc.mcx(clauses, output)

    # Un-compute clause qubits
    for (a, b, c), clause in zip(clause_list, clauses):
        qc.append(compare_triplet(reverse=False), [*cells[a], *cells[b], *cells[c], *ancilla, clause])
        qc.append(compare_triplet(reverse=True), [*cells[a], *cells[b], *cells[c], *ancilla, clause])


def compare_triplet(reverse):
    a, b, c = QuantumRegister(2), QuantumRegister(2), QuantumRegister(2)
    ancilla = QuantumRegister(5)
    output = QuantumRegister(1)

    qc = QuantumCircuit(a, b, c, ancilla, output)

    # Compare cells a and c
    qc.cx(a[0], ancilla[0])
    qc.cx(c[0], ancilla[0])

    qc.cx(a[1], ancilla[1])
    qc.cx(c[1], ancilla[1])

    qc.x(ancilla[0:2])

    qc.mcx(ancilla[0:2], ancilla[2])
    qc.x(ancilla[2])

    # Compare cells b and c
    qc.cx(b[0], c[0])
    qc.cx(b[1], c[1])

    qc.x(c)

    qc.mcx(c, ancilla[3])
    qc.x(ancilla[3])

    # Compare cells a and b
    qc.cx(a[0], b[0])
    qc.cx(a[1], b[1])

    qc.x(b)

    qc.mcx(b, ancilla[4])
    qc.x(ancilla[4])

    if not reverse:
        # Combine all comparisons
        qc.mcx(ancilla[2:5], output)

    if reverse:
        qc = qc.reverse_ops()

    compare = qc.to_gate()
    compare.name = "U$_cmp$"
    return compare


def grover_diffusion(qc, cells):
    qc.h(all_qubits(cells))
    qc.x(all_qubits(cells))
    qc.h(cells[-1][-1])

    qc.mcx(all_qubits(cells)[:-1], cells[-1][-1])

    qc.h(cells[-1][-1])
    qc.x(all_qubits(cells))
    qc.h(all_qubits(cells))


def all_qubits(registers):
    return [q for r in registers for q in r]


cells = [QuantumRegister(2) for _ in range(9)]
ancilla = QuantumRegister(5)
clauses = QuantumRegister(6)
output = QuantumRegister(1)
c = ClassicalRegister(18)

qc = QuantumCircuit(*cells, ancilla, clauses, output, c)


'''
Define algorithm
'''
qc.h(all_qubits(cells))

# Initialize output qubit to state |->
qc.x(output)
qc.h(output)

for _ in range(82):
    oracle(qc, clause_list, cells, ancilla, clauses, output)
    grover_diffusion(qc, cells)

qc.measure(all_qubits(cells), c)

# print(qc.draw())

print("Starting simulation")
job = execute(qc, simulator, shots=1)

result = job.result()

print(result)

counts = result.get_counts(qc)
print("Counts are:", counts)

plot_histogram(counts).show()
plt.show()
