import { Client, LocalAuth } from 'whatsapp-web.js';
import qrcode from 'qrcode';
import path from 'path';
import fs from 'fs';
import { config } from './config';

export type SessionStatus = 'NOT_INITIALIZED' | 'QR_READY' | 'AUTHENTICATING' | 'CONNECTED' | 'DISCONNECTED' | 'FAILED';

export interface SessionInfo {
  companyId: string;
  status: SessionStatus;
  qrCode?: string; // Base64 Data URL
  client?: Client;
  queue?: CompanyQueue;
  errorMessage?: string;
}

interface MessageJob {
  to: string;
  message: string;
  resolve: (value: boolean) => void;
}

class CompanyQueue {
  private queue: MessageJob[] = [];
  private processing = false;
  private delayMin = 1500;
  private delayMax = 3000;

  constructor(private client: Client) {}

  public enqueue(to: string, message: string): Promise<boolean> {
    return new Promise((resolve) => {
      this.queue.push({ to, message, resolve });
      this.processNext();
    });
  }

  private async processNext() {
    if (this.processing || this.queue.length === 0) return;
    this.processing = true;

    const job = this.queue.shift();
    if (job) {
      let success = false;
      try {
        console.log(`[Queue] Sending message to ${job.to}...`);

        let chatId: string;

        if (job.to.includes('@g.us')) {
          // Group JID — use as-is
          chatId = job.to;
        } else {
          // Individual number — resolve LID via getNumberId to avoid "No LID for user" error
          const cleanNumber = job.to.replace(/\D/g, '');
          const numberId = await this.client.getNumberId(cleanNumber);
          if (!numberId) {
            throw new Error(`Number ${job.to} is not registered on WhatsApp`);
          }
          chatId = numberId._serialized;
          console.log(`[Queue] Resolved number ${job.to} -> ${chatId}`);
        }

        await this.client.sendMessage(chatId, job.message);
        success = true;
        console.log(`[Queue] Message successfully delivered to ${chatId}`);
      } catch (err: any) {
        console.error(`[Queue] Failed to send to ${job.to}:`, err);
        success = false;
      }

      job.resolve(success);

      // Generate a humanized random delay between delayMin and delayMax
      const delay = Math.floor(Math.random() * (this.delayMax - this.delayMin + 1) + this.delayMin);
      console.log(`[Queue] Applying human delay of ${delay}ms before next message...`);
      setTimeout(() => {
        this.processing = false;
        this.processNext();
      }, delay);
    } else {
      this.processing = false;
    }
  }
}

export class WhatsAppSessionManager {
  private static instance: WhatsAppSessionManager;
  private sessions: Map<string, SessionInfo> = new Map();

  private constructor() {
    // Ensure sessions path exists
    if (!fs.existsSync(config.sessionsPath)) {
      fs.mkdirSync(config.sessionsPath, { recursive: true });
    }
  }

  public static getInstance(): WhatsAppSessionManager {
    if (!WhatsAppSessionManager.instance) {
      WhatsAppSessionManager.instance = new WhatsAppSessionManager();
    }
    return WhatsAppSessionManager.instance;
  }

  public getSession(companyId: string): SessionInfo {
    const session = this.sessions.get(companyId);
    if (!session) {
      return { companyId, status: 'NOT_INITIALIZED' };
    }
    return {
      companyId: session.companyId,
      status: session.status,
      qrCode: session.qrCode,
      errorMessage: session.errorMessage
    };
  }

