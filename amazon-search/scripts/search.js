#!/usr/bin/env node
import { searchAmazon, scrapeAmazonProduct, scrapeMultipleProducts, closeBrowser } from './scraper.js';

const args = process.argv.slice(2);
let query = '';
let asin = '';
let url = '';
let batch = [];
let domain = 'amazon.de';
let max = 10;
let delayMs = 2000;

for (let i = 0; i < args.length; i++) {
  if (args[i] === '--query' || args[i] === '-q') {
    query = args[++i];
  } else if (args[i] === '--asin' || args[i] === '-a') {
    asin = args[++i];
  } else if (args[i] === '--url' || args[i] === '-u') {
    url = args[++i];
  } else if (args[i] === '--batch' || args[i] === '-b') {
    batch = (args[++i] || '').split(',').map(s => s.trim()).filter(Boolean);
  } else if (args[i] === '--domain' || args[i] === '-d') {
    domain = args[++i];
  } else if (args[i] === '--max' || args[i] === '-m') {
    max = parseInt(args[++i], 10) || 10;
  } else if (args[i] === '--delay') {
    delayMs = parseInt(args[++i], 10) || 2000;
  }
}

async function main() {
  if (batch.length > 0) {
    const urls = batch.map(item => item.startsWith('http') ? item : `https://${domain}/dp/${item}`);
    const results = await scrapeMultipleProducts(urls);
    console.log(JSON.stringify(results, null, 2));
  } else if (url || asin) {
    const targetUrl = url || `https://${domain}/dp/${asin}`;
    const product = await scrapeAmazonProduct(targetUrl);
    console.log(JSON.stringify(product, null, 2));
  } else if (query) {
    // Add brief jitter delay before search to prevent burst rate-limiting
    await new Promise(r => setTimeout(r, 500 + Math.random() * 500));
    const results = await searchAmazon(query, domain, max);
    console.log(JSON.stringify(results, null, 2));
  } else {
    console.error('Usage: search.js [--query "text"] [--url "URL"] [--asin "ASIN"] [--batch "url1,url2"] [--domain "amazon.de"] [--max 10]');
    process.exit(1);
  }
  await closeBrowser();
}

main().catch(err => {
  console.error('Error:', err);
  process.exit(1);
});
