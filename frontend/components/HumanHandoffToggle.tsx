"use client";

import { useState } from "react";

export default function HumanHandoffToggle() {
  const [isAiActive, setIsAiActive] = useState(true);

  return (
    <div className="flex items-center gap-3">
      <span className="font-label-caps text-outline text-[11px] uppercase tracking-wider">
        MODO IA / INTERVENCIÓN MANUAL
      </span>
      <button
        onClick={() => setIsAiActive(!isAiActive)}
        aria-pressed={isAiActive}
        className={`w-10 h-5 rounded-full relative flex items-center transition-colors duration-300 focus:outline-none ${
          isAiActive ? "bg-primary-container" : "bg-[#242424]"
        }`}
      >
        <span
          className={`w-4 h-4 bg-white rounded-full absolute transition-transform duration-300 ${
            isAiActive ? "translate-x-[22px]" : "translate-x-[2px]"
          }`}
        ></span>
      </button>
    </div>
  );
}
