from playwright.async_api import async_playwright
from playwright.sync_api import sync_playwright
import requests
import asyncio
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, APIC, error
from PyPDF2 import PdfMerger
import os
import re
import sys
import time
import shutil

forbidden_chars = ["<", ">", ":", '"', "'", "/", "\\", "|", "?", "*", " "]

def auth(playwright):
    print("Signing you in...")
    # Grab session data after user is signed in
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context(storage_state="session.json" if 'session.json' in os.listdir('.') else None)

    page = context.new_page()
    page.goto('https://www.scribd.com/login', wait_until='domcontentloaded')

    page.locator("div.user_row").wait_for(state='attached', timeout=0)

    print('Logged in successfully.')

    storage = context.storage_state(path="session.json")
    context.close()
    browser.close()

def embedCover(audioPath, coverPath):
    audio_path = audioPath
    picture_path = coverPath
    audio = MP3(audio_path, ID3=ID3)

    # adding ID3 tag if it is not present
    try:
        audio.add_tags()
    except error:
        pass

    audio.tags.add(APIC(mime='image/jpeg',type=3,desc=u'Cover',data=open(picture_path,'rb').read()))
    # edit ID3 tags to open and read the picture from the path specified and assign it

    audio.save()  # save the current changes
    print("Embed cover")
    
async def audioBook():
    userLink = input("Input the link of the audio book you want to download: ")
    userLink = userLink.replace("audiobook", "listen")
    userLink = userLink[:userLink.rfind('/')]

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
            os.makedirs(f"./Downloaded/Audio Books/{title}")
        except FileExistsError:
            pass
        
        # Download Cover Image
        coverURL = await page.locator("main > div.left_col > div.thumbnail_container > img").get_attribute("src")
        cover = requests.get(coverURL)
        cover_size = len(cover.content)
        with open(f'./Downloaded/Audio Books/{title}/cover.jpg', 'wb') as f:
            f.write(cover.content)
            if (os.path.getsize(f'./Downloaded/Audio Books/{title}/cover.jpg') == cover_size):
                print(f"Downloaded cover image")
        
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
            with open(f'./Downloaded/Audio Books/{title}/{trackInfo}.mp3', 'wb') as f:
                f.write(track.content)
                if (os.path.getsize(f'./Downloaded/Audio Books/{title}/{trackInfo}.mp3') == track_size):
                    print(f"Downloaded {trackInfo}.mp3")
                    embedCover(f'./Downloaded/Audio Books/{title}/{trackInfo}.mp3', f'./Downloaded/Audio Books/{title}/cover.jpg')
                        
        print(f"Finished downloading your audio book: {title}")
        
