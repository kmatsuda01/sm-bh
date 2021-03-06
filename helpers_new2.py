import numpy as np
import math

# Class for handling the Lambda, Gamma, and Theta tensors
class TEBD(object):

	# Initialize
	def __init__(self, model, sim, init, logs):
		self.Lambda = lambda0(sim)
		coeffs = Initialize_States(sim, init)
		self.tensorA = Gamma0(coeffs, sim)
		L = sim['L']
		for i in range(1, L):
			self.tensorA[i] = np.transpose(np.tensordot(np.diag(self.Lambda[i-1]), self.tensorA[i], axes=(0,1)), (1,0,2))
		self.tau = 0
		self.model = model
		self.sim = sim
		self.init = init
		self.logs = logs
		self.rhos = np.zeros((sim['L'], sim['N']+1, sim['d'], sim['d']), dtype=np.complex64)
		self.a_avg = np.zeros((sim['L'], sim['N']+1), dtype=np.complex64)
		self.n_avg = np.zeros((sim['L'], sim['N']+1))
		self.aa = np.zeros((sim['L'], sim['L']), dtype=np.complex64)

	# The simulation loop
	def Run_Simulation(self):
		# Define simulation parameters
		N = self.sim['N']
		L = self.sim['L']
		d = self.sim['d']
		logs = self.logs
		it = self.sim['it']

		# Define operators
		ops = Operators(self.model, self.sim)
		V_odd = ops.V_odd
		V_even = ops.V_even
		V_0 = ops.V_0
		V_Lm2 = ops.V_Lm2
		a_op = ops.a
		a_dag = ops.a_dag
		n_op = ops.n_op

		# Create arrays to hold data
		# and store initial values
		if (logs['rho']):
			for r in range(0, L):
				self.rhos[r,0] = self.Single_Site_Rho(r)
		if (logs['a']):
			for r in range(0, L):
				self.a_avg[r,0] = np.trace(np.dot(self.Single_Site_Rho(r), a_op))
		if (logs['n']):
			for r in range(0, L):
				self.n_avg[r,0] = np.real(np.trace(np.dot(self.Single_Site_Rho(r), n_op)))
		# if (logs['aa']):
		# 	for l in range(0, L):
		# 		for k in range(l+1, L):
		# 			# Calculate <a^dag_k, a_l>
		# 			self.aa[l,k] = np.trace(np.dot(np.reshape(self.Two_Site_Rho(l, k), (d*d, d*d)), np.kron(a_dag, a_op)))
		# 			self.aa[k,l] = self.aa[l,k]
		# 		# Diagonal terms are number expectation values
		# 		self.aa[l,l] = np.trace(np.dot(self.Single_Site_Rho(l), n_op))

		# # Loop: do all the odds, then evens, then odd
		for i in range(1, N+1):
			if (not it):
				# Evolve odd links delta * t / 2
				for h in range(0, L-2):
					if h % 2 == 1:
						self.Update(V_odd, h)
				if (L-2) % 2 == 1:
					self.Update(V_Lm2, L-2)		
				
				# Evolve even links delta * t
				self.Update(V_0, 0)
				for j in range(1, L-2):
					if j % 2 == 0:
						self.Update(V_even, j)
				if (L-2) % 2 == 0:
					self.Update(V_Lm2, L-2)	
				
				# Evolve odd links delta * t / 2
				for k in range(0, L-2):
					if k % 2 == 1:
						self.Update(V_odd, k)
				if (L-2) % 2 == 1:
					self.Update(V_Lm2, L-2)
			# else:
			# 	# Evolve odd links delta * t / 2
			# 	for h in range(0, L-1):
			# 		if h % 2 == 1:
			# 			self.Update(V_odd, h)
			# 			print ('v', h, np.trace(self.Single_Site_Rho(h)))
			# 		else:
			# 			self.Update(np.reshape(np.identity(d*d), (d,d,d,d)), h)
			# 			print ('id', h, np.trace(self.Single_Site_Rho(h)))

			# 	if ((L-1) % 2 == 1):
			# 		self.Update(V_last, L-2)
			# 		print ('v', L-1, np.trace(self.Single_Site_Rho(L-1)))
				
			# 	# Evolve even links delta * t
			# 	if ((L-1) % 2 == 0):
			# 		self.Update(V_last, L-2)
			# 		print ('v', L-1, np.trace(self.Single_Site_Rho(L-1)))

			# 	for j in np.arange(L-2, -1, -1):
			# 		if j % 2 == 0:
			# 			self.Update(V_even, j)
			# 			print ('v', j, np.trace(self.Single_Site_Rho(j)))
			# 		else:
			# 			self.Update(np.reshape(np.identity(d*d), (d,d,d,d)), j)
			# 			print ('id', j, np.trace(self.Single_Site_Rho(j)))

			# 	for j in range(0, L-1):
			# 		if j % 2 == 0:
			# 			self.Update(V_even, j)
			# 		else:
			# 			self.Update(np.reshape(np.identity(d*d), (d,d,d,d)), j)
			# 	if (L-1) % 2 == 0:
			# 		self.Update(V_last, L-2)	
				
			# 	# Evolve odd links delta * t / 2
			# 	for k in range(L-2, -1, -1):
			# 		if k % 2 == 1:
			# 			self.Update(V_odd, k)
			# 		else:
			# 			self.Update(np.reshape(np.identity(d**2), (d,d,d,d)), k)
			# 	if ((L-1) % 2 == 1):
			# 		self.Update(V_last, L-2)
			
			# Log data:
			if (not it):
				if (i % (logs['skip'] + 1) == 0):
					ind = int(i / (logs['skip'] + 1))
					if (logs['rho']):
						# Store single particle density matrices
						for r in range(0, L):
							self.rhos[r,ind] = self.Single_Site_Rho(r)
					if (logs['a']):
						# Store expectation values of a
						for r in range(0, L):
							self.a_avg[r,ind] = np.trace(np.dot(self.Single_Site_Rho(r), a_op))
					if (logs['n']):
						# Store expectation values of n
						for r in range(0, L):
							self.n_avg[r,ind] = np.real(np.trace(np.dot(self.Single_Site_Rho(r), n_op)))

			# Can delete this later:
			if (i % 50 == 0):
				print "step {0} done".format(i)

		# If imaginary time, one last sweep to ensure orthonormality
		if it:
			for i in range(0, L-1):
				self.Update(np.reshape(np.identity(d*d), (d,d,d,d)), i)

		# # Only store SPDM at the very end
		# # Probably only want to do this for calculating GS
		# if (it):
		# 	if (logs['rho']):
		# 		# Store single particle density matrices
		# 		for r in range(0, L):
		# 			self.rhos[r,-1] = self.Single_Site_Rho(r)
		# 	if (logs['a']):
		# 		# Store expectation values of a
		# 		for r in range(0, L):
		# 			self.a_avg[r,-1] = np.trace(np.dot(self.Single_Site_Rho(r), a_op))
		# 	if (logs['n']):
		# 		# Store expectation values of n
		# 		for r in range(0, L):
		# 			self.n_avg[r,-1] = np.real(np.trace(np.dot(self.Single_Site_Rho(r), n_op)))
		# 	# if (logs['aa']):
		# 	# 	for l in range(0, L):
		# 	# 		for k in range(l+1, L):
		# 	# 			# Calculate <a^dag_k, a_l>
		# 	# 			self.aa[l,k] = np.trace(np.dot(np.reshape(self.Two_Site_Rho(l, k), (d*d, d*d)), np.kron(a_dag, a_op)))
		# 	# 			self.aa[k,l] = self.aa[l,k]
		# 	# 		# Diagonal terms are number expectation values
		# 	# 		self.aa[l,l] = np.trace(np.dot(self.Single_Site_Rho(l), n_op))
	
	# Build the Theta tensor
	def Build_Theta(self, l):
		L = self.sim['L']
		chi = self.sim['chi']
		Lambda = self.Lambda
		A_l = self.tensorA[l]
		A_lp1 = self.tensorA[l+1]

		if (l != self.sim['L']-2):
			theta = np.tensordot(A_l, A_lp1, axes=(-1,1))
			# theta = np.tensordot(theta, np.diag(Lambda[l+1]), axes=(-1, 0))
			theta = np.transpose(theta, (0,2,1,3))
		elif (l == self.sim['L']-2):
			theta = np.tensordot(A_l, A_lp1, axes=(-1,1))
			theta = np.transpose(theta, (0,2,1,3))
		return theta

	# This follows the discussion in
	# http://inside.mines.edu/~lcarr/theses/mishmash_thesis_2008.pdf,
	# section 3.2.3.
	# Note that while the linked thesis indexes from 1,
	# we index from zero here to avoid confusion in the code.
	# Therefore, l runs from [0, ..., L - 1] in our case,
	# instead of [1, ..., L] as shown in the thesis.
	def Update(self, V, l):
		d = self.sim['d']; L = self.sim['L'];
		chi = self.sim['chi']; delta = self.sim['delta'];

		# Build the appropriate Theta tensor
		Theta = self.Build_Theta(l)
		# print (l, 'b', Theta[:,:,0,0])
		# Apply the unitary matrix V
		Theta = np.tensordot(V, Theta, axes=([2,3], [0,1]))
		# print (l, 'a', Theta[:,:,0,0])
		
		if (l != L - 2):
			Phi = np.tensordot(Theta, np.diag(self.Lambda[l+1]), axes=(-1,0))
		else:
			Phi = Theta

		# Reshape to a square matrix and do singular value decomposition:
		Phi = np.reshape(np.transpose(Phi, (0,2,1,3)), (d*chi, d*chi))
		# Theta = np.reshape(np.transpose(Theta, (0,2,1,3)), (d*chi, d*chi))
		# Theta = np.reshape(np.transpose(Theta, (2,0,1,3)), (d*chi, d*chi))

		Phi = Phi / np.linalg.norm(np.absolute(Phi))
		# Theta = Theta / np.linalg.norm(np.absolute(Theta))
		# A and transpose.C contain the new Gamma[l] and Gamma[l+1]
		# B contains new Lambda[l]
		# A, B, C = np.linalg.svd(Theta)
		A, B, C = np.linalg.svd(Phi)

		# Truncate at chi eigenvalues and enforce normalization
		norm = np.linalg.norm(B[0:chi])
		B = B / norm
		self.Lambda[l] = B[0:chi]
		# print (l, self.Lambda[l])

		# Keep track of the truncation error accumulated on this step
		self.tau += delta * (1 - norm**2)

		# Find the new Gammas:
		# Gamma_l:
		A_l = np.reshape(A[:, 0:chi], (d, chi, chi))
		self.tensorA[l] = A_l

		# Gamma_(l+1):
		A_l_dag = np.transpose(np.conjugate(A_l), (0,2,1))
		# Theta = np.transpose(np.reshape(Theta, (d, chi, d, chi)), (0,2,1,3))	
		# Theta = np.transpose(np.reshape(Theta, (chi, d, d, chi)), (2,0,1,3))
		# A_lp1 = np.transpose(np.tensordot(A_l_conj, Theta, axes=([0,2],[0,2])), (1,2,0))
		A_lp1 = np.transpose(np.tensordot(A_l_dag, Theta, axes=([0,-1],[0,2])), (1,0,2))
		self.tensorA[l+1] = A_lp1
		# if l == 0:
		# 	test1 = np.tensordot(A_lp1, np.diag(self.Lambda[l+1]), axes=(-1,0))
		# else:
		# 	test1 = A_lp1
		# C = np.reshape(np.transpose(C[0:chi,:]), (d, chi, chi))
		# test2 = np.transpose(np.tensordot(np.diag(B[0:chi]), C, axes=(0,1)), (1,0,2))
		# print np.allclose(test1, test2)

		# print (l, 'last', self.Build_Theta(l)[:,:,0,0])
		

		# # Need to treat boundary subsystems differently...
		# if (l != 0 and l != L - 2):
		# 	# Reshape to a square matrix and do singular value decomposition:
		# 	Theta = np.reshape(np.transpose(Theta, (2,0,1,3)), (d*chi, d*chi))
		# 	Theta *= 1 / np.linalg.norm(np.absolute(Theta))
		# 	# A and transpose.C contain the new Gamma[l] and Gamma[l+1]
		# 	# B contains new Lambda[l]
		# 	A, B, C = np.linalg.svd(Theta)

		# 	# Truncate at chi eigenvalues and enforce normalization
		# 	norm = np.linalg.norm(B[0:chi])
		# 	B = B / norm
		# 	self.Lambda[l] = B[0:chi]

		# 	# Keep track of the truncation error accumulated on this step
		# 	self.tau += delta * (1 - norm**2)

		# 	# Find the new Gammas:
		# 	# Gamma_l:
		# 	A_l = np.reshape(A[:, 0:chi], (d, chi, chi))
		# 	self.tensorA[l] = A_l

		# 	# Gamma_(l+1):
		# 	A_l_conj = np.conjugate(A_l)
		# 	Theta = np.transpose(np.reshape(Theta, (d, chi, d, chi)), (0,2,1,3))
		# 	# A_lp1 = np.transpose(np.tensordot(A_l_conj, Theta, axes=([0,1],[0,2])), (1,2,0))
		# 	A_lp1 = np.transpose(np.tensordot(A_l_conj, Theta, axes=([0,1],[0,2])), (1,0,2))
		# 	self.tensorA[l+1] = A_lp1 
			
		# # The Gamma_0 tensor has one less index... need to treat slightly differently
		# elif (l == 0):
		# 	# Reshape to a square matrix and do singular value decomposition:
		# 	Theta = np.reshape(np.transpose(Theta, (2,0,1,3)), (d*chi, d*chi))
		# 	Theta *= 1.0 / np.linalg.norm(np.absolute(Theta))
		# 	# A and transpose.C contain the new Gamma[l] and Gamma[l+1]
		# 	# B contains new Lambda[l]
		# 	A, B, C = np.linalg.svd(Theta, full_matrices=False)

		# 	# Enforce normalization
		# 	# Don't need to truncate here because chi is bounded by
		# 	# the dimension of the smaller subsystem, which is here d < chi
		# 	norm = np.linalg.norm(B[0:chi])
		# 	B = B / norm
		# 	self.Lambda[l] = B[0:chi]

		# 	# Keep track of the truncation error accumulated on this step
		# 	self.tau += delta * (1 - norm**2)

		# 	# Find the new Gammas:
		# 	# Gamma_l:
		# 	# Note: can't truncate because the matrix
		# 	# is smaller than in the non-edge cases
		# 	A_l = np.reshape(A[:,0:chi], (d, chi, chi))
		# 	self.tensorA[l] = A_l

		# 	A_l_conj = np.conjugate(A_l)
		# 	Theta = np.transpose(np.reshape(Theta, (d, chi, d, chi)), (0,2,1,3))
		# 	A_lp1 = np.tensordot(A_l_conj, Theta, axes=([0,1],[0,2]))
		# 	# self.tensorA[l+1] = np.transpose(A_lp1, (1,2,0))
		# 	self.tensorA[l+1] = np.transpose(A_lp1, (1,0,2))

		# elif (l == L - 2):
		# 	# Reshape to a square matrix and do singular value decomposition:
		# 	Theta = np.reshape(np.transpose(Theta, (2,0,1,3)), (d*chi, d*chi))
		# 	Theta *= 1.0 / np.linalg.norm(np.absolute(Theta))
		# 	# A and transpose.C contain the new Gamma[l] and Gamma[l+1]
		# 	# B contains new Lambda[l]
		# 	A, B, C = np.linalg.svd(Theta)

		# 	# Enforce normalization
		# 	# Don't need to truncate here because chi is bounded by
		# 	# the dimension of the smaller subsystem, here equals d < chi
		# 	norm = np.linalg.norm(B[0:chi])
		# 	B = B / norm
		# 	self.Lambda[l] = B[0:chi]

		# 	# Keep track of the truncation error accumulated on this step
		# 	self.tau += delta * (1 - norm**2)

		# 	# Find the new Gammas:
		# 	# Treat the L-2 case normally:
		# 	A_l = np.reshape(A[:,0:chi], (d, chi, chi))
		# 	self.tensorA[l] = A_l

		# 	# Gamma_(L-1):
		# 	# Note: can't truncate because the matrix
		# 	# is smaller than in the non-edge cases
		# 	A_l_conj = np.conjugate(A_l)
		# 	Theta = np.transpose(np.reshape(Theta, (d, chi, d, chi)), (0,2,1,3))
		# 	# A_lp1 = np.tensordot(A_l_conj, Theta, axes=([0,1],[0,2]))
		# 	# self.tensorA[l+1] = np.transpose(A_lp1, (1,2,0))
		# 	A_lp1 = np.tensordot(A_l_conj, Theta, axes=([0,1],[0,2]))
		# 	self.tensorA[l+1] = np.transpose(A_lp1, (1,0,2))
		

	# Calculate the reduced density matrix,
	# tracing over all sites except site k
	# See Mishmash thesis for derivation
	def Single_Site_Rho(self, k):
		L = self.sim['L']
		Lambda = self.Lambda
		A_k = self.tensorA[k]

		# Need to treat boundaries differently...
		# See Mishmash thesis pg. 73 for formulas
		if (k != 0 and k != L - 1):
			Rho_L = np.tensordot(np.conjugate(A_k), np.diag(Lambda[k]), axes=(-1,0))
			Rho_R = np.tensordot(A_k, np.diag(Lambda[k,:]), axes=(-1,0))
			Rho = np.tensordot(Rho_L, Rho_R, axes=([1,-1],[1,-1]))
			Rho = np.transpose(Rho)
		elif (k == 0):
			Rho_L = np.tensordot(np.conjugate(A_k), np.diag(Lambda[k+1,:]), axes=(-1,0))
			Rho_R = np.tensordot(A_k, np.diag(Lambda[k+1,:]), axes=(-1,0))
			Rho = np.tensordot(Rho_L, Rho_R, axes=([1,2],[1,2]))
			Rho = np.transpose(Rho)
		elif (k == L - 1):
			Rho = np.tensordot(np.conjugate(A_k), A_k, axes=([1,2], [1,2]))
			Rho = np.transpose(Rho)
		return Rho

	# # Calculate the reduced density matrix,
	# # tracing over all sites except site k and l
	# # See http://sourceforge.net/projects/opentebd/
	# # documentation
	# def Two_Site_Rho(self, l, k):
	# 	L = self.sim['L']; chi = self.sim['chi']; d = self.sim['d']
	# 	Lambda = self.Lambda
	# 	Gamma = self.Gamma
	# 	swap = 0

	# 	# Assume l < k
	# 	if (k < l):
	# 		temp = k
	# 		k = l
	# 		l = temp
	# 		swap = 1

	# 	# Form tensor:	
	# 	if (k < L - 2):
	# 		tensor_l = np.tensordot(np.diag(Lambda[k]), Gamma[k], axes=(0,1))
	# 		tensor_l = np.tensordot(tensor_l, np.diag(Lambda[k+1]), axes=(-1, 0))
	# 		tensor_r = np.tensordot(np.diag(Lambda[k+1]), np.conjugate(Gamma[k]), axes=(0,-1))
	# 		tensor_r = np.tensordot(tensor_r, np.diag(Lambda[k]), axes=(-1,0))
	# 		tensor = np.tensordot(tensor_l, tensor_r, axes=(-1, 0))
	# 		# Arrange indices as (ik, ik', ak-1, ak-1')
	# 		tensor = np.transpose(tensor, (1,2,0,3))
	# 	elif (k == L - 2):
	# 		tensor_l = np.tensordot(np.diag(Lambda[k]), Gamma[k], axes=(0,1))
	# 		tensor_l = np.tensordot(tensor_l, np.identity(chi), axes=(-1, 0))
	# 		tensor_r = np.tensordot(np.identity(chi), np.conjugate(Gamma[k]), axes=(0,-1))
	# 		tensor_r = np.tensordot(tensor_r, np.diag(Lambda[k]), axes=(-1,0))
	# 		tensor = np.tensordot(tensor_l, tensor_r, axes=(-1, 0))
	# 		# Arrange indices as (ik, ik', ak-1, ak-1')
	# 		tensor = np.transpose(tensor, (1,2,0,3))
	# 	elif (k == L - 1):
	# 		tensor = np.outer(Gamma[k], np.conjugate(Gamma[k]))
	# 		tensor = np.reshape(tensor, (d, chi, d, chi))
	# 		tensor = np.transpose(tensor, (0,2,1,3))
	# 	for i in range(0, l-k-1):
	# 		tensor = np.tensordot(Gamma[k-1], tensor, axes=(-1,2))
	# 		tensor = np.tensordot(np.diag(Lambda[k-1]), tensor, axes=(-1, 1))
	# 		tensor = np.tensordot(tensor, np.conjugate(Gamma[k-1]), axes=([1,-1], [0, -1]))
	# 		tensor = np.tensordot(tensor, np.diag(Lambda[k-1]), axes=(-1, 0))
	# 		np.transpose(tensor, (1,2,0,3))

	# 	if (l != 0):
	# 		rho_ts = np.tensordot(tensor, np.conjugate(Gamma[l]), axes=(-1, -1))
	# 		rho_ts = np.tensordot(rho_ts, np.diag(Lambda[l]), axes=(-1, 0))
	# 		rho_ts = np.tensordot(Gamma[l], rho_ts, axes=(-1,2))
	# 		rho_ts = np.tensordot(np.diag(Lambda[l]), rho_ts, axes=([0, 1], [1,-1]))
	# 		# Transpose to (il, il', ik, ik')
	# 		rho_lk = np.transpose(rho_ts, (0,3,1,2))
	# 	else:
	# 		rho_ts = np.tensordot(tensor, np.conjugate(Gamma[l]), axes=(-1, -1))
	# 		rho_ts = np.tensordot(Gamma[l], rho_ts, axes=(-1,2))
	# 		# Transpose to (il, il', ik, ik')
	# 		rho_lk = np.transpose(rho_ts, (0,3,1,2))
	# 	return rho_lk


