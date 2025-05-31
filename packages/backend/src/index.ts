import express from 'express';
import cors from 'cors';
import dotenv from 'dotenv';
import { ethers } from 'ethers';
import { VeriGreenService } from './services/VeriGreenService';
import addressRoutes from './routes/address.routes';

// Load environment variables
dotenv.config();

const app = express();
const port = process.env.PORT || 3000;

// Middleware
app.use(cors());
app.use(express.json());

// Initialize ethers provider
const provider = new ethers.JsonRpcProvider(process.env.RPC_URL);

// Initialize VeriGreenService
const veriGreenService = new VeriGreenService({
    address: process.env.CONTRACT_ADDRESS || '',
    abi: [], // Add your contract ABI here
    provider: provider,
    wsUrl: process.env.WS_URL
});

// Start listening to events
veriGreenService.startListening().catch(console.error);

// Routes
app.use('/api/address', addressRoutes);

// API Endpoints
app.get('/health', (req, res) => {
    res.json({ status: 'ok' });
});

// Get past events with block range
app.get('/events/:type', async (req, res) => {
    try {
        const { type } = req.params;
        const { fromBlock, toBlock } = req.query;

        const events = await veriGreenService.getPastEvents(
            type,
            fromBlock ? parseInt(fromBlock as string) : undefined,
            toBlock ? parseInt(toBlock as string) : undefined
        );

        res.json(events);
    } catch (error) {
        console.error('Error fetching events:', error);
        res.status(500).json({ error: 'Failed to fetch events' });
    }
});

// Get events by address
app.get('/events/address/:address', async (req, res) => {
    try {
        const { address } = req.params;
        const events = await veriGreenService.getEventsByAddress(address);
        res.json(events);
    } catch (error) {
        console.error('Error fetching events by address:', error);
        res.status(500).json({ error: 'Failed to fetch events by address' });
    }
});

// Get events by type with limit
app.get('/events/type/:type', async (req, res) => {
    try {
        const { type } = req.params;
        const { limit } = req.query;
        const events = await veriGreenService.getEventsByType(
            type,
            limit ? parseInt(limit as string) : undefined
        );
        res.json(events);
    } catch (error) {
        console.error('Error fetching events by type:', error);
        res.status(500).json({ error: 'Failed to fetch events by type' });
    }
});

// Get latest block number
app.get('/latest-block', async (req, res) => {
    try {
        const blockNumber = await veriGreenService.getLatestBlockNumber();
        res.json({ blockNumber });
    } catch (error) {
        console.error('Error fetching latest block:', error);
        res.status(500).json({ error: 'Failed to fetch latest block' });
    }
});

// Start server
app.listen(port, () => {
    console.log(`Server is running on port ${port}`);
});

// Handle cleanup on process termination
process.on('SIGINT', async () => {
    console.log('Cleaning up...');
    await veriGreenService.cleanup();
    process.exit(0);
}); 