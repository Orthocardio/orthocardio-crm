export default function TopNavigation() {
  return (
    <nav className="bg-[#121212] flex justify-between items-center px-8 h-16 w-full flex-shrink-0 border-b border-[#1a1a1a] shadow-[0_10px_30px_-15px_rgba(10,25,47,0.4)] relative z-50">
      <div className="flex items-center gap-4">
        <span className="text-xl font-bold tracking-tight text-white font-h3">
          Ortho-Cardio
        </span>
      </div>
      <div className="flex items-center gap-6">
        <span className="material-symbols-outlined text-gray-400 hover:text-white transition-colors duration-200 ease-in-out cursor-pointer">
          notifications
        </span>
        <span className="material-symbols-outlined text-gray-400 hover:text-white transition-colors duration-200 ease-in-out cursor-pointer">
          settings
        </span>
        <span
          className="material-symbols-outlined text-gray-400 hover:text-white transition-colors duration-200 ease-in-out cursor-pointer"
          title="Executive Profile"
        >
          account_circle
        </span>
      </div>
    </nav>
  );
}