# Operator definitions:
# Not really important for this to be a class
class Operators(object):
	def __init__(self, model, sim):
		# Set up ladder operators	
		d = sim['d']
		L = sim['L']
		a = np.zeros((d,d), dtype=np.complex64)
		for i in range(0,d-1):
			a[i, i+1] = math.sqrt(i+1)
		a_dag = np.transpose(a)
		n_op = np.dot(a_dag, a)

		self.a = a
		self.a_dag = a_dag
		self.n_op = n_op
	
		# Set up Hamiltonian
		J = model['J']; U = model['U']; delta = sim['delta']

		if (sim['it']):
			mu = sim['mu'] * U
		else:
			mu = 0
		# Build two site Hamiltonian:
		hop = -J * (np.kron(a_dag, a) + np.kron(a, a_dag))
		onsite = (U / 4) * np.kron(np.dot(n_op, n_op - np.identity(d)), np.identity(d)) + (U / 4) * np.kron(np.identity(d), np.dot(n_op, n_op - np.identity(d))) - (mu/2) * np.kron(n_op, np.identity(d)) - (mu/2) * np.kron(np.identity(d), n_op)
		H_2site = hop + onsite
		H_0 = H_2site + (U / 4) * np.kron(np.dot(n_op, n_op - np.identity(d)), np.identity(d)) - (mu/2) * np.kron(n_op, np.identity(d))
		H_Lm2 = H_2site + (U / 4) * np.kron(np.identity(d), np.dot(n_op, n_op - np.identity(d))) - (mu/2) * np.kron(np.identity(d), n_op)
		# Diagonalize 
		w,v = np.linalg.eigh(H_2site)
		# Check if we are looking at tau = it evolution to find ground state:
		if (not sim['it']):
			self.V_odd = np.reshape(np.dot(np.dot(v,np.diag(np.exp(-1j*delta*(w) / 2))), np.transpose(v)), (d,d,d,d))
			self.V_even = np.reshape(np.dot(np.dot(v,np.diag(np.exp(-1j*delta*(w)))), np.transpose(v)), (d,d,d,d))
		else:
			self.V_odd = np.reshape(np.dot(np.dot(v,np.diag(np.exp(-delta*(w) / 2))), np.transpose(v)), (d,d,d,d))
			self.V_even = np.reshape(np.dot(np.dot(v,np.diag(np.exp(-delta*(w) / 2))), np.transpose(v)), (d,d,d,d))
		w0, v0 = np.linalg.eigh(H_0)
		self.V_0 = np.reshape(np.dot(np.dot(v0,np.diag(np.exp(-1j*delta*(w0)))), np.transpose(v0)), (d,d,d,d))
		w_Lm2, v_Lm2 = np.linalg.eigh(H_Lm2)
		if (L - 2) % 2 == 0:
			self.V_Lm2 = np.reshape(np.dot(np.dot(v_Lm2,np.diag(np.exp(-1j*delta*(w_Lm2)))), np.transpose(v_Lm2)), (d,d,d,d))
		else:
			self.V_Lm2 = np.reshape(np.dot(np.dot(v_Lm2,np.diag(np.exp(-1j*delta*(w_Lm2) / 2))), np.transpose(v_Lm2)), (d,d,d,d))
		# # Same thing for last site
		# H_last = 
		# wp, vp = np.linalg.eigh(H_last)
		# if ((sim['L'] - 1) % 2 == 0):
		# 	if (not sim['it']):
		# 		self.V_last = np.reshape(np.dot(np.dot(vp,np.diag(np.exp(-1j * delta*(wp) ))), np.transpose(vp)), (d,d,d,d))
		# 		# self.V_last = np.transpose(self.V_last, (0,3,2,1))
		# 	else:
		# 		self.V_last = np.reshape(np.dot(np.dot(vpp,np.diag(np.exp(- delta*(wp)/2 ))), np.transpose(vp)), (d,d,d,d))
		# else:	
		# 	if (not sim['it']):
		# 		self.V_last = np.reshape(np.dot(np.dot(vp,np.diag(np.exp(-1j * delta*(wp) / 2))), np.transpose(vp)), (d,d,d,d))
		# 		# self.V_last = np.transpose(self.V_last, (0,3,2,1f))
		# 	else:
		# 		self.V_last = np.reshape(np.dot(np.dot(vp,np.diag(np.exp(- delta*(wp) / 2))), np.transpose(vp)), (d,d,d,d))

