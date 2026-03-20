import { useEffect } from 'react';

// SEO Helper Component - Updates meta tags dynamically
export const SEOHead = ({ 
  title, 
  description, 
  image, 
  url,
  type = 'website',
  keywords = ''
}) => {
  useEffect(() => {
    // Update document title
    document.title = title ? `${title} | TratorShop` : 'TratorShop - Marketplace de Máquinas Agrícolas MS';
    
    // Helper to update or create meta tag
    const setMeta = (name, content, isProperty = false) => {
      if (!content) return;
      const attr = isProperty ? 'property' : 'name';
      let meta = document.querySelector(`meta[${attr}="${name}"]`);
      if (!meta) {
        meta = document.createElement('meta');
        meta.setAttribute(attr, name);
        document.head.appendChild(meta);
      }
      meta.setAttribute('content', content);
    };

    // Basic meta tags
    setMeta('description', description || 'O maior marketplace de tratores, colheitadeiras e implementos agrícolas do Mato Grosso do Sul. Compre e venda máquinas agrícolas.');
    setMeta('keywords', keywords || 'tratores, colheitadeiras, implementos, máquinas agrícolas, agricultura, Mato Grosso do Sul, MS, comprar trator, vender trator');
    
    // Open Graph tags
    setMeta('og:title', title || 'TratorShop - Marketplace de Máquinas Agrícolas', true);
    setMeta('og:description', description || 'Compre e venda tratores, colheitadeiras e implementos no MS', true);
    setMeta('og:type', type, true);
    setMeta('og:url', url || window.location.href, true);
    setMeta('og:image', image || 'https://images.unsplash.com/photo-1758533696874-587c4e62940c?w=1200&h=630&fit=crop', true);
    setMeta('og:site_name', 'TratorShop', true);
    setMeta('og:locale', 'pt_BR', true);
    
    // Twitter Card tags
    setMeta('twitter:card', 'summary_large_image');
    setMeta('twitter:title', title || 'TratorShop - Marketplace de Máquinas Agrícolas');
    setMeta('twitter:description', description || 'Compre e venda tratores, colheitadeiras e implementos no MS');
    setMeta('twitter:image', image || 'https://images.unsplash.com/photo-1758533696874-587c4e62940c?w=1200&h=630&fit=crop');

    // Cleanup function not needed as we want tags to persist
  }, [title, description, image, url, type, keywords]);

  return null;
};

// Generate listing-specific SEO data
export const getListingSEO = (listing) => {
  if (!listing) return {};
  
  const formatPrice = (price) => {
    return new Intl.NumberFormat('pt-BR', {
      style: 'currency',
      currency: 'BRL',
      minimumFractionDigits: 0
    }).format(price);
  };

  const categoryNames = {
    tratores: 'Trator',
    implementos: 'Implemento',
    colheitadeiras: 'Colheitadeira',
    pecas: 'Peça'
  };

  const title = `${listing.title} - ${formatPrice(listing.price)} em ${listing.city}`;
  const description = `${categoryNames[listing.category] || 'Máquina'} ${listing.brand || ''} ${listing.model || ''} ${listing.year || ''} à venda em ${listing.city}, MS. ${listing.condition === 'novo' ? 'Novo' : listing.condition === 'seminovo' ? 'Seminovo' : 'Usado'}. ${listing.hours_used ? listing.hours_used + ' horas de uso.' : ''} Contato via WhatsApp.`.trim().replace(/\s+/g, ' ');
  
  const keywords = [
    listing.title,
    listing.brand,
    listing.model,
    listing.category,
    listing.city,
    'MS',
    'Mato Grosso do Sul',
    'máquina agrícola',
    'comprar',
    'vender'
  ].filter(Boolean).join(', ');

  return { title, description, keywords };
};

// Generate search page SEO data
export const getSearchSEO = (category, city, search) => {
  const categoryNames = {
    tratores: 'Tratores',
    implementos: 'Implementos',
    colheitadeiras: 'Colheitadeiras',
    pecas: 'Peças'
  };

  let title = 'Máquinas Agrícolas';
  let description = 'Encontre tratores, colheitadeiras, implementos e peças no Mato Grosso do Sul.';

  if (category && categoryNames[category]) {
    title = categoryNames[category];
    description = `${categoryNames[category]} à venda no Mato Grosso do Sul. Encontre as melhores ofertas.`;
  }

  if (city) {
    title += ` em ${city}`;
    description = description.replace('no Mato Grosso do Sul', `em ${city}, MS`);
  }

  if (search) {
    title = `Busca: ${search}`;
    description = `Resultados para "${search}" no TratorShop. Máquinas agrícolas no MS.`;
  }

  return { 
    title, 
    description,
    keywords: `${category || 'máquinas agrícolas'}, ${city || 'Mato Grosso do Sul'}, comprar, vender, agricultura`
  };
};

export default SEOHead;