def eBook():
    ZOOM = 0.625
    book_url = input("Enter the ebook url you want to download: ")

    # create cache dir
    book_filename = book_url.split('/')[5]
    cache_dir = f'{os.getcwd()}/{book_filename}'
    try:
        os.mkdir(cache_dir)
    except FileExistsError:
        pass

    with sync_playwright() as playwright:
        # Grab session data after user is signed in
        browser = playwright.chromium.launch(headless=False)
        context = browser.new_context(storage_state="session.json" if 'session.json' in os.listdir('.') else None)

        page = context.new_page()
        page.goto('https://www.scribd.com/login', wait_until='domcontentloaded')

        page.locator("div.user_row").wait_for(state='attached', timeout=0)

        print('Logged in successfully.')

        storage = context.storage_state(path="session.json")
        context.close()
        browser.close()

        browser = playwright.chromium.launch(headless=False)

        print('Loading viewer...')
    
        # After having the session data, proceed the user's link
        context = browser.new_context(
            storage_state=  "session.json",
            viewport={'width': 1200, 'height': 1600},
            ignore_https_errors = True,
            user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.181 Safari/537.36'
        )
        context.set_extra_http_headers({'Accept-Language': 'en-US,en;q=0.9'})

        page = context.new_page()
        page.goto(book_url.replace('book', 'read'))

        if 'Browser limit exceeded' in page.content():
            context.close()
            browser.close()
            sys.exit('You have tried to read this from too many computers or web browsers recently, and will need to wait up to 24 hours before returning to this book.')

        # retrieve fonts
        font_style = page.locator('#fontfaces').inner_html()

        # open display menu
        page.locator('.icon-ic_displaysettings').wait_for(state='visible')
        page.evaluate("() => document.querySelector('.icon-ic_displaysettings').click()")

        # change to vertical mode
        page.locator('.vertical_mode_btn').wait_for(state='visible')
        page.evaluate("() => document.querySelector('.vertical_mode_btn').click()")

        # open toc menu
        page.locator('div.vertical_page[data-page="0"]').wait_for(state='visible')
        page.evaluate("() => document.querySelector('.icon-ic_toc_list').click()")
        chapter_selector = page.locator('li.text_btn[role="none"]')
        chapter_selector.nth(0).wait_for(state='visible')

        # retrieve the number of chapters
        num_of_chapters = chapter_selector.count()

        # load the first chapter
        page.evaluate("() => document.querySelector('li.text_btn[data-idx=\"0\"]').click()")
        chapter_no = 1

        # to render the chapter pages and save them as pdf
        render_page = context.new_page()
        render_page.set_viewport_size({"width": 1200, "height": 1600})

        while True:

            page.locator('div.vertical_page[data-page="0"]').wait_for()

            chapter_pages = page.locator('div.vertical_page')
            number_of_chapter_pages = chapter_pages.count()

            print(f'Downloading chapter {chapter_no}/{num_of_chapters} ({number_of_chapter_pages} pages)')

            merger = PdfMerger()

            page_no = 1

            while True:

                page_elem = chapter_pages.nth(page_no-1)
                html = page_elem.inner_html()

                # replace img urls
                html = html.replace('src="/', 'src="https://www.scribd.com/')

                # set page size
                match = re.findall('width: ([0-9.]+)px; height: ([0-9.]+)px;', html)[0]
                width, height = float(match[0]), float(match[1])
                style = f'@page {{ size: {width*ZOOM}px {height*ZOOM}px; margin: 0; }} @media print {{ html, body {{ height: {height*ZOOM}px; width: {width*ZOOM}px;}}}}'
                html = re.sub('data-colindex="0" style="', 'data-colindex="0" x="', html)
                html = re.sub('position: absolute.*?"', f'overflow: hidden; height: {height}px; width: {width}px; white-space: nowrap; zoom: {ZOOM};"', html)

                # render page
                content = f'<style>{style}{font_style}</style>{html}'
                render_page.set_content(content)

                # print pdf
                pdf_file = f'{cache_dir}/{chapter_no}_{page_no}.pdf'
                render_page.pdf(path=pdf_file, prefer_css_page_size = True)
                merger.append(pdf_file)

                if page_no == number_of_chapter_pages:
                    merger.write(f"{cache_dir}/{chapter_no}.pdf")
                    merger.close()
                    break

                page_no += 1

            if chapter_no == num_of_chapters:
                break

            page.evaluate("() => document.querySelectorAll('button.load_next_btn')[0].click()")

            time.sleep(1)
            chapter_no += 1

    print('Merging PDF pages...')
    merger = PdfMerger()

    for chapter_no in range(1, num_of_chapters+1):
        merger.append(f"{cache_dir}/{chapter_no}.pdf")

    merger.write(f"{book_filename}.pdf")
    merger.close()

    # delete cache dir
    shutil.rmtree(cache_dir)

    print('Download completed, enjoy your book!')

if __name__ == '__main__':
    con = True
    while con:
        userChoice = input('''
                                                            Welcome to the     
                                                                                                                                                            
                                    ##  ###       ###                                    ###                   ###                
            ####                         ##        ##    #####                            ##                    ##                
            ##  #   ###   ### ##   ###    ###    ####      ## ##   ###  ## # ## ## ##     ##    ###    ###    ####    ###   ### ## 
            ####   ## ##   ###      ##   ## ##  ## ##      #   #  ## ##  # # #   ## ##    ##   ## ##     ##  ## ##   ## ##   ###   
            ### ##       ##       #    #  ## ##  ##     ##  ## ##  ##  #####   ## #    ##   ##  ##  ##### ##  ##  ######   ##    
            ##  #  ## ##   ##       ##   ## ##  ## ##      #  ##  ## ##   ####   ## ##    ##   ## ##  ## ##  ## ##   ##      ##     
            ####    ###   ####    ###### ####    #####    #####    ###    # #    ## ### #####   ###   ######  #####   ####  ####    
                                        
                                        
                                        Made with love ❤️  DanielHo (https://github.com/Hai567)     
                        
1. Download ebook
2. Download audio book  
3. Exit 
Choose (1/2): ''')

        if userChoice == "1":
            eBook()
        elif userChoice == "2":
            asyncio.run(audioBook())
        elif userChoice == "3":
            print("Exiting...")
            break
        else:
            print("Invalid choice, aborting...")
            break