import express, { Request, Response, NextFunction } from 'express';
import { WhatsAppSessionManager } from './manager';
import { config } from './config';

const app = express();
app.use(express.json());

// Logger Middleware
app.use((req: Request, res: Response, next: NextFunction) => {
  console.log(`[HTTP] ${req.method} ${req.url}`);
  next();
});

// Authentication Middleware
const authenticate = (req: Request, res: Response, next: NextFunction) => {
  const authHeader = req.headers.authorization;
  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    console.warn(`[Auth] Unauthorized request: Missing or invalid Authorization header.`);
    return res.status(401).json({ status: 'error', message: 'Unauthorized: Missing or invalid token.' });
  }

  const token = authHeader.substring(7);
  if (token !== config.apiKey) {
    console.warn(`[Auth] Unauthorized request: Provided token does not match config API Key.`);
    return res.status(401).json({ status: 'error', message: 'Unauthorized: Invalid token.' });
  }

  next();
};

app.use(authenticate);

// Send message endpoint
app.post('/api/v1/whatsapp/send', async (req: Request, res: Response) => {
  const { company_id, to, message } = req.body;

  if (!company_id || !to || !message) {
    return res.status(400).json({
      status: 'error',
      message: 'Missing required parameters: company_id, to, and message are required.'
    });
  }

  console.log(`[API] Received send message request for company ${company_id} to ${to}`);
  
  try {
    const success = await WhatsAppSessionManager.getInstance().sendMessage(company_id, to, message);
    if (success) {
      return res.status(200).json({ status: 'success', message: 'Message enqueued successfully.' });
    } else {
      return res.status(500).json({
        status: 'error',
        message: 'Failed to send message. Ensure session is CONNECTED.'
      });
    }
  } catch (err: any) {
    console.error(`[API] Error sending message:`, err);
    return res.status(500).json({ status: 'error', message: err.message || String(err) });
  }
});

// Get session status endpoint
app.get('/api/v1/whatsapp/session/:company_id/status', (req: Request, res: Response) => {
  const { company_id } = req.params;
  
  if (!company_id) {
    return res.status(400).json({ status: 'error', message: 'company_id parameter is required.' });
  }

  const session = WhatsAppSessionManager.getInstance().getSession(company_id);
  return res.status(200).json({
    companyId: session.companyId,
    status: session.status,
    errorMessage: session.errorMessage
  });
});

// Get session QR endpoint
app.get('/api/v1/whatsapp/session/:company_id/qr', (req: Request, res: Response) => {
  const { company_id } = req.params;

  if (!company_id) {
    return res.status(400).json({ status: 'error', message: 'company_id parameter is required.' });
  }

  const session = WhatsAppSessionManager.getInstance().getSession(company_id);
  return res.status(200).json({
    companyId: session.companyId,
    status: session.status,
    qrCode: session.qrCode,
    errorMessage: session.errorMessage
  });
});

// Initialize session endpoint
app.post('/api/v1/whatsapp/session/:company_id/initialize', async (req: Request, res: Response) => {
  const { company_id } = req.params;

  if (!company_id) {
    return res.status(400).json({ status: 'error', message: 'company_id parameter is required.' });
  }

  console.log(`[API] Request to initialize session for company ${company_id}`);

  try {
    const session = await WhatsAppSessionManager.getInstance().initializeSession(company_id);
    return res.status(200).json({
      companyId: session.companyId,
      status: session.status,
      errorMessage: session.errorMessage
    });
  } catch (err: any) {
    console.error(`[API] Error initializing session:`, err);
    return res.status(500).json({ status: 'error', message: err.message || String(err) });
  }
});

// Error handling middleware
app.use((err: any, req: Request, res: Response, next: NextFunction) => {
  console.error('[Error] Unhandled Express Error:', err);
  return res.status(500).json({ status: 'error', message: 'Internal Server Error' });
});

// Start the server
const server = app.listen(config.port, () => {
  console.log(`🚀 InternoCore WhatsApp Gateway running on port ${config.port}`);
});

// Graceful Shutdown
process.on('SIGTERM', () => {
  console.log('SIGTERM signal received: closing HTTP server');
  server.close(() => {
    console.log('HTTP server closed');
  });
});
