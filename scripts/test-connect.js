const puppeteer = require('puppeteer-core');

(async () => {
    try {
        console.log("Fetching browser WS endpoint...");
        const response = await fetch('http://127.0.0.1:9222/json/version');
        const data = await response.json();
        const wsEndpoint = data.webSocketDebuggerUrl;
        console.log("WS Endpoint: " + wsEndpoint);

        const browser = await puppeteer.connect({
            browserWSEndpoint: wsEndpoint,
            defaultViewport: null
        });

        const pages = await browser.pages();
        console.log("Found " + pages.length + " open tabs.");
        for (let i = 0; i < pages.length; i++) {
            console.log("Tab " + i + ": " + await pages[i].title() + " - " + await pages[i].url());
        }

        browser.disconnect();
    } catch (e) {
        console.error(e);
    }
})();
