import { FrameLocator, Locator, Page } from "playwright";
import { Review } from "../types/review.type.js";
import { CrawlerHelper } from "../interface/crawler-helper.interface.js";
import moment from "moment";
import path from "path";
import { mkdir, writeFileSync } from "fs";
import { writeFile } from "fs/promises";

export class St11 implements CrawlerHelper {
  private page: Page;
  private collection: Review[] = [];
  private maxCount: number;
  private url: string;

  constructor(page: Page, url: string, maxCount: number) {
    this.page = page;
    this.url = url;
    this.maxCount = maxCount;
  }

  async getReviewList() {
    await this.page.goto(this.url);
    const tabButton = await this.page.waitForSelector('#tabMenuDetail2');

    await tabButton.click();

    const reviewFrame = await this.page.frameLocator('#ifrmReview');

    while (true) {
      await this.getReviewContentInElement(reviewFrame);
      let isContinue = false;
      if (this.collection.length < this.maxCount) isContinue = await this.loadMoreReviews(reviewFrame);

      if (!isContinue) break;
    }

    await this.exportCSV(this.collection);

    return this.collection;
  }

  private async getReviewContentInElement(frame: FrameLocator) {
    const reviewContainerElement = await frame.locator('#review-list-page-area .area_list:not([data-crawl])');
    await reviewContainerElement.waitFor({ state: 'visible' });

    console.log('Review Container Element: ', await reviewContainerElement.isVisible());
    
    await reviewContainerElement.evaluate((el) => {
      el.setAttribute('data-crawl', 'true');
    });

    const elements = await frame.locator('#review-list-page-area .area_list:not([data-crawl]) .review_list_element').all();
    console.log('Elements: ', elements.length);
    console.log(`Found ${elements.length} reviews...`);
    for (const element of elements) {
      if (this.collection.length >= this.maxCount) break;

      console.log('--------------------------------');
      console.log(`Start Crawling Review... ${this.collection.length} / ${this.maxCount}`);

      console.log('Element Visible: ', await element.isVisible());

      await element.scrollIntoViewIfNeeded();

      const nameFieldClassName = '.c_product_reviewer .name';
      const scoreFieldClassName = '.c_product_review_cont .c_seller_grade em';
      const contentFieldClassName = '.c_product_review_cont .cont_review_hide';
      const dateFieldClassName = '.date';

      let name: string;
      let score: string;
      let content: string;
      let date: string;
      let formattedDate: Date;

      try {
        name = (await element.locator(nameFieldClassName).textContent())?.trim() as string;
        console.log('Got Name: ', name);
        score = (await element.locator(scoreFieldClassName).textContent())?.trim() as string;
        console.log('Got Score: ', score);
        content = (await element.locator(contentFieldClassName).textContent())?.trim() as string;
        console.log('Got Content: ', content);
        date = (await element.locator(dateFieldClassName).textContent())?.trim() as string;
        console.log('Got Date: ', date);
        formattedDate = moment(date).toDate();
      } catch (error) {
        console.log(error);
        continue;
      }

      this.collection.push({
        author: name,
        score,
        content,
        createdAt: formattedDate,
      });
    }
    console.log('--------------------------------');
    console.log('End Crawling Review');

    return this.collection;
  }

  private async loadMoreReviews(frame: FrameLocator) {
    console.log('Load Next Page');
    const loadMoreButton = await frame.locator('button[name="review_more"]');

    if (await loadMoreButton.isVisible()) {
      await loadMoreButton.click();
      return true;
    } else {
      return false;
    }
  }

  private async exportCSV(reviews: Review[]) {
    const pathname = path.join(process.cwd(), `output`);
    const destination = `${pathname}/${moment().format('YYYY-MM-DD_HH-mm-ss')}-11st-reviews.csv`;

    await mkdir(pathname, { recursive: true }, (err) => {
      if (err) console.error(err);
    });

    await writeFile(destination, 'author,score,content,createdAt\n');

    for (const review of reviews) {
      await writeFile(destination, `${review.author},${review.score},${review.content},${review.createdAt}\n`, { flag: 'a', encoding: 'utf8' });
    }
    
    return destination
  }
}