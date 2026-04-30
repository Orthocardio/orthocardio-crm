// Ortho-Cardio CRM Búnker API Layer
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface Contact {
  phone_number: string;
  name: string;
  role?: string;
  hospital?: string;
  is_ai_active: boolean;
  status: string;
  followup_draft?: string;
  last_interaction: string;
}

export interface Message {
  id: number;
  sender_type: "user" | "ai" | "human";
  content: string;
  timestamp: string;
}

export const api = {
  async getContacts(): Promise<Contact[]> {
    const response = await fetch(`${API_BASE_URL}/api/contacts`);
    if (!response.ok) throw new Error("Failed to fetch contacts");
    return response.json();
  },

  async getMessages(phoneNumber: string): Promise<Message[]> {
    const response = await fetch(`${API_BASE_URL}/api/contacts/${phoneNumber}/messages`);
    if (!response.ok) throw new Error("Failed to fetch messages");
    return response.json();
  },

  async sendMessage(phoneNumber: string, content: string): Promise<void> {
    const response = await fetch(`${API_BASE_URL}/api/contacts/${phoneNumber}/messages`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ content }),
    });
    if (!response.ok) throw new Error("Failed to send message");
  },

  async toggleAI(phoneNumber: string): Promise<boolean> {
    const response = await fetch(`${API_BASE_URL}/api/contacts/${phoneNumber}/toggle_ai`, {
      method: "POST",
    });
    if (!response.ok) throw new Error("Failed to toggle AI");
    const data = await response.json();
    return data.is_ai_active;
  }
};
