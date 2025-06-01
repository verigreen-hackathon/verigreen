export const EVENTS_ABI = [
  {
    type: 'event',
    name: 'LandClaimed',
    inputs: [
      { name: 'owner', type: 'address', indexed: true, internalType: 'address' },
      { name: 'forestId', type: 'string', indexed: true, internalType: 'string' },
      { name: 'coordinate1', type: 'string', indexed: false, internalType: 'string' },
      { name: 'coordinate2', type: 'string', indexed: false, internalType: 'string' },
      { name: 'coordinate3', type: 'string', indexed: false, internalType: 'string' },
      { name: 'coordinate4', type: 'string', indexed: false, internalType: 'string' },
    ],
    anonymous: false,
  },
  {
    type: 'event',
    name: 'LandTilesVerified',
    inputs: [
      { name: 'owner', type: 'address', indexed: true, internalType: 'address' },
      { name: 'forestId', type: 'string', indexed: false, internalType: 'string' },
      { name: 'tilesHash', type: 'bytes32', indexed: false, internalType: 'bytes32' },
    ],
    anonymous: false,
  },
  {
    type: 'event',
    name: 'RandomNumberGenerated',
    inputs: [
      { name: 'sequenceNumber', type: 'uint64', indexed: true, internalType: 'uint64' },
      { name: 'randomNumber', type: 'uint256', indexed: false, internalType: 'uint256' },
    ],
    anonymous: false,
  },
  {
    type: 'event',
    name: 'RandomNumberRequested',
    inputs: [
      { name: 'sequenceNumber', type: 'uint64', indexed: true, internalType: 'uint64' },
      { name: 'userRandomNumber', type: 'bytes32', indexed: false, internalType: 'bytes32' },
    ],
    anonymous: false,
  },
]

export const ENTROPY_ABI = [
  {
    type: 'constructor',
    inputs: [{ name: 'entropyAddress', type: 'address', internalType: 'address' }],
    stateMutability: 'nonpayable',
  },
  {
    type: 'function',
    name: '_entropyCallback',
    inputs: [
      { name: 'sequence', type: 'uint64', internalType: 'uint64' },
      { name: 'provider', type: 'address', internalType: 'address' },
      { name: 'randomNumber', type: 'bytes32', internalType: 'bytes32' },
    ],
    outputs: [],
    stateMutability: 'nonpayable',
  },
  {
    type: 'function',
    name: 'requestRandomNumber',
    inputs: [
      { name: 'userRandomNumber', type: 'bytes32', internalType: 'bytes32' },
      { name: 'maxNumber', type: 'uint256', internalType: 'uint256' },
    ],
    outputs: [],
    stateMutability: 'payable',
  },
  {
    type: 'event',
    name: 'RandomNumberGenerated',
    inputs: [
      { name: 'sequenceNumber', type: 'uint64', indexed: true, internalType: 'uint64' },
      { name: 'randomNumber', type: 'uint256', indexed: false, internalType: 'uint256' },
    ],
    anonymous: false,
  },
  {
    type: 'event',
    name: 'RandomNumberRequested',
    inputs: [
      { name: 'sequenceNumber', type: 'uint64', indexed: true, internalType: 'uint64' },
      { name: 'userRandomNumber', type: 'bytes32', indexed: false, internalType: 'bytes32' },
    ],
    anonymous: false,
  },
  { type: 'error', name: 'InvalidSequenceNumber', inputs: [] },
]