# # Operator definitions:
# # Not really important for this to be a class
# class Operators(object):
# 	def __init__(self, model, sim):
# 		# Set up ladder operators	
# 		d = sim['d']
# 		a = np.zeros((d,d), dtype=np.complex64)
# 		for i in range(0,d-1):
# 			a[i, i+1] = math.sqrt(i+1)
# 		a_dag = np.transpose(a)
# 		n_op = np.dot(a_dag, a)

# 		self.a = a
# 		self.a_dag = a_dag
# 		self.n_op = n_op
	
# 		# Set up Hamiltonian
# 		J = model['J']; U = model['U']; delta = sim['delta']

# 		if (sim['it']):
# 			mu = sim['mu'] * U
# 		else:
# 			mu = 0
# 		# Build two site Hamiltonian:
# 		H_2site = - J * (np.kron(a_dag, a) + np.kron(a, a_dag)) + (U / 2) * np.kron(np.dot(n_op, n_op - np.identity(d)), np.identity(d)) - mu * np.kron(n_op, np.identity(d))
# 		# Diagonalize 
# 		w,v = np.linalg.eigh(H_2site)
# 		# Check if we are looking at tau = it evolution to find ground state:
# 		if (not sim['it']):
# 			self.V_odd = np.reshape(np.dot(np.dot(v,np.diag(np.exp(-1j*delta*(w) / 2))), np.transpose(v)), (d,d,d,d))
# 			self.V_even = np.reshape(np.dot(np.dot(v,np.diag(np.exp(-1j*delta*(w)))), np.transpose(v)), (d,d,d,d))
# 			# self.V_odd = np.transpose(self.V_odd, (0,3,2,1))
# 			# self.V_even = np.transpose(self.V_even, (0,3,2,1))
# 		else:
# 			self.V_odd = np.reshape(np.dot(np.dot(v,np.diag(np.exp(-delta*(w) / 2))), np.transpose(v)), (d,d,d,d))
# 			self.V_even = np.reshape(np.dot(np.dot(v,np.diag(np.exp(-delta*(w) / 2))), np.transpose(v)), (d,d,d,d))
# 		# Same thing for last site
# 		H_last = (U/2) * np.kron(np.identity(d), np.dot(n_op, n_op - np.identity(d))) - mu * np.kron(np.identity(d), n_op)
# 		wp, vp = np.linalg.eigh(H_last)
# 		if ((sim['L'] - 1) % 2 == 0):
# 			if (not sim['it']):
# 				self.V_last = np.reshape(np.dot(np.dot(vp,np.diag(np.exp(-1j * delta*(wp) ))), np.transpose(vp)), (d,d,d,d))
# 				# self.V_last = np.transpose(self.V_last, (0,3,2,1))
# 			else:
# 				self.V_last = np.reshape(np.dot(np.dot(vpp,np.diag(np.exp(- delta*(wp)/2 ))), np.transpose(vp)), (d,d,d,d))
# 		else:	
# 			if (not sim['it']):
# 				self.V_last = np.reshape(np.dot(np.dot(vp,np.diag(np.exp(-1j * delta*(wp) / 2))), np.transpose(vp)), (d,d,d,d))
# 				# self.V_last = np.transpose(self.V_last, (0,3,2,1f))
# 			else:
# 				self.V_last = np.reshape(np.dot(np.dot(vp,np.diag(np.exp(- delta*(wp) / 2))), np.transpose(vp)), (d,d,d,d))

