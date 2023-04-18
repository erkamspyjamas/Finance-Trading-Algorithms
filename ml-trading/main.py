#region imports
from AlgorithmImports import *
#endregion
from tensorflow.keras.models import Sequential
import json

class SmoothSkyBlueMosquito(QCAlgorithm):

    def Initialize(self):
        self.SetStartDate(2018, 1, 1)  # Set Start Date
        self.SetEndDate(2020, 1, 1)  # Set Start Date
        
        # Get model
        model_key = 'bitcoin_price_predictor'       
        if self.ObjectStore.ContainsKey(model_key):
            model_str = self.ObjectStore.Read(model_key)
            config = json.loads(model_str)['config']
            self.model = Sequential.from_config(config)

        self.SetBrokerageModel(BrokerageName.Bitfinex, AccountType.Margin)  # Crypto brokerage
        self.SetCash(100000)  # Set Strategy Cash
        self.symbol = self.AddCrypto("BTCUSD", Resolution.Daily).Symbol
        self.SetBenchmark(self.symbol)


    def OnData(self, data):
        if self.GetPrediction() == "Up":
            self.SetHoldings(self.symbol, 1)
        else:
            self.SetHoldings(self.symbol, -0.5)
    
    def GetPrediction(self):
        # instead of history requests, use rolling window for more efficiency
        df = self.History(self.symbol, 40).loc[self.symbol]
        df_change = df[["close", "open", "high", "low", "volume"]].pct_change().dropna()
        model_input = []
        # turn history into right input format for model
        for index, row in df_change.tail(30).iterrows():
            model_input.append(np.array(row))
        model_input = np.array([model_input])
        if round(self.model.predict(model_input)[0][0]) == 1:
            return "Up"
        else:
            return "Down"
