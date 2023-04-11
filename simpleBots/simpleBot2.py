#region imports
from AlgorithmImports import *
#endregion
class TrailingStopLoss(QCAlgorithm):
    
    def Initialize(self):
        self.SetStartDate(2018, 1, 1)
        self.SetEndDate(2021, 1, 1)
        self.SetCash(100000)
        self.qqq = self.AddEquity("QQQ", Resolution.Hour).Symbol
        
        self.entryTicket = None
        self.stopMarketTicket = None
        self.entryTime = datetime.min
        self.stopMarketOrderFillTime = datetime.min
        self.highestPrice = 0

    def OnData(self, data):
        
        # wait 30 days after last exit
        if (self.Time - self.stopMarketOrderFillTime).days < 30:
            return
        
        price = self.Securities[self.qqq].Price
        
        # send entry limit order
        if not self.Portfolio.Invested and not self.Transactions.GetOpenOrders(self.qqq):
            quantity = self.CalculateOrderQuantity(self.qqq, 0.9)
            self.entryTicket = self.LimitOrder(self.qqq, quantity, price, "Entry Order")
            self.entryTime = self.Time
        
        # move limit price if not filled after 1 day
        if (self.Time - self.entryTime).days > 1 and self.entryTicket.Status != OrderStatus.Filled:
            self.entryTime = self.Time
            updateFields = UpdateOrderFields()
            updateFields.LimitPrice = price
            self.entryTicket.Update(updateFields)
        
        if self.stopMarketTicket is not None and self.Portfolio.Invested:
            # move up trailing stop price
            if price > self.highestPrice:
                self.highestPrice = price
                updateFields = UpdateOrderFields()
                updateFields.StopPrice = price * 0.95
                self.stopMarketTicket.Update(updateFields)
                #self.Debug(updateFields.StopPrice)

    def OnOrderEvent(self, orderEvent):
        
        if orderEvent.Status != OrderStatus.Filled:
            return
        
        # send stop loss order if entry limit order is filled
        if self.entryTicket is not None and self.entryTicket.OrderId == orderEvent.OrderId:
            self.stopMarketTicket = self.StopMarketOrder(self.qqq, -self.entryTicket.Quantity, 0.95 * self.entryTicket.AverageFillPrice)
        
        # save fill time of stop loss order (and reset highestPrice)
        if self.stopMarketTicket is not None and self.stopMarketTicket.OrderId == orderEvent.OrderId: 
            self.stopMarketOrderFillTime = self.Time
            self.highestPrice = 0