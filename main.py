import yfinance as yf
import pandas as pd
import mplfinance as mpf
import customtkinter as ctk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class StockApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title('Stock Market Supply and Demand Analysis Tool')
        self.geometry('1200x800')
        self.configure(bg='#000000')
        self.set_icon()

        self.frame = ctk.CTkFrame(self, fg_color="#1e1e1e")
        self.frame.pack(pady=20, padx=20, fill='x')

        self.ticker_label = ctk.CTkLabel(self.frame, text="Ticker Symbol:", text_color="green")
        self.ticker_label.grid(row=0, column=0, padx=10)

        self.ticker_entry = ctk.CTkEntry(self.frame, fg_color="black", text_color="green")
        self.ticker_entry.grid(row=0, column=1, padx=10)

        self.plot_button = ctk.CTkButton(
            self.frame, text='Show Charts', 
            command=self.plot_stock, 
            fg_color="green", 
            text_color="black", 
            hover_color="#00FF00"
            )
        self.plot_button.grid(row=0, column=2, padx=10)

        self.notebook = ctk.CTkTabview(self, fg_color="#1e1e1e", bg_color="black")
        self.notebook.pack(expand=1, fill='both', padx=10, pady=10)

        self.frames = {}
        self.intervals = {
            '5m': '60d',
            '15m': '60d',
            '30m': '60d',
            '60m': '60d',
            '1d': '60d'
        }

        for interval in self.intervals:
            self.notebook.add(interval)
            frame = ctk.CTkFrame(self.notebook.tab(interval), fg_color="#1e1e1e")
            frame.pack(fill='both', expand=True)
            self.frames[interval] = frame

    def set_icon(self):
        try:
            self.iconbitmap(default='dollar_icon.ico')
        except Exception as e:
            print(f"Error setting icon: {e}")

    def fetch_stock_data(self, ticker, interval='5m'):
        period = self.intervals[interval]
        stock = yf.Ticker(ticker)
        data = stock.history(interval=interval, period=period)
        return data

    def identify_zones(self, data, threshold=0.02):
        zones = []
        data['PriceChange'] = data['Close'].pct_change()

        for i in range(1, len(data)-1):
            if data['Volume'].iloc[i] > data['Volume'].mean() and abs(data['PriceChange'].iloc[i]) > threshold:
                if data['Close'].iloc[i] > data['Close'].iloc[i-1] and data['Close'].iloc[i] > data['Close'].iloc[i+1]:
                    zones.append((data.index[i], 'Supply', data['Close'].iloc[i]))
                elif data['Close'].iloc[i] < data['Close'].iloc[i-1] and data['Close'].iloc[i] < data['Close'].iloc[i+1]:
                    zones.append((data.index[i], 'Demand', data['Close'].iloc[i]))

        return zones

    def plot_zones(self, data, zones, ticker, interval):
        # 78 bars for 1 day in 5m, 15m, 30m, 60m intervals
        # 30 days for 1d interval
        if interval != '1d':
            data = data.tail(78)  
        else:
            data = data.tail(30)  

        # Copy data to avoid SettingWithCopyWarning
        data = data.copy()
        data['Color'] = ['green' if close >= open else 'red' for close, open in zip(data['Close'], data['Open'])]

        current_price = data['Close'].iloc[-1]
        valid_zones = [zone for zone in zones if (zone[1] == 'Supply' and current_price < zone[2]) or (zone[1] == 'Demand' and current_price > zone[2])]

        mc = mpf.make_marketcolors(up='green', down='red', wick={'up':'green', 'down':'red'}, volume={'up':'green', 'down':'red'})
        style = mpf.make_mpf_style(
            marketcolors=mc, 
            base_mpf_style='nightclouds', 
            rc={
                'axes.facecolor': 'black', 
                'axes.edgecolor': 'white', 
                'axes.labelcolor': 'white', 
                'xtick.color': 'white', 
                'ytick.color': 'white'
                }
            )

        ap = []
        for date, zone_type, price in valid_zones:
            color = 'red' if zone_type == 'Supply' else 'green'
            ap.append(mpf.make_addplot([price]*len(data), type='line', color=color, linestyle='--', width=1))

        ylim_min = data['Low'].min() * 0.99
        ylim_max = data['High'].max() * 1.01

        fig, ax = mpf.plot(
            data,
            type='candle',
            addplot=ap,
            title=f'{ticker} Price Chart ({interval})',
            ylabel='',
            volume=True,
            ylabel_lower='',
            figscale=2.0,
            style=style,
            returnfig=True,
            ylim=(ylim_min, ylim_max),
            datetime_format='%d/%m' if interval == '1d' else '%H:%M'
        )

        fig.subplots_adjust(left=0, right=1, top=0.9, bottom=0.1)

        return fig

    def plot_in_frame(self, frame, fig):
        for widget in frame.winfo_children():
            widget.destroy()

        canvas = FigureCanvasTkAgg(fig, master=frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill='both', expand=True)

    def plot_stock(self):
        ticker = self.ticker_entry.get().upper().strip()

        for interval in self.intervals:
            try:
                data = self.fetch_stock_data(ticker, interval=interval)
                if data.empty:
                    raise ValueError("No data found")
                zones = self.identify_zones(data)
                fig = self.plot_zones(data, zones, ticker, interval)
                self.plot_in_frame(self.frames[interval], fig)
            except Exception as e:
                print(f"Error fetching data for {ticker} with interval {interval}: {e}")

if __name__ == '__main__':
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("green")
    app = StockApp()
    app.mainloop()
