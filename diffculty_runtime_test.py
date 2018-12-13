"""
This file is used to simulate the block generation process 
to extract computation time with respect to difficulty

- UCB CE290I: Teng Zeng, Zining Wang, Qianhua Luo
"""
from hashlib import sha256
import matplotlib.pyplot as plt
import numpy as np
import time
import json

def generate_block_hash(difficulty, previous_hash, nonce, index):
	
	sha = sha256()
	# generate "block"
	timestamp = time.time()
	block_string = str(index) + str(timestamp) + str(previous_hash) + str(nonce)
	sha.update(block_string)
	hash_val = sha.hexdigest()

	return hash_val



difficulty_attemp = 6
boxplot_list = list()
meanplot_list = list()

for difficulty in range(difficulty_attemp):

	print("Starting with difficulty = " + str(difficulty))

	nonce = 0
	previous_hash = 0
	index = -1

	attempt_list = range(30)
	computationTime_list = list()

	# initialize hash value
	hash_val = generate_block_hash(difficulty, previous_hash, nonce, index)

	for index in attempt_list:

		t_start = time.time()
		while not hash_val.startswith("0" * difficulty):

				nonce += 1 #increase nonce value to find valid proof
				hash_val = generate_block_hash(difficulty, previous_hash, nonce, index) #updated block hash
		
		t_end = time.time()
		computationTime_list.append(t_end - t_start)

		previous_hash = hash_val

	boxplot_list.append(computationTime_list)
	meanplot_list.append(np.mean(computationTime_list))

# plt.boxplot(boxplot_list, notch=True, positions = range(difficulty_attemp), widths = 0.6)
plt.scatter(range(difficulty_attemp), meanplot_list, marker="x", color="r")
plt.title("Difficulty vs Computation Time", fontsize=18)
plt.xlabel("Difficulty", fontsize=14)
plt.xticks(range(difficulty_attemp))
plt.ylabel("Time takes to mine", fontsize=14)
plt.ylim([-0.001, 0.08])
plt.show()

for elem in meanplot_list:
	print(elem)