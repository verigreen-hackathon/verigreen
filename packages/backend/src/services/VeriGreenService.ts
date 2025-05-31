import { ContractListenerService, ContractConfig, EventData } from '../contracts/ContractListenerService';
import { ethers } from 'ethers';
import { PrismaClient } from '@prisma/client';
import { ContractEventData, TransferEventData, ApprovalEventData, MintEventData, BurnEventData } from '../types/events';

export class VeriGreenService {
    private contractService: ContractListenerService;
    private prisma: PrismaClient;
    private isListening: boolean = false;

    constructor(
        contractConfig: ContractConfig,
        private readonly eventTypes: string[] = ['Transfer', 'Approval', 'Mint', 'Burn']
    ) {
        this.contractService = new ContractListenerService(contractConfig);
        this.prisma = new PrismaClient();
    }

    async startListening(): Promise<void> {
        if (this.isListening) {
            throw new Error('Service is already listening to events');
        }

        try {
            // Start listening to each event type
            for (const eventType of this.eventTypes) {
                await this.contractService.listenToEvent(eventType, async (eventData: EventData) => {
                    await this.handleEvent(eventData);
                });
            }

            this.isListening = true;
            console.log('Started listening to VeriGreen contract events');
        } catch (error) {
            console.error('Error starting event listeners:', error);
            throw error;
        }
    }

    async stopListening(): Promise<void> {
        if (!this.isListening) {
            return;
        }

        try {
            // Stop listening to each event type
            for (const eventType of this.eventTypes) {
                await this.contractService.stopListeningToEvent(eventType);
            }

            this.isListening = false;
            console.log('Stopped listening to VeriGreen contract events');
        } catch (error) {
            console.error('Error stopping event listeners:', error);
            throw error;
        }
    }

    private async handleEvent(eventData: EventData): Promise<void> {
        try {
            // Format the event data based on event type
            const formattedData = this.formatEventData(eventData);

            // Save to database
            await this.saveEventToDatabase(formattedData);
        } catch (error) {
            console.error('Error handling event:', error);
            // You might want to implement retry logic or error reporting here
        }
    }

    private formatEventData(eventData: EventData): ContractEventData {
        const { eventName, args, blockNumber, transactionHash } = eventData;

        // Format data based on event type
        switch (eventName) {
            case 'Transfer':
                return {
                    type: 'TRANSFER',
                    from: args[0],
                    to: args[1],
                    amount: args[2].toString(),
                    blockNumber,
                    transactionHash
                } as TransferEventData;

            case 'Approval':
                return {
                    type: 'APPROVAL',
                    owner: args[0],
                    spender: args[1],
                    amount: args[2].toString(),
                    blockNumber,
                    transactionHash
                } as ApprovalEventData;

            case 'Mint':
                return {
                    type: 'MINT',
                    to: args[0],
                    amount: args[1].toString(),
                    blockNumber,
                    transactionHash
                } as MintEventData;

            case 'Burn':
                return {
                    type: 'BURN',
                    from: args[0],
                    amount: args[1].toString(),
                    blockNumber,
                    transactionHash
                } as BurnEventData;

            default:
                throw new Error(`Unsupported event type: ${eventName}`);
        }
    }

    private async saveEventToDatabase(formattedData: ContractEventData): Promise<void> {
        try {
            // Check if event already exists to prevent duplicates
            const existingEvent = await this.prisma.contractEvent.findFirst({
                where: {
                    transactionHash: formattedData.transactionHash,
                    type: formattedData.type
                }
            });

            if (existingEvent) {
                console.log(`Event already exists: ${formattedData.transactionHash}`);
                return;
            }

            await this.prisma.contractEvent.create({
                data: {
                    type: formattedData.type,
                    data: formattedData,
                    blockNumber: formattedData.blockNumber,
                    transactionHash: formattedData.transactionHash,
                    timestamp: new Date()
                }
            });
        } catch (error) {
            console.error('Error saving event to database:', error);
            throw error;
        }
    }

    async getPastEvents(eventType: string, fromBlock?: number, toBlock?: number): Promise<ContractEventData[]> {
        try {
            const events = await this.contractService.getPastEvents(eventType, fromBlock, toBlock);
            return events.map((event: EventData) => this.formatEventData(event));
        } catch (error) {
            console.error('Error getting past events:', error);
            throw error;
        }
    }

    // MongoDB-specific query methods
    async getEventsByAddress(address: string): Promise<ContractEventData[]> {
        try {
            const events = await this.prisma.contractEvent.findMany({
                where: {
                    OR: [
                        { data: { path: ['from'], equals: address } },
                        { data: { path: ['to'], equals: address } },
                        { data: { path: ['owner'], equals: address } },
                        { data: { path: ['spender'], equals: address } }
                    ]
                },
                orderBy: {
                    blockNumber: 'desc'
                }
            });

            return events.map((event: any) => event.data as ContractEventData);
        } catch (error) {
            console.error('Error getting events by address:', error);
            throw error;
        }
    }

    async getEventsByType(type: string, limit: number = 100): Promise<ContractEventData[]> {
        try {
            const events = await this.prisma.contractEvent.findMany({
                where: {
                    type: type.toUpperCase()
                },
                orderBy: {
                    blockNumber: 'desc'
                },
                take: limit
            });

            return events.map((event: any) => event.data as ContractEventData);
        } catch (error) {
            console.error('Error getting events by type:', error);
            throw error;
        }
    }

    async getLatestBlockNumber(): Promise<number> {
        try {
            const latestEvent = await this.prisma.contractEvent.findFirst({
                orderBy: {
                    blockNumber: 'desc'
                }
            });

            return latestEvent?.blockNumber || 0;
        } catch (error) {
            console.error('Error getting latest block number:', error);
            throw error;
        }
    }

    async cleanup(): Promise<void> {
        try {
            await this.stopListening();
            await this.contractService.cleanup();
            await this.prisma.$disconnect();
        } catch (error) {
            console.error('Error during cleanup:', error);
            throw error;
        }
    }
} 