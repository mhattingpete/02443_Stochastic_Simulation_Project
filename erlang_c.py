from scipy.special import factorial
import numpy as np

E = 8
m = 10

i = np.arange(m)
p_q = (((E**m)/factorial(m))*(m/(m-E)))/(np.sum(E**i/factorial(i))+((E**m/factorial(m))*(m/(m-E))))