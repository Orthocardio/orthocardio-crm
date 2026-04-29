export default function Sidebar() {
  return (
    <aside className="bg-[#1a1a1a] shadow-2xl shadow-[#0a192f]/40 flex flex-col py-6 px-4 gap-2 w-[280px] flex-shrink-0 h-full border-r border-surface-container overflow-y-auto">
      <div className="mb-6 px-2">
        <h2 className="font-label-caps text-xs font-black uppercase text-gray-500 mb-1">
          LEAD MANAGEMENT
        </h2>
        <p className="font-metadata text-gray-400">Clinical Precision</p>
      </div>
      
      <nav className="flex flex-col gap-1 flex-1">
        <a
          className="flex items-center gap-3 px-3 py-2 bg-[#0056b3]/10 text-[#0056b3] font-semibold rounded transition-all duration-200 font-body-sm"
          href="#"
        >
          <span className="material-symbols-outlined">person_search</span>
          <span>Incoming Leads</span>
        </a>
        <a
          className="flex items-center gap-3 px-3 py-2 text-gray-400 hover:bg-[#0056b3]/5 hover:text-white rounded transition-all duration-200 font-body-sm"
          href="#"
        >
          <span className="material-symbols-outlined">chat_bubble</span>
          <span>Active Cases</span>
        </a>
        <a
          className="flex items-center gap-3 px-3 py-2 text-gray-400 hover:bg-[#0056b3]/5 hover:text-white rounded transition-all duration-200 font-body-sm"
          href="#"
        >
          <span className="material-symbols-outlined">local_hospital</span>
          <span>Hospital Directory</span>
        </a>
        <a
          className="flex items-center gap-3 px-3 py-2 text-gray-400 hover:bg-[#0056b3]/5 hover:text-white rounded transition-all duration-200 font-body-sm"
          href="#"
        >
          <span className="material-symbols-outlined">inventory_2</span>
          <span>Inventory Sync</span>
        </a>
        <a
          className="flex items-center gap-3 px-3 py-2 text-gray-400 hover:bg-[#0056b3]/5 hover:text-white rounded transition-all duration-200 font-body-sm"
          href="#"
        >
          <span className="material-symbols-outlined">monitoring</span>
          <span>Analytics</span>
        </a>
      </nav>

      <div className="mt-8">
        <h3 className="font-label-caps text-on-surface-variant mb-2 px-2">
          RECENT LEADS
        </h3>
        <div className="flex flex-col gap-1">
          <button className="text-left px-3 py-3 rounded hover:bg-surface-container transition-colors group">
            <div className="font-label-caps text-on-surface group-hover:text-primary-container transition-colors mb-1">
              Dr. Alejandro Méndez
            </div>
            <div className="font-metadata text-outline">
              Hospital ABC Santa Fe
            </div>
          </button>
          <button className="text-left px-3 py-3 rounded hover:bg-surface-container transition-colors group">
            <div className="font-label-caps text-on-surface group-hover:text-primary-container transition-colors mb-1">
              Dra. Sofía Valdés
            </div>
            <div className="font-metadata text-outline">
              Médica Sur
            </div>
          </button>
          <button className="text-left px-3 py-3 rounded hover:bg-surface-container transition-colors group">
            <div className="font-label-caps text-on-surface group-hover:text-primary-container transition-colors mb-1">
              Paciente Roberto Ruiz
            </div>
            <div className="font-metadata text-outline">
              Hospital Ángeles
            </div>
          </button>
        </div>
      </div>
    </aside>
  );
}
