import json
import time
import requests

from hashlib import sha256
from flask import Flask, request

class Block:
	"""
	Block object for blocks.
	"""
	
	def __init__(self, index, timestamp, transaction, pointer, previous_hash):
		"""
		index: index of the Block.
		timestamp: clicking event time stamp.
		transaction: transaction event record.
		pointer: the pointer/address pointing to the requested song.
		previous_hash: hash value of the previous block.

		--> maybe we will need to add another parameter, smart-contract.
		"""

		self.index = index
		self.timestamp = timestamp
		self.transactions = transaction
		self.pointer = pointer
		self.previous_hash = previous_hash
		self.nonce = 0 #used for PoW

	def block_hash(self):
		"""
		return the hash value of the block.
		"""

		sha = sha256()
		block_string = str(self.index) + str(self.timestamp) \
					+ str(self.transactions) + str(self.pointer) \
					+ str(self.previous_hash) + str(self.nonce)

		sha.update(block_string)

		return sha.hexdigest()
		
class Blockchain:
	"""
	Blockchain object for blockchain.
	"""

	difficulty = 0 #PoW algorithm difficulty

	def __init__(self):
		self.transaction_pending = list()
		self.chain = list()

		# initialize the genesis block and append to the chain. index = 0, previous_hash = 0
		first_block = Block(0, time.time(), 
							[], "Not pointing to any music", 0)
		
		first_block.hash = first_block.block_hash()
		self.chain.append(first_block)

	def add_new_block(self, block, proof):
		"""
		add newly created block to the chain.
		need to verify PoW first.
		"""

		#Check if previous block hash matches
		last_block = self.chain[-1]
		if block.previous_hash != last_block.hash:
			return False #"Previous block hash value does not match."

		#Check if proof is valid
		valid = proof.startswith("0" * Blockchain.difficulty)
		valid =  (proof == block.block_hash())
				
		if not valid:
			return False #"Not valid proof as it does not match block hash"

		block.hash = proof
		self.chain.append(block)
	
		return True

	def proof_of_work(self, block):
		"""
		iteratively finds the valid hash value that satisfies our criteria.
		"""
		block.nonce = 0 #make sure to reset the nonce value to zero

		block_hash = block.block_hash()
		while not block_hash.startswith("0" * Blockchain.difficulty):
			block.nonce += 1 #increase nonce value to find valid proof
			block_hash = block.block_hash() #updated block hash

		return block_hash

	def add_new_transaction(self, transaction):
		self.transaction_pending.append(transaction)

	@classmethod
	def check_chain_validity(cls, chain):
		previous_hash = "0"
		result = True

		for block in chain:
			block_hash = block.hash
			delattr(block, "hash") #remove to recompute

			valid = proof.startswith("0" * Blockchain.difficulty)
			valid =  (proof == block.block_hash())

			if not valid or previous_hash != block.previous_hash:
				result =  False
				break

			block.hash, previous_hash = block_hash, block_hash

		return result

	def mine(self, pointer=None):
		"""
		add pending transaction to the new block and add new block to the chain
		"""
		if not self.transaction_pending:
			return False #"no pending transaction awaiting"

		new_block = Block(index=self.chain[-1].index+1,
						timestamp=time.time(),
						transaction=self.transaction_pending,
						pointer=pointer,
						previous_hash=self.chain[-1].hash)

		proof = self.proof_of_work(new_block)
		self.add_new_block(new_block, proof)

		self.transaction_pending = list()
		announce_new_block(new_block) #announce to the network
		return new_block.index



##------------------------------------------------------------------------------##




app = Flask(__name__)

# the node's copy of blockchain
blockchain = Blockchain()

# the address to other participating members of the network
peers = set()


# endpoint to submit a new transaction. This will be used by
# our application to add new data (posts) to the blockchain
@app.route('/new_transaction', methods=['POST'])
def new_transaction():
    tx_data = request.get_json()
    required_fields = ["song","listener","artist"]

    for field in required_fields:
        if not tx_data.get(field):
            return "Invlaid transaction data", 404

    tx_data["timestamp"] = time.time()

    blockchain.add_new_transaction(tx_data)

    return "Success", 201


# endpoint to return the node's copy of the chain.
# Our application will be using this endpoint to query
# all the posts to display.
@app.route('/chain', methods=['GET'])
def get_chain():
    # make sure we've the longest chain
    consensus()
    chain_data = []
    for block in blockchain.chain:
        chain_data.append(block.__dict__)
    return json.dumps({"length": len(chain_data),
                       "chain": chain_data})


# endpoint to request the node to mine the unconfirmed
# transactions (if any). We'll be using it to initiate
# a command to mine from our application itself.
@app.route('/mine', methods=['GET'])
def mine_pending_transaction():
    result = blockchain.mine()
    if not result:
        return "No transaction to mine"
    return "Block #{} is mined.".format(result)


# endpoint to add new peers to the network.
@app.route('/add_nodes', methods=['POST'])
def register_new_peers():
    nodes = request.get_json()
    if not nodes:
        return "Invalid data", 400
    for node in nodes:
        peers.add(node)

    return "Success", 201


# endpoint to add a block mined by someone else to
# the node's chain. The block is first verified by the node
# and then added to the chain.
@app.route('/add_block', methods=['POST'])
def validate_and_add_block():
    block_data = request.get_json()
    block = Block(block_data["index"],
                  block_data["transactions"],
                  block_data["timestamp",
                  block_data["previous_hash"]])

    proof = block_data['hash']
    added = blockchain.add_block(block, proof)

    if not added:
        return "The block was discarded by the node", 400

    return "Block added to the chain", 201


# endpoint to query unconfirmed transactions
@app.route('/pending_tx')
def get_pending_tx():
    return json.dumps(blockchain.transaction_pending)


def consensus():
    """
    Our simple consnsus algorithm. If a longer valid chain is
    found, our chain is replaced with it.
    """
    global blockchain

    longest_chain = None
    current_len = len(blockchain.chain)

    for node in peers:
        response = requests.get('http://{}/chain'.format(node))
        length = response.json()['length']
        chain = response.json()['chain']
        if length > current_len and blockchain.check_chain_validity(chain):
            current_len = length
            longest_chain = chain

    if longest_chain:
        blockchain = longest_chain
        return True

    return False


def announce_new_block(block):
    """
    A function to announce to the network once a block has been mined.
    Other blocks can simply verify the proof of work and add it to their
    respective chains.
    """
    for peer in peers:
        url = "http://{}/add_block".format(peer)
        requests.post(url, data=json.dumps(block.__dict__, sort_keys=True))


app.run(debug=True, port=8000)































