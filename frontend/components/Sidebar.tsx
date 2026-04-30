"use client";

import { useEffect, useState } from "react";
import { api, Contact } from "@/utils/api";

interface SidebarProps {
  activeContact: Contact | null;
  onSelectContact: (contact: Contact) => void;
}

export default function Sidebar({ activeContact, onSelectContact }: SidebarProps) {
  const [contacts, setContacts] = useState<Contact[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchContacts = async () => {
      try {
        const data = await api.getContacts();
        setContacts(data);
      } catch (error) {
        console.error("Error loading contacts:", error);
      } finally {
        setLoading(false);
      }
    };
    fetchContacts();
  }, []);

  return (
    <aside className="w-80 h-full bg-[#0f0f12] border-r border-[#1e1e24] flex flex-col flex-shrink-0">
      {/* Brand Logo Section */}
      <div className="p-8 border-b border-[#1e1e24] bg-[#0c0c0f]">
        <div className="flex items-center gap-3">
          <img src="/logo.png" alt="Ortho-Cardio Logo" className="h-10 w-auto object-contain" />
          <div className="flex flex-col">
            <span className="text-[14px] font-black tracking-tighter text-[#e1e1e6]">ORTHO-CARDIO</span>
            <span className="text-[9px] font-bold text-[#007aff] uppercase tracking-widest">Búnker v2.0</span>
          </div>
        </div>
      </div>
      
      <div className="flex-1 overflow-y-auto custom-scrollbar">
        <div className="p-4">
          <h3 className="text-[#4a4a52] text-[10px] font-bold tracking-[0.2em] uppercase mb-4 px-2">
            Incoming Leads
          </h3>
          
          {loading ? (
            <div className="p-4 text-[#4a4a52] text-xs">Cargando prospectos...</div>
          ) : (
            <div className="flex flex-col gap-1">
              {contacts.map((contact) => (
                <button
                  key={contact.phone_number}
                  onClick={() => onSelectContact(contact)}
                  className={`text-left p-4 rounded-lg transition-all duration-300 group ${
                    activeContact?.phone_number === contact.phone_number
                      ? "bg-[#16161d] border border-[#0056b3]/30"
                      : "hover:bg-[#16161d] border border-transparent"
                  }`}
                >
                  <div className="flex justify-between items-start mb-1">
                    <span className={`text-sm font-bold tracking-tight ${
                      activeContact?.phone_number === contact.phone_number ? "text-[#007aff]" : "text-[#e1e1e6]"
                    }`}>
                      {contact.name || contact.phone_number}
                    </span>
                    <div className="flex items-center gap-2">
                      {contact.followup_draft && (
                        <span className="h-2 w-2 rounded-full bg-[#007aff] shadow-[0_0_8px_#007aff]/50" title="Requiere Seguimiento"></span>
                      )}
                      {contact.is_ai_active && (
                        <span className="text-[10px] bg-[#0056b3]/20 text-[#007aff] px-2 py-0.5 rounded font-bold">IA</span>
                      )}
                    </div>

                  </div>
                  <div className="text-[#71717a] text-xs font-medium truncate">
                    {contact.hospital || "Hospital por definir"}
                  </div>
                  <div className="text-[#4a4a52] text-[10px] mt-2 flex items-center gap-1">
                    <span className="material-symbols-outlined text-[12px]">schedule</span>
                    {contact.last_interaction ? new Date(contact.last_interaction).toLocaleDateString() : "Sin actividad"}
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>
      </div>

      <div className="p-6 border-t border-[#1e1e24] bg-[#0c0c0f]">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-full bg-[#1c1c24] flex items-center justify-center border border-[#2e2e38]">
            <span className="material-symbols-outlined text-[#007aff] text-sm">shield</span>
          </div>
          <div>
            <div className="text-[#e1e1e6] text-xs font-bold">Carlos Cortés</div>
            <div className="text-[#4a4a52] text-[10px]">Admin Principal</div>
          </div>
        </div>
      </div>
    </aside>
  );
}

