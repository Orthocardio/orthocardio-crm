'use client';

import { useState, useEffect } from 'react';
import { createClient } from '@supabase/supabase-js';

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
);

export default function MarketingStaging() {
  const [campaigns, setCampaigns] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchCampaigns();
    
    const channel = supabase
      .channel('marketing_changes')
      .on('postgres_changes', { event: '*', schema: 'public', table: 'marketing_campaigns' }, () => {
        fetchCampaigns();
      })
      .subscribe();

    return () => { supabase.removeChannel(channel); };
  }, []);

  async function fetchCampaigns() {
    const { data, error } = await supabase
      .from('marketing_campaigns')
      .select('*')
      .order('created_at', { ascending: false });
    
    if (!error) setCampaigns(data);
    setLoading(false);
  }

  async function handleApprove(id: string, imageUrl: string) {
    const { error } = await supabase
      .from('marketing_campaigns')
      .update({ status: 'APPROVED', image_url: imageUrl })
      .eq('id', id);
    
    if (error) alert('Error al aprobar campaña');
  }

  return (
    <div className="min-h-screen bg-[#0a0a0a] text-white p-8 font-sans">
      <header className="mb-12 border-b border-zinc-800 pb-6">
        <h1 className="text-3xl font-bold tracking-tight text-blue-400">Marketing Staging</h1>
        <p className="text-zinc-400 mt-2">Centro de Mando Creativo - Ortho-Cardio Búnker</p>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {campaigns.map((camp) => (
          <div key={camp.id} className="bg-zinc-900 border border-zinc-800 rounded-xl p-6 shadow-2xl transition-all hover:border-blue-500/50">
            <div className="flex justify-between items-start mb-4">
              <span className={`text-xs font-mono px-2 py-1 rounded ${
                camp.status === 'PENDING_ASSETS' ? 'bg-amber-500/10 text-amber-500' : 
                camp.status === 'APPROVED' ? 'bg-emerald-500/10 text-emerald-500' : 'bg-blue-500/10 text-blue-500'
              }`}>
                {camp.status}
              </span>
              <span className="text-xs text-zinc-500">{camp.target_region}</span>
            </div>

            <h2 className="text-xl font-semibold mb-2">{camp.copy_headline}</h2>
            <p className="text-zinc-400 text-sm mb-6 leading-relaxed">{camp.copy_body}</p>

            <div className="bg-black/50 rounded-lg p-4 mb-6 border border-zinc-800">
              <p className="text-[10px] uppercase tracking-widest text-zinc-500 mb-2 font-bold">Visual Prompt (Nano Banana)</p>
              <p className="text-xs font-mono text-zinc-300 italic">{camp.nano_banana_prompt}</p>
              <button 
                onClick={() => navigator.clipboard.writeText(camp.nano_banana_prompt)}
                className="mt-3 text-[10px] text-blue-400 hover:text-blue-300 font-bold transition-colors"
              >
                COPIAR PROMPT
              </button>
            </div>

            {camp.status === 'PENDING_ASSETS' && (
              <div className="border-2 border-dashed border-zinc-800 rounded-lg p-8 text-center hover:bg-zinc-800/50 transition-all cursor-pointer">
                <p className="text-xs text-zinc-500 mb-2">Suelte el render final aquí</p>
                <input 
                  type="file" 
                  className="hidden" 
                  onChange={(e) => {
                    // Lógica de subida a Supabase Storage aquí
                    // Por ahora simulamos la URL para la aprobación
                    const mockUrl = "https://example.com/render.jpg";
                    handleApprove(camp.id, mockUrl);
                  }}
                />
                <button className="text-[10px] bg-blue-600 hover:bg-blue-500 text-white px-4 py-2 rounded-full font-bold transition-all">
                  SUBIR RENDER
                </button>
              </div>
            )}

            {camp.image_url && (
              <div className="rounded-lg overflow-hidden border border-zinc-800 mb-4">
                <img src={camp.image_url} alt="Render" className="w-full h-48 object-cover grayscale hover:grayscale-0 transition-all duration-500" />
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
