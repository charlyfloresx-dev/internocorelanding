import dotenv from 'dotenv';
import path from 'path';

// Load .env if present (primarily for development)
dotenv.config();

export const config = {
  port: parseInt(process.env.PORT || '3000', 10),
  apiKey: process.env.API_KEY || 'DEV_INTERNAL_KEY_123',
  sessionsPath: process.env.SESSIONS_PATH || path.join(__dirname, '../sessions'),
};
