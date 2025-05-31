import { ethers } from 'ethers';

// Example contract interface - replace with your actual contract ABI
export const contractABI = [
    // Add your contract ABI here
];

export interface ContractConfig {
    address: string;
    abi: any[];
    provider: ethers.Provider;
    wsUrl?: string; // WebSocket URL for real-time events
}

export interface EventData {
    eventName: string;
    args: any;
    blockNumber: number;
    transactionHash: string;
}

export class ContractError extends Error {
    constructor(
        message: string,
        public readonly code: string,
        public readonly details?: any
    ) {
        super(message);
        this.name = 'ContractError';
    }
}

export class ContractListenerService {
    private contract: ethers.Contract;
    private wsProvider?: ethers.WebSocketProvider;
    private wsContract?: ethers.Contract;
    private eventListeners: Map<string, Set<(eventData: EventData) => void>> = new Map();
    private isConnected: boolean = false;
    private reconnectAttempts: number = 0;
    private readonly MAX_RECONNECT_ATTEMPTS = 5;
    private readonly RECONNECT_DELAY = 5000; // 5 seconds
    private wsUrl?: string;
    private contractConfig: ContractConfig;

    constructor(config: ContractConfig) {
        this.contractConfig = config;
        this.contract = new ethers.Contract(
            config.address,
            config.abi,
            config.provider
        );

        if (config.wsUrl) {
            this.wsUrl = config.wsUrl;
            this.initializeWebSocket(config.wsUrl, config);
        }
    }

    private async initializeWebSocket(wsUrl: string, config: ContractConfig) {
        try {
            this.wsProvider = new ethers.WebSocketProvider(wsUrl);
            this.wsContract = new ethers.Contract(
                config.address,
                config.abi,
                this.wsProvider
            );

            this.setupWebSocketHandlers();
            this.isConnected = true;
            this.reconnectAttempts = 0;
        } catch (error) {
            throw new ContractError(
                'Failed to initialize WebSocket connection',
                'WS_INIT_ERROR',
                error
            );
        }
    }

    private setupWebSocketHandlers() {
        if (!this.wsProvider) return;

        this.wsProvider.on('error', (error) => {
            console.error('WebSocket error:', error);
            this.handleWebSocketError();
        });

        this.wsProvider.on('close', () => {
            console.log('WebSocket connection closed');
            this.handleWebSocketError();
        });
    }

    private async handleWebSocketError() {
        this.isConnected = false;

        if (this.reconnectAttempts < this.MAX_RECONNECT_ATTEMPTS) {
            this.reconnectAttempts++;
            console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.MAX_RECONNECT_ATTEMPTS})...`);

            setTimeout(async () => {
                try {
                    if (this.wsProvider) {
                        await this.wsProvider.destroy();
                    }
                    // Reinitialize WebSocket connection
                    if (this.wsUrl) {
                        await this.initializeWebSocket(this.wsUrl, this.contractConfig);
                        // Reattach event listeners
                        this.reattachEventListeners();
                    }
                } catch (error) {
                    console.error('Reconnection failed:', error);
                    this.handleWebSocketError();
                }
            }, this.RECONNECT_DELAY);
        } else {
            throw new ContractError(
                'Max reconnection attempts reached',
                'WS_MAX_RECONNECT_ERROR'
            );
        }
    }

    private reattachEventListeners() {
        this.eventListeners.forEach((callbacks, eventName) => {
            callbacks.forEach(callback => {
                this.listenToEvent(eventName, callback);
            });
        });
    }

    getContractAddress(): Promise<string> {
        return this.contract.getAddress();
    }

    // Listen to a specific event
    async listenToEvent(eventName: string, callback: (eventData: EventData) => void): Promise<void> {
        try {
            // Store the callback for reconnection purposes
            if (!this.eventListeners.has(eventName)) {
                this.eventListeners.set(eventName, new Set());
            }
            this.eventListeners.get(eventName)?.add(callback);

            const contract = this.wsContract || this.contract;

            contract.on(eventName, (...args) => {
                try {
                    const event = args[args.length - 1] as ethers.EventLog;
                    const eventData: EventData = {
                        eventName: eventName,
                        args: event.args,
                        blockNumber: event.blockNumber,
                        transactionHash: event.transactionHash
                    };
                    callback(eventData);
                } catch (error) {
                    throw new ContractError(
                        `Error processing event ${eventName}`,
                        'EVENT_PROCESSING_ERROR',
                        error
                    );
                }
            });
        } catch (error) {
            throw new ContractError(
                `Error listening to event ${eventName}`,
                'EVENT_LISTEN_ERROR',
                error
            );
        }
    }

    // Get past events
    async getPastEvents(eventName: string, fromBlock?: number, toBlock?: number): Promise<EventData[]> {
        try {
            const events = await this.contract.queryFilter(
                this.contract.filters[eventName](),
                fromBlock,
                toBlock
            );

            return events.map(event => {
                if (event instanceof ethers.EventLog) {
                    return {
                        eventName: eventName,
                        args: event.args,
                        blockNumber: event.blockNumber,
                        transactionHash: event.transactionHash
                    };
                }
                throw new ContractError(
                    'Event is not an EventLog instance',
                    'INVALID_EVENT_TYPE'
                );
            });
        } catch (error) {
            throw new ContractError(
                `Error getting past events for ${eventName}`,
                'PAST_EVENTS_ERROR',
                error
            );
        }
    }

    // Stop listening to a specific event
    async stopListeningToEvent(eventName: string): Promise<void> {
        try {
            const contract = this.wsContract || this.contract;
            contract.removeAllListeners(eventName);
            this.eventListeners.delete(eventName);
        } catch (error) {
            throw new ContractError(
                `Error stopping event listener for ${eventName}`,
                'STOP_LISTENING_ERROR',
                error
            );
        }
    }

    // Cleanup method to be called when the service is no longer needed
    async cleanup(): Promise<void> {
        try {
            if (this.wsProvider) {
                await this.wsProvider.destroy();
            }
            this.eventListeners.clear();
            this.isConnected = false;
        } catch (error) {
            throw new ContractError(
                'Error during cleanup',
                'CLEANUP_ERROR',
                error
            );
        }
    }
} 