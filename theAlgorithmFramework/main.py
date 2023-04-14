#region imports
from AlgorithmImports import *
#endregion
from AlphaModel import *

class VerticalTachyonRegulators(QCAlgorithm):

    def Initialize(self):
        self.SetStartDate(2020, 1, 1)
        self.SetEndDate(2021, 1, 1)
        self.SetCash(100000)

        # Universe selection
        self.month = 0
        self.num_coarse = 500

        self.UniverseSettings.Resolution = Resolution.Daily
        self.AddUniverse(self.CoarseSelectionFunction, self.FineSelectionFunction)
        
        # Alpha Model
        self.AddAlpha(FundamentalFactorAlphaModel())

        # Portfolio construction model
        self.SetPortfolioConstruction(EqualWeightingPortfolioConstructionModel(self.IsRebalanceDue))
        
        # Risk model
        self.SetRiskManagement(NullRiskManagementModel())

        # Execution model
        self.SetExecution(ImmediateExecutionModel())

    # Share the same rebalance function for Universe and PCM for clarity
    def IsRebalanceDue(self, time):
        # Rebalance on the first day of the Quarter
        if time.month == self.month or time.month not in [1, 4, 7, 10]:
            return None
            
        self.month = time.month
        return time

    def CoarseSelectionFunction(self, coarse):
        # If not time to rebalance, keep the same universe
        if not self.IsRebalanceDue(self.Time): 
            return Universe.Unchanged

        # Select only those with fundamental data and a sufficiently large price
        # Sort by top dollar volume: most liquid to least liquid
        selected = sorted([x for x in coarse if x.HasFundamentalData and x.Price > 5],
                            key = lambda x: x.DollarVolume, reverse=True)

        return [x.Symbol for x in selected[:self.num_coarse]]


    def FineSelectionFunction(self, fine):
        # Filter the fine data for equities that IPO'd more than 5 years ago in selected sectors
        
        sectors = [
            MorningstarSectorCode.FinancialServices,
            MorningstarSectorCode.RealEstate,
            MorningstarSectorCode.Healthcare,
            MorningstarSectorCode.Utilities,
            MorningstarSectorCode.Technology]
        
        filtered_fine = [x.Symbol for x in fine if x.SecurityReference.IPODate + timedelta(365*5) < self.Time
                                    and x.AssetClassification.MorningstarSectorCode in sectors
                                    and x.OperationRatios.ROE.Value > 0
                                    and x.OperationRatios.NetMargin.Value > 0
                                    and x.ValuationRatios.PERatio > 0]
                
        return filtered_fine