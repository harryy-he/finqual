from node_tree import Node

"""
No. of shares
"""
s_b = Node("WeightedAverageNumberOfSharesOutstandingBasic", attribute = "debit")
s_d = Node("WeightedAverageNumberOfDilutedSharesOutstanding", attribute = "debit")

s_b1 = Node("WeightedAverageShares", attribute = "debit", parent = s_b)
s_d1 = Node("AdjustedWeightedAverageShares", attribute = "debit", parent = s_d)
"""
EPS
"""

eps = Node("EarningsPerShareBasic", attribute = "credit")
eps_d = Node("EarningsPerShareDiluted", attribute = "credit")

eps1 = Node("BasicEarningsLossPerShare", attribute = "credit", parent = eps)
eps_d1 = Node("DilutedEarningsLossPerShare", attribute = "credit", parent = eps_d)
"""
Net Income
"""

ni = Node("NetIncomeLoss", attribute="credit")

# Level 1
ni1_1 = Node("ProfitLoss", attribute="credit", parent=ni)

"""
Pre-tax income
"""
pti1 = Node("ProfitLossBeforeTax", attribute="credit", parent=ni1_1) # IFRS
pti = Node("IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest", attribute="credit", parent=pti1)

# Level 1

pti1_1 = Node("IncomeLossFromContinuingOperationsBeforeIncomeTaxesMinorityInterestAndIncomeLossFromEquityMethodInvestments", attribute="credit", parent=pti)

"""
Tax
"""
tax1 = Node("IncomeTaxExpenseContinuingOperations", attribute="debit", parent=ni1_1) #IFRS
tax = Node("IncomeTaxExpenseBenefit", attribute="debit", parent=tax1)

"""
Operating Income
"""
oi1 = Node("ProfitLossFromOperatingActivities", attribute="credit", parent=pti1_1) #IFRS
oi = Node("OperatingIncomeLoss", attribute="credit", parent=oi1)

"""
Gross Profit
"""
# Level 1
gp = Node("GrossProfit", attribute="credit", parent=oi)

"""
Revenue
"""
rev = Node("Revenues", attribute="credit", parent=gp)

# Level 1

rev1_1 = Node("RevenueFromContractWithCustomerExcludingAssessedTax", attribute="credit", parent=rev)
rev1_2 = Node("RevenueFromContractWithCustomerIncludingAssessedTax", attribute="credit", parent=rev1_1)

rev1_3 = Node("SalesRevenueNet", attribute="credit", parent=rev1_2)
rev1_4 = Node("SalesRevenueGoodsNet", attribute="credit", parent=rev1_3)

rev1_5 = Node("RegulatedAndUnregulatedOperatingRevenue", attribute="credit", parent=rev1_4)

rev1_6 = Node("RevenuesNetOfInterestExpense", attribute="credit", parent=rev1_5)

rev1_7 = Node("Revenue", attribute = "credit", parent = rev1_6) #IFRS

# Level 2

rev2_1 = Node("NoninterestIncome", attribute="credit", parent=rev1_7)
rev2_2 = Node("InterestIncomeExpenseNet", attribute="credit", parent=rev1_7)

"""
Cost of Revenue
"""
cor = Node("CostOfSales", attribute="debit", parent=gp)
cor1 = Node("CostOfRevenue", attribute="debit", parent=cor)

# Level 1
cor1_1 = Node("CostOfGoodsAndServicesSold", attribute="debit", parent=cor)
cor1_2 = Node("FinancingInterestExpense", attribute="debit", parent=cor)
cor1_3 = Node("ProvisionForLoanLeaseAndOtherLosses", attribute="debit", parent=cor)
cor1_4 = Node("PolicyholderBenefitsAndClaimsIncurredNet", attribute="debit", parent=cor)
cor1_5 = Node("LiabilityForFuturePolicyBenefitsPeriodExpense", attribute="debit", parent=cor)
cor1_6 = Node("InterestCreditedToPolicyholdersAccountBalances", attribute="debit", parent=cor)
cor1_7 = Node("PolicyholderDividends", attribute="debit", parent=cor)
cor1_8 = Node("DeferredSalesInducementsAmortizationExpense", attribute="debit", parent=cor)
cor1_9 = Node("PresentValueOfFutureInsuranceProfitsAmortizationExpense1", attribute="debit", parent=cor)
cor1_10 = Node("AmortizationOfMortgageServicingRightsMSRs", attribute="debit", parent=cor)
cor1_11 = Node("DeferredPolicyAcquisitionCostAmortizationExpense", attribute="debit", parent=cor)
cor1_12 = Node("AmortizationOfValueOfBusinessAcquiredVOBA", attribute="debit", parent=cor)
cor1_13 = Node("OtherCostOfOperatingRevenue", attribute="debit", parent=cor)
cor1_14 = Node("MerchantMarineOperatingDifferentialSubsidy", attribute="debit", parent=cor)

