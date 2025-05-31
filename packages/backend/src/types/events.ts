export interface BaseEventData {
    type: string;
    blockNumber: number;
    transactionHash: string;
    timestamp?: Date;
}

export interface TransferEventData extends BaseEventData {
    type: 'TRANSFER';
    from: string;
    to: string;
    amount: string;
}

export interface ApprovalEventData extends BaseEventData {
    type: 'APPROVAL';
    owner: string;
    spender: string;
    amount: string;
}

export interface MintEventData extends BaseEventData {
    type: 'MINT';
    to: string;
    amount: string;
}

export interface BurnEventData extends BaseEventData {
    type: 'BURN';
    from: string;
    amount: string;
}

export type ContractEventData =
    | TransferEventData
    | ApprovalEventData
    | MintEventData
    | BurnEventData; 