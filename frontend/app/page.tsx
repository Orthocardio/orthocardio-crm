import Sidebar from "@/components/Sidebar";
import TopNavigation from "@/components/TopNavigation";
import ChatArea from "@/components/ChatArea";

export default function Home() {
  return (
    <div className="h-screen flex flex-col overflow-hidden bg-background text-on-background font-inter">
      <TopNavigation />
      <div className="flex flex-1 overflow-hidden">
        <Sidebar />
        <ChatArea />
      </div>
    </div>
  );
}