# Level 2
cor2_1 = Node("CostDepreciationAmortizationAndDepletion", attribute="debit", parent=cor1_1)
cor2_2 = Node("CostOfGoodsAndServiceExcludingDepreciationDepletionAndAmortization", attribute="debit", parent=cor1_1)

cor2_3 = Node("ProvisionForOtherCreditLosses", attribute="debit", parent=cor1_3)
cor2_4 = Node("ProvisionForOtherLosses", attribute="debit", parent=cor1_3)
cor2_5 = Node("ProvisionForLoanLossesExpensed", attribute="debit", parent=cor1_3)
cor2_6 = Node("NetInvestmentInLeaseCreditLossExpenseReversal", attribute="debit", parent=cor1_3)

cor2_7 = Node("PolicyholderBenefitsAndClaimsIncurredGross", attribute="debit", parent=cor1_7)

# Level 3
cor3_1 = Node("CostDirectMaterial", attribute="debit", parent=cor2_1)
cor3_2 = Node("CostOfGoodsSoldSalesTypeLease", attribute="debit", parent=cor2_1)
cor3_3 = Node("CostOfGoodsSoldDirectFinancingLease", attribute="debit", parent=cor2_1)
cor3_4 = Node("DirectCostsOfLeasedAndRentedPropertyOrEquipment", attribute="debit", parent=cor2_1)
cor3_5 = Node("CostDirectLabor", attribute="debit", parent=cor2_1)
cor3_6 = Node("CostOfGoodsAndServicesSoldOverhead", attribute="debit", parent=cor2_1)
cor3_7 = Node("CostMaintenance", attribute="debit", parent=cor2_1)
cor3_8 = Node("DirectTaxesAndLicensesCosts", attribute="debit", parent=cor2_1)
cor3_9 = Node("CostOfTrustAssetsSoldToPayExpenses", attribute="debit", parent=cor2_1)
cor3_10 = Node("CostOfPropertyRepairsAndMaintenance", attribute="debit", parent=cor2_1)
cor3_11 = Node("CostOfOtherPropertyOperatingExpense", attribute="debit", parent=cor2_1)
cor3_12 = Node("DirectOperatingCosts", attribute="debit", parent=cor2_1)
cor3_13 = Node("LossOnContracts", attribute="debit", parent=cor2_1)
cor3_14 = Node("AffiliateCosts", attribute="debit", parent=cor2_1)
cor3_15 = Node("InventoryFirmPurchaseCommitmentLoss", attribute="debit", parent=cor2_1)
cor3_16 = Node("ExciseAndSalesTaxes", attribute="debit", parent=cor2_1)
cor3_17 = Node("ProductionRelatedImpairmentsOrCharges", attribute="debit", parent=cor2_1)

cor3_18 = Node("CostOfGoodsAndServicesSoldDepreciationAndAmortization", attribute="debit", parent=cor2_2)
cor3_19 = Node("CostDepletion", attribute="debit", parent=cor2_2)

cor3_20 = Node("PolicyholderBenefitsAndClaimsIncurredGross", attribute="debit", parent=cor2_7)
cor3_21 = Node("ReinsuranceCostsAndRecoveriesNet", attribute="debit", parent=cor2_7)

# Level 4
cor4_1 = Node("CostOfGoodsAndServicesSoldDepreciation", attribute="debit", parent=cor3_18)
cor4_2 = Node("CostOfGoodsAndServicesSoldAmortization", attribute="debit", parent=cor3_18)

cor4_3 = Node("WaterProductionCosts", attribute="debit", parent=cor3_12)
cor4_4 = Node("CostOfPurchasedWater", attribute="debit", parent=cor3_12)
cor4_5 = Node("RecoveryOfDirectCosts", attribute="credit", parent=cor3_12)
cor4_6 = Node("ManufacturingCosts", attribute="debit", parent=cor3_12)
cor4_7 = Node("DirectOperatingMaintenanceSuppliesCosts", attribute="debit", parent=cor3_12)
cor4_8 = Node("OperatingInsuranceAndClaimsCostsProduction", attribute="debit", parent=cor3_12)
cor4_9 = Node("FuelCosts", attribute="debit", parent=cor3_12)
cor4_10 = Node("DirectCommunicationsAndUtilitiesCosts", attribute="debit", parent=cor3_12)
cor4_11 = Node("AircraftRentalAndLandingFees", attribute="debit", parent=cor3_12)
cor4_12 = Node("AircraftMaintenanceMaterialsAndRepairs", attribute="debit", parent=cor3_12)

# Level 5
cor5_1 = Node("DirectOperatingCommunicationsCosts", attribute="debit", parent=cor4_10)

cor5_2 = Node("AircraftRental", attribute="debit", parent=cor4_11)
cor5_3 = Node("LandingFeesAndOtherRentals", attribute="debit", parent=cor4_11)

