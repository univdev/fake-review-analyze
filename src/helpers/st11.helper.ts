import { Page } from "playwright";
import { Review } from "../types/review.type.js";
import { CrawlerHelper } from "../interface/crawler-helper.interface.js";

export class St11 implements CrawlerHelper {
  private page: Page;
  private collection: Review[] = [];
  private url: string;

  constructor(page: Page, url: string) {
    this.page = page;
    this.url = url;
  }

  async getReviewList(maxCount: number) {
    await this.page.goto(this.url);
    const reviewFrame = await this.page.frameLocator('iframe.ifrmReview');
    console.log(reviewFrame);
    return this.collection;
  }
}