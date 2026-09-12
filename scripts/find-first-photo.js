const puppeteer = require('puppeteer-core');
const fs = require('fs');

(async () => {
    console.log("Launching headless browser with copied profile...");
    const browser = await puppeteer.launch({
        executablePath: 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
        headless: true, // Run headless so it doesn't bother the user
        userDataDir: 'C:\\Users\\megat\\TempChromeUserData',
        args: [
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-blink-features=AutomationControlled',
            '--profile-directory=Profile 9'
        ]
    });

    const page = await browser.newPage();
    
    // Set a realistic viewport
    await page.setViewport({ width: 1280, height: 800 });
    
    console.log("Navigating to Facebook Photos...");
    await page.goto('https://www.facebook.com/profile.php?id=1668818405&sk=photos_by', { waitUntil: 'networkidle2' });

    console.log("Scrolling to the very bottom to find the first photo ever posted...");
    let previousHeight = 0;
    let currentHeight = await page.evaluate('document.body.scrollHeight');
    let scrollAttempts = 0;

    while (scrollAttempts < 5) {
        await page.evaluate('window.scrollTo(0, document.body.scrollHeight)');
        await new Promise(r => setTimeout(r, 2000));
        
        previousHeight = currentHeight;
        currentHeight = await page.evaluate('document.body.scrollHeight');
        
        if (currentHeight === previousHeight) {
            scrollAttempts++;
            console.log(`Height unchanged. Attempt ${scrollAttempts}/5...`);
        } else {
            scrollAttempts = 0; // Reset
            console.log(`Scrolled... new height: ${currentHeight}`);
        }
    }

    console.log("Reached the bottom. Locating the oldest photo...");
    // Facebook photos in the grid usually have 'a' tags with href containing 'photo' or 'fbid'
    // The last one in the DOM should be the oldest.
    
    const photoLinks = await page.$$eval('a[href*="fbid"], a[href*="photo"]', links => 
        links.filter(a => a.querySelector('img')).map(a => a.href)
    );

    if (photoLinks.length > 0) {
        const oldestPhotoUrl = photoLinks[photoLinks.length - 1];
        console.log(`Oldest photo URL found: ${oldestPhotoUrl}`);
        
        console.log("Navigating to the oldest photo to get its date...");
        await page.goto(oldestPhotoUrl, { waitUntil: 'networkidle2' });
        
        await new Promise(r => setTimeout(r, 3000));

        const dateText = await page.evaluate(() => {
            const svgs = document.querySelectorAll('svg');
            for (let svg of svgs) {
                if (svg.getAttribute('aria-label') === 'Shared with Public' || svg.getAttribute('aria-label') === 'Shared with Friends') {
                    const container = svg.closest('a') || svg.closest('span');
                    if (container && container.innerText) {
                        return container.innerText;
                    }
                }
            }
            
            const links = Array.from(document.querySelectorAll('a'));
            for(let a of links) {
                if(a.innerText.match(/(January|February|March|April|May|June|July|August|September|October|November|December) \d{1,2}, \d{4}/i)) {
                    return a.innerText;
                }
                if(a.innerText.match(/\d{1,2} (Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec) \d{4}/i)) {
                    return a.innerText;
                }
            }
            return "Date not found explicitly via script. Please check the screenshot or manual review.";
        });

        console.log(`Extracted Date: ${dateText}`);
        fs.writeFileSync('C:\\Users\\megat\\Hermes-WebApp\\scripts\\first_photo_date.txt', `URL: ${oldestPhotoUrl}\nDate: ${dateText}`);
        
        await page.screenshot({ path: 'C:\\Users\\megat\\Hermes-WebApp\\scripts\\first_photo_proof.png' });
        console.log("Saved screenshot to first_photo_proof.png");
    } else {
        console.log("No photos found on the page. Taking a debug screenshot...");
        await page.screenshot({ path: 'C:\\Users\\megat\\Hermes-WebApp\\scripts\\debug_facebook.png' });
    }

    await browser.close();
    console.log("Browser closed. Job done.");
})();