"""
Operating Expenses
"""
opex1 = Node("NoninterestExpense", attribute = "debit", parent = oi)
opex2 = Node("OperatingExpense", attribute="debit", parent=opex1)
opex = Node("OperatingExpenses", attribute="debit", parent=opex2)

# Level 1
opex1_1 = Node("OperatingCostsAndExpenses", attribute="debit", parent=opex)
opex1_2 = Node("SellingGeneralAndAdministrativeExpense", attribute="debit", parent=opex)
opex1_3 = Node("ProvisionForDoubtfulAccounts", attribute="debit", parent=opex)
opex1_4 = Node("OtherGeneralExpense", attribute="debit", parent=opex)
opex1_5 = Node("GainLossOnDispositionOfAssets1", attribute="debit", parent=opex)
opex1_6 = Node("SalesTypeLeaseSellingProfitLoss", attribute="debit", parent=opex)
opex1_7 = Node("DirectFinancingLeaseSellingLoss", attribute="debit", parent=opex)
opex1_8 = Node("OtherUnderwritingExpense", attribute="debit", parent=opex)
opex1_9 = Node("DemutualizationCostAndExpense", attribute="debit", parent=opex)
opex1_10 = Node("InsuranceCommissions", attribute="debit", parent=opex)
opex1_11 = Node("FloorBrokerageExchangeAndClearanceFees", attribute="debit", parent=opex)
opex1_12 = Node("AdministrativeFeesExpense", attribute="debit", parent=opex)
opex1_13 = Node("IncentiveFeeExpense", attribute="debit", parent=opex)
opex1_14 = Node("ManagementFeeExpense", attribute="debit", parent=opex)

# Level 2
opex2_1 = Node("ResearchAndDevelopmentExpense", attribute="debit", parent=opex1_1)
opex2_2 = Node("DepreciationAndAmortization", attribute="debit", parent=opex1_1)
opex2_3 = Node("ExplorationExpense", attribute="debit", parent=opex1_1)
opex2_4 = Node("CarryingCostsPropertyAndExplorationRights", attribute="debit", parent=opex1_1)
opex2_5 = Node("RecapitalizationCosts", attribute="debit", parent=opex1_1)
opex2_6 = Node("RestructuringSettlementAndImpairmentProvisions", attribute="debit", parent=opex1_1)
opex2_7 = Node("CustodyFees", attribute="debit", parent=opex1_1)
opex2_8 = Node("TrusteeFees", attribute="debit", parent=opex1_1)
opex2_9 = Node("SponsorFees", attribute="debit", parent=opex1_1)
opex2_10 = Node("RoyaltyExpense", attribute="debit", parent=opex1_1)
opex2_11 = Node("AccretionExpenseIncludingAssetRetirementObligations", attribute="debit", parent=opex1_1)
opex2_12 = Node("LoanPortfolioExpense", attribute="debit", parent=opex1_1)
opex2_13 = Node("PreOpeningCosts", attribute="debit", parent=opex1_1)
opex2_14 = Node("GainLossRelatedToLitigationSettlement", attribute="credit", parent=opex1_1)
opex2_15 = Node("MalpracticeLossContingencyClaimsIncurredNet", attribute="debit", parent=opex1_1)
opex2_16 = Node("InsuranceRecoveries", attribute="credit", parent=opex1_1)
opex2_17 = Node("OtherCostAndExpenseOperating", attribute="debit", parent=opex1_1)
opex2_18 = Node("BusinessCombinationIntegrationRelatedCosts", attribute="debit", parent=opex1_1)
opex2_19 = Node("UnsolicitedTenderOfferCosts", attribute="debit", parent=opex1_1)
opex2_20 = Node("ProfessionalAndContractServicesExpense", attribute="debit", parent=opex1_1)

opex2_21 = Node("SellingAndMarketingExpense", attribute="debit", parent=opex1_2)
opex2_22 = Node("GeneralAndAdministrativeExpense", attribute="debit", parent=opex1_2)
opex2_23 = Node("OtherSellingGeneralAndAdministrativeExpense", attribute="debit", parent=opex1_2)

opex2_24 = Node("GainLossOnSaleOfPropertyPlantEquipment", attribute="debit", parent=opex1_5)
opex2_25 = Node("GainLossOnSaleOfBusiness", attribute="debit", parent=opex1_5)
opex2_26 = Node("SaleAndLeasebackTransactionGainLossNet", attribute="debit", parent=opex1_5)
opex2_27 = Node("GainLossOnDispositionOfIntangibleAssets", attribute="debit", parent=opex1_5)
opex2_28 = Node("GainLossOnTerminationOfLease", attribute="debit", parent=opex1_5)
opex2_29 = Node("GainLossOnSaleOfOtherAssets", attribute="debit", parent=opex1_5)

opex2_30 = Node("FloorBrokerage", attribute="debit", parent=opex1_11)
opex2_31 = Node("ExchangeFees", attribute="debit", parent=opex1_11)
opex2_32 = Node("OrderFlowFees", attribute="debit", parent=opex1_11)
opex2_33 = Node("ClearanceFees", attribute="debit", parent=opex1_11)

# Level 3

opex3_1 = Node("ResearchAndDevelopmentExpenseExcludingAcquiredInProcessCost", attribute="debit", parent=opex2_1)
opex3_2 = Node("ResearchAndDevelopmentExpenseSoftwareExcludingAcquiredInProcessCost", attribute="debit", parent=opex2_1)
opex3_3 = Node("ResearchAndDevelopmentAssetAcquiredOtherThanThroughBusinessCombinationWrittenOff", attribute="debit", parent=opex2_1)

opex3_4 = Node("DepreciationNonproduction", attribute="debit", parent=opex2_2)
opex3_5 = Node("DepletionOfOilAndGasProperties", attribute="debit", parent=opex2_2)
opex3_6 = Node("AmortizationOfDeferredCharges", attribute="debit", parent=opex2_2)
opex3_7 = Node("OtherDepreciationAndAmortization", attribute="debit", parent=opex2_2)

opex3_8 = Node("RestructuringCharges", attribute="debit", parent=opex2_6)
opex3_9 = Node("BusinessCombinationAcquisitionRelatedCosts", attribute="debit", parent=opex2_6)
opex3_10 = Node("DefinedBenefitPlanRecognizedNetGainLossDueToSettlements1", attribute="debit", parent=opex2_6)
opex3_11 = Node("InventoryRecallExpense", attribute="debit", parent=opex2_6)
opex3_12 = Node("GainOnBusinessInterruptionInsuranceRecovery", attribute="debit", parent=opex2_6)
opex3_13 = Node("EnvironmentalRemediationExpenseAfterRecovery", attribute="debit", parent=opex2_6)
opex3_14 = Node("AssetImpairmentCharges", attribute="debit", parent=opex2_6)

opex3_15 = Node("AssetRetirementObligationAccretionExpense", attribute="debit", parent=opex2_11)
opex3_16 = Node("AccretionExpense", attribute="debit", parent=opex2_11)

opex3_17 = Node("LitigationSettlementAmountAwardedToOtherParty", attribute="credit", parent=opex2_14)
opex3_18 = Node("LitigationSettlementAmountAwardedFromOtherParty", attribute="debit", parent=opex2_14)
opex3_19 = Node("LitigationSettlementInterest", attribute="debit", parent=opex2_14)
opex3_20 = Node("LitigationSettlementExpense", attribute="debit", parent=opex2_14)

opex3_21 = Node("MalpracticeLossContingencyClaimsIncurredInPeriod", attribute="debit", parent=opex2_15)
opex3_22 = Node("MalpracticeLossContingencyReturnOfPremiums", attribute="credit", parent=opex2_15)
opex3_23 = Node("MalpracticeLossContingencyInsuranceRecoveries", attribute="credit", parent=opex2_15)
opex3_24 = Node("MalpracticeLossContingencyClaimsIncurredInPriorPeriods", attribute="debit", parent=opex2_15)

opex3_25 = Node("SellingExpense", attribute="debit", parent=opex2_21)
opex3_26 = Node("SalesCommissionsAndFees", attribute="debit", parent=opex2_21)
opex3_27 = Node("MarketingAndAdvertisingExpense", attribute="debit", parent=opex2_21)
opex3_28 = Node("FranchisorCosts", attribute="debit", parent=opex2_21)
opex3_29 = Node("ProductWarrantyExpense", attribute="debit", parent=opex2_21)
opex3_30 = Node("OtherSellingAndMarketingExpense", attribute="debit", parent=opex2_21)

opex3_31 = Node("AllocatedShareBasedCompensationExpense", attribute="debit", parent=opex2_22)
opex3_32 = Node("SalariesWagesAndOfficersCompensation", attribute="debit", parent=opex2_22)
opex3_33_1 = Node("LaborAndRelatedExpense", attribute="debit", parent=opex2_22)
opex3_33 = Node("OtherLaborRelatedExpenses", attribute="debit", parent=opex3_33_1)
opex3_34 = Node("ProfessionalFees", attribute="debit", parent=opex2_22)
opex3_35 = Node("BusinessDevelopment", attribute="debit", parent=opex2_22)
opex3_36 = Node("GeneralInsuranceExpense", attribute="debit", parent=opex2_22)
opex3_37 = Node("RealEstateInsurance", attribute="debit", parent=opex2_22)
opex3_38 = Node("CommunicationsInformationTechnologyAndOccupancy", attribute="debit", parent=opex2_22)
opex3_39 = Node("OperatingLeaseExpense", attribute="debit", parent=opex2_22)
opex3_40 = Node("TravelAndEntertainmentExpense", attribute="debit", parent=opex2_22)
opex3_41 = Node("SuppliesAndPostageExpense", attribute="debit", parent=opex2_22)
opex3_42 = Node("InsuranceTax", attribute="debit", parent=opex2_22)
opex3_43 = Node("TaxesExcludingIncomeAndExciseTaxes", attribute="debit", parent=opex2_22)
opex3_44 = Node("OtherGeneralAndAdministrativeExpense", attribute="debit", parent=opex2_22)
opex3_45 = Node("LossContingencyLossInPeriod", attribute="debit", parent=opex2_22)

