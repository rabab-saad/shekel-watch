import axios from 'axios';
import { config } from '../config';

// Green API: chatId format is "972XXXXXXXXX@c.us" (country code, no leading +)
function toChatId(phone: string): string {
  // Strip any prefix like "whatsapp:" or "+"
  const digits = phone.replace(/^whatsapp:\+?/, '').replace(/^\+/, '');
  return `${digits}@c.us`;
}

export async function sendWhatsAppMessage(to: string, body: string): Promise<void> {
  const chatId = toChatId(to);
  const url = `https://api.green-api.com/waInstance${config.GREENAPI_INSTANCE_ID}/sendMessage/${config.GREENAPI_TOKEN}`;

  await axios.post(url, { chatId, message: body });
}
