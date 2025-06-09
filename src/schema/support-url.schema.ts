import { z } from "zod";  
import { SUPPORT_SHOP_LIST } from "../constants/support-shop.constant.js";

export const SUPPORT_URL_SCHEMA = z.string().url().refine((url) => {
  const arr = Object.values(SUPPORT_SHOP_LIST);
  const supportList = arr.map((shop) => shop.url);

  return supportList.some((shopUrl) => url.includes(shopUrl));
}, { message: '지원하지 않는 쇼핑몰입니다.' });