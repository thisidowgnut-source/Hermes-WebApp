const puppeteer = require('puppeteer-core');

(async () => {
    console.log("Launching Chrome...");
    const browser = await puppeteer.launch({
        executablePath: 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
        headless: true,
        userDataDir: 'C:\\Users\\megat\\AppData\\Local\\Google\\Chrome\\User Data',
        args: ['--profile-directory=Profile 9']
    });

    console.log("Opening new page...");
    const page = await browser.newPage();
    
    console.log("Navigating to Facebook profile...");
    await page.goto('https://www.facebook.com/profile.php?id=1668818405', { waitUntil: 'networkidle2' });

    console.log("Reviewing profile info...");
    const profileName = await page.evaluate(() => {
        const h1 = document.querySelector('h1');
        return h1 ? h1.innerText : 'Name not found';
    });

    console.log(`Profile Name: ${profileName}`);
    
    // Check if we need to post
    // If the user wants to post, we can find the "What's on your mind?" input
    console.log("Checking for post input...");
    const postBox = await page.$('div[role="button"]:has-text("What\'s on your mind")');
    if (postBox) {
        console.log("Post box found. Ready to post.");
    } else {
        console.log("Post box not found. Ensure we are logged in.");
    }

    // Keep browser open for user to see
    await browser.close();
})();
