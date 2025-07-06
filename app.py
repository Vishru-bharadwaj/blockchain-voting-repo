import hashlib
import json
import random
from flask import Flask, request, jsonify, render_template
from py_ecc.bn128 import add, multiply, G1, G2, pairing
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

# In-memory storage
voters = {}  # {voter_id: public_key}
blockchain = []  # Stores blocks
voted_voters = set()  # Keeps track of voters who have voted

# Merkle Tree Implementation
class MerkleTree:
    def __init__(self, data):
        self.leaves = [hashlib.sha256(d.encode()).hexdigest() for d in data]
        self.tree = self.build_tree(self.leaves)
    
    def build_tree(self, leaves):
        if not leaves:  # Add this base case
            return []  # Return an empty list for empty leaves
        if len(leaves) == 1:
            return leaves
        
        next_level = []
        for i in range(0, len(leaves), 2):
            combined = leaves[i] + (leaves[i+1] if i+1 < len(leaves) else '')
            next_level.append(hashlib.sha256(combined.encode()).hexdigest())
        
        return self.build_tree(next_level)
    
    def get_root(self):
        return self.tree[0] if self.tree else None

# Blockchain Implementation
class Block:
    def __init__(self, index, previous_hash, votes, merkle_root, nonce=0):
        self.index = index
        self.previous_hash = previous_hash
        self.votes = votes
        self.merkle_root = merkle_root
        self.nonce = nonce
        self.hash = self.compute_hash()
    
    def compute_hash(self):
        block_string = json.dumps({
            "index": self.index,
            "previous_hash": self.previous_hash,
            "votes": self.votes,
            "merkle_root": self.merkle_root,
            "nonce": self.nonce
        }, sort_keys=True)
        return hashlib.sha256(block_string.encode()).hexdigest()
    
    def mine_block(self, difficulty):
        while not self.hash.startswith('0' * difficulty):
            self.nonce += 1
            self.hash = self.compute_hash()

# ZKP-Based Voter Authentication
def generate_zkp(secret):
    g = G1  # Generator
    h = multiply(G1, secret)
    r = random.randint(1, 10**6)
    commitment = multiply(G1, r)
    challenge = random.randint(1, 10**6)
    response = r + challenge * secret
    return h, commitment, challenge, response

def verify_zkp(public_key, commitment, challenge, response):
    expected_commitment = add(commitment, multiply(public_key, challenge))  # Compute expected value
    actual_commitment = multiply(G1, response)  # Compute response side

    print(f"🔹 [ZKP Backend] Expected Commitment (RHS): {expected_commitment}")
    print(f"🔹 [ZKP Backend] Actual Commitment (LHS): {actual_commitment}")
    print(f"🔹 [ZKP Backend] Challenge: {challenge}")
    print(f"🔹 [ZKP Backend] Response: {response}")
    print(f"🔹 [ZKP Backend] Public Key: {public_key}")
    print(f"🔹 [ZKP Backend] Commitment Sent: {commitment}")

    return actual_commitment == expected_commitment


# Create Genesis Block
def create_genesis_block():
    genesis_votes = []  # Genesis block has no votes
    genesis_merkle_tree = MerkleTree(genesis_votes)
    genesis_block = Block(0, "0", genesis_votes, genesis_merkle_tree.get_root())
    genesis_block.mine_block(difficulty=4)  # Mine the genesis block
    return genesis_block

# Initialize Blockchain with Genesis Block
blockchain.append(create_genesis_block())

@app.route('/register', methods=['POST'])
def register():
    data = request.json
    voter_id = data['voter_id']
    secret = data['secret']
    public_key = multiply(G1, secret)

    if voter_id in voters:
        return jsonify({'error': 'Voter already registered'}), 400

    voters[voter_id] = public_key

    print(f"✅ [REGISTER] Voter ID: {voter_id}, Secret: {secret}, Public Key: {public_key}")

    return jsonify({'message': 'Voter registered successfully', 'public_key': str(public_key)})


@app.route('/vote', methods=['POST'])
def vote():
    data = request.json
    voter_id = data['voter_id']
    vote_choice = data['vote']
    r = data['r']  # Receive only r
    challenge = data['challenge']
    response = data['response']

    if voter_id not in voters:
        return jsonify({'error': 'Voter not registered'}), 400
    if voter_id in voted_voters:
        return jsonify({'error': 'Voter has already voted'}), 400
    public_key = voters[voter_id]

    # Compute commitment in the backend
    commitment = multiply(G1, r)

    print(f"🔹 Received ZKP: Commitment={commitment}, Challenge={challenge}, Response={response}")
    print(f"🔹 Expected Public Key: {public_key}")

    if not verify_zkp(public_key, commitment, challenge, response):
        return jsonify({'error': 'Invalid ZKP authentication'}), 400
    voted_voters.add(voter_id)
    previous_hash = blockchain[-1].hash if blockchain else "0" * 64

    # Create new block with vote
    votes = [vote_choice]
    merkle_tree = MerkleTree(votes)
    new_block = Block(len(blockchain), previous_hash, votes, merkle_tree.get_root())
    new_block.mine_block(difficulty=4)  # PoW
    blockchain.append(new_block)

    return jsonify({'message': 'Vote recorded', 'block_hash': new_block.hash, 'merkle_root': new_block.merkle_root})



@app.route('/results', methods=['GET'])
def results():
    # Count votes
    vote_count = {}
    for block in blockchain:
        for vote in block.votes:
            vote_count[vote] = vote_count.get(vote, 0) + 1

    # Determine the winner
    if vote_count:
        winner = max(vote_count, key=vote_count.get)
    else:
        winner = "No votes yet"

    chain_data = [{
        "index": block.index,
        "previous_hash": block.previous_hash,
        "votes": block.votes,
        "merkle_root": block.merkle_root,
        "hash": block.hash
    } for block in blockchain]

    return jsonify({
        'blockchain': chain_data,
        'vote_count': vote_count,
        'winner': winner
    })

@app.route('/')
def home():
    return render_template("index.html")

if __name__ == '__main__':
    print("-------------app is starting------------")
    app.run(host='0.0.0.0', port=5000, debug=True)

