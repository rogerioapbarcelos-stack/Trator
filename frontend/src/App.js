import { useEffect, useState, useCallback, createContext, useContext, useRef } from "react";
import "@/App.css";
import { BrowserRouter, Routes, Route, useNavigate, useLocation, Link, useParams, useSearchParams } from "react-router-dom";
import axios from "axios";
import { Toaster, toast } from "sonner";
import { 
  Search, Menu, X, MapPin, Phone, ChevronRight, Star, Eye, Clock, 
  Plus, LogOut, User, Settings, Tractor, Wrench, Cog, Loader2,
  ChevronLeft, MessageCircle, Share2, Heart, Filter, Grid, List,
  Upload, Image as ImageIcon, Trash2, Edit, Camera
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardFooter, CardHeader } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { 
  DropdownMenu, 
  DropdownMenuContent, 
  DropdownMenuItem, 
  DropdownMenuSeparator,
  DropdownMenuTrigger 
} from "@/components/ui/dropdown-menu";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { SEOHead, getListingSEO, getSearchSEO } from "@/components/SEOHead";

// Fix Leaflet default marker icon
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
});

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// MS Cities coordinates for map
const MS_CITY_COORDS = {
  "Campo Grande": [-20.4697, -54.6201],
  "Dourados": [-22.2231, -54.8118],
  "Três Lagoas": [-20.7849, -51.7013],
  "Corumbá": [-19.0087, -57.6517],
  "Ponta Porã": [-22.5357, -55.7256],
  "Naviraí": [-23.0651, -54.1996],
  "Nova Andradina": [-22.2328, -53.3434],
  "Aquidauana": [-20.4666, -55.7869],
  "Sidrolândia": [-20.9308, -54.9610],
  "Paranaíba": [-19.6744, -51.1909],
  "Maracaju": [-21.6108, -55.1678],
  "Coxim": [-18.5066, -54.7600],
  "Amambai": [-23.1048, -55.2256],
  "Rio Brilhante": [-21.8014, -54.5461],
  "Cassilândia": [-19.1127, -51.7349],
  "Chapadão do Sul": [-18.7881, -52.6265],
  "Costa Rica": [-18.5425, -53.1281],
  "São Gabriel do Oeste": [-19.3919, -54.5508],
  "Jardim": [-21.4799, -56.1380],
  "Bonito": [-21.1267, -56.4836]
};

// Auth Context
const AuthContext = createContext(null);

export const useAuth = () => useContext(AuthContext);

const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  const checkAuth = useCallback(async () => {
    if (window.location.hash?.includes('session_id=')) {
      setLoading(false);
      return;
    }
    
    try {
      const response = await axios.get(`${API}/auth/me`, { withCredentials: true });
      setUser(response.data);
    } catch (error) {
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    checkAuth();
  }, [checkAuth]);

  const login = () => {
    // REMINDER: DO NOT HARDCODE THE URL, OR ADD ANY FALLBACKS OR REDIRECT URLS, THIS BREAKS THE AUTH
    const redirectUrl = window.location.origin + '/dashboard';
    window.location.href = `https://auth.emergentagent.com/?redirect=${encodeURIComponent(redirectUrl)}`;
  };

  const logout = async () => {
    try {
      await axios.post(`${API}/auth/logout`, {}, { withCredentials: true });
      setUser(null);
      toast.success("Você saiu da sua conta");
    } catch (error) {
      console.error("Logout error:", error);
    }
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, logout, checkAuth, setUser }}>
      {children}
    </AuthContext.Provider>
  );
};

// Auth Callback Component
const AuthCallback = () => {
  const navigate = useNavigate();
  const { setUser } = useAuth();
  const hasProcessed = useRef(false);

  useEffect(() => {
    if (hasProcessed.current) return;
    hasProcessed.current = true;

    const processAuth = async () => {
      const hash = window.location.hash;
      const sessionId = hash.split('session_id=')[1]?.split('&')[0];
      
      if (!sessionId) {
        navigate('/');
        return;
      }

      try {
        const response = await axios.post(
          `${API}/auth/session`,
          { session_id: sessionId },
          { withCredentials: true }
        );
        setUser(response.data);
        toast.success(`Bem-vindo, ${response.data.name}!`);
        navigate('/dashboard', { replace: true, state: { user: response.data } });
      } catch (error) {
        console.error("Auth error:", error);
        toast.error("Erro ao fazer login");
        navigate('/');
      }
    };

    processAuth();
  }, [navigate, setUser]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50">
      <div className="text-center">
        <Loader2 className="w-12 h-12 animate-spin text-[#1A4D2E] mx-auto mb-4" />
        <p className="text-slate-600">Autenticando...</p>
      </div>
    </div>
  );
};

// Header Component
const Header = () => {
  const { user, login, logout } = useAuth();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const navigate = useNavigate();

  return (
    <header className="sticky top-0 z-50 bg-white border-b border-slate-200 shadow-sm">
      <div className="max-w-7xl mx-auto px-4 md:px-8">
        <div className="flex items-center justify-between h-16">
          <Link to="/" className="flex items-center gap-2" data-testid="logo-link">
            <div className="w-10 h-10 bg-[#1A4D2E] rounded-lg flex items-center justify-center">
              <Tractor className="w-6 h-6 text-white" />
            </div>
            <span className="font-bold text-xl text-[#1A4D2E] hidden sm:block" style={{ fontFamily: 'Outfit' }}>
              TratorShop
            </span>
          </Link>

          <nav className="hidden md:flex items-center gap-6">
            <Link to="/buscar?category=tratores" className="text-slate-600 hover:text-[#1A4D2E] transition-colors" data-testid="nav-tractors">
              Tratores
            </Link>
            <Link to="/buscar?category=implementos" className="text-slate-600 hover:text-[#1A4D2E] transition-colors" data-testid="nav-implements">
              Implementos
            </Link>
            <Link to="/buscar?category=colheitadeiras" className="text-slate-600 hover:text-[#1A4D2E] transition-colors" data-testid="nav-harvesters">
              Colheitadeiras
            </Link>
            <Link to="/buscar?category=pecas" className="text-slate-600 hover:text-[#1A4D2E] transition-colors" data-testid="nav-parts">
              Peças
            </Link>
          </nav>

          <div className="flex items-center gap-3">
            <Button 
              onClick={() => navigate(user ? '/anunciar' : '/login')}
              className="bg-[#F9C02D] hover:bg-[#f5b00b] text-[#1A4D2E] font-bold hidden sm:flex"
              data-testid="cta-advertise"
            >
              <Plus className="w-4 h-4 mr-2" />
              Anunciar
            </Button>

            {user ? (
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="ghost" className="relative h-10 w-10 rounded-full" data-testid="user-menu-trigger">
                    <Avatar className="h-10 w-10">
                      <AvatarImage src={user.picture} alt={user.name} />
                      <AvatarFallback className="bg-[#1A4D2E] text-white">
                        {user.name?.charAt(0)}
                      </AvatarFallback>
                    </Avatar>
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent className="w-56" align="end">
                  <div className="px-2 py-1.5">
                    <p className="text-sm font-medium">{user.name}</p>
                    <p className="text-xs text-slate-500">{user.email}</p>
                  </div>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem onClick={() => navigate('/dashboard')} data-testid="menu-dashboard">
                    <User className="w-4 h-4 mr-2" />
                    Meus Anúncios
                  </DropdownMenuItem>
                  {user.is_admin && (
                    <DropdownMenuItem onClick={() => navigate('/admin')} data-testid="menu-admin">
                      <Settings className="w-4 h-4 mr-2" />
                      Painel Admin
                    </DropdownMenuItem>
                  )}
                  <DropdownMenuSeparator />
                  <DropdownMenuItem onClick={logout} data-testid="menu-logout">
                    <LogOut className="w-4 h-4 mr-2" />
                    Sair
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            ) : (
              <Button variant="outline" onClick={login} className="border-[#1A4D2E] text-[#1A4D2E]" data-testid="login-button">
                Entrar
              </Button>
            )}

            <Button 
              variant="ghost" 
              size="icon" 
              className="md:hidden"
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              data-testid="mobile-menu-button"
            >
              {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
            </Button>
          </div>
        </div>

        {mobileMenuOpen && (
          <div className="md:hidden py-4 border-t border-slate-100 mobile-menu-enter">
            <nav className="flex flex-col gap-2">
              <Link to="/buscar?category=tratores" className="px-3 py-2 text-slate-600 hover:bg-slate-50 rounded-lg" onClick={() => setMobileMenuOpen(false)}>
                Tratores
              </Link>
              <Link to="/buscar?category=implementos" className="px-3 py-2 text-slate-600 hover:bg-slate-50 rounded-lg" onClick={() => setMobileMenuOpen(false)}>
                Implementos
              </Link>
              <Link to="/buscar?category=colheitadeiras" className="px-3 py-2 text-slate-600 hover:bg-slate-50 rounded-lg" onClick={() => setMobileMenuOpen(false)}>
                Colheitadeiras
              </Link>
              <Link to="/buscar?category=pecas" className="px-3 py-2 text-slate-600 hover:bg-slate-50 rounded-lg" onClick={() => setMobileMenuOpen(false)}>
                Peças
              </Link>
              <div className="pt-2 mt-2 border-t border-slate-100">
                <Button 
                  onClick={() => { navigate(user ? '/anunciar' : '/login'); setMobileMenuOpen(false); }}
                  className="w-full bg-[#F9C02D] hover:bg-[#f5b00b] text-[#1A4D2E] font-bold"
                >
                  <Plus className="w-4 h-4 mr-2" />
                  Anunciar Máquina
                </Button>
              </div>
            </nav>
          </div>
        )}
      </div>
    </header>
  );
};

// Footer Component
const Footer = () => (
  <footer className="bg-[#1A4D2E] text-white py-12">
    <div className="max-w-7xl mx-auto px-4 md:px-8">
      <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
        <div>
          <div className="flex items-center gap-2 mb-4">
            <div className="w-10 h-10 bg-white/10 rounded-lg flex items-center justify-center">
              <Tractor className="w-6 h-6 text-[#F9C02D]" />
            </div>
            <span className="font-bold text-xl" style={{ fontFamily: 'Outfit' }}>TratorShop</span>
          </div>
          <p className="text-white/70 text-sm">
            O maior marketplace de máquinas agrícolas do Mato Grosso do Sul.
          </p>
        </div>
        
        <div>
          <h4 className="font-semibold mb-4" style={{ fontFamily: 'Outfit' }}>Categorias</h4>
          <ul className="space-y-2 text-white/70 text-sm">
            <li><Link to="/buscar?category=tratores" className="hover:text-white">Tratores</Link></li>
            <li><Link to="/buscar?category=implementos" className="hover:text-white">Implementos</Link></li>
            <li><Link to="/buscar?category=colheitadeiras" className="hover:text-white">Colheitadeiras</Link></li>
            <li><Link to="/buscar?category=pecas" className="hover:text-white">Peças</Link></li>
          </ul>
        </div>

        <div>
          <h4 className="font-semibold mb-4" style={{ fontFamily: 'Outfit' }}>Cidades</h4>
          <ul className="space-y-2 text-white/70 text-sm">
            <li><Link to="/buscar?city=Campo Grande" className="hover:text-white">Campo Grande</Link></li>
            <li><Link to="/buscar?city=Dourados" className="hover:text-white">Dourados</Link></li>
            <li><Link to="/buscar?city=Três Lagoas" className="hover:text-white">Três Lagoas</Link></li>
            <li><Link to="/buscar?city=Corumbá" className="hover:text-white">Corumbá</Link></li>
          </ul>
        </div>

        <div>
          <h4 className="font-semibold mb-4" style={{ fontFamily: 'Outfit' }}>Contato</h4>
          <p className="text-white/70 text-sm">
            Dúvidas ou sugestões?<br />
            contato@tratorshop.com.br
          </p>
        </div>
      </div>
      
      <div className="border-t border-white/10 mt-8 pt-8 text-center text-white/50 text-sm">
        © {new Date().getFullYear()} TratorShop. Todos os direitos reservados.
      </div>
    </div>
  </footer>
);

// Listing Card Component
const ListingCard = ({ listing }) => {
  const navigate = useNavigate();
  const imageUrl = listing.images?.[0] 
    ? `${API}/files/${listing.images[0]}`
    : 'https://images.unsplash.com/photo-1758533696874-587c4e62940c?w=400&h=300&fit=crop';

  const formatPrice = (price) => {
    return new Intl.NumberFormat('pt-BR', {
      style: 'currency',
      currency: 'BRL',
      minimumFractionDigits: 0
    }).format(price);
  };

  return (
    <Card 
      className="overflow-hidden cursor-pointer card-hover transition-card group border-slate-200"
      onClick={() => navigate(`/anuncio/${listing.listing_id}`)}
      data-testid={`listing-card-${listing.listing_id}`}
    >
      <div className="relative aspect-[4/3] overflow-hidden bg-slate-100">
        <img 
          src={imageUrl} 
          alt={listing.title}
          className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-105"
          loading="lazy"
          onError={(e) => {
            e.target.src = 'https://images.unsplash.com/photo-1758533696874-587c4e62940c?w=400&h=300&fit=crop';
          }}
        />
        {listing.is_featured && (
          <Badge className="absolute top-3 left-3 bg-[#F9C02D] text-[#1A4D2E] font-semibold">
            <Star className="w-3 h-3 mr-1 fill-current" />
            Destaque
          </Badge>
        )}
      </div>
      <CardContent className="p-4">
        <p className="price-tag mb-2">{formatPrice(listing.price)}</p>
        <h3 className="font-semibold text-slate-900 line-clamp-2 mb-2 group-hover:text-[#1A4D2E] transition-colors">
          {listing.title}
        </h3>
        <div className="flex items-center gap-1 text-slate-500 text-sm">
          <MapPin className="w-4 h-4" />
          <span>{listing.city}, {listing.state}</span>
        </div>
      </CardContent>
      <CardFooter className="px-4 pb-4 pt-0 flex items-center justify-between text-xs text-slate-400">
        <div className="flex items-center gap-1">
          <Eye className="w-3 h-3" />
          <span>{listing.views || 0}</span>
        </div>
        <div className="flex items-center gap-1">
          <Clock className="w-3 h-3" />
          <span>{new Date(listing.created_at).toLocaleDateString('pt-BR')}</span>
        </div>
      </CardFooter>
    </Card>
  );
};

// Category Card Component
const CategoryCard = ({ category, image, count }) => {
  const navigate = useNavigate();
  const icons = {
    tratores: Tractor,
    implementos: Wrench,
    colheitadeiras: Tractor,
    pecas: Cog
  };
  const Icon = icons[category.id] || Tractor;

  return (
    <div 
      className="relative overflow-hidden rounded-xl aspect-[4/3] group cursor-pointer"
      onClick={() => navigate(`/buscar?category=${category.id}`)}
      data-testid={`category-card-${category.id}`}
    >
      <img 
        src={image} 
        alt={category.name}
        className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-110"
        loading="lazy"
      />
      <div className="absolute inset-0 category-overlay" />
      <div className="absolute bottom-0 left-0 right-0 p-4 text-white">
        <div className="flex items-center gap-2 mb-1">
          <Icon className="w-5 h-5" />
          <h3 className="font-semibold text-lg" style={{ fontFamily: 'Outfit' }}>{category.name}</h3>
        </div>
        <p className="text-white/70 text-sm">{count} anúncios</p>
      </div>
    </div>
  );
};

// Search Bar Component
const SearchBar = ({ onSearch, initialQuery = '', initialCity = '' }) => {
  const [query, setQuery] = useState(initialQuery);
  const [city, setCity] = useState(initialCity);
  const [cities, setCities] = useState([]);

  useEffect(() => {
    axios.get(`${API}/cities`).then(res => setCities(res.data)).catch(() => {});
  }, []);

  const handleSubmit = (e) => {
    e.preventDefault();
    onSearch({ query, city });
  };

  return (
    <form onSubmit={handleSubmit} className="w-full" data-testid="search-form">
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
          <Input
            type="text"
            placeholder="Buscar máquinas..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="h-12 pl-12 pr-4 rounded-full border-slate-200 focus:border-[#1A4D2E] focus:ring-[#1A4D2E]/20 shadow-sm"
            data-testid="search-input"
          />
        </div>
        <Select value={city} onValueChange={setCity}>
          <SelectTrigger className="h-12 w-full sm:w-48 rounded-full border-slate-200" data-testid="city-select">
            <MapPin className="w-4 h-4 mr-2 text-slate-400" />
            <SelectValue placeholder="Cidade" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Todas as cidades</SelectItem>
            {cities.map(c => (
              <SelectItem key={c} value={c}>{c}</SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Button 
          type="submit" 
          className="h-12 px-8 bg-[#1A4D2E] hover:bg-[#143d24] rounded-full"
          data-testid="search-button"
        >
          Buscar
        </Button>
      </div>
    </form>
  );
};

// Image Upload Component
const ImageUploader = ({ images, onImagesChange, listingId, maxImages = 10 }) => {
  const [uploading, setUploading] = useState(false);
  const fileInputRef = useRef(null);

  const handleFileSelect = async (e) => {
    const files = Array.from(e.target.files);
    if (files.length === 0) return;

    if (images.length + files.length > maxImages) {
      toast.error(`Máximo de ${maxImages} imagens permitido`);
      return;
    }

    setUploading(true);
    const newImages = [];

    for (const file of files) {
      // Validate file type
      if (!['image/jpeg', 'image/png', 'image/webp'].includes(file.type)) {
        toast.error(`${file.name}: Formato não suportado`);
        continue;
      }

      // Validate file size (max 5MB)
      if (file.size > 5 * 1024 * 1024) {
        toast.error(`${file.name}: Arquivo muito grande (max 5MB)`);
        continue;
      }

      try {
        const formData = new FormData();
        formData.append('file', file);
        
        const res = await axios.post(
          `${API}/listings/${listingId}/images`,
          formData,
          { 
            withCredentials: true,
            headers: { 'Content-Type': 'multipart/form-data' }
          }
        );
        newImages.push(res.data.path);
      } catch (error) {
        console.error("Error uploading image:", error);
        toast.error(`Erro ao enviar ${file.name}`);
      }
    }

    if (newImages.length > 0) {
      onImagesChange([...images, ...newImages]);
      toast.success(`${newImages.length} imagem(ns) enviada(s)`);
    }
    setUploading(false);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const removeImage = (index) => {
    const newImages = images.filter((_, i) => i !== index);
    onImagesChange(newImages);
  };

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
        {images.map((img, idx) => (
          <div key={idx} className="relative aspect-square rounded-lg overflow-hidden bg-slate-100 group">
            <img 
              src={`${API}/files/${img}`} 
              alt={`Imagem ${idx + 1}`}
              className="w-full h-full object-cover"
            />
            <button
              type="button"
              onClick={() => removeImage(idx)}
              className="absolute top-2 right-2 p-1.5 bg-red-500 text-white rounded-full opacity-0 group-hover:opacity-100 transition-opacity"
            >
              <Trash2 className="w-4 h-4" />
            </button>
            {idx === 0 && (
              <span className="absolute bottom-2 left-2 px-2 py-0.5 bg-[#1A4D2E] text-white text-xs rounded">
                Principal
              </span>
            )}
          </div>
        ))}
        
        {images.length < maxImages && (
          <button
            type="button"
            onClick={() => fileInputRef.current?.click()}
            disabled={uploading}
            className="aspect-square rounded-lg border-2 border-dashed border-slate-300 hover:border-[#1A4D2E] flex flex-col items-center justify-center gap-2 text-slate-400 hover:text-[#1A4D2E] transition-colors"
          >
            {uploading ? (
              <Loader2 className="w-8 h-8 animate-spin" />
            ) : (
              <>
                <Camera className="w-8 h-8" />
                <span className="text-xs">Adicionar</span>
              </>
            )}
          </button>
        )}
      </div>

      <input
        ref={fileInputRef}
        type="file"
        accept="image/jpeg,image/png,image/webp"
        multiple
        onChange={handleFileSelect}
        className="hidden"
      />

      <p className="text-xs text-slate-500">
        {images.length}/{maxImages} imagens • JPEG, PNG ou WebP • Máx. 5MB cada
      </p>
    </div>
  );
};

// Location Map Component
const LocationMap = ({ city, className = "" }) => {
  const coords = MS_CITY_COORDS[city] || MS_CITY_COORDS["Campo Grande"];
  
  return (
    <div className={`rounded-lg overflow-hidden ${className}`} style={{ height: '300px' }}>
      <MapContainer 
        center={coords} 
        zoom={12} 
        scrollWheelZoom={false}
        style={{ height: '100%', width: '100%' }}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        <Marker position={coords}>
          <Popup>{city}, MS</Popup>
        </Marker>
      </MapContainer>
    </div>
  );
};

// Home Page
const HomePage = () => {
  const navigate = useNavigate();
  const [featuredListings, setFeaturedListings] = useState([]);
  const [recentListings, setRecentListings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState({ total_listings: 0, total_users: 0 });

  const categoryImages = {
    tratores: 'https://images.unsplash.com/photo-1758533696874-587c4e62940c?w=600&h=400&fit=crop',
    implementos: 'https://images.pexels.com/photos/2933243/pexels-photo-2933243.jpeg?auto=compress&w=600&h=400&fit=crop',
    colheitadeiras: 'https://images.pexels.com/photos/6680160/pexels-photo-6680160.jpeg?auto=compress&w=600&h=400&fit=crop',
    pecas: 'https://images.pexels.com/photos/7568421/pexels-photo-7568421.jpeg?auto=compress&w=600&h=400&fit=crop'
  };

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [featuredRes, recentRes, statsRes] = await Promise.all([
          axios.get(`${API}/listings/featured?limit=4`),
          axios.get(`${API}/listings?limit=8`),
          axios.get(`${API}/stats`)
        ]);
        setFeaturedListings(featuredRes.data);
        setRecentListings(recentRes.data.listings || []);
        setStats(statsRes.data);
      } catch (error) {
        console.error("Error fetching data:", error);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  const handleSearch = ({ query, city }) => {
    const params = new URLSearchParams();
    if (query) params.set('search', query);
    if (city && city !== 'all') params.set('city', city);
    navigate(`/buscar?${params.toString()}`);
  };

  const categories = [
    { id: 'tratores', name: 'Tratores' },
    { id: 'implementos', name: 'Implementos' },
    { id: 'colheitadeiras', name: 'Colheitadeiras' },
    { id: 'pecas', name: 'Peças' }
  ];

  return (
    <div className="min-h-screen bg-white" data-testid="home-page">
      <SEOHead />
      
      {/* Hero Section */}
      <section className="relative bg-[#1A4D2E] overflow-hidden">
        <div className="absolute inset-0">
          <img 
            src="https://images.unsplash.com/photo-1762291398819-335cdb4b14f1?w=1920&h=800&fit=crop"
            alt="Agricultural field"
            className="w-full h-full object-cover opacity-30"
          />
        </div>
        <div className="relative max-w-7xl mx-auto px-4 md:px-8 py-16 md:py-24">
          <div className="max-w-3xl">
            <h1 
              className="text-4xl md:text-5xl lg:text-6xl font-bold text-white mb-6 tracking-tight"
              style={{ fontFamily: 'Outfit' }}
            >
              Compre e venda máquinas agrícolas no MS
            </h1>
            <p className="text-lg md:text-xl text-white/80 mb-8">
              O maior marketplace de tratores, colheitadeiras e implementos do Mato Grosso do Sul
            </p>
            <div className="bg-white rounded-2xl p-4 md:p-6 shadow-xl">
              <SearchBar onSearch={handleSearch} />
            </div>
          </div>
        </div>
      </section>

      {/* Categories Section */}
      <section className="py-12 md:py-16 bg-slate-50">
        <div className="max-w-7xl mx-auto px-4 md:px-8">
          <div className="flex items-center justify-between mb-8">
            <h2 className="text-2xl md:text-3xl font-semibold text-slate-900" style={{ fontFamily: 'Outfit' }}>
              Categorias
            </h2>
            <Link to="/buscar" className="text-[#1A4D2E] font-medium flex items-center gap-1 hover:underline">
              Ver todas <ChevronRight className="w-4 h-4" />
            </Link>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 md:gap-6">
            {categories.map(category => (
              <CategoryCard 
                key={category.id}
                category={category}
                image={categoryImages[category.id]}
                count={stats.total_listings || 0}
              />
            ))}
          </div>
        </div>
      </section>

      {/* Featured Listings */}
      {featuredListings.length > 0 && (
        <section className="py-12 md:py-16">
          <div className="max-w-7xl mx-auto px-4 md:px-8">
            <div className="flex items-center justify-between mb-8">
              <div className="flex items-center gap-3">
                <Star className="w-6 h-6 text-[#F9C02D] fill-current" />
                <h2 className="text-2xl md:text-3xl font-semibold text-slate-900" style={{ fontFamily: 'Outfit' }}>
                  Destaques
                </h2>
              </div>
              <Link to="/buscar?featured=true" className="text-[#1A4D2E] font-medium flex items-center gap-1 hover:underline">
                Ver todos <ChevronRight className="w-4 h-4" />
              </Link>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
              {loading ? (
                [...Array(4)].map((_, i) => (
                  <Card key={i} className="overflow-hidden">
                    <Skeleton className="aspect-[4/3]" />
                    <CardContent className="p-4">
                      <Skeleton className="h-6 w-24 mb-2" />
                      <Skeleton className="h-4 w-full mb-2" />
                      <Skeleton className="h-4 w-32" />
                    </CardContent>
                  </Card>
                ))
              ) : (
                featuredListings.map(listing => (
                  <ListingCard key={listing.listing_id} listing={listing} />
                ))
              )}
            </div>
          </div>
        </section>
      )}

      {/* Recent Listings */}
      <section className="py-12 md:py-16 bg-slate-50">
        <div className="max-w-7xl mx-auto px-4 md:px-8">
          <div className="flex items-center justify-between mb-8">
            <h2 className="text-2xl md:text-3xl font-semibold text-slate-900" style={{ fontFamily: 'Outfit' }}>
              Anúncios Recentes
            </h2>
            <Link to="/buscar" className="text-[#1A4D2E] font-medium flex items-center gap-1 hover:underline">
              Ver todos <ChevronRight className="w-4 h-4" />
            </Link>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {loading ? (
              [...Array(8)].map((_, i) => (
                <Card key={i} className="overflow-hidden">
                  <Skeleton className="aspect-[4/3]" />
                  <CardContent className="p-4">
                    <Skeleton className="h-6 w-24 mb-2" />
                    <Skeleton className="h-4 w-full mb-2" />
                    <Skeleton className="h-4 w-32" />
                  </CardContent>
                </Card>
              ))
            ) : recentListings.length > 0 ? (
              recentListings.map(listing => (
                <ListingCard key={listing.listing_id} listing={listing} />
              ))
            ) : (
              <div className="col-span-full text-center py-12">
                <Tractor className="w-16 h-16 text-slate-300 mx-auto mb-4" />
                <p className="text-slate-500">Nenhum anúncio disponível ainda</p>
                <Button 
                  onClick={() => navigate('/anunciar')}
                  className="mt-4 bg-[#F9C02D] hover:bg-[#f5b00b] text-[#1A4D2E] font-bold"
                >
                  Seja o primeiro a anunciar!
                </Button>
              </div>
            )}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-16 md:py-24 bg-[#1A4D2E]">
        <div className="max-w-4xl mx-auto px-4 md:px-8 text-center">
          <h2 className="text-3xl md:text-4xl font-bold text-white mb-4" style={{ fontFamily: 'Outfit' }}>
            Tem uma máquina para vender?
          </h2>
          <p className="text-white/80 text-lg mb-8">
            Anuncie gratuitamente e alcance milhares de compradores em todo o Mato Grosso do Sul
          </p>
          <Button 
            onClick={() => navigate('/anunciar')}
            className="bg-[#F9C02D] hover:bg-[#f5b00b] text-[#1A4D2E] font-bold text-lg px-8 py-6"
            data-testid="cta-advertise-footer"
          >
            <Plus className="w-5 h-5 mr-2" />
            Anunciar Máquina
          </Button>
        </div>
      </section>
    </div>
  );
};

// Search Page
const SearchPage = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const [listings, setListings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const navigate = useNavigate();

  const category = searchParams.get('category') || '';
  const city = searchParams.get('city') || '';
  const search = searchParams.get('search') || '';
  const featured = searchParams.get('featured') === 'true';

  const seo = getSearchSEO(category, city, search);

  useEffect(() => {
    const fetchListings = async () => {
      setLoading(true);
      try {
        const params = new URLSearchParams();
        if (category) params.set('category', category);
        if (city) params.set('city', city);
        if (search) params.set('search', search);
        if (featured) params.set('featured', 'true');
        params.set('page', page.toString());
        params.set('limit', '20');

        const res = await axios.get(`${API}/listings?${params.toString()}`);
        setListings(res.data.listings || []);
        setTotal(res.data.total || 0);
      } catch (error) {
        console.error("Error fetching listings:", error);
        toast.error("Erro ao buscar anúncios");
      } finally {
        setLoading(false);
      }
    };
    fetchListings();
  }, [category, city, search, featured, page]);

  const handleSearch = ({ query, city: newCity }) => {
    const params = new URLSearchParams(searchParams);
    if (query) params.set('search', query);
    else params.delete('search');
    if (newCity && newCity !== 'all') params.set('city', newCity);
    else params.delete('city');
    setSearchParams(params);
    setPage(1);
  };

  const categoryNames = {
    tratores: 'Tratores',
    implementos: 'Implementos',
    colheitadeiras: 'Colheitadeiras',
    pecas: 'Peças'
  };

  return (
    <div className="min-h-screen bg-slate-50" data-testid="search-page">
      <SEOHead 
        title={seo.title}
        description={seo.description}
        keywords={seo.keywords}
      />
      
      {/* Search Header */}
      <div className="bg-white border-b border-slate-200 py-6">
        <div className="max-w-7xl mx-auto px-4 md:px-8">
          <SearchBar onSearch={handleSearch} initialQuery={search} initialCity={city} />
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 md:px-8 py-8">
        {/* Filters & Results Count */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
          <div>
            <h1 className="text-xl md:text-2xl font-semibold text-slate-900" style={{ fontFamily: 'Outfit' }}>
              {category ? categoryNames[category] : 'Todos os anúncios'}
              {city && ` em ${city}`}
            </h1>
            <p className="text-slate-500">{total} anúncios encontrados</p>
          </div>
          
          {/* Category Filter */}
          <div className="flex gap-2 overflow-x-auto pb-2 sm:pb-0">
            {['tratores', 'implementos', 'colheitadeiras', 'pecas'].map(cat => (
              <Button
                key={cat}
                variant={category === cat ? "default" : "outline"}
                size="sm"
                onClick={() => {
                  const params = new URLSearchParams(searchParams);
                  if (category === cat) params.delete('category');
                  else params.set('category', cat);
                  setSearchParams(params);
                }}
                className={category === cat ? "bg-[#1A4D2E]" : ""}
                data-testid={`filter-${cat}`}
              >
                {categoryNames[cat]}
              </Button>
            ))}
          </div>
        </div>

        {/* Listings Grid */}
        {loading ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {[...Array(8)].map((_, i) => (
              <Card key={i} className="overflow-hidden">
                <Skeleton className="aspect-[4/3]" />
                <CardContent className="p-4">
                  <Skeleton className="h-6 w-24 mb-2" />
                  <Skeleton className="h-4 w-full mb-2" />
                  <Skeleton className="h-4 w-32" />
                </CardContent>
              </Card>
            ))}
          </div>
        ) : listings.length > 0 ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {listings.map(listing => (
              <ListingCard key={listing.listing_id} listing={listing} />
            ))}
          </div>
        ) : (
          <div className="text-center py-16">
            <Tractor className="w-16 h-16 text-slate-300 mx-auto mb-4" />
            <p className="text-slate-500 mb-4">Nenhum anúncio encontrado</p>
            <Button onClick={() => setSearchParams({})} variant="outline">
              Limpar filtros
            </Button>
          </div>
        )}

        {/* Pagination */}
        {total > 20 && (
          <div className="flex justify-center gap-2 mt-8">
            <Button
              variant="outline"
              onClick={() => setPage(p => Math.max(1, p - 1))}
              disabled={page === 1}
            >
              <ChevronLeft className="w-4 h-4" />
            </Button>
            <span className="flex items-center px-4 text-slate-600">
              Página {page} de {Math.ceil(total / 20)}
            </span>
            <Button
              variant="outline"
              onClick={() => setPage(p => p + 1)}
              disabled={page >= Math.ceil(total / 20)}
            >
              <ChevronRight className="w-4 h-4" />
            </Button>
          </div>
        )}
      </div>
    </div>
  );
};

// Listing Detail Page  
const ListingDetailPage = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [listing, setListing] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedImage, setSelectedImage] = useState(0);

  useEffect(() => {
    const fetchListing = async () => {
      try {
        const res = await axios.get(`${API}/listings/${id}`);
        setListing(res.data);
      } catch (error) {
        console.error("Error fetching listing:", error);
        toast.error("Anúncio não encontrado");
        navigate('/');
      } finally {
        setLoading(false);
      }
    };
    fetchListing();
  }, [id, navigate]);

  const handleWhatsAppClick = async () => {
    if (!listing) return;
    
    try {
      await axios.post(`${API}/listings/${listing.listing_id}/whatsapp-click`);
    } catch (error) {
      console.error("Error tracking click:", error);
    }

    const message = encodeURIComponent(`Olá! Vi seu anúncio "${listing.title}" no TratorShop e tenho interesse.`);
    const phone = listing.whatsapp.replace(/\D/g, '');
    window.open(`https://wa.me/55${phone}?text=${message}`, '_blank');
  };

  const formatPrice = (price) => {
    return new Intl.NumberFormat('pt-BR', {
      style: 'currency',
      currency: 'BRL',
      minimumFractionDigits: 0
    }).format(price);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-50 py-8">
        <div className="max-w-6xl mx-auto px-4 md:px-8">
          <Skeleton className="h-[400px] w-full rounded-xl mb-6" />
          <div className="grid md:grid-cols-3 gap-6">
            <div className="md:col-span-2">
              <Skeleton className="h-8 w-48 mb-4" />
              <Skeleton className="h-6 w-full mb-2" />
              <Skeleton className="h-6 w-3/4" />
            </div>
            <Skeleton className="h-48 rounded-xl" />
          </div>
        </div>
      </div>
    );
  }

  if (!listing) return null;

  const seo = getListingSEO(listing);
  const images = listing.images?.length > 0 
    ? listing.images.map(img => `${API}/files/${img}`)
    : ['https://images.unsplash.com/photo-1758533696874-587c4e62940c?w=800&h=600&fit=crop'];

  const conditionLabels = {
    novo: 'Novo',
    seminovo: 'Seminovo',
    usado: 'Usado'
  };

  return (
    <div className="min-h-screen bg-slate-50" data-testid="listing-detail-page">
      <SEOHead 
        title={seo.title}
        description={seo.description}
        keywords={seo.keywords}
        type="product"
        image={images[0]}
      />
      
      <div className="max-w-6xl mx-auto px-4 md:px-8 py-8">
        {/* Breadcrumb */}
        <nav className="flex items-center gap-2 text-sm text-slate-500 mb-6">
          <Link to="/" className="hover:text-[#1A4D2E]">Início</Link>
          <ChevronRight className="w-4 h-4" />
          <Link to={`/buscar?category=${listing.category}`} className="hover:text-[#1A4D2E] capitalize">
            {listing.category}
          </Link>
          <ChevronRight className="w-4 h-4" />
          <span className="text-slate-900 truncate">{listing.title}</span>
        </nav>

        <div className="grid lg:grid-cols-3 gap-8">
          {/* Main Content */}
          <div className="lg:col-span-2 space-y-6">
            {/* Image Gallery */}
            <div className="bg-white rounded-xl overflow-hidden shadow-sm">
              <div className="aspect-[16/10] relative bg-slate-100">
                <img 
                  src={images[selectedImage]}
                  alt={listing.title}
                  className="w-full h-full object-contain"
                  onError={(e) => {
                    e.target.src = 'https://images.unsplash.com/photo-1758533696874-587c4e62940c?w=800&h=600&fit=crop';
                  }}
                />
                {listing.is_featured && (
                  <Badge className="absolute top-4 left-4 bg-[#F9C02D] text-[#1A4D2E] font-semibold">
                    <Star className="w-3 h-3 mr-1 fill-current" />
                    Destaque
                  </Badge>
                )}
              </div>
              {images.length > 1 && (
                <div className="flex gap-2 p-4 overflow-x-auto">
                  {images.map((img, idx) => (
                    <button
                      key={idx}
                      onClick={() => setSelectedImage(idx)}
                      className={`w-20 h-20 rounded-lg overflow-hidden flex-shrink-0 border-2 transition-all ${
                        selectedImage === idx ? 'border-[#1A4D2E]' : 'border-transparent'
                      }`}
                    >
                      <img src={img} alt="" className="w-full h-full object-cover" />
                    </button>
                  ))}
                </div>
              )}
            </div>

            {/* Details */}
            <Card>
              <CardHeader>
                <h1 className="text-2xl md:text-3xl font-bold text-slate-900" style={{ fontFamily: 'Outfit' }}>
                  {listing.title}
                </h1>
                <div className="flex items-center gap-4 text-slate-500">
                  <span className="flex items-center gap-1">
                    <MapPin className="w-4 h-4" />
                    {listing.city}, {listing.state}
                  </span>
                  <span className="flex items-center gap-1">
                    <Eye className="w-4 h-4" />
                    {listing.views} visualizações
                  </span>
                </div>
              </CardHeader>
              <CardContent className="space-y-6">
                {/* Specs */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  {listing.brand && (
                    <div className="bg-slate-50 rounded-lg p-3">
                      <p className="text-xs text-slate-500 uppercase tracking-wider">Marca</p>
                      <p className="font-semibold">{listing.brand}</p>
                    </div>
                  )}
                  {listing.model && (
                    <div className="bg-slate-50 rounded-lg p-3">
                      <p className="text-xs text-slate-500 uppercase tracking-wider">Modelo</p>
                      <p className="font-semibold">{listing.model}</p>
                    </div>
                  )}
                  {listing.year && (
                    <div className="bg-slate-50 rounded-lg p-3">
                      <p className="text-xs text-slate-500 uppercase tracking-wider">Ano</p>
                      <p className="font-semibold">{listing.year}</p>
                    </div>
                  )}
                  {listing.hours_used && (
                    <div className="bg-slate-50 rounded-lg p-3">
                      <p className="text-xs text-slate-500 uppercase tracking-wider">Horas</p>
                      <p className="font-semibold mono">{listing.hours_used.toLocaleString('pt-BR')}h</p>
                    </div>
                  )}
                  <div className="bg-slate-50 rounded-lg p-3">
                    <p className="text-xs text-slate-500 uppercase tracking-wider">Condição</p>
                    <p className="font-semibold">{conditionLabels[listing.condition] || listing.condition}</p>
                  </div>
                </div>

                {/* Description */}
                <div>
                  <h3 className="font-semibold text-lg mb-2" style={{ fontFamily: 'Outfit' }}>Descrição</h3>
                  <p className="text-slate-600 whitespace-pre-wrap">{listing.description}</p>
                </div>
              </CardContent>
            </Card>

            {/* Map */}
            <Card>
              <CardHeader>
                <h3 className="font-semibold text-lg" style={{ fontFamily: 'Outfit' }}>Localização</h3>
              </CardHeader>
              <CardContent>
                <LocationMap city={listing.city} />
              </CardContent>
            </Card>
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Price Card */}
            <Card className="sticky top-24">
              <CardContent className="p-6">
                <p className="text-4xl font-bold text-[#1A4D2E] mb-6" style={{ fontFamily: 'Outfit' }}>
                  {formatPrice(listing.price)}
                </p>
                
                <Button 
                  onClick={handleWhatsAppClick}
                  className="w-full bg-[#25D366] hover:bg-[#1ebd59] text-white font-bold py-6 text-lg whatsapp-pulse"
                  data-testid="whatsapp-button"
                >
                  <MessageCircle className="w-5 h-5 mr-2" />
                  Chamar no WhatsApp
                </Button>

                {/* Seller Info */}
                {listing.seller && (
                  <div className="mt-6 pt-6 border-t border-slate-100">
                    <div className="flex items-center gap-3">
                      <Avatar>
                        <AvatarImage src={listing.seller.picture} />
                        <AvatarFallback className="bg-[#1A4D2E] text-white">
                          {listing.seller.name?.charAt(0)}
                        </AvatarFallback>
                      </Avatar>
                      <div>
                        <p className="font-semibold">{listing.seller.name}</p>
                        <p className="text-sm text-slate-500">Vendedor</p>
                      </div>
                    </div>
                  </div>
                )}

                {/* Published Date */}
                <div className="mt-4 text-sm text-slate-500 flex items-center gap-2">
                  <Clock className="w-4 h-4" />
                  Publicado em {new Date(listing.created_at).toLocaleDateString('pt-BR')}
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
};

// Create/Edit Listing Page
const ListingFormPage = () => {
  const { user, loading: authLoading } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const { id: editId } = useParams();
  const isEditing = !!editId;
  
  const [loading, setLoading] = useState(false);
  const [fetchingListing, setFetchingListing] = useState(isEditing);
  const [cities, setCities] = useState([]);
  const [images, setImages] = useState([]);
  const [listingId, setListingId] = useState(editId || null);
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    category: '',
    price: '',
    brand: '',
    model: '',
    year: '',
    hours_used: '',
    condition: '',
    city: '',
    whatsapp: ''
  });

  const currentUser = user || location.state?.user;

  useEffect(() => {
    if (authLoading) return;
    if (!currentUser) {
      navigate('/login');
      return;
    }
    axios.get(`${API}/cities`).then(res => setCities(res.data)).catch(() => {});
    
    // Fetch existing listing for editing
    if (isEditing) {
      axios.get(`${API}/listings/${editId}`, { withCredentials: true })
        .then(res => {
          const listing = res.data;
          setFormData({
            title: listing.title || '',
            description: listing.description || '',
            category: listing.category || '',
            price: listing.price?.toString() || '',
            brand: listing.brand || '',
            model: listing.model || '',
            year: listing.year?.toString() || '',
            hours_used: listing.hours_used?.toString() || '',
            condition: listing.condition || '',
            city: listing.city || '',
            whatsapp: listing.whatsapp || ''
          });
          setImages(listing.images || []);
          setListingId(listing.listing_id);
        })
        .catch(err => {
          toast.error("Erro ao carregar anúncio");
          navigate('/dashboard');
        })
        .finally(() => setFetchingListing(false));
    }
  }, [currentUser, authLoading, navigate, isEditing, editId]);

  const handleChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!formData.title || !formData.description || !formData.category || !formData.price || !formData.city || !formData.whatsapp || !formData.condition) {
      toast.error("Preencha todos os campos obrigatórios");
      return;
    }

    setLoading(true);
    try {
      const payload = {
        ...formData,
        price: parseFloat(formData.price),
        year: formData.year ? parseInt(formData.year) : null,
        hours_used: formData.hours_used ? parseInt(formData.hours_used) : null
      };

      if (isEditing) {
        await axios.put(`${API}/listings/${editId}`, payload, { withCredentials: true });
        toast.success("Anúncio atualizado! Aguardando re-aprovação.");
      } else {
        const res = await axios.post(`${API}/listings`, payload, { withCredentials: true });
        setListingId(res.data.listing_id);
        toast.success("Anúncio criado! Agora adicione fotos.");
      }
      
      if (!isEditing && !listingId) {
        // Stay on page to add images after creation
      } else {
        navigate('/dashboard');
      }
    } catch (error) {
      console.error("Error saving listing:", error);
      toast.error("Erro ao salvar anúncio");
    } finally {
      setLoading(false);
    }
  };

  if (!currentUser && !authLoading) return null;
  
  if (fetchingListing) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-[#1A4D2E]" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50 py-8" data-testid="listing-form-page">
      <SEOHead title={isEditing ? "Editar Anúncio" : "Anunciar Máquina"} />
      
      <div className="max-w-3xl mx-auto px-4 md:px-8">
        <h1 className="text-2xl md:text-3xl font-bold text-slate-900 mb-8" style={{ fontFamily: 'Outfit' }}>
          {isEditing ? "Editar Anúncio" : "Anunciar Máquina"}
        </h1>

        <form onSubmit={handleSubmit}>
          {/* Images Section - Show if listing exists */}
          {listingId && (
            <Card className="mb-6">
              <CardHeader>
                <h2 className="text-lg font-semibold" style={{ fontFamily: 'Outfit' }}>Fotos</h2>
                <p className="text-sm text-slate-500">Adicione fotos para atrair mais compradores</p>
              </CardHeader>
              <CardContent>
                <ImageUploader 
                  images={images}
                  onImagesChange={setImages}
                  listingId={listingId}
                />
              </CardContent>
            </Card>
          )}

          <Card className="mb-6">
            <CardHeader>
              <h2 className="text-lg font-semibold" style={{ fontFamily: 'Outfit' }}>Informações Básicas</h2>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <Label htmlFor="title">Título do anúncio *</Label>
                <Input
                  id="title"
                  value={formData.title}
                  onChange={(e) => handleChange('title', e.target.value)}
                  placeholder="Ex: Trator John Deere 5085E 2020"
                  className="mt-1"
                  data-testid="input-title"
                />
              </div>

              <div>
                <Label htmlFor="description">Descrição *</Label>
                <Textarea
                  id="description"
                  value={formData.description}
                  onChange={(e) => handleChange('description', e.target.value)}
                  placeholder="Descreva sua máquina em detalhes..."
                  rows={4}
                  className="mt-1"
                  data-testid="input-description"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>Categoria *</Label>
                  <Select value={formData.category} onValueChange={(v) => handleChange('category', v)}>
                    <SelectTrigger className="mt-1" data-testid="select-category">
                      <SelectValue placeholder="Selecione" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="tratores">Tratores</SelectItem>
                      <SelectItem value="implementos">Implementos</SelectItem>
                      <SelectItem value="colheitadeiras">Colheitadeiras</SelectItem>
                      <SelectItem value="pecas">Peças</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div>
                  <Label htmlFor="price">Preço (R$) *</Label>
                  <Input
                    id="price"
                    type="number"
                    value={formData.price}
                    onChange={(e) => handleChange('price', e.target.value)}
                    placeholder="150000"
                    className="mt-1"
                    data-testid="input-price"
                  />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="mb-6">
            <CardHeader>
              <h2 className="text-lg font-semibold" style={{ fontFamily: 'Outfit' }}>Especificações</h2>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="brand">Marca</Label>
                  <Input
                    id="brand"
                    value={formData.brand}
                    onChange={(e) => handleChange('brand', e.target.value)}
                    placeholder="John Deere"
                    className="mt-1"
                    data-testid="input-brand"
                  />
                </div>
                <div>
                  <Label htmlFor="model">Modelo</Label>
                  <Input
                    id="model"
                    value={formData.model}
                    onChange={(e) => handleChange('model', e.target.value)}
                    placeholder="5085E"
                    className="mt-1"
                    data-testid="input-model"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="year">Ano</Label>
                  <Input
                    id="year"
                    type="number"
                    value={formData.year}
                    onChange={(e) => handleChange('year', e.target.value)}
                    placeholder="2020"
                    className="mt-1"
                    data-testid="input-year"
                  />
                </div>
                <div>
                  <Label htmlFor="hours">Horas de uso</Label>
                  <Input
                    id="hours"
                    type="number"
                    value={formData.hours_used}
                    onChange={(e) => handleChange('hours_used', e.target.value)}
                    placeholder="2500"
                    className="mt-1"
                    data-testid="input-hours"
                  />
                </div>
              </div>

              <div>
                <Label>Condição *</Label>
                <Select value={formData.condition} onValueChange={(v) => handleChange('condition', v)}>
                  <SelectTrigger className="mt-1" data-testid="select-condition">
                    <SelectValue placeholder="Selecione" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="novo">Novo</SelectItem>
                    <SelectItem value="seminovo">Seminovo</SelectItem>
                    <SelectItem value="usado">Usado</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </CardContent>
          </Card>

          <Card className="mb-6">
            <CardHeader>
              <h2 className="text-lg font-semibold" style={{ fontFamily: 'Outfit' }}>Localização e Contato</h2>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <Label>Cidade *</Label>
                <Select value={formData.city} onValueChange={(v) => handleChange('city', v)}>
                  <SelectTrigger className="mt-1" data-testid="select-city">
                    <SelectValue placeholder="Selecione sua cidade" />
                  </SelectTrigger>
                  <SelectContent>
                    {cities.map(city => (
                      <SelectItem key={city} value={city}>{city}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div>
                <Label htmlFor="whatsapp">WhatsApp *</Label>
                <Input
                  id="whatsapp"
                  value={formData.whatsapp}
                  onChange={(e) => handleChange('whatsapp', e.target.value)}
                  placeholder="(67) 99999-9999"
                  className="mt-1"
                  data-testid="input-whatsapp"
                />
                <p className="text-xs text-slate-500 mt-1">
                  Compradores entrarão em contato diretamente pelo WhatsApp
                </p>
              </div>
            </CardContent>
          </Card>

          <div className="flex gap-4">
            <Button type="button" variant="outline" onClick={() => navigate('/dashboard')} className="flex-1">
              Cancelar
            </Button>
            <Button 
              type="submit" 
              className="flex-1 bg-[#1A4D2E] hover:bg-[#143d24]"
              disabled={loading}
              data-testid="submit-listing"
            >
              {loading ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : null}
              {isEditing ? "Salvar Alterações" : (listingId ? "Atualizar e Finalizar" : "Criar Anúncio")}
            </Button>
          </div>

          <p className="text-center text-sm text-slate-500 mt-4">
            {isEditing ? "Alterações serão analisadas antes de serem publicadas" : "Seu anúncio será analisado antes de ser publicado"}
          </p>
        </form>
      </div>
    </div>
  );
};

// Dashboard Page
const DashboardPage = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [listings, setListings] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!user && !location.state?.user) {
      navigate('/login');
      return;
    }
    fetchListings();
  }, [user, navigate, location.state]);

  const fetchListings = async () => {
    try {
      const res = await axios.get(`${API}/my-listings`, { withCredentials: true });
      setListings(res.data);
    } catch (error) {
      console.error("Error fetching listings:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (listingId) => {
    if (!window.confirm('Tem certeza que deseja excluir este anúncio?')) return;
    
    try {
      await axios.delete(`${API}/listings/${listingId}`, { withCredentials: true });
      toast.success("Anúncio excluído");
      fetchListings();
    } catch (error) {
      toast.error("Erro ao excluir anúncio");
    }
  };

  const formatPrice = (price) => {
    return new Intl.NumberFormat('pt-BR', {
      style: 'currency',
      currency: 'BRL',
      minimumFractionDigits: 0
    }).format(price);
  };

  const statusBadges = {
    pending: { label: 'Aguardando', className: 'bg-amber-100 text-amber-800' },
    approved: { label: 'Ativo', className: 'bg-green-100 text-green-800' },
    rejected: { label: 'Rejeitado', className: 'bg-red-100 text-red-800' },
    expired: { label: 'Expirado', className: 'bg-slate-100 text-slate-600' }
  };

  return (
    <div className="min-h-screen bg-slate-50 py-8" data-testid="dashboard-page">
      <SEOHead title="Meus Anúncios" />
      
      <div className="max-w-6xl mx-auto px-4 md:px-8">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl md:text-3xl font-bold text-slate-900" style={{ fontFamily: 'Outfit' }}>
              Meus Anúncios
            </h1>
            <p className="text-slate-500">Gerencie suas máquinas anunciadas</p>
          </div>
          <Button 
            onClick={() => navigate('/anunciar')}
            className="bg-[#F9C02D] hover:bg-[#f5b00b] text-[#1A4D2E] font-bold"
            data-testid="new-listing-button"
          >
            <Plus className="w-4 h-4 mr-2" />
            Novo Anúncio
          </Button>
        </div>

        {loading ? (
          <div className="space-y-4">
            {[...Array(3)].map((_, i) => (
              <Skeleton key={i} className="h-32 rounded-xl" />
            ))}
          </div>
        ) : listings.length > 0 ? (
          <div className="space-y-4">
            {listings.map(listing => (
              <Card key={listing.listing_id} className="overflow-hidden" data-testid={`my-listing-${listing.listing_id}`}>
                <div className="flex flex-col sm:flex-row">
                  <div className="sm:w-48 h-32 bg-slate-100 relative">
                    {listing.images?.[0] ? (
                      <img 
                        src={`${API}/files/${listing.images[0]}`}
                        alt={listing.title}
                        className="w-full h-full object-cover"
                      />
                    ) : (
                      <div className="w-full h-full flex items-center justify-center">
                        <Tractor className="w-12 h-12 text-slate-300" />
                      </div>
                    )}
                  </div>
                  <div className="flex-1 p-4">
                    <div className="flex items-start justify-between">
                      <div>
                        <div className="flex items-center gap-2 mb-1">
                          <Badge className={statusBadges[listing.status]?.className}>
                            {statusBadges[listing.status]?.label}
                          </Badge>
                          {listing.is_featured && (
                            <Badge className="bg-[#F9C02D] text-[#1A4D2E]">
                              <Star className="w-3 h-3 mr-1" />
                              Destaque
                            </Badge>
                          )}
                        </div>
                        <h3 className="font-semibold text-lg">{listing.title}</h3>
                        <p className="text-[#1A4D2E] font-bold">{formatPrice(listing.price)}</p>
                        <p className="text-sm text-slate-500">{listing.city} • {listing.views} views • {listing.whatsapp_clicks} cliques WhatsApp</p>
                      </div>
                      <div className="flex gap-2">
                        <Button 
                          variant="outline" 
                          size="sm"
                          onClick={() => navigate(`/editar/${listing.listing_id}`)}
                          data-testid={`edit-${listing.listing_id}`}
                        >
                          <Edit className="w-4 h-4 mr-1" />
                          Editar
                        </Button>
                        <Button 
                          variant="ghost" 
                          size="sm"
                          onClick={() => handleDelete(listing.listing_id)}
                          className="text-red-600 hover:text-red-700 hover:bg-red-50"
                        >
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      </div>
                    </div>
                  </div>
                </div>
              </Card>
            ))}
          </div>
        ) : (
          <Card className="p-12 text-center">
            <Tractor className="w-16 h-16 text-slate-300 mx-auto mb-4" />
            <p className="text-slate-500 mb-4">Você ainda não tem anúncios</p>
            <Button 
              onClick={() => navigate('/anunciar')}
              className="bg-[#F9C02D] hover:bg-[#f5b00b] text-[#1A4D2E] font-bold"
            >
              Criar primeiro anúncio
            </Button>
          </Card>
        )}
      </div>
    </div>
  );
};

// Admin Page
const AdminPage = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [listings, setListings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('pending');

  useEffect(() => {
    if (!user?.is_admin) {
      navigate('/');
      return;
    }
    fetchListings();
  }, [user, navigate, filter]);

  const fetchListings = async () => {
    setLoading(true);
    try {
      const res = await axios.get(`${API}/admin/listings?status=${filter}`, { withCredentials: true });
      setListings(res.data);
    } catch (error) {
      console.error("Error fetching listings:", error);
      toast.error("Erro ao carregar anúncios");
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = async (listingId) => {
    try {
      await axios.post(`${API}/admin/listings/${listingId}/approve`, {}, { withCredentials: true });
      toast.success("Anúncio aprovado!");
      fetchListings();
    } catch (error) {
      toast.error("Erro ao aprovar");
    }
  };

  const handleReject = async (listingId) => {
    try {
      await axios.post(`${API}/admin/listings/${listingId}/reject`, {}, { withCredentials: true });
      toast.success("Anúncio rejeitado");
      fetchListings();
    } catch (error) {
      toast.error("Erro ao rejeitar");
    }
  };

  const handleFeature = async (listingId, featured) => {
    try {
      await axios.post(`${API}/admin/listings/${listingId}/feature?featured=${featured}`, {}, { withCredentials: true });
      toast.success(featured ? "Anúncio destacado!" : "Destaque removido");
      fetchListings();
    } catch (error) {
      toast.error("Erro ao alterar destaque");
    }
  };

  const formatPrice = (price) => {
    return new Intl.NumberFormat('pt-BR', {
      style: 'currency',
      currency: 'BRL',
      minimumFractionDigits: 0
    }).format(price);
  };

  if (!user?.is_admin) return null;

  return (
    <div className="min-h-screen bg-slate-50 py-8" data-testid="admin-page">
      <SEOHead title="Painel Admin" />
      
      <div className="max-w-6xl mx-auto px-4 md:px-8">
        <h1 className="text-2xl md:text-3xl font-bold text-slate-900 mb-8" style={{ fontFamily: 'Outfit' }}>
          Painel Administrativo
        </h1>

        <Tabs value={filter} onValueChange={setFilter}>
          <TabsList className="mb-6">
            <TabsTrigger value="pending" data-testid="tab-pending">
              Pendentes
            </TabsTrigger>
            <TabsTrigger value="approved" data-testid="tab-approved">
              Aprovados
            </TabsTrigger>
            <TabsTrigger value="rejected" data-testid="tab-rejected">
              Rejeitados
            </TabsTrigger>
          </TabsList>

          <TabsContent value={filter}>
            {loading ? (
              <div className="space-y-4">
                {[...Array(3)].map((_, i) => (
                  <Skeleton key={i} className="h-32 rounded-xl" />
                ))}
              </div>
            ) : listings.length > 0 ? (
              <div className="space-y-4">
                {listings.map(listing => (
                  <Card key={listing.listing_id} className="overflow-hidden">
                    <div className="flex flex-col md:flex-row">
                      <div className="md:w-48 h-32 bg-slate-100">
                        {listing.images?.[0] ? (
                          <img 
                            src={`${API}/files/${listing.images[0]}`}
                            alt={listing.title}
                            className="w-full h-full object-cover"
                          />
                        ) : (
                          <div className="w-full h-full flex items-center justify-center">
                            <Tractor className="w-12 h-12 text-slate-300" />
                          </div>
                        )}
                      </div>
                      <div className="flex-1 p-4">
                        <div className="flex items-start justify-between">
                          <div>
                            <h3 className="font-semibold text-lg">{listing.title}</h3>
                            <p className="text-[#1A4D2E] font-bold">{formatPrice(listing.price)}</p>
                            <p className="text-sm text-slate-500">
                              {listing.city} • Por: {listing.seller?.name || 'N/A'} ({listing.seller?.email})
                            </p>
                            <p className="text-sm text-slate-500">
                              Criado em: {new Date(listing.created_at).toLocaleDateString('pt-BR')}
                            </p>
                          </div>
                          <div className="flex gap-2">
                            {listing.status === 'pending' && (
                              <>
                                <Button 
                                  size="sm"
                                  onClick={() => handleApprove(listing.listing_id)}
                                  className="bg-green-600 hover:bg-green-700"
                                  data-testid={`approve-${listing.listing_id}`}
                                >
                                  Aprovar
                                </Button>
                                <Button 
                                  size="sm"
                                  variant="outline"
                                  onClick={() => handleReject(listing.listing_id)}
                                  className="text-red-600 border-red-200 hover:bg-red-50"
                                  data-testid={`reject-${listing.listing_id}`}
                                >
                                  Rejeitar
                                </Button>
                              </>
                            )}
                            {listing.status === 'approved' && (
                              <Button 
                                size="sm"
                                variant={listing.is_featured ? "outline" : "default"}
                                onClick={() => handleFeature(listing.listing_id, !listing.is_featured)}
                                className={listing.is_featured ? "" : "bg-[#F9C02D] hover:bg-[#f5b00b] text-[#1A4D2E]"}
                                data-testid={`feature-${listing.listing_id}`}
                              >
                                <Star className={`w-4 h-4 mr-1 ${listing.is_featured ? 'fill-current' : ''}`} />
                                {listing.is_featured ? 'Remover Destaque' : 'Destacar'}
                              </Button>
                            )}
                          </div>
                        </div>
                      </div>
                    </div>
                  </Card>
                ))}
              </div>
            ) : (
              <Card className="p-12 text-center">
                <p className="text-slate-500">Nenhum anúncio {filter === 'pending' ? 'pendente' : filter === 'approved' ? 'aprovado' : 'rejeitado'}</p>
              </Card>
            )}
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
};

// Login Page
const LoginPage = () => {
  const { user, login } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    if (user) {
      navigate('/dashboard');
    }
  }, [user, navigate]);

  return (
    <div className="min-h-screen bg-slate-50 flex items-center justify-center py-12 px-4" data-testid="login-page">
      <SEOHead title="Entrar" />
      
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <div className="w-16 h-16 bg-[#1A4D2E] rounded-xl flex items-center justify-center mx-auto mb-4">
            <Tractor className="w-10 h-10 text-white" />
          </div>
          <h1 className="text-2xl font-bold" style={{ fontFamily: 'Outfit' }}>
            Entre no TratorShop
          </h1>
          <p className="text-slate-500">
            Faça login para anunciar suas máquinas
          </p>
        </CardHeader>
        <CardContent>
          <Button 
            onClick={login}
            className="w-full bg-white hover:bg-slate-50 text-slate-900 border border-slate-200 py-6"
            data-testid="google-login-button"
          >
            <svg className="w-5 h-5 mr-3" viewBox="0 0 24 24">
              <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
              <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
              <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
              <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
            </svg>
            Continuar com Google
          </Button>
        </CardContent>
      </Card>
    </div>
  );
};

// App Router
const AppRouter = () => {
  const location = useLocation();
  
  if (location.hash?.includes('session_id=')) {
    return <AuthCallback />;
  }

  return (
    <>
      <Header />
      <main>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/buscar" element={<SearchPage />} />
          <Route path="/anuncio/:id" element={<ListingDetailPage />} />
          <Route path="/anunciar" element={<ListingFormPage />} />
          <Route path="/editar/:id" element={<ListingFormPage />} />
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/admin" element={<AdminPage />} />
          <Route path="/login" element={<LoginPage />} />
        </Routes>
      </main>
      <Footer />
    </>
  );
};

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Toaster position="top-center" richColors />
        <AppRouter />
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