# Helper functions for initialization:

# Initialize state vectors (product state)
# L sites, number cutoff nmax
# n_onsite is the number on each site
# flag: 0 is Fock state, 1 is (truncated) coherent state with mean occupation = n_onsite
# flag = 0: if number_onsite is an integer, initialize n = n_onsite Mott insulator
# 		if not, initialize w/ probability (n_onsite - floor(n_onsite))
# flag = 1: approximate coherent state with alpha = sqrt(n_onsite)
def Initialize_States(sim, init):
	n_max = sim['d']
	L = sim['L']
	n_onsite = init['nbar']
	flag = init['flag']
	site = init['site']

	# Initialize a matrix of zeros
	mat = np.zeros((L, n_max), dtype=np.complex64)

	# If not coherent states
	if (flag == 0):
		if (math.floor(n_onsite) >= 0):
			# Check that you're under the number cutoff
			if (math.floor(n_onsite) < n_max):
				mat[:,math.floor(n_onsite)] = 1.0
			# If not, initialize to vacuum
			else:
				return mat

			# Check for fractional occupation
			if (n_onsite != math.floor(n_onsite)):
				filling = n_onsite - math.floor(n_onsite)
				rands = np.random.rand(L)
				# Populate next highest state with probability = filling
				for i in range(0, L):
					if rands[i] < filling:
						ind = int(math.floor(n_onsite))
						mat[i,ind+1] = 1.0
						mat[i,ind] = 0.0
	# If coherent state
	elif (flag == 1):
		# Calculate normalization factor
		norm = 0
		for i in range(0, n_max):
			norm += math.pow(n_onsite, i) / math.factorial(i)
		norm = np.sqrt(norm)
		# Build coherent states
		for i in range(0, n_max):
			mat[:,i] = math.pow(n_onsite, float(i) / 2) / (np.sqrt(math.factorial(i)) * norm)

	# If want to initialize n_onsite particles on a given site
	elif (flag == 2):
		# Check that you're under the number cutoff
		if (math.floor(n_onsite) < n_max):
			mat[:, 0] = 1.0
			mat[site, 0] = 0.0
			mat[site,math.floor(n_onsite)] = 1.0
	return mat

# Initialize the coefficient tensors
# See http://inside.mines.edu/~lcarr/theses/mishmash_thesis_2008.pdf,
# Appendix A, assuming product wavefunctions
# Important not to inadverdently cast to real numbers instead of complex!
def lambda0(sim):
	L = sim['L']; chi = sim['chi']
	# From Appendix A, pg. 173
	mat = np.zeros((L-1, chi), dtype=np.complex64)
	mat[:,0] = 1.0
	return mat

# From Appendix A, pg. 173
def Gamma0(coeffs, sim):
	d = sim['d']; L = sim['L']; chi = sim['chi']
	Gamma = []

	for i in range(0, L):
		mat = np.zeros((d, chi, chi), dtype=np.complex64)
		mat[:, 0, 0] = coeffs[i,:]
		Gamma.append(mat)
	return Gamma
