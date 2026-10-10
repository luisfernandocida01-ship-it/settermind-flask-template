'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useAuth } from './useAuth';

export default function Sidebar() {
  const pathname = usePathname();
  const { logout } = useAuth();

  // No mostrar el sidebar en pantallas públicas de autenticación/registro
  if (pathname === '/login' || pathname === '/register') {
    return null;
  }

  const navSections = [
    {
      phase: 'FASE 1: ESTRATEGIA & RADAR',
      items: [
        { name: 'Estrategia & Avatar', path: '/strategies', icon: '✦' },
        { name: 'Radar de Prospectos', path: '/prospect', icon: '◎' },
      ],
    },
    {
      phase: 'FASE 2: CONVERSIÓN & MENSAJES',
      items: [
        { name: 'Fábrica de Guiones', path: '/content-factory', icon: '💬' },
        { name: 'Imán de Perfil', path: '/profile-magnet', icon: '🧲' },
        { name: 'Pipeline & Mensajes', path: '/conversations', icon: '🚀' },
      ],
    },
    {
      phase: 'FASE 3: GESTIÓN & CUENTA',
      items: [
        { name: 'Historial de Análisis', path: '/history', icon: '📋' },
        { name: 'Recursos & Soporte', path: '/resources', icon: '📚' },
      ],
    },
  ];

  return (
    <aside className="w-64 bg-[#0B111A] border-r border-[#1E2D42] min-h-screen flex flex-col justify-between p-5 text-gray-300 shrink-0">
      <div>
        {/* Encabezado Marca */}
        <div className="mb-6">
          <div className="flex items-center space-x-3 mb-3">
            <div className="w-9 h-9 rounded-lg bg-[#0E2A47] border border-[#D4AF37] text-[#F3C969] font-black flex items-center justify-center text-lg shadow-sm">
              M
            </div>
            <div>
              <h2 className="text-white font-bold text-base leading-tight">SetterMind AI</h2>
              <p className="text-[10px] text-gray-400 uppercase tracking-wider">Suite de Prospección</p>
            </div>
          </div>

          <Link
            href="/"
            className={`flex items-center space-x-2 px-3 py-2 rounded-lg text-xs font-semibold transition ${
              pathname === '/'
                ? 'bg-sky-600 text-white font-bold shadow-md shadow-sky-900/30'
                : 'hover:bg-[#111A28] text-gray-300 hover:text-white'
            }`}
          >
            <span>📊</span>
            <span>Dashboard Principal</span>
          </Link>
        </div>

        {/* Fases de Navegación */}
        <nav className="space-y-6">
          {navSections.map((section) => (
            <div key={section.phase}>
              <p className="text-[10px] font-bold tracking-wider text-gray-500 uppercase px-3 mb-2">
                {section.phase}
              </p>
              <ul className="space-y-1">
                {section.items.map((item) => {
                  const isActive = pathname === item.path;
                  return (
                    <li key={item.path}>
                      <Link
                        href={item.path}
                        className={`flex items-center space-x-3 px-3 py-2 rounded-lg text-xs font-semibold transition ${
                          isActive
                            ? 'bg-[#162235] text-sky-400 border border-sky-500/30 font-bold'
                            : 'hover:bg-[#111A28] hover:text-white text-gray-400'
                        }`}
                      >
                        <span className="text-sm">{item.icon}</span>
                        <span>{item.name}</span>
                      </Link>
                    </li>
                  );
                })}
              </ul>
            </div>
          ))}
        </nav>
      </div>

      {/* Footer del Menú: Licencia y Logout */}
      <div className="pt-4 border-t border-[#1E2D42] space-y-3">
        <div className="bg-[#06090E] border border-[#1E2D42] rounded-lg p-2.5">
          <div className="flex items-center justify-between text-[11px] font-semibold text-emerald-400">
            <span>Licencia Hotmart</span>
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
          </div>
          <p className="text-[10px] text-gray-500 mt-0.5">SaaS-20™ Activo</p>
        </div>

        <button
          onClick={logout}
          className="w-full bg-red-950/40 hover:bg-red-900/60 border border-red-800/40 text-red-300 text-xs font-bold py-2 px-3 rounded-lg transition text-center"
        >
          Cerrar Sesión
        </button>
      </div>
    </aside>
  );
}