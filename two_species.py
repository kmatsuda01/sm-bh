import numpy as np
import math
import helpers_2species
import datetime
from matplotlib import pyplot as plt

# Simulation and model parameters
model = {'Ja': 1.0, 'Ua': 0.0, 'Jb': 0.0, 'Uab': 0.0}
# Note: set 'it' == True to find ground state, False to calculate real time evolution
# If doing imaginary time evolution, we need to add in a chemical potential term to conserve number
# mu is in units of U
sim = {'da': 4, 'db': 1, 'chi': 50, 'L': 4, 'delta': 0.001, 'N': 200, 'it': False, 'mu': 0.5}
# Local Hilbert space dimension: 'da' dimensions for majority, 2 dimensional for minority
sim['d'] = sim['da'] * sim['db']

# Choose which expectation values to log:
# Skip: how many iterations to skip between logging expectation values
logs = {'rho': False, 'a': True, 'b': False, 'na': True, 'nb': True, 'aa': False, 'skip': 0}

# Choose your initial state:
# For majority: flag = 0 for Fock states, = 1 for coherent states
# site = site to initialize impurity on
init = {'nbar': 0.5, 'flag': 0, 'site': 1};

# Which parameter(s) to sweep?
sweep_par = ['Ua']
# What range to sweep over?
# Script will iterate through this array
par1_range = [model['Ua']] # np.arange(2, 2.2, 0.2)
par2_range = np.arange(0.5, 0.7, 0.2)
sweep_range = [(x,y) for x in par1_range for y in par2_range]

for i in range(0, len(sweep_range)):
	for j in range(0, len(sweep_par)):
		if (sweep_par[j] in model):
			model[sweep_par[j]] = sweep_range[i][j]
		elif (sweep_par[j] in sim):
			sim[sweep_par[j]] = sweep_range[i][j]
		elif (sweep_par[j] in init):
			init[sweep_par[j]] = sweep_range[i][j]

	# Open a file for saving results
	filename = datetime.datetime.now().strftime("%m_%d_%H_%M_%S")
	f = open(filename + ".txt", 'w')
	# Log parameters to file
	f.write("d = {0}, chi = {1}, L = {2}\n".format(sim['d'], sim['chi'], sim['L']))
	f.write("delta = {0}, N = {1}\n".format(sim['delta'], sim['N']))
	f.write("Ja = {0}, Ua = {1}, Jb = {2}, Uab = {3}\n".format(model['Ja'], model['Ua'], model['Jb'], model['Uab']))
	f.write("nbar = {0}, flag = {1}\n".format(init['nbar'], init['flag']))
	f.write("rho = {0}, a = {1}, b, = {2}, na = {3}, skip = {4}\n".format(logs['rho'], logs['a'], logs['b'], logs['na'], logs['skip']))

	# Run the simulation
	simulation = helpers_2species.TEBD(model, sim, init, logs)
	simulation.Run_Simulation()

	# spdm = simulation.aa
	# f.write("{0}\n".format(np.array2string(spdm)))

	# # Get the data
	# a_avg = simulation.a_avg
	# # Average to find average superfluid order parameter
	# a_gs = np.mean(np.absolute(a_avg[:,-1]))
	# print a_gs
	# f.write("order par = {0}\n".format(a_gs))

	f.write("error = {0}".format(simulation.tau))
	# Close file
	f.close()

print simulation.n_a_avg[:,0]

a_avg = simulation.a_avg
print a_avg[:,0]
# Plot stuff
L = sim['L']; chi = sim['chi']; d = sim['d']; delta = sim['delta']; N = sim['N']
f, ax = plt.subplots(L, sharex=True, sharey=True)
for i in range(0, L):
	ts = np.linspace(0, (N+1)*delta, num=N+1)
	ax[i].plot(ts, np.absolute(a_avg[i,:]), 'bo', label="TEBD site {0}".format(i))
	ax[i].plot(ts, np.absolute(math.sqrt(init['nbar']) * np.exp(init['nbar'] * np.expm1(-1j * ts * model['Ua']))), 'r-', linewidth=2)
	ax[i].legend()
	ax[i].set_yticks(np.arange(0,1.5,0.5))
	ax[i].set_yticklabels(np.arange(0,1.5,0.5))
	ax[i].set_ylim([-0.1, 1.1])
