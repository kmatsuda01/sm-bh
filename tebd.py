import numpy as np
import math
import helpers
import datetime
from matplotlib import pyplot as plt

# Simulation and model parameters
model = {'J': 0, 'U': 1}
# Note: set 'it' == True to find ground state, False to calculate real time evolution
# If doing imaginary time evolution, we need to add in a chemical potential term to conserve number
# mu is in units of U
sim = {'d': 8, 'chi': 50, 'L': 4, 'delta': 0.01, 'N': 1500, 'it': False, 'mu': 0.5}

# Choose which expectation values to log:
# Skip: how many iterations to skip between logging expectation values
logs = {'rho': False, 'a': True, 'n': False, 'aa': False, 'skip': 0}

# Choose your initial state:
# state_flag = 0 for Fock states, = 1 for coherent states
init = {'nbar': 1, 'flag': 1};

# Which parameter(s) to sweep?
sweep_par = ['U']
# What range to sweep over?
# Script will iterate through this array
par1_range = [1.0] # np.arange(2, 2.2, 0.2)
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
	f.write("J = {0}, U = {1}\n".format(model['J'], model['U']))
	f.write("nbar = {0}, flag = {1}\n".format(init['nbar'], init['flag']))
	f.write("rho = {0}, a = {1}, n = {2}, skip = {3}\n".format(logs['rho'], logs['a'], logs['n'], logs['skip']))

	# Run the simulation
	simulation = helpers.TEBD(model, sim, init, logs)
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

	print sweep_range[i]

a_avg = simulation.a_avg
# Plot stuff
L = sim['L']; chi = sim['chi']; d = sim['d']; delta = sim['delta']; N = sim['N']
f, ax = plt.subplots(L, sharex=True, sharey=True)
for i in range(0, L):
	ts = np.arange(0, (N+1)*delta, delta)
	ax[i].plot(ts, np.absolute(a_avg[i,:]), 'bo', label="TEBD site {0}".format(i))
	ax[i].plot(ts, np.absolute(init['nbar'] * np.exp(init['nbar'] * np.expm1(-1j * ts * model['U']))), 'r-', linewidth=2)
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

plt.xlabel(r"t ($\hbar/U$)", fontsize=16)
plt.ylabel(r"$|\langle a(t) \rangle|$", fontsize=16)
plt.savefig(filename + "_a.pdf", format="pdf")
plt.show()