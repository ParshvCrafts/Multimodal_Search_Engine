import Breadcrumb from '@/components/product/Breadcrumb'
import Gallery from '@/components/product/Gallery'
import ProductInfo from '@/components/product/ProductInfo'
import Accordions from '@/components/product/Accordions'
import CompleteTheLook from '@/components/product/CompleteTheLook'
import Footer from '@/components/layout/Footer'
import { getProduct, getOutfit, getSimilar } from '@/lib/api'
import { MOCK_OUTFIT_ITEMS, MOCK_RELATED } from '@/lib/mock-data'

interface Props {
  params: Promise<{ sku: string }>
}

export default async function ProductDetailPage({ params }: Props) {
  const { sku } = await params

  const [product, outfit, similar] = await Promise.all([
    getProduct(sku),
    getOutfit(sku),
    getSimilar(sku, 5),
  ])

  const outfitItems = outfit.items.length > 0
    ? outfit.items
    : MOCK_OUTFIT_ITEMS.map(p => ({
        sku: p.sku, name: p.name, brand: p.brand,
        price: p.price, category: p.category, image_url: p.image_url,
      }))

  const relatedItems = similar.results.length > 0 ? similar.results : MOCK_RELATED

  return (
    <main>
      <Breadcrumb name={product.name} category={product.category} gender={product.gender} />

      {/* 58/42 split layout */}
      <div style={{ display: 'grid', gridTemplateColumns: '58% 42%' }}>
        {/* Left: Gallery */}
        <Gallery
          imageUrls={product.image_urls ?? []}
          score={product.score}
          productName={product.name}
        />

        {/* Right: Info + Accordions */}
        <div>
          <ProductInfo product={product} />
          <div style={{ padding: '0 56px 40px 40px' }}>
            <Accordions product={product} />
          </div>
        </div>
      </div>

      {/* Full-width sections */}
      <CompleteTheLook items={outfitItems} title="Complete the Look" subtitle="Curated outfit pairings" />
      <CompleteTheLook
        items={relatedItems}
        title="You May Also Like"
        subtitle="View all"
      />
      <Footer />
    </main>
  )
}
