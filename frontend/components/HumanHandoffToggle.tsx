"use client";

interface HumanHandoffToggleProps {
  isAiActive: boolean;
  onToggle: () => void;
}

export default function HumanHandoffToggle({ isAiActive, onToggle }: HumanHandoffToggleProps) {
  return (
    <div className="flex items-center gap-3">
      <span className="text-[10px] font-black text-[#4a4a52] uppercase tracking-[0.2em]">
        Inteligencia Clínica
      </span>
      <button
        onClick={onToggle}
        className={`w-12 h-6 rounded-full relative flex items-center transition-all duration-500 shadow-inner ${
          isAiActive ? "bg-[#007aff]/20" : "bg-[#16161d]"
        }`}
      >
        <span
          className={`w-4 h-4 rounded-full absolute transition-all duration-500 shadow-lg ${
            isAiActive 
              ? "translate-x-[26px] bg-[#007aff]" 
              : "translate-x-[4px] bg-[#2a2a32]"
          }`}
        ></span>
      </button>
    </div>
  );
}

