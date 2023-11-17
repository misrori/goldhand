import tempfile
import os
from tqdm import tqdm

def create_video(tickers, output_file, second_to_watch_a_plot = 5):
    t_folder = tempfile.TemporaryDirectory()
    print(f'Temporary directory created: {t_folder.name}')

    counter = 1
    for ticker in tqdm(tickers):
        #try:
        t = GoldHand(ticker)
        p = t.plotly_last_year(tw.get_plotly_title(ticker))
        p.update_layout(height=1080, width=1920)
        p.write_image(f"{t_folder.name}/{counter:03d}_{ticker}.png")
        counter +=1
    # except:
        #     print(f'\nerror {ticker}')

    os.system(f"ffmpeg -framerate 1/{second_to_watch_a_plot} -pattern_type glob -i '{t_folder.name}/*.png' -c:v libx264 -pix_fmt yuv420p {output_file}")

    print(f'Your file is at {output_file}')
    