# Level 4
opex4_1 = Node("AmortizationOfAcquisitionCosts", attribute="debit", parent=opex3_6)
opex4_2 = Node("AmortizationOfIntangibleAssets", attribute="debit", parent=opex3_6)
opex4_3 = Node("AmortizationOfDeferredSalesCommissions", attribute="debit", parent=opex3_6)
opex4_4 = Node("AmortizationOfRegulatoryAsset", attribute="debit", parent=opex3_6)
opex4_5 = Node("FinanceLeaseRightOfUseAssetAmortization", attribute="debit", parent=opex3_6)
opex4_6 = Node("AmortizationOfPowerContractsEmissionCredits", attribute="debit", parent=opex3_6)
opex4_7 = Node("AmortizationOfNuclearFuelLease", attribute="debit", parent=opex3_6)
opex4_8 = Node("AmortizationOfAdvanceRoyalty", attribute="debit", parent=opex3_6)
opex4_9 = Node("AmortizationOfDeferredPropertyTaxes", attribute="debit", parent=opex3_6)
opex4_10 = Node("AmortizationOfRateDeferral", attribute="debit", parent=opex3_6)
opex4_11 = Node("AmortizationOfDeferredHedgeGains", attribute="debit", parent=opex3_6)
opex4_12 = Node("AmortizationAndDepreciationOfDecontaminatingAndDecommissioningAssets", attribute="debit", parent=opex3_6)
opex4_13 = Node("OtherAmortizationOfDeferredCharges", attribute="debit", parent=opex3_6)

opex4_14 = Node("BusinessExitCosts1", attribute="debit", parent=opex3_8)
opex4_15 = Node("SeveranceCosts1", attribute="debit", parent=opex3_8)
opex4_16 = Node("OtherRestructuringCosts", attribute="debit", parent=opex3_8)

opex4_17 = Node("GoodwillAndIntangibleAssetImpairment", attribute="debit", parent=opex3_14)
opex4_18 = Node("EquityMethodInvestmentOtherThanTemporaryImpairment", attribute="debit", parent=opex3_14)
opex4_19 = Node("ImpairmentLossesRelatedToRealEstatePartnerships", attribute="debit", parent=opex3_14)
opex4_20 = Node("SalesTypeLeaseImpairmentLoss", attribute="debit", parent=opex3_14)
opex4_21 = Node("DirectFinancingLeaseImpairmentLoss", attribute="debit", parent=opex3_14)
opex4_22 = Node("ImpairmentOfLeasehold", attribute="debit", parent=opex3_14)
opex4_23 = Node("TangibleAssetImpairmentCharges", attribute="debit", parent=opex3_14)
opex4_24 = Node("AffordableHousingProjectInvestmentWriteDownAmount", attribute="debit", parent=opex3_14)

opex4_25 = Node("LegalFees", attribute="debit", parent=opex3_20)

opex4_26 = Node("EnvironmentalRemediationExpense", attribute="debit", parent=opex3_13)
opex4_27 = Node("EnvironmentalCostsRecognizedRecoveryCreditedToExpense", attribute="credit", parent=opex3_13)

opex4_28 = Node("MarketingExpense", attribute="debit", parent=opex3_27)
opex4_29 = Node("AdvertisingExpense", attribute="debit", parent=opex3_27)

opex4_30 = Node("CostsOfFranchisorOwnedOutlets", attribute="debit", parent=opex3_28)
opex4_31 = Node("CostsOfFranchisedOutlets", attribute="debit", parent=opex3_28)

opex4_32 = Node("CommunicationsAndInformationTechnology", attribute="debit", parent=opex3_38)
opex4_33 = Node("OccupancyNet", attribute="debit", parent=opex3_38)

opex4_34 = Node("SuppliesExpense", attribute="debit", parent=opex3_41)
opex4_35 = Node("PostageExpense", attribute="debit", parent=opex3_41)

opex4_36 = Node("RealEstateTaxExpense", attribute="debit", parent=opex3_43)
opex4_37 = Node("ProductionTaxExpense", attribute="debit", parent=opex3_43)
opex4_38 = Node("PumpTaxes", attribute="debit", parent=opex3_43)
opex4_39 = Node("TaxesOther", attribute="debit", parent=opex3_43)

"""
Nonoperating Income
"""
noi = Node("NonoperatingIncomeExpense", attribute="credit", parent=pti1_1)

