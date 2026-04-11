import Hero from '@/components/landing/Hero'
import Marquee from '@/components/landing/Marquee'
import Features from '@/components/landing/Features'
import Carousel from '@/components/landing/Carousel'
import SearchTeaser from '@/components/landing/SearchTeaser'
import Footer from '@/components/layout/Footer'

export default function LandingPage() {
  return (
    <main>
      <Hero />
      <Marquee />
      <Features />
      <Carousel />
      <SearchTeaser />
      <Footer />
    </main>
  )
}
