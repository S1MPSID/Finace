# ComplianceAudit Hardhat Project

This project contains the `ComplianceAudit` smart contract and a Hardhat 3 test setup using `mocha` + `ethers`.

Deployed on **Base Sepolia**: `0xF1FB4e26CdeF0927dD8AC9e6633fFdFe42EFc150`  
See also root [blockchain.md](../blockchain.md) and [SESSION_HISTORY.md](../SESSION_HISTORY.md).

## Requirements

- Node.js 20+
- `pnpm`

## Install

```bash
pnpm install
```

## Compile

```bash
pnpm build
```

## Run Tests

Run tests on Hardhat in-memory network:

```bash
pnpm test
```

Run tests on local Ganache RPC (`127.0.0.1:8545`):

```bash
pnpm test:ganache
```

## Start Ganache Locally

In terminal 1:

```bash
pnpm ganache:start
```

Ganache starts on:

- RPC URL: `http://127.0.0.1:8545`
- Chain ID: `1337`

## Deploy ComplianceAudit to Local Ganache

In terminal 2 (after Ganache is running):

```bash
pnpm deploy:ganache
```

Deployment script:

- `scripts/deployCompliance.ts`

## Useful Hardhat Networks in Config

- `ganache` -> `http://127.0.0.1:8545`
- `localhost` -> `http://127.0.0.1:8545`
- `hardhatMainnet` (simulated)
- `hardhatOp` (simulated)
- `sepolia` (requires config variables)