# Level 1
noi1_1 = Node("InvestmentIncomeNonoperating", attribute="credit", parent=noi)
noi1_2 = Node("GainLossOnContractTermination", attribute="credit", parent=noi)
noi1_3 = Node("GainLossOnCondemnation", attribute="credit", parent=noi)
noi1_4 = Node("LossFromCatastrophes", attribute="debit", parent=noi)
noi1_5 = Node("PublicUtilitiesAllowanceForFundsUsedDuringConstructionAdditions", attribute="credit", parent=noi)
noi1_6 = Node("ForeignCurrencyTransactionGainLossBeforeTax", attribute="credit", parent=noi)
noi1_7 = Node("SalesTypeLeaseInitialDirectCostExpenseCommencement", attribute="debit", parent=noi)
noi1_8 = Node("OperatingLeaseInitialDirectCostExpenseOverTerm", attribute="debit", parent=noi)
noi1_9 = Node("GainLossOnSaleOfLeasedAssetsNetOperatingLeases", attribute="credit", parent=noi)
noi1_10 = Node("GainsLossesOnSalesOfOtherRealEstate", attribute="credit", parent=noi)
noi1_11 = Node("BankOwnedLifeInsuranceIncome", attribute="credit", parent=noi)
noi1_12 = Node("RealEstateInvestmentPartnershipRevenue", attribute="credit", parent=noi)
noi1_13 = Node("ConversionGainsAndLossesOnForeignInvestments", attribute="credit", parent=noi)
noi1_14 = Node("ProfitLossFromRealEstateOperations", attribute="credit", parent=noi)
noi1_15 = Node("MortgageServicingRightsMSRImpairmentRecovery", attribute="credit", parent=noi)
noi1_16 = Node("DebtInstrumentConvertibleBeneficialConversionFeature", attribute="credit", parent=noi)
noi1_17 = Node("PublicUtilitiesAllowanceForFundsUsedDuringConstructionCapitalizedCostOfEquity", attribute="credit", parent=noi)
noi1_18 = Node("NetPeriodicDefinedBenefitsExpenseReversalOfExpenseExcludingServiceCostComponent", attribute="debit", parent=noi)
noi1_19 = Node("OtherNonoperatingIncomeExpense", attribute="credit", parent=noi)
noi1_20 = Node("UnusualOrInfrequentItemNetGainLoss", attribute="debit", parent=noi)

# Level 2

noi2_1 = Node("NonoperatingGainsLosses", attribute="credit", parent=noi1_1)
noi2_2 = Node("RoyaltyIncomeNonoperating", attribute="credit", parent=noi1_1)
noi2_3 = Node("RentalIncomeNonoperating", attribute="credit", parent=noi1_1)
noi2_4 = Node("DevelopmentProfitsNonoperating", attribute="credit", parent=noi1_1)
noi2_5 = Node("RecoveryStrandedCosts", attribute="debit", parent=noi1_1)
noi2_6 = Node("LeveragedLeasesIncomeStatementNetIncomeFromLeveragedLeases", attribute="credit", parent=noi1_1)
noi2_7 = Node("InvestmentIncomeNet", attribute="credit", parent=noi1_1)

noi2_8 = Node("ForeignCurrencyTransactionGainLossRealized", attribute="credit", parent=noi1_6)
noi2_9 = Node("ForeignCurrencyTransactionGainLossUnrealized", attribute="credit", parent=noi1_6)

noi2_10 = Node("OtherNonoperatingIncome", attribute="credit", parent=noi1_19)
noi2_11 = Node("OtherNonoperatingExpense", attribute="debit", parent=noi1_19)

noi2_12 = Node("DiscontinuedApplicationOfSpecializedAccountingForRegulatedOperations", attribute="credit", parent=noi1_20)
noi2_13 = Node("UnusualOrInfrequentItemGainGross", attribute="credit", parent=noi1_20)
noi2_14 = Node("UnusualOrInfrequentItemNetOfInsuranceProceeds", attribute="debit", parent=noi1_20)

# Level 3

noi3_1 = Node("GainLossOnInvestments", attribute="credit", parent=noi2_1)
noi3_2 = Node("VentureCapitalGainsLossesNet", attribute="credit", parent=noi2_1)
noi3_3 = Node("DisposalGroupNotDiscontinuedOperationGainLossOnDisposal", attribute="credit", parent=noi2_1)
noi3_4 = Node("GainLossOnSaleOfStockInSubsidiaryOrEquityMethodInvestee", attribute="credit", parent=noi2_1)
noi3_5 = Node("DeconsolidationGainOrLossAmount", attribute="credit", parent=noi2_1)
noi3_6 = Node("GainLossOnSaleOfPreviouslyUnissuedStockBySubsidiaryOrEquityInvesteeNonoperatingIncome", attribute="credit", parent=noi2_1)
noi3_7 = Node("GainLossOnSaleOfInterestInProjects", attribute="credit", parent=noi2_1)
noi3_8 = Node("GainLossOnDerivativeInstrumentsNetPretax", attribute="credit", parent=noi2_1)
noi3_9 = Node("BusinessCombinationBargainPurchaseGainRecognizedAmount", attribute="credit", parent=noi2_1)
noi3_10 = Node("OtherNonoperatingGainsLosses", attribute="credit", parent=noi2_1)

noi3_11 = Node("LeveragedLeasesIncomeStatementIncomeFromLeveragedLeases", attribute="credit", parent=noi2_6)
noi3_12 = Node("LeveragedLeasesIncomeStatementIncomeTaxExpenseOnLeveragedLeases", attribute="debit", parent=noi2_6)
noi3_13 = Node("LeveragedLeasesIncomeStatementInvestmentTaxCreditRecognizedOnLeveragedLeases", attribute="credit", parent=noi2_6)

noi3_14 = Node("InvestmentIncomeInterestAndDividend", attribute="credit", parent=noi2_6)
noi3_15 = Node("InvestmentIncomeNetAmortizationOfDiscountAndPremium", attribute="credit", parent=noi2_6)
noi3_16 = Node("InvestmentIncomeInvestmentExpense", attribute="debit", parent=noi2_6)

noi3_17 = Node("OtherNonoperatingAssetRelatedIncome", attribute="credit", parent=noi2_10)

noi3_18 = Node("UnusualOrInfrequentItemInsuranceProceeds", attribute="credit", parent=noi2_14)
noi3_19 = Node("UnusualOrInfrequentItemLossGross", attribute="debit", parent=noi2_14)

# Level 4

noi4_1 = Node("EquityMethodInvestmentRealizedGainLossOnDisposal", attribute="credit", parent=noi3_4)
noi4_2 = Node("GainOrLossOnSaleOfStockInSubsidiary", attribute="credit", parent=noi3_4)

noi4_3 = Node("GainOrLossOnSaleOfPreviouslyUnissuedStockBySubsidiary", attribute="credit", parent=noi3_6)
noi4_4 = Node("GainOrLossOnSaleOfPreviouslyUnissuedStockByEquityInvestee", attribute="credit", parent=noi3_6)

noi4_5 = Node("GainLossFromPriceRiskManagementActivity", attribute="credit", parent=noi3_8)
noi4_6 = Node("GainLossOnOilAndGasHedgingActivity", attribute="credit", parent=noi3_8)
noi4_7 = Node("DerivativeInstrumentsNotDesignatedAsHedgingInstrumentsGainLossNet", attribute="credit", parent=noi3_8)

noi4_8 = Node("InvestmentIncomeInterest", attribute="credit", parent=noi3_14)
noi4_9 = Node("InvestmentIncomeDividend", attribute="credit", parent=noi3_14)

noi4_10 = Node("InvestmentIncomeAmortizationOfDiscount", attribute="credit", parent=noi3_15)
noi4_11 = Node("InvestmentIncomeAmortizationOfPremium", attribute="credit", parent=noi3_15)

# Level 5

noi5_1 = Node("GainLossOnInterestRateDerivativeInstrumentsNotDesignatedAsHedgingInstruments", attribute="credit", parent=noi4_7)
noi5_2 = Node("GainLossOnDerivativeInstrumentsHeldForTradingPurposesNet", attribute="credit", parent=noi4_7)

noi5_3 = Node("InterestIncomeRelatedParty", attribute="credit", parent=noi4_8)

"""
Costs and Expenses
"""

ce = Node("CostsAndExpenses", attribute="credit")

"""
Net Interest Income/Expense
"""

nii = Node("InterestRevenueExpenseNet", attribute="credit")
nii1_1 = Node("InterestIncomeExpenseNet", attribute="credit", parent=nii)

"""
Interest and Debt Expense
"""

ide = Node("InterestAndDebtExpense", attribute="debit", parent=pti1_1)

# Level 1

ide1_1 = Node("InterestExpense", attribute="debit", parent=ide)
ide1_2 = Node("GainsLossesOnExtinguishmentOfDebt", attribute="credit", parent=ide)
ide1_3 = Node("InducedConversionOfConvertibleDebtExpense", attribute="debit", parent=ide)
ide1_4 = Node("GainsLossesOnRestructuringOfDebt", attribute="credit", parent=ide)
ide1_5 = Node("GainsLossesOnRecourseDebt", attribute="credit", parent=ide)
ide1_6 = Node("GainLossOnNonRecourseDebt", attribute="credit", parent=ide)
ide1_7 = Node("GainLossOnRepurchaseOfDebtInstrument", attribute="debit", parent=ide)
ide1_8 = Node("DistributionsOnMandatorilyRedeemableSecurities", attribute="credit", parent=ide)

# Level 2

ide2_1 = Node("InterestExpenseDebt", attribute="debit", parent=ide1_1)
ide2_2 = Node("InterestExpenseCustomerDeposits", attribute="debit", parent=ide1_1)
ide2_3 = Node("DebtRelatedCommitmentFeesAndDebtIssuanceCosts", attribute="debit", parent=ide1_1)
ide2_4 = Node("FinanceLeaseInterestExpense", attribute="debit", parent=ide1_1)
ide2_5 = Node("InterestExpenseRelatedParty", attribute="debit", parent=ide1_1)
ide2_6 = Node("InterestExpenseOther", attribute="debit", parent=ide1_1)
ide2_7 = Node("InterestExpenseDeposits", attribute="debit", parent=ide1_1)
ide2_8 = Node("InterestExpenseTradingLiabilities", attribute="debit", parent=ide1_1)
ide2_9 = Node("InterestExpenseBorrowings", attribute="debit", parent=ide1_1)
ide2_10 = Node("InterestExpenseBeneficialInterestsIssuedByConsolidatedVariableInterestEntities", attribute="debit", parent=ide1_1)
ide2_11 = Node("InterestExpenseTrustPreferredSecurities", attribute="debit", parent=ide1_1)

ide2_12 = Node("GainsLossesOnExtinguishmentOfDebtBeforeWriteOffOfDeferredDebtIssuanceCost", attribute="credit", parent=ide1_2)
ide2_13 = Node("WriteOffOfDeferredDebtIssuanceCost", attribute="debit", parent=ide1_2)

# Level 3
ide3_1 = Node("InterestExpenseDomesticDeposits", attribute="debit", parent=ide2_7)
ide3_2 = Node("InterestExpenseForeignDeposits", attribute="debit", parent=ide2_7)

ide3_3 = Node("InterestExpenseShortTermBorrowings", attribute="debit", parent=ide2_9)
ide3_4 = Node("InterestExpenseLongTermDebtAndCapitalSecurities", attribute="debit", parent=ide2_9)

# Level 4
ide4_1 = Node("InterestExpenseNOWAccountsMoneyMarketAccountsAndSavingsDeposits", attribute="debit", parent=ide3_1)
ide4_2 = Node("InterestExpenseDemandDepositAccounts", attribute="debit", parent=ide3_1)
ide4_3 = Node("InterestExpenseTimeDeposits", attribute="debit", parent=ide3_1)
ide4_4 = Node("InterestExpenseOtherDomesticDeposits", attribute="debit", parent=ide3_1)

ide4_5 = Node("InterestExpenseFederalFundsPurchasedAndSecuritiesSoldUnderAgreementsToRepurchase", attribute="debit", parent=ide3_3)
ide4_6 = Node("InterestExpenseShortTermBorrowingsExcludingFederalFundsAndSecuritiesSoldUnderAgreementsToRepurchase", attribute="debit", parent=ide3_3)

ide4_7 = Node("InterestExpenseLongTermDebt", attribute="debit", parent=ide3_4)
ide4_8 = Node("InterestExpenseCapitalSecurities", attribute="debit", parent=ide3_4)

# Level 5

ide5_1 = Node("InterestExpenseNegotiableOrderOfWithdrawalNOWDeposits", attribute="debit", parent=ide4_1)
ide5_2 = Node("InterestExpenseMoneyMarketDeposits", attribute="debit", parent=ide4_1)
ide5_3 = Node("InterestExpenseSavingsDeposits", attribute="debit", parent=ide4_1)

ide5_4 = Node("InterestExpenseTimeDepositsLessThan100000", attribute="debit", parent=ide4_3)
ide5_5 = Node("InterestExpenseTimeDeposits100000OrMore", attribute="debit", parent=ide4_3)

ide5_6 = Node("InterestExpenseFederalFundsPurchased", attribute="debit", parent=ide4_5)
ide5_7 = Node("InterestExpenseSecuritiesSoldUnderAgreementsToRepurchase", attribute="debit", parent=ide4_5)

ide5_8 = Node("InterestExpenseFederalHomeLoanBankAndFederalReserveBankAdvancesShortTerm", attribute="debit", parent=ide4_6)
ide5_9 = Node("InterestExpenseCommercialPaper", attribute="debit", parent=ide4_6)
ide5_10 = Node("InterestExpenseOtherShortTermBorrowings", attribute="debit", parent=ide4_6)

ide5_11 = Node("InterestExpenseSubordinatedNotesAndDebentures", attribute="debit", parent=ide4_7)
ide5_12 = Node("InterestExpenseJuniorSubordinatedDebentures", attribute="debit", parent=ide4_7)
ide5_13 = Node("InterestExpenseMediumTermNotes", attribute="debit", parent=ide4_7)
ide5_14 = Node("InterestExpenseFederalHomeLoanBankAndFederalReserveBankAdvancesLongTerm", attribute="debit",
               parent=ide4_7)
ide5_15 = Node("InterestExpenseOtherLongTermDebt", attribute="debit", parent=ide4_7)