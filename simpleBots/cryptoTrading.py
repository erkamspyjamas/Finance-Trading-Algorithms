#region imports
from AlgorithmImports import *
#endregion
class CreativeRedHornet(QCAlgorithm):

    def Initialize(self):
        self.SetStartDate(2019, 1, 1)
        self.SetEndDate(2021, 1, 1)
        self.SetCash(100000)
        
        self.Settings.FreePortfolioValuePercentage = 0.05
        self.positionSizeUSD = 5000
        self.rsiEntryThreshold = 70 # enter position if rsi rises above this threshold
        self.rsiExitThreshold = 60 # exit position if rsi drops below this threshold
        self.minimumVolume = 1000000 # filters out symbols with 30 day avg daily dollar volume less than this 
        
        # add data for all tickers
        universe = ['BTCUSD', 'LTCUSD', 'ETHUSD', 'ETCUSD', 'RRTUSD', 'ZECUSD', 'XMRUSD', 'XRPUSD', 'EOSUSD', 'SANUSD', 'OMGUSD', 'NEOUSD', 'ETPUSD', 'BTGUSD', 'SNTUSD', 'BATUSD', 'FUNUSD', 'ZRXUSD', 'TRXUSD', 'REQUSD', 'LRCUSD', 'WAXUSD', 'DAIUSD', 'BFTUSD', 'ODEUSD', 'ANTUSD', 'XLMUSD', 'XVGUSD', 'MKRUSD', 'KNCUSD', 'LYMUSD', 'UTKUSD', 'VEEUSD', 'ESSUSD', 'IQXUSD', 'ZILUSD', 'BNTUSD', 'XRAUSD', 'VETUSD', 'GOTUSD', 'XTZUSD', 'MLNUSD', 'PNKUSD', 'DGBUSD', 'BSVUSD', 'ENJUSD', 'PAXUSD']
        self.pairs = [ Pair(self, ticker, self.minimumVolume) for ticker in universe ]
        self.SetBenchmark("BTCUSD") 
        self.SetWarmup(30)
 
    def OnData(self, data):
        
        for pair in self.pairs: 
            if not pair.rsi.IsReady:
                return
            
            symbol = pair.symbol
            rsi = pair.rsi.Current.Value 
            
            if self.Portfolio[symbol].Invested:
                if not pair.Investable():
                    self.Liquidate(symbol, "Not enough volume")
                elif rsi < self.rsiExitThreshold:
                    self.Liquidate(symbol, "RSI below threshold")
                continue
            
            if not pair.Investable():
                continue
            
            if rsi > self.rsiEntryThreshold and self.Portfolio.MarginRemaining > self.positionSizeUSD:
                self.Buy(symbol, self.positionSizeUSD / self.Securities[symbol].Price)

class Pair:
    def __init__(self, algorithm, ticker, minimumVolume): 
        self.symbol = algorithm.AddCrypto(ticker, Resolution.Daily, Market.Bitfinex).Symbol
        self.rsi    = algorithm.RSI(self.symbol, 14,  MovingAverageType.Simple, Resolution.Daily)
        self.volume = IndicatorExtensions.Times(algorithm.SMA(self.symbol, 30, Resolution.Daily, Field.Volume), 
                                                algorithm.SMA(self.symbol, 30, Resolution.Daily, Field.Close))
        self.minimumVolume = minimumVolume
    
    def Investable(self):
        return (self.volume.Current.Value > self.minimumVolume)