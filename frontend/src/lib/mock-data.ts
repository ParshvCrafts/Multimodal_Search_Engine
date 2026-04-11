import { SearchResultItem, ProductDetail } from './types'

export const MOCK_PRODUCTS: SearchResultItem[] = [
  { sku: 'ms-001', name: 'Rib Knit Frill Hem Funnel Neck Dress in Black', brand: 'Miss Selfridge', price: 32.99, color: 'Black', color_family: 'black', category: 'Dresses', gender: 'Women', image_url: '', score: 0.97, style_tags: ['Knit', 'Mini', 'Funnel Neck'], in_stock: true },
  { sku: 'ur-002', name: 'Square Neck Mini Dress in Floral Print', brand: 'Urban Revivo', price: 44.00, color: 'Floral', color_family: 'multi', category: 'Dresses', gender: 'Women', image_url: '', score: 0.93, style_tags: ['Floral', 'Mini', 'Square Neck'], in_stock: true },
  { sku: 'ad-003', name: 'Satin Midi Dress with Cowl Neck in Chocolate', brand: 'ASOS Design', price: 55.00, color: 'Chocolate', color_family: 'brown', category: 'Dresses', gender: 'Women', image_url: '', score: 0.91, style_tags: ['Satin', 'Midi', 'Cowl Neck', 'Backless'], in_stock: true },
  { sku: 'ad-004', name: 'Cotton Shirred Maxi Smock Dress in Deep Green', brand: 'ASOS Design', price: 44.00, color: 'Deep Green', color_family: 'green', category: 'Dresses', gender: 'Women', image_url: '', score: 0.89, style_tags: ['Cotton', 'Maxi', 'Smock', 'Shirred'], in_stock: true },
  { sku: 'os-005', name: 'Tailored Wide Leg Trousers in Camel', brand: '& Other Stories', price: 69.00, color: 'Camel', color_family: 'beige', category: 'Trousers', gender: 'Women', image_url: '', score: 0.87, style_tags: ['Tailored', 'Wide Leg', 'Formal'], in_stock: true },
  { sku: 'co-006', name: 'Relaxed Linen Blazer in Stone', brand: 'COS', price: 115.00, color: 'Stone', color_family: 'grey', category: 'Jackets', gender: 'Women', image_url: '', score: 0.85, style_tags: ['Linen', 'Relaxed', 'Blazer'], in_stock: true },
  { sku: 'tff-007', name: 'Wrap Midi Dress in Ivory Floral', brand: 'Traffic People', price: 89.00, color: 'Ivory', color_family: 'white', category: 'Dresses', gender: 'Women', image_url: '', score: 0.84, style_tags: ['Wrap', 'Midi', 'Floral', 'Boho'], in_stock: true },
  { sku: 'nt-008', name: 'Oversized Knit Cardigan in Oatmeal', brand: 'New Look', price: 27.99, color: 'Oatmeal', color_family: 'beige', category: 'Knitwear', gender: 'Women', image_url: '', score: 0.82, style_tags: ['Oversized', 'Knit', 'Cardigan'], in_stock: true },
  { sku: 'tt-009', name: 'High Waist Barrel Leg Jeans in Mid Blue', brand: 'Topshop', price: 49.99, color: 'Mid Blue', color_family: 'blue', category: 'Jeans', gender: 'Women', image_url: '', score: 0.81, style_tags: ['High Waist', 'Barrel Leg', 'Denim'], in_stock: true },
  { sku: 'ad-010', name: 'Linen Blend Shirt Dress in White', brand: 'ASOS Design', price: 39.00, color: 'White', color_family: 'white', category: 'Dresses', gender: 'Women', image_url: '', score: 0.80, style_tags: ['Linen', 'Shirt Dress', 'Casual'], in_stock: true },
  { sku: 'hm-011', name: 'Slip Dress with Lace Trim in Dusty Rose', brand: 'H&M', price: 24.99, color: 'Dusty Rose', color_family: 'pink', category: 'Dresses', gender: 'Women', image_url: '', score: 0.79, style_tags: ['Slip', 'Lace', 'Satin', 'Evening'], in_stock: true },
  { sku: 'ri-012', name: 'Plisse Pleated Midi Skirt in Sage', brand: 'River Island', price: 35.00, color: 'Sage', color_family: 'green', category: 'Skirts', gender: 'Women', image_url: '', score: 0.78, style_tags: ['Pleated', 'Midi', 'Plisse'], in_stock: true },
  { sku: 'mng-013', name: 'Structured Shoulder Blazer in Black', brand: 'Mango', price: 79.99, color: 'Black', color_family: 'black', category: 'Jackets', gender: 'Women', image_url: '', score: 0.77, style_tags: ['Structured', 'Power Shoulder', 'Office'], in_stock: true },
  { sku: 'zr-014', name: 'Satin Effect Midi Skirt in Chocolate', brand: 'Zara', price: 45.99, color: 'Chocolate', color_family: 'brown', category: 'Skirts', gender: 'Women', image_url: '', score: 0.76, style_tags: ['Satin', 'Midi', 'Bias Cut'], in_stock: true },
  { sku: 'fr-015', name: 'Broderie Anglaise Mini Dress in White', brand: 'Free People', price: 92.00, color: 'White', color_family: 'white', category: 'Dresses', gender: 'Women', image_url: '', score: 0.75, style_tags: ['Broderie', 'Mini', 'Summer', 'Cotton'], in_stock: true },
  { sku: 'ad-016', name: 'Oversized Denim Jacket in Washed Black', brand: 'ASOS Design', price: 52.00, color: 'Washed Black', color_family: 'black', category: 'Jackets', gender: 'Women', image_url: '', score: 0.74, style_tags: ['Denim', 'Oversized', 'Casual'], in_stock: true },
  { sku: 'nl-017', name: 'Ruched Bodycon Mini Dress in Cream', brand: 'New Look', price: 22.99, color: 'Cream', color_family: 'white', category: 'Dresses', gender: 'Women', image_url: '', score: 0.73, style_tags: ['Ruched', 'Bodycon', 'Mini', 'Going Out'], in_stock: true },
  { sku: 'wh-018', name: 'Balloon Sleeve Blouse in Ecru', brand: 'Warehouse', price: 36.00, color: 'Ecru', color_family: 'white', category: 'Tops', gender: 'Women', image_url: '', score: 0.72, style_tags: ['Balloon Sleeve', 'Romantic', 'Blouse'], in_stock: true },
  { sku: 'pe-019', name: 'Wide Leg Tailored Trousers in Caramel', brand: 'Pretty Lavish', price: 58.00, color: 'Caramel', color_family: 'beige', category: 'Trousers', gender: 'Women', image_url: '', score: 0.71, style_tags: ['Wide Leg', 'Tailored', 'Smart'], in_stock: true },
  { sku: 'tf-020', name: 'Floral Wrap Midi Dress in Terracotta', brand: 'Traffic People', price: 85.00, color: 'Terracotta', color_family: 'orange', category: 'Dresses', gender: 'Women', image_url: '', score: 0.70, style_tags: ['Floral', 'Wrap', 'Midi', 'Boho'], in_stock: true },
]

