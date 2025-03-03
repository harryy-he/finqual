from node_tree import Node

"""
Temporary Equity
"""

te = Node("TemporaryEquityCarryingAmountIncludingPortionAttributableToNoncontrollingInterests", attribute="credit")

# Level 1

te1_1 = Node("TemporaryEquityCarryingAmountAttributableToParent", attribute="credit", parent=te)
te1_2 = Node("RedeemableNoncontrollingInterestEquityCarryingAmount", attribute="credit", parent=te)

# Level 2
te1_3 = Node("RedeemableNoncontrollingInterestEquityCommonCarryingAmount", attribute="credit", parent=te1_2)
te1_4 = Node("RedeemableNoncontrollingInterestEquityPreferredCarryingAmount", attribute="credit", parent=te1_2)
te1_5 = Node("RedeemableNoncontrollingInterestEquityOtherCarryingAmount", attribute="credit", parent=te1_2)

"""
Stockholder's Equity
"""

se = Node("StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest", attribute="credit")
se1 = Node("Equity", attribute="credit", parent=se)
# Level 1

se1_1 = Node("StockholdersEquity", attribute="credit", parent=se1)
se1_2 = Node("MinorityInterest", attribute="credit", parent=se1)

# Level 2
se2_1 = Node("PreferredStockValue", attribute="credit", parent=se1_1)
se2_2 = Node("PreferredStockSharesSubscribedButUnissuedSubscriptionsReceivable", attribute="debit", parent=se1_1)
se2_3 = Node("CommonStockValue", attribute="credit", parent=se1_1)
se2_27 = Node("IssuedCapital", attribute="credit", parent=se2_3) #IFRS
se2_4 = Node("TreasuryStockValue", attribute="debit", parent=se1_1)
se2_5 = Node("CommonStockHeldBySubsidiary", attribute="debit", parent=se1_1)
se2_6 = Node("CommonStockShareSubscribedButUnissuedSubscriptionsReceivable", attribute="debit", parent=se1_1)
se2_7 = Node("CommonStockSharesSubscriptions", attribute="credit", parent=se1_1)
se2_8 = Node("AdditionalPaidInCapital", attribute="credit", parent=se1_1)
se2_28 = Node("SharePremium", attribute="credit", parent=se2_8) #IFRS
se2_9 = Node("TreasuryStockDeferredEmployeeStockOwnershipPlan", attribute="credit", parent=se1_1)
se2_10 = Node("DeferredCompensationEquity", attribute="debit", parent=se1_1)
se2_11 = Node("AccumulatedOtherComprehensiveIncomeLossNetOfTax", attribute="credit", parent=se1_1)
se2_30 = Node("AccumulatedOtherComprehensiveIncome", attribute="credit", parent=se2_11)
se2_12 = Node("RetainedEarningsAccumulatedDeficit", attribute="credit", parent=se1_1)
se2_26 = Node("RetainedEarnings", attribute="credit", parent=se2_12) #IFRS
se2_13 = Node("UnearnedESOPShares", attribute="debit", parent=se1_1)
se2_14 = Node("OtherAdditionalCapital", attribute="credit", parent=se1_1)
se2_29 = Node("OtherReserves", attribute="credit", parent=se2_14) #IFRS
se2_15 = Node("ReceivableFromOfficersAndDirectorsForIssuanceOfCapitalStock", attribute="debit", parent=se1_1)
se2_16 = Node("ReceivableFromShareholdersOrAffiliatesForIssuanceOfCapitalStock", attribute="debit", parent=se1_1)
se2_17 = Node("WarrantsAndRightsOutstanding", attribute="credit", parent=se1_1)
se2_18 = Node("StockholdersEquityNoteSubscriptionsReceivable", attribute="debit", parent=se1_1)

se2_19 = Node("MinorityInterestInLimitedPartnerships", attribute="credit", parent=se1_2)
se2_20 = Node("MinorityInterestInOperatingPartnerships", attribute="credit", parent=se1_2)
se2_21 = Node("MinorityInterestInPreferredUnitHolders", attribute="credit", parent=se1_2)
se2_22 = Node("MinorityInterestInJointVentures", attribute="credit", parent=se1_2)
se2_23 = Node("OtherMinorityInterests", attribute="credit", parent=se1_2)
se2_24 = Node("NonredeemableNoncontrollingInterest", attribute="credit", parent=se1_2)
se2_25 = Node("NoncontrollingInterestInVariableInterestEntity", attribute="credit", parent=se1_2)

# Level 3
se3_1 = Node("TreasuryStockCommonValue", attribute="debit", parent=se2_4)
se3_2 = Node("TreasuryStockPreferredValue", attribute="debit", parent=se2_4)

se3_3 = Node("AdditionalPaidInCapitalCommonStock", attribute="credit", parent=se2_8)
se3_4 = Node("AdditionalPaidInCapitalPreferredStock", attribute="credit", parent=se2_8)

se3_5 = Node("AccumulatedOtherComprehensiveIncomeLossForeignCurrencyTranslationAdjustmentNetOfTax", attribute="credit",
             parent=se2_11)
se3_6 = Node("AccumulatedOtherComprehensiveIncomeLossAvailableForSaleSecuritiesAdjustmentNetOfTax", attribute="credit",
             parent=se2_11)
se3_7 = Node("AociLossCashFlowHedgeCumulativeGainLossAfterTax", attribute="credit", parent=se2_11)
se3_8 = Node("AccumulatedOtherComprehensiveIncomeLossDefinedBenefitPensionAndOtherPostretirementPlansNetOfTax",
             attribute="debit", parent=se2_11)
se3_9 = Node("AccumulatedOtherComprehensiveIncomeLossFinancialLiabilityFairValueOptionAfterTax", attribute="credit",
             parent=se2_11)
se3_10 = Node("AociDerivativeQualifyingAsHedgeExcludedComponentAfterTax", attribute="credit", parent=se2_11)

se3_11 = Node("RetainedEarningsAppropriated", attribute="credit", parent=se2_26)
se3_12 = Node("RetainedEarningsUnappropriated", attribute="credit", parent=se2_26)

# Level 4
se4_1 = Node("DefinedBenefitPlanAccumulatedOtherComprehensiveIncomeNetGainsLossesAfterTax", attribute="credit",
             parent=se3_8)
se4_2 = Node("DefinedBenefitPlanAccumulatedOtherComprehensiveIncomeNetPriorServiceCostCreditAfterTax",
             attribute="debit", parent=se3_8)
se4_3 = Node("DefinedBenefitPlanAccumulatedOtherComprehensiveIncomeNetTransitionAssetsObligationsAfterTax",
             attribute="credit", parent=se3_8)

"""
Cash and Cash Equivalents - Cashflow
"""
# Level 0
cce = Node("CashAndCashEquivalentsPeriodIncreaseDecrease", attribute="debit")


# End-cash position
cce1 = Node("CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents", attribute="debit")
cce2 = Node("CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalentsIncludingDisposalGroupAndDiscontinuedOperations", attribute="debit", parent=cce1)
cce3 = Node("CashAndCashEquivalentsAtCarryingValue", attribute="debit", parent=cce2)
cce4 = Node("CashAndCashEquivalents", attribute="debit", parent=cce3)

# Level 1

cce1_1 = Node("EffectOfExchangeRateOnCashCashEquivalentsRestrictedCashAndRestrictedCashEquivalentsIncludingDisposalGroupAndDiscontinuedOperations", attribute="debit", parent=cce)
cce1_3 = Node("EffectOfExchangeRateOnCashAndCashEquivalents", attribute="debit", parent=cce1_1)
cce1_4 = Node("EffectOfExchangeRateChangesOnCashAndCashEquivalents", attribute="debit", parent=cce1_3)

cce1_2 = Node("CashAndCashEquivalentsPeriodIncreaseDecreaseExcludingExchangeRateEffect", attribute="debit", parent=cce)

# Level 2

cce2_1 = Node("EffectOfExchangeRateOnCashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents", attribute="debit", parent=cce1_4)
cce2_2 = Node("EffectOfExchangeRateOnCashCashEquivalentsRestrictedCashAndRestrictedCashEquivalentsDisposalGroupIncludingDiscontinuedOperations", attribute="debit", parent=cce2_1)

cce2_3 = Node("NetCashProvidedByUsedInOperatingActivities", attribute="debit", parent=cce1_2)
cce2_3_1 = Node("CashFlowsFromUsedInOperatingActivities", attribute="debit", parent=cce2_3)
cce2_4 = Node("NetCashProvidedByUsedInInvestingActivities", attribute="debit", parent=cce1_2)
cce2_4_1 = Node("CashFlowsFromUsedInInvestingActivities", attribute="debit", parent=cce2_4)
cce2_5 = Node("NetCashProvidedByUsedInFinancingActivities", attribute="debit", parent=cce1_2)
cce2_5_1 = Node("CashFlowsFromUsedInFinancingActivities", attribute="debit", parent=cce2_5)

# Level 3

cce3_7 = Node("EffectOfExchangeRateOnCashAndCashEquivalentsContinuingOperations", attribute="debit", parent=cce2_2)
cce3_8 = Node("EffectOfExchangeRateOnCashAndCashEquivalentsDiscontinuedOperations", attribute="debit", parent=cce2_2)

cce3_1 = Node("ProfitLoss", attribute="debit", parent=cce2_3_1)
cce3_2 = Node("AdjustmentsToReconcileNetIncomeLossToCashProvidedByUsedInOperatingActivities", attribute="debit",
              parent=cce2_3_1)

cce3_3 = Node("NetCashProvidedByUsedInInvestingActivitiesContinuingOperations", attribute="debit", parent=cce2_4_1)
cce3_4 = Node("CashProvidedByUsedInInvestingActivitiesDiscontinuedOperations", attribute="debit", parent=cce2_4_1)

cce3_5 = Node("NetCashProvidedByUsedInFinancingActivitiesContinuingOperations", attribute="debit", parent=cce2_5_1)
cce3_6 = Node("CashProvidedByUsedInFinancingActivitiesDiscontinuedOperations", attribute="debit", parent=cce2_5_1)

# Level 4

cce4_1 = Node("IncomeLossIncludingPortionAttributableToNoncontrollingInterest", attribute="credit", parent=cce3_1)
cce4_2 = Node("IncomeTaxExpenseBenefitContinuingOperationsDiscontinuedOperationsExtraordinaryItems", attribute="debit",
              parent=cce3_1)

cce4_3 = Node("AdjustmentsNoncashItemsToReconcileNetIncomeLossToCashProvidedByUsedInOperatingActivities", attribute="debit", parent=cce3_2)
cce4_4 = Node("PaymentsForProceedsFromTenantAllowance", attribute="credit", parent=cce3_2)
cce4_5 = Node("PaymentsForProceedsFromOtherDeposits", attribute="credit", parent=cce3_2)
cce4_6 = Node("IncreaseDecreaseInOperatingCapital", attribute="credit", parent=cce3_2)
cce4_7 = Node("OtherOperatingActivitiesCashFlowStatement", attribute="debit", parent=cce3_2)

cce4_8 = Node("PaymentsForProceedsFromProductiveAssets", attribute="credit", parent=cce3_3)

# level 5

cce5_1 = Node("PaymentsToAcquireProductiveAssets", attribute="credit", parent=cce4_8)

cce5_2 = Node("DepreciationDepletionAndAmortization", attribute="debit", parent=cce4_3)
cce5_2_1 = Node("DepreciationAndAmortisationExpense", attribute = "debit", parent = cce5_2) #IFRS
cce5_2_2 = Node("DepreciationAmortisationAndImpairmentLossReversalOfImpairmentLossRecognisedInProfitOrLoss", attribute = "debit", parent = cce5_2_1) #IFRS

# Level 6

cce6_1 = Node("PaymentsToAcquirePropertyPlantAndEquipment", attribute="credit", parent=cce5_1)

cce6_2 = Node("DepreciationAndAmortization", attribute="debit", parent=cce5_2_2)
cce6_3 = Node("Depletion", attribute="debit", parent=cce5_2_2)

# Level 7
cce7_1 = Node("PaymentsToAcquireAndDevelopRealEstate", attribute="credit", parent=cce6_1)
cce7_2 = Node("PaymentsToAcquireFurnitureAndFixtures", attribute="credit", parent=cce6_1)
cce7_3 = Node("PaymentsToAcquireMachineryAndEquipment", attribute="credit", parent=cce6_1)
cce7_4 = Node("PaymentsToAcquireOilAndGasPropertyAndEquipment", attribute="credit", parent=cce6_1)
cce7_5 = Node("PaymentsToExploreAndDevelopOilAndGasProperties", attribute="credit", parent=cce6_1)
cce7_6 = Node("PaymentsToAcquireMiningAssets", attribute="credit", parent=cce6_1)
cce7_7 = Node("PaymentsToAcquireTimberlands", attribute="credit", parent=cce6_1)
cce7_8 = Node("PaymentsToAcquireWaterAndWasteWaterSystems", attribute="credit", parent=cce6_1)
cce7_9 = Node("PaymentsToAcquireOtherPropertyPlantAndEquipment", attribute="credit", parent=cce6_1)

cce7_10 = Node("Depreciation", attribute="debit", parent=cce6_2)
cce7_14 = Node("DepreciationExpense", attribute="debit", parent=cce7_10) #IFRS
cce7_11 = Node("AdjustmentForAmortization", attribute="debit", parent=cce6_2)
cce7_15 = Node("AmortisationExpense", attribute="debit", parent=cce7_11) #IFRS
cce7_12 = Node("AmortizationOfDeferredCharges", attribute="debit", parent=cce6_2)
cce7_13 = Node("OtherDepreciationAndAmortization", attribute="debit", parent=cce6_2)

# Level 8

cce8_1 = Node("PaymentsToAcquireRealEstate", attribute="credit", parent=cce7_1)
cce8_2 = Node("PaymentsToDevelopRealEstateAssets", attribute="credit", parent=cce7_1)
cce8_3 = Node("PaymentsForConstructionInProcess", attribute="credit", parent=cce7_1)

cce8_4 = Node("PaymentsToAcquireOilAndGasProperty", attribute="credit", parent=cce7_4)
cce8_5 = Node("PaymentsToAcquireOilAndGasEquipment", attribute="credit", parent=cce7_4)

cce8_6 = Node("PaymentsToAcquireWaterSystems", attribute="credit", parent=cce7_8)
cce8_7 = Node("PaymentsToAcquireWasteWaterSystems", attribute="credit", parent=cce7_8)

cce8_8 = Node("CostOfGoodsSoldDepreciation", attribute="debit", parent=cce7_14)
cce8_9 = Node("CostOfServicesDepreciation", attribute="debit", parent=cce7_14)
cce8_10 = Node("DepreciationNonproduction", attribute="debit", parent=cce7_14)

cce8_11 = Node("CostOfServicesAmortization", attribute="debit", parent=cce7_15)
cce8_12 = Node("AmortizationOfIntangibleAssets", attribute="debit", parent=cce7_15)
cce8_13 = Node("CostOfGoodsSoldAmortization", attribute="debit", parent=cce7_15)

# Level 9

cce9_1 = Node("PaymentsForDepositsOnRealEstateAcquisitions", attribute="credit", parent=cce8_1)
cce9_2 = Node("PaymentsToAcquireCommercialRealEstate", attribute="credit", parent=cce8_1)
cce9_3 = Node("PaymentsToAcquireBuildings", attribute="credit", parent=cce8_1)
cce9_4 = Node("PaymentsForCapitalImprovements", attribute="credit", parent=cce8_1)
cce9_5 = Node("PaymentsToAcquireResidentialRealEstate", attribute="credit", parent=cce8_1)
cce9_6 = Node("PaymentsToAcquireLand", attribute="credit", parent=cce8_1)
cce9_7 = Node("PaymentsToAcquireLandHeldForUse", attribute="credit", parent=cce8_1)
cce9_8 = Node("PaymentsToAcquireHeldForSaleRealEstate", attribute="credit", parent=cce8_1)
cce9_9 = Node("PaymentsToAcquireOtherRealEstate", attribute="credit", parent=cce8_1)

cce9_10 = Node("", attribute="credit", parent=cce8_1)