import { SUPPORT_SHOP_LIST } from "../constants/support-shop.constant.js";

export const getSiteName = (url: string): string | never => {
  const arr = Object.entries(SUPPORT_SHOP_LIST);
  const supportList = arr.map(([key, { url }]) => [key, url]);

  const siteName = supportList.find(([key, url]) => url.includes(url));

  if (siteName === undefined) throw new Error('지원하지 않는 쇼핑몰입니다.');

  return siteName[0];
}