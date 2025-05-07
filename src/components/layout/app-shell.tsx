import type { ReactNode } from 'react';
import Link from 'next/link';
import {
  Sidebar,
  SidebarHeader,
  SidebarContent,
  SidebarMenu,
  SidebarMenuItem,
  SidebarMenuButton,
  SidebarTrigger,
  SidebarInset,
  SidebarFooter,
} from '@/components/ui/sidebar';
import { Button } from '@/components/ui/button';
import { ShieldAlert } from 'lucide-react';
import { APP_NAME, NAV_LINKS } from '@/lib/constants';
import { usePathname } from 'next/navigation'; // Corrected import

interface AppShellProps {
  children: ReactNode;
}

export function AppShell({ children }: AppShellProps) {
  const pathname = usePathname();

  return (
    <div className="flex min-h-screen w-full">
      <Sidebar collapsible="icon" variant="sidebar" side="left">
        <SidebarHeader className="p-4">
          <Link href="/" className="flex items-center gap-2 text-xl font-semibold text-primary-foreground">
            <ShieldAlert className="h-7 w-7 text-accent" />
            <span>{APP_NAME}</span>
          </Link>
        </SidebarHeader>
        <SidebarContent className="p-2">
          <SidebarMenu>
            {NAV_LINKS.map((item) => (
              <SidebarMenuItem key={item.title}>
                <Link href={item.href} legacyBehavior passHref>
                  <SidebarMenuButton
                    asChild
                    isActive={pathname === item.href}
                    tooltip={item.title}
                  >
                    <a>
                      <item.icon />
                      <span>{item.title}</span>
                    </a>
                  </SidebarMenuButton>
                </Link>
              </SidebarMenuItem>
            ))}
          </SidebarMenu>
        </SidebarContent>
        <SidebarFooter className="p-4">
          {/* Add footer content here if needed, e.g. user profile, logout */}
        </SidebarFooter>
      </Sidebar>

      <SidebarInset className="flex flex-col">
        <header className="sticky top-0 z-10 flex h-14 items-center justify-between border-b bg-background/80 px-4 backdrop-blur-sm lg:px-6">
          <div className="flex items-center gap-2">
            <SidebarTrigger className="md:hidden" />
            <h1 className="text-xl font-semibold">
              {NAV_LINKS.find(link => pathname?.startsWith(link.href))?.title || APP_NAME}
            </h1>
          </div>
          {/* Add header actions here if needed e.g. Search, Notifications, User Menu */}
        </header>
        <main className="flex-1 overflow-y-auto p-4 lg:p-6">
          {children}
        </main>
      </SidebarInset>
    </div>
  );
}
