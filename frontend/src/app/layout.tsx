import type { Metadata } from 'next'
import './globals.css'
import { ThemeProvider } from '@/context/ThemeContext'
import Navbar from '@/components/layout/Navbar'

export const metadata: Metadata = {
  title: 'Interlace - Multimodal Fashion Search',
  description: 'Find exactly what you want. Describe it, photograph it, or just feel it.',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: `try{var t=localStorage.getItem('interlace-theme');if(t==='light')document.documentElement.classList.add('light');}catch(e){}` }} />
      </head>
      <body>
        <ThemeProvider>
          <Navbar />
          <div style={{ paddingTop: '68px' }}>
            {children}
          </div>
        </ThemeProvider>
      </body>
    </html>
  )
}
