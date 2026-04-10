import { useState, useEffect } from 'react';
import { Search, ShieldCheck, Terminal, Copy, Check, Box } from 'lucide-react';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

interface Package {
  id: string;
  name: string;
  description: string | null;
  version: string;
  developer: string;
}

export default function App() {
  const [packages, setPackages] = useState<Package[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [copiedId, setCopiedId] = useState<string | null>(null);

  useEffect(() => {
    const fetchPackages = async () => {
      try {
        const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8080';
        const response = await fetch(`${API_URL}/api/v1/packages`);
        if (response.ok) {
          const data = await response.json();
          setPackages(data.packages || []);
        } else {
          setPackages([]); // Removed hardcoded dummy fallback
        }
      } catch (err) {
        console.error('Failed to fetch packages:', err);
          setPackages([]); // Removed hardcoded dummy fallback
      } finally {
        setIsLoading(false);
      }
    };

    fetchPackages();
  }, []);

  const handleCopy = (name: string, id: string) => {
    navigator.clipboard.writeText(`vget install ${name}`);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const filteredPackages = packages.filter(p => 
    p.name.toLowerCase().includes(search.toLowerCase()) || 
    (p.description && p.description.toLowerCase().includes(search.toLowerCase()))
  );

  return (
    <div className="min-h-screen flex flex-col font-sans">
      <header className="border-b border-border bg-surface/80 backdrop-blur-sm sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="bg-primary/10 p-2 rounded-md">
              <ShieldCheck className="w-6 h-6 text-primary" />
            </div>
            <span className="font-bold text-xl tracking-tight">vget</span>
            <span className="text-sm text-textMuted ml-2 border-l border-border pl-4 hidden sm:block">
              Secure Package Registry
            </span>
          </div>
          
          <div className="flex items-center gap-4">
            <a href="https://github.com/vget/vget" target="_blank" rel="noreferrer" className="text-textMuted hover:text-text transition-colors text-sm font-medium">
              Documentation
            </a>
          </div>
        </div>
      </header>

      <main className="flex-1 w-full max-w-7xl mx-auto px-6 py-12 flex flex-col gap-8">
        
        <section className="flex flex-col gap-6 items-center text-center max-w-3xl mx-auto mb-8">
          <h1 className="text-4xl sm:text-5xl font-extrabold tracking-tight text-text">
            Discover Verified Packages
          </h1>
          <p className="text-lg text-textMuted">
            Explore cryptographically signed libraries built for security and performance. 
            Every package is verified via Ed25519 signatures upon installation.
          </p>
          
          <div className="relative w-full max-w-xl mt-4 group">
            <div className="absolute inset-y-0 left-4 flex items-center pointer-events-none">
              <Search className="w-5 h-5 text-textMuted group-focus-within:text-primary transition-colors" />
            </div>
            <input
              type="text"
              placeholder="Search packages by name or description..."
              className="w-full bg-surface border border-border rounded-lg py-4 pl-12 pr-4 text-text placeholder:text-textMuted focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary transition-all shadow-sm"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
            <div className="absolute inset-y-0 right-4 flex items-center pointer-events-none">
              <div className="flex items-center gap-1 border border-border bg-background rounded px-2 py-1 text-xs text-textMuted font-mono">
                <kbd>/</kbd>
              </div>
            </div>
          </div>
        </section>

        <section className="w-full">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-2xl font-bold flex items-center gap-2">
              <Box className="w-5 h-5 text-primary" />
              Registry
            </h2>
            <span className="text-sm text-textMuted font-mono">
              {filteredPackages.length} packages found
            </span>
          </div>

          {isLoading ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {[...Array(6)].map((_, i) => (
                <div key={i} className="h-48 bg-surface rounded-xl border border-border animate-pulse" />
              ))}
            </div>
          ) : filteredPackages.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {filteredPackages.map((pkg) => (
                <div 
                  key={pkg.id} 
                  className="group bg-surface rounded-xl border border-border p-6 hover:border-primary/50 hover:shadow-[0_0_20px_rgba(0,229,255,0.05)] transition-all flex flex-col justify-between"
                >
                  <div className="flex flex-col gap-3">
                    <div className="flex items-start justify-between">
                      <h3 className="text-xl font-bold text-text group-hover:text-primary transition-colors truncate">
                        {pkg.name}
                      </h3>
                      <span className="px-2.5 py-1 bg-background border border-border rounded-md text-xs font-mono text-textMuted">
                        v{pkg.version}
                      </span>
                    </div>
                    <p className="text-textMuted text-sm line-clamp-2 min-h-[40px]">
                      {pkg.description || 'No description provided.'}
                    </p>
                    <div className="flex items-center gap-2 text-xs text-textMuted mt-1">
                      <span className="w-2 h-2 rounded-full bg-green-500/80"></span>
                      <span>Verified publisher: <span className="text-text">{pkg.developer}</span></span>
                    </div>
                  </div>

                  <div className="mt-6 pt-4 border-t border-border flex flex-col gap-2">
                    <span className="text-xs text-textMuted uppercase tracking-wider font-semibold">Install Command</span>
                    <button
                      onClick={() => handleCopy(pkg.name, pkg.id)}
                      className={cn(
                        "w-full flex items-center justify-between px-3 py-2.5 rounded-lg border font-mono text-sm transition-all",
                        copiedId === pkg.id 
                          ? "bg-primary/10 border-primary text-primary"
                          : "bg-background border-border text-textMuted hover:text-text hover:border-textMuted"
                      )}
                    >
                      <div className="flex items-center gap-2 truncate">
                        <Terminal className="w-4 h-4 shrink-0" />
                        <span className="truncate">vget install {pkg.name}</span>
                      </div>
                      {copiedId === pkg.id ? (
                        <Check className="w-4 h-4 shrink-0" />
                      ) : (
                        <Copy className="w-4 h-4 shrink-0 opacity-50 group-hover:opacity-100" />
                      )}
                    </button>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="w-full py-16 flex flex-col items-center justify-center text-center bg-surface rounded-xl border border-border border-dashed">
              <Box className="w-12 h-12 text-border mb-4" />
              <h3 className="text-lg font-medium text-text">No packages found</h3>
              <p className="text-textMuted mt-1 max-w-md">
                We couldn't find any packages matching "{search}". Try adjusting your search query.
              </p>
            </div>
          )}
        </section>
      </main>
    </div>
  );
}