  public async initializeSession(companyId: string): Promise<SessionInfo> {
    let session = this.sessions.get(companyId);

    // If already connected or authenticating, do not re-initialize
    if (session && (session.status === 'CONNECTED' || session.status === 'AUTHENTICATING')) {
      console.log(`[Manager] Session for company ${companyId} already in status ${session.status}`);
      return this.getSession(companyId);
    }

    // Clean up existing client if present
    if (session && session.client) {
      try {
        await session.client.destroy();
      } catch (e) {
        console.warn(`[Manager] Error destroying previous client for company ${companyId}:`, e);
      }
    }

    // Remove stale Chromium SingletonLock left by previous crashed/restarted process
    const sessionDir = path.join(config.sessionsPath, `session-${companyId}`);
    const lockFile = path.join(sessionDir, 'SingletonLock');
    if (fs.existsSync(lockFile)) {
      try {
        fs.unlinkSync(lockFile);
        console.log(`[Manager] Removed stale Chromium lock for company ${companyId}`);
      } catch (e) {
        console.warn(`[Manager] Could not remove lock file for company ${companyId}:`, e);
      }
    }

    console.log(`[Manager] Initializing new session for company ${companyId}...`);

    const client = new Client({
      authStrategy: new LocalAuth({
        clientId: companyId,
        dataPath: config.sessionsPath
      }),
      puppeteer: {
        headless: true,
        args: [
          '--no-sandbox',
          '--disable-setuid-sandbox',
          '--disable-dev-shm-usage',
          '--disable-accelerated-2d-canvas',
          '--no-first-run',
          '--no-zygote',
          '--single-process',
          '--disable-gpu'
        ]
      }
    });

    session = {
      companyId,
      status: 'NOT_INITIALIZED',
      client,
      queue: new CompanyQueue(client)
    };
    this.sessions.set(companyId, session);

    // Setup event listeners
    client.on('qr', async (qr) => {
      console.log(`[Manager] QR Code generated for company ${companyId}`);
      try {
        const qrCodeDataUrl = await qrcode.toDataURL(qr);
        const currentSession = this.sessions.get(companyId);
        if (currentSession) {
          currentSession.status = 'QR_READY';
          currentSession.qrCode = qrCodeDataUrl;
        }
      } catch (err: any) {
        console.error(`[Manager] Error generating QR Data URL for company ${companyId}:`, err);
      }
    });

    client.on('authenticated', () => {
      console.log(`[Manager] Company ${companyId} authenticated successfully`);
      const currentSession = this.sessions.get(companyId);
      if (currentSession) {
        currentSession.status = 'AUTHENTICATING';
        currentSession.qrCode = undefined; // QR is no longer valid
      }
    });

    client.on('auth_failure', (msg) => {
      console.error(`[Manager] Auth Failure for company ${companyId}:`, msg);
      const currentSession = this.sessions.get(companyId);
      if (currentSession) {
        currentSession.status = 'FAILED';
        currentSession.errorMessage = msg;
      }
    });

    client.on('ready', () => {
      console.log(`[Manager] Client ready for company ${companyId}`);
      const currentSession = this.sessions.get(companyId);
      if (currentSession) {
        currentSession.status = 'CONNECTED';
        currentSession.qrCode = undefined;
        currentSession.errorMessage = undefined;
      }
    });

    client.on('disconnected', (reason) => {
      console.warn(`[Manager] Client disconnected for company ${companyId}:`, reason);
      const currentSession = this.sessions.get(companyId);
      if (currentSession) {
        currentSession.status = 'DISCONNECTED';
        currentSession.errorMessage = reason;
      }
    });

    // Start initialization in background (non-blocking)
    client.initialize().catch((err: any) => {
      console.error(`[Manager] Failed during initialization of company ${companyId}:`, err);
      const currentSession = this.sessions.get(companyId);
      if (currentSession) {
        currentSession.status = 'FAILED';
        currentSession.errorMessage = err.message || String(err);
      }
    });

    return this.getSession(companyId);
  }

  public async sendMessage(companyId: string, to: string, message: string): Promise<boolean> {
    const session = this.sessions.get(companyId);
    if (!session || session.status !== 'CONNECTED' || !session.queue) {
      console.warn(`[Manager] Cannot send message: session for company ${companyId} is not CONNECTED.`);
      return false;
    }
    return await session.queue.enqueue(to, message);
  }
}
