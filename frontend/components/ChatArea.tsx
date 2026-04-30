"use client";

import { useEffect, useState, useRef } from "react";
import { createClient } from "@/utils/supabase/client";
import { api, Message, Contact } from "@/utils/api";
import HumanHandoffToggle from "./HumanHandoffToggle";

interface ChatAreaProps {
  activeContact: Contact | null;
}

export default function ChatArea({ activeContact }: ChatAreaProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputText, setInputText] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [localAiActive, setLocalAiActive] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);
  const supabase = createClient();

  useEffect(() => {
    if (activeContact) {
      setLocalAiActive(activeContact.is_ai_active);
      if (activeContact.followup_draft) {
        setInputText(activeContact.followup_draft);
      } else {
        setInputText("");
      }
    }
  }, [activeContact]);


  const handleToggleAI = async () => {
    if (!activeContact) return;
    try {
      const newState = await api.toggleAI(activeContact.phone_number);
      setLocalAiActive(newState);
    } catch (error) {
      console.error("Error toggling AI:", error);
    }
  };

  useEffect(() => {
    if (!activeContact) {
      setMessages([]);
      return;
    }

    const fetchMessages = async () => {
      try {
        const data = await api.getMessages(activeContact.phone_number);
        setMessages(data);
      } catch (error) {
        console.error("Error loading messages:", error);
      }
    };

    fetchMessages();

    const channel = supabase
      .channel(`chat_${activeContact.phone_number}`)
      .on(
        "postgres_changes",
        { 
          event: "INSERT", 
          schema: "public", 
          table: "messages",
          filter: `contact_phone=eq.${activeContact.phone_number}`
        },
        (payload) => {
          const newMessage = payload.new as Message;
          setMessages((prev) => {
            if (prev.some(m => m.id === newMessage.id)) return prev;
            return [...prev, newMessage];
          });
        }
      )
      .subscribe();

    return () => {
      supabase.removeChannel(channel);
    };
  }, [activeContact]);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const handleSendMessage = async () => {
    if (!inputText.trim() || !activeContact || isSending) return;

    setIsSending(true);
    try {
      await api.sendMessage(activeContact.phone_number, inputText);
      setInputText("");
    } catch (error) {
      console.error("Error sending message:", error);
    } finally {
      setIsSending(false);
    }
  };

  if (!activeContact) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center bg-[#0c0c0f] text-[#4a4a52]">
        <span className="material-symbols-outlined text-4xl mb-4">clinical_notes</span>
        <p className="text-sm font-medium tracking-wide">Seleccione un prospecto clínico para iniciar la gestión</p>
      </div>
    );
  }

  return (
    <main className="flex-1 flex flex-col bg-[#0c0c0f] relative overflow-hidden h-full">
      {/* Header */}
      <header className="px-8 py-6 border-b border-[#1e1e24] bg-[#0f0f12] flex justify-between items-center">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <h1 className="text-[#e1e1e6] text-lg font-bold tracking-tight">
              {activeContact.name}
            </h1>
            <span className="text-[10px] bg-[#16161d] text-[#71717a] border border-[#1e1e24] px-2 py-0.5 rounded uppercase font-bold">
              {activeContact.phone_number}
            </span>
          </div>
          <p className="text-[#71717a] text-xs font-medium">{activeContact.hospital || "S/N Hospital"}</p>
        </div>

        <HumanHandoffToggle isAiActive={localAiActive} onToggle={handleToggleAI} />
      </header>

      {/* History */}
      <div
        ref={scrollRef}
        className="flex-1 overflow-y-auto px-8 py-10 flex flex-col gap-8 custom-scrollbar"
      >
        {messages.map((msg) => {
          const isUser = msg.sender_type === "user";
          const isAI = msg.sender_type === "ai";
          
          return (
            <div key={msg.id} className={`flex w-full ${isUser ? "justify-start" : "justify-end"}`}>
              <div className={`max-w-[65%] group`}>
                <div className={`relative p-4 rounded-xl border ${
                  isUser 
                    ? "bg-[#16161d] border-[#1e1e24] text-[#e1e1e6]" 
                    : isAI 
                      ? "bg-[#0c1a2d] border-[#0056b3]/30 text-[#e1e1e6]"
                      : "bg-[#007aff] border-transparent text-white"
                }`}>
                  {isAI && (
                    <div className="absolute -top-2.5 left-4 flex items-center gap-1.5 px-2 py-0.5 bg-[#0c0c0f] border border-[#0056b3]/30 rounded">
                      <span className="material-symbols-outlined text-[12px] text-[#007aff]">smart_toy</span>
                      <span className="text-[9px] font-black text-[#007aff] uppercase tracking-tighter">Clinical Intelligence</span>
                    </div>
                  )}
                  <p className="text-sm leading-relaxed font-medium">{msg.content}</p>
                </div>
                <div className={`mt-2 flex items-center gap-2 ${isUser ? "justify-start" : "justify-end"}`}>
                  <span className="text-[10px] font-bold text-[#4a4a52] uppercase">
                    {isAI ? "Automated" : isUser ? "Client" : "Executive"}
                  </span>
                  <span className="text-[10px] text-[#2a2a32]">|</span>
                  <span className="text-[10px] text-[#4a4a52]">
                    {new Date(msg.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </span>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Input */}
      <div className="p-8 bg-[#0f0f12] border-t border-[#1e1e24]">
        {activeContact.followup_draft && inputText === activeContact.followup_draft && (
          <div className="flex items-center gap-1.5 mb-3 px-1">
            <span className="material-symbols-outlined text-[12px] text-[#007aff]">lightbulb</span>
            <span className="text-[10px] font-black text-[#007aff] uppercase tracking-widest">Sugerencia de Seguimiento IA</span>
          </div>
        )}
        <div className="flex items-end gap-4 bg-[#0c0c0f] p-3 rounded-xl border border-[#1e1e24] focus-within:border-[#007aff]/50 transition-all duration-300">

          <textarea
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            disabled={isSending}
            className="flex-1 bg-transparent border-none text-[#e1e1e6] text-sm font-medium resize-none focus:ring-0 placeholder:text-[#4a4a52] p-2 min-h-[44px] max-h-[120px] custom-scrollbar"
            placeholder="Redactar respuesta técnica..."
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
            disabled={isSending || !inputText.trim()}
            className={`px-6 py-3 rounded-lg flex items-center justify-center transition-all duration-300 ${
              !inputText.trim() || isSending
                ? "bg-[#16161d] text-[#4a4a52] cursor-not-allowed"
                : "bg-[#007aff] text-white hover:bg-[#0056b3] shadow-lg shadow-[#007aff]/10"
            }`}
          >
            <span className="text-[11px] font-black uppercase tracking-widest">
              {isSending ? "Enviando..." : "Transmitir"}
            </span>
          </button>
        </div>
      </div>
    </main>
  );
}