export const VERI_GREEN_ABI = [
  {
    type: 'constructor',
    inputs: [
      { name: 'greenVerifierAddress', type: 'address', internalType: 'address' },
      { name: 'initialOwner', type: 'address', internalType: 'address' },
    ],
    stateMutability: 'nonpayable',
  },
  {
    type: 'function',
    name: 'compareStrings',
    inputs: [
      { name: '_a', type: 'string', internalType: 'string' },
      { name: '_b', type: 'string', internalType: 'string' },
    ],
    outputs: [{ name: '', type: 'bool', internalType: 'bool' }],
    stateMutability: 'pure',
  },
  {
    type: 'function',
    name: 'greenToken',
    inputs: [],
    outputs: [{ name: '', type: 'address', internalType: 'contract IVeriGreenToken' }],
    stateMutability: 'view',
  },
  {
    type: 'function',
    name: 'greenVerifier',
    inputs: [],
    outputs: [{ name: '', type: 'address', internalType: 'address' }],
    stateMutability: 'view',
  },
  {
    type: 'function',
    name: 'hashString',
    inputs: [{ name: '_a', type: 'string', internalType: 'string' }],
    outputs: [{ name: '', type: 'bytes32', internalType: 'bytes32' }],
    stateMutability: 'pure',
  },
  {
    type: 'function',
    name: 'owner',
    inputs: [],
    outputs: [{ name: '', type: 'address', internalType: 'address' }],
    stateMutability: 'view',
  },
  { type: 'function', name: 'renounceOwnership', inputs: [], outputs: [], stateMutability: 'nonpayable' },
  {
    type: 'function',
    name: 'rewardAmount',
    inputs: [],
    outputs: [{ name: '', type: 'uint256', internalType: 'uint256' }],
    stateMutability: 'view',
  },
  {
    type: 'function',
    name: 'setGreenTokenAddress',
    inputs: [{ name: 'greenTokenAddress_', type: 'address', internalType: 'address' }],
    outputs: [],
    stateMutability: 'nonpayable',
  },
  {
    type: 'function',
    name: 'setRewardAmount',
    inputs: [{ name: 'rewardAmount_', type: 'uint256', internalType: 'uint256' }],
    outputs: [],
    stateMutability: 'nonpayable',
  },
  {
    type: 'function',
    name: 'transferOwnership',
    inputs: [{ name: 'newOwner', type: 'address', internalType: 'address' }],
    outputs: [],
    stateMutability: 'nonpayable',
  },
  {
    type: 'function',
    name: 'verifyLand',
    inputs: [
      { name: 'account', type: 'address', internalType: 'address' },
      { name: 'forestId', type: 'string', internalType: 'string' },
      { name: 'coordinate1', type: 'string', internalType: 'string' },
      { name: 'coordinate2', type: 'string', internalType: 'string' },
      { name: 'coordinate3', type: 'string', internalType: 'string' },
      { name: 'coordinate4', type: 'string', internalType: 'string' },
    ],
    outputs: [],
    stateMutability: 'nonpayable',
  },
  {
    type: 'function',
    name: 'verifyTilesInLand',
    inputs: [
      { name: 'account', type: 'address', internalType: 'address' },
      { name: 'forestId', type: 'string', internalType: 'string' },
      { name: 'tilesHash', type: 'bytes32', internalType: 'bytes32' },
    ],
    outputs: [],
    stateMutability: 'nonpayable',
  },
  {
    type: 'event',
    name: 'LandClaimed',
    inputs: [
      { name: 'owner', type: 'address', indexed: true, internalType: 'address' },
      { name: 'forestId', type: 'string', indexed: true, internalType: 'string' },
      { name: 'coordinate1', type: 'string', indexed: false, internalType: 'string' },
      { name: 'coordinate2', type: 'string', indexed: false, internalType: 'string' },
      { name: 'coordinate3', type: 'string', indexed: false, internalType: 'string' },
      { name: 'coordinate4', type: 'string', indexed: false, internalType: 'string' },
    ],
    anonymous: false,
  },
  {
    type: 'event',
    name: 'LandTilesVerified',
    inputs: [
      { name: 'owner', type: 'address', indexed: true, internalType: 'address' },
      { name: 'forestId', type: 'string', indexed: false, internalType: 'string' },
      { name: 'tilesHash', type: 'bytes32', indexed: false, internalType: 'bytes32' },
    ],
    anonymous: false,
  },
  {
    type: 'event',
    name: 'OwnershipTransferred',
    inputs: [
      { name: 'previousOwner', type: 'address', indexed: true, internalType: 'address' },
      { name: 'newOwner', type: 'address', indexed: true, internalType: 'address' },
    ],
    anonymous: false,
  },
  { type: 'error', name: 'LandIsNotVerified', inputs: [] },
  { type: 'error', name: 'NotValidProver', inputs: [] },
  {
    type: 'error',
    name: 'OwnableInvalidOwner',
    inputs: [{ name: 'owner', type: 'address', internalType: 'address' }],
  },
  {
    type: 'error',
    name: 'OwnableUnauthorizedAccount',
    inputs: [{ name: 'account', type: 'address', internalType: 'address' }],
  },
]
