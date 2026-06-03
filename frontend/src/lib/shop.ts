export type ShopTab = "bundle" | "gems" | "credits";

export interface ShopProduct {
  id: string;
  name: string;
  product_type: ShopTab;
  price: number;
  sale_price: number | null;
  gems_amount: number;
  credits_amount: number;
  is_active: boolean;
}

export const STARS_TO_USD = 0.02;

export function starsPrice(product: ShopProduct): number {
  return product.sale_price ?? product.price;
}

export function usdFromStars(stars: number): number {
  return Math.round(stars * STARS_TO_USD * 100) / 100;
}

export function discountedStars(stars: number, discountPercent: number): number {
  if (discountPercent <= 0) return stars;
  return Math.max(1, Math.floor(stars * (100 - discountPercent) / 100));
}

export const MOCK_SHOP_PRODUCTS: ShopProduct[] = [
  {
    id: "mock-bundle-1",
    name: "Стартовый набор",
    product_type: "bundle",
    price: 150,
    sale_price: 99,
    gems_amount: 200,
    credits_amount: 50,
    is_active: true,
  },
  {
    id: "mock-bundle-2",
    name: "Премиум набор",
    product_type: "bundle",
    price: 500,
    sale_price: 399,
    gems_amount: 800,
    credits_amount: 200,
    is_active: true,
  },
  {
    id: "mock-gems-1",
    name: "100 гемов",
    product_type: "gems",
    price: 50,
    sale_price: null,
    gems_amount: 100,
    credits_amount: 0,
    is_active: true,
  },
  {
    id: "mock-gems-2",
    name: "500 гемов",
    product_type: "gems",
    price: 200,
    sale_price: 179,
    gems_amount: 500,
    credits_amount: 0,
    is_active: true,
  },
  {
    id: "mock-gems-3",
    name: "1500 гемов",
    product_type: "gems",
    price: 500,
    sale_price: null,
    gems_amount: 1500,
    credits_amount: 0,
    is_active: true,
  },
  {
    id: "mock-credits-1",
    name: "50 сердец",
    product_type: "credits",
    price: 80,
    sale_price: null,
    gems_amount: 0,
    credits_amount: 50,
    is_active: true,
  },
  {
    id: "mock-credits-2",
    name: "200 сердец",
    product_type: "credits",
    price: 280,
    sale_price: 249,
    gems_amount: 0,
    credits_amount: 200,
    is_active: true,
  },
];

export const SHOP_TAB_LABELS: Record<ShopTab, string> = {
  bundle: "Наборы",
  gems: "Гемы",
  credits: "Сердца",
};
