import { chromium } from 'playwright';
import { Command } from 'commander';
import { SUPPORT_URL_SCHEMA } from './schema/support-url.schema.js';
import { getSiteName } from './utils/common.js';
import { SUPPORT_SHOP_NAME } from './constants/support-shop.constant.js';
import { St11 } from './helpers/st11.helper.js';
import { CrawlerHelper } from './interface/crawler-helper.interface.js';

(async () => {
  const program = new Command();
  const browser = await chromium.launch({
    headless: false,
  });

  program
    .requiredOption('-u, --url <url>', '해당 상품의 URL로 접속합니다.')
    .requiredOption('-m, --max-count <maxCount>', '크롤링 할 리뷰의 갯수를 지정합니다.');

  program.parse(process.argv);

  const { url, maxCount } = program.opts();
  const parsedUrl = SUPPORT_URL_SCHEMA.safeParse(url);

  if (parsedUrl.success === false) throw new Error(parsedUrl.error.message);

  let crawler: CrawlerHelper;
  const context = await browser.newContext();
  const page = await context.newPage();
  await page.goto(url);

  const siteName = getSiteName(url);

  if (siteName === SUPPORT_SHOP_NAME["11st"]) {
    crawler = new St11(page, url);
    await crawler.getReviewList(maxCount);
  }
})();