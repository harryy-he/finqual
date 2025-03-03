from node_tree import Node

"""
Assets
"""

a = Node("Assets", attribute="debit")

"""
Liabilities
"""
l = Node("Liabilities", attribute="credit")

"""
Current Assets
"""
ca1 = Node("CurrentAssets", attribute="debit", parent=a)
ca = Node("AssetsCurrent", attribute="debit", parent=ca1)

# Level 1
ca1_1 = Node("CashCashEquivalentsAndShortTermInvestments", attribute="debit", parent=ca)
ca1_1_1 = Node("CashAndCashEquivalents", attribute="debit", parent=ca1_1)
ca1_2 = Node("NetInvestmentInLeaseCurrent", attribute="debit", parent=ca)
ca1_3 = Node("RestrictedCashAndInvestmentsCurrent", attribute="debit", parent=ca)

ca1_4 = Node("ReceivablesNetCurrent", attribute="debit", parent=ca)
ca1_35 = Node("AccountsAndOtherReceivablesNetCurrent", attribute="debit", parent=ca1_4)
ca1_35_1 = Node("CurrentReceivablesFromContractsWithCustomers", attribute="debit", parent=ca1_35) #IFRS
ca1_35_2 = Node("TradeAndOtherCurrentReceivables", attribute="debit", parent=ca1_35_1) #IFRS

ca1_5 = Node("InventoryNetOfAllowancesCustomerAdvancesAndProgressBillings", attribute="debit", parent=ca)
ca1_6 = Node("PrepaidExpenseCurrent", attribute="debit", parent=ca)
ca1_7 = Node("ContractWithCustomerAssetNetCurrent", attribute="debit", parent=ca)
ca1_8 = Node("CapitalizedContractCostNetCurrent", attribute="debit", parent=ca)
ca1_9 = Node("DeferredCostsCurrent", attribute="debit", parent=ca)
ca1_10 = Node("DerivativeInstrumentsAndHedges", attribute="debit", parent=ca)
ca1_11 = Node("RegulatoryAssetsCurrent", attribute="debit", parent=ca)
ca1_12 = Node("FundsHeldForClients", attribute="debit", parent=ca)
ca1_13 = Node("DeferredRentAssetNetCurrent", attribute="debit", parent=ca)
ca1_14 = Node("AssetsHeldInTrustCurrent", attribute="debit", parent=ca)
ca1_15 = Node("AdvancesOnInventoryPurchases", attribute="debit", parent=ca)
ca1_16 = Node("FinancingReceivableAccruedInterestAfterAllowanceForCreditLoss", attribute="debit", parent=ca)
ca1_17 = Node("AccountsReceivableNoncurrentAccruedInterestAfterAllowanceForCreditLoss", attribute="debit", parent=ca)
ca1_18 = Node("DebtSecuritiesHeldToMaturityAccruedInterestAfterAllowanceForCreditLoss", attribute="debit", parent=ca)
ca1_19 = Node("NetInvestmentInLeaseAccruedInterestAfterAllowanceForCreditLoss", attribute="debit", parent=ca)
ca1_20 = Node("SalesTypeLeaseNetInvestmentInLeaseAccruedInterestAfterAllowanceForCreditLoss", attribute="debit", parent=ca)
ca1_21 = Node("DirectFinancingLeaseNetInvestmentInLeaseAccruedInterestAfterAllowanceForCreditLoss", attribute="debit", parent=ca)
ca1_22 = Node("FinancialAssetAmortizedCostAccruedInterestAfterAllowanceForCreditLoss", attribute="debit", parent=ca)
ca1_23 = Node("DebtSecuritiesAvailableForSaleAccruedInterestAfterAllowanceForCreditLossCurrent", attribute="debit", parent=ca)
ca1_24 = Node("FinancingReceivableExcludingAccruedInterestAfterAllowanceForCreditLossCurrent", attribute="debit", parent=ca)
ca1_25 = Node("DebtSecuritiesHeldToMaturityExcludingAccruedInterestAfterAllowanceForCreditLossCurrent", attribute="debit", parent=ca)
ca1_26 = Node("NetInvestmentInLeaseExcludingAccruedInterestAfterAllowanceForCreditLossCurrent", attribute="debit", parent=ca)
ca1_27 = Node("DebtSecuritiesAvailableForSaleAmortizedCostExcludingAccruedInterestAfterAllowanceForCreditLossCurrent", attribute="debit", parent=ca)
ca1_28 = Node("AdvanceRoyaltiesCurrent", attribute="debit", parent=ca)
ca1_29 = Node("AssetsOfDisposalGroupIncludingDiscontinuedOperationCurrent", attribute="debit", parent=ca)
ca1_30 = Node("AssetsHeldForSaleNotPartOfDisposalGroupCurrent", attribute="debit", parent=ca)
ca1_31 = Node("DepositsAssetsCurrent", attribute="debit", parent=ca)
ca1_32 = Node("IntangibleAssetsCurrent", attribute="debit", parent=ca)
ca1_33 = Node("BusinessCombinationContingentConsiderationAssetCurrent", attribute="debit", parent=ca)
ca1_34 = Node("OtherAssetsCurrent", attribute="debit", parent=ca)

# Level 2
ca2_1 = Node("CashAndCashEquivalentsAtCarryingValue", attribute="debit", parent=ca1_1_1)
ca2_1_1 = Node("Cash", attribute="debit", parent=ca2_1) # IFRS
ca2_2 = Node("ShortTermInvestments", attribute="debit", parent=ca1_1_1)
ca2_2_1 = Node("CashEquivalents", attribute="debit", parent=ca2_2) #IFRS

ca2_3 = Node("RestrictedCashAndCashEquivalentsAtCarryingValue", attribute="debit", parent=ca1_3)
ca2_4 = Node("RestrictedInvestmentsCurrent", attribute="debit", parent=ca1_3)
ca2_5 = Node("OtherRestrictedAssetsCurrent", attribute="debit", parent=ca1_3)

ca2_6 = Node("AccountsNotesAndLoansReceivableNetCurrent", attribute="debit", parent=ca1_35_2)
ca2_7 = Node("NontradeReceivablesCurrent", attribute="debit", parent=ca1_35_2)
ca2_8 = Node("UnbilledReceivablesCurrent", attribute="debit", parent=ca1_35_2)
ca2_9 = Node("ReceivablesLongTermContractsOrPrograms", attribute="debit", parent=ca1_35_2)
ca2_10 = Node("AccountsReceivableFromSecuritization", attribute="debit", parent=ca1_35_2)
ca2_11 = Node("OtherReceivablesNetCurrent", attribute="debit", parent=ca1_35_2)
ca2_42 = Node("CurrentTradeReceivables", attribute="debit", parent=ca1_35_2) #IFRS
ca2_43 = Node("CurrentPrepayments", attribute="debit", parent=ca1_35_2) #IFRS
ca2_44 = Node("OtherCurrentReceivables", attribute="debit", parent=ca1_35_2) #IFRS

ca2_12 = Node("InventoryNet", attribute="debit", parent=ca1_5)
ca2_12_1 = Node("Inventories", attribute="debit", parent=ca2_12) #IFRS
ca2_13 = Node("ProgressPaymentsNettedAgainstInventoryForLongTermContractsOrPrograms", attribute="debit", parent=ca1_5)

ca2_14 = Node("FinancingReceivableExcludingAccruedInterestBeforeAllowanceForCreditLossCurrent", attribute="debit",
              parent=ca1_24)
ca2_15 = Node("FinancingReceivableAllowanceForCreditLossExcludingAccruedInterestCurrent", attribute="credit",
              parent=ca1_24)

ca2_16 = Node("DebtSecuritiesHeldToMaturityExcludingAccruedInterestBeforeAllowanceForCreditLossCurrent",
              attribute="debit", parent=ca1_25)
ca2_17 = Node("DebtSecuritiesHeldToMaturityAllowanceForCreditLossExcludingAccruedInterestCurrent", attribute="credit",
              parent=ca1_25)

ca2_18 = Node("NetInvestmentInLeaseExcludingAccruedInterestBeforeAllowanceForCreditLossCurrent", attribute="debit",
              parent=ca1_26)
ca2_19 = Node("NetInvestmentInLeaseAllowanceForCreditLossExcludingAccruedInterestCurrent", attribute="credit",
              parent=ca1_26)

ca2_20 = Node("DebtSecuritiesAvailableForSaleAmortizedCostExcludingAccruedInterestBeforeAllowanceForCreditLossCurrent", attribute="debit", parent=ca1_27)
ca2_21 = Node("DebtSecuritiesAvailableForSaleAmortizedCostAllowanceForCreditLossExcludingAccruedInterestCurrent", attribute="credit", parent=ca1_27)

ca2_22 = Node("DisposalGroupIncludingDiscontinuedOperationCashAndCashEquivalents", attribute="debit", parent=ca1_29)
ca2_23 = Node("DisposalGroupIncludingDiscontinuedOperationInventoryCurrent", attribute="debit", parent=ca1_29)
ca2_24 = Node("DisposalGroupIncludingDiscontinuedOperationOtherCurrentAssets", attribute="debit", parent=ca1_29)
ca2_25 = Node("DisposalGroupIncludingDiscontinuedOperationAccountsNotesAndLoansReceivableNet", attribute="debit",
              parent=ca1_29)
ca2_26 = Node("DisposalGroupIncludingDiscontinuedOperationGoodwillCurrent", attribute="debit", parent=ca1_29)
ca2_27 = Node("DisposalGroupIncludingDiscontinuedOperationPropertyPlantAndEquipmentCurrent", attribute="debit",
              parent=ca1_29)
ca2_28 = Node("DisposalGroupIncludingDiscontinuedOperationIntangibleAssetsCurrent", attribute="debit", parent=ca1_29)

ca2_29 = Node("TradeAndLoansReceivablesHeldForSaleNetNotPartOfDisposalGroup", attribute="debit", parent=ca1_30)
ca2_30 = Node("AssetsHeldForSaleNotPartOfDisposalGroupCurrentOther", attribute="debit", parent=ca1_30)

ca2_31 = Node("DerivativeAssetsCurrent", attribute="debit", parent=ca1_10)
ca2_32 = Node("HedgingAssetsCurrent", attribute="debit", parent=ca1_10)
ca2_33 = Node("CommodityContractAssetCurrent", attribute="debit", parent=ca1_10)
ca2_34 = Node("EnergyMarketingContractsAssetsCurrent", attribute="debit", parent=ca1_10)

ca2_35 = Node("DeferredCostsLeasingNetCurrent", attribute="debit", parent=ca1_9)
ca2_36 = Node("DeferredFuelCost", attribute="debit", parent=ca1_9)
ca2_37 = Node("DeferredStormAndPropertyReserveDeficiencyCurrent", attribute="debit", parent=ca1_9)
ca2_38 = Node("OtherDeferredCostsNet", attribute="debit", parent=ca1_9)
ca2_39 = Node("DeferredOfferingCosts", attribute="debit", parent=ca1_9)

ca2_40 = Node("PrepaidInsurance", attribute="debit", parent=ca1_6)
ca2_41 = Node("PrepaidRent", attribute="debit", parent=ca1_6)
ca2_42_1 = Node("PrepaidAdvertising", attribute="debit", parent=ca1_6)
ca2_43_2 = Node("PrepaidRoyalties", attribute="debit", parent=ca1_6)
ca2_44_3 = Node("Supplies", attribute="debit", parent=ca1_6)
ca2_45 = Node("PrepaidInterest", attribute="debit", parent=ca1_6)
ca2_46 = Node("PrepaidTaxes", attribute="debit", parent=ca1_6)
ca2_47 = Node("OtherPrepaidExpenseCurrent", attribute="debit", parent=ca1_6)

# Level 3
ca3_1 = Node("CashAndDueFromBanks", attribute="debit", parent=ca2_1_1)
ca3_1_1 = Node("BalancesWithBanks", attribute="debit", parent=ca3_1) #IFRS
ca3_2 = Node("InterestBearingDepositsInBanks", attribute="debit", parent=ca2_1_1)
ca3_3 = Node("CashEquivalentsAtCarryingValue", attribute="debit", parent=ca2_1_1)

ca3_4 = Node("EquitySecuritiesFvNi", attribute="debit", parent=ca2_2_1)
ca3_5 = Node("DebtSecuritiesCurrent", attribute="debit", parent=ca2_2_1)
ca3_6 = Node("MarketableSecuritiesCurrent", attribute="debit", parent=ca2_2_1)
ca3_7 = Node("OtherShortTermInvestments", attribute="debit", parent=ca2_2_1)

ca3_8 = Node("RestrictedCashCurrent", attribute="debit", parent=ca2_3)
ca3_9 = Node("RestrictedCashEquivalentsCurrent", attribute="debit", parent=ca2_3)

ca3_10 = Node("InventoryGross", attribute="debit", parent=ca2_12_1)
ca3_11 = Node("InventoryAdjustments", attribute="credit", parent=ca2_12_1)

ca3_12 = Node("AccountsReceivableNetCurrent", attribute="debit", parent=ca2_6)
ca3_13 = Node("NotesAndLoansReceivableNetCurrent", attribute="credit", parent=ca2_6)

ca3_14 = Node("AllowanceForDoubtfulOtherReceivablesCurrent", attribute="debit", parent=ca2_11)
ca3_15 = Node("OtherReceivablesGrossCurrent", attribute="credit", parent=ca2_11)

ca3_16 = Node("DeferredGasCost", attribute="debit", parent=ca2_30)

ca3_17 = Node("OtherDeferredCostsGross", attribute="debit", parent=ca2_32)
ca3_18 = Node("AccumulatedAmortizationOfOtherDeferredCosts", attribute="credit", parent=ca2_32)

# Level 4
ca4_1 = Node("Cash", attribute="debit", parent=ca3_1_1)
ca4_2 = Node("DueFromBanks", attribute="debit", parent=ca3_1_1)

ca4_3 = Node("TradingSecuritiesDebt", attribute="debit", parent=ca3_5)
ca4_4 = Node("AvailableForSaleSecuritiesDebtSecuritiesCurrent", attribute="debit", parent=ca3_5)
ca4_5 = Node("DebtSecuritiesHeldToMaturityAmortizedCostAfterAllowanceForCreditLossCurrent", attribute="debit",
             parent=ca3_5)

ca4_6 = Node("AccountsReceivableGrossCurrent", attribute="debit", parent=ca3_12)
ca4_7 = Node("AllowanceForDoubtfulAccountsReceivableCurrent", attribute="credit", parent=ca3_12)

ca4_8 = Node("AirlineRelatedInventory", attribute="debit", parent=ca3_10)
ca4_9 = Node("RetailRelatedInventory", attribute="debit", parent=ca3_10)
ca4_10 = Node("EnergyRelatedInventory", attribute="debit", parent=ca3_10)
ca4_11 = Node("AgriculturalRelatedInventory", attribute="debit", parent=ca3_10)
ca4_12 = Node("PublicUtilitiesInventory", attribute="debit", parent=ca3_10)

ca4_13 = Node("InventoryValuationReserves", attribute="credit", parent=ca3_11)
ca4_14 = Node("InventoryLIFOReserve", attribute="credit", parent=ca3_11)

ca4_15 = Node("AssetBackedSecuritiesAtCarryingValue", attribute="debit", parent=ca3_3)
ca4_16 = Node("CertificatesOfDepositAtCarryingValue", attribute="debit", parent=ca3_3)
ca4_17 = Node("CommercialPaperAtCarryingValue", attribute="debit", parent=ca3_3)
ca4_18 = Node("CreditAndDebitCardReceivablesAtCarryingValue", attribute="debit", parent=ca3_3)
ca4_19 = Node("MoneyMarketFundsAtCarryingValue", attribute="debit", parent=ca3_3)
ca4_20 = Node("MunicipalDebtSecuritiesAtCarryingValue", attribute="debit", parent=ca3_3)
ca4_21 = Node("TimeDepositsAtCarryingValue", attribute="debit", parent=ca3_3)
ca4_22 = Node("USGovernmentSecuritiesAtCarryingValue", attribute="debit", parent=ca3_3)
ca4_23 = Node("USGovernmentAgenciesSecuritiesAtCarryingValue", attribute="debit", parent=ca3_3)
ca4_24 = Node("OtherCashEquivalentsAtCarryingValue", attribute="debit", parent=ca3_3)

# Level 5
ca5_1 = Node("HeldToMaturitySecuritiesCurrent", attribute="debit", parent=ca4_5)
ca5_2 = Node("DebtSecuritiesHeldToMaturityAllowanceForCreditLossCurrent", attribute="credit", parent=ca4_5)

ca5_3 = Node("AirlineRelatedInventoryAircraftFuel", attribute="debit", parent=ca4_8)
ca5_4 = Node("AirlineRelatedInventoryAircraftParts", attribute="debit", parent=ca4_8)

ca5_5 = Node("RetailRelatedInventoryMerchandise", attribute="debit", parent=ca4_9)
ca5_6 = Node("RetailRelatedInventoryPackagingAndOtherSupplies", attribute="debit", parent=ca4_9)

ca5_7 = Node("EnergyRelatedInventoryPetroleum", attribute="debit", parent=ca4_10)
ca5_8 = Node("EnergyRelatedInventoryNaturalGasLiquids", attribute="debit", parent=ca4_10)
ca5_9 = Node("EnergyRelatedInventoryNaturalGasInStorage", attribute="debit", parent=ca4_10)
ca5_10 = Node("EnergyRelatedInventoryGasStoredUnderground", attribute="debit", parent=ca4_10)
ca5_11 = Node("EnergyRelatedInventoryPropaneGas", attribute="debit", parent=ca4_10)
ca5_12 = Node("EnergyRelatedInventoryCoal", attribute="debit", parent=ca4_10)
ca5_13 = Node("EnergyRelatedInventoryChemicals", attribute="debit", parent=ca4_10)
ca5_14 = Node("EnergyRelatedInventoryOtherFossilFuel", attribute="debit", parent=ca4_10)
ca5_15 = Node("CrudeOilAndNaturalGasLiquids", attribute="debit", parent=ca4_10)
ca5_16 = Node("InventoryCrudeOilProductsAndMerchandise", attribute="debit", parent=ca4_10)

ca5_17 = Node("AgriculturalRelatedInventoryPlantMaterial", attribute="debit", parent=ca4_11)
ca5_18 = Node("AgriculturalRelatedInventoryGrowingCrops", attribute="debit", parent=ca4_11)
ca5_19 = Node("AgriculturalRelatedInventoryFeedAndSupplies", attribute="debit", parent=ca4_11)

ca5_20 = Node("ConstructionContractorReceivableIncludingContractRetainageYearOne", attribute="debit", parent=ca4_6)
ca5_21 = Node("ConstructionContractorReceivableRetainageYearOne", attribute="debit", parent=ca4_6)
ca5_22 = Node("ContractReceivableDueOneYearOrLess", attribute="debit", parent=ca4_6)

"""
Non-current Assets
"""
nca = Node("AssetsNoncurrent", attribute="debit", parent=a)

# Level 1

nca1_1 = Node("InventoryNoncurrent", attribute="debit", parent=nca)
nca1_2 = Node("FinanceLeaseRightOfUseAsset", attribute="debit", parent=nca)
nca1_3 = Node("OperatingLeaseRightOfUseAsset", attribute="debit", parent=nca)
nca1_4 = Node("NetInvestmentInLeaseNoncurrent", attribute="debit", parent=nca)
nca1_5 = Node("AccountsReceivableExcludingAccruedInterestAfterAllowanceForCreditLossNoncurrent", attribute="debit",
              parent=nca)
nca1_6 = Node("FinancingReceivableExcludingAccruedInterestAfterAllowanceForCreditLossNoncurrent", attribute="debit",
              parent=nca)
nca1_7 = Node("DebtSecuritiesHeldToMaturityExcludingAccruedInterestAfterAllowanceForCreditLossNoncurrent", attribute="debit", parent=nca)
nca1_8 = Node("NetInvestmentInLeaseExcludingAccruedInterestAfterAllowanceForCreditLossNoncurrent", attribute="debit", parent=nca)
nca1_9 = Node("DebtSecuritiesAvailableForSaleAmortizedCostExcludingAccruedInterestAfterAllowanceForCreditLossNoncurrent", attribute="debit", parent=nca)
nca1_10 = Node("LeveragedLeasesNetInvestmentInLeveragedLeasesDisclosureInvestmentInLeveragedLeasesNet", attribute="debit", parent=nca)
nca1_11 = Node("InventoryRealEstate", attribute="debit", parent=nca)
nca1_12 = Node("NontradeReceivablesNoncurrent", attribute="debit", parent=nca)
nca1_13 = Node("PropertyPlantAndEquipmentNet", attribute="debit", parent=nca)
nca1_13_1 = Node("PropertyPlantAndEquipmentIncludingRightofuseAssets", attribute="debit", parent=nca1_13)
nca1_14 = Node("PropertyPlantAndEquipmentCollectionsNotCapitalized", attribute="debit", parent=nca)
nca1_15 = Node("DebtSecuritiesAvailableForSaleAccruedInterestAfterAllowanceForCreditLossNoncurrent", attribute="debit", parent=nca)
nca1_16 = Node("OilAndGasPropertySuccessfulEffortMethodNet", attribute="debit", parent=nca)
nca1_17 = Node("OilAndGasPropertyFullCostMethodNet", attribute="debit", parent=nca)
nca1_18 = Node("LongTermInvestmentsAndReceivablesNet", attribute="debit", parent=nca)
nca1_19 = Node("IntangibleAssetsNetIncludingGoodwill", attribute="debit", parent=nca)
nca1_19_1 = Node("IntangibleAssetsAndGoodwill", attribute="debit", parent=nca1_19)
nca1_20 = Node("PrepaidExpenseNoncurrent", attribute="debit", parent=nca)
nca1_21 = Node("ContractWithCustomerAssetNetNoncurrent", attribute="debit", parent=nca)
nca1_22 = Node("CapitalizedContractCostNetNoncurrent", attribute="debit", parent=nca)
nca1_23 = Node("DerivativeInstrumentsAndHedgesNoncurrent", attribute="debit", parent=nca)
nca1_24 = Node("RegulatedEntityOtherAssetsNoncurrent", attribute="debit", parent=nca)
nca1_25 = Node("DepositsAssetsNoncurrent", attribute="debit", parent=nca)
nca1_26 = Node("DeferredRentReceivablesNetNoncurrent", attribute="debit", parent=nca)
nca1_27 = Node("AssetsHeldInTrustNoncurrent", attribute="debit", parent=nca)
nca1_28 = Node("RestrictedCashAndInvestmentsNoncurrent", attribute="debit", parent=nca)
nca1_29 = Node("DisposalGroupIncludingDiscontinuedOperationAssetsNoncurrent", attribute="debit", parent=nca)
nca1_30 = Node("AdvanceRoyaltiesNoncurrent", attribute="debit", parent=nca)
nca1_31 = Node("EstimatedInsuranceRecoveries", attribute="debit", parent=nca)
nca1_32 = Node("CustomerFunds", attribute="debit", parent=nca)
nca1_33 = Node("DeferredCosts", attribute="debit", parent=nca)
nca1_34 = Node("DeferredIncomeTaxAssetsNet", attribute="debit", parent=nca)
nca1_35 = Node("BusinessCombinationContingentConsiderationAssetNoncurrent", attribute="debit", parent=nca)
nca1_36 = Node("OtherAssetsNoncurrent", attribute="debit", parent=nca)
nca1_37 = Node("AmortizationMethodQualifiedAffordableHousingProjectInvestments", attribute="debit", parent=nca)
nca1_38 = Node("OtherReceivableAfterAllowanceForCreditLossNoncurrent", attribute="debit", parent=nca)

# Level 2

nca2_1 = Node("InventoryDrillingNoncurrent", attribute="debit", parent=nca1_1)
nca2_2 = Node("InventoryGasInStorageUndergroundNoncurrent", attribute="debit", parent=nca1_1)
nca2_3 = Node("OtherInventoryNoncurrent", attribute="debit", parent=nca1_1)

nca2_4 = Node("AccountsReceivableExcludingAccruedInterestBeforeAllowanceForCreditLossNoncurrent", attribute="debit", parent=nca1_5)
nca2_5 = Node("AccountsReceivableAllowanceForCreditLossExcludingAccruedInterestNoncurrent", attribute="credit", parent=nca1_5)

nca2_6 = Node("FinancingReceivableExcludingAccruedInterestBeforeAllowanceForCreditLossNoncurrent", attribute="debit", parent=nca1_6)
nca2_7 = Node("FinancingReceivableAllowanceForCreditLossExcludingAccruedInterestNoncurrent", attribute="credit", parent=nca1_6)

nca2_8 = Node("DebtSecuritiesHeldToMaturityExcludingAccruedInterestBeforeAllowanceForCreditLossNoncurrent", attribute="debit", parent=nca1_7)
nca2_9 = Node("DebtSecuritiesHeldToMaturityAllowanceForCreditLossExcludingAccruedInterestNoncurrent", attribute="credit", parent=nca1_7)

nca2_10 = Node("NetInvestmentInLeaseExcludingAccruedInterestBeforeAllowanceForCreditLossNoncurrent", attribute="debit", parent=nca1_8)
nca2_11 = Node("NetInvestmentInLeaseAllowanceForCreditLossExcludingAccruedInterestNoncurrent", attribute="credit", parent=nca1_8)

nca2_12 = Node("DebtSecuritiesAvailableForSaleAmortizedCostExcludingAccruedInterestBeforeAllowanceForCreditLossNoncurrent", attribute="debit", parent=nca1_9)
nca2_13 = Node("DebtSecuritiesAvailableForSaleAmortizedCostAllowanceForCreditLossExcludingAccruedInterestNoncurrent", attribute="credit", parent=nca1_9)

nca2_13_1 = Node("InventoryRealEstateImprovements", attribute="debit", parent=nca1_11)
nca2_14 = Node("InventoryRealEstateHeldForSale", attribute="debit", parent=nca1_11)
nca2_15 = Node("InventoryRealEstateLandAndLandDevelopmentCosts", attribute="debit", parent=nca1_11)
nca2_16 = Node("InventoryRealEstateConstructionInProcess", attribute="debit", parent=nca1_11)
nca2_17 = Node("InventoryRealEstateMortgageLoansHeldInInventory", attribute="debit", parent=nca1_11)
nca2_18 = Node("InventoryOperativeBuilders", attribute="debit", parent=nca1_11)
nca2_19 = Node("InventoryRealEstateTimeshareAvailableForSale", attribute="debit", parent=nca1_11)
nca2_20 = Node("InventoryRealEstateOther", attribute="debit", parent=nca1_11)

nca2_21 = Node("InterestReceivableNoncurrent", attribute="debit", parent=nca1_12)
nca2_22 = Node("IncomeTaxesReceivableNoncurrent", attribute="debit", parent=nca1_12)
nca2_23 = Node("ValueAddedTaxReceivableNoncurrent", attribute="debit", parent=nca1_12)
nca2_24 = Node("InsuranceSettlementsReceivableNoncurrent", attribute="debit", parent=nca1_12)
nca2_25 = Node("GrantsReceivableNoncurrent", attribute="debit", parent=nca1_12)
nca2_26 = Node("InsuranceReceivableForMalpracticeNoncurrent", attribute="debit", parent=nca1_12)
nca2_27 = Node("OilAndGasJointInterestBillingReceivablesNoncurrent", attribute="debit", parent=nca1_12)

nca2_28 = Node("PropertyPlantAndEquipmentGross", attribute="debit", parent=nca1_13_1)
nca2_28_1 = Node("PropertyPlantAndEquipment", attribute="debit", parent=nca2_28) #IFRS
nca2_29 = Node("AccumulatedDepreciationDepletionAndAmortizationPropertyPlantAndEquipment", attribute="credit", parent=nca1_13_1)

nca2_30 = Node("OilAndGasPropertySuccessfulEffortMethodGross", attribute="debit", parent=nca1_16)
nca2_31 = Node("OilAndGasPropertySuccessfulEffortMethodAccumulatedDepreciationDepletionAmortizationAndImpairment", attribute="credit", parent=nca1_16)
nca2_32 = Node("OtherOilAndGasPropertySuccessfulEffortMethod", attribute="debit", parent=nca1_16)

nca2_33 = Node("OilAndGasPropertyFullCostMethodGross", attribute="debit", parent=nca1_17)
nca2_34 = Node("OilAndGasPropertyFullCostMethodDepletion", attribute="credit", parent=nca1_17)

nca2_35 = Node("LongTermInvestments", attribute="debit", parent=nca1_18)
nca2_36 = Node("LongTermAccountsNotesAndLoansReceivableNetNoncurrent", attribute="debit", parent=nca1_18)

nca2_37 = Node("Goodwill", attribute="debit", parent=nca1_19_1)
nca2_38 = Node("IntangibleAssetsNetExcludingGoodwill", attribute="debit", parent=nca1_19_1)
nca2_38_1 = Node("IntangibleAssetsOtherThanGoodwill", attribute="debit", parent=nca2_38)

nca2_39 = Node("PrepaidExpenseOtherNoncurrent", attribute="debit", parent=nca1_20)
nca2_40 = Node("PrepaidMineralRoyaltiesNoncurrent", attribute="debit", parent=nca1_20)

nca2_41 = Node("DerivativeAssetsNoncurrent", attribute="debit", parent=nca1_23)
nca2_42 = Node("HedgingAssetsNoncurrent", attribute="debit", parent=nca1_23)
nca2_43 = Node("CommodityContractAssetNoncurrent", attribute="debit", parent=nca1_23)
nca2_44 = Node("EnergyMarketingContractsAssetsNoncurrent", attribute="debit", parent=nca1_23)

nca2_45 = Node("RegulatoryAssetsNoncurrent", attribute="debit", parent=nca1_24)
nca2_46 = Node("SecuritizedRegulatoryTransitionAssetsNoncurrent", attribute="debit", parent=nca1_24)
nca2_47 = Node("DemandSideManagementProgramCostsNoncurrent", attribute="debit", parent=nca1_24)
nca2_48 = Node("UnamortizedLossReacquiredDebtNoncurrent", attribute="debit", parent=nca1_24)
nca2_49 = Node("DecommissioningFundInvestments", attribute="debit", parent=nca1_24)
nca2_50 = Node("AssetRecoveryDamagedPropertyCostsNoncurrent", attribute="debit", parent=nca1_24)
nca2_51 = Node("DeferredStormAndPropertyReserveDeficiencyNoncurrent", attribute="debit", parent=nca1_24)
nca2_52 = Node("InvestmentsInPowerAndDistributionProjects", attribute="debit", parent=nca1_24)
nca2_53 = Node("UnamortizedDebtIssuanceExpense", attribute="debit", parent=nca1_24)
nca2_54 = Node("PhaseInPlanAmountOfCostsDeferredForRateMakingPurposes", attribute="debit", parent=nca1_24)

nca2_55 = Node("RestrictedCashAndCashEquivalentsNoncurrent", attribute="debit", parent=nca1_28)
nca2_56 = Node("RestrictedInvestmentsNoncurrent", attribute="debit", parent=nca1_28)
nca2_57 = Node("OtherRestrictedAssetsNoncurrent", attribute="debit", parent=nca1_28)

nca2_58 = Node("DisposalGroupIncludingDiscontinuedOperationOtherNoncurrentAssets", attribute="debit", parent=nca1_29)
nca2_59 = Node("DisposalGroupIncludingDiscontinuedOperationInventoryNoncurrent", attribute="debit", parent=nca1_29)
nca2_60 = Node("DisposalGroupIncludingDiscontinuedOperationDeferredTaxAssets", attribute="debit", parent=nca1_29)
nca2_61 = Node("DisposalGroupIncludingDiscontinuedOperationIntangibleAssetsNoncurrent", attribute="debit",
               parent=nca1_29)
nca2_62 = Node("DisposalGroupIncludingDiscontinuedOperationGoodwillNoncurrent", attribute="debit", parent=nca1_29)
nca2_63 = Node("DisposalGroupIncludingDiscontinuedOperationPropertyPlantAndEquipmentNoncurrent", attribute="debit",
               parent=nca1_29)

nca2_64 = Node("DeferredCostsLeasingNetNoncurrent", attribute="debit", parent=nca1_33)
nca2_65 = Node("CapitalizedSoftwareDevelopmentCostsForSoftwareSoldToCustomers", attribute="debit", parent=nca1_33)
nca2_66 = Node("DeferredCompensationPlanAssets", attribute="debit", parent=nca1_33)

nca2_67 = Node("OtherReceivableBeforeAllowanceForCreditLossNoncurrent", attribute="debit", parent=nca1_38)
nca2_68 = Node("OtherReceivableAllowanceForCreditLossNoncurrent", attribute="debit", parent=nca1_38)

# Level 3
nca3_1 = Node("LandAndLandImprovements", attribute="debit", parent=nca2_28_1)
nca3_2 = Node("BuildingsAndImprovementsGross", attribute="debit", parent=nca2_28_1)
nca3_3 = Node("MachineryAndEquipmentGross", attribute="debit", parent=nca2_28_1)
nca3_4 = Node("FurnitureAndFixturesGross", attribute="debit", parent=nca2_28_1)
nca3_5 = Node("FixturesAndEquipmentGross", attribute="debit", parent=nca2_28_1)
nca3_6 = Node("CapitalizedComputerSoftwareGross", attribute="debit", parent=nca2_28_1)
nca3_7 = Node("ConstructionInProgressGross", attribute="debit", parent=nca2_28_1)
nca3_8 = Node("LeaseholdImprovementsGross", attribute="debit", parent=nca2_28_1)
nca3_9 = Node("TimberAndTimberlands", attribute="debit", parent=nca2_28_1)
nca3_10 = Node("PropertyPlantAndEquipmentOther", attribute="debit", parent=nca2_28_1)

nca3_11 = Node("UnprovedOilAndGasPropertySuccessfulEffortMethod", attribute="debit", parent=nca2_30)
nca3_12 = Node("ProvedOilAndGasPropertySuccessfulEffortMethod", attribute="debit", parent=nca2_30)

nca3_13 = Node("OilAndGasPropertySuccessfulEffortMethodAccumulatedImpairment", attribute="credit", parent=nca2_31)
nca3_14 = Node("OilAndGasPropertySuccessfulEffortMethodAccumulatedDepreciationDepletionAndAmortization",
               attribute="credit", parent=nca2_31)

nca3_15 = Node("InvestmentsInAffiliatesSubsidiariesAssociatesAndJointVentures", attribute="debit", parent=nca2_35)
nca3_16 = Node("EquitySecuritiesFVNINoncurrent", attribute="debit", parent=nca2_35)
nca3_17 = Node("DebtSecuritiesNoncurrent", attribute="debit", parent=nca2_35)
nca3_18 = Node("MarketableSecuritiesNoncurrent", attribute="debit", parent=nca2_35)
nca3_19 = Node("InvestmentInPhysicalCommodities", attribute="debit", parent=nca2_35)
nca3_20 = Node("OtherLongTermInvestments", attribute="debit", parent=nca2_35)
nca3_21 = Node("AuctionRateSecuritiesNoncurrent", attribute="debit", parent=nca2_35)
nca3_22 = Node("LeveragedLeaseInvestment", attribute="debit", parent=nca2_35)

nca3_23 = Node("AccountsReceivableNetNoncurrent", attribute="debit", parent=nca2_36)
nca3_24 = Node("NotesAndLoansReceivableNetNoncurrent", attribute="debit", parent=nca2_36)

nca3_25 = Node("GoodwillGross", attribute="debit", parent=nca2_37)
nca3_26 = Node("GoodwillImpairedAccumulatedImpairmentLoss", attribute="credit", parent=nca2_37)

nca3_27 = Node("FiniteLivedIntangibleAssetsNet", attribute="debit", parent=nca2_38)
nca3_28 = Node("IndefiniteLivedIntangibleAssetsExcludingGoodwill", attribute="debit", parent=nca2_38)
nca3_29 = Node("OtherIntangibleAssetsNet", attribute="debit", parent=nca2_38)

nca3_30 = Node("RestrictedCashNoncurrent", attribute="debit", parent=nca2_55)
nca3_31 = Node("RestrictedCashEquivalentsNoncurrent", attribute="debit", parent=nca2_55)

# Level 4

nca4_1 = Node("EquityMethodInvestments", attribute="debit", parent=nca3_15)
nca4_2 = Node("AdvancesToAffiliate", attribute="debit", parent=nca3_15)

nca4_3 = Node("AvailableForSaleSecuritiesDebtSecuritiesNoncurrent", attribute="debit", parent=nca3_17)
nca4_4 = Node("DebtSecuritiesHeldToMaturityAmortizedCostAfterAllowanceForCreditLossNoncurrent", attribute="debit",
              parent=nca3_17)

nca4_5 = Node("AccountsReceivableGrossNoncurrent", attribute="debit", parent=nca3_23)
nca4_6 = Node("AllowanceForDoubtfulAccountsReceivableNoncurrent", attribute="credit", parent=nca3_23)

nca4_7 = Node("NotesAndLoansReceivableGrossNoncurrent", attribute="debit", parent=nca3_24)
nca4_8 = Node("AllowanceForNotesAndLoansReceivableNoncurrent", attribute="credit", parent=nca3_24)

nca4_9 = Node("FiniteLivedIntangibleAssetsAccumulatedAmortization", attribute="credit", parent=nca3_27)
nca4_10 = Node("FiniteLivedIntangibleAssetsGross", attribute="debit", parent=nca3_27)

# Level 5

nca5_1 = Node("HeldToMaturitySecuritiesNoncurrent", attribute="debit", parent=nca4_4)
nca5_2 = Node("DebtSecuritiesHeldToMaturityAllowanceForCreditLossNoncurrent", attribute="credit", parent=nca4_4)

nca5_3 = Node("ConstructionContractorReceivableIncludingContractRetainageAfterYearOne", attribute="debit",
              parent=nca4_5)
nca5_4 = Node("ConstructionContractorReceivableRetainageAfterYearOne", attribute="debit", parent=nca4_5)
nca5_5 = Node("ContractReceivableDueAfterOneYear", attribute="debit", parent=nca4_5)

"""
Current Liabilities
"""
cl1 = Node("CurrentLiabilities", attribute="credit", parent=l)
cl = Node("LiabilitiesCurrent", attribute="credit", parent=cl1)

# Level 1

cl1_1 = Node("AccountsPayableAndAccruedLiabilitiesCurrent", attribute="credit", parent=cl)
cl1_1_1 = Node("CurrentAccrualsAndCurrentDeferredIncomeIncludingCurrentContractLiabilities", attribute = "credit", parent = cl1_1) # IFRS
cl1_2 = Node("DeferredRevenueCurrent", attribute="credit", parent=cl)
cl1_3 = Node("DebtCurrent", attribute="credit", parent=cl)
cl1_4 = Node("DeferredCompensationLiabilityCurrent", attribute="credit", parent=cl)
cl1_5 = Node("DeferredRentCreditCurrent", attribute="credit", parent=cl)
cl1_6 = Node("DerivativeInstrumentsAndHedgesLiabilities", attribute="credit", parent=cl)
cl1_7 = Node("RestructuringReserveCurrent", attribute="credit", parent=cl)
cl1_8 = Node("LiabilityForUncertainTaxPositionsCurrent", attribute="credit", parent=cl)
cl1_9 = Node("PostemploymentBenefitsLiabilityCurrent", attribute="credit", parent=cl)
cl1_10 = Node("SecuritiesLoaned", attribute="credit", parent=cl)
cl1_11 = Node("RegulatoryLiabilityCurrent", attribute="credit", parent=cl)
cl1_12 = Node("ProvisionForLossOnContracts", attribute="credit", parent=cl)
cl1_13 = Node("LitigationReserveCurrent", attribute="credit", parent=cl)
cl1_14 = Node("AccruedEnvironmentalLossContingenciesCurrent", attribute="credit", parent=cl)
cl1_15 = Node("AssetRetirementObligationCurrent", attribute="credit", parent=cl)
cl1_16 = Node("AccruedCappingClosurePostClosureAndEnvironmentalCosts", attribute="credit", parent=cl)
cl1_17 = Node("AccruedReclamationCostsCurrent", attribute="credit", parent=cl)
cl1_18 = Node("DeferredGasPurchasesCurrent", attribute="credit", parent=cl)
cl1_19 = Node("DueToRelatedPartiesCurrent", attribute="credit", parent=cl)
cl1_20 = Node("LiabilitiesOfDisposalGroupIncludingDiscontinuedOperationCurrent", attribute="credit", parent=cl)
cl1_21 = Node("LiabilitiesOfBusinessTransferredUnderContractualArrangementCurrent", attribute="credit", parent=cl)
cl1_22 = Node("SharesSubjectToMandatoryRedemptionSettlementTermsAmountCurrent", attribute="credit", parent=cl)
cl1_23 = Node("CustomerRefundLiabilityCurrent", attribute="credit", parent=cl)
cl1_24 = Node("SelfInsuranceReserveCurrent", attribute="credit", parent=cl)
cl1_25 = Node("ProgramRightsObligationsCurrent", attribute="credit", parent=cl)
cl1_26 = Node("BusinessCombinationContingentConsiderationLiabilityCurrent", attribute="credit", parent=cl)
cl1_27 = Node("OtherLiabilitiesCurrent", attribute="credit", parent=cl)

# Level 2

cl2_1 = Node("AccountsPayableCurrent", attribute="credit", parent=cl1_1_1)
cl2_2 = Node("AccruedLiabilitiesCurrent", attribute="credit", parent=cl1_1_1)
cl2_3 = Node("EmployeeRelatedLiabilitiesCurrent", attribute="credit", parent=cl1_1_1)
cl2_4 = Node("TaxesPayableCurrent", attribute="credit", parent=cl1_1_1)
cl2_5 = Node("InterestAndDividendsPayableCurrent", attribute="credit", parent=cl1_1_1)
cl2_6 = Node("SettlementLiabilitiesCurrent", attribute="credit", parent=cl1_1_1)

cl2_7 = Node("ContractWithCustomerLiabilityCurrent", attribute="credit", parent=cl1_2)
cl2_8 = Node("DeferredIncomeCurrent", attribute="credit", parent=cl1_2)

cl2_9 = Node("ShortTermBorrowings", attribute="credit", parent=cl1_3)
cl2_10 = Node("LongTermDebtAndCapitalLeaseObligationsCurrent", attribute="credit", parent=cl1_3)
cl2_29 = Node("ShorttermBorrowings", attribute="credit", parent=cl1_3)
cl2_30 = Node("CurrentPortionOfLongtermBorrowings", attribute="credit", parent=cl1_3)
cl2_31 = Node("CurrentBorrowingsAndCurrentPortionOfNoncurrentBorrowings", attribute="credit", parent=cl1_3)

cl2_11 = Node("DeferredCompensationShareBasedArrangementsLiabilityCurrent", attribute="credit", parent=cl1_4)
cl2_12 = Node("DeferredCompensationCashBasedArrangementsLiabilityCurrent", attribute="credit", parent=cl1_4)
cl2_13 = Node("OtherDeferredCompensationArrangementsLiabilityCurrent", attribute="credit", parent=cl1_4)

cl2_14 = Node("DerivativeLiabilitiesCurrent", attribute="credit", parent=cl1_6)
cl2_15 = Node("EnergyMarketingContractLiabilitiesCurrent", attribute="credit", parent=cl1_6)
cl2_16 = Node("HedgingLiabilitiesCurrent", attribute="credit", parent=cl1_6)

cl2_17 = Node("AccountsPayableRelatedPartiesCurrent", attribute="credit", parent=cl1_19)
cl2_18 = Node("NotesPayableRelatedPartiesClassifiedCurrent", attribute="credit", parent=cl1_19)
cl2_19 = Node("DueToEmployeesCurrent", attribute="credit", parent=cl1_19)
cl2_20 = Node("DueToOfficersOrStockholdersCurrent", attribute="credit", parent=cl1_19)
cl2_21 = Node("DueToAffiliateCurrentDueToOtherRelatedPartiesClassifiedCurrent", attribute="credit", parent=cl1_19)
cl2_22 = Node("DueToOtherRelatedPartiesClassifiedCurrent", attribute="credit", parent=cl1_19)

cl2_23 = Node("DisposalGroupIncludingDiscontinuedOperationAccountsPayableAndAccruedLiabilitiesCurrent",attribute="credit", parent=cl1_20)
cl2_24 = Node("DisposalGroupIncludingDiscontinuedOperationDeferredRevenueCurrent", attribute="credit", parent=cl1_20)
cl2_25 = Node("DisposalGroupIncludingDiscontinuedOperationAccruedIncomeTaxesPayable", attribute="credit", parent=cl1_20)
cl2_26 = Node("DisposalGroupIncludingDiscontinuedOperationOtherCurrentLiabilities", attribute="credit", parent=cl1_20)
cl2_27 = Node("DisposalGroupIncludingDiscontinuedOperationPensionPlanBenefitObligationCurrent", attribute="credit", parent=cl1_20)
cl2_28 = Node("DisposalGroupIncludingDiscontinuedOperationPostretirementPlanBenefitObligationCurrent", attribute="credit", parent=cl1_20)

# Level 3

cl3_1 = Node("AccountsPayableTradeCurrent", attribute="credit", parent=cl2_1)
cl3_2 = Node("AccountsPayableInterestBearingCurrent", attribute="credit", parent=cl2_1)
cl3_3 = Node("ConstructionPayableCurrent", attribute="credit", parent=cl2_1)
cl3_4 = Node("OilAndGasSalesPayableCurrent", attribute="credit", parent=cl2_1)
cl3_5 = Node("GasPurchasePayableCurrent", attribute="credit", parent=cl2_1)
cl3_6 = Node("EnergyMarketingAccountsPayable", attribute="credit", parent=cl2_1)
cl3_7 = Node("GasImbalancePayableCurrent", attribute="credit", parent=cl2_1)
cl3_8 = Node("AccountsPayableUnderwritersPromotersAndEmployeesOtherThanSalariesAndWagesCurrent", attribute="credit",parent=cl2_1)
cl3_9 = Node("AccountsPayableOtherCurrent", attribute="credit", parent=cl2_1)
cl3_63= Node("TradeAndOtherCurrentPayablesToRelatedParties", attribute="credit", parent=cl2_1) #IFRS
cl3_64= Node("CurrentContractLiabilities", attribute="credit", parent=cl2_1) #IFRS

cl3_10 = Node("AccruedInsuranceCurrent", attribute="credit", parent=cl2_2)
cl3_11 = Node("AccruedRentCurrent", attribute="credit", parent=cl2_2)
cl3_12 = Node("AccruedRoyaltiesCurrent", attribute="credit", parent=cl2_2)
cl3_13 = Node("AccruedUtilitiesCurrent", attribute="credit", parent=cl2_2)
cl3_14 = Node("AccruedSalesCommissionCurrent", attribute="credit", parent=cl2_2)
cl3_15 = Node("AccruedProfessionalFeesCurrent", attribute="credit", parent=cl2_2)
cl3_16 = Node("AccruedAdvertisingCurrent", attribute="credit", parent=cl2_2)
cl3_17 = Node("AccruedExchangeFeeRebateCurrent", attribute="credit", parent=cl2_2)
cl3_18 = Node("ProductWarrantyAccrualClassifiedCurrent", attribute="credit", parent=cl2_2)
cl3_19 = Node("AccruedMarketingCostsCurrent", attribute="credit", parent=cl2_2)
cl3_20 = Node("OtherAccruedLiabilitiesCurrent", attribute="credit", parent=cl2_2)
cl3_66 = Node("Accruals", attribute="credit", parent=cl2_2) #IFRS
cl3_65 = Node("AccrualsClassifiedAsCurrent", attribute="credit", parent=cl2_2) #IFRS

cl3_21 = Node("AccruedSalariesCurrent", attribute="credit", parent=cl2_3)
cl3_22 = Node("AccruedVacationCurrent", attribute="credit", parent=cl2_3)
cl3_23 = Node("AccruedBonusesCurrent", attribute="credit", parent=cl2_3)
cl3_24 = Node("AccruedPayrollTaxesCurrent", attribute="credit", parent=cl2_3)
cl3_25 = Node("AccruedEmployeeBenefitsCurrent", attribute="credit", parent=cl2_3)
cl3_26 = Node("WorkersCompensationLiabilityCurrent", attribute="credit", parent=cl2_3)
cl3_27 = Node("PensionAndOtherPostretirementDefinedBenefitPlansCurrentLiabilities", attribute="credit", parent=cl2_3)
cl3_28 = Node("PensionAndOtherPostretirementAndPostemploymentBenefitPlansLiabilitiesCurrent", attribute="credit", parent=cl2_3)
cl3_29 = Node("OtherEmployeeRelatedLiabilitiesCurrent", attribute="credit", parent=cl2_3)
cl3_30 = Node("DefinedBenefitPensionPlanLiabilitiesCurrent", attribute="credit", parent=cl2_3)

cl3_31 = Node("SalesAndExciseTaxPayableCurrent", attribute="credit", parent=cl2_4)
cl3_32 = Node("AccruedIncomeTaxesCurrent", attribute="credit", parent=cl2_4)
cl3_33 = Node("AccrualForTaxesOtherThanIncomeTaxesCurrent", attribute="credit", parent=cl2_4)

cl3_34 = Node("DividendsPayableCurrent", attribute="credit", parent=cl2_5)
cl3_35 = Node("InterestPayableCurrent", attribute="credit", parent=cl2_5)

cl3_36 = Node("BankOverdrafts", attribute="credit", parent=cl2_9)
cl3_37 = Node("CommercialPaper", attribute="credit", parent=cl2_9)
cl3_38 = Node("BridgeLoan", attribute="credit", parent=cl2_9)
cl3_39 = Node("ConstructionLoan", attribute="credit", parent=cl2_9)
cl3_40 = Node("ShortTermBankLoansAndNotesPayable", attribute="credit", parent=cl2_9)
cl3_41 = Node("ShortTermNonBankLoansAndNotesPayable", attribute="credit", parent=cl2_9)
cl3_42 = Node("SecuritiesSoldUnderAgreementsToRepurchase", attribute="credit", parent=cl2_9)
cl3_43 = Node("FederalHomeLoanBankAdvancesMaturitiesSummaryDueWithinOneYearOfBalanceSheetDate", attribute="credit",
              parent=cl2_9)
cl3_44 = Node("WarehouseAgreementBorrowings", attribute="credit", parent=cl2_9)
cl3_45 = Node("OtherShortTermBorrowings", attribute="credit", parent=cl2_9)

cl3_46 = Node("SecuredDebtCurrent", attribute="credit", parent=cl2_10)
cl3_47 = Node("ConvertibleDebtCurrent", attribute="credit", parent=cl2_10)
cl3_48 = Node("UnsecuredDebtCurrent", attribute="credit", parent=cl2_10)
cl3_49 = Node("SubordinatedDebtCurrent", attribute="credit", parent=cl2_10)
cl3_50 = Node("ConvertibleSubordinatedDebtCurrent", attribute="credit", parent=cl2_10)
cl3_51 = Node("LongTermCommercialPaperCurrent", attribute="credit", parent=cl2_10)
cl3_52 = Node("LongTermConstructionLoanCurrent", attribute="credit", parent=cl2_10)
cl3_53 = Node("LongtermTransitionBondCurrent", attribute="credit", parent=cl2_10)
cl3_54 = Node("LongtermPollutionControlBondCurrent", attribute="credit", parent=cl2_10)
cl3_55 = Node("JuniorSubordinatedDebentureOwedToUnconsolidatedSubsidiaryTrustCurrent", attribute="credit",
              parent=cl2_10)
cl3_56 = Node("OtherLongTermDebtCurrent", attribute="credit", parent=cl2_10)
cl3_57 = Node("LinesOfCreditCurrent", attribute="credit", parent=cl2_10)
cl3_58 = Node("NotesAndLoansPayableCurrent", attribute="credit", parent=cl2_10)
cl3_59 = Node("SpecialAssessmentBondCurrent", attribute="credit", parent=cl2_10)
cl3_60 = Node("FederalHomeLoanBankAdvancesCurrent", attribute="credit", parent=cl2_10)

cl3_61 = Node("DisposalGroupIncludingDiscontinuedOperationAccountsPayableCurrent", attribute="credit", parent=cl2_23)
cl3_62 = Node("DisposalGroupIncludingDiscontinuedOperationAccruedLiabilitiesCurrent", attribute="credit", parent=cl2_23)

# Level 4

cl4_6 = Node("CurrentAdvances", attribute = "credit", parent = cl3_64)

cl4_1 = Node("StandardProductWarrantyAccrualCurrent", attribute="credit", parent=cl3_18)
cl4_2 = Node("ExtendedProductWarrantyAccrualCurrent", attribute="credit", parent=cl3_18)

cl4_3 = Node("TaxCutsAndJobsActOf2017TransitionTaxForAccumulatedForeignEarningsLiabilityCurrent", attribute="credit",
             parent=cl3_32)

cl4_4 = Node("NotesPayableCurrent", attribute="credit", parent=cl3_58)
cl4_5 = Node("LoansPayableCurrent", attribute="credit", parent=cl3_58)

# Level 5

cl5_1 = Node("MediumtermNotesCurrent", attribute="credit", parent=cl4_4)
cl5_2 = Node("ConvertibleNotesPayableCurrent", attribute="credit", parent=cl4_4)
cl5_3 = Node("NotesPayableToBankCurrent", attribute="credit", parent=cl4_4)
cl5_4 = Node("SeniorNotesCurrent", attribute="credit", parent=cl4_4)
cl5_5 = Node("JuniorSubordinatedNotesCurrent", attribute="credit", parent=cl4_4)
cl5_6 = Node("OtherNotesPayableCurrent", attribute="credit", parent=cl4_4)

cl5_7 = Node("LoansPayableToBankCurrent", attribute="credit", parent=cl4_5)
cl5_8 = Node("OtherLoansPayableCurrent", attribute="credit", parent=cl4_5)

"""
Non-Current Liabilties
"""

ncl = Node("LiabilitiesNoncurrent", attribute="credit", parent=l)
ncl1 = Node("NoncurrentLiabilities", attribute="credit", parent=ncl)

# Level 1

ncl1_1 = Node("LongTermDebtAndCapitalLeaseObligations", attribute="credit", parent=ncl1)
ncl1_2 = Node("LiabilitiesOtherThanLongtermDebtNoncurrent", attribute="credit", parent=ncl1)

# Level 2

ncl2_1 = Node("LongTermDebtNoncurrent", attribute="credit", parent=ncl1_1)
ncl2_2 = Node("CapitalLeaseObligationsNoncurrent", attribute="credit", parent=ncl1_1)

ncl2_3 = Node("LiabilitiesOtherThanLongtermDebtNoncurrent", attribute="credit", parent=ncl1_2)

# Level 3

ncl3_1 = Node("LongTermLineOfCredit", attribute="credit", parent=ncl2_1)
ncl3_2 = Node("CommercialPaperNoncurrent", attribute="credit", parent=ncl2_1)
ncl3_3 = Node("ConstructionLoanNoncurrent", attribute="credit", parent=ncl2_1)
ncl3_4 = Node("SecuredLongTermDebt", attribute="credit", parent=ncl2_1)
ncl3_5 = Node("SubordinatedLongTermDebt", attribute="credit", parent=ncl2_1)
ncl3_6 = Node("UnsecuredLongTermDebt", attribute="credit", parent=ncl2_1)
ncl3_7 = Node("ConvertibleDebtNoncurrent", attribute="credit", parent=ncl2_1)
ncl3_8 = Node("ConvertibleSubordinatedDebtNoncurrent", attribute="credit", parent=ncl2_1)
ncl3_9 = Node("LongTermTransitionBond", attribute="credit", parent=ncl2_1)
ncl3_10 = Node("LongTermPollutionControlBond", attribute="credit", parent=ncl2_1)
ncl3_11 = Node("JuniorSubordinatedDebentureOwedToUnconsolidatedSubsidiaryTrustNoncurrent", attribute="credit", parent=ncl2_1)
ncl3_12 = Node("LongTermNotesAndLoans", attribute="credit", parent=ncl2_1)
ncl3_13 = Node("SpecialAssessmentBondNoncurrent", attribute="credit", parent=ncl2_1)
ncl3_14 = Node("LongtermFederalHomeLoanBankAdvancesNoncurrent", attribute="credit", parent=ncl2_1)
ncl3_15 = Node("OtherLongTermDebtNoncurrent", attribute="credit", parent=ncl2_1)
ncl3_45 = Node("LongtermBorrowings", attribute="credit", parent=ncl2_1)

ncl3_16 = Node("AccountsPayableAndAccruedLiabilitiesNoncurrent", attribute="credit", parent=ncl2_3)
ncl3_17 = Node("DeferredRevenueNoncurrent", attribute="credit", parent=ncl2_3)
ncl3_18 = Node("DeferredCompensationLiabilityClassifiedNoncurrent", attribute="credit", parent=ncl2_3)
ncl3_19 = Node("AccumulatedDeferredInvestmentTaxCredit", attribute="credit", parent=ncl2_3)
ncl3_20 = Node("DeferredGainOnSaleOfProperty", attribute="credit", parent=ncl2_3)
ncl3_21 = Node("DeferredRentCreditNoncurrent", attribute="credit", parent=ncl2_3)
ncl3_22 = Node("AssetRetirementObligationsNoncurrent", attribute="credit", parent=ncl2_3)
ncl3_23 = Node("DeferredIncomeTaxLiabilitiesNet", attribute="credit", parent=ncl2_3)
ncl3_24 = Node("LiabilityForUncertainTaxPositionsNoncurrent", attribute="credit", parent=ncl2_3)
ncl3_25 = Node("PensionAndOtherPostretirementAndPostemploymentBenefitPlansLiabilitiesNoncurrent", attribute="credit",
               parent=ncl2_3)
ncl3_26 = Node("AccruedEnvironmentalLossContingenciesNoncurrent", attribute="credit", parent=ncl2_3)
ncl3_27 = Node("CustomerRefundLiabilityNoncurrent", attribute="credit", parent=ncl2_3)
ncl3_28 = Node("OffMarketLeaseUnfavorable", attribute="credit", parent=ncl2_3)
ncl3_29 = Node("LeaseDepositLiability", attribute="credit", parent=ncl2_3)
ncl3_30 = Node("SharesSubjectToMandatoryRedemptionSettlementTermsAmountNoncurrent", attribute="credit", parent=ncl2_3)
ncl3_31 = Node("LitigationReserveNoncurrent", attribute="credit", parent=ncl2_3)
ncl3_32 = Node("RegulatoryLiabilityNoncurrent", attribute="credit", parent=ncl2_3)
ncl3_33 = Node("RestructuringReserveNoncurrent", attribute="credit", parent=ncl2_3)
ncl3_34 = Node("DueToRelatedPartiesNoncurrent", attribute="credit", parent=ncl2_3)
ncl3_35 = Node("LiabilitiesOfDisposalGroupIncludingDiscontinuedOperationNoncurrent", attribute="credit", parent=ncl2_3)
ncl3_36 = Node("LiabilitiesOfBusinessTransferredUnderContractualArrangementNoncurrent", attribute="credit",
               parent=ncl2_3)
ncl3_37 = Node("OtherLiabilitiesNoncurrent", attribute="credit", parent=ncl2_3)
ncl3_38 = Node("OperatingLeaseLiabilityNoncurrent", attribute="credit", parent=ncl2_3)
ncl3_39 = Node("DueToRelatedPartiesNoncurrent", attribute="credit", parent=ncl2_3)
ncl3_40 = Node("SelfInsuranceReserveNoncurrent", attribute="credit", parent=ncl2_3)
ncl3_41 = Node("ProgramRightsObligationsNoncurrent", attribute="credit", parent=ncl2_3)
ncl3_42 = Node("BusinessCombinationContingentConsiderationLiabilityNoncurrent", attribute="credit", parent=ncl2_3)
ncl3_43 = Node("DerivativeInstrumentsAndHedgesLiabilitiesNoncurrent", attribute="credit", parent=ncl2_3)
ncl3_44 = Node("QualifiedAffordableHousingProjectInvestmentsCommitment", attribute="credit", parent=ncl2_3)

# Level 4

ncl4_1 = Node("LongTermNotesPayable", attribute="credit", parent=ncl3_12)
ncl4_2 = Node("LongTermLoansPayable", attribute="credit", parent=ncl3_12)

ncl4_3 = Node("AccruedInsuranceNoncurrent", attribute="credit", parent=ncl3_16)
ncl4_4 = Node("AccruedIncomeTaxesNoncurrent", attribute="credit", parent=ncl3_16)
ncl4_5 = Node("AccruedRentNoncurrent", attribute="credit", parent=ncl3_16)
ncl4_6 = Node("ProductWarrantyAccrualNoncurrent", attribute="credit", parent=ncl3_16)
ncl4_7 = Node("AccountsPayableInterestBearingNoncurrent", attribute="credit", parent=ncl3_16)
ncl4_8 = Node("OtherAccruedLiabilitiesNoncurrent", attribute="credit", parent=ncl3_16)
ncl4_9 = Node("WorkersCompensationLiabilityNoncurrent", attribute="credit", parent=ncl3_16)

ncl4_10 = Node("ContractWithCustomerLiabilityNoncurrent", attribute="credit", parent=ncl3_17)
ncl4_11 = Node("DeferredIncomeNoncurrent", attribute="credit", parent=ncl3_17)

ncl4_12 = Node("DeferredCompensationSharebasedArrangementsLiabilityClassifiedNoncurrent", attribute="credit",
               parent=ncl3_18)
ncl4_13 = Node("DeferredCompensationCashbasedArrangementsLiabilityClassifiedNoncurrent", attribute="credit",
               parent=ncl3_18)
ncl4_14 = Node("OtherDeferredCompensationArrangementsLiabilityClassifiedNoncurrent", attribute="credit", parent=ncl3_18)

ncl4_15 = Node("MineReclamationAndClosingLiabilityNoncurrent", attribute="credit", parent=ncl3_22)
ncl4_16 = Node("OilAndGasReclamationLiabilityNoncurrent", attribute="credit", parent=ncl3_22)
ncl4_17 = Node("AccruedCappingClosurePostClosureAndEnvironmentalCostsNoncurrent", attribute="credit", parent=ncl3_22)
ncl4_18 = Node("DecommissioningLiabilityNoncurrent", attribute="credit", parent=ncl3_22)
ncl4_19 = Node("SpentNuclearFuelObligationNoncurrent", attribute="credit", parent=ncl3_22)

ncl4_20 = Node("PensionAndOtherPostretirementDefinedBenefitPlansLiabilitiesNoncurrent", attribute="credit",
               parent=ncl3_25)
ncl4_21 = Node("PostemploymentBenefitsLiabilityNoncurrent", attribute="credit", parent=ncl3_25)

ncl4_22 = Node("NotesPayableRelatedPartiesNoncurrent", attribute="credit", parent=ncl3_34)
ncl4_23 = Node("DueToEmployeesNoncurrent", attribute="credit", parent=ncl3_34)
ncl4_24 = Node("DueToOfficersOrStockholdersNoncurrent", attribute="credit", parent=ncl3_34)
ncl4_25 = Node("DueToAffiliateNoncurrent", attribute="credit", parent=ncl3_34)
ncl4_26 = Node("DueToOtherRelatedPartiesNoncurrent", attribute="credit", parent=ncl3_34)
ncl4_27 = Node("AccountsPayableRelatedPartiesNoncurrent", attribute="credit", parent=ncl3_34)

ncl4_28 = Node("DisposalGroupIncludingDiscontinuedOperationDeferredTaxLiabilities", attribute="credit", parent=ncl3_35)
ncl4_29 = Node("DisposalGroupIncludingDiscontinuedOperationDeferredRevenueNoncurrent", attribute="credit",
               parent=ncl3_35)
ncl4_30 = Node("DisposalGroupIncludingDiscontinuedOperationOtherNoncurrentLiabilities", attribute="credit",
               parent=ncl3_35)
ncl4_31 = Node("DisposalGroupIncludingDiscontinuedOperationPensionPlanBenefitObligationNoncurrent", attribute="credit",
               parent=ncl3_35)
ncl4_32 = Node("DisposalGroupIncludingDiscontinuedOperationPostretirementPlanBenefitObligationNoncurrent",
               attribute="credit", parent=ncl3_35)
ncl4_33 = Node("DisposalGroupIncludingDiscontinuedOperationAccruedIncomeTaxPayableNoncurrent", attribute="credit",
               parent=ncl3_35)

ncl4_34 = Node("DerivativeLiabilitiesNoncurrent", attribute="credit", parent=ncl3_43)
ncl4_35 = Node("HedgingLiabilitiesNoncurrent", attribute="credit", parent=ncl3_43)
ncl4_36 = Node("EnergyMarketingContractLiabilitiesNoncurrent", attribute="credit", parent=ncl3_43)

# Level 5

ncl5_1 = Node("MediumtermNotesNoncurrent", attribute="credit", parent=ncl4_1)
ncl5_2 = Node("JuniorSubordinatedLongTermNotes", attribute="credit", parent=ncl4_1)
ncl5_3 = Node("SeniorLongTermNotes", attribute="credit", parent=ncl4_1)
ncl5_4 = Node("ConvertibleLongTermNotesPayable", attribute="credit", parent=ncl4_1)
ncl5_5 = Node("NotesPayableToBankNoncurrent", attribute="credit", parent=ncl4_1)
ncl5_6 = Node("OtherLongTermNotesPayable", attribute="credit", parent=ncl4_1)

ncl5_7 = Node("LongTermLoansFromBank", attribute="credit", parent=ncl4_2)
ncl5_8 = Node("OtherLoansPayableLongTerm", attribute="credit", parent=ncl4_2)

ncl5_9 = Node("TaxCutsAndJobsActOf2017TransitionTaxForAccumulatedForeignEarningsLiabilityNoncurrent",
              attribute="credit", parent=ncl4_4)

ncl5_10 = Node("ExtendedProductWarrantyAccrualNoncurrent", attribute="credit", parent=ncl4_6)
ncl5_11 = Node("StandardProductWarrantyAccrualNoncurrent", attribute="credit", parent=ncl4_6)

ncl5_12 = Node("DefinedBenefitPensionPlanLiabilitiesNoncurrent", attribute="credit", parent=ncl4_20)
ncl5_13 = Node("OtherPostretirementDefinedBenefitPlanLiabilitiesNoncurrent", attribute="credit", parent=ncl4_20)
ncl5_14 = Node("OtherPostretirementBenefitsPayableNoncurrent", attribute="credit", parent=ncl4_20)


"""
Commitments and Contingencies
"""

cc = Node("CommitmentsAndContingencies", attribute="credit")

# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------

"""
Banks and financial services balance sheet items
"""

#ca3_1 # Cash due from banks
#ca3_2 # Deposits from other banks

"""
Banks - Assets
"""

#Level 1
ba1_1 = Node("FederalFundsSoldAndSecuritiesPurchasedUnderAgreementsToResell", attribute = "debit") #Securities Purchased Under Agreements to Resell
ba1_12 = Node("CarryingValueOfFederalFundsSoldSecuritiesPurchasedUnderAgreementsToResellAndDepositsPaidForSecuritiesBorrowed", attribute = "debit", parent = ba1_1)
ba1_13 = Node("CarryingValueOfSecuritiesPurchasedUnderAgreementsToResellAndDepositsPaidForSecuritiesBorrowed", attribute = "debit", parent = ba1_12)



ba1_4 = Node("NotesReceivableNet", attribute = "debit") #Loans and Leases, Net
ba1_5 = Node("FinancingReceivableExcludingAccruedInterestAfterAllowanceForCreditLoss", attribute = "debit", parent = ba1_4) #Loans and Leases

ba1_3 = Node("SecuritiesBorrowed", attribute = "debit") # Securities Borrowed

ba1_14 = Node("MarketableSecurities", attribute = "debit") #Marketable Securities

ba1_6 = Node("TradingSecurities", attribute = "debit", parent = ba1_14) #Trading Securities

ba1_15 = Node("DerivativeAssets", attribute = "debit", parent = ba1_14) #Derivative Assets
ba1_15_1 = Node("DerivativeFinancialAssets", attribute = "debit", parent = ba1_15) #Derivative Assets

ba1_7 = Node("AvailableForSaleSecuritiesDebtSecurities", attribute = "debit", parent = ba1_14) #Available-For-Sale Securities
ba1_8 = Node("DebtSecuritiesAvailableForSaleExcludingAccruedInterest", attribute = "debit", parent = ba1_7) #Available-For-Sale Securities

ba1_9 = Node("DebtSecuritiesHeldToMaturityExcludingAccruedInterestAfterAllowanceForCreditLoss", attribute = "debit", parent = ba1_14) #Held-To-Maturity Securities
ba1_17 = Node("DebtSecuritiesHeldToMaturityAmortizedCostAfterAllowanceForCreditLoss", attribute = "debit", parent = ba1_9)

ba1_10 = Node("PropertyPlantAndEquipmentAndFinanceLeaseRightOfUseAssetAfterAccumulatedDepreciationAndAmortization", attribute = "debit") #Premises and Equipment

ba1_11 = Node("OtherAssets", attribute = "debit")

ba1_16 = Node("AccountsReceivableNet", attribute = "debit") # Accounts Receivables

ba1_18 = Node("FinancialInstrumentsOwnedAtFairValue", attribute = "debit") #Financial Instruments Owned

#Level 2
ba2_22 = Node("LoansAndAdvancesToCustomers", attribute = "debit", parent = ba1_4)
ba2_23 = Node("LoansAndAdvancesToBanks", attribute = "debit", parent = ba1_4)
ba2_24 = Node("CorporateLoans", attribute = "debit", parent = ba2_22)
ba2_25 = Node("ConsumerLoans", attribute = "debit", parent = ba2_22)
ba2_26 = Node("LoansToGovernment", attribute = "debit", parent = ba2_22)


ba2_1 = Node("FederalFundsSold", attribute = "debit", parent = ba1_13)
ba2_2 = Node("SecuritiesPurchasedUnderAgreementsToResell", attribute = "debit", parent = ba1_13)

ba2_3 = Node("FinancingReceivableAllowanceForCreditLossExcludingAccruedInterest", attribute = "credit", parent = ba1_5)
ba2_4 = Node("FinancingReceivableAllowanceForCreditLosses", attribute = "credit", parent = ba2_3)

ba2_5 = Node("FinancingReceivableExcludingAccruedInterestBeforeAllowanceForCreditLoss", attribute = "debit", parent = ba1_5)
ba2_6 = Node("NotesReceivableGross", attribute = "debit", parent = ba2_5) # Gross loans

ba2_7 = Node("TradingSecuritiesDebt", attribute = "debit", parent = ba1_6)
ba2_8 = Node("EquitySecuritiesFvNiCurrentAndNoncurrent", attribute = "debit", parent = ba1_6)

ba2_9 = Node("DebtSecuritiesHeldToMaturityAllowanceForCreditLossExcludingAccruedInterest", attribute = "credit", parent = ba1_17)
ba2_22 = Node("DebtSecuritiesHeldToMaturityAllowanceForCreditLoss", attribute = "credit", parent = ba2_9)
ba2_10 = Node("DebtSecuritiesHeldToMaturityExcludingAccruedInterestBeforeAllowanceForCreditLoss", attribute = "debit", parent = ba1_17)
ba2_21 = Node("HeldToMaturitySecurities", attribute = "debit", parent = ba2_10)

ba2_11 = Node("FinanceLeaseRightOfUseAsset", attribute = "credit", parent = ba1_10)
ba2_12 = Node("PropertyPlantAndEquipmentNet", attribute = "debit", parent = ba1_10)
ba2_12_1 = Node("PropertyPlantAndEquipment", attribute = "debit", parent = ba2_12)

ba2_13 = Node("ReceivablesFromCustomers", attribute = "debit", parent = ba1_16)
ba2_20 = Node("ContractWithCustomerReceivableAfterAllowanceForCreditLossCurrent", attribute = "debit", parent = ba2_13)
ba2_14 = Node("ReceivablesFromBrokersDealersAndClearingOrganizations", attribute = "debit", parent = ba1_16)
ba2_15 = Node("AccountsReceivableFromSecuritization", attribute = "debit", parent = ba1_16)
ba2_16 = Node("AccountsReceivableBilledForLongTermContractsOrPrograms", attribute = "debit", parent = ba1_16)
ba2_17 = Node("NotesReceivableGross", attribute = "debit", parent = ba1_16)
ba2_18 = Node("AccruedInvestmentIncomeReceivable", attribute = "debit", parent = ba1_16)
ba2_19 = Node("PremiumsReceivableAtCarryingValue", attribute = "debit", parent = ba1_16)
ba2_37 = Node("OtherReceivables", attribute = "debit", parent = ba1_16)
ba2_30 = Node("TradeAndOtherReceivablesDueFromRelatedParties", attribute = "debit", parent = ba1_16)
ba2_31 = Node("TradeReceivables", attribute = "debit", parent = ba1_16)

ba2_32 = Node("FinancialAssets", attribute = "debit", parent = ba1_18)
"""
Banks - Liabilities
"""
#Level 1
bl1_1 = Node("FederalFundsPurchasedAndSecuritiesSoldUnderAgreementsToRepurchase", attribute = "credit") #Securities Loaned
bl1_2 = Node("CarryingValueOfSecuritiesSoldUnderRepurchaseAgreementsAndDepositsReceivedForSecuritiesLoaned", attribute = "credit", parent = bl1_1)

bl1_3 = Node("Deposits", attribute = "credit") #Total Deposits

bl1_4 = Node("TradingLiabilities", attribute = "credit") #Trading Liabilities

bl1_5 = Node("ShortTermBorrowings", attribute = "credit") #Short-Term Debt

bl1_6 = Node("LongTermDebtAndCapitalLeaseObligationsIncludingCurrentMaturities", attribute = "credit") #Long-Term Debt

bl1_8 = Node("AccountsPayableAndAccruedLiabilitiesCurrentAndNoncurrent", attribute = "credit") # Accounts Payable and Accrued Liabilities

bl1_9 = Node("FinancialInstrumentsSoldNotYetPurchasedAtFairValue", attribute = "credit") # Short-sales

bl1_10 = Node("Other", attribute = "credit")

#Level 2
bl2_1 = Node("FederalFundsPurchased", attribute = "credit", parent = bl1_2)
bl2_2 = Node("SecuritiesSoldUnderAgreementsToRepurchase", attribute = "credit", parent = bl1_2)

bl2_3 = Node("LongTermDebt", attribute = "credit", parent = bl1_6)

bl2_4 = Node("AccountsPayableCurrentAndNoncurrent", attribute = "credit", parent = bl1_8)
bl2_5 = Node("AccruedLiabilitiesCurrentAndNoncurrent", attribute = "credit", parent = bl1_8)

bl2_6 = Node("DepositsFromBanks", attribute = "credit", parent = bl1_3)
bl2_7 = Node("DepositsFromCustomers", attribute = "credit", parent = bl1_3)

#Level 3


bl3_1 = Node("AccruedLiabilitiesAndOtherLiabilities", attribute = "credit", parent = bl2_5)
bl3_2 = Node("EmployeeRelatedLiabilitiesCurrentAndNoncurrent", attribute = "credit", parent = bl2_5)
bl3_3 = Node("OtherAccruedLiabilitiesCurrentAndNoncurrent", attribute = "credit", parent = bl2_5)

bl3_4 = Node("PayablesToCustomers", attribute = "credit", parent = bl2_4)
bl3_5 = Node("AccountsPayableTradeCurrentAndNoncurrent", attribute = "credit", parent = bl2_4)
bl3_6 = Node("AccountsPayableInterestBearingCurrentAndNoncurrent", attribute = "credit", parent = bl2_4)

#Level 4

bl4_1 = Node("AccruedEmployeeBenefitsCurrentAndNoncurrent", attribute = "credit", parent = bl3_2)
bl4_2 = Node("AccruedSalariesCurrentAndNoncurrent", attribute = "credit", parent = bl3_2)
bl4_3 = Node("WorkersCompensationLiabilityCurrentAndNoncurrent", attribute = "credit", parent = bl3_2)
bl4_4 = Node("OtherEmployeeRelatedLiabilitiesCurrentAndNoncurrent", attribute = "credit", parent = bl3_2)
