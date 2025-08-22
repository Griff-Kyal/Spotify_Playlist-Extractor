from playwright.sync_api import sync_playwright
import pandas as pd
import time
import json

from config import (
    playlist_url,
    max_attempts,
    run_headless
)

def scroll_and_load_all_tracks(page):
    """Scroll gradually to load all tracks dynamically."""
    previous_count = 0
    attempts = 0
    
    try:
        page.click('body')
        page.wait_for_timeout(500)
    except:
        pass
    
    print("Testing basic scrolling functionality ...")
    initial_scroll = page.evaluate("window.pageYOffset")
    page.evaluate("window.scrollBy(0, 100)")
    page.wait_for_timeout(500)
    after_scroll = page.evaluate("window.pageYOffset")
    print(f"Basic scroll test: {initial_scroll} -> {after_scroll}")
    
    scrollable_elements = page.evaluate("""
        () => {
            const elements = [];
            document.querySelectorAll('*').forEach(el => {
                if (el.scrollHeight > el.clientHeight) {
                    const style = window.getComputedStyle(el);
                    if (style.overflowY === 'scroll' || style.overflowY === 'auto' || style.overflow === 'auto') {
                        elements.push({
                            tag: el.tagName,
                            class: el.className,
                            id: el.id,
                            scrollHeight: el.scrollHeight,
                            clientHeight: el.clientHeight,
                            selector: el.tagName.toLowerCase() + 
                                     (el.id ? '#' + el.id : '') + 
                                     (el.className ? '.' + el.className.split(' ').join('.') : '')
                        });
                    }
                }
            });
            return elements;
        }
    """)
    
    print("Found scrollable elements:")
    for elem in scrollable_elements[:5]:
        print(f"  - {elem}")
    
    main_container = None
    for elem in scrollable_elements:
        if any(keyword in elem.get('class', '').lower() for keyword in ['main', 'content', 'scroll', 'tracklist']):
            main_container = elem['selector']
            print(f"Selected main container: {main_container}")
            break
    
    if not main_container and scrollable_elements:
        main_container = scrollable_elements[0]['selector']
        print(f"Using first scrollable element: {main_container}")
    
    while attempts < max_attempts:
        old_meta = page.locator('meta[name="music:song"]').count()
        old_dom = page.locator('[data-testid="tracklist-row"]').count()
        
        try:
            scrolled = False
            
            if main_container:
                result = page.evaluate(f"""
                    (() => {{
                        const el = document.querySelector('{main_container.replace("'", "\\'")}');
                        if (el) {{
                            const before = el.scrollTop;
                            el.scrollBy(0, 400);
                            const after = el.scrollTop;
                            console.log('Container scroll:', before, '->', after);
                            return after > before;
                        }}
                        return false;
                    }})()
                """)
                scrolled = result
                print(f"Container scroll result: {result}")
            
            if not scrolled:
                before = page.evaluate("window.pageYOffset")
                page.evaluate("window.scrollBy(0, 400)")
                after = page.evaluate("window.pageYOffset")
                scrolled = after > before
                print(f"Window scroll: {before} -> {after}")
            
            if not scrolled:
                page.keyboard.press("PageDown")
                page.wait_for_timeout(300)
                print("Used PageDown key")
                scrolled = True
            
            if not scrolled:
                page.mouse.wheel(0, 400)
                print("Used mouse wheel")
                scrolled = True
            
            page.wait_for_timeout(1500)
            
        except Exception as e:
            print(f"Scrolling error: {e}")
        
        new_meta = page.locator('meta[name="music:song"]').count()
        new_dom = page.locator('[data-testid="tracklist-row"]').count()
        global current_count
        current_count = max(new_meta, new_dom)
        
        print(f"Track count: {current_count} (meta: {old_meta}->{new_meta}, dom: {old_dom}->{new_dom})")
        
        if current_count == previous_count:
            attempts += 1
            print(f"No new tracks, attempt {attempts}/{max_attempts}")
        else:
            print(f"Found {current_count - previous_count} new tracks")
            attempts = max(0, attempts - 2)
            previous_count = current_count
    
    print(f"Final count: {current_count} tracks")
    return current_count

def total_songs_playlist(page):
    global song_count_total
    global validation_check
    """Get total number of songs in the playlist."""
    song_max_attempts = 3
    for attempt in range(song_max_attempts):
        try:
            song_count = page.locator('meta[name="music:song_count"]')
            if song_count.count() > 0:
                song_count_total = int(song_count.get_attribute("content", timeout=10000))
                print(f"Found {song_count_total} songs total in this playlist")
                validation_check = True
                return song_count_total
            else:
                print(f"Attempt {attempt + 1}: Song count meta tag not found, waiting ...")
                page.wait_for_timeout(2000)
        except Exception as e:
            print(f"Attempt {attempt + 1}: Error getting song count: {e}")
            if attempt < song_max_attempts - 1:
                page.wait_for_timeout(3000)
                
                # Try refreshing the page content
                page.evaluate("location.reload()")
                page.wait_for_timeout(5000)
                handle_cookie_banner(page)
    
    print("Warning: Could not determine total song count, proceeding anyway ...")
    validation_check = False
    song_count_total = 0
    return 0

