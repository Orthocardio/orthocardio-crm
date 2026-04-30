"use client";

import { useState } from "react";
import Sidebar from "@/components/Sidebar";
import ChatArea from "@/components/ChatArea";
import { Contact } from "@/utils/api";

export default function Home() {
  const [activeContact, setActiveContact] = useState<Contact | null>(null);

  return (
    <div className="h-screen flex bg-[#0c0c0f] text-[#e1e1e6] font-sans selection:bg-[#007aff]/30">
      <Sidebar activeContact={activeContact} onSelectContact={setActiveContact} />
      <div className="flex-1 flex flex-col min-w-0 h-full">
        <ChatArea activeContact={activeContact} />
      </div>
    </div>
  );
}
