-- Crear tabla de campañas de marketing
CREATE TABLE IF NOT EXISTS marketing_campaigns (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    target_region TEXT NOT NULL,
    copy_headline TEXT,
    copy_body TEXT,
    nano_banana_prompt TEXT NOT NULL,
    image_url TEXT,
    status TEXT DEFAULT 'PENDING_ASSETS', -- PENDING_ASSETS, APPROVED, PUBLISHED
    scheduled_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Habilitar Realtime
ALTER PUBLICATION supabase_realtime ADD TABLE marketing_campaigns;

-- Crear Bucket de Storage para assets de marketing
-- (Esto se suele hacer vía consola o API de Supabase, 
-- pero dejamos la referencia para el Storage de 'marketing-assets')
