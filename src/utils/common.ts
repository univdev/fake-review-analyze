import { SUPPORT_SHOP_LIST } from "../constants/support-shop.constant.js";

export const getSiteName = (url: string): string | never => {
  const arr = Object.values(SUPPORT_SHOP_LIST);
  const supportList = arr.map((shop) => shop.url);

  const siteName = supportList.find((shopUrl) => url.includes(shopUrl));

  if (siteName === undefined) throw new Error('지원하지 않는 쇼핑몰입니다.');

  return siteName;
}