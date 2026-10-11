#!/usr/bin/env node
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { CallToolRequestSchema, ListToolsRequestSchema, } from "@modelcontextprotocol/sdk/types.js";
import { chromium } from "playwright";
const LOCALE_MAP = {
    "amazon.com": { domain: "amazon.com", acceptLanguage: "en-US,en;q=0.9", currencySymbol: "$", currency: "USD" },
    "amazon.co.uk": { domain: "amazon.co.uk", acceptLanguage: "en-GB,en;q=0.9", currencySymbol: "£", currency: "GBP" },
    "amazon.de": { domain: "amazon.de", acceptLanguage: "de-DE,de;q=0.9,en;q=0.8", currencySymbol: "€", currency: "EUR" },
    "amazon.fr": { domain: "amazon.fr", acceptLanguage: "fr-FR,fr;q=0.9,en;q=0.8", currencySymbol: "€", currency: "EUR" },
    "amazon.co.jp": { domain: "amazon.co.jp", acceptLanguage: "ja-JP,ja;q=0.9,en;q=0.8", currencySymbol: "¥", currency: "JPY" },
    "amazon.ca": { domain: "amazon.ca", acceptLanguage: "en-CA,en;q=0.9", currencySymbol: "$", currency: "CAD" },
    "amazon.com.au": { domain: "amazon.com.au", acceptLanguage: "en-AU,en;q=0.9", currencySymbol: "$", currency: "AUD" },
    "amazon.es": { domain: "amazon.es", acceptLanguage: "es-ES,es;q=0.9,en;q=0.8", currencySymbol: "€", currency: "EUR" },
    "amazon.it": { domain: "amazon.it", acceptLanguage: "it-IT,it;q=0.9,en;q=0.8", currencySymbol: "€", currency: "EUR" },
    "amazon.nl": { domain: "amazon.nl", acceptLanguage: "nl-NL,nl;q=0.9,en;q=0.8", currencySymbol: "€", currency: "EUR" },
    "amazon.com.br": { domain: "amazon.com.br", acceptLanguage: "pt-BR,pt;q=0.9,en;q=0.8", currencySymbol: "R$", currency: "BRL" },
    "amazon.com.mx": { domain: "amazon.com.mx", acceptLanguage: "es-MX,es;q=0.9,en;q=0.8", currencySymbol: "$", currency: "MXN" },
    "amazon.in": { domain: "amazon.in", acceptLanguage: "en-IN,en;q=0.9", currencySymbol: "₹", currency: "INR" },
    "amazon.sg": { domain: "amazon.sg", acceptLanguage: "en-SG,en;q=0.9", currencySymbol: "$", currency: "SGD" },
    "amazon.ae": { domain: "amazon.ae", acceptLanguage: "en-AE,en;q=0.9,ar;q=0.8", currencySymbol: "AED", currency: "AED" },
    "amazon.sa": { domain: "amazon.sa", acceptLanguage: "ar-SA,ar;q=0.9,en;q=0.8", currencySymbol: "SAR", currency: "SAR" },
    "amazon.se": { domain: "amazon.se", acceptLanguage: "sv-SE,sv;q=0.9,en;q=0.8", currencySymbol: "kr", currency: "SEK" },
    "amazon.pl": { domain: "amazon.pl", acceptLanguage: "pl-PL,pl;q=0.9,en;q=0.8", currencySymbol: "zł", currency: "PLN" },
    "amazon.com.tr": { domain: "amazon.com.tr", acceptLanguage: "tr-TR,tr;q=0.9,en;q=0.8", currencySymbol: "₺", currency: "TRY" },
    "amazon.eg": { domain: "amazon.eg", acceptLanguage: "ar-EG,ar;q=0.9,en;q=0.8", currencySymbol: "EGP", currency: "EGP" },
};
function getLocaleFromUrl(url) {
    for (const [domain, config] of Object.entries(LOCALE_MAP)) {
        if (url.includes(domain))
            return config;
    }
    return LOCALE_MAP["amazon.com"];
}
const BRAND_PREFIXES = [
    "Visit the ", "Brand: ", "Store: ",
    "ブランド: ", "ストア: ",
    "Marke: ", "Besuche den ",
    "Marque : ", "Marque: ", "Visiter la boutique ",
    "Marca: ", "Visita la tienda de ",
    "Marca: ", "Visita lo Store di ",
    "Marca: ", "Visite a loja ",
    "Merk: ", "Bezoek de ",
    "Marka: ",
    "Varumärke: ",
];
const BRAND_SUFFIXES = [
    " Store", " store", "-Store", " Shop", " shop",
    "ストア",
];
const DATE_LABELS = [
    "date first available",
    "発売日",
    "im angebot von amazon.de seit",
    "disponible sur amazon.fr depuis",
    "disponible en amazon.es desde",
    "disponibile su amazon.it dal",
    "date de mise en ligne",
    "disponível na amazon.com.br desde",
];
const RANKING_LABELS = [
    "best seller", "ranking", "bestseller",
    "ランキング",
    "amazon bestseller-rang",
    "classement des meilleures ventes",
    "clasificación en los más vendidos",
    "posizione nella classifica bestseller",
];
function cleanBrand(text) {
    let cleaned = text;
    for (const prefix of BRAND_PREFIXES) {
        if (cleaned.toLowerCase().startsWith(prefix.toLowerCase())) {
            cleaned = cleaned.slice(prefix.length);
            break;
        }
    }
    for (const suffix of BRAND_SUFFIXES) {
        if (cleaned.toLowerCase().endsWith(suffix.toLowerCase())) {
            cleaned = cleaned.slice(0, -suffix.length);
            break;
        }
    }
    return cleaned.trim();
}
function matchesAny(text, patterns) {
    const lowerText = text.toLowerCase();
    return patterns.some(pattern => lowerText.includes(pattern.toLowerCase()));
}
let browser = null;
async function getBrowser() {
    if (!browser) {
        browser = await chromium.launch({
            headless: true,
            executablePath: process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH || undefined,
            args: ["--no-sandbox", "--disable-setuid-sandbox"],
        });
    }
    return browser;
}
async function delay(ms) {
    return new Promise((resolve) => setTimeout(resolve, ms));
}
function extractAsin(url) {
    const patterns = [
        /\/dp\/([A-Z0-9]{10})/i,
        /\/gp\/product\/([A-Z0-9]{10})/i,
        /\/asin\/([A-Z0-9]{10})/i,
        /\/product\/([A-Z0-9]{10})/i,
    ];
    for (const pattern of patterns) {
        const match = url.match(pattern);
        if (match)
            return match[1];
    }
    return "";
}
function cleanText(text) {
    if (!text)
        return "";
    return text
        .replace(/\s+/g, " ")
        .replace(/[\n\r\t]/g, " ")
        .replace(/\s{2,}/g, " ")
        .replace(/var\s+\w+.*?;/g, "")
        .replace(/P\.when\(.*?\);/gs, "")
        .replace(/window\.\w+.*?;/g, "")
        .trim();
}
export async function scrapeAmazonProduct(url) {
    const locale = getLocaleFromUrl(url);
    const result = {
        url,
        asin: extractAsin(url),
        title: "",
        price: "",
        originalPrice: "",
        discount: "",
        currency: "",
        brand: "",
        seller: "",
        category: "",
        description: "",
        features: [],
        specs: {},
        images: [],
        rating: "",
        ratingValue: 0,
        reviewCount: "",
        availability: "",
        isPrime: false,
        productDimensions: "",
        weight: "",
        dateFirstAvailable: "",
        bestSellerRank: "",
    };
    let page = null;
    try {
        const browserInstance = await getBrowser();
        page = await browserInstance.newPage();
        await page.setExtraHTTPHeaders({
            "Accept-Language": locale.acceptLanguage,
            Accept: "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        });
        await page.setViewportSize({ width: 1920, height: 1080 });
        await page.goto(url, { waitUntil: "domcontentloaded", timeout: 30000 });
        await delay(2000);
        const captchaPresent = await page
            .locator('input[name="captchacharacters"]')
            .isVisible()
            .catch(() => false);
        if (captchaPresent) {
            result.error = "CAPTCHA detected - please try again later";
            return result;
        }
        result.title = cleanText(await page
            .locator("#productTitle, #title, h1.a-size-large, h1 span")
            .first()
            .textContent()
            .catch(() => ""));
        await delay(1500 + Math.random() * 1000);
        result.brand = cleanBrand(cleanText(await page
            .locator("#bylineInfo")
            .textContent()
            .catch(() => "")));
        result.price = cleanText(await page
            .locator(".a-price .a-offscreen")
            .first()
            .textContent()
            .catch(() => ""));
        if (!result.price) {
            result.price = cleanText(await page
                .locator("#priceblock_ourprice, #priceblock_dealprice, #corePrice_feature_div .a-price-whole")
                .first()
                .textContent()
                .catch(() => ""));
        }
        result.originalPrice = cleanText(await page
            .locator(".basisPrice .a-offscreen, #priceblock_listprice, .a-text-strike")
            .first()
            .textContent()
            .catch(() => ""));
        result.discount = cleanText(await page
            .locator(".savingsPercentage, #dealprice_savings_percentage")
            .first()
            .textContent()
            .catch(() => ""));
        if (result.price) {
            if (result.price.includes("¥") || result.price.includes("￥")) {
                result.currency = "JPY";
            }
            else if (result.price.includes("£")) {
                result.currency = "GBP";
            }
            else if (result.price.includes("€")) {
                result.currency = "EUR";
            }
            else if (result.price.includes("₹")) {
                result.currency = "INR";
            }
            else if (result.price.includes("R$")) {
                result.currency = "BRL";
            }
            else if (result.price.includes("₺")) {
                result.currency = "TRY";
            }
            else if (result.price.includes("zł")) {
                result.currency = "PLN";
            }
            else if (result.price.includes("kr")) {
                result.currency = "SEK";
            }
            else if (result.price.includes("$")) {
                result.currency = locale.currency;
            }
            else {
                result.currency = locale.currency;
            }
        }
        const ratingText = await page
            .locator("#acrPopover")
            .getAttribute("title")
            .catch(() => "");
        result.rating = cleanText(ratingText);
        const ratingMatch = result.rating.match(/(\d+\.?\d*)/);
        if (ratingMatch) {
            result.ratingValue = parseFloat(ratingMatch[1]);
        }
        result.reviewCount = cleanText(await page
            .locator("#acrCustomerReviewText")
            .textContent()
            .catch(() => ""));
        result.availability = cleanText(await page
            .locator("#availability span, #availability")
            .first()
            .textContent()
            .catch(() => ""));
        result.isPrime = await page
            .locator(".a-icon-prime, #prime-icon")
            .isVisible()
            .catch(() => false);
        result.seller = cleanText(await page
            .locator("#sellerProfileTriggerId, #merchant-info")
            .textContent()
            .catch(() => ""));
        const mainImage = await page
            .locator("#landingImage, #imgBlkFront, #main-image")
            .getAttribute("src")
            .catch(() => "");
        if (mainImage && !mainImage.includes("data:image")) {
            result.images.push(mainImage);
        }
        const hiResImage = await page
            .locator("#landingImage")
            .getAttribute("data-old-hires")
            .catch(() => "");
        if (hiResImage && !result.images.includes(hiResImage)) {
            result.images.unshift(hiResImage);
        }
        const thumbnails = await page.locator("#altImages img").all();
        for (const thumb of thumbnails.slice(0, 5)) {
            const src = await thumb.getAttribute("src").catch(() => "");
            if (src && !src.includes("data:image") && !src.includes("icon")) {
                const largeUrl = src.replace(/\._.*_\./, "._AC_SL1500_.");
                if (!result.images.includes(largeUrl)) {
                    result.images.push(largeUrl);
                }
            }
        }
        const featureBullets = await page
            .locator("#feature-bullets li span.a-list-item")
            .all();
        for (const bullet of featureBullets) {
            const text = cleanText(await bullet.textContent().catch(() => ""));
            if (text &&
                text.length > 5 &&
                !text.toLowerCase().includes("click here")) {
                result.features.push(text);
            }
        }
        result.description = cleanText(await page
            .locator("#productDescription p, #productDescription")
            .first()
            .textContent()
            .catch(() => ""));
        const breadcrumbs = await page
            .locator("#wayfinding-breadcrumbs_feature_div li a")
            .all();
        const categories = [];
        for (const crumb of breadcrumbs) {
            const text = cleanText(await crumb.textContent().catch(() => ""));
            if (text)
                categories.push(text);
        }
        result.category = categories.join(" > ");
        const specSelectors = [
            "#productDetails_techSpec_section_1 tr",
            "#productDetails_detailBullets_sections1 tr",
            "#technicalSpecifications_section_1 tr",
            ".prodDetTable tr",
            "#productDetails_db_sections tr",
        ];
        for (const selector of specSelectors) {
            const rows = await page.locator(selector).all();
            for (const row of rows) {
                const key = cleanText(await row
                    .locator("th")
                    .first()
                    .textContent()
                    .catch(() => ""));
                const value = cleanText(await row
                    .locator("td")
                    .first()
                    .textContent()
                    .catch(() => ""));
                if (key && value && key !== value && !value.includes("P.when")) {
                    const cleanKey = key.replace(/[‎\u200E]/g, "").trim();
                    const cleanValue = value.replace(/[‎\u200E]/g, "").trim();
                    if (cleanKey && cleanValue) {
                        result.specs[cleanKey] = cleanValue;
                        if (cleanKey.toLowerCase().includes("dimension")) {
                            result.productDimensions = cleanValue;
                        }
                        if (cleanKey.toLowerCase().includes("weight") &&
                            !cleanKey.toLowerCase().includes("item")) {
                            result.weight = cleanValue;
                        }
                        if (matchesAny(cleanKey, DATE_LABELS)) {
                            result.dateFirstAvailable = cleanValue;
                        }
                        if (matchesAny(cleanKey, RANKING_LABELS)) {
                            result.bestSellerRank = cleanValue;
                        }
                    }
                }
            }
        }
        const detailBullets = await page
            .locator("#detailBullets_feature_div li, #productDetails_detailBullets_sections1 li")
            .all();
        for (const bullet of detailBullets) {
            const text = await bullet.textContent().catch(() => "");
            if (text) {
                const colonIndex = text.indexOf(":");
                if (colonIndex > 0) {
                    const key = cleanText(text.substring(0, colonIndex));
                    const value = cleanText(text.substring(colonIndex + 1));
                    if (key && value && !value.includes("P.when")) {
                        result.specs[key] = value;
                    }
                }
            }
        }
        const additionalInfo = await page
            .locator("#productDetails_expanderTables_dep498 tr, #detailBulletsWrapper_feature_div li")
            .all();
        for (const item of additionalInfo) {
            const text = await item.textContent().catch(() => "");
            if (text && text.includes(":")) {
                const parts = text.split(":");
                if (parts.length >= 2) {
                    const key = cleanText(parts[0]);
                    const value = cleanText(parts.slice(1).join(":"));
                    if (key && value && !result.specs[key]) {
                        result.specs[key] = value;
                    }
                }
            }
        }
        for (const [key, value] of Object.entries(result.specs)) {
            if (value.includes("var ") ||
                value.includes("function") ||
                value.includes("window.") ||
                value.length > 500) {
                delete result.specs[key];
            }
        }
    }
    catch (error) {
        result.error = `Error scraping: ${error instanceof Error ? error.message : String(error)}`;
    }
    finally {
        if (page) {
            await page.close().catch(() => { });
        }
    }
    return result;
}
export async function searchAmazon(query, domain = "amazon.com", maxResults = 10) {
    const locale = LOCALE_MAP[domain] || LOCALE_MAP["amazon.com"];
    const result = {
        query,
        totalResults: "",
        results: [],
    };
    let page = null;
    try {
        const browserInstance = await getBrowser();
        page = await browserInstance.newPage();
        await page.setExtraHTTPHeaders({
            "Accept-Language": locale.acceptLanguage,
            Accept: "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        });
        await page.setViewportSize({ width: 1920, height: 1080 });
        await page.route("**/*", (route) => {
            const type = route.request().resourceType();
            if (["image", "media", "font", "stylesheet"].includes(type)) {
                return route.abort();
            }
            return route.continue();
        });
        const searchUrl = `https://${domain}/s?k=${encodeURIComponent(query)}`;
        await page.goto(searchUrl, {
            waitUntil: "commit",
            timeout: 10000,
        });
        await page.waitForSelector('[data-component-type="s-search-result"]', {
            timeout: 5000,
        }).catch(() => { });
        await delay(300);
        const captchaPresent = await page
            .locator('input[name="captchacharacters"]')
            .isVisible()
            .catch(() => false);
        if (captchaPresent) {
            result.error = "CAPTCHA detected - please try again later";
            return result;
        }
        result.totalResults = cleanText(await page.evaluate(() => {
            const el = document.querySelector(".s-result-count, .sg-col-inner h1");
            return el?.textContent?.trim() || "";
        }));
        const rawItems = await page.evaluate((max) => {
            const elements = Array.from(document.querySelectorAll('[data-component-type="s-search-result"]'));
            return elements.slice(0, max).map((item) => {
                const asin = item.getAttribute("data-asin") || "";
                const titleEl = item.querySelector("h2 a span, .a-text-normal");
                const title = titleEl ? titleEl.textContent?.trim() || "" : "";
                const linkEl = item.querySelector("h2 a, a.a-link-normal[href*='/dp/']");
                const href = linkEl ? linkEl.getAttribute("href") : "";
                const priceEl = item.querySelector(".a-price .a-offscreen");
                const price = priceEl ? priceEl.textContent?.trim() || "" : "";
                const ratingEl = item.querySelector(".a-icon-star-small .a-icon-alt, .a-icon-star .a-icon-alt, .a-icon-alt");
                const rating = ratingEl ? ratingEl.textContent?.trim() || "" : "";
                const reviewEl = item.querySelector('[aria-label*="rating"], .a-size-small .a-link-normal');
                const reviewCount = reviewEl ? reviewEl.textContent?.trim() || "" : "";
                const imgEl = item.querySelector(".s-image");
                const image = imgEl ? imgEl.getAttribute("src") || "" : "";
                const primeEl = item.querySelector(".a-icon-prime, [aria-label*='Prime']");
                const isPrime = !!primeEl;
                const bestSellerEl = item.querySelector(".a-badge-text");
                const isBestSeller = !!bestSellerEl;
                return {
                    asin,
                    title,
                    href,
                    price,
                    rating,
                    reviewCount,
                    image,
                    isPrime,
                    isBestSeller
                };
            });
        }, maxResults);
        for (const item of rawItems) {
            if (item.title && item.asin) {
                const url = item.asin ? `https://${domain}/dp/${item.asin}` : (item.href ? `https://${domain}${item.href.split("?")[0]}` : "");
                result.results.push({
                    asin: item.asin,
                    title: cleanText(item.title),
                    url,
                    price: cleanText(item.price),
                    rating: cleanText(item.rating),
                    reviewCount: cleanText(item.reviewCount),
                    image: item.image,
                    isPrime: item.isPrime,
                    isBestSeller: item.isBestSeller,
                });
            }
        }
    }
    catch (error) {
        result.error = `Error searching: ${error instanceof Error ? error.message : String(error)}`;
    }
    finally {
        if (page) {
            await page.close().catch(() => { });
        }
    }
    return result;
}
export async function scrapeMultipleProducts(urls) {
    const results = [];
    for (let i = 0; i < urls.length; i++) {
        const url = urls[i];
        console.error(`Scraping ${i + 1}/${urls.length}: ${url}`);
        const result = await scrapeAmazonProduct(url);
        results.push(result);
        if (i < urls.length - 1) {
            await delay(3000 + Math.random() * 2000);
        }
    }
    return results;
}
const server = new Server({
    name: "amazon-scraper",
    version: "1.0.0",
}, {
    capabilities: {
        tools: {},
    },
});
server.setRequestHandler(ListToolsRequestSchema, async () => {
    return {
        tools: [
            {
                name: "scrape_amazon_product",
                description: "Scrape detailed product information from any Amazon product URL. Returns comprehensive data including title, price, brand, all specs, features, images, ratings, availability, and more. Works with any Amazon domain (JP, US, UK, etc.) and any product category.",
                inputSchema: {
                    type: "object",
                    properties: {
                        url: {
                            type: "string",
                            description: "Full Amazon product URL (e.g., https://www.amazon.com/dp/B0XXXXXXXX). Works with any Amazon domain.",
                        },
                    },
                    required: ["url"],
                },
            },
            {
                name: "scrape_amazon_batch",
                description: "Scrape multiple Amazon products at once. Includes automatic delays to avoid rate limiting. Returns an array of detailed product data.",
                inputSchema: {
                    type: "object",
                    properties: {
                        urls: {
                            type: "array",
                            items: { type: "string" },
                            description: "Array of Amazon product URLs to scrape",
                        },
                    },
                    required: ["urls"],
                },
            },
            {
                name: "search_amazon",
                description: "Search for products on Amazon. Returns a list of matching products with basic info (title, price, rating, Prime status). Use this to find products before scraping detailed info.",
                inputSchema: {
                    type: "object",
                    properties: {
                        query: {
                            type: "string",
                            description: "Search query (e.g., 'gaming monitor 27 inch')",
                        },
                        domain: {
                            type: "string",
                            description: "Amazon domain (default: amazon.com). Supported: amazon.com, amazon.co.uk, amazon.de, amazon.fr, amazon.co.jp, amazon.ca, amazon.com.au, amazon.es, amazon.it, amazon.nl, amazon.com.br, amazon.com.mx, amazon.in, amazon.sg, amazon.ae, amazon.sa, amazon.se, amazon.pl, amazon.com.tr, amazon.eg",
                            default: "amazon.com",
                        },
                        maxResults: {
                            type: "number",
                            description: "Maximum number of results to return (default: 10, max: 20)",
                            default: 10,
                        },
                    },
                    required: ["query"],
                },
            },
        ],
    };
});
server.setRequestHandler(CallToolRequestSchema, async (request) => {
    const { name, arguments: args } = request.params;
    try {
        if (name === "scrape_amazon_product") {
            const { url } = args;
            const result = await scrapeAmazonProduct(url);
            return {
                content: [{ type: "text", text: JSON.stringify(result, null, 2) }],
            };
        }
        if (name === "scrape_amazon_batch") {
            const { urls } = args;
            const results = await scrapeMultipleProducts(urls);
            return {
                content: [{ type: "text", text: JSON.stringify(results, null, 2) }],
            };
        }
        if (name === "search_amazon") {
            const { query, domain = "amazon.co.jp", maxResults = 10, } = args;
            const results = await searchAmazon(query, domain, Math.min(maxResults, 20));
            return {
                content: [{ type: "text", text: JSON.stringify(results, null, 2) }],
            };
        }
        return {
            content: [{ type: "text", text: `Unknown tool: ${name}` }],
            isError: true,
        };
    }
    catch (error) {
        return {
            content: [
                {
                    type: "text",
                    text: `Error: ${error instanceof Error ? error.message : String(error)}`,
                },
            ],
            isError: true,
        };
    }
});
process.on("SIGINT", async () => {
    if (browser)
        await browser.close();
    process.exit(0);
});
process.on("SIGTERM", async () => {
    if (browser)
        await browser.close();
    process.exit(0);
});
export async function closeBrowser() {
    if (browser) {
        await browser.close();
        browser = null;
    }
}
async function main() {
    const transport = new StdioServerTransport();
    await server.connect(transport);
    console.error("Amazon Scraper MCP v1.0.0 running on stdio");
}
if (process.argv[1] && (process.argv[1].endsWith("index.js") || process.argv[1].endsWith("index.ts"))) {
    main().catch(console.error);
}
