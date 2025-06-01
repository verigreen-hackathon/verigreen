import express from 'express'
import cors from 'cors'
import dotenv from 'dotenv'
import submissionRoutes from './routes/submissions.routes'
import { prisma } from './config/prisma'

// Load environment variables
dotenv.config()

const app = express()
const port = process.env.PORT || 3000

// Middleware
app.use(cors())
app.use(express.json())

// Routes
app.use('/api/address', submissionRoutes)

async function main() {
  try {
    await prisma.$connect()
  } catch (error) {
    console.error(error)
    process.exit(1)
  }
}

main()

// API Endpoints
app.get('/health', (req, res) => {
  res.json({ success: true, data: 'ok', message: null })
})

// Start server
app.listen(port, () => {
  console.log(`Server is running on port ${port}`)
})

process.addListener('unhandledRejection', (reason, promise) => {
  console.error(reason, promise)
})

process.addListener('uncaughtException', (error) => {
  console.error(error)
})