def get_track_urls(page):
    """Extract track URLs from meta tags."""
    url_elements = page.locator('meta[name="music:song"]')
    url_count = url_elements.count()
    print(f"Found {url_count} tracks in metadata")

    urls = []
    for i in range(url_count):
        url = url_elements.nth(i).get_attribute("content")
        if url:
            urls.append(url)
    return urls

def get_tracks_from_dom(page):
    """Extract track information directly from DOM elements."""
    try:
        page.wait_for_selector('[data-testid="playlist-tracklist"]', timeout=10000)
        handle_cookie_banner(page)
        
        print("Scrolling to load all tracks ...")
        total_tracks = scroll_and_load_all_tracks(page)
        print(f"Finished scrolling, found {total_tracks} tracks")
        
        page.wait_for_timeout(2000)
        
        tracks = page.evaluate("""
            () => {
                const tracks = [];
                
                const trackSelectors = [
                    '[data-testid="tracklist-row"]',
                    '[role="row"]',
                    '.tracklist-row',
                    'div[data-testid*="track"]'
                ];
                
                let trackElements = [];
                for (const selector of trackSelectors) {
                    trackElements = document.querySelectorAll(selector);
                    if (trackElements.length > 0) {
                        console.log(`Found ${trackElements.length} tracks using selector: ${selector}`);
                        break;
                    }
                }
                
                trackElements.forEach((track, index) => {
                    try {
                        let titleElement = track.querySelector('a[data-testid="internal-track-link"]') ||
                                         track.querySelector('[data-testid="track-title"]') ||
                                         track.querySelector('a[href*="/track/"]') ||
                                         track.querySelector('.track-name a');
                        
                        let artistElements = track.querySelectorAll('a[href*="/artist/"]') ||
                                           track.querySelectorAll('[data-testid="track-artist"] a') ||
                                           track.querySelectorAll('.artist-name a');
                        
                        if (titleElement) {
                            const title = titleElement.textContent.trim();
                            const artists = Array.from(artistElements).map(a => a.textContent.trim()).filter(name => name).join(', ');
                            const url = titleElement.href;
                            
                            if (title) {
                                tracks.push({
                                    title: title,
                                    artists: artists || 'Unknown Artist',
                                    url: url || '',
                                    index: index + 1
                                });
                            }
                        }
                    } catch (e) {
                        console.log('Error processing track:', e);
                    }
                });
                
                console.log(`Successfully extracted ${tracks.length} tracks`);
                return tracks;
            }
        """)
        
        return tracks
    except Exception as e:
        print(f"Error extracting from DOM: {e}")
        return []

def fetch_track_data(playwright, track_url):
    """Fetch detailed track data from individual track pages."""
    try:
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        page.goto(track_url, timeout=30000)
        page.wait_for_timeout(1000)

        title = page.locator('meta[property="og:title"]').get_attribute("content")
        artist = page.locator('meta[name="music:musician_description"]').get_attribute("content")
        
        if not title:
            title = page.locator('h1[data-testid="entityTitle"]').text_content()
        
        if not artist:
            artist_elements = page.locator('a[href*="/artist/"]')
            if artist_elements.count() > 0:
                artists = []
                for i in range(artist_elements.count()):
                    artists.append(artist_elements.nth(i).text_content())
                artist = ", ".join(artists)

        browser.close()

        if title and artist:
            return {
                "Title": title.strip(),
                "Artist(s)": artist.strip(),
                "URL": track_url
            }
        else:
            print(f"Missing data for {track_url}")
    except Exception as e:
        print(f"Error fetching data for {track_url}: {e}")
    return None

def handle_cookie_banner(page):
    """Handle cookie consent banners that might interfere with scrolling."""
    try:
        page.wait_for_timeout(3000)
        
        cookie_selectors = [
            'button[id*="onetrust-accept"]',
            'button[data-testid="cookie-accept-all"]',
            'button:has-text("Accept All")',
            'button:has-text("Accept all cookies")',
            'button:has-text("Accept")',
            '#onetrust-accept-btn-handler',
            '.onetrust-close-btn-handler',
            'button[aria-label*="Accept"]'
        ]
        
        for selector in cookie_selectors:
            try:
                cookie_button = page.locator(selector).first
                if cookie_button.is_visible(timeout=2000):
                    print(f"Found cookie banner, clicking: {selector}")
                    cookie_button.click(timeout=5000)
                    page.wait_for_timeout(2000)
                    
                    # Wait for the cookie banner to disappear
                    try:
                        cookie_button.wait_for(state='hidden', timeout=5000)
                        print("Cookie banner dismissed successfully")
                    except:
                        print("Cookie banner may still be visible")
                    
                    return True
            except Exception as e:
                print(f"Failed to click {selector}: {e}")
                continue
                
        # Additional fallback - try to dismiss any modal or overlay
        try:
            page.keyboard.press("Escape")
            page.wait_for_timeout(1000)
            
            # Check if there are any modal overlays and try to close them
            modal_selectors = [
                '[role="dialog"]',
                '.modal',
                '[data-testid="modal"]',
                '.overlay'
            ]
            
            for modal_selector in modal_selectors:
                modals = page.locator(modal_selector)
                if modals.count() > 0:
                    print(f"Found modal overlay: {modal_selector}")
                    # Try to find close button in modal
                    close_buttons = page.locator(f'{modal_selector} button:has-text("Close"), {modal_selector} button[aria-label*="close"], {modal_selector} .close')
                    if close_buttons.count() > 0:
                        close_buttons.first.click()
                        page.wait_for_timeout(1000)
                        
        except Exception as e:
            print(f"Modal dismissal failed: {e}")
        
    except Exception as e:
        print(f"Cookie banner handling: {e}")
    
    return False

def main(headless=True):
    """Main function to extract playlist data."""
    with sync_playwright() as playwright:
        browser_args = ['--disable-web-security', '--disable-blink-features=AutomationControlled']
        
        if not headless:
            browser_args.append('--start-maximized')
            
        browser = playwright.chromium.launch(
            headless=headless,
            args=browser_args
        )
        context = browser.new_context(
            viewport={'width': 1920, 'height': 1080} if headless else None,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        
        if not headless:
            try:
                page.set_viewport_size({'width': 1920, 'height': 1080})
            except:
                pass
        
        print("Loading playlist page ...")
        page.goto(playlist_url, timeout=30000)
        
        print("Handling cookie banner ...")
        banner_handled = handle_cookie_banner(page)
        if not banner_handled:
            print(f"Unsuccessfull, attempting one more time ...")
            handle_cookie_banner(page)

        # Give extra time for page to settle after cookie handling
        page.wait_for_timeout(3000)
        
        # Verify page is fully loaded by checking for key elements
        try:
            page.wait_for_selector('[data-testid="playlist-tracklist"], [data-testid="entityTitle"]', timeout=15000)
            print("Playlist page loaded successfully")
        except:
            print("Warning: Playlist elements not fully loaded, attempting to continue ...")
        
        if not headless:
            page.bring_to_front()

        total_songs_playlist(page)
        
        print("Attempting to extract tracks from DOM ...")
        
        initial_meta = page.locator('meta[name="music:song"]').count()
        initial_dom = page.locator('[data-testid="tracklist-row"]').count()
        print(f"Initial track counts - Meta: {initial_meta}, DOM: {initial_dom}")
        
        dom_tracks = get_tracks_from_dom(page)
        
        if dom_tracks:
            print(f"Successfully extracted {len(dom_tracks)} tracks from DOM")
            track_data = []
            for track in dom_tracks:
                track_data.append({
                    "Title": track["title"],
                    "Artist(s)": track["artists"],
                    "URL": track["url"]
                })
        else:
            print("DOM extraction failed, trying metadata extraction ...")
            scroll_and_load_all_tracks(page)
            track_urls = get_track_urls(page)
            browser.close()
            
            if not track_urls:
                print("No tracks found!")
                return
            
            print(f"Found {len(track_urls)} track URLs, fetching detailed data ...")
            track_data = []
            for index, url in enumerate(track_urls):
                print(f"Progress: {index+1}/{len(track_urls)}")
                info = fetch_track_data(playwright, url)
                if info:
                    track_data.append(info)
                time.sleep(0.5)
        
        browser.close()

        if not validation_check:
            print(f"Could not get total nuber of songs. Skipping validation check ...")
        else:
            if song_count_total == current_count:
                print("Validation successful - all tracks loaded")
            else:
                print(f"Validation failed, difference of {song_count_total - current_count} songs")
        
        if track_data:
            df = pd.DataFrame(track_data)
            df.to_csv("spotify_playlist.csv", index=False)
            print(f"Successfully saved {len(df)} tracks to spotify_playlist.csv")
            
            with open("spotify_playlist.json", "w", encoding="utf-8") as f:
                json.dump(track_data, f, indent=2, ensure_ascii=False)
            print("Also saved as JSON backup")
        else:
            print("No track data was extracted!")

if __name__ == "__main__":
    main(headless=run_headless)