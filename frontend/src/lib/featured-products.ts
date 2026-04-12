/**
 * Curated featured products for the landing page.
 *
 * These are real ASOS catalog items hand-picked for diversity across
 * category, gender, color, brand, and price range.
 * Image URLs point to the ASOS CDN and will render in the browser.
 *
 * To refresh: search the backend for interesting queries and swap SKUs.
 */

export interface FeaturedProduct {
  sku: string
  name: string
  brand: string
  price: number
  category: string
  gender: string
  color: string
  image_url: string
}

export const FEATURED_PRODUCTS: FeaturedProduct[] = [
  // 1. Elegant black dress — Women
  {
    sku: '109450190',
    name: 'ASYOU halter dress in black',
    brand: 'ASYOU',
    price: 13.00,
    category: 'Dresses',
    gender: 'Women',
    color: 'black',
    image_url: 'https://images.asos-media.com/products/asyou-halter-dress-in-black/201087122-4?$n_1920w$&wid=1926&fit=constrain',
  },
  // 2. Leather jacket — Women
  {
    sku: '117383185',
    name: "Barney's Originals Petite Belina real leather jacket",
    brand: "Barney's Originals",
    price: 105.00,
    category: 'Coats & Jackets',
    gender: 'Women',
    color: 'black',
    image_url: 'https://images.asos-media.com/products/barneys-originals-petite-belina-real-leather-jacket/202522749-4?$n_1920w$&wid=1926&fit=constrain',
  },
  // 3. Floral print midi — Women (multi/colorful)
  {
    sku: '119673677',
    name: 'ASOS DESIGN scoop neck midi dress in floral print',
    brand: 'ASOS DESIGN',
    price: 32.00,
    category: 'Dresses',
    gender: 'Women',
    color: 'multi',
    image_url: 'https://images.asos-media.com/products/asos-design-scoop-neck-midi-dress-in-floral-print/203121509-4?$n_1920w$&wid=1926&fit=constrain',
  },
  // 4. Tailored waistcoat — Men (beige/neutral)
  {
    sku: '124458381',
    name: 'NA-KD co-ord tailored waistcoat in beige',
    brand: 'NA-KD',
    price: 42.00,
    category: 'Suits & Tailoring',
    gender: 'Men',
    color: 'beige',
    image_url: 'https://images.asos-media.com/products/na-kd-co-ord-tailored-waistcoat-in-beige/204054807-4?$n_1920w$&wid=1926&fit=constrain',
  },
  // 5. Denim jeans — Unisex (blue)
  {
    sku: '127088568',
    name: 'Simply Be straight leg jeans in mid blue wash',
    brand: 'Simply Be',
    price: 26.00,
    category: 'Jeans',
    gender: 'Unisex',
    color: 'blue wash',
    image_url: 'https://images.asos-media.com/products/simply-be-straight-leg-jeans-in-mid-blue-wash/204397474-5?$n_1920w$&wid=1926&fit=constrain',
  },
  // 6. Distressed cable hoodie — Unisex (streetwear)
  {
    sku: '121146203',
    name: 'Reclaimed Vintage unisex cable hoodie with distressing',
    brand: 'Reclaimed Vintage',
    price: 37.99,
    category: 'Hoodies & Sweatshirts',
    gender: 'Unisex',
    color: 'multi',
    image_url: 'https://images.asos-media.com/products/reclaimed-vintage-unisex-cable-hoodie-with-distressing/203438959-4?$n_1920w$&wid=1926&fit=constrain',
  },
  // 7. Formal coat — Unisex (winter)
  {
    sku: '123276199',
    name: 'Simply Be single breasted formal coat in black',
    brand: 'Simply Be',
    price: 55.00,
    category: 'Coats & Jackets',
    gender: 'Unisex',
    color: 'black',
    image_url: 'https://images.asos-media.com/products/simply-be-single-breasted-formal-coat-in-black/203887625-4?$n_1920w$&wid=1926&fit=constrain',
  },
  // 8. Bridal bodycon mini — Women (white/occasion)
  {
    sku: '123688740',
    name: 'Extro & Vert Bridal bodycon mini dress with bow',
    brand: 'Extro & Vert',
    price: 80.00,
    category: 'Dresses',
    gender: 'Women',
    color: 'white',
    image_url: 'https://images.asos-media.com/products/extro-vert-bridal-bodycon-mini-dress-with-bow/203974815-4?$n_1920w$&wid=1926&fit=constrain',
  },
  // 9. Patchwork knit jumper — Unisex (colorful/knitwear)
  {
    sku: '1936417',
    name: 'Labelrail x Hana Cross oversized jumper in patchwork knit',
    brand: 'Labelrail',
    price: 28.00,
    category: 'Knitwear',
    gender: 'Unisex',
    color: 'multi',
    image_url: 'https://images.asos-media.com/products/labelrail-x-hana-cross-oversized-jumper-in-patchwork-knit/23247818-4?$n_1920w$&wid=1926&fit=constrain',
  },
  // 10. White button shirt — Unisex (classic)
  {
    sku: '123173892',
    name: 'New Look button through shirt in white',
    brand: 'New Look',
    price: 15.99,
    category: 'Tops',
    gender: 'Unisex',
    color: 'white',
    image_url: 'https://images.asos-media.com/products/new-look-button-through-shirt-in-white/203868132-4?$n_1920w$&wid=1926&fit=constrain',
  },
  // 11. Black midi skirt — Women
  {
    sku: '120743780',
    name: 'Extro & Vert Petite midi skirt with split in black',
    brand: 'Extro & Vert',
    price: 36.00,
    category: 'Skirts',
    gender: 'Women',
    color: 'black',
    image_url: 'https://images.asos-media.com/products/extro-vert-petite-midi-skirt-with-split-in-black-co-ord/203453138-4?$n_1920w$&wid=1926&fit=constrain',
  },
  // 12. V-neck blouse — Women (work/smart)
  {
    sku: '117448440',
    name: 'JDY v neck blouse in black',
    brand: 'JDY',
    price: 18.00,
    category: 'Tops',
    gender: 'Women',
    color: 'black',
    image_url: 'https://images.asos-media.com/products/jdy-v-neck-blouse-in-black/202551143-4?$n_1920w$&wid=1926&fit=constrain',
  },
]
