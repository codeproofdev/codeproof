# CodeProof

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Docker](https://img.shields.io/badge/Docker-ready-blue.svg)](https://www.docker.com/)

> Bitcoin-focused online judge platform. Learn development fundamentals, cryptography, Lightning, and Layer 2/3 protocols through hands-on coding challenges.

## What is CodeProof?

CodeProof is an online judge platform built specifically for learning Bitcoin development through practice. Think Codeforces, but entirely focused on Bitcoin.

We created this because there's a gap in Bitcoin education—plenty of theory, but not enough places to actually *build* and test your understanding through real coding challenges. CodeProof bridges that gap.

What makes it unique? Your accepted solutions get mined into blocks every 10 minutes. Points decrease as more people solve problems. It's competitive programming meets Bitcoin's incentive structure.

## Features

- **Blockchain-Anchored Solutions** - Every accepted solution is mined into a block
- **Dynamic Scoring** - Points decrease as more developers solve problems
- **Bitcoin-Specific Challenges** - Problems covering Bitcoin protocol, cryptography, Lightning Network, and Layer 2/3 protocols
- **Global Leaderboards** - Compete with Bitcoin developers worldwide
- **Multi-Language Support** - Code in Python, C++, Rust, JavaScript, or Go
- **Secure Sandbox** - All code runs in isolated environments using Isolate (the same system used in programming competitions)
- **Progressive Learning** - Problems organized by difficulty and topic, from basics to advanced

## Quick Start

Just clone and run:

```bash
git clone https://github.com/Forte11Cuba/codeproof.git
cd codeproof
docker-compose up
```

That's it! Access the platform:
- **Frontend**: http://localhost:3000
- **API Docs**: http://localhost:8000/docs

### Requirements

- Docker 20.10+ and Docker Compose
- 8GB+ RAM (for the judge container with compilers)
- Linux or macOS recommended (for full cgroups support)

### Optional Configuration

If you want to customize settings, copy the example environment file:

```bash
cp .env.example .env
# Edit .env with your preferences
```

## Tech Stack

**Backend**
- FastAPI with Python 3.11 for the API
- PostgreSQL 15 for data persistence
- Redis 7 for caching and job queues
- APScheduler for background jobs (block mining, score updates)
- Isolate sandbox for secure code execution

**Frontend**
- Vanilla HTML5/CSS3/JavaScript (modern and fast)
- Internationalization support (English/Spanish)

**Infrastructure**
- Docker and Docker Compose
- Microservices architecture (backend, worker, database, redis)
- Nginx for serving static content

## Project Structure

```
codeproof/
├── backend/              # FastAPI backend and judge system
│   ├── app/
│   │   ├── main.py      # Application entry point
│   │   ├── models/      # Database models
│   │   ├── routes/      # API endpoints
│   │   ├── judge/       # Code execution engine
│   │   └── jobs/        # Background tasks
│   └── Dockerfile.judge # Judge container with compilers
├── frontend/            # Static web interface
│   ├── index.html
│   ├── css/
│   └── js/
├── data/
│   └── problems/        # Problem definitions and test cases
└── docker-compose.yml   # Container orchestration
```

## Problem Categories

CodeProof organizes challenges across 5 major areas of Bitcoin development, from computer science fundamentals to cutting-edge Layer 2/3 protocols:

### Algorithms & Data Structures
Core computer science fundamentals that form the foundation of efficient Bitcoin implementations.

- **Basics**: Arrays, strings, sorting, searching
- **Search Algorithms**: Binary search, backtracking, brute force
- **Greedy Algorithms**: Optimization problems and greedy strategies
- **Divide & Conquer**: Merge sort, quicksort, recursive algorithms
- **Data Structures**: Stacks, queues, hash tables, trees, heaps, union-find
- **Graph Theory**: DFS, BFS, shortest paths, minimum spanning trees
- **Dynamic Programming**: Classic DP, knapsack problems, longest common subsequence
- **Strings**: Pattern matching, string hashing, trie structures
- **Mathematics**: Number theory, combinatorics, modular arithmetic
- **Geometry**: Computational geometry fundamentals
- **Network Flow**: Maximum flow, bipartite matching

### ₿ Bitcoin Core & Protocol
The heart of Bitcoin—learn how the protocol actually works under the hood.

- **Fundamentals**: Blockchain basics, proof-of-work, address generation
- **Transactions & Script**: Transaction structure, Bitcoin Script, Taproot, Miniscript
- **Blocks & Consensus**: Block validation, consensus rules, chain forks
- **Mining & Difficulty**: Proof-of-work mechanics, difficulty adjustment, Stratum protocol
- **UTXO & Mempool**: UTXO set management, mempool behavior, fee estimation and selection
- **P2P Network**: Peer-to-peer protocol, peer discovery, transaction relay
- **Storage & Indexing**: Chainstate database, block storage, indexing strategies

### Cryptography
Cryptographic primitives that secure Bitcoin and enable trustless transactions.

- **Hash Functions**: SHA-256, RIPEMD-160, merkle tree construction
- **Signatures & ECC**: ECDSA, Schnorr signatures, MuSig2, adaptor signatures
- **Key Management**: HD wallets, BIP32/39/44 standards, output descriptors
- **Encoding**: Base58, Bech32, Bech32m encoding schemes

### Layer 2/3 & Sidechains
Scaling solutions and off-chain protocols that extend Bitcoin's capabilities.

**Lightning Network (Layer 2)**
- **Fundamentals**: Payment channels, commitment transactions, revocation mechanisms
- **Routing**: Pathfinding algorithms, onion routing, BOLT specifications
- **Advanced**: Multi-path payments (MPP), Atomic Multi-Path (AMP), watchtowers, splicing, channel factories

**Cashu & Ecash (Layer 3)**
- **Protocol**: Blind signatures, mint operations, multi-mint federation, NUT specifications

**Sidechains & Client-Side Validation**
- **Sidechains**: Liquid Network, RSK, drivechain concepts
- **Client Validation**: RGB protocol, Taro/Taproot Assets

**State Channels & Covenants**
- **Statechains**: Statechain protocols, Mercury implementation
- **Covenants**: OP_CTV, OP_VAULT, covenant proposals and use cases

### Privacy & Security (ID: 400-499)
Privacy-enhancing techniques and security best practices for Bitcoin applications.

- **Privacy Techniques**: CoinJoin implementations, PayJoin protocol, Silent Payments
- **Chain Analysis**: UTXO clustering, transaction graph analysis, heuristics
- **Security**: Secure key storage, multisignature schemes, hardware wallets, timelocks


## Contributing

We welcome contributions! Here's the workflow:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/cool-feature`)
3. Commit your changes (`git commit -m 'Add cool feature'`)
4. Push to the branch (`git push origin feature/cool-feature`)
5. Open a Pull Request

## Adding New Problems

Problems are defined in YAML format in `data/problems/` with:
- Metadata (title, description, difficulty)
- Test cases (input/output)
- Resource limits (time, memory)
- Reference solution

This separation keeps the platform code clean and lets educators focus on creating great learning content.

## Educational Philosophy

CodeProof intentionally separates platform code from educational content (problems). Here's why:

- **Content Independence** - Educators can create and modify problems without touching infrastructure code
- **Curriculum Flexibility** - Easy to adapt for different learning levels and teaching approaches
- **Quality Focus** - Platform developers focus on the best judging system; Bitcoin experts focus on great problems
- **Open Ecosystem** - Community can contribute problems while maintaining platform quality

This design lets CodeProof serve as infrastructure for multiple educational initiatives across Latin America and beyond.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

**Built with 🧡 by Forte11Cuba**
