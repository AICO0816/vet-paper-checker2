import feedparser
import ssl
from datetime import datetime
import pytz
import requests
import sys
import traceback

# --- 設定項目 ---
JOURNALS = {
    "Veterinary Quarterly": "https://www.tandfonline.com/action/showFeed?jc=tveq20&type=rss",
    "Journal of Veterinary Internal Medicine": "https://onlinelibrary.wiley.com/feed/19391676/most-recent",
    "Veterinary and Comparative Oncology": "https://onlinelibrary.wiley.com/feed/17485827/most-recent",
    "Journal of Feline Medicine and Surgery": "http://feeds.feedburner.com/Jfm-TheJournalOfFelineMedicineAndSurgery",
    "American Journal of Veterinary Research": "https://avmajournals.avma.org/rss/journal/ajvr",
    "Journal of Veterinary Medical Science": "https://www.jstage.jst.go.jp/browse/jvms/_rss/-char/en",
    "Open Veterinary Journal": "https://www.openveterinaryjournal.com/feed/",
    "Frontiers in Veterinary Science": "https://www.frontiersin.org/journals/veterinary-science/rss",
    "MDPI Animals": "https://www.mdpi.com/rss/journal/animals"
}
ARTICLE_LIMIT = 10
REQUEST_TIMEOUT = 15

# --- ここから下のプログラムは変更不要です ---

if hasattr(ssl, '_create_unverified_context'):
    ssl._create_default_https_context = ssl._create_unverified_context

def format_authors(authors):
    """著者情報をフォーマットする"""
    if not authors: 
        return "著者情報なし"
    
    try:
        author_names = []
        for author in authors:
            if isinstance(author, dict):
                name = author.get('name', '')
            elif isinstance(author, str):
                name = author
            else:
                name = str(author)
            
            if name:
                author_names.append(name)
        
        if len(author_names) > 3:
            return ', '.join(author_names[:3]) + ', et al.'
        return ', '.join(author_names)
    except Exception as e:
        print(f"著者情報の処理でエラー: {e}")
        return "著者情報なし"

def parse_date(entry):
    """エントリから日付を解析する"""
    try:
        # 'published_parsed' または 'updated_parsed' から日付を取得
        date_struct = entry.get('published_parsed') or entry.get('updated_parsed')
        if date_struct:
            # time.struct_timeを直接datetimeに変換
            from time import mktime
            timestamp = mktime(date_struct)
            return datetime.fromtimestamp(timestamp)
        
        # 文字列形式の日付も試してみる
        date_str = entry.get('published') or entry.get('updated')
        if date_str:
            return feedparser._parse_date(date_str)
        
        return None
    except Exception as e:
        print(f"日付解析エラー: {e}")
        return None

def fetch_feed_with_retry(url, max_retries=3):
    """フィードを取得する（リトライ機能付き）"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    for attempt in range(max_retries):
        try:
            print(f"フィード取得中: {url} (試行 {attempt + 1}/{max_retries})")
            response = requests.get(url, timeout=REQUEST_TIMEOUT, headers=headers)
            response.raise_for_status()
            
            # フィードを解析
            feed = feedparser.parse(response.content)
            
            # フィードが正常に解析されたかチェック
            if hasattr(feed, 'bozo') and feed.bozo:
                print(f"警告: フィードの解析に問題があります: {feed.get('bozo_exception', 'Unknown error')}")
            
            return feed
            
        except requests.exceptions.Timeout:
            print(f"タイムアウト (試行 {attempt + 1}/{max_retries})")
            if attempt == max_retries - 1:
                raise
        except requests.exceptions.RequestException as e:
            print(f"ネットワークエラー: {e} (試行 {attempt + 1}/{max_retries})")
            if attempt == max_retries - 1:
                raise
        except Exception as e:
            print(f"予期しないエラー: {e} (試行 {attempt + 1}/{max_retries})")
            if attempt == max_retries - 1:
                raise

def generate_html():
    """HTMLを生成する"""
    html_body = ""
    total_articles = 0
    
    for name, url in JOURNALS.items():
        print(f"\n処理中: {name}")
        journal_html = f"<h2><i class='fas fa-paw'></i> {name}</h2>\n<div class='article-list'>\n"
        
        try:
            feed = fetch_feed_with_retry(url)
            
            if not feed.entries:
                print(f"  新しい論文はありませんでした")
                journal_html += "<div class='article-card no-update'>新しい論文はありませんでした。</div>"
            else:
                print(f"  {len(feed.entries)}件の論文を取得")
                articles_added = 0
                
                # 最新のものから上限数だけ表示
                for entry in feed.entries[:ARTICLE_LIMIT]:
                    try:
                        title = entry.get('title', 'タイトルなし')
                        link = entry.get('link', '#')
                        
                        published_date_obj = parse_date(entry)
                        published_date_str = published_date_obj.strftime('%Y-%m-%d') if published_date_obj else "日付不明"
                        authors_str = format_authors(entry.get('authors'))

                        journal_html += f"""
                        <div class="article-card">
                            <h3><a href="{link}" target="_blank" rel="noopener noreferrer">{title}</a></h3>
                            <div class="metadata">
                                <span class="date"><i class="fas fa-calendar-alt"></i> {published_date_str}</span>
                                <span class="authors"><i class="fas fa-user-edit"></i> {authors_str}</span>
                            </div>
                        </div>
                        """
                        articles_added += 1
                        total_articles += 1
                        
                    except Exception as e:
                        print(f"  記事の処理でエラー: {e}")
                        continue
                
                print(f"  {articles_added}件の記事を追加")
                        
        except Exception as e:
            error_msg = f"フィード取得中にエラーが発生しました: {str(e)}"
            print(f"  エラー: {error_msg}")
            journal_html += f"<div class='article-card error'>{error_msg}</div>"
        
        journal_html += "</div>\n"
        html_body += journal_html

    # 日本時間で最終更新時刻を生成
    try:
        jst = pytz.timezone('Asia/Tokyo')
        last_updated_str = datetime.now(jst).strftime('%Y-%m-%d %H:%M:%S JST')
    except Exception as e:
        print(f"時刻取得エラー: {e}")
        last_updated_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    final_html = f"""
    <!DOCTYPE html><html lang="ja"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>最新の獣医学論文 🐾</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css">
    <style>
        :root {{ --bg-color: #f0f8ff; --card-bg-color: #ffffff; --header-color: #4682b4; --text-color: #333333; --link-color: #1e90ff; --meta-color: #5f9ea0; --border-color: #e0ffff; --shadow-color: rgba(0, 0, 0, 0.08); }}
        body {{ font-family: 'Helvetica Neue', 'Arial', 'Hiragino Sans', 'Meiryo', sans-serif; line-height: 1.7; margin: 0; padding: 20px; background-color: var(--bg-color); color: var(--text-color); }}
        .container {{ max-width: 900px; margin: auto; background: var(--card-bg-color); padding: 20px 30px; border-radius: 12px; box-shadow: 0 4px 12px var(--shadow-color); }}
        h1 {{ color: var(--header-color); border-bottom: 3px solid var(--border-color); padding-bottom: 15px; text-align: center; font-size: 2em; }}
        h2 {{ color: var(--header-color); margin-top: 40px; border-left: 6px solid var(--link-color); padding-left: 12px; font-size: 1.5em; }}
        .article-list {{ display: grid; gap: 15px; }}
        .article-card {{ background: #fafffe; border: 1px solid var(--border-color); padding: 20px; border-radius: 8px; transition: transform 0.2s, box-shadow 0.2s; }}
        .article-card:hover {{ transform: translateY(-3px); box-shadow: 0 6px 15px var(--shadow-color); }}
        .article-card h3 {{ margin-top: 0; margin-bottom: 12px; font-size: 1.1em; }}
        .article-card h3 a {{ color: var(--link-color); text-decoration: none; font-weight: 600; }}
        .article-card h3 a:hover {{ text-decoration: underline; }}
        .metadata {{ display: flex; flex-wrap: wrap; gap: 8px 20px; font-size: 0.9em; color: var(--meta-color); }}
        .metadata span i {{ margin-right: 6px; }}
        .no-update, .error {{ text-align: center; color: #888; padding: 20px; }}
        .update-time {{ text-align: right; color: #777; font-size: 0.85em; margin-top: 30px; }}
        .fas {{ color: var(--meta-color); }}
    </style></head><body><div class="container">
    <h1><i class="fas fa-book-medical"></i> 最新の獣医学論文</h1>{html_body}
    <p class="update-time">最終更新: {last_updated_str} (合計 {total_articles} 記事)</p>
    </div></body></html>
    """
    
    try:
        with open("index.html", "w", encoding="utf-8") as f:
            f.write(final_html)
        print(f"\nindex.htmlを生成しました。合計 {total_articles} 記事を処理しました。")
        return True
    except Exception as e:
        print(f"HTMLファイルの書き込みでエラー: {e}")
        return False

if __name__ == "__main__":
    try:
        print("獣医学論文取得スクリプトを開始します...")
        success = generate_html()
        if success:
            print("スクリプトが正常に完了しました。")
            sys.exit(0)
        else:
            print("スクリプトの実行中にエラーが発生しました。")
            sys.exit(1)
    except Exception as e:
        print(f"致命的なエラー: {e}")
        traceback.print_exc()
        sys.exit(1)
