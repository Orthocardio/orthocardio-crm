"use client";

import { useEffect, useState, useRef } from "react";
import { createClient } from "@/utils/supabase/client";
import HumanHandoffToggle from "./HumanHandoffToggle";

interface Message {
  id: number;
  contact_id: string;
  sender_type: "client" | "ai" | "human";
  content: string;
  timestamp: string;
}

export default function ChatArea() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputText, setInputText] = useState("");
  const scrollRef = useRef<HTMLDivElement>(null);
  const supabase = createClient();

  useEffect(() => {
    // 1. Cargar mensajes iniciales (opcional, pero recomendado)
    const fetchMessages = async () => {
      const { data, error } = await supabase
        .from("messages")
        .select("*")
        .order("timestamp", { ascending: true });

      if (data) setMessages(data);
    };

    fetchMessages();

    // 2. Suscripción Realtime a la tabla 'messages'
    const channel = supabase
      .channel("realtime_messages")
      .on(
        "postgres_changes",
        { event: "INSERT", schema: "public", table: "messages" },
        (payload) => {
          const newMessage = payload.new as Message;
          setMessages((prev) => [...prev, newMessage]);
        }
      )
      .subscribe();

    return () => {
      supabase.removeChannel(channel);
    };
  }, []);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const handleSendMessage = async () => {
    if (!inputText.trim()) return;

    // En un entorno real, aquí llamaríamos a un endpoint de FastAPI o 
    // insertaríamos directamente en Supabase si los permisos lo permiten.
    // Para esta demo, asumimos que el backend procesa el envío.
    console.log("Enviando mensaje:", inputText);
    setInputText("");
  };

  return (
    <main className="flex-1 flex flex-col bg-background relative overflow-hidden h-full">
      {/* Chat Header */}
      <header className="flex items-center justify-between px-8 py-6 border-b border-surface-container bg-surface flex-shrink-0">
        <div className="flex flex-col">
          <h1 className="font-h2 text-on-surface text-xl font-semibold">
            Prospecto: Dr. Alejandro Méndez
          </h1>
          <span className="font-metadata text-outline mt-1 text-sm">
            Hospital ABC Santa Fe
          </span>
        </div>
        <HumanHandoffToggle />
      </header>

      {/* Chat History Area */}
      <div
        ref={scrollRef}
        className="flex-1 overflow-y-auto px-8 py-10 flex flex-col gap-6"
      >
        {messages.map((msg) => {
          if (msg.sender_type === "client") {
            return (
              <div key={msg.id} className="flex w-full justify-start">
                <div className="max-w-[70%] bg-[#1a1a1a] rounded-lg p-4">
                  <p className="font-body-lg text-on-surface">{msg.content}</p>
                  <div className="font-metadata text-outline mt-2 text-left text-xs">
                    {new Date(msg.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </div>
                </div>
              </div>
            );
          } else if (msg.sender_type === "ai") {
            return (
              <div key={msg.id} className="flex w-full justify-start">
                <div className="max-w-[70%] bg-[#1a1a1a] border border-[#0056b3]/20 rounded-lg p-4 relative">
                  <div className="absolute -top-3 left-4 bg-background px-2">
                    <span className="font-label-caps text-primary-container flex items-center gap-1 text-[10px] font-bold">
                      <span className="material-symbols-outlined text-[14px]">smart_toy</span>
                      AI ASSISTANT
                    </span>
                  </div>
                  <p className="font-body-lg text-on-surface mt-2">{msg.content}</p>
                  <div className="font-metadata text-outline mt-2 text-left text-xs">
                    {new Date(msg.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </div>
                </div>
              </div>
            );
          } else {
            return (
              <div key={msg.id} className="flex w-full justify-end">
                <div className="max-w-[70%] bg-[#0a192f] rounded-lg p-4">
                  <p className="font-body-lg text-on-surface">{msg.content}</p>
                  <div className="font-metadata text-outline mt-2 text-right text-xs">
                    {new Date(msg.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </div>
                </div>
              </div>
            );
          }
        })}
      </div>

      {/* Bottom Input */}
      <div className="p-8 border-t border-surface-container bg-surface flex-shrink-0">
        <div className="flex items-end gap-4 bg-[#121212] p-2 rounded-lg border border-surface-container focus-within:border-primary-container transition-colors">
          <textarea
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            className="flex-1 bg-transparent border-none text-on-surface font-body-lg resize-none focus:ring-0 placeholder:text-outline p-2 min-h-[44px] max-h-[120px]"
            placeholder="Escribir mensaje..."
            rows={1}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                handleSendMessage();
              }
            }}
          ></textarea>
          <button
            onClick={handleSendMessage}
            className="bg-primary-container text-white font-label-caps px-6 py-3 rounded hover:bg-on-primary-fixed-variant transition-colors mb-1 h-[44px] flex items-center justify-center font-bold text-xs uppercase"
          >
            ENVIAR
          </button>
        </div>
      </div>
    </main>
  );
}
