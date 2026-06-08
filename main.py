from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt
from googleapiclient.discovery import build
import re


def strip_emojis(text):
    return re.sub(r'[^\x00-\x7F]+', '', text)

# Set up the YouTube Data API client
def setup_youtube_client(api_key):
    return build('youtube', 'v3', developerKey=api_key)

def get_video_ids(youtube, channel_id, start_date, end_date):
    # Get the uploads playlist ID from the channel's content details
    request = youtube.channels().list(
        part='contentDetails',
        id=channel_id
    )
    response = request.execute()
    uploads_playlist_id = response['items'][0]['contentDetails']['relatedPlaylists']['uploads']

    video_ids = []
    next_page_token = None

    while True:
        request = youtube.playlistItems().list(
            part='snippet',
            playlistId=uploads_playlist_id,
            maxResults=50,
            pageToken=next_page_token
        )
        response = request.execute()

        for item in response['items']:
            published_at_str = item['snippet']['publishedAt']
            
            if '.' in published_at_str:
                published_at = datetime.strptime(published_at_str, '%Y-%m-%dT%H:%M:%S.%fZ')
            else:
                published_at = datetime.strptime(published_at_str, '%Y-%m-%dT%H:%M:%SZ')

            if start_date <= published_at < end_date:
                video_ids.append(item['snippet']['resourceId']['videoId'])

        next_page_token = response.get('nextPageToken')
        if not next_page_token:
            break

    return video_ids

def get_video_stats(youtube, video_ids):
    stats = []

    for i in range(0, len(video_ids), 50): # API allows up to 50 IDs per request
        request = youtube.videos().list(
            part='snippet,statistics',
            id=','.join(video_ids[i:i+50])
        )
        response = request.execute()

        for item in response['items']:
            published_at_str = item['snippet']['publishedAt']
            
            if '.' in published_at_str:
                published_at = datetime.strptime(published_at_str, '%Y-%m-%dT%H:%M:%S.%fZ')
            else:
                published_at = datetime.strptime(published_at_str, '%Y-%m-%dT%H:%M:%SZ')

            stats.append({
                'title': strip_emojis(item['snippet']['title']),
                'views': int(item['statistics'].get('viewCount', 0)),
                'day': published_at.strftime('%A'),
                'date': published_at.strftime('%Y-%m-%d')
            })

    return stats

def calculate_average_views(df):
    total_views = df['views'].sum()
    num_videos = len(df)
    average_views = total_views / num_videos if num_videos > 0 else 0
    return average_views

def find_best_worst_performing_videos(df):
    best_video = df.loc[df['views'].idxmax()]
    worst_video = df.loc[df['views'].idxmin()]
    return best_video, worst_video

def find_best_days(df):
    day_counts = df.groupby('day')['views'].sum()
    best_day = day_counts.idxmax()
    return best_day, day_counts[best_day]

def track_view_growth_over_time(df):
    df['date'] = pd.to_datetime(df['date'])
    df.sort_values(by='date', inplace=True)
    growth_rate = (df['views'].iloc[-1] - df['views'].iloc[0]) / len(df)
    return growth_rate

def get_top_video_per_month(df):
    df['month'] = pd.to_datetime(df['date']).dt.to_period('M')
    return df.loc[df.groupby('month')['views'].idxmax()][['month', 'title', 'views']]

def get_total_views_per_month(df):
    df['month'] = pd.to_datetime(df['date']).dt.to_period('M')
    return df.groupby('month')['views'].sum()

def generate_report(average_views, best_video, worst_video, best_day, best_day_views, growth_rate, top_per_month, total_per_month):
    with open('report.txt', 'w') as f:
        f.write(f"Average views per video: {average_views}\n")
        f.write(f"Best performing video:\n{best_video.to_string()}\n")
        f.write(f"Worst performing video:\n{worst_video.to_string()}\n")
        f.write(f"Day with the most views: {best_day} ({best_day_views} views)\n")
        f.write(f"Growth rate over time: {growth_rate:.2f} views per day\n\n")
        f.write("Top video per month:\n")
        f.write(top_per_month.to_string())
        f.write("\n\nTotal views per month:\n")
        f.write(total_per_month.to_string())

def plot_view_growth_over_time(df):
    df['date'] = pd.to_datetime(df['date'])
    df.sort_values(by='date', inplace=True)
    
    plt.figure(figsize=(14, 6))
    plt.plot(range(len(df)), df['views'], marker='o')
    plt.title('Views per Video (sorted by date)')
    plt.xlabel('Video Index')
    plt.ylabel('Views')

    # Format y-axis labels
    def format_yaxis(y, pos):
        if y >= 1000000:
            return f'{y/1000000:.1f}M'
        elif y >= 1000:
            return f'{y/1000:.1f}K'
        else:
            return str(int(y))
    
    plt.gca().yaxis.set_major_formatter(plt.FuncFormatter(format_yaxis))

    plt.grid(True)
    plt.tight_layout()
    plt.savefig('view_growth_line.png')

def plot_monthly_views(total_per_month):
    months = [str(m) for m in total_per_month.index]
    plt.figure(figsize=(10, 5))
    plt.bar(months, total_per_month.values)
    plt.title('Total Views per Month')
    plt.xlabel('Month')
    plt.ylabel('Views')

    # Format y-axis labels
    def format_yaxis(y, pos):
        if y >= 1000000:
            return f'{y/1000000:.1f}M'
        elif y >= 1000:
            return f'{y/1000:.1f}K'
        else:
            return str(int(y))
    
    plt.gca().yaxis.set_major_formatter(plt.FuncFormatter(format_yaxis))

    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig('monthly_views.png')

def main():
    api_key = input("Enter YouTube API Key: ")
    youtube = setup_youtube_client(api_key)
    channel_id = input("Enter YouTube Channel ID: ")
    start_date_str = input("Enter Start Date (MM/DD/YY): ")
    end_date_str = input("Enter End Date (MM/DD/YY): ")
    from datetime import timedelta
    start_date = datetime.strptime(start_date_str, '%m/%d/%y')
    end_date = datetime.strptime(end_date_str, '%m/%d/%y') + timedelta(days=1)
    video_ids = get_video_ids(youtube, channel_id, start_date, end_date)
    stats = get_video_stats(youtube, video_ids)
    df = pd.DataFrame(stats)
    df.to_csv('youtube_stats.csv', index=False)
    average_views = calculate_average_views(df)
    best_video, worst_video = find_best_worst_performing_videos(df)
    best_day, best_day_views = find_best_days(df)
    growth_rate = track_view_growth_over_time(df)
    top_per_month = get_top_video_per_month(df)
    total_per_month = get_total_views_per_month(df)
    generate_report(average_views, best_video, worst_video, best_day, best_day_views, growth_rate, top_per_month, total_per_month)
    plot_view_growth_over_time(df)
    plot_monthly_views(total_per_month)

if __name__ == '__main__':
    main()