ax[0].set_title(r"TEBD simulation: $L = {0}$, $d = {1}$, $\chi = {2}$".format(L,d,chi), fontsize=18)
f.subplots_adjust(hspace=0)
plt.setp([a.get_xticklabels() for a in f.axes[:-1]], visible=False)

f.add_subplot(111, frameon=False)
# hide tick and tick label of the big axes
plt.tick_params(labelcolor='none', top='off', bottom='off', left='off', right='off')

plt.xlabel(r"t ($\hbar/U_a$)", fontsize=16)
plt.ylabel(r"$|\langle a(t) \rangle|$", fontsize=16)
plt.savefig(filename + "_a.pdf", format="pdf")

n_b_avg = simulation.n_b_avg
# Plot stuff
L = sim['L']; chi = sim['chi']; d = sim['d']; delta = sim['delta']; N = sim['N']
f, ax = plt.subplots(L, sharex=True, sharey=True)
for i in range(0, L):
	ts = np.linspace(0, (N+1)*delta, num=(N+1))
	ax[i].plot(ts, np.absolute(n_b_avg[i,:]), 'bo', label="TEBD site {0}".format(i))
	ax[i].set_yticks(np.arange(0,1.5,0.5))
	ax[i].set_yticklabels(np.arange(0,1.5,0.5))
	ax[i].set_ylim([-0.1, 1.1])
ax[0].set_title(r"TEBD simulation: $L = {0}$, $d = {1}$, $\chi = {2}$".format(L,d,chi), fontsize=18)
f.subplots_adjust(hspace=0)
plt.setp([a.get_xticklabels() for a in f.axes[:-1]], visible=False)

f.add_subplot(111, frameon=False)
# hide tick and tick label of the big axes
plt.tick_params(labelcolor='none', top='off', bottom='off', left='off', right='off')

plt.xlabel(r"t ($\hbar/J_b$)", fontsize=16)
plt.ylabel(r"$\langle n_b(t) \rangle$", fontsize=16)
plt.savefig(filename + "_b.pdf", format="pdf")


n_a_avg = simulation.n_a_avg
# Plot stuff
L = sim['L']; chi = sim['chi']; d = sim['d']; delta = sim['delta']; N = sim['N']
f, ax = plt.subplots(L, sharex=True, sharey=True)
for i in range(0, L):
	ts = np.linspace(0, (N+1)*delta, num=(N+1))
	ax[i].plot(ts, np.absolute(n_a_avg[i,:]), 'bo', label="TEBD site {0}".format(i))
	ax[i].set_yticks(np.arange(0,4.5,0.5))
	ax[i].set_yticklabels(np.arange(0,4.5,0.5))
	ax[i].set_ylim([-0.1, 4.1])
ax[0].set_title(r"TEBD simulation: $L = {0}$, $d = {1}$, $\chi = {2}$".format(L,d,chi), fontsize=18)
f.subplots_adjust(hspace=0)
plt.setp([a.get_xticklabels() for a in f.axes[:-1]], visible=False)

f.add_subplot(111, frameon=False)
# hide tick and tick label of the big axes
plt.tick_params(labelcolor='none', top='off', bottom='off', left='off', right='off')

plt.xlabel(r"t ($\hbar/J_b$)", fontsize=16)
plt.ylabel(r"$\langle n_a(t) \rangle$", fontsize=16)
plt.savefig(filename + "_b.pdf", format="pdf")
plt.show()
plt.show()