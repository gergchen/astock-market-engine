import type { Metadata, Viewport } from 'next'
import { Sora, IBM_Plex_Mono } from 'next/font/google'
import './globals.css'
import { SystemStatusProvider } from '@/components/SystemStatusProvider'
import { ErrorBoundary } from '@/components/ErrorBoundary'

const sora = Sora({
  subsets: ['latin'],
  variable: '--font-sora',
  display: 'swap',
  weight: ['300', '400', '500', '600', '700'],
})

const ibmPlexMono = IBM_Plex_Mono({
  subsets: ['latin'],
  variable: '--font-mono',
  display: 'swap',
  weight: ['400', '500', '600'],
})

export const viewport: Viewport = {
  themeColor: '#0F0F0F',
  width: 'device-width',
  initialScale: 1,
}

export const metadata: Metadata = {
  title: 'AStock 市场认知引擎',
  description: 'A股市场行为逻辑分析系统',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="zh-CN" className="dark" style={{ colorScheme: 'dark' }}>
      <body
        className={`${sora.variable} ${ibmPlexMono.variable} font-sans bg-[hsl(var(--bg-root))] text-foreground`}
        style={{ fontFamily: "var(--font-sora), 'PingFang SC', 'Microsoft YaHei', system-ui, sans-serif" }}
      >
        <ErrorBoundary>
          <SystemStatusProvider>
            {children}
          </SystemStatusProvider>
        </ErrorBoundary>
      </body>
    </html>
  )
}

