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

export const SHOP_TAB_LABELS: Record<ShopTab, string> = {
  bundle: "Наборы",
  gems: "Гемы",
  credits: "Сердца",
};
