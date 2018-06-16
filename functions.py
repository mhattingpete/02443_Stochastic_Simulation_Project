import numpy as np

def hyperexpon(x,lmbda,w1,w2):
	v = np.sqrt((lmbda+w1+w2)**2-4*lmbda*w2)
	return lmbda*(lmbda+v+w1-w2)*(v+w1+w2+lmbda)/(4*v)*np.exp(-0.5*(v+w1+w2+lmbda)*x)+lmbda*(v-lmbda-w1+w2)*(lmbda+w2+w1-v)/(4*v)*np.exp(-0.5*(lmbda+w2+w1-v)*x)