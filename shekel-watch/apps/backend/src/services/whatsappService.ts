import twilio from 'twilio';
import { config } from '../config';

const client = twilio(config.TWILIO_ACCOUNT_SID, config.TWILIO_AUTH_TOKEN);

export async function sendWhatsAppMessage(to: string, body: string): Promise<void> {
  const toFormatted = to.startsWith('whatsapp:') ? to : `whatsapp:${to}`;
  await client.messages.create({
    from: config.TWILIO_WHATSAPP_FROM,
    to:   toFormatted,
    body,
  });
}