export const MOCK_PRODUCT_DETAIL: ProductDetail = {
  sku: 'tff-007',
  name: 'Wrap Midi Dress in Ivory Floral',
  brand: 'Traffic People',
  price: 89.00,
  color: 'Ivory',
  color_family: 'white',
  category: 'Dresses',
  gender: 'Women',
  image_url: '',
  image_urls: ['', '', '', ''],
  score: 0.92,
  style_tags: ['Floral', 'Wrap', 'Midi', 'Occasion', 'Boho', 'Summer', 'Elegant'],
  in_stock: true,
  fit: 'Regular',
  material: 'Viscose',
  available_sizes: ['XS', 'S', 'M', 'L'],
  unavailable_sizes: ['XL', 'XXL'],
  available_colors: [
    { name: 'Ivory', hex: '#f5f0e2' },
    { name: 'Dusty Rose', hex: '#c9a0a0' },
  ],
  description: 'A flowing wrap midi dress featuring an all-over floral print, V-neckline, and adjustable tie waist. Cut from lightweight viscose for effortless drape.',
  care_instructions: ['Machine wash cold', 'Do not tumble dry', 'Cool iron if needed', 'Do not bleach'],
  sizing_info: "True to size. Model is 5'9\" wearing size S.",
  delivery_info: 'Free standard delivery on orders over £35. Express delivery available. Free returns within 28 days.',
}

export const MOCK_OUTFIT_ITEMS: SearchResultItem[] = MOCK_PRODUCTS.filter(p =>
  ['os-005', 'co-006', 'ri-012', 'wh-018', 'pe-019'].includes(p.sku)
)

export const MOCK_RELATED: SearchResultItem[] = MOCK_PRODUCTS.filter(p =>
  ['ad-003', 'ur-002', 'hm-011', 'fr-015', 'tf-020'].includes(p.sku)
)
