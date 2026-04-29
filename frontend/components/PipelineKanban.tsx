"use client";

import { useState } from "react";

interface Lead {
  id: string;
  name: string;
  hospital: string;
  status: "new" | "quoted" | "closed";
}

const initialLeads: Lead[] = [
  { id: "1", name: "Dr. Alejandro Méndez", hospital: "Hospital ABC Santa Fe", status: "new" },
  { id: "2", name: "Dra. Sofía Valdés", hospital: "Médica Sur", status: "quoted" },
  { id: "3", name: "Paciente Roberto Ruiz", hospital: "Hospital Ángeles", status: "new" },
];

export default function PipelineKanban() {
  const [leads, setLeads] = useState<Lead[]>(initialLeads);

  const columns = [
    { title: "NUEVOS PROSPECTOS", status: "new" },
    { title: "COTIZACIÓN ENVIADA", status: "quoted" },
    { title: "VENTA CERRADA", status: "closed" },
  ];

  return (
    <div className="flex-1 bg-surface-dim p-8 overflow-x-auto">
      <div className="flex gap-6 min-w-[900px] h-full">
        {columns.map((col) => (
          <div key={col.status} className="flex-1 flex flex-col gap-4 bg-surface-container-low p-4 rounded-xl border border-surface-variant/20">
            <h3 className="font-label-caps text-xs text-outline mb-2">{col.title}</h3>
            <div className="flex flex-col gap-3">
              {leads
                .filter((l) => l.status === col.status)
                .map((lead) => (
                  <div key={lead.id} className="bg-surface p-4 rounded-lg shadow-sm border border-surface-variant/10 hover:border-primary/30 transition-all cursor-grab active:cursor-grabbing">
                    <div className="font-body-lg text-on-surface text-sm font-semibold">{lead.name}</div>
                    <div className="font-metadata text-outline text-[11px] mt-1">{lead.hospital}</div>
                  </div>
                ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
