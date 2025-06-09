import { Page } from "playwright";
import { Review } from "../types/review.type.js";

export interface CrawlerHelper {
  getReviewList(maxCount: number): Promise<Review[]>;
}