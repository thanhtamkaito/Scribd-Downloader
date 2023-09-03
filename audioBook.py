from playwright.async_api import async_playwright
import requests
import asyncio
import os
forbidden_chars = ["<", ">", ":", '"', "'", "/", "\\", "|", "?", "*", " "]
userLink = input("Input the link of the audio book you want to download: ")
userLink = userLink.replace("audiobook", "listen")
userLink = userLink[:userLink.rfind('/')]

async def auth(playwright):
    # Grab session data after user is signed in
	browser = await playwright.chromium.launch(headless=False)
	context = await browser.new_context(storage_state="session.json" if 'session.json' in os.listdir('.') else None)

	page = await context.new_page()
	await page.goto('https://www.scribd.com/login', wait_until='domcontentloaded')

	await page.locator("div.user_row").wait_for(state='attached', timeout=0)

	print('Logged in successfully.')

	storage = await context.storage_state(path="session.json")
	await context.close()
	await browser.close()
    

async def main(userLink):
    async with async_playwright() as p:
        await auth(p)
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            storage_state=  "session.json",
            viewport={'width': 1200, 'height': 1600},
            ignore_https_errors = True,
            user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.181 Safari/537.36'
        )
        await context.set_extra_http_headers({'Accept-Language': 'en-US,en;q=0.9'})
        page = await context.new_page()
        await page.goto(userLink)
        
        await page.wait_for_load_state('domcontentloaded')
        # Get title then create new directory
        title = await page.locator("main > div.right_col > div > div > span > div.meta.control_row > h1 > a").inner_text()
        title = title[0: title.find("\n")]
        for forbiddenChar in forbidden_chars:
            if (forbiddenChar in title):
                title = title.replace(forbiddenChar, "-")
        try:
            os.mkdir(f"{title}")
        except FileExistsError:
            pass
        
        # Download Cover Image
        coverURL = await page.locator("main > div.left_col > div.thumbnail_container > img").get_attribute("src")
        cover = requests.get(coverURL)
        with open(f'{title}/cover.jpg', 'wb') as f:
            f.write(cover.content)
        
        # open toc menu
        await page.evaluate("() => document.querySelector('.icon-ic_toc_list').click()")
        await page.locator('.toc_container.menu_icon_container > div > div > div > div.button_menu_items_container > ul > li:nth-child(3) > a').wait_for(state='visible')
        contentList = page.locator("div.toc_container.menu_icon_container > div > div > div > div.button_menu_items_container > ul > li")
        # retrieve the number of chapters
        num_of_chapters = await contentList.count()
        await page.locator('div.toc_container.menu_icon_container > div > div > div > div.button_menu_items_container > ul > li:nth-child(1) > a').click()
        
        for i in range(num_of_chapters):
            audioLink = await page.evaluate("() => document.querySelector('audio#audioplayer').getAttribute('src')")
            trackInfo = await page.locator("div.track_info").inner_text()
            await page.evaluate("() => document.querySelector('button.text_btn.control.next_track.flat_btn.auto__base_component.auto__shared_react_common_button').click()")
            track = requests.get(audioLink)
            track_size = len(track.content)
            with open(f'{title}/{trackInfo}.mp3', 'wb') as f:
                f.write(track.content)
                if (os.path.getsize(f'{title}/{trackInfo}.mp3') == track_size):
                    print(f"Downloaded {trackInfo}.mp3")
        print(f"Finished downloading your audio book: {title}")
if __name__ == '__main__':
    if ("listen" not in userLink):
        print(f"It seems like {userLink} is not an audio book, please check again!")
    else:
        asyncio.run(main(userLink)) 