from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister, Aer, execute
from qiskit.visualization import plot_histogram

import matplotlib.pyplot as plt

simulator = Aer.get_backend('qasm_simulator')


clause_list = [(0, 1), (2, 3), (0, 2), (1, 3)]
clause_list_len = len(clause_list)


def oracle(qc, clause_list, cells, ancilla, output):
    for (c1, c2), a in zip(clause_list, ancilla):
        qc.cx(c1, a)
        qc.cx(c2, a)

    # And all ancilla quibits together to check if the latin square is valid
    qc.mcx(ancilla, output)

    for (c1, c2), a in zip(clause_list, ancilla):
        qc.cx(c1, a)
        qc.cx(c2, a)


def grover_diffusion(qc, cells):
    qc.h(cells)
    qc.x(cells)
    qc.h(cells[-1])

    qc.mcx(cells[:-1], cells[-1])

    qc.h(cells[-1])
    qc.x(cells)
    qc.h(cells)


cells = QuantumRegister(4)
ancilla = QuantumRegister(clause_list_len)
output = QuantumRegister(1)
c = ClassicalRegister(4)

qc = QuantumCircuit(cells, ancilla, output, c)


'''
Define algorithm
'''
qc.h(cells)

# Initialize output qubit to state |->
qc.x(output)
qc.h(output)

for _ in range(2):
    oracle(qc, clause_list, cells, ancilla, output)
    grover_diffusion(qc, cells)

qc.measure(cells, c)

print(qc.draw(output='latex_source'))

print("Starting simulation")
job = execute(qc, simulator, shots=40000)

result = job.result()

print(result)

counts = result.get_counts(qc)
print("Counts are:", counts)

for k, v in counts.items():
    if v > 200:
        c1, c2, c3, c4 = k[0:4]
        print(c1, c2)
        print(c3, c4)
        print()

plot_histogram(counts).show()
plt.show()
