from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister, Aer, execute
from qiskit.visualization import plot_histogram

import matplotlib.pyplot as plt

import time

simulator = Aer.get_backend('qasm_simulator')


# Constraints are in form ((a, b), t)
# where <cell a> should not equal <cell b> and both <cell a> and <cell b> should not be <t>
row_constraints = [((0, 1), 1), ((2, 3), 2)]
column_constraints = [((0, 2), 1), ((1, 3), 2)]

clause_list = row_constraints + column_constraints


def oracle(qc, clause_list, cells, ancilla, clauses, output):
    # Compute output of all clauses
    check_clauses(qc, clause_list, cells, ancilla, clauses)

    # And all clauses together to check if latin square is valid
    qc.mcx(clauses, output)

    # Un-compute clause qubits
    check_clauses(qc, clause_list, cells, ancilla, clauses)


def check_clauses(qc, clause_list, cells, ancilla, clauses):
    for ((a, b), t), clause in zip(clause_list, clauses):
        # Prepare state t
        if t == 1:
            qc.x(ancilla[1])
        elif t == 2:
            qc.x(ancilla[0])

        qc.append(compare_triplet(reverse=False), [*cells[a], *cells[b], *ancilla, clause])
        qc.append(compare_triplet(reverse=True), [*cells[a], *cells[b], *ancilla, clause])

        # Reset state t
        if t == 1:
            qc.x(ancilla[1])
        elif t == 2:
            qc.x(ancilla[0])


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
    for cell in cells:
        qc.x(cell[0])
        qc.ch(cell[0], cell[1])
        qc.ry(-1.91063, cell[0])

    qc.x(all_qubits(cells))
    qc.h(cells[-1][-1])

    qc.mcx(all_qubits(cells)[:-1], cells[-1][-1])

    qc.h(cells[-1][-1])
    qc.x(all_qubits(cells))

    for cell in cells:
        qc.ry(1.91063, cell[0])
        qc.ch(cell[0], cell[1])
        qc.x(cell[0])


def all_qubits(registers):
    return [q for r in registers for q in r]


cells = [QuantumRegister(2) for _ in range(4)]
ancilla = QuantumRegister(7)
clauses = QuantumRegister(4)
output = QuantumRegister(1)
c = ClassicalRegister(8)

qc = QuantumCircuit(*cells, ancilla, clauses, output, c)


'''
Define algorithm
'''
# Initialize all cells to equal superposition of |00>, |01> and |10>
for cell in cells:
    qc.ry(1.91063, cell[0])
    qc.ch(cell[0], cell[1])
    qc.x(cell[0])

# Initialize output qubit to state |->
qc.x(output)
qc.h(output)

for _ in range(7):
    oracle(qc, clause_list, cells, ancilla, clauses, output)
    grover_diffusion(qc, cells)


qc.measure(all_qubits(cells), c)

# print(qc.draw())

print("Starting simulation")
start_time = time.time()
job = execute(qc, simulator, shots=10000)

result = job.result()

end_time = time.time()
print("Simulation took", end_time - start_time)

print(result)

counts = result.get_counts(qc)
print("Counts are:", counts)

for k, v in counts.items():
    if v > 100:
        c1, c2, c3, c4 = k[0:2], k[2:4], k[4:6], k[6:8]
        c1, c2, c3, c4 = int(c1, base=2), int(c2, base=2), int(c3, base=2), int(c4, base=2)
        print("Count:", v)
        print(c1, c2)
        print(c3, c4)
        print()

plot_histogram(counts).show()
plt.show()
