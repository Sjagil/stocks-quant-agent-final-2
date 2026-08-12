# Project Structuur

```text
.
├── artifacts
│   ├── environment
│   │   ├── main-pip-freeze.txt
│   │   ├── moondev-pip-freeze.txt
│   │   ├── qlib-pip-freeze.txt
│   │   └── vnpy-pip-freeze.txt
│   ├── evaluations
│   └── models
│       └── smoke_ppo.zip
├── build
│   ├── bdist.macosx-15.7-arm64
│   └── lib
│       └── stocks
│           ├── __init__.py
│           ├── contracts
│           │   ├── __init__.py
│           │   └── trade_intent.py
│           ├── intelligence_agent
│           │   ├── __init__.py
│           │   ├── agent.py
│           │   ├── allocator.py
│           │   ├── config.py
│           │   ├── indicators.py
│           │   ├── models.py
│           │   ├── nlp
│           │   │   ├── __init__.py
│           │   │   └── engine.py
│           │   ├── providers
│           │   │   ├── __init__.py
│           │   │   ├── eodhd.py
│           │   │   ├── fred.py
│           │   │   └── openfx.py
│           │   ├── scoring.py
│           │   └── store.py
│           ├── orchestration
│           │   ├── __init__.py
│           │   └── decision_pipeline.py
│           └── rl
│               ├── __init__.py
│               ├── config.py
│               ├── environment.py
│               ├── evaluator.py
│               ├── features.py
│               ├── rewards.py
│               ├── shadow_policy.py
│               ├── splits.py
│               └── trainer.py
├── config
│   └── rl.yaml
├── data
│   ├── adjusted
│   │   ├── AAPL_1h.corporate_actions.json
│   │   ├── AAPL_1h.parquet
│   │   ├── AMD_1h.corporate_actions.json
│   │   ├── AMD_1h.parquet
│   │   ├── CPER_1h.corporate_actions.json
│   │   ├── CPER_1h.parquet
│   │   ├── GLD_1h.corporate_actions.json
│   │   ├── GLD_1h.parquet
│   │   ├── MSFT_1h.corporate_actions.json
│   │   ├── MSFT_1h.parquet
│   │   ├── NVDA_1h.corporate_actions.json
│   │   ├── NVDA_1h.parquet
│   │   ├── QQQ_1h.corporate_actions.json
│   │   ├── QQQ_1h.parquet
│   │   ├── SLV_1h.corporate_actions.json
│   │   ├── SLV_1h.parquet
│   │   ├── SPY_1h.corporate_actions.json
│   │   └── SPY_1h.parquet
│   ├── processed
│   │   ├── AAPL_1d.metadata.json
│   │   ├── AAPL_1d.parquet
│   │   ├── AAPL_1h.metadata.json
│   │   ├── AAPL_1h.parquet
│   │   ├── AMD_1d.metadata.json
│   │   ├── AMD_1d.parquet
│   │   ├── AMD_1h.metadata.json
│   │   ├── AMD_1h.parquet
│   │   ├── CPER_1d.metadata.json
│   │   ├── CPER_1d.parquet
│   │   ├── CPER_1h.metadata.json
│   │   ├── CPER_1h.parquet
│   │   ├── GLD_1d.metadata.json
│   │   ├── GLD_1d.parquet
│   │   ├── GLD_1h.metadata.json
│   │   ├── GLD_1h.parquet
│   │   ├── MSFT_1d.metadata.json
│   │   ├── MSFT_1d.parquet
│   │   ├── MSFT_1h.metadata.json
│   │   ├── MSFT_1h.parquet
│   │   ├── NVDA_1d.metadata.json
│   │   ├── NVDA_1d.parquet
│   │   ├── NVDA_1h.metadata.json
│   │   ├── NVDA_1h.parquet
│   │   ├── QQQ_1d.metadata.json
│   │   ├── QQQ_1d.parquet
│   │   ├── QQQ_1h.metadata.json
│   │   ├── QQQ_1h.parquet
│   │   ├── SLV_1d.metadata.json
│   │   ├── SLV_1d.parquet
│   │   ├── SLV_1h.metadata.json
│   │   ├── SLV_1h.parquet
│   │   ├── SMOKE_1h.parquet
│   │   ├── SPY_1d.metadata.json
│   │   ├── SPY_1d.parquet
│   │   ├── SPY_1h.metadata.json
│   │   └── SPY_1h.parquet
│   └── raw
├── logs
├── pyproject.toml
├── README.md
├── references
│   ├── =
│   ├── FinRL-Trading
│   │   ├── data
│   │   │   ├── finrl_trading.7z
│   │   │   ├── fundamental_data_full.csv
│   │   │   └── sp500_historical_constituents.csv
│   │   ├── deploy.sh
│   │   ├── docker-compose.yml
│   │   ├── Dockerfile
│   │   ├── docs
│   │   │   └── trading_calendar_guide.md
│   │   ├── examples
│   │   │   ├── compare_cost_models.ipynb
│   │   │   ├── data
│   │   │   │   └── cache
│   │   │   │       └── sp500_components_latest.csv
│   │   │   ├── FinRL_Full_selection.ipynb
│   │   │   ├── FinRL_universe_portfolio.ipynb
│   │   │   ├── README.md
│   │   │   ├── realtime_stock_price.ipynb
│   │   │   └── weight_allocation_guide.md
│   │   ├── figs
│   │   │   ├── All_Backtests_v2.png
│   │   │   ├── DRL_Timing_Backtest.png
│   │   │   ├── FinRL_X_Framework.png
│   │   │   ├── Paper_Trading.png
│   │   │   └── Sector_Rotation_Standalone.png
│   │   ├── LICENSE
│   │   ├── ML_STOCK_SELECTION.md
│   │   ├── README.md
│   │   ├── requirements.txt
│   │   ├── setup.py
│   │   └── src
│   │       ├── __init__.py
│   │       ├── backtest
│   │       │   ├── __init__.py
│   │       │   └── backtest_engine.py
│   │       ├── config
│   │       │   ├── __init__.py
│   │       │   └── settings.py
│   │       ├── data
│   │       │   ├── __init__.py
│   │       │   ├── backfill_historical_sp500.py
│   │       │   ├── data_fetcher.py
│   │       │   ├── data_processor.py
│   │       │   ├── data_store.py
│   │       │   ├── fetch_and_store_fundamentals.py
│   │       │   ├── fill_recent_yreturn.py
│   │       │   ├── fix_adj_close.py
│   │       │   └── trading_calendar.py
│   │       ├── main.py
│   │       ├── strategies
│   │       │   ├── __init__.py
│   │       │   ├── adaptive_rotation
│   │       │   │   ├── __init__.py
│   │       │   │   ├── adaptive_rotation_engine.py
│   │       │   │   ├── config_loader.py
│   │       │   │   ├── data_preprocessor.py
│   │       │   │   ├── exception_framework.py
│   │       │   │   ├── group_strength.py
│   │       │   │   ├── intra_group_ranking.py
│   │       │   │   ├── market_regime.py
│   │       │   │   ├── portfolio_builder.py
│   │       │   │   ├── risk_manager.py
│   │       │   │   ├── utils
│   │       │   │   │   ├── __init__.py
│   │       │   │   │   ├── __pycache__
│   │       │   │   │   │   ├── __init__.cpython-311.pyc
│   │       │   │   │   │   ├── calendar_utils.cpython-311.pyc
│   │       │   │   │   │   └── robust_stats.cpython-311.pyc
│   │       │   │   │   ├── calendar_utils.py
│   │       │   │   │   └── robust_stats.py
│   │       │   │   └── walk_forward.py
│   │       │   ├── AdaptiveRotationConf_v1.2.1.yaml
│   │       │   ├── AdaptiveRotationConf_v1.2.2.yaml
│   │       │   ├── base_signal.py
│   │       │   ├── base_strategy.py
│   │       │   ├── execution_engine.py
│   │       │   ├── fundamental_portfolio_drl.py
│   │       │   ├── group_selection_by_gics.py
│   │       │   ├── ml_bucket_selection.py
│   │       │   ├── ml_strategy.py
│   │       │   ├── rl_model.py
│   │       │   ├── run_adaptive_rotation_strategy.py
│   │       │   ├── strategylogger.py
│   │       │   ├── tsmomsignal.py
│   │       │   └── universe_manager.py
│   │       ├── tools
│   │       │   └── dashboard.py
│   │       ├── trading
│   │       │   ├── __init__.py
│   │       │   ├── alpaca_manager.py
│   │       │   ├── performance_analyzer.py
│   │       │   └── trade_executor.py
│   │       ├── utils
│   │       │   └── __init__.py
│   │       └── web
│   │           ├── __init__.py
│   │           ├── app.py
│   │           └── components.py
│   ├── Lean
│   │   ├── Algorithm
│   │   │   ├── Alphas
│   │   │   │   ├── AlphaModel.cs
│   │   │   │   ├── AlphaModelExtensions.cs
│   │   │   │   ├── AlphaModelPythonWrapper.cs
│   │   │   │   ├── CompositeAlphaModel.cs
│   │   │   │   ├── IAlphaModel.cs
│   │   │   │   ├── INamedModel.cs
│   │   │   │   ├── NullAlphaModel.cs
│   │   │   │   └── NullAlphaModel.py
│   │   │   ├── CandlestickPatterns.cs
│   │   │   ├── ConstituentUniverseDefinitions.cs
│   │   │   ├── DollarVolumeUniverseDefinitions.cs
│   │   │   ├── Execution
│   │   │   │   ├── ExecutionModel.cs
│   │   │   │   ├── ExecutionModelPythonWrapper.cs
│   │   │   │   ├── IExecutionModel.cs
│   │   │   │   ├── ImmediateExecutionModel.cs
│   │   │   │   ├── ImmediateExecutionModel.py
│   │   │   │   ├── NullExecutionModel.cs
│   │   │   │   └── NullExecutionModel.py
│   │   │   ├── INotifiedSecurityChanges.cs
│   │   │   ├── Portfolio
│   │   │   │   ├── IPortfolioConstructionModel.cs
│   │   │   │   ├── IPortfolioOptimizer.cs
│   │   │   │   ├── NullPortfolioConstructionModel.cs
│   │   │   │   ├── NullPortfolioConstructionModel.py
│   │   │   │   ├── PortfolioBias.cs
│   │   │   │   ├── PortfolioConstructionModel.cs
│   │   │   │   └── PortfolioConstructionModelPythonWrapper.cs
│   │   │   ├── Properties
│   │   │   │   └── AssemblyInfo.cs
│   │   │   ├── QCAlgorithm.cs
│   │   │   ├── QCAlgorithm.Framework.cs
│   │   │   ├── QCAlgorithm.Framework.Python.cs
│   │   │   ├── QCAlgorithm.History.cs
│   │   │   ├── QCAlgorithm.Indicators.cs
│   │   │   ├── QCAlgorithm.Plotting.cs
│   │   │   ├── QCAlgorithm.Python.cs
│   │   │   ├── QCAlgorithm.Trading.cs
│   │   │   ├── QCAlgorithm.Universe.cs
│   │   │   ├── QuantConnect.Algorithm.csproj
│   │   │   ├── Risk
│   │   │   │   ├── CompositeRiskManagementModel.cs
│   │   │   │   ├── CompositeRiskManagementModel.py
│   │   │   │   ├── IRiskManagementModel.cs
│   │   │   │   ├── NullRiskManagementModel.cs
│   │   │   │   ├── NullRiskManagementModel.py
│   │   │   │   ├── RiskManagementModel.cs
│   │   │   │   └── RiskManagementModelPythonWrapper.cs
│   │   │   ├── Selection
│   │   │   │   ├── CompositeUniverseSelectionModel.cs
│   │   │   │   ├── CustomUniverse.cs
│   │   │   │   ├── CustomUniverseSelectionModel.cs
│   │   │   │   ├── IUniverseSelectionModel.cs
│   │   │   │   ├── ManualUniverse.cs
│   │   │   │   ├── ManualUniverseSelectionModel.cs
│   │   │   │   ├── ManualUniverseSelectionModel.py
│   │   │   │   ├── NullUniverseSelectionModel.cs
│   │   │   │   ├── OptionChainedUniverseSelectionModel.cs
│   │   │   │   ├── OptionContractUniverse.cs
│   │   │   │   ├── UniverseSelectionModel.cs
│   │   │   │   ├── UniverseSelectionModel.py
│   │   │   │   └── UniverseSelectionModelPythonWrapper.cs
│   │   │   └── UniverseDefinitions.cs
│   │   ├── Algorithm.CSharp
│   │   │   ├── AccordVectorMachinesAlgorithm.cs
│   │   │   ├── AccumulativeInsightPortfolioRegressionAlgorithm.cs
│   │   │   ├── AddAlphaModelAlgorithm.cs
│   │   │   ├── AddAndRemoveOptionContractRegressionAlgorithm.cs
│   │   │   ├── AddAndRemoveSecuritySameLoopRegressionAlgorithm.cs
│   │   │   ├── AddBetaIndicatorNewAssetsRegressionAlgorithm.cs
│   │   │   ├── AddBetaIndicatorRegressionAlgorithm.cs
│   │   │   ├── AddFutureContractWithContinuousRegressionAlgorithm.cs
│   │   │   ├── AddFutureOptionContractDataStreamingRegressionAlgorithm.cs
│   │   │   ├── AddFutureOptionContractFromFutureChainRegressionAlgorithm.cs
│   │   │   ├── AddFutureOptionContractWithInternalMappedUnderlyingRegressionAlgorithm.cs
│   │   │   ├── AddFutureOptionSingleOptionChainSelectedInUniverseFilterRegressionAlgorithm.cs
│   │   │   ├── AddFutureUniverseSelectionModelRegressionAlgorithm.cs
│   │   │   ├── AddOptionContractExpiresRegressionAlgorithm.cs
│   │   │   ├── AddOptionContractFromUniverseRegressionAlgorithm.cs
│   │   │   ├── AddOptionContractTwiceRegressionAlgorithm.cs
│   │   │   ├── AddOptionUniverseSelectionModelRegressionAlgorithm.cs
│   │   │   ├── AddOptionWithOnMarketOpenOnlyFilterRegressionAlgorithm.cs
│   │   │   ├── AddRemoveOptionUniverseRegressionAlgorithm.cs
│   │   │   ├── AddRemoveSecurityCacheRegressionAlgorithm.cs
│   │   │   ├── AddRemoveSecurityRegressionAlgorithm.cs
│   │   │   ├── AddRiskManagementAlgorithm.cs
│   │   │   ├── AddTwoAndRemoveOneOptionContractRegressionAlgorithm.cs
│   │   │   ├── AddUniverseSelectionModelAlgorithm.cs
│   │   │   ├── AddUniverseSelectionModelCoarseAlgorithm.cs
│   │   │   ├── AdjustedVolumeRegressionAlgorithm.cs
│   │   │   ├── AlgorithmModeAndDeploymentTargetAlgorithm.cs
│   │   │   ├── AllShortableSymbolsCoarseSelectionRegressionAlgorithm.cs
│   │   │   ├── Alphas
│   │   │   │   ├── GasAndCrudeOilEnergyCorrelationAlpha.cs
│   │   │   │   ├── GlobalEquityMeanReversionIBSAlpha.cs
│   │   │   │   ├── GreenblattMagicFormulaAlpha.cs
│   │   │   │   ├── IntradayReversalCurrencyMarketsAlpha.cs
│   │   │   │   ├── MeanReversionLunchBreakAlpha.cs
│   │   │   │   ├── RebalancingLeveragedETFAlpha.cs
│   │   │   │   ├── ShareClassMeanReversionAlpha.cs
│   │   │   │   ├── SykesShortMicroCapAlpha.cs
│   │   │   │   ├── TriangleExchangeRateArbitrageAlpha.cs
│   │   │   │   ├── TripleLeveragedETFPairVolatilityDecayAlpha.cs
│   │   │   │   └── VixDualThrustAlpha.cs
│   │   │   ├── AsynchronousUniverseRegressionAlgorithm.cs
│   │   │   ├── AutomaticIndicatorWarmupDataTypeRegressionAlgorithm.cs
│   │   │   ├── AutomaticIndicatorWarmupOptionIndicatorsMirrorContractsRegressionAlgorithm.cs
│   │   │   ├── AutomaticIndicatorWarmupRegressionAlgorithm.cs
│   │   │   ├── AutomaticSeedBaseRegressionAlgorithm.cs
│   │   │   ├── AutoRegressiveIntegratedMovingAverageRegressionAlgorithm.cs
│   │   │   ├── AuxiliaryDataHandlersRegressionAlgorithm.cs
│   │   │   ├── BacktestingAsynchronousOrdersRegressionAlgorithm.cs
│   │   │   ├── BacktestingBrokerageRegressionAlgorithm.cs
│   │   │   ├── BaseFrameworkRegressionAlgorithm.cs
│   │   │   ├── BasicPythonIntegrationTemplateAlgorithm.cs
│   │   │   ├── BasicSetAccountCurrencyAlgorithm.cs
│   │   │   ├── BasicSetAccountCurrencyWithAmountAlgorithm.cs
│   │   │   ├── BasicTemplateAlgorithm.cs
│   │   │   ├── BasicTemplateAxosAlgorithm.cs
│   │   │   ├── BasicTemplateCfdAlgorithm.cs
│   │   │   ├── BasicTemplateContinuousFutureAlgorithm.cs
│   │   │   ├── BasicTemplateContinuousFutureWithExtendedMarketAlgorithm.cs
│   │   │   ├── BasicTemplateCryptoAlgorithm.cs
│   │   │   ├── BasicTemplateCryptoFrameworkAlgorithm.cs
│   │   │   ├── BasicTemplateCryptoFutureAlgorithm.cs
│   │   │   ├── BasicTemplateCryptoFutureHourlyAlgorithm.cs
│   │   │   ├── BasicTemplateDailyAlgorithm.cs
│   │   │   ├── BasicTemplateEurexFuturesAlgorithm.cs
│   │   │   ├── BasicTemplateFillForwardAlgorithm.cs
│   │   │   ├── BasicTemplateForexAlgorithm.cs
│   │   │   ├── BasicTemplateFrameworkAlgorithm.cs
│   │   │   ├── BasicTemplateFutureOptionAlgorithm.cs
│   │   │   ├── BasicTemplateFutureRolloverAlgorithm.cs
│   │   │   ├── BasicTemplateFuturesAlgorithm.cs
│   │   │   ├── BasicTemplateFuturesConsolidationAlgorithm.cs
│   │   │   ├── BasicTemplateFuturesDailyAlgorithm.cs
│   │   │   ├── BasicTemplateFuturesFrameworkAlgorithm.cs
│   │   │   ├── BasicTemplateFuturesFrameworkWithExtendedMarketAlgorithm.cs
│   │   │   ├── BasicTemplateFuturesHistoryAlgorithm.cs
│   │   │   ├── BasicTemplateFuturesHistoryWithExtendedMarketHoursAlgorithm.cs
│   │   │   ├── BasicTemplateFuturesHourlyAlgorithm.cs
│   │   │   ├── BasicTemplateFuturesWithExtendedMarketAlgorithm.cs
│   │   │   ├── BasicTemplateFuturesWithExtendedMarketDailyAlgorithm.cs
│   │   │   ├── BasicTemplateFuturesWithExtendedMarketHourlyAlgorithm.cs
│   │   │   ├── BasicTemplateHourlyAlgorithm.cs
│   │   │   ├── BasicTemplateIndexAlgorithm.cs
│   │   │   ├── BasicTemplateIndexDailyAlgorithm.cs
│   │   │   ├── BasicTemplateIndexHourlyAlgorithm.cs
│   │   │   ├── BasicTemplateIndexOptionsAlgorithm.cs
│   │   │   ├── BasicTemplateIndexOptionsDailyAlgorithm.cs
│   │   │   ├── BasicTemplateIndexOptionsHourlyAlgorithm.cs
│   │   │   ├── BasicTemplateIndiaAlgorithm.cs
│   │   │   ├── BasicTemplateIndiaIndexAlgorithm.cs
│   │   │   ├── BasicTemplateIntrinioEconomicData.cs
│   │   │   ├── BasicTemplateLibrary.cs
│   │   │   ├── BasicTemplateMultiAssetAlgorithm.cs
│   │   │   ├── BasicTemplateOptionEquityStrategyAlgorithm.cs
│   │   │   ├── BasicTemplateOptionsAlgorithm.cs
│   │   │   ├── BasicTemplateOptionsConsolidationAlgorithm.cs
│   │   │   ├── BasicTemplateOptionsDailyAlgorithm.cs
│   │   │   ├── BasicTemplateOptionsFilterUniverseAlgorithm.cs
│   │   │   ├── BasicTemplateOptionsFrameworkAlgorithm.cs
│   │   │   ├── BasicTemplateOptionsHistoryAlgorithm.cs
│   │   │   ├── BasicTemplateOptionsHourlyAlgorithm.cs
│   │   │   ├── BasicTemplateOptionStrategyAlgorithm.cs
│   │   │   ├── BasicTemplateOptionTradesAlgorithm.cs
│   │   │   ├── BasicTemplateSPXWeeklyIndexOptionsAlgorithm.cs
│   │   │   ├── BasicTemplateSPXWeeklyIndexOptionsStrategyAlgorithm.cs
│   │   │   ├── BasicTemplateTradableIndexAlgorithm.cs
│   │   │   ├── Benchmarks
│   │   │   │   ├── BasicTemplateBenchmark.cs
│   │   │   │   ├── CoarseFineUniverseSelectionBenchmark.cs
│   │   │   │   ├── EmptyEquityAndOptions400Benchmark.cs
│   │   │   │   ├── EmptyMinute400EquityAlgorithm.xlsx
│   │   │   │   ├── EmptyMinute400EquityBenchmark.cs
│   │   │   │   ├── EmptySingleSecuritySecondEquityBenchmark.cs
│   │   │   │   ├── EmptySPXOptionChainBenchmark.cs
│   │   │   │   ├── HistoryRequestBenchmark.cs
│   │   │   │   ├── IndicatorRibbonBenchmark.cs
│   │   │   │   ├── ScheduledEventsBenchmark.cs
│   │   │   │   ├── StatefulCoarseUniverseSelectionBenchmark.cs
│   │   │   │   └── StatelessCoarseUniverseSelectionBenchmark.cs
│   │   │   ├── BinanceCashAccountFeeRegressionAlgorithm.cs
│   │   │   ├── BinanceCryptoFutureBnfcrCollateralRegressionAlgorithm.cs
│   │   │   ├── BinanceMarginAccountFeeRegressionAlgorithm.cs
│   │   │   ├── BitfinexCashAccountFeeRegressionAlgorithm.cs
│   │   │   ├── BitfinexMarginAccountFeeRegressionAlgorithm.cs
│   │   │   ├── BlackLittermanPortfolioOptimizationFrameworkAlgorithm.cs
│   │   │   ├── BrokerageActivityEventHandlingAlgorithm.cs
│   │   │   ├── BrokerageModelAlgorithm.cs
│   │   │   ├── BubbleAlgorithm.cs
│   │   │   ├── BybitCryptoFuturesRegressionAlgorithm.cs
│   │   │   ├── BybitCryptoRegressionAlgorithm.cs
│   │   │   ├── BybitCustomDataCryptoRegressionAlgorithm.cs
│   │   │   ├── CallbackCommandRegressionAlgorithm.cs
│   │   │   ├── CancelOpenOrdersRegressionAlgorithm.cs
│   │   │   ├── CanLiquidateWithOrderPropertiesRegressionAlgorithm.cs
│   │   │   ├── CapacityTests
│   │   │   │   ├── BeastVsPenny.cs
│   │   │   │   ├── CheeseMilkHourlyRebalance.cs
│   │   │   │   ├── EmaPortfolioRebalance100.cs
│   │   │   │   ├── IntradayMinuteScalping.cs
│   │   │   │   ├── IntradayMinuteScalpingBTCETH.cs
│   │   │   │   ├── IntradayMinuteScalpingEURUSD.cs
│   │   │   │   ├── IntradayMinuteScalpingFuturesES.cs
│   │   │   │   ├── IntradayMinuteScalpingGBPJPY.cs
│   │   │   │   ├── IntradayMinuteScalpingTRYJPY.cs
│   │   │   │   ├── MonthlyRebalanceDaily.cs
│   │   │   │   ├── MonthlyRebalanceHourly.cs
│   │   │   │   ├── SplitTestingStrategy.cs
│   │   │   │   └── SpyBondPortfolioRebalance.cs
│   │   │   ├── CapmAlphaRankingFrameworkAlgorithm.cs
│   │   │   ├── CfdTimeZonesRegressionAlgorithm.cs
│   │   │   ├── ClassicRangeConsolidatorAlgorithm.cs
│   │   │   ├── ClassicRangeConsolidatorWithTickAlgorithm.cs
│   │   │   ├── ClassicRenkoConsolidatorAlgorithm.cs
│   │   │   ├── ClassicRenkoConsolidatorWithFuturesAndDefaultTickTypeRegressionAlgorithm.cs
│   │   │   ├── ClassicRenkoConsolidatorWithFuturesQuoteTickTypeRegressionAlgorithm.cs
│   │   │   ├── ClassicRenkoConsolidatorWithFuturesTickTypesRegressionAlgorithm.cs
│   │   │   ├── CoarseFineAsyncUniverseRegressionAlgorithm.cs
│   │   │   ├── CoarseFineFundamentalComboAlgorithm.cs
│   │   │   ├── CoarseFineFundamentalRegressionAlgorithm.cs
│   │   │   ├── CoarseFineOptionUniverseChainRegressionAlgorithm.cs
│   │   │   ├── CoarseFundamentalImmediateSelectionRegressionAlgorithm.cs
│   │   │   ├── CoarseFundamentalTop3Algorithm.cs
│   │   │   ├── CoarseNoLookAheadBiasAlgorithm.cs
│   │   │   ├── CoarseSelectionsAutomaticSeedRegressionAlgorithm.cs
│   │   │   ├── CoarseSelectionTimeRegressionAlgorithm.cs
│   │   │   ├── CoinbaseCryptoYearMarketTradingRegressionAlgorithm.cs
│   │   │   ├── Collective2PortfolioSignalExportDemonstrationAlgorithm.cs
│   │   │   ├── Collective2SignalExportDemonstrationAlgorithm.cs
│   │   │   ├── ComboLegLimitOrderAlgorithm.cs
│   │   │   ├── ComboLegLimitOrderAsyncAlgorithm.cs
│   │   │   ├── ComboLimitOrderAlgorithm.cs
│   │   │   ├── ComboLimitOrderAsyncAlgorithm.cs
│   │   │   ├── ComboMarketOrderAlgorithm.cs
│   │   │   ├── ComboOrderAlgorithm.cs
│   │   │   ├── ComboOrdersFillModelAlgorithm.cs
│   │   │   ├── ComboOrderTicketDemoAlgorithm.cs
│   │   │   ├── CompleteOrderTagUpdateAlgorithm.cs
│   │   │   ├── CompositeAlphaModelFrameworkAlgorithm.cs
│   │   │   ├── CompositeIndicatorWorksAsExpectedRegressionAlgorithm.cs
│   │   │   ├── CompositeRiskManagementModelFrameworkAlgorithm.cs
│   │   │   ├── ConfidenceWeightedFrameworkAlgorithm.cs
│   │   │   ├── ConsolidateDifferentTickTypesRegressionAlgorithm.cs
│   │   │   ├── ConsolidateHourBarsIntoDailyBarsRegressionAlgorithm.cs
│   │   │   ├── ConsolidateRegressionAlgorithm.cs
│   │   │   ├── ConsolidateScanRegressionAlgorithm.cs
│   │   │   ├── ConsolidateWithSizeAttributeRegressionAlgorithm.cs
│   │   │   ├── ConsolidatorAndAlgorithmTimeConsistencyWithWarmupRegressionAlgorithm.cs
│   │   │   ├── ConsolidatorAnIdentityIndicatorRegressionAlgorithm.cs
│   │   │   ├── ConsolidatorRollingWindowRegressionAlgorithm.cs
│   │   │   ├── ConsolidatorStartTimeRegressionAlgorithm.cs
│   │   │   ├── ConstituentsQC500GeneratorAlgorithm.cs
│   │   │   ├── ConstituentsUniverseDataGeneratorAlgorithm.cs
│   │   │   ├── ConstituentsUniverseImmediateSelectionRegressionAlgorithm.cs
│   │   │   ├── ConstituentsUniverseRegressionAlgorithm.cs
│   │   │   ├── ContinuousBackMonthRawFutureRegressionAlgorithm.cs
│   │   │   ├── ContinuousFutureBackMonthRegressionAlgorithm.cs
│   │   │   ├── ContinuousFutureHistoryRegressionAlgorithm.cs
│   │   │   ├── ContinuousFutureHistoryTimeSpanWarmupRegressionAlgorithm.cs
│   │   │   ├── ContinuousFutureImmediateUniverseSelectionRegressionAlgorithm.cs
│   │   │   ├── ContinuousFutureLimitIfTouchedOrderRegressionAlgorithm.cs
│   │   │   ├── ContinuousFutureModelsConsistencyRegressionAlgorithm.cs
│   │   │   ├── ContinuousFutureOpenPositionsLiquidationOnDelistingRegressionAlgorithm.cs
│   │   │   ├── ContinuousFutureRegressionAlgorithm.cs
│   │   │   ├── ContinuousFutureRolloverBaseRegressionAlgorithm.cs
│   │   │   ├── ContinuousFutureRolloverDailyExchangeTimeZoneAheadOfDataRegressionAlgorithm.cs
│   │   │   ├── ContinuousFutureRolloverDailyExchangeTimeZoneAheadOfDataWithInitialSeedRegressionAlgorithm.cs
│   │   │   ├── ContinuousFutureRolloverDailyExchangeTimeZoneBehindOfDataRegressionAlgorithm.cs
│   │   │   ├── ContinuousFutureRolloverDailyExchangeTimeZoneBehindOfDataWithInitialSeedRegressionAlgorithm.cs
│   │   │   ├── ContinuousFutureRolloverDailyExchangeTimeZoneSameAsDataRegressionAlgorithm.cs
│   │   │   ├── ContinuousFutureRolloverDailyExchangeTimeZoneSameAsDataWithIntialSeedRegressionAlgorithm.cs
│   │   │   ├── ContinuousFutureRolloverHourExchangeTimeZoneAheadOfDataRegressionAlgorithm.cs
│   │   │   ├── ContinuousFutureRolloverHourExchangeTimeZoneAheadOfDataWithInitialSeedRegressionAlgorithm.cs
│   │   │   ├── ContinuousFutureRolloverHourExchangeTimeZoneBehindOfDataRegressionAlgorithm.cs
│   │   │   ├── ContinuousFutureRolloverHourExchangeTimeZoneBehindOfDataWithInitialSeedRegressionAlgorithm.cs
│   │   │   ├── ContinuousFutureRolloverHourExchangeTimeZoneSameAsDataRegressionAlgorithm.cs
│   │   │   ├── ContinuousFutureRolloverHourExchangeTimeZoneSameAsDataWithInitialSeedRegressionAlgorithm.cs
│   │   │   ├── ContinuousFutureRolloverMinuteExchangeTimeZoneAheadOfDataRegressionAlgorithm.cs
│   │   │   ├── ContinuousFutureRolloverMinuteExchangeTimeZoneAheadOfDataWithInitialSeedRegressionAlgorithm.cs
│   │   │   ├── ContinuousFutureRolloverMinuteExchangeTimeZoneBehindOfDataRegressionAlgorithm.cs
│   │   │   ├── ContinuousFutureRolloverMinuteExchangeTimeZoneBehindOfDataWithInitialSeedRegressionAlgorithm.cs
│   │   │   ├── ContinuousFutureRolloverMinuteExchangeTimeZoneSameAsDataRegressionAlgorithm.cs
│   │   │   ├── ContinuousFutureRolloverMinuteExchangeTimeZoneSameAsDataWithInitialSeedRegressionAlgorithm.cs
│   │   │   ├── ContinuousFuturesDailyRegressionAlgorithm.cs
│   │   │   ├── ConvertToFrameworkAlgorithm.cs
│   │   │   ├── CorrectConsolidatedBarTypeForTickTypesAlgorithm.cs
│   │   │   ├── CorrelationTypeComparisonRegressionAlgorithm.cs
│   │   │   ├── CoveredAndProtectiveCallStrategiesAlgorithm.cs
│   │   │   ├── CoveredAndProtectivePutStrategiesAlgorithm.cs
│   │   │   ├── CoveredCallComboLimitOrderAlgorithm.cs
│   │   │   ├── CryptoBaseCurrencyFeeRegressionAlgorithm.cs
│   │   │   ├── CryptoFutureDailyMarginInterestRegressionAlgorithm.cs
│   │   │   ├── CryptoFutureHourlyMarginInterestRegressionAlgorithm.cs
│   │   │   ├── CryptoFutureLeverageBasedMarginRegressionAlgorithm.cs
│   │   │   ├── CustomBenchmarkAlgorithm.cs
│   │   │   ├── CustomBenchmarkRegressionAlgorithm.cs
│   │   │   ├── CustomBrokerageMessageHandlerAlgorithm.cs
│   │   │   ├── CustomBrokerageModelRegressionAlgorithm.cs
│   │   │   ├── CustomBrokerageSideOrderHandlingRegressionAlgorithm.cs
│   │   │   ├── CustomBuyingPowerModelAlgorithm.cs
│   │   │   ├── CustomChartingAlgorithm.cs
│   │   │   ├── CustomDataAutomaticSeedRegressionAlgorithm.cs
│   │   │   ├── CustomDataBenchmarkRegressionAlgorithm.cs
│   │   │   ├── CustomDataBitcoinAlgorithm.cs
│   │   │   ├── CustomDataIndicatorExtensionsAlgorithm.cs
│   │   │   ├── CustomDataMultiFileObjectStoreRegressionAlgorithm.cs
│   │   │   ├── CustomDataNIFTYAlgorithm.cs
│   │   │   ├── CustomDataObjectStoreRegressionAlgorithm.cs
│   │   │   ├── CustomDataPropertiesRegressionAlgorithm.cs
│   │   │   ├── CustomDataRegressionAlgorithm.cs
│   │   │   ├── CustomDataSecurityCacheGetDataRegressionAlgorithm.cs
│   │   │   ├── CustomDataTypeHistoryAlgorithm.cs
│   │   │   ├── CustomDataUniverseAlgorithm.cs
│   │   │   ├── CustomDataUniverseImmediateSelectionRegressionAlgorithm.cs
│   │   │   ├── CustomDataUniverseRegressionAlgorithm.cs
│   │   │   ├── CustomDataUniverseScheduledRegressionAlgorithm.cs
│   │   │   ├── CustomDataUsingMapFileRegressionAlgorithm.cs
│   │   │   ├── CustomDataWorksWithDifferentExchangesRegressionAlgorithm.cs
│   │   │   ├── CustomDataZipFileEntryNamesRegressionAlgorithm.cs
│   │   │   ├── CustomDataZipFileRegressionAlgorithm.cs
│   │   │   ├── CustomDataZipFileSpecificEntryRegressionAlgorithm.cs
│   │   │   ├── CustomDataZippedObjectStoreRegressionAlgorithm.cs
│   │   │   ├── CustomFrameworkModelsAlgorithm.cs
│   │   │   ├── CustomMarginInterestRateModelAlgorithm.cs
│   │   │   ├── CustomModelsAlgorithm.cs
│   │   │   ├── CustomOptionAssignmentRegressionAlgorithm.cs
│   │   │   ├── CustomOptionExerciseModelRegressionAlgorithm.cs
│   │   │   ├── CustomOptionPriceModelRegressionAlgorithm.cs
│   │   │   ├── CustomPartialFillModelAlgorithm.cs
│   │   │   ├── CustomPortfolioOptimizerRegressionAlgorithm.cs
│   │   │   ├── CustomSecurityDataFilterRegressionAlgorithm.cs
│   │   │   ├── CustomSecurityInitializerAlgorithm.cs
│   │   │   ├── CustomShortableProviderRegressionAlgorithm.cs
│   │   │   ├── CustomSignalExportDemonstrationAlgorithm.cs
│   │   │   ├── CustomUniverseImmediateSelectionRegressionAlgorithm.cs
│   │   │   ├── CustomUniverseSelectionModelRegressionAlgorithm.cs
│   │   │   ├── CustomUniverseSelectionRegressionAlgorithm.cs
│   │   │   ├── CustomUniverseWithBenchmarkRegressionAlgorithm.cs
│   │   │   ├── CustomVolatilityModelAlgorithm.cs
│   │   │   ├── CustomWarmUpPeriodIndicatorAlgorithm.cs
│   │   │   ├── DailyAlgorithm.cs
│   │   │   ├── DailyConsolidationExtendedMarketHoursWarningRegressionAlgorithm.cs
│   │   │   ├── DailyHistoryForDailyResolutionRegressionAlgorithm.cs
│   │   │   ├── DailyHistoryForMinuteResolutionRegressionAlgorithm.cs
│   │   │   ├── DailyOptionChainOpenInterestDataWithoutStrictDailyEndTimesRegressionAlgorithm.cs
│   │   │   ├── DailyOptionChainOpenInterestDataWithStrictDailyEndTimesRegressionAlgorithm.cs
│   │   │   ├── DailyResolutionMarketOrderConversionRegressionAlgorithm.cs
│   │   │   ├── DailyResolutionSplitRegressionAlgorithm.cs
│   │   │   ├── DailyResolutionVsTimeSpanNoPreciseEndRegressionAlgorithm.cs
│   │   │   ├── DailyResolutionVsTimeSpanRegressionAlgorithm.cs
│   │   │   ├── DailyResolutionVsTimeSpanWithMinuteEquityAlgorithm.cs
│   │   │   ├── DailyResolutionVsTimeSpanWithSecondEquityAlgorithm.cs
│   │   │   ├── DailyResolutionVsTimeSpanWithTickResolutionEquityAlgorithm.cs
│   │   │   ├── DailyStrictEndTimeConsolidatorsRegressionAlgorithm.cs
│   │   │   ├── DailyStrictEndTimeDisabledConsolidatorsRegressionAlgorithm.cs
│   │   │   ├── DataConsolidationAlgorithm.cs
│   │   │   ├── DaylightSavingTimeHistoryRegressionAlgorithm.cs
│   │   │   ├── DefaultFutureChainRegressionAlgorithm.cs
│   │   │   ├── DefaultMarginComboOrderRegressionAlgorithm.cs
│   │   │   ├── DefaultMarginMultipleOrdersRegressionAlgorithm.cs
│   │   │   ├── DefaultOptionPriceModelRegressionAlgorithm.cs
│   │   │   ├── DefaultSchedulingSymbolRegressionAlgorithm.cs
│   │   │   ├── DelayedSettlementAfterManualSecurityRemovalAlgorithm.cs
│   │   │   ├── DelistedFutureLiquidateDailyRegressionAlgorithm.cs
│   │   │   ├── DelistedFutureLiquidateFromChainAndContinuousMidnightExpiryRegressionAlgorithm.cs
│   │   │   ├── DelistedFutureLiquidateFromChainAndContinuousRegressionAlgorithm.cs
│   │   │   ├── DelistedFutureLiquidateRegressionAlgorithm.cs
│   │   │   ├── DelistedIndexOptionDivestedRegression.cs
│   │   │   ├── DelistingEventsAlgorithm.cs
│   │   │   ├── DelistingFutureOptionDailyRegressionAlgorithm.cs
│   │   │   ├── DelistingFutureOptionRegressionAlgorithm.cs
│   │   │   ├── DescendingCustomDataObjectStoreRegressionAlgorithm.cs
│   │   │   ├── DisplacedMovingAverageRibbon.cs
│   │   │   ├── DividendAlgorithm.cs
│   │   │   ├── DividendRegressionAlgorithm.cs
│   │   │   ├── DropboxBaseDataUniverseSelectionAlgorithm.cs
│   │   │   ├── DropboxUniverseSelectionAlgorithm.cs
│   │   │   ├── DuplicatedIndexOptionSubscriptionRegressionAlgorithm.cs
│   │   │   ├── DuplicateOptionAssignmentRegressionAlgorithm.cs
│   │   │   ├── DuplicateSecurityWithBenchmarkRegressionAlgorithm.cs
│   │   │   ├── DYDXCryptoFuturesRegressionAlgorithm.cs
│   │   │   ├── DynamicSecurityDataRegressionAlgorithm.cs
│   │   │   ├── EmaCrossAlphaModelFrameworkRegressionAlgorithm.cs
│   │   │   ├── EmaCrossFuturesFrontMonthAlgorithm.cs
│   │   │   ├── EmaCrossUniverseSelectionAlgorithm.cs
│   │   │   ├── EmaCrossUniverseSelectionFrameworkAlgorithm.cs
│   │   │   ├── EmitInsightCryptoCashAccountType.cs
│   │   │   ├── EmitInsightNoAlphaModelAlgorithm.cs
│   │   │   ├── EmitInsightsAlgorithm.cs
│   │   │   ├── EqualWeightingPortfolioConstructionModelFutureRegressionAlgorithm.cs
│   │   │   ├── EquityMarginCallAlgorithm.cs
│   │   │   ├── EquityOptionsUniverseSettingsRegressionAlgorithm.cs
│   │   │   ├── EquitySplitHoldingsDailyRegressionAlgorithm.cs
│   │   │   ├── EquitySplitHoldingsHourRegressionAlgorithm.cs
│   │   │   ├── EquitySplitHoldingsMinuteRegressionAlgorithm.cs
│   │   │   ├── EquityTickQuoteAdjustedModeRegressionAlgorithm.cs
│   │   │   ├── EquityTradeAndQuotesRegressionAlgorithm.cs
│   │   │   ├── ETFConstituentsFrameworkAlgorithm.cs
│   │   │   ├── ETFConstituentsFrameworkWithDifferentSelectionModelAlgorithm.cs
│   │   │   ├── ETFGlobalRotationAlgorithm.cs
│   │   │   ├── EuropeanOptionsCannotBeExercisedBeforeExpiryRegressionAlgorithm.cs
│   │   │   ├── ExecutionModelOrderEventsRegressionAlgorithm.cs
│   │   │   ├── ExpiryHelperAlphaModelFrameworkAlgorithm.cs
│   │   │   ├── ExtendedMarketHoursHistoryRegressionAlgorithm.cs
│   │   │   ├── ExtendedMarketTradingRegressionAlgorithm.cs
│   │   │   ├── FeeModelNotUsingAccountCurrency.cs
│   │   │   ├── FillForwardEnumeratorOutOfOrderBarRegressionAlgorithm.cs
│   │   │   ├── FillForwardFromWarmUpRegressionAlgorithm.cs
│   │   │   ├── FillForwardResolutionAdjustedOnRemovalRegressionAlgorithm.cs
│   │   │   ├── FillForwardStrictEndTimeDailyRegressionAlgorithm.cs
│   │   │   ├── FillForwardStrictEndTimeHourRegressionAlgorithm.cs
│   │   │   ├── FillForwardStrictEndTimeMinuteRegressionAlgorithm.cs
│   │   │   ├── FillForwardUntilExpiryRegressionAlgorithm.cs
│   │   │   ├── FillOutsideHoursDailyResolutionAlgorithm.cs
│   │   │   ├── FillOutsideHoursHourResolutionAlgorithm.cs
│   │   │   ├── FillOutsideHoursMinuteResolutionAlgorithm.cs
│   │   │   ├── FillOutsideHoursSecondResolutionAlgorithm.cs
│   │   │   ├── FillOutsideHoursTickResolutionAlgorithm.cs
│   │   │   ├── FilteredIdentityAlgorithm.cs
│   │   │   ├── FinancialAdvisorDemoAlgorithm.cs
│   │   │   ├── FineFundamentalFilteredUniverseRegressionAlgorithm.cs
│   │   │   ├── ForexInternalFeedOnDataHigherResolutionRegressionAlgorithm.cs
│   │   │   ├── ForexInternalFeedOnDataSameResolutionRegressionAlgorithm.cs
│   │   │   ├── ForexMultiResolutionRegressionAlgorithm.cs
│   │   │   ├── ForwardDataOnlyFillModelAlgorithm.cs
│   │   │   ├── FractionalQuantityRegressionAlgorithm.cs
│   │   │   ├── FreePortfolioValueFixedRegressionAlgorithm.cs
│   │   │   ├── FreePortfolioValueRegressionAlgorithm.cs
│   │   │   ├── FuncRiskFreeRateInterestRateModelWithPythonLambda.cs
│   │   │   ├── FundamentalCustomSelectionTimeRegressionAlgorithm.cs
│   │   │   ├── FundamentalCustomSelectionTimeWarmupRegressionAlgorithm.cs
│   │   │   ├── FundamentalRegressionAlgorithm.cs
│   │   │   ├── FundamentalUniverseSelectionRegressionAlgorithm.cs
│   │   │   ├── FutureChainInternalSubscriptionsRegressionAlgorithm.cs
│   │   │   ├── FutureContractsExtendedMarketHoursRegressionAlgorithm.cs
│   │   │   ├── FutureMarketOpenAndCloseRegressionAlgorithm.cs
│   │   │   ├── FutureMarketOpenAndCloseWithExtendedMarketRegressionAlgorithm.cs
│   │   │   ├── FutureMarketOpenConsolidatorRegressionAlgorithm.cs
│   │   │   ├── FutureMarketOpenConsolidatorWithExtendedMarketRegressionAlgorithm.cs
│   │   │   ├── FutureNoTimeInUniverseRegressionAlgorithm.cs
│   │   │   ├── FutureOptionBuySellCallIntradayRegressionAlgorithm.cs
│   │   │   ├── FutureOptionCallITMExpiryRegressionAlgorithm.cs
│   │   │   ├── FutureOptionCallITMGreeksExpiryRegressionAlgorithm.cs
│   │   │   ├── FutureOptionCallOTMExpiryRegressionAlgorithm.cs
│   │   │   ├── FutureOptionChainFullDataRegressionAlgorithm.cs
│   │   │   ├── FutureOptionChainsMultipleFullDataRegressionAlgorithm.cs
│   │   │   ├── FutureOptionContinuousFutureRegressionAlgorithm.cs
│   │   │   ├── FutureOptionDailyRegressionAlgorithm.cs
│   │   │   ├── FutureOptionHourlyRegressionAlgorithm.cs
│   │   │   ├── FutureOptionIndicatorsRegressionAlgorithm.cs
│   │   │   ├── FutureOptionMultipleContractsInDifferentContractMonthsWithSameUnderlyingFutureRegressionAlgorithm.cs
│   │   │   ├── FutureOptionPutITMExpiryRegressionAlgorithm.cs
│   │   │   ├── FutureOptionPutOTMExpiryRegressionAlgorithm.cs
│   │   │   ├── FutureOptionShortCallITMExpiryRegressionAlgorithm.cs
│   │   │   ├── FutureOptionShortCallOTMExpiryRegressionAlgorithm.cs
│   │   │   ├── FutureOptionShortPutITMExpiryRegressionAlgorithm.cs
│   │   │   ├── FutureOptionShortPutOTMExpiryRegressionAlgorithm.cs
│   │   │   ├── FutureOptionWithFutureFilterRegressionAlgorithm.cs
│   │   │   ├── FuturesAndFutureOptionsUniverseSettingsRegressionAlgorithm.cs
│   │   │   ├── FuturesAndFuturesOptionsExpiryTimeAndLiquidationRegressionAlgorithm.cs
│   │   │   ├── FuturesAutomaticSeedRegressionAlgorithm.cs
│   │   │   ├── FuturesChainFullDataRegressionAlgorithm.cs
│   │   │   ├── FuturesChainsMultipleFullDataRegressionAlgorithm.cs
│   │   │   ├── FuturesDailySettlementLongRegressionAlgorithm.cs
│   │   │   ├── FuturesDailySettlementShortRegressionAlgorithm.cs
│   │   │   ├── FuturesExpiredContractRegression.cs
│   │   │   ├── FuturesExtendedMarketHoursRegressionAlgorithm.cs
│   │   │   ├── FuturesFrameworkRegressionAlgorithm.cs
│   │   │   ├── FutureSharingTickerRegressionAlgorithm.cs
│   │   │   ├── FuturesMomentumAlgorithm.cs
│   │   │   ├── FutureStopMarketOrderOnExtendedHoursRegressionAlgorithm.cs
│   │   │   ├── FutureUniverseHistoryRegressionAlgorithm.cs
│   │   │   ├── FutureUniverseOpenInterestRegressionAlgorithm.cs
│   │   │   ├── FuzzyInferenceAlgorithm.cs
│   │   │   ├── G10CurrencySelectionModelFrameworkAlgorithm.cs
│   │   │   ├── GetParameterRegressionAlgorithm.cs
│   │   │   ├── HistoricalReturnsAlphaModelFrameworkRegressionAlgorithm.cs
│   │   │   ├── HistoryAlgorithm.cs
│   │   │   ├── HistoryAuxiliaryDataRegressionAlgorithm.cs
│   │   │   ├── HistoryProviderManagerRegressionAlgorithm.cs
│   │   │   ├── HistoryTickRegressionAlgorithm.cs
│   │   │   ├── HistoryWithCustomDataSourceRegressionAlgorithm.cs
│   │   │   ├── HistoryWithDifferentContinuousContractDepthOffsetsRegressionAlgorithm.cs
│   │   │   ├── HistoryWithDifferentDataMappingModeRegressionAlgorithm.cs
│   │   │   ├── HistoryWithDifferentDataNormalizationModeRegressionAlgorithm.cs
│   │   │   ├── HistoryWithSymbolChangesRegressionAlgorithm.cs
│   │   │   ├── HourMarketOrderFillsAtBarCloseRegressionAlgorithm.cs
│   │   │   ├── HourResolutionMappingEventRegressionAlgorithm.cs
│   │   │   ├── HourResolutionMarketOrderStalePriceRegressionAlgorithm.cs
│   │   │   ├── HourReverseSplitRegressionAlgorithm.cs
│   │   │   ├── HourSplitRegressionAlgorithm.cs
│   │   │   ├── HSIFutureDailyRegressionAlgorithm.cs
│   │   │   ├── HSIFutureHourRegressionAlgorithm.cs
│   │   │   ├── ImmediateExecutionModelMinimumOrderMarginRegressionAlgorithm.cs
│   │   │   ├── ImmediateExecutionModelWorksWithBinanceFeeModel.cs
│   │   │   ├── InceptionDateSelectionRegressionAlgorithm.cs
│   │   │   ├── IndexOptionBearCallSpreadAlgorithm.cs
│   │   │   ├── IndexOptionBearPutSpreadAlgorithm.cs
│   │   │   ├── IndexOptionBullCallSpreadAlgorithm.cs
│   │   │   ├── IndexOptionBullPutSpreadAlgorithm.cs
│   │   │   ├── IndexOptionBuySellCallIntradayRegressionAlgorithm.cs
│   │   │   ├── IndexOptionCallButterflyAlgorithm.cs
│   │   │   ├── IndexOptionCallCalendarSpreadAlgorithm.cs
│   │   │   ├── IndexOptionCallITMExpiryDailyRegressionAlgorithm.cs
│   │   │   ├── IndexOptionCallITMExpiryRegressionAlgorithm.cs
│   │   │   ├── IndexOptionCallITMGreeksExpiryRegressionAlgorithm.cs
│   │   │   ├── IndexOptionCallOTMExpiryDailyRegressionAlgorithm.cs
│   │   │   ├── IndexOptionCallOTMExpiryRegressionAlgorithm.cs
│   │   │   ├── IndexOptionChainApisConsistencyRegressionAlgorithm.cs
│   │   │   ├── IndexOptionIndicatorsRegressionAlgorithm.cs
│   │   │   ├── IndexOptionIronCondorAlgorithm.cs
│   │   │   ├── IndexOptionModelsConsistencyRegressionAlgorithm.cs
│   │   │   ├── IndexOptionPutButterflyAlgorithm.cs
│   │   │   ├── IndexOptionPutCalendarSpreadAlgorithm.cs
│   │   │   ├── IndexOptionPutITMExpiryRegressionAlgorithm.cs
│   │   │   ├── IndexOptionPutOTMExpiryRegressionAlgorithm.cs
│   │   │   ├── IndexOptionScaledStrikeRegressionAlgorithm.cs
│   │   │   ├── IndexOptionShortCallITMExpiryRegressionAlgorithm.cs
│   │   │   ├── IndexOptionShortCallOTMExpiryRegressionAlgorithm.cs
│   │   │   ├── IndexOptionShortPutITMExpiryRegressionAlgorithm.cs
│   │   │   ├── IndexOptionShortPutOTMExpiryRegressionAlgorithm.cs
│   │   │   ├── IndexOptionsUniverseSettingsRegressionAlgorithm.cs
│   │   │   ├── IndexOptionUniverseOpenInterestRegressionAlgorithm.cs
│   │   │   ├── IndexSecurityCanBeTradableRegressionAlgorithm.cs
│   │   │   ├── IndexSecurityIsNotTradableRegressionAlgorithm.cs
│   │   │   ├── IndiaDataRegressionAlgorithm.cs
│   │   │   ├── IndicatorBasedOptionPricingModelIndexOptionRegressionAlgorithm.cs
│   │   │   ├── IndicatorBasedOptionPricingModelRegressionAlgorithm.cs
│   │   │   ├── IndicatorHistoryAlgorithm.cs
│   │   │   ├── IndicatorHistoryRegressionAlgorithm.cs
│   │   │   ├── IndicatorSelectorsWorkWithDifferentOptions.cs
│   │   │   ├── IndicatorSuiteAlgorithm.cs
│   │   │   ├── IndicatorVolatilityModelAlgorithm.cs
│   │   │   ├── IndicatorWarmupAlgorithm.cs
│   │   │   ├── IndicatorWithRenkoBarsRegressionAlgorithm.cs
│   │   │   ├── IndustryStandardSecurityIdentifiersRegressionAlgorithm.cs
│   │   │   ├── InsightScoringRegressionAlgorithm.cs
│   │   │   ├── InsightTagAlphaRegressionAlgorithm.cs
│   │   │   ├── InsightWeightingFrameworkAlgorithm.cs
│   │   │   ├── InsufficientBuyingPowerForAutomaticExerciseRegressionAlgorithm.cs
│   │   │   ├── InsufficientMarginOrderUpdateRegressionAlgorithm.cs
│   │   │   ├── InteractiveBrokersBrokerageDisablesIndexOptionsExerciseRegressionAlgorithm.cs
│   │   │   ├── InternalSubscriptionHistoryRequestAlgorithm.cs
│   │   │   ├── IronCondorStrategyAlgorithm.cs
│   │   │   ├── IsMarketOpenCheckAlgorithm.cs
│   │   │   ├── IsMarketOpenCheckWithExtendedMarketHoursAlgorithm.cs
│   │   │   ├── LargeQuantityOptionStrategyAlgorithm.cs
│   │   │   ├── LeveragePrecedenceRegressionAlgorithm.cs
│   │   │   ├── LimitFillRegressionAlgorithm.cs
│   │   │   ├── LimitIfTouchedAsyncRegressionAlgorithm.cs
│   │   │   ├── LimitIfTouchedRegressionAlgorithm.cs
│   │   │   ├── LimitOrdersAreFilledAfterHoursForFuturesRegressionAlgorithm.cs
│   │   │   ├── LiquidateAllExceptSpecifiedSymbolRegressionAlgorithm.cs
│   │   │   ├── LiquidateRegressionAlgorithm.cs
│   │   │   ├── LiquidateUsingSetHoldingsRegressionAlgorithm.cs
│   │   │   ├── LiquidatingMultipleOptionStrategiesRegressionAlgorithm.cs
│   │   │   ├── LiquidETFUniverseFrameworkAlgorithm.cs
│   │   │   ├── LiveFeaturesAlgorithm.cs
│   │   │   ├── LongAndShortButterflyCallStrategiesAlgorithm.cs
│   │   │   ├── LongAndShortButterflyPutStrategiesAlgorithm.cs
│   │   │   ├── LongAndShortCallCalendarSpreadStrategiesAlgorithm.cs
│   │   │   ├── LongAndShortPutCalendarSpreadStrategiesAlgorithm.cs
│   │   │   ├── LongAndShortStraddleStrategiesAlgorithm.cs
│   │   │   ├── LongAndShortStrangleStrategiesAlgorithm.cs
│   │   │   ├── LongOnlyAlphaStreamAlgorithm.cs
│   │   │   ├── MacdAlphaModelFrameworkRegressionAlgorithm.cs
│   │   │   ├── MACDTrendAlgorithm.cs
│   │   │   ├── ManualContinuousFuturesPositionRolloverFromSymbolChangedEventHandlerRegressionAlgorithm.cs
│   │   │   ├── ManualContinuousFuturesPositionRolloverRegressionAlgorithm.cs
│   │   │   ├── ManuallySetMarketHoursAndSymbolPropertiesDatabaseEntriesAlgorithm.cs
│   │   │   ├── MappedBenchmarkRegressionAlgorithm.cs
│   │   │   ├── MarginCallClosedMarketRegressionAlgorithm.cs
│   │   │   ├── MarginCallEventsAlgorithm.cs
│   │   │   ├── MarginRemainingRegressionAlgorithm.cs
│   │   │   ├── MarketHourAwareIntradayConsolidationRegressionAlgorithm.cs
│   │   │   ├── MarketImpactSlippageModelRegressionAlgorithm.cs
│   │   │   ├── MarketOnCloseOrderAsyncRegressionAlgorithm.cs
│   │   │   ├── MarketOnCloseOrderBufferCheckRegressionAlgorithm.cs
│   │   │   ├── MarketOnCloseOrderBufferExtendedMarketHoursRegressionAlgorithm.cs
│   │   │   ├── MarketOnCloseOrderBufferRegressionAlgorithm.cs
│   │   │   ├── MarketOnCloseOrderFillsOnCloseTradeWithTickResolutionAlgorithm.cs
│   │   │   ├── MarketOnCloseOrderRegressionAlgorithm.cs
│   │   │   ├── MarketOnOpenOnCloseAlgorithm.cs
│   │   │   ├── MarketOnOpenOrderAsyncRegressionAlgorithm.cs
│   │   │   ├── MarketOnOpenOrderFillsOnOpenTradeWithTickResolutionAlgorithm.cs
│   │   │   ├── MarketOnOpenOrderRegressionAlgorithm.cs
│   │   │   ├── MarketOrdersAreSupportedOnExtendedHoursForFuturesRegressionAlgorithm.cs
│   │   │   ├── MarketOrderStaleDataFillRegressionAlgorithm.cs
│   │   │   ├── MaximumDrawdownPercentPerSecurityFrameworkRegressionAlgorithm.cs
│   │   │   ├── MaximumDrawdownPercentPortfolioFrameworkRegressionAlgorithm.cs
│   │   │   ├── MaximumSectorExposureRiskManagementModelFrameworkRegressionAlgorithm.cs
│   │   │   ├── MaximumUnrealizedProfitPercentPerSecurityFrameworkRegressionAlgorithm.cs
│   │   │   ├── MeanReversionPortfolioAlgorithm.cs
│   │   │   ├── MeanVarianceOptimizationFrameworkAlgorithm.cs
│   │   │   ├── MinimumOrderMarginRegressionAlgorithm.cs
│   │   │   ├── MinimumOrderSizeRegressionAlgorithm.cs
│   │   │   ├── MissingTickDataAlgorithm.cs
│   │   │   ├── MovingAverageCrossAlgorithm.cs
│   │   │   ├── MultipleSymbolConsolidationAlgorithm.cs
│   │   │   ├── MultipleUniverseSelectionOrderRegressionAlgorithm.cs
│   │   │   ├── MultiResolutionConsolidators.cs
│   │   │   ├── MultiUniverseSharedSecurityRegressionAlgorithm.cs
│   │   │   ├── NakedCallStrategyAlgorithm.cs
│   │   │   ├── NakedPutStrategyAlgorithm.cs
│   │   │   ├── NakedShortOptionStrategyOverMarginAlgorithm.cs
│   │   │   ├── NamedArgumentsRegression.cs
│   │   │   ├── NikkeiIndexRegressionAlgorithm.cs
│   │   │   ├── NoMarginCallExpectedRegressionAlgorithm.cs
│   │   │   ├── NoMarginCallOutsideRegularHoursRegressionAlgorithm.cs
│   │   │   ├── NoMinimumOrderMarginRegressionAlgorithm.cs
│   │   │   ├── NonDynamicOptionsFilterRegressionAlgorithm.cs
│   │   │   ├── NoUniverseSelectorRegressionAlgorithm.cs
│   │   │   ├── NullBuyingPowerOptionBullCallSpreadAlgorithm.cs
│   │   │   ├── NullMarginComboOrderRegressionAlgorithm.cs
│   │   │   ├── NullMarginMultipleOrdersRegressionAlgorithm.cs
│   │   │   ├── NullOptionAssignmentRegressionAlgorithm.cs
│   │   │   ├── NumeraiSignalExportDemonstrationAlgorithm.cs
│   │   │   ├── ObjectStoreExampleAlgorithm.cs
│   │   │   ├── OnEndOfDayAddDataRegressionAlgorithm.cs
│   │   │   ├── OnEndOfDayInternalSecurityRegressionAlgorithm.cs
│   │   │   ├── OnEndOfDayRegressionAlgorithm.cs
│   │   │   ├── OnOrderEventExceptionRegression.cs
│   │   │   ├── OnWarmupFinishedNoWarmup.cs
│   │   │   ├── OnWarmupFinishedOrderingRegressionAlgorithm.cs
│   │   │   ├── OnWarmupFinishedRegressionAlgorithm.cs
│   │   │   ├── OnWarmupFinishedScheduledUniverseRegressionAlgorithm.cs
│   │   │   ├── OpeningBreakoutAlgorithm.cs
│   │   │   ├── OpenInterestFuturesRegressionAlgorithm.cs
│   │   │   ├── OptionAssignmentRegressionAlgorithm.cs
│   │   │   ├── OptionAssignmentStatisticsRegressionAlgorithm.cs
│   │   │   ├── OptionChainApisConsistencyRegressionAlgorithm.cs
│   │   │   ├── OptionChainConsistencyRegressionAlgorithm.cs
│   │   │   ├── OptionChainedAndUniverseSelectionRegressionAlgorithm.cs
│   │   │   ├── OptionChainedUniverseSelectionModelRegressionAlgorithm.cs
│   │   │   ├── OptionChainFullDataRegressionAlgorithm.cs
│   │   │   ├── OptionChainIncludeWeeklysByDefaultRegressionAlgorithm.cs
│   │   │   ├── OptionChainProviderAlgorithm.cs
│   │   │   ├── OptionChainsMultipleFullDataRegressionAlgorithm.cs
│   │   │   ├── OptionChainSubscriptionRemovalRegressionAlgorithm.cs
│   │   │   ├── OptionChainUniverseImmediateSelectionRegressionAlgorithm.cs
│   │   │   ├── OptionChainUniverseRemovalRegressionAlgorithm.cs
│   │   │   ├── OptionDataNullReferenceRegressionAlgorithm.cs
│   │   │   ├── OptionDelistedDataRegressionAlgorithm.cs
│   │   │   ├── OptionEquityBaseStrategyRegressionAlgorithm.cs
│   │   │   ├── OptionEquityBearCallLadderRegressionAlgorithm.cs
│   │   │   ├── OptionEquityBearCallSpreadRegressionAlgorithm.cs
│   │   │   ├── OptionEquityBearCallSpreadSetHoldingsRegressionAlgorithm.cs
│   │   │   ├── OptionEquityBearPutLadderRegressionAlgorithm.cs
│   │   │   ├── OptionEquityBearPutSpreadRegressionAlgorithm.cs
│   │   │   ├── OptionEquityBoxSpreadRegressionAlgorithm.cs
│   │   │   ├── OptionEquityBullCallLadderRegressionAlgorithm.cs
│   │   │   ├── OptionEquityBullCallSpreadRegressionAlgorithm.cs
│   │   │   ├── OptionEquityBullPutLadderRegressionAlgorithm.cs
│   │   │   ├── OptionEquityBullPutSpreadRegressionAlgorithm.cs
│   │   │   ├── OptionEquityCallBackspreadRegressionAlgorithm.cs
│   │   │   ├── OptionEquityCallButterflyRegressionAlgorithm.cs
│   │   │   ├── OptionEquityCallCalendarSpreadRegressionAlgorithm.cs
│   │   │   ├── OptionEquityConversionRegressionAlgorithm.cs
│   │   │   ├── OptionEquityCoveredCallRegressionAlgorithm.cs
│   │   │   ├── OptionEquityCoveredPutRegressionAlgorithm.cs
│   │   │   ├── OptionEquityIronButterflyRegressionAlgorithm.cs
│   │   │   ├── OptionEquityIronCondorRegressionAlgorithm.cs
│   │   │   ├── OptionEquityJellyRollRegressionAlgorithm.cs
│   │   │   ├── OptionEquityOverlappingBullCallSpreadsRegressionAlgorithm.cs
│   │   │   ├── OptionEquityProtectiveCollarRegressionAlgorithm.cs
│   │   │   ├── OptionEquityPutBackspreadRegressionAlgorithm.cs
│   │   │   ├── OptionEquityPutButterflyRegressionAlgorithm.cs
│   │   │   ├── OptionEquityPutCalendarSpreadRegressionAlgorithm.cs
│   │   │   ├── OptionEquityReverseConversionRegressionAlgorithm.cs
│   │   │   ├── OptionEquityShortBoxSpreadRegressionAlgorithm.cs
│   │   │   ├── OptionEquityShortButterflyCallRegressionAlgorithm.cs
│   │   │   ├── OptionEquityShortButterflyPutRegressionAlgorithm.cs
│   │   │   ├── OptionEquityShortCallBackspreadRegressionAlgorithm.cs
│   │   │   ├── OptionEquityShortIronButterflyRegressionAlgorithm.cs
│   │   │   ├── OptionEquityShortIronCondorRegressionAlgorithm.cs
│   │   │   ├── OptionEquityShortJellyRollRegressionAlgorithm.cs
│   │   │   ├── OptionEquityShortPutBackspreadRegressionAlgorithm.cs
│   │   │   ├── OptionEquityStraddleRegressionAlgorithm.cs
│   │   │   ├── OptionEquityStrangleRegressionAlgorithm.cs
│   │   │   ├── OptionEquityStrategyMatcherRegressionAlgorithm.cs
│   │   │   ├── OptionExerciseAssignRegressionAlgorithm.cs
│   │   │   ├── OptionExerciseOnExpiryAndNonTradableDateRegressionAlgorithm.cs
│   │   │   ├── OptionExerciseOnExpiryAndNonTradableDateWithOptionSelectionRegressionAlgorithm.cs
│   │   │   ├── OptionExerciseRegressionAlgorithm.cs
│   │   │   ├── OptionExpiryDateOnHolidayCase.cs
│   │   │   ├── OptionExpiryDateTodayRegressionAlgorithm.cs
│   │   │   ├── OptionFilterReturnsNullRegressionAlgorithm.cs
│   │   │   ├── OptionGreeksRegressionAlgorithm.cs
│   │   │   ├── OptionIndicatorsMirrorContractsRegressionAlgorithm.cs
│   │   │   ├── OptionIndicatorsRegressionAlgorithm.cs
│   │   │   ├── OptionModelsConsistencyRegressionAlgorithm.cs
│   │   │   ├── OptionNoTimeInUniverseRegressionAlgorithm.cs
│   │   │   ├── OptionOpenInterestRegressionAlgorithm.cs
│   │   │   ├── OptionOrdersOnSplitRegressionAlgorithm.cs
│   │   │   ├── OptionOTMExpiryOrderHasZeroPriceRegressionAlgorithm.cs
│   │   │   ├── OptionPriceModelForOptionStylesBaseRegressionAlgorithm.cs
│   │   │   ├── OptionPriceModelForSupportedAmericanOptionRegressionAlgorithm.cs
│   │   │   ├── OptionPriceModelForSupportedAmericanOptionTimeSpanWarmupRegressionAlgorithm.cs
│   │   │   ├── OptionPriceModelForSupportedEuropeanOptionRegressionAlgorithm.cs
│   │   │   ├── OptionPriceModelForSupportedEuropeanOptionTimeSpanWarmupRegressionAlgorithm.cs
│   │   │   ├── OptionPriceModelForUnsupportedAmericanOptionRegressionAlgorithm.cs
│   │   │   ├── OptionPriceModelForUnsupportedAmericanOptionTimeSpanWarmupRegressionAlgorithm.cs
│   │   │   ├── OptionPriceModelForUnsupportedEuropeanOptionRegressionAlgorithm.cs
│   │   │   ├── OptionPriceModelForUnsupportedEuropeanOptionTimeSpanWarmupRegressionAlgorithm.cs
│   │   │   ├── OptionRenameDailyRegressionAlgorithm.cs
│   │   │   ├── OptionRenameRegressionAlgorithm.cs
│   │   │   ├── OptionResolutionRegressionAlgorithm.cs
│   │   │   ├── OptionsAutomaticSeedRegressionAlgorithm.cs
│   │   │   ├── OptionsExpiredContractRegression.cs
│   │   │   ├── OptionShortCallMarginCallEventsAlgorithm.cs
│   │   │   ├── OptionsMarginCallEventsAlgorithmBase.cs
│   │   │   ├── OptionSplitRegressionAlgorithm.cs
│   │   │   ├── OptionSplitWarmupRegressionAlgorithm.cs
│   │   │   ├── OptionStrategyFactoryMethodsBaseAlgorithm.cs
│   │   │   ├── OptionStrategyFilteringUniverseBaseAlgorithm.cs
│   │   │   ├── OptionStrategyFilteringUniverseBoxSpreadRegressionAlgorithm.cs
│   │   │   ├── OptionStrategyFilteringUniverseCallButterflyRegressionAlgorithm.cs
│   │   │   ├── OptionStrategyFilteringUniverseCallCalendarSpreadRegressionAlgorithm.cs
│   │   │   ├── OptionStrategyFilteringUniverseCallLadderRegressionAlgorithm.cs
│   │   │   ├── OptionStrategyFilteringUniverseCallSpreadRegressionAlgorithm.cs
│   │   │   ├── OptionStrategyFilteringUniverseConversionRegressionAlgorithm.cs
│   │   │   ├── OptionStrategyFilteringUniverseIronCondorRegressionAlgorithm.cs
│   │   │   ├── OptionStrategyFilteringUniverseJellyRollRegressionAlgorithm.cs
│   │   │   ├── OptionStrategyFilteringUniverseProtectiveCollarRegressionAlgorithm.cs
│   │   │   ├── OptionStrategyFilteringUniversePutButterflyRegressionAlgorithm.cs
│   │   │   ├── OptionStrategyFilteringUniversePutCalendarSpreadRegressionAlgorithm.cs
│   │   │   ├── OptionStrategyFilteringUniversePutLadderRegressionAlgorithm.cs
│   │   │   ├── OptionStrategyFilteringUniversePutSpreadRegressionAlgorithm.cs
│   │   │   ├── OptionStrategyFilteringUniverseSingleCallRegressionAlgorithm.cs
│   │   │   ├── OptionStrategyFilteringUniverseSinglePutRegressionAlgorithm.cs
│   │   │   ├── OptionStrategyFilteringUniverseStraddleRegressionAlgorithm.cs
│   │   │   ├── OptionStrategyFilteringUniverseStrangleRegressionAlgorithm.cs
│   │   │   ├── OptionStrategyMarginCallEventsAlgorithm.cs
│   │   │   ├── OptionSymbolCanonicalRegressionAlgorithm.cs
│   │   │   ├── OptionTimeSliceRegressionAlgorithm.cs
│   │   │   ├── OptionUniverseFilterGreeksRegressionAlgorithm.cs
│   │   │   ├── OptionUniverseFilterGreeksShortcutsRegressionAlgorithm.cs
│   │   │   ├── OptionUniverseFilterOptionsDataLinqRegressionAlgorithm.cs
│   │   │   ├── OptionUniverseFilterOptionsDataRegressionAlgorithm.cs
│   │   │   ├── OptionUniverseHistoryRegressionAlgorithm.cs
│   │   │   ├── OptionUniverseOpenInterestRegressionAlgorithm.cs
│   │   │   ├── OptionUniverseRemovedAndReAddedMemberCleanupRegressionAlgorithm.cs
│   │   │   ├── OptionUniverseRemovedAndReAddedRegressionAlgorithm.cs
│   │   │   ├── OrderImmutabilityRegressionAlgorithm.cs
│   │   │   ├── OrderSubmissionDataRegressionAlgorithm.cs
│   │   │   ├── OrderTicketAssignmentDemoAlgorithm.cs
│   │   │   ├── OrderTicketDemoAlgorithm.cs
│   │   │   ├── ParameterizedAlgorithm.cs
│   │   │   ├── PearsonCorrelationPairsTradingAlphaModelFrameworkAlgorithm.cs
│   │   │   ├── PeriodBasedHistoryRequestNotAllowedWithTickResolutionRegressionAlgorithm.cs
│   │   │   ├── PeriodConsolidatorRegressionAlgorithm.cs
│   │   │   ├── PersistentCustomDataUniverseRegressionAlgorithm.cs
│   │   │   ├── PortfolioOptimizationNumericsAlgorithm.cs
│   │   │   ├── PortfolioRebalanceOnCustomFuncRegressionAlgorithm.cs
│   │   │   ├── PortfolioRebalanceOnDateRulesRegressionAlgorithm.cs
│   │   │   ├── PortfolioRebalanceOnInsightChangesRegressionAlgorithm.cs
│   │   │   ├── PortfolioRebalanceOnSecurityChangesRegressionAlgorithm.cs
│   │   │   ├── PortfolioTargetTagsRegressionAlgorithm.cs
│   │   │   ├── ProcessSplitSymbolsRegressionAlgorithm.cs
│   │   │   ├── Properties
│   │   │   │   └── AssemblyInfo.cs
│   │   │   ├── QLOptionPricingModelRegressionAlgorithm.cs
│   │   │   ├── QuantConnect.Algorithm.CSharp.csproj
│   │   │   ├── QuitAfterInitializationRegressionAlgorithm.cs
│   │   │   ├── QuitInInitializationRegressionAlgorithm.cs
│   │   │   ├── RangeConsolidatorAlgorithm.cs
│   │   │   ├── RangeConsolidatorWithTickAlgorithm.cs
│   │   │   ├── RawDataRegressionAlgorithm.cs
│   │   │   ├── RawPricesCoarseUniverseAlgorithm.cs
│   │   │   ├── RawPricesUniverseRegressionAlgorithm.cs
│   │   │   ├── RegisterIndicatorAndConsolidatorWithoutSubscriptionRegressionAlgorithm.cs
│   │   │   ├── RegisterIndicatorRegressionAlgorithm.cs
│   │   │   ├── RegressionAlgorithm.cs
│   │   │   ├── RegressionChannelAlgorithm.cs
│   │   │   ├── RegressionTests
│   │   │   │   ├── Collective2IndexOptionAlgorithm.cs
│   │   │   │   ├── CorrelationLastComputedValueRegressionAlgorithm.cs
│   │   │   │   ├── CustomData
│   │   │   │   │   ├── CustomDataIconicTypesAddDataRegressionAlgorithm.cs
│   │   │   │   │   ├── CustomDataIconicTypesDefaultResolutionRegressionAlgorithm.cs
│   │   │   │   │   ├── CustomDataLinkedIconicTypeAddDataCoarseSelectionRegressionAlgorithm.cs
│   │   │   │   │   ├── CustomDataLinkedIconicTypeAddDataOnSecuritiesChangedRegressionAlgorithm.cs
│   │   │   │   │   └── CustomDataUnlinkedTradeBarIconicTypeConsolidationRegressionAlgorithm.cs
│   │   │   │   └── Universes
│   │   │   │       ├── ETFConstituentUniverseCompositeDelistingRegressionAlgorithm.cs
│   │   │   │       ├── ETFConstituentUniverseCompositeDelistingRegressionAlgorithmNoAddEquityETF.cs
│   │   │   │       ├── ETFConstituentUniverseFilterFunctionRegressionAlgorithm.cs
│   │   │   │       ├── ETFConstituentUniverseFrameworkRegressionAlgorithm.cs
│   │   │   │       ├── ETFConstituentUniverseFrameworkRegressionAlgorithmNewUniverseModel.cs
│   │   │   │       ├── ETFConstituentUniverseImmediateSelectionRegressionAlgorithm.cs
│   │   │   │       ├── ETFConstituentUniverseMappedCompositeRegressionAlgorithm.cs
│   │   │   │       └── ETFConstituentUniverseRSIAlphaModelAlgorithm.cs
│   │   │   ├── RemoveUnderlyingRegressionAlgorithm.cs
│   │   │   ├── ResolutionSwitchingAlgorithm.cs
│   │   │   ├── RestingMarketOrderFillsAtBarOpenRegressionAlgorithm.cs
│   │   │   ├── RevertComboOrderPositionsAlgorithm.cs
│   │   │   ├── RiskParityPortfolioAlgorithm.cs
│   │   │   ├── RiskParityPortfolioWeightsCheckAlgorithm.cs
│   │   │   ├── RollingWindowAlgorithm.cs
│   │   │   ├── RollOutFrontMonthToBackMonthOptionUsingCalendarSpreadRegressionAlgorithm.cs
│   │   │   ├── RsiAlphaModelFrameworkRegressionAlgorithm.cs
│   │   │   ├── RuntimeCurrencyConversionSeedingRegressionAlgorithm.cs
│   │   │   ├── SamcoBasicTemplateOptionsAlgorithm.cs
│   │   │   ├── ScaledFillForwardDataRegressionAlgorithm.cs
│   │   │   ├── ScaledRawDataNormalizationModeNotAllowedSecuritiesAlgorithm.cs
│   │   │   ├── ScaledRawHistoryAlgorithm.cs
│   │   │   ├── ScheduledEventsAlgorithm.cs
│   │   │   ├── ScheduledEventsOrderRegressionAlgorithm.cs
│   │   │   ├── ScheduledQueuingAlgorithm.cs
│   │   │   ├── ScheduledUniverseRegressionAlgorithm.cs
│   │   │   ├── ScheduledUniverseSelectionModelRegressionAlgorithm.cs
│   │   │   ├── SectorExposureRiskFrameworkAlgorithm.cs
│   │   │   ├── SectorWeightingFrameworkAlgorithm.cs
│   │   │   ├── SecurityCustomPropertiesAlgorithm.cs
│   │   │   ├── SecurityInitializationOnReAdditionForEquityRegressionAlgorithm.cs
│   │   │   ├── SecurityInitializationOnReAdditionForManuallyAddedFutureContractRegressionAlgorithm.cs
│   │   │   ├── SecurityInitializationOnReAdditionForManuallyAddedOptionRegressionAlgorithm.cs
│   │   │   ├── SecurityInitializationOnReAdditionForSelectedOptionRegressionAlgorithm.cs
│   │   │   ├── SecurityInitializationOnReAdditionForUniverseSelectionRegressionAlgorithm.cs
│   │   │   ├── SecuritySeederRegressionAlgorithm.cs
│   │   │   ├── SecuritySessionDailyNoPreciseEndTimeRegressionAlgorithm.cs
│   │   │   ├── SecuritySessionExtendedMarketHoursRegressionAlgorithm.cs
│   │   │   ├── SecuritySessionRegressionAlgorithm.cs
│   │   │   ├── SecuritySessionWithChangeOfResolutionRegressionAlgorithm.cs
│   │   │   ├── SecuritySessionWithDailyResolutionRegressionAlgorithm.cs
│   │   │   ├── SecuritySessionWithFutureContractRegressionAlgorithm.cs
│   │   │   ├── SecuritySessionWithFuturesExtendedMarketHoursRegressionAlgorithm.cs
│   │   │   ├── SecuritySessionWithFuturesRegressionAlgorithm.cs
│   │   │   ├── SecuritySessionWithOptionRegressionAlgorithm.cs
│   │   │   ├── SecurityToSymbolRegressionAlgorithm.cs
│   │   │   ├── SetAccountCurrencyCashBuyingPowerModelRegressionAlgorithm.cs
│   │   │   ├── SetAccountCurrencySecurityMarginModelRegressionAlgorithm.cs
│   │   │   ├── SetCashOnDataRegressionAlgorithm.cs
│   │   │   ├── SetCustomSettlementModelRegressionAlgorithm.cs
│   │   │   ├── SetDataNormalizationModeOnAddSecurityAlgorithm.cs
│   │   │   ├── SetEquityDataNormalizationModeOnAddEquity.cs
│   │   │   ├── SetHoldingReturnsOrderTicketsRegressionAlgorithm.cs
│   │   │   ├── SetHoldingsAsyncRegressionAlgorithm.cs
│   │   │   ├── SetHoldingsFutureRegressionAlgorithm.cs
│   │   │   ├── SetHoldingsLiquidateExistingHoldingsMultipleTargetsRegressionAlgorithm.cs
│   │   │   ├── SetHoldingsMarketOnOpenRegressionAlgorithm.cs
│   │   │   ├── SetHoldingsMultipleTargetsRegressionAlgorithm.cs
│   │   │   ├── SetHoldingsRegressionAlgorithm.cs
│   │   │   ├── ShortableProviderOrdersRejectedRegressionAlgorithm.cs
│   │   │   ├── ShortInterestFeeRegressionAlgorithm.cs
│   │   │   ├── SingleLotOptionStrategyMarginCallRegressionAlgorithm.cs
│   │   │   ├── SingleOptionPositionGroupBuyingPowerModelRegressionAlgorithm.cs
│   │   │   ├── SmaCrossUniverseSelectionAlgorithm.cs
│   │   │   ├── SparseDataRegressionAlgorithm.cs
│   │   │   ├── SplitEquityRegressionAlgorithm.cs
│   │   │   ├── SplitOnTradeBuilderRegressionAlgorithm.cs
│   │   │   ├── SplitPartialShareRegressionAlgorithm.cs
│   │   │   ├── SpreadExecutionModelRegressionAlgorithm.cs
│   │   │   ├── StableCoinsRegressionAlgorithm.cs
│   │   │   ├── StandardDeviationExecutionModelRegressionAlgorithm.cs
│   │   │   ├── StartingCapitalRegressionAlgorithm.cs
│   │   │   ├── StatisticsResultsAlgorithm.cs
│   │   │   ├── StochasticIndicatorAndSubIndicatorsWarmUpRegressionAlgorithm.cs
│   │   │   ├── StochasticIndicatorWarmsUpProperlyRegressionAlgorithm.cs
│   │   │   ├── StopLimitOrderRegressionAlgorithm.cs
│   │   │   ├── StopLimitOrderRegressionAsyncAlgorithm.cs
│   │   │   ├── StopLossOnOrderEventRegressionAlgorithm.cs
│   │   │   ├── StopMarketOrderAsyncRegressionAlgorithm.cs
│   │   │   ├── StopMarketOrderRegressionAlgorithm.cs
│   │   │   ├── StressSymbols.cs
│   │   │   ├── StressSymbolsAlgorithm.cs
│   │   │   ├── StrictEndTimeLowerResolutionFillForwardRegressionAlgorithm.cs
│   │   │   ├── StrictEndTimeLowerResolutionFillForwardWithExtendedMarketHoursRegressionAlgorithm.cs
│   │   │   ├── StringToSymbolImplicitConversionRegressionAlgorithm.cs
│   │   │   ├── SwitchDataModeRegressionAlgorithm.cs
│   │   │   ├── TickDataFilteringAlgorithm.cs
│   │   │   ├── TickHistoryRequestWithoutTickSubscriptionRegressionAlgorithm.cs
│   │   │   ├── TickQuoteBarConsolidatorWithDefaultTickTypeRegressionAlgorithm.cs
│   │   │   ├── TickQuoteBarConsolidatorWithTickTypeRegressionAlgorithm.cs
│   │   │   ├── TickTradeBarConsolidatorWithDefaultTickTypeRegressionAlgorithm.cs
│   │   │   ├── TickTradeBarConsolidatorWithQuoteTickTypeRegressionAlgorithm.cs
│   │   │   ├── TickTradeBarConsolidatorWithTradeTickTypeRegressionAlgorithm.cs
│   │   │   ├── TiingoPriceAlgorithm.cs
│   │   │   ├── TimeInForceAlgorithm.cs
│   │   │   ├── TimeRulesDefaultTimeZoneRegressionAlgorithm.cs
│   │   │   ├── TotalPortfolioValueRegressionAlgorithm.cs
│   │   │   ├── TradeStationBrokerageTradeWithOutsideRegularMarketHoursParameter.cs
│   │   │   ├── TradingNotAddedEquitiesRegressionAlgorithm.cs
│   │   │   ├── TradingNotAddedOptionsRegressionAlgorithm.cs
│   │   │   ├── TrailingStopOrderAsyncRegressionAlgorithm.cs
│   │   │   ├── TrailingStopOrderRegressionAlgorithm.cs
│   │   │   ├── TrailingStopRiskFrameworkRegressionAlgorithm.cs
│   │   │   ├── TrainingExampleAlgorithm.cs
│   │   │   ├── TrainingInitializeRegressionAlgorithm.cs
│   │   │   ├── TwoLegCurrencyConversionRegressionAlgorithm.cs
│   │   │   ├── UniverseOnlyRegressionAlgorithm.cs
│   │   │   ├── UniverseSelectedRegressionAlgorithm.cs
│   │   │   ├── UniverseSelectionDefinitionsAlgorithm.cs
│   │   │   ├── UniverseSelectionRegressionAlgorithm.cs
│   │   │   ├── UniverseSelectionSymbolCacheRemovalRegressionTest.cs
│   │   │   ├── UniverseSharingSecurityDifferentSubscriptionRequestRegressionAlgorithm.cs
│   │   │   ├── UniverseSharingSubscriptionRequestRegressionAlgorithm.cs
│   │   │   ├── UniverseSharingSubscriptionTradableRegressionAlgorithm.cs
│   │   │   ├── UniverseUnchangedRegressionAlgorithm.cs
│   │   │   ├── UnregisterIndicatorRegressionAlgorithm.cs
│   │   │   ├── UnsettledCashWhenQuoteCurrencyIsNotAccountCurrencyAlgorithm.cs
│   │   │   ├── UpdateOrderLiveTestAlgorithm.cs
│   │   │   ├── UpdateOrderRegressionAlgorithm.cs
│   │   │   ├── UserDefinedUniverseAlgorithm.cs
│   │   │   ├── VBaseSignalExportDemonstrationAlgorithm.cs
│   │   │   ├── VolatilityModelsWithRawDataAlgorithm.cs
│   │   │   ├── VolumeRenkoConsolidatorAlgorithm.cs
│   │   │   ├── VolumeShareSlippageModelAlgorithm.cs
│   │   │   ├── VolumeWeightedAveragePriceExecutionModelRegressionAlgorithm.cs
│   │   │   ├── WarmUpAfterInitializeRegression.cs
│   │   │   ├── WarmupAlgorithm.cs
│   │   │   ├── WarmupConversionRatesRegressionAlgorithm.cs
│   │   │   ├── WarmupDailyResolutionRegressionAlgorithm.cs
│   │   │   ├── WarmupDataTypesBarCountWarmupRegressionAlgorithm.cs
│   │   │   ├── WarmupDataTypesRegressionAlgorithm.cs
│   │   │   ├── WarmupFutureRegressionAlgorithm.cs
│   │   │   ├── WarmupFutureTimeSpanWarmupRegressionAlgorithm.cs
│   │   │   ├── WarmupHistoryAlgorithm.cs
│   │   │   ├── WarmupIndicatorRegressionAlgorithm.cs
│   │   │   ├── WarmupLowerResolutionBarCountRegressionAlgorithm.cs
│   │   │   ├── WarmupLowerResolutionBarCountSettingRegressionAlgorithm.cs
│   │   │   ├── WarmupLowerResolutionOptionRegressionAlgorithm.cs
│   │   │   ├── WarmupLowerResolutionSelectionRegressionAlgorithm.cs
│   │   │   ├── WarmupLowerResolutionTimeSpanRegressionAlgorithm.cs
│   │   │   ├── WarmupLowerResolutionTimeSpanSettingRegressionAlgorithm.cs
│   │   │   ├── WarmupMinuteResolutionRegressionAlgorithm.cs
│   │   │   ├── WarmupOptionRegressionAlgorithm.cs
│   │   │   ├── WarmupOptionResolutionRegressionAlgorithm.cs
│   │   │   ├── WarmupScheduledEventsRegressionAlgorithm.cs
│   │   │   ├── WarmupScheduledEventsTimeSpanWarmupRegressionAlgorithm.cs
│   │   │   ├── WarmupSelectionBarCountRegressionAlgorithm.cs
│   │   │   ├── WarmupSelectionRegressionAlgorithm.cs
│   │   │   ├── WarmupStartingPortfolioValueRegressionAlgorithm.cs
│   │   │   ├── WarmupTrainRegressionAlgorithm.cs
│   │   │   ├── WeeklyUniverseSelectionRegressionAlgorithm.cs
│   │   │   ├── YearlyUniverseSelectionScheduleRegressionAlgorithm.cs
│   │   │   ├── ZeroDTEIndexOptionsRegressionAlgorithm.cs
│   │   │   ├── ZeroDTEOptionsRegressionAlgorithm.cs
│   │   │   ├── ZeroedBenchmarkRegressionAlgorithm.cs
│   │   │   └── ZeroFeeRegressionAlgorithm.cs
│   │   ├── Algorithm.Framework
│   │   │   ├── Alphas
│   │   │   │   ├── BasePairsTradingAlphaModel.cs
│   │   │   │   ├── BasePairsTradingAlphaModel.py
│   │   │   │   ├── ConstantAlphaModel.cs
│   │   │   │   ├── ConstantAlphaModel.py
│   │   │   │   ├── EmaCrossAlphaModel.cs
│   │   │   │   ├── EmaCrossAlphaModel.py
│   │   │   │   ├── HistoricalReturnsAlphaModel.cs
│   │   │   │   ├── HistoricalReturnsAlphaModel.py
│   │   │   │   ├── MacdAlphaModel.cs
│   │   │   │   ├── MacdAlphaModel.py
│   │   │   │   ├── PearsonCorrelationPairsTradingAlphaModel.cs
│   │   │   │   ├── PearsonCorrelationPairsTradingAlphaModel.py
│   │   │   │   ├── RsiAlphaModel.cs
│   │   │   │   └── RsiAlphaModel.py
│   │   │   ├── Execution
│   │   │   │   ├── SpreadExecutionModel.cs
│   │   │   │   ├── SpreadExecutionModel.py
│   │   │   │   ├── StandardDeviationExecutionModel.cs
│   │   │   │   ├── StandardDeviationExecutionModel.py
│   │   │   │   ├── VolumeWeightedAveragePriceExecutionModel.cs
│   │   │   │   └── VolumeWeightedAveragePriceExecutionModel.py
│   │   │   ├── NotifiedSecurityChanges.cs
│   │   │   ├── Portfolio
│   │   │   │   ├── AccumulativeInsightPortfolioConstructionModel.cs
│   │   │   │   ├── AccumulativeInsightPortfolioConstructionModel.py
│   │   │   │   ├── AlphaStreamsPortfolioConstructionModel.cs
│   │   │   │   ├── BlackLittermanOptimizationPortfolioConstructionModel.cs
│   │   │   │   ├── BlackLittermanOptimizationPortfolioConstructionModel.py
│   │   │   │   ├── ConfidenceWeightedPortfolioConstructionModel.cs
│   │   │   │   ├── ConfidenceWeightedPortfolioConstructionModel.py
│   │   │   │   ├── EqualWeightingPortfolioConstructionModel.cs
│   │   │   │   ├── EqualWeightingPortfolioConstructionModel.py
│   │   │   │   ├── InsightWeightingPortfolioConstructionModel.cs
│   │   │   │   ├── InsightWeightingPortfolioConstructionModel.py
│   │   │   │   ├── MaximumSharpeRatioPortfolioOptimizer.cs
│   │   │   │   ├── MaximumSharpeRatioPortfolioOptimizer.py
│   │   │   │   ├── MeanReversionPortfolioConstructionModel.cs
│   │   │   │   ├── MeanReversionPortfolioConstructionModel.py
│   │   │   │   ├── MeanVarianceOptimizationPortfolioConstructionModel.cs
│   │   │   │   ├── MeanVarianceOptimizationPortfolioConstructionModel.py
│   │   │   │   ├── MinimumVariancePortfolioOptimizer.cs
│   │   │   │   ├── MinimumVariancePortfolioOptimizer.py
│   │   │   │   ├── PortfolioOptimizerPythonWrapper.cs
│   │   │   │   ├── ReturnsSymbolData.cs
│   │   │   │   ├── RiskParityPortfolioConstructionModel.cs
│   │   │   │   ├── RiskParityPortfolioConstructionModel.py
│   │   │   │   ├── RiskParityPortfolioOptimizer.cs
│   │   │   │   ├── RiskParityPortfolioOptimizer.py
│   │   │   │   ├── SectorWeightingPortfolioConstructionModel.cs
│   │   │   │   ├── SectorWeightingPortfolioConstructionModel.py
│   │   │   │   ├── UnconstrainedMeanVariancePortfolioOptimizer.cs
│   │   │   │   └── UnconstrainedMeanVariancePortfolioOptimizer.py
│   │   │   ├── Properties
│   │   │   │   └── AssemblyInfo.cs
│   │   │   ├── QuantConnect.Algorithm.Framework.csproj
│   │   │   ├── Risk
│   │   │   │   ├── MaximumDrawdownPercentPerSecurity.cs
│   │   │   │   ├── MaximumDrawdownPercentPerSecurity.py
│   │   │   │   ├── MaximumDrawdownPercentPortfolio.cs
│   │   │   │   ├── MaximumDrawdownPercentPortfolio.py
│   │   │   │   ├── MaximumSectorExposureRiskManagementModel.cs
│   │   │   │   ├── MaximumSectorExposureRiskManagementModel.py
│   │   │   │   ├── MaximumUnrealizedProfitPercentPerSecurity.cs
│   │   │   │   ├── MaximumUnrealizedProfitPercentPerSecurity.py
│   │   │   │   ├── TrailingStopRiskManagementModel.cs
│   │   │   │   └── TrailingStopRiskManagementModel.py
│   │   │   └── Selection
│   │   │       ├── CoarseFundamentalUniverseSelectionModel.cs
│   │   │       ├── EmaCrossUniverseSelectionModel.cs
│   │   │       ├── EmaCrossUniverseSelectionModel.py
│   │   │       ├── EnergyETFUniverse.cs
│   │   │       ├── ETFConstituentsUniverseSelectionModel.cs
│   │   │       ├── ETFConstituentsUniverseSelectionModel.py
│   │   │       ├── FineFundamentalUniverseSelectionModel.cs
│   │   │       ├── FundamentalUniverseSelectionModel.cs
│   │   │       ├── FundamentalUniverseSelectionModel.py
│   │   │       ├── FutureUniverseSelectionModel.cs
│   │   │       ├── FutureUniverseSelectionModel.py
│   │   │       ├── InceptionDateUniverseSelectionModel.cs
│   │   │       ├── LiquidETFUniverse.cs
│   │   │       ├── MetalsETFUniverse.cs
│   │   │       ├── OpenInterestFutureUniverseSelectionModel.cs
│   │   │       ├── OptionUniverseSelectionModel.cs
│   │   │       ├── OptionUniverseSelectionModel.py
│   │   │       ├── QC500UniverseSelectionModel.cs
│   │   │       ├── QC500UniverseSelectionModel.py
│   │   │       ├── ScheduledUniverseSelectionModel.cs
│   │   │       ├── SP500SectorsETFUniverse.cs
│   │   │       ├── TechnologyETFUniverse.cs
│   │   │       ├── USTreasuriesETFUniverse.cs
│   │   │       └── VolatilityETFUniverse.cs
│   │   ├── Algorithm.Python
│   │   │   ├── AccumulativeInsightPortfolioRegressionAlgorithm.py
│   │   │   ├── AddAlphaModelAlgorithm.py
│   │   │   ├── AddFutureOptionContractDataStreamingRegressionAlgorithm.py
│   │   │   ├── AddFutureOptionSingleOptionChainSelectedInUniverseFilterRegressionAlgorithm.py
│   │   │   ├── AddFutureUniverseSelectionModelRegressionAlgorithm.py
│   │   │   ├── AddOptionContractExpiresRegressionAlgorithm.py
│   │   │   ├── AddOptionContractFromUniverseRegressionAlgorithm.py
│   │   │   ├── AddOptionUniverseSelectionModelRegressionAlgorithm.py
│   │   │   ├── AddRemoveSecurityRegressionAlgorithm.py
│   │   │   ├── AddRiskManagementAlgorithm.py
│   │   │   ├── AddUniverseSelectionModelAlgorithm.py
│   │   │   ├── AlgorithmModeAndDeploymentTargetAlgorithm.py
│   │   │   ├── AllShortableSymbolsCoarseSelectionRegressionAlgorithm.py
│   │   │   ├── Alphas
│   │   │   │   ├── ContingentClaimsAnalysisDefaultPredictionAlpha.py
│   │   │   │   ├── GasAndCrudeOilEnergyCorrelationAlpha.py
│   │   │   │   ├── GlobalEquityMeanReversionIBSAlpha.py
│   │   │   │   ├── GreenblattMagicFormulaAlpha.py
│   │   │   │   ├── IntradayReversalCurrencyMarketsAlpha.py
│   │   │   │   ├── MeanReversionLunchBreakAlpha.py
│   │   │   │   ├── MortgageRateVolatilityAlpha.py
│   │   │   │   ├── PriceGapMeanReversionAlpha.py
│   │   │   │   ├── RebalancingLeveragedETFAlpha.py
│   │   │   │   ├── ShareClassMeanReversionAlpha.py
│   │   │   │   ├── SykesShortMicroCapAlpha.py
│   │   │   │   ├── TriangleExchangeRateArbitrageAlpha.py
│   │   │   │   ├── TripleLeverageETFPairVolatilityDecayAlpha.py
│   │   │   │   └── VIXDualThrustAlpha.py
│   │   │   ├── AsynchronousUniverseRegressionAlgorithm.py
│   │   │   ├── AutoRegressiveIntegratedMovingAverageRegressionAlgorithm.py
│   │   │   ├── AuxiliaryDataHandlersRegressionAlgorithm.py
│   │   │   ├── BaseFrameworkRegressionAlgorithm.py
│   │   │   ├── BasicCSharpIntegrationTemplateAlgorithm.py
│   │   │   ├── BasicSetAccountCurrencyAlgorithm.py
│   │   │   ├── BasicSetAccountCurrencyWithAmountAlgorithm.py
│   │   │   ├── BasicTemplateAlgorithm.py
│   │   │   ├── BasicTemplateAxosAlgorithm.py
│   │   │   ├── BasicTemplateCfdAlgorithm.py
│   │   │   ├── BasicTemplateContinuousFutureAlgorithm.py
│   │   │   ├── BasicTemplateContinuousFutureWithExtendedMarketAlgorithm.py
│   │   │   ├── BasicTemplateCryptoAlgorithm.py
│   │   │   ├── BasicTemplateCryptoFutureAlgorithm.py
│   │   │   ├── BasicTemplateCryptoFutureHourlyAlgorithm.py
│   │   │   ├── BasicTemplateDailyAlgorithm.py
│   │   │   ├── BasicTemplateEurexFuturesAlgorithm.py
│   │   │   ├── BasicTemplateFillForwardAlgorithm.py
│   │   │   ├── BasicTemplateForexAlgorithm.py
│   │   │   ├── BasicTemplateFrameworkAlgorithm.py
│   │   │   ├── BasicTemplateFutureOptionAlgorithm.py
│   │   │   ├── BasicTemplateFutureRolloverAlgorithm.py
│   │   │   ├── BasicTemplateFuturesAlgorithm.py
│   │   │   ├── BasicTemplateFuturesConsolidationAlgorithm.py
│   │   │   ├── BasicTemplateFuturesDailyAlgorithm.py
│   │   │   ├── BasicTemplateFuturesFrameworkAlgorithm.py
│   │   │   ├── BasicTemplateFuturesFrameworkWithExtendedMarketAlgorithm.py
│   │   │   ├── BasicTemplateFuturesHistoryAlgorithm.py
│   │   │   ├── BasicTemplateFuturesHistoryWithExtendedMarketHoursAlgorithm.py
│   │   │   ├── BasicTemplateFuturesHourlyAlgorithm.py
│   │   │   ├── BasicTemplateFuturesWithExtendedMarketAlgorithm.py
│   │   │   ├── BasicTemplateFuturesWithExtendedMarketDailyAlgorithm.py
│   │   │   ├── BasicTemplateFuturesWithExtendedMarketHourlyAlgorithm.py
│   │   │   ├── BasicTemplateIndexAlgorithm.py
│   │   │   ├── BasicTemplateIndexDailyAlgorithm.py
│   │   │   ├── BasicTemplateIndexOptionsAlgorithm.py
│   │   │   ├── BasicTemplateIndiaAlgorithm.py
│   │   │   ├── BasicTemplateIndiaIndexAlgorithm.py
│   │   │   ├── BasicTemplateIntrinioEconomicData.py
│   │   │   ├── BasicTemplateLibrary.py
│   │   │   ├── BasicTemplateOptionEquityStrategyAlgorithm.py
│   │   │   ├── BasicTemplateOptionsAlgorithm.py
│   │   │   ├── BasicTemplateOptionsConsolidationAlgorithm.py
│   │   │   ├── BasicTemplateOptionsDailyAlgorithm.py
│   │   │   ├── BasicTemplateOptionsFilterUniverseAlgorithm.py
│   │   │   ├── BasicTemplateOptionsFrameworkAlgorithm.py
│   │   │   ├── BasicTemplateOptionsHistoryAlgorithm.py
│   │   │   ├── BasicTemplateOptionsHourlyAlgorithm.py
│   │   │   ├── BasicTemplateOptionsPriceModel.py
│   │   │   ├── BasicTemplateOptionStrategyAlgorithm.py
│   │   │   ├── BasicTemplateOptionTradesAlgorithm.py
│   │   │   ├── BasicTemplateSPXWeeklyIndexOptionsAlgorithm.py
│   │   │   ├── BasicTemplateTradableIndexAlgorithm.py
│   │   │   ├── Benchmarks
│   │   │   │   ├── BasicTemplateBenchmark.py
│   │   │   │   ├── CoarseFineUniverseSelectionBenchmark.py
│   │   │   │   ├── EmptyEquityAndOptions400Benchmark.py
│   │   │   │   ├── EmptyMinute400EquityBenchmark.py
│   │   │   │   ├── EmptySingleSecuritySecondEquityBenchmark.py
│   │   │   │   ├── EmptySPXOptionChainBenchmark.py
│   │   │   │   ├── HistoryRequestBenchmark.py
│   │   │   │   ├── IndicatorRibbonBenchmark.py
│   │   │   │   ├── ScheduledEventsBenchmark.py
│   │   │   │   ├── StatefulCoarseUniverseSelectionBenchmark.py
│   │   │   │   └── StatelessCoarseUniverseSelectionBenchmark.py
│   │   │   ├── BlackLittermanPortfolioOptimizationFrameworkAlgorithm.py
│   │   │   ├── BrokerageActivityEventHandlingAlgorithm.py
│   │   │   ├── BrokerageModelAlgorithm.py
│   │   │   ├── BubbleAlgorithm.py
│   │   │   ├── build.bat
│   │   │   ├── build.sh
│   │   │   ├── BybitCryptoFuturesRegressionAlgorithm.py
│   │   │   ├── BybitCryptoRegressionAlgorithm.py
│   │   │   ├── BybitCustomDataCryptoRegressionAlgorithm.py
│   │   │   ├── CallbackCommandRegressionAlgorithm.py
│   │   │   ├── CanLiquidateWithOrderPropertiesRegressionAlgorithm.py
│   │   │   ├── CapmAlphaRankingFrameworkAlgorithm.py
│   │   │   ├── ClassicRangeConsolidatorAlgorithm.py
│   │   │   ├── ClassicRangeConsolidatorWithTickAlgorithm.py
│   │   │   ├── ClassicRenkoConsolidatorAlgorithm.py
│   │   │   ├── CoarseFineAsyncUniverseRegressionAlgorithm.py
│   │   │   ├── CoarseFineFundamentalComboAlgorithm.py
│   │   │   ├── CoarseFineFundamentalRegressionAlgorithm.py
│   │   │   ├── CoarseFineOptionUniverseChainRegressionAlgorithm.py
│   │   │   ├── CoarseFundamentalTop3Algorithm.py
│   │   │   ├── Collective2PortfolioSignalExportDemonstrationAlgorithm.py
│   │   │   ├── Collective2SignalExportDemonstrationAlgorithm.py
│   │   │   ├── ComboOrdersFillModelAlgorithm.py
│   │   │   ├── ComboOrderTicketDemoAlgorithm.py
│   │   │   ├── CompleteOrderTagUpdateAlgorithm.py
│   │   │   ├── CompositeAlphaModelFrameworkAlgorithm.py
│   │   │   ├── CompositeIndicatorWorksAsExpectedRegressionAlgorithm.py
│   │   │   ├── CompositeRiskManagementModelFrameworkAlgorithm.py
│   │   │   ├── ConfidenceWeightedFrameworkAlgorithm.py
│   │   │   ├── ConsolidateDifferentTickTypesRegressionAlgorithm.py
│   │   │   ├── ConsolidateHourBarsIntoDailyBarsRegressionAlgorithm.py
│   │   │   ├── ConsolidateRegressionAlgorithm.py
│   │   │   ├── ConsolidateWithSizeAttributeRegressionAlgorithm.py
│   │   │   ├── ConsolidatorRollingWindowRegressionAlgorithm.py
│   │   │   ├── ConsolidatorStartTimeRegressionAlgorithm.py
│   │   │   ├── ConstituentsQC500GeneratorAlgorithm.py
│   │   │   ├── ConstituentsUniverseRegressionAlgorithm.py
│   │   │   ├── ContinuousFutureModelsConsistencyRegressionAlgorithm.py
│   │   │   ├── ContinuousFutureRegressionAlgorithm.py
│   │   │   ├── ConvertToFrameworkAlgorithm.py
│   │   │   ├── CorrectConsolidatedBarTypeForTickTypesAlgorithm.py
│   │   │   ├── CoveredAndProtectiveCallStrategiesAlgorithm.py
│   │   │   ├── CoveredAndProtectivePutStrategiesAlgorithm.py
│   │   │   ├── CrunchDAOSignalExportDemonstrationAlgorithm.py
│   │   │   ├── CustomBenchmarkAlgorithm.py
│   │   │   ├── CustomBenchmarkRegressionAlgorithm.py
│   │   │   ├── CustomBrokerageModelRegressionAlgorithm.py
│   │   │   ├── CustomBrokerageSideOrderHandlingRegressionAlgorithm.py
│   │   │   ├── CustomBrokerageSideOrderHandlingRegressionPartialAlgorithm.py
│   │   │   ├── CustomBuyingPowerModelAlgorithm.py
│   │   │   ├── CustomChartingAlgorithm.py
│   │   │   ├── CustomConsolidatorRegressionAlgorithm.py
│   │   │   ├── CustomDataBenchmarkRegressionAlgorithm.py
│   │   │   ├── CustomDataBitcoinAlgorithm.py
│   │   │   ├── CustomDataIconicTypesAddDataRegressionAlgorithm.py
│   │   │   ├── CustomDataIndicatorExtensionsAlgorithm.py
│   │   │   ├── CustomDataLinkedIconicTypeAddDataCoarseSelectionRegressionAlgorithm.py
│   │   │   ├── CustomDataLinkedIconicTypeAddDataOnSecuritiesChangedRegressionAlgorithm.py
│   │   │   ├── CustomDataMultiFileObjectStoreRegressionAlgorithm.py
│   │   │   ├── CustomDataNIFTYAlgorithm.py
│   │   │   ├── CustomDataObjectStoreRegressionAlgorithm.py
│   │   │   ├── CustomDataPropertiesRegressionAlgorithm.py
│   │   │   ├── CustomDataRegressionAlgorithm.py
│   │   │   ├── CustomDataSecurityCacheGetDataRegressionAlgorithm.py
│   │   │   ├── CustomDataTypeHistoryAlgorithm.py
│   │   │   ├── CustomDataUniverseAlgorithm.py
│   │   │   ├── CustomDataUniverseRegressionAlgorithm.py
│   │   │   ├── CustomDataUniverseScheduledRegressionAlgorithm.py
│   │   │   ├── CustomDataUsingMapFileRegressionAlgorithm.py
│   │   │   ├── CustomDataZippedObjectStoreRegressionAlgorithm.py
│   │   │   ├── CustomIndicatorAlgorithm.py
│   │   │   ├── CustomIndicatorWithExtensionAlgorithm.py
│   │   │   ├── CustomMarginInterestRateModelAlgorithm.py
│   │   │   ├── CustomModelsAlgorithm.py
│   │   │   ├── CustomModelsPEP8Algorithm.py
│   │   │   ├── CustomOptionAssignmentRegressionAlgorithm.py
│   │   │   ├── CustomOptionExerciseModelRegressionAlgorithm.py
│   │   │   ├── CustomOptionPriceModelRegressionAlgorithm.py
│   │   │   ├── CustomPartialFillModelAlgorithm.py
│   │   │   ├── CustomPortfolioOptimizerRegressionAlgorithm.py
│   │   │   ├── CustomSecurityDataFilterRegressionAlgorithm.py
│   │   │   ├── CustomSecurityInitializerAlgorithm.py
│   │   │   ├── CustomSettlementModelRegressionAlgorithm.py
│   │   │   ├── CustomShortableProviderRegressionAlgorithm.py
│   │   │   ├── CustomSignalExportDemonstrationAlgorithm.py
│   │   │   ├── CustomUniverseSelectionModelRegressionAlgorithm.py
│   │   │   ├── CustomVolatilityModelAlgorithm.py
│   │   │   ├── CustomWarmUpPeriodIndicatorAlgorithm.py
│   │   │   ├── DailyAlgorithm.py
│   │   │   ├── DataConsolidationAlgorithm.py
│   │   │   ├── DefaultSchedulingSymbolRegressionAlgorithm.py
│   │   │   ├── DelistingEventsAlgorithm.py
│   │   │   ├── DescendingCustomDataObjectStoreRegressionAlgorithm.py
│   │   │   ├── DisplacedMovingAverageRibbon.py
│   │   │   ├── DividendAlgorithm.py
│   │   │   ├── DropboxBaseDataUniverseSelectionAlgorithm.py
│   │   │   ├── DropboxCoarseFineAlgorithm.py
│   │   │   ├── DropboxUniverseSelectionAlgorithm.py
│   │   │   ├── DynamicSecurityDataRegressionAlgorithm.py
│   │   │   ├── EmaCrossAlphaModelFrameworkRegressionAlgorithm.py
│   │   │   ├── EmaCrossFuturesFrontMonthAlgorithm.py
│   │   │   ├── EmaCrossUniverseSelectionAlgorithm.py
│   │   │   ├── EmaCrossUniverseSelectionFrameworkAlgorithm.py
│   │   │   ├── ETFConstituentsFrameworkAlgorithm.py
│   │   │   ├── ETFConstituentsFrameworkWithDifferentSelectionModelAlgorithm.py
│   │   │   ├── ETFConstituentUniverseCompositeDelistingRegressionAlgorithm.py
│   │   │   ├── ETFConstituentUniverseCompositeDelistingRegressionAlgorithmNoAddEquityETF.py
│   │   │   ├── ETFConstituentUniverseFilterFunctionRegressionAlgorithm.py
│   │   │   ├── ETFConstituentUniverseFrameworkRegressionAlgorithm.py
│   │   │   ├── ETFConstituentUniverseMappedCompositeRegressionAlgorithm.py
│   │   │   ├── ETFConstituentUniverseRSIAlphaModelAlgorithm.py
│   │   │   ├── ETFGlobalRotationAlgorithm.py
│   │   │   ├── ExecutionModelOrderEventsRegressionAlgorithm.py
│   │   │   ├── ExpiryHelperAlphaModelFrameworkAlgorithm.py
│   │   │   ├── ExtendedMarketTradingRegressionAlgorithm.py
│   │   │   ├── FilteredIdentityAlgorithm.py
│   │   │   ├── FilterUniverseRegressionAlgorithm.py
│   │   │   ├── FinancialAdvisorDemoAlgorithm.py
│   │   │   ├── FineFundamentalFilteredUniverseRegressionAlgorithm.py
│   │   │   ├── ForwardDataOnlyFillModelAlgorithm.py
│   │   │   ├── FractionalQuantityRegressionAlgorithm.py
│   │   │   ├── FuncRiskFreeRateInterestRateModelWithPythonLambda.py
│   │   │   ├── FundamentalCustomSelectionTimeRegressionAlgorithm.py
│   │   │   ├── FundamentalRegressionAlgorithm.py
│   │   │   ├── FundamentalUniverseSelectionAlgorithm.py
│   │   │   ├── FundamentalUniverseSelectionRegressionAlgorithm.py
│   │   │   ├── FutureContractsExtendedMarketHoursRegressionAlgorithm.py
│   │   │   ├── FutureOptionBuySellCallIntradayRegressionAlgorithm.py
│   │   │   ├── FutureOptionCallITMExpiryRegressionAlgorithm.py
│   │   │   ├── FutureOptionCallOTMExpiryRegressionAlgorithm.py
│   │   │   ├── FutureOptionChainFullDataRegressionAlgorithm.py
│   │   │   ├── FutureOptionChainsMultipleFullDataRegressionAlgorithm.py
│   │   │   ├── FutureOptionContinuousFutureRegressionAlgorithm.py
│   │   │   ├── FutureOptionDailyRegressionAlgorithm.py
│   │   │   ├── FutureOptionHourlyRegressionAlgorithm.py
│   │   │   ├── FutureOptionMultipleContractsInDifferentContractMonthsWithSameUnderlyingFutureRegressionAlgorithm.py
│   │   │   ├── FutureOptionPutITMExpiryRegressionAlgorithm.py
│   │   │   ├── FutureOptionPutOTMExpiryRegressionAlgorithm.py
│   │   │   ├── FutureOptionShortCallITMExpiryRegressionAlgorithm.py
│   │   │   ├── FutureOptionShortCallOTMExpiryRegressionAlgorithm.py
│   │   │   ├── FutureOptionShortPutITMExpiryRegressionAlgorithm.py
│   │   │   ├── FutureOptionShortPutOTMExpiryRegressionAlgorithm.py
│   │   │   ├── FutureOptionWithFutureFilterRegressionAlgorithm.py
│   │   │   ├── FuturesAndFuturesOptionsExpiryTimeAndLiquidationRegressionAlgorithm.py
│   │   │   ├── FuturesChainFullDataRegressionAlgorithm.py
│   │   │   ├── FuturesChainsMultipleFullDataRegressionAlgorithm.py
│   │   │   ├── FuturesExtendedMarketHoursRegressionAlgorithm.py
│   │   │   ├── FuturesMomentumAlgorithm.py
│   │   │   ├── FutureStopMarketOrderOnExtendedHoursRegressionAlgorithm.py
│   │   │   ├── FutureUniverseHistoryRegressionAlgorithm.py
│   │   │   ├── G10CurrencySelectionModelFrameworkAlgorithm.py
│   │   │   ├── GetParameterRegressionAlgorithm.py
│   │   │   ├── HistoricalReturnsAlphaModelFrameworkRegressionAlgorithm.py
│   │   │   ├── HistoryAlgorithm.py
│   │   │   ├── HistoryAuxiliaryDataRegressionAlgorithm.py
│   │   │   ├── HistoryTickRegressionAlgorithm.py
│   │   │   ├── HistoryWithCustomDataSourceRegressionAlgorithm.py
│   │   │   ├── HistoryWithDifferentContinuousContractDepthOffsetsRegressionAlgorithm.py
│   │   │   ├── HistoryWithDifferentDataMappingModeRegressionAlgorithm.py
│   │   │   ├── HistoryWithDifferentDataNormalizationModeRegressionAlgorithm.py
│   │   │   ├── HourReverseSplitRegressionAlgorithm.py
│   │   │   ├── HourSplitRegressionAlgorithm.py
│   │   │   ├── ImmediateExecutionModelWorksWithBinanceFeeModel.py
│   │   │   ├── InceptionDateSelectionRegressionAlgorithm.py
│   │   │   ├── IndexOptionBearCallSpreadAlgorithm.py
│   │   │   ├── IndexOptionBearPutSpreadAlgorithm.py
│   │   │   ├── IndexOptionBullCallSpreadAlgorithm.py
│   │   │   ├── IndexOptionBullPutSpreadAlgorithm.py
│   │   │   ├── IndexOptionBuySellCallIntradayRegressionAlgorithm.py
│   │   │   ├── IndexOptionCallButterflyAlgorithm.py
│   │   │   ├── IndexOptionCallCalendarSpreadAlgorithm.py
│   │   │   ├── IndexOptionCallITMExpiryRegressionAlgorithm.py
│   │   │   ├── IndexOptionCallITMGreeksExpiryRegressionAlgorithm.py
│   │   │   ├── IndexOptionCallOTMExpiryRegressionAlgorithm.py
│   │   │   ├── IndexOptionChainApisConsistencyRegressionAlgorithm.py
│   │   │   ├── IndexOptionIronCondorAlgorithm.py
│   │   │   ├── IndexOptionModelsConsistencyRegressionAlgorithm.py
│   │   │   ├── IndexOptionPutButterflyAlgorithm.py
│   │   │   ├── IndexOptionPutCalendarSpreadAlgorithm.py
│   │   │   ├── IndexOptionPutITMExpiryRegressionAlgorithm.py
│   │   │   ├── IndexOptionPutOTMExpiryRegressionAlgorithm.py
│   │   │   ├── IndexOptionShortCallITMExpiryRegressionAlgorithm.py
│   │   │   ├── IndexOptionShortCallOTMExpiryRegressionAlgorithm.py
│   │   │   ├── IndexOptionShortPutITMExpiryRegressionAlgorithm.py
│   │   │   ├── IndexOptionShortPutOTMExpiryRegressionAlgorithm.py
│   │   │   ├── IndiaDataRegressionAlgorithm.py
│   │   │   ├── IndicatorExtensionsSMAWithCustomIndicatorsRegressionAlgorithm.py
│   │   │   ├── IndicatorHistoryAlgorithm.py
│   │   │   ├── IndicatorHistoryRegressionAlgorithm.py
│   │   │   ├── IndicatorSelectorsWorkWithDifferentOptions.py
│   │   │   ├── IndicatorSuiteAlgorithm.py
│   │   │   ├── IndicatorVolatilityModelAlgorithm.py
│   │   │   ├── IndicatorWarmupAlgorithm.py
│   │   │   ├── IndicatorWithRenkoBarsRegressionAlgorithm.py
│   │   │   ├── IndustryStandardSecurityIdentifiersRegressionAlgorithm.py
│   │   │   ├── InsightScoringRegressionAlgorithm.py
│   │   │   ├── InsightTagAlphaRegressionAlgorithm.py
│   │   │   ├── InsightWeightingFrameworkAlgorithm.py
│   │   │   ├── IronCondorStrategyAlgorithm.py
│   │   │   ├── KerasNeuralNetworkAlgorithm.py
│   │   │   ├── LimitFillRegressionAlgorithm.py
│   │   │   ├── LimitIfTouchedAsyncRegressionAlgorithm.py
│   │   │   ├── LimitIfTouchedRegressionAlgorithm.py
│   │   │   ├── LiquidETFUniverseFrameworkAlgorithm.py
│   │   │   ├── LiveFeaturesAlgorithm.py
│   │   │   ├── LongAndShortButterflyCallStrategiesAlgorithm.py
│   │   │   ├── LongAndShortButterflyPutStrategiesAlgorithm.py
│   │   │   ├── LongAndShortCallCalendarSpreadStrategiesAlgorithm.py
│   │   │   ├── LongAndShortPutCalendarSpreadStrategiesAlgorithm.py
│   │   │   ├── LongAndShortStraddleStrategiesAlgorithm.py
│   │   │   ├── LongAndShortStrangleStrategiesAlgorithm.py
│   │   │   ├── LongOnlyAlphaStreamAlgorithm.py
│   │   │   ├── MacdAlphaModelFrameworkRegressionAlgorithm.py
│   │   │   ├── MACDTrendAlgorithm.py
│   │   │   ├── main.py
│   │   │   ├── ManuallyRemovedConsolidatorsAlgorithm.py
│   │   │   ├── ManuallySetMarketHoursAndSymbolPropertiesDatabaseEntriesAlgorithm.py
│   │   │   ├── MarginCallEventsAlgorithm.py
│   │   │   ├── MarketHourAwareIntradayConsolidationRegressionAlgorithm.py
│   │   │   ├── MarketImpactSlippageModelRegressionAlgorithm.py
│   │   │   ├── MarketOnCloseOrderBufferExtendedMarketHoursRegressionAlgorithm.py
│   │   │   ├── MarketOnCloseOrderBufferRegressionAlgorithm.py
│   │   │   ├── MarketOnOpenOnCloseAlgorithm.py
│   │   │   ├── MaximumDrawdownPercentPerSecurityFrameworkRegressionAlgorithm.py
│   │   │   ├── MaximumDrawdownPercentPortfolioFrameworkRegressionAlgorithm.py
│   │   │   ├── MaximumSectorExposureRiskManagementModelFrameworkRegressionAlgorithm.py
│   │   │   ├── MaximumUnrealizedProfitPercentPerSecurityFrameworkRegressionAlgorithm.py
│   │   │   ├── MeanReversionPortfolioAlgorithm.py
│   │   │   ├── MeanVarianceOptimizationFrameworkAlgorithm.py
│   │   │   ├── MovingAverageCrossAlgorithm.py
│   │   │   ├── MultipleSymbolConsolidationAlgorithm.py
│   │   │   ├── NakedCallStrategyAlgorithm.py
│   │   │   ├── NakedPutStrategyAlgorithm.py
│   │   │   ├── NamedArgumentsRegression.py
│   │   │   ├── NLTKSentimentTradingAlgorithm.py
│   │   │   ├── NoUniverseSelectorRegressionAlgorithm.py
│   │   │   ├── NullBuyingPowerOptionBullCallSpreadAlgorithm.py
│   │   │   ├── NullMarginMultipleOrdersRegressionAlgorithm.py
│   │   │   ├── NullOptionAssignmentRegressionAlgorithm.py
│   │   │   ├── NumeraiSignalExportDemonstrationAlgorithm.py
│   │   │   ├── ObjectStoreExampleAlgorithm.py
│   │   │   ├── OnEndOfDayRegressionAlgorithm.py
│   │   │   ├── OnWarmupFinishedNoWarmup.py
│   │   │   ├── OnWarmupFinishedRegressionAlgorithm.py
│   │   │   ├── OpenInterestFuturesRegressionAlgorithm.py
│   │   │   ├── OptionAssignmentRegressionAlgorithm.py
│   │   │   ├── OptionChainApisConsistencyRegressionAlgorithm.py
│   │   │   ├── OptionChainConsistencyRegressionAlgorithm.py
│   │   │   ├── OptionChainedUniverseSelectionModelRegressionAlgorithm.py
│   │   │   ├── OptionChainFullDataRegressionAlgorithm.py
│   │   │   ├── OptionChainIncludeWeeklysByDefaultRegressionAlgorithm.py
│   │   │   ├── OptionChainProviderAlgorithm.py
│   │   │   ├── OptionChainsMultipleFullDataRegressionAlgorithm.py
│   │   │   ├── OptionDataNullReferenceRegressionAlgorithm.py
│   │   │   ├── OptionExerciseAssignRegressionAlgorithm.py
│   │   │   ├── OptionFilterReturnsNullRegressionAlgorithm.py
│   │   │   ├── OptionIndicatorsMirrorContractsRegressionAlgorithm.py
│   │   │   ├── OptionIndicatorsRegressionAlgorithm.py
│   │   │   ├── OptionModelsConsistencyRegressionAlgorithm.py
│   │   │   ├── OptionOpenInterestRegressionAlgorithm.py
│   │   │   ├── OptionPriceModelForOptionStylesBaseRegressionAlgorithm.py
│   │   │   ├── OptionPriceModelForSupportedAmericanOptionRegressionAlgorithm.py
│   │   │   ├── OptionPriceModelForSupportedAmericanOptionTimeSpanWarmupRegressionAlgorithm.py
│   │   │   ├── OptionPriceModelForSupportedEuropeanOptionRegressionAlgorithm.py
│   │   │   ├── OptionPriceModelForSupportedEuropeanOptionTimeSpanWarmupRegressionAlgorithm.py
│   │   │   ├── OptionPriceModelForUnsupportedAmericanOptionRegressionAlgorithm.py
│   │   │   ├── OptionPriceModelForUnsupportedAmericanOptionTimeSpanWarmupRegressionAlgorithm.py
│   │   │   ├── OptionPriceModelForUnsupportedEuropeanOptionRegressionAlgorithm.py
│   │   │   ├── OptionPriceModelForUnsupportedEuropeanOptionTimeSpanWarmupRegressionAlgorithm.py
│   │   │   ├── OptionRenameRegressionAlgorithm.py
│   │   │   ├── OptionSplitRegressionAlgorithm.py
│   │   │   ├── OptionStrategyFactoryMethodsBaseAlgorithm.py
│   │   │   ├── OptionUniverseFilterGreeksRegressionAlgorithm.py
│   │   │   ├── OptionUniverseFilterGreeksShortcutsRegressionAlgorithm.py
│   │   │   ├── OptionUniverseFilterOptionsDataRegressionAlgorithm.py
│   │   │   ├── OptionUniverseHistoryRegressionAlgorithm.py
│   │   │   ├── OrderTicketAssignmentDemoAlgorithm.py
│   │   │   ├── OrderTicketDemoAlgorithm.py
│   │   │   ├── PandasDataFrameFromMultipleTickTypeTickHistoryRegressionAlgorithm.py
│   │   │   ├── PandasDataFrameHistoryAlgorithm.py
│   │   │   ├── ParameterizedAlgorithm.py
│   │   │   ├── PearsonCorrelationPairsTradingAlphaModelFrameworkAlgorithm.py
│   │   │   ├── PEP8StyleBasicAlgorithm.py
│   │   │   ├── PeriodBasedHistoryRequestNotAllowedWithTickResolutionRegressionAlgorithm.py
│   │   │   ├── PersistentCustomDataUniverseRegressionAlgorithm.py
│   │   │   ├── PortfolioRebalanceOnCustomFuncRegressionAlgorithm.py
│   │   │   ├── PortfolioRebalanceOnDateRulesRegressionAlgorithm.py
│   │   │   ├── PortfolioTargetTagsRegressionAlgorithm.py
│   │   │   ├── Properties
│   │   │   │   └── AssemblyInfo.cs
│   │   │   ├── PythonAlgorithm.cs
│   │   │   ├── PythonDictionaryFeatureRegressionAlgorithm.py
│   │   │   ├── PytorchNeuralNetworkAlgorithm.py
│   │   │   ├── QLOptionPricingModelRegressionAlgorithm.py
│   │   │   ├── QuantConnect.Algorithm.Python.csproj
│   │   │   ├── QuantConnect.Algorithm.PythonTools.pyproj
│   │   │   ├── QuitAfterInitializationRegressionAlgorithm.py
│   │   │   ├── QuitInInitializationRegressionAlgorithm.py
│   │   │   ├── RangeConsolidatorAlgorithm.py
│   │   │   ├── RangeConsolidatorWithTickAlgorithm.py
│   │   │   ├── RawDataRegressionAlgorithm.py
│   │   │   ├── RawPricesCoarseUniverseAlgorithm.py
│   │   │   ├── RawPricesUniverseRegressionAlgorithm.py
│   │   │   ├── readme.md
│   │   │   ├── RegisterIndicatorRegressionAlgorithm.py
│   │   │   ├── RegressionAlgorithm.py
│   │   │   ├── RegressionChannelAlgorithm.py
│   │   │   ├── RiskParityPortfolioAlgorithm.py
│   │   │   ├── RollingWindowAlgorithm.py
│   │   │   ├── RsiAlphaModelFrameworkRegressionAlgorithm.py
│   │   │   ├── ScheduledEventsAlgorithm.py
│   │   │   ├── ScheduledQueuingAlgorithm.py
│   │   │   ├── ScheduledUniverseRegressionAlgorithm.py
│   │   │   ├── ScheduledUniverseSelectionModelRegressionAlgorithm.py
│   │   │   ├── ScikitLearnLinearRegressionAlgorithm.py
│   │   │   ├── SectorExposureRiskFrameworkAlgorithm.py
│   │   │   ├── SectorWeightingFrameworkAlgorithm.py
│   │   │   ├── SecurityCustomPropertiesAlgorithm.py
│   │   │   ├── SecurityDynamicPropertyPythonClassAlgorithm.py
│   │   │   ├── SecuritySeederRegressionAlgorithm.py
│   │   │   ├── SecuritySessionRegressionAlgorithm.py
│   │   │   ├── SecuritySessionWithChangeOfResolutionRegressionAlgorithm.py
│   │   │   ├── SecuritySessionWithFuturesRegressionAlgorithm.py
│   │   │   ├── SecurityToSymbolRegressionAlgorithm.py
│   │   │   ├── SelectUniverseSymbolsFromIDRegressionAlgorithm.py
│   │   │   ├── SetCustomSettlementModelRegressionAlgorithm.py
│   │   │   ├── SetEquityDataNormalizationModeOnAddEquity.py
│   │   │   ├── SetHoldingsAsyncRegressionAlgorithm.py
│   │   │   ├── SetHoldingsLiquidateExistingHoldingsMultipleTargetsRegressionAlgorithm.py
│   │   │   ├── SetHoldingsMultipleTargetsRegressionAlgorithm.py
│   │   │   ├── SetHoldingsRegressionAlgorithm.py
│   │   │   ├── ShortableProviderOrdersRejectedRegressionAlgorithm.py
│   │   │   ├── ShortInterestFeeRegressionAlgorithm.py
│   │   │   ├── SliceGetByTypeRegressionAlgorithm.py
│   │   │   ├── SmaCrossUniverseSelectionAlgorithm.py
│   │   │   ├── SpreadExecutionModelRegressionAlgorithm.py
│   │   │   ├── StableCoinsRegressionAlgorithm.py
│   │   │   ├── StandardDeviationExecutionModelRegressionAlgorithm.py
│   │   │   ├── StatisticsResultsAlgorithm.py
│   │   │   ├── StochasticIndicatorWarmsUpProperlyRegressionAlgorithm.py
│   │   │   ├── StopLimitOrderAsyncRegressionAlgorithm.py
│   │   │   ├── StopLimitOrderRegressionAlgorithm.py
│   │   │   ├── StringToSymbolImplicitConversionRegressionAlgorithm.py
│   │   │   ├── TalibIndicatorsAlgorithm.py
│   │   │   ├── TensorFlowNeuralNetworkAlgorithm.py
│   │   │   ├── TickDataFilteringAlgorithm.py
│   │   │   ├── TickHistoryRequestWithoutTickSubscriptionRegressionAlgorithm.py
│   │   │   ├── TiingoPriceAlgorithm.py
│   │   │   ├── TimeInForceAlgorithm.py
│   │   │   ├── TrailingStopOrderAsyncRegressionAlgorithm.py
│   │   │   ├── TrailingStopOrderRegressionAlgorithm.py
│   │   │   ├── TrailingStopRiskFrameworkRegressionAlgorithm.py
│   │   │   ├── TrainingExampleAlgorithm.py
│   │   │   ├── TrainingInitializeRegressionAlgorithm.py
│   │   │   ├── TwoLegCurrencyConversionRegressionAlgorithm.py
│   │   │   ├── UniverseOnlyRegressionAlgorithm.py
│   │   │   ├── UniverseSelectedRegressionAlgorithm.py
│   │   │   ├── UniverseSelectionDefinitionsAlgorithm.py
│   │   │   ├── UniverseSelectionRegressionAlgorithm.py
│   │   │   ├── UniverseUnchangedRegressionAlgorithm.py
│   │   │   ├── UnregisterIndicatorRegressionAlgorithm.py
│   │   │   ├── UpdateOrderRegressionAlgorithm.py
│   │   │   ├── UserDefinedUniverseAlgorithm.py
│   │   │   ├── VBaseSignalExportDemonstrationAlgorithm.py
│   │   │   ├── VolumeRenkoConsolidatorAlgorithm.py
│   │   │   ├── VolumeShareSlippageModelAlgorithm.py
│   │   │   ├── VolumeWeightedAveragePriceExecutionModelRegressionAlgorithm.py
│   │   │   ├── WarmupAlgorithm.py
│   │   │   ├── WarmupHistoryAlgorithm.py
│   │   │   ├── WeeklyUniverseSelectionRegressionAlgorithm.py
│   │   │   └── ZeroedBenchmarkRegressionAlgorithm.py
│   │   ├── AlgorithmFactory
│   │   │   ├── DebuggerHelper.cs
│   │   │   ├── Loader.cs
│   │   │   ├── Properties
│   │   │   │   └── AssemblyInfo.cs
│   │   │   ├── Python
│   │   │   │   └── Wrappers
│   │   │   │       └── AlgorithmPythonWrapper.cs
│   │   │   └── QuantConnect.AlgorithmFactory.csproj
│   │   ├── Api
│   │   │   ├── Api.cs
│   │   │   ├── ApiConnection.cs
│   │   │   ├── ApiUtils.cs
│   │   │   ├── Properties
│   │   │   │   └── AssemblyInfo.cs
│   │   │   └── QuantConnect.Api.csproj
│   │   ├── Brokerages
│   │   │   ├── Authentication
│   │   │   │   ├── LeanOAuthTokenHandler.cs
│   │   │   │   ├── LeanTokenCredentials.cs
│   │   │   │   ├── LeanTokenHandler.cs
│   │   │   │   ├── OAuthTokenRequest.cs
│   │   │   │   └── TokenType.cs
│   │   │   ├── Backtesting
│   │   │   │   ├── BacktestingBrokerage.cs
│   │   │   │   └── BacktestingBrokerageFactory.cs
│   │   │   ├── BaseWebsocketsBrokerage.cs
│   │   │   ├── BestBidAskUpdatedEventArgs.cs
│   │   │   ├── Brokerage.cs
│   │   │   ├── BrokerageConcurrentMessageHandler.cs
│   │   │   ├── BrokerageException.cs
│   │   │   ├── BrokerageFactory.cs
│   │   │   ├── BrokerageMultiWebSocketEntry.cs
│   │   │   ├── BrokerageMultiWebSocketSubscriptionManager.cs
│   │   │   ├── CrossZero
│   │   │   │   ├── CrossZeroFirstOrderRequest.cs
│   │   │   │   ├── CrossZeroOrderResponse.cs
│   │   │   │   └── CrossZeroSecondOrderRequest.cs
│   │   │   ├── DefaultConnectionHandler.cs
│   │   │   ├── DefaultOrderBook.cs
│   │   │   ├── IConnectionHandler.cs
│   │   │   ├── IOrderBookUpdater.cs
│   │   │   ├── ISymbolMapper.cs
│   │   │   ├── IWebSocket.cs
│   │   │   ├── LevelOneOrderBook
│   │   │   │   ├── BaseDataEventArgs.cs
│   │   │   │   ├── LevelOneMarketData.cs
│   │   │   │   └── LevelOneServiceManager.cs
│   │   │   ├── Paper
│   │   │   │   ├── PaperBrokerage.cs
│   │   │   │   └── PaperBrokerageFactory.cs
│   │   │   ├── Properties
│   │   │   │   └── AssemblyInfo.cs
│   │   │   ├── QuantConnect.Brokerages.csproj
│   │   │   ├── QuantConnect.Brokerages.csproj.DotSettings
│   │   │   ├── SymbolPropertiesDatabaseSymbolMapper.cs
│   │   │   ├── WebSocketClientWrapper.cs
│   │   │   ├── WebSocketCloseData.cs
│   │   │   ├── WebSocketError.cs
│   │   │   └── WebSocketMessage.cs
│   │   ├── ci_build_stubs.sh
│   │   ├── Common
│   │   │   ├── Algorithm
│   │   │   │   └── Framework
│   │   │   │       ├── Alphas
│   │   │   │       │   ├── Analysis
│   │   │   │       │   │   └── InsightManager.cs
│   │   │   │       │   ├── GeneratedInsightsCollection.cs
│   │   │   │       │   ├── IInsightScoreFunction.cs
│   │   │   │       │   ├── Insight.cs
│   │   │   │       │   ├── InsightCollection.cs
│   │   │   │       │   ├── InsightDirection.cs
│   │   │   │       │   ├── InsightScore.cs
│   │   │   │       │   ├── InsightScoreFunctionPythonWrapper.cs
│   │   │   │       │   ├── InsightScoreType.cs
│   │   │   │       │   ├── InsightType.cs
│   │   │   │       │   └── Serialization
│   │   │   │       │       ├── InsightJsonConverter.cs
│   │   │   │       │       └── SerializedInsight.cs
│   │   │   │       └── Portfolio
│   │   │   │           ├── IPortfolioTarget.cs
│   │   │   │           ├── PortfolioTarget.cs
│   │   │   │           ├── PortfolioTargetCollection.cs
│   │   │   │           └── SignalExports
│   │   │   │               ├── BaseSignalExport.cs
│   │   │   │               ├── Collective2SignalExport.cs
│   │   │   │               ├── CrunchDAOSignalExport.cs
│   │   │   │               ├── NumeraiSignalExport.cs
│   │   │   │               ├── SignalExportManager.cs
│   │   │   │               ├── SignalExportTargetParameters.cs
│   │   │   │               └── VBaseSignalExport.cs
│   │   │   ├── AlgorithmConfiguration.cs
│   │   │   ├── AlgorithmImports.py
│   │   │   ├── AlgorithmSettings.cs
│   │   │   ├── AlgorithmUtils.cs
│   │   │   ├── Analysis.cs
│   │   │   ├── Api
│   │   │   │   ├── Account.cs
│   │   │   │   ├── Authentication.cs
│   │   │   │   ├── AuthenticationResponse.cs
│   │   │   │   ├── Backtest.cs
│   │   │   │   ├── BacktestReport.cs
│   │   │   │   ├── BaseOptimization.cs
│   │   │   │   ├── Compile.cs
│   │   │   │   ├── CompileState.cs
│   │   │   │   ├── Data.cs
│   │   │   │   ├── Estimate.cs
│   │   │   │   ├── InsightResponse.cs
│   │   │   │   ├── LiveAlgorithm.cs
│   │   │   │   ├── LiveAlgorithmResults.cs
│   │   │   │   ├── LiveAlgorithmResultsJsonConverter.cs
│   │   │   │   ├── LiveAlgorithmSettings.cs
│   │   │   │   ├── LiveLog.cs
│   │   │   │   ├── Nodes.cs
│   │   │   │   ├── ObjectStoreResponse.cs
│   │   │   │   ├── Optimization.cs
│   │   │   │   ├── OptimizationBacktest.cs
│   │   │   │   ├── OptimizationBacktestJsonConverter.cs
│   │   │   │   ├── Organization.cs
│   │   │   │   ├── ParameterSetJsonConverter.cs
│   │   │   │   ├── Portfolio.cs
│   │   │   │   ├── Project.cs
│   │   │   │   ├── ProjectFile.cs
│   │   │   │   ├── ProjectNode.cs
│   │   │   │   ├── ReadChartResponse.cs
│   │   │   │   ├── RestResponse.cs
│   │   │   │   ├── Serialization
│   │   │   │   │   └── ProductJsonConverter.cs
│   │   │   │   └── StringRepresentation.cs
│   │   │   ├── BaseSeries.cs
│   │   │   ├── Benchmarks
│   │   │   │   ├── FuncBenchmark.cs
│   │   │   │   ├── IBenchmark.cs
│   │   │   │   └── SecurityBenchmark.cs
│   │   │   ├── BinaryComparison.cs
│   │   │   ├── BinaryComparisonExtensions.cs
│   │   │   ├── Brokerages
│   │   │   │   ├── AlpacaBrokerageModel.cs
│   │   │   │   ├── AlphaStreamsBrokerageModel.cs
│   │   │   │   ├── AxosClearingBrokerageModel.cs
│   │   │   │   ├── BinanceBrokerageModel.cs
│   │   │   │   ├── BinanceCoinFuturesBrokerageModel.cs
│   │   │   │   ├── BinanceFuturesBrokerageModel.cs
│   │   │   │   ├── BinanceUSBrokerageModel.cs
│   │   │   │   ├── BitfinexBrokerageModel.cs
│   │   │   │   ├── BloombergFixBrokerageModel.cs
│   │   │   │   ├── BrokerageExtensions.cs
│   │   │   │   ├── BrokerageFactoryAttribute.cs
│   │   │   │   ├── BrokerageMessageEvent.cs
│   │   │   │   ├── BrokerageMessageType.cs
│   │   │   │   ├── BrokerageName.cs
│   │   │   │   ├── BybitBrokerageModel.cs
│   │   │   │   ├── CharlesSchwabBrokerageModel.cs
│   │   │   │   ├── CoinbaseBrokerageModel.cs
│   │   │   │   ├── DefaultBrokerageMessageHandler.cs
│   │   │   │   ├── DefaultBrokerageModel.cs
│   │   │   │   ├── DelistingNotificationEventArgs.cs
│   │   │   │   ├── DowngradeErrorCodeToWarningBrokerageMessageHandler.cs
│   │   │   │   ├── dYdXBrokerageModel.cs
│   │   │   │   ├── ExanteBrokerageModel.cs
│   │   │   │   ├── EzeBrokerageModel.cs
│   │   │   │   ├── FTXBrokerageModel.cs
│   │   │   │   ├── FTXUSBrokerageModel.cs
│   │   │   │   ├── FxcmBrokerageModel.cs
│   │   │   │   ├── GDAXBrokerageModel.cs
│   │   │   │   ├── IBrokerageMessageHandler.cs
│   │   │   │   ├── IBrokerageModel.cs
│   │   │   │   ├── InteractiveBrokersBrokerageModel.cs
│   │   │   │   ├── InteractiveBrokersFixModel.cs
│   │   │   │   ├── KrakenBrokerageModel.cs
│   │   │   │   ├── NewBrokerageOrderNotificationEventArgs.cs
│   │   │   │   ├── OandaBrokerageModel.cs
│   │   │   │   ├── OptionNotificationEventArgs.cs
│   │   │   │   ├── PublicBrokerageModel.cs
│   │   │   │   ├── RBIBrokerageModel.cs
│   │   │   │   ├── SamcoBrokerageModel.cs
│   │   │   │   ├── TastytradeBrokerageModel.cs
│   │   │   │   ├── TDAmeritradeBrokerageModel.cs
│   │   │   │   ├── TerminalLinkBrokerageModel.cs
│   │   │   │   ├── TradeStationBrokerageModel.cs
│   │   │   │   ├── TradierBrokerageModel.cs
│   │   │   │   ├── TradingTechnologiesBrokerageModel.cs
│   │   │   │   ├── WebullBrokerageModel.cs
│   │   │   │   ├── WolverineBrokerageModel.cs
│   │   │   │   └── ZerodhaBrokerageModel.cs
│   │   │   ├── Candlestick.cs
│   │   │   ├── CandlestickSeries.cs
│   │   │   ├── CapacityEstimate.cs
│   │   │   ├── Chart.cs
│   │   │   ├── ChartPoint.cs
│   │   │   ├── ChartSeriesJsonConverter.cs
│   │   │   ├── Commands
│   │   │   │   ├── AddSecurityCommand.cs
│   │   │   │   ├── AlgorithmStatusCommand.cs
│   │   │   │   ├── BaseCommand.cs
│   │   │   │   ├── BaseCommandHandler.cs
│   │   │   │   ├── CallbackCommand.cs
│   │   │   │   ├── CancelOrderCommand.cs
│   │   │   │   ├── Command.cs
│   │   │   │   ├── CommandResultsPacket.cs
│   │   │   │   ├── FileCommandHandler.cs
│   │   │   │   ├── ICommand.cs
│   │   │   │   ├── ICommandHandler.cs
│   │   │   │   ├── LiquidateCommand.cs
│   │   │   │   ├── OrderCommand.cs
│   │   │   │   ├── QuitCommand.cs
│   │   │   │   └── UpdateOrderCommand.cs
│   │   │   ├── Country.cs
│   │   │   ├── Currencies.cs
│   │   │   ├── Data
│   │   │   │   ├── Auxiliary
│   │   │   │   │   ├── AuxiliaryDataKey.cs
│   │   │   │   │   ├── CorporateFactorProvider.cs
│   │   │   │   │   ├── CorporateFactorRow.cs
│   │   │   │   │   ├── FactorFile.cs
│   │   │   │   │   ├── FactorFileZipHelper.cs
│   │   │   │   │   ├── IFactorProvider.cs
│   │   │   │   │   ├── IFactorRow.cs
│   │   │   │   │   ├── LocalDiskFactorFileProvider.cs
│   │   │   │   │   ├── LocalDiskMapFileProvider.cs
│   │   │   │   │   ├── LocalZipFactorFileProvider.cs
│   │   │   │   │   ├── LocalZipMapFileProvider.cs
│   │   │   │   │   ├── MapFile.cs
│   │   │   │   │   ├── MapFilePrimaryExchangeProvider.cs
│   │   │   │   │   ├── MapFileResolver.cs
│   │   │   │   │   ├── MapFileRow.cs
│   │   │   │   │   ├── MapFileZipHelper.cs
│   │   │   │   │   ├── MappingContractFactorProvider.cs
│   │   │   │   │   ├── MappingContractFactorRow.cs
│   │   │   │   │   ├── MappingExtensions.cs
│   │   │   │   │   ├── PriceScalingExtensions.cs
│   │   │   │   │   ├── QuoteConditionFlags.cs
│   │   │   │   │   ├── SymbolDateRange.cs
│   │   │   │   │   ├── TickerDateRange.cs
│   │   │   │   │   └── TradeConditionFlags.cs
│   │   │   │   ├── BaseData.cs
│   │   │   │   ├── BaseDataRequest.cs
│   │   │   │   ├── Channel.cs
│   │   │   │   ├── Consolidators
│   │   │   │   │   ├── BaseDataConsolidator.cs
│   │   │   │   │   ├── BaseTimelessConsolidator.cs
│   │   │   │   │   ├── Calendar.cs
│   │   │   │   │   ├── CalendarType.cs
│   │   │   │   │   ├── ClassicRangeConsolidator.cs
│   │   │   │   │   ├── ClassicRenkoConsolidator.cs
│   │   │   │   │   ├── ConsolidatorBase.cs
│   │   │   │   │   ├── DataConsolidator.cs
│   │   │   │   │   ├── DollarVolumeRenkoConsolidator.cs
│   │   │   │   │   ├── DynamicDataConsolidator.cs
│   │   │   │   │   ├── FilteredIdentityDataConsolidator.cs
│   │   │   │   │   ├── IDataConsolidator.cs
│   │   │   │   │   ├── IdentityDataConsolidator.cs
│   │   │   │   │   ├── MarketHourAwareConsolidator.cs
│   │   │   │   │   ├── OpenInterestConsolidator.cs
│   │   │   │   │   ├── PeriodCountConsolidatorBase.cs
│   │   │   │   │   ├── QuoteBarConsolidator.cs
│   │   │   │   │   ├── RangeConsolidator.cs
│   │   │   │   │   ├── RenkoConsolidator.cs
│   │   │   │   │   ├── SequentialConsolidator.cs
│   │   │   │   │   ├── SessionConsolidator.cs
│   │   │   │   │   ├── TickConsolidator.cs
│   │   │   │   │   ├── TickQuoteBarConsolidator.cs
│   │   │   │   │   ├── TradeBarConsolidator.cs
│   │   │   │   │   ├── TradeBarConsolidatorBase.cs
│   │   │   │   │   └── VolumeRenkoConsolidator.cs
│   │   │   │   ├── ConsolidatorWrapper.cs
│   │   │   │   ├── ConstantDividendYieldModel.cs
│   │   │   │   ├── ConstantRiskFreeRateInterestRateModel.cs
│   │   │   │   ├── Custom
│   │   │   │   │   ├── AlphaStreams
│   │   │   │   │   │   └── PlaceHolder.cs
│   │   │   │   │   ├── FxcmVolume.cs
│   │   │   │   │   ├── IconicTypes
│   │   │   │   │   │   ├── IndexedLinkedData.cs
│   │   │   │   │   │   ├── IndexedLinkedData2.cs
│   │   │   │   │   │   ├── LinkedData.cs
│   │   │   │   │   │   ├── UnlinkedData.cs
│   │   │   │   │   │   └── UnlinkedDataTradeBar.cs
│   │   │   │   │   ├── Intrinio
│   │   │   │   │   │   ├── EconomicDataSources.cs
│   │   │   │   │   │   ├── IntrinioConfig.cs
│   │   │   │   │   │   └── IntrinioEconomicData.cs
│   │   │   │   │   ├── NullData.cs
│   │   │   │   │   └── Tiingo
│   │   │   │   │       ├── Tiingo.cs
│   │   │   │   │       ├── TiingoDailyData.cs
│   │   │   │   │       ├── TiingoPrice.cs
│   │   │   │   │       └── TiingoSymbolMapper.cs
│   │   │   │   ├── DataAggregatorInitializeParameters.cs
│   │   │   │   ├── DataHistory.cs
│   │   │   │   ├── DataMonitor.cs
│   │   │   │   ├── DataQueueHandlerSubscriptionManager.cs
│   │   │   │   ├── DiskDataCacheProvider.cs
│   │   │   │   ├── DividendYieldProvider.cs
│   │   │   │   ├── DownloaderExtensions.cs
│   │   │   │   ├── DynamicData.cs
│   │   │   │   ├── EventBasedDataQueueHandlerSubscriptionManager.cs
│   │   │   │   ├── FileFormat.cs
│   │   │   │   ├── FuncRiskFreeRateInterestRateModel.cs
│   │   │   │   ├── Fundamental
│   │   │   │   │   ├── AssetClassificationHelper.cs
│   │   │   │   │   ├── FineFundamental.cs
│   │   │   │   │   ├── Fundamental.cs
│   │   │   │   │   ├── FundamentalInstanceProvider.cs
│   │   │   │   │   ├── FundamentalProperty.cs
│   │   │   │   │   ├── FundamentalTimeDependentProperty.cs
│   │   │   │   │   ├── FundamentalUniverse.cs
│   │   │   │   │   ├── Generated
│   │   │   │   │   │   ├── AccountsPayableBalanceSheet.cs
│   │   │   │   │   │   ├── AccountsReceivableBalanceSheet.cs
│   │   │   │   │   │   ├── AccruedandDeferredIncomeBalanceSheet.cs
│   │   │   │   │   │   ├── AccruedandDeferredIncomeCurrentBalanceSheet.cs
│   │   │   │   │   │   ├── AccruedandDeferredIncomeNonCurrentBalanceSheet.cs
│   │   │   │   │   │   ├── AccruedInterestReceivableBalanceSheet.cs
│   │   │   │   │   │   ├── AccruedInvestmentIncomeBalanceSheet.cs
│   │   │   │   │   │   ├── AccruedLiabilitiesTotalBalanceSheet.cs
│   │   │   │   │   │   ├── AccumulatedDepreciationBalanceSheet.cs
│   │   │   │   │   │   ├── AdditionalPaidInCapitalBalanceSheet.cs
│   │   │   │   │   │   ├── AdvanceFromFederalHomeLoanBanksBalanceSheet.cs
│   │   │   │   │   │   ├── AdvancesfromCentralBanksBalanceSheet.cs
│   │   │   │   │   │   ├── AllowanceForDoubtfulAccountsReceivableBalanceSheet.cs
│   │   │   │   │   │   ├── AllowanceForLoansAndLeaseLossesBalanceSheet.cs
│   │   │   │   │   │   ├── AllowanceForNotesReceivableBalanceSheet.cs
│   │   │   │   │   │   ├── AllTaxesPaidCashFlowStatement.cs
│   │   │   │   │   │   ├── AmortizationCashFlowStatement.cs
│   │   │   │   │   │   ├── AmortizationIncomeStatement.cs
│   │   │   │   │   │   ├── AmortizationOfFinancingCostsAndDiscountsCashFlowStatement.cs
│   │   │   │   │   │   ├── AmortizationOfIntangiblesCashFlowStatement.cs
│   │   │   │   │   │   ├── AmortizationOfIntangiblesIncomeStatement.cs
│   │   │   │   │   │   ├── AmortizationOfSecuritiesCashFlowStatement.cs
│   │   │   │   │   │   ├── AmortizationSupplementalIncomeStatement.cs
│   │   │   │   │   │   ├── AssetClassification.cs
│   │   │   │   │   │   ├── AssetImpairmentChargeCashFlowStatement.cs
│   │   │   │   │   │   ├── AssetsHeldForSaleBalanceSheet.cs
│   │   │   │   │   │   ├── AssetsHeldForSaleCurrentBalanceSheet.cs
│   │   │   │   │   │   ├── AssetsHeldForSaleNonCurrentBalanceSheet.cs
│   │   │   │   │   │   ├── AssetsOfDiscontinuedOperationsBalanceSheet.cs
│   │   │   │   │   │   ├── AssetsPledgedasCollateralSubjecttoSaleorRepledgingTotalBalanceSheet.cs
│   │   │   │   │   │   ├── AssetsTurnover.cs
│   │   │   │   │   │   ├── AuditorReportStatus.cs
│   │   │   │   │   │   ├── AvailableForSaleSecuritiesBalanceSheet.cs
│   │   │   │   │   │   ├── AverageDilutionEarningsIncomeStatement.cs
│   │   │   │   │   │   ├── AVG5YrsROIC.cs
│   │   │   │   │   │   ├── BalanceSheet.cs
│   │   │   │   │   │   ├── BalanceSheetFileDate.cs
│   │   │   │   │   │   ├── BankIndebtednessBalanceSheet.cs
│   │   │   │   │   │   ├── BankLoansCurrentBalanceSheet.cs
│   │   │   │   │   │   ├── BankLoansNonCurrentBalanceSheet.cs
│   │   │   │   │   │   ├── BankLoansTotalBalanceSheet.cs
│   │   │   │   │   │   ├── BankOwnedLifeInsuranceBalanceSheet.cs
│   │   │   │   │   │   ├── BasicAccountingChange.cs
│   │   │   │   │   │   ├── BasicAverageShares.cs
│   │   │   │   │   │   ├── BasicContinuousOperations.cs
│   │   │   │   │   │   ├── BasicDiscontinuousOperations.cs
│   │   │   │   │   │   ├── BasicEPS.cs
│   │   │   │   │   │   ├── BasicEPSOtherGainsLosses.cs
│   │   │   │   │   │   ├── BasicExtraordinary.cs
│   │   │   │   │   │   ├── BeginningCashPositionCashFlowStatement.cs
│   │   │   │   │   │   ├── BiologicalAssetsBalanceSheet.cs
│   │   │   │   │   │   ├── BookValuePerShareGrowth.cs
│   │   │   │   │   │   ├── BuildingsAndImprovementsBalanceSheet.cs
│   │   │   │   │   │   ├── CapExGrowth.cs
│   │   │   │   │   │   ├── CapExReportedCashFlowStatement.cs
│   │   │   │   │   │   ├── CapExSalesRatio.cs
│   │   │   │   │   │   ├── CapitalExpenditureAnnual5YrGrowth.cs
│   │   │   │   │   │   ├── CapitalExpenditureCashFlowStatement.cs
│   │   │   │   │   │   ├── CapitalExpendituretoEBITDA.cs
│   │   │   │   │   │   ├── CapitalLeaseObligationsBalanceSheet.cs
│   │   │   │   │   │   ├── CapitalStockBalanceSheet.cs
│   │   │   │   │   │   ├── CashAdvancesandLoansMadetoOtherPartiesCashFlowStatement.cs
│   │   │   │   │   │   ├── CashAndCashEquivalentsBalanceSheet.cs
│   │   │   │   │   │   ├── CashAndDueFromBanksBalanceSheet.cs
│   │   │   │   │   │   ├── CashBalanceSheet.cs
│   │   │   │   │   │   ├── CashCashEquivalentsAndFederalFundsSoldBalanceSheet.cs
│   │   │   │   │   │   ├── CashCashEquivalentsAndMarketableSecuritiesBalanceSheet.cs
│   │   │   │   │   │   ├── CashConversionCycle.cs
│   │   │   │   │   │   ├── CashDividendsForMinoritiesCashFlowStatement.cs
│   │   │   │   │   │   ├── CashDividendsPaidCashFlowStatement.cs
│   │   │   │   │   │   ├── CashEquivalentsBalanceSheet.cs
│   │   │   │   │   │   ├── CashFlowFileDate.cs
│   │   │   │   │   │   ├── CashFlowFromContinuingFinancingActivitiesCashFlowStatement.cs
│   │   │   │   │   │   ├── CashFlowFromContinuingInvestingActivitiesCashFlowStatement.cs
│   │   │   │   │   │   ├── CashFlowFromContinuingOperatingActivitiesCashFlowStatement.cs
│   │   │   │   │   │   ├── CashFlowFromDiscontinuedOperationCashFlowStatement.cs
│   │   │   │   │   │   ├── CashFlowfromFinancingGrowth.cs
│   │   │   │   │   │   ├── CashFlowfromInvestingGrowth.cs
│   │   │   │   │   │   ├── CashFlowsfromusedinOperatingActivitiesDirectCashFlowStatement.cs
│   │   │   │   │   │   ├── CashFlowStatement.cs
│   │   │   │   │   │   ├── CashFromDiscontinuedFinancingActivitiesCashFlowStatement.cs
│   │   │   │   │   │   ├── CashFromDiscontinuedInvestingActivitiesCashFlowStatement.cs
│   │   │   │   │   │   ├── CashFromDiscontinuedOperatingActivitiesCashFlowStatement.cs
│   │   │   │   │   │   ├── CashGeneratedfromOperatingActivitiesCashFlowStatement.cs
│   │   │   │   │   │   ├── CashPaidforInsuranceActivitiesCashFlowStatement.cs
│   │   │   │   │   │   ├── CashPaidtoReinsurersCashFlowStatement.cs
│   │   │   │   │   │   ├── CashPaymentsforDepositsbyBanksandCustomersCashFlowStatement.cs
│   │   │   │   │   │   ├── CashPaymentsforLoansCashFlowStatement.cs
│   │   │   │   │   │   ├── CashRatio.cs
│   │   │   │   │   │   ├── CashRatioGrowth.cs
│   │   │   │   │   │   ├── CashReceiptsfromDepositsbyBanksandCustomersCashFlowStatement.cs
│   │   │   │   │   │   ├── CashReceiptsfromFeesandCommissionsCashFlowStatement.cs
│   │   │   │   │   │   ├── CashReceiptsfromLoansCashFlowStatement.cs
│   │   │   │   │   │   ├── CashReceiptsfromRepaymentofAdvancesandLoansMadetoOtherPartiesCashFlowStatement.cs
│   │   │   │   │   │   ├── CashReceiptsfromSecuritiesRelatedActivitiesCashFlowStatement.cs
│   │   │   │   │   │   ├── CashReceiptsfromTaxRefundsCashFlowStatement.cs
│   │   │   │   │   │   ├── CashReceivedfromInsuranceActivitiesCashFlowStatement.cs
│   │   │   │   │   │   ├── CashRestrictedOrPledgedBalanceSheet.cs
│   │   │   │   │   │   ├── CashtoTotalAssets.cs
│   │   │   │   │   │   ├── CededPremiumsIncomeStatement.cs
│   │   │   │   │   │   ├── CFOGrowth.cs
│   │   │   │   │   │   ├── ChangeInAccountPayableCashFlowStatement.cs
│   │   │   │   │   │   ├── ChangeInAccruedExpenseCashFlowStatement.cs
│   │   │   │   │   │   ├── ChangeinAccruedIncomeCashFlowStatement.cs
│   │   │   │   │   │   ├── ChangeInAccruedInvestmentIncomeCashFlowStatement.cs
│   │   │   │   │   │   ├── ChangeinAdvancesfromCentralBanksCashFlowStatement.cs
│   │   │   │   │   │   ├── ChangeinCashSupplementalAsReportedCashFlowStatement.cs
│   │   │   │   │   │   ├── ChangeInDeferredAcquisitionCostsCashFlowStatement.cs
│   │   │   │   │   │   ├── ChangeinDeferredAcquisitionCostsNetCashFlowStatement.cs
│   │   │   │   │   │   ├── ChangeInDeferredChargesCashFlowStatement.cs
│   │   │   │   │   │   ├── ChangeinDepositsbyBanksandCustomersCashFlowStatement.cs
│   │   │   │   │   │   ├── ChangeInDividendPayableCashFlowStatement.cs
│   │   │   │   │   │   ├── ChangeInFederalFundsAndSecuritiesSoldForRepurchaseCashFlowStatement.cs
│   │   │   │   │   │   ├── ChangeinFinancialAssetsCashFlowStatement.cs
│   │   │   │   │   │   ├── ChangeinFinancialLiabilitiesCashFlowStatement.cs
│   │   │   │   │   │   ├── ChangeInFundsWithheldCashFlowStatement.cs
│   │   │   │   │   │   ├── ChangeInIncomeTaxPayableCashFlowStatement.cs
│   │   │   │   │   │   ├── ChangeinInsuranceContractAssetsCashFlowStatement.cs
│   │   │   │   │   │   ├── ChangeinInsuranceContractLiabilitiesCashFlowStatement.cs
│   │   │   │   │   │   ├── ChangeinInsuranceFundsCashFlowStatement.cs
│   │   │   │   │   │   ├── ChangeinInsuranceLiabilitiesNetofReinsuranceIncomeStatement.cs
│   │   │   │   │   │   ├── ChangeInInterestPayableCashFlowStatement.cs
│   │   │   │   │   │   ├── ChangeInInventoryCashFlowStatement.cs
│   │   │   │   │   │   ├── ChangeinInvestmentContractIncomeStatement.cs
│   │   │   │   │   │   ├── ChangeinInvestmentContractLiabilitiesCashFlowStatement.cs
│   │   │   │   │   │   ├── ChangeInLoansCashFlowStatement.cs
│   │   │   │   │   │   ├── ChangeInLossAndLossAdjustmentExpenseReservesCashFlowStatement.cs
│   │   │   │   │   │   ├── ChangeInOtherCurrentAssetsCashFlowStatement.cs
│   │   │   │   │   │   ├── ChangeInOtherCurrentLiabilitiesCashFlowStatement.cs
│   │   │   │   │   │   ├── ChangeInOtherWorkingCapitalCashFlowStatement.cs
│   │   │   │   │   │   ├── ChangeInPayableCashFlowStatement.cs
│   │   │   │   │   │   ├── ChangeInPayablesAndAccruedExpenseCashFlowStatement.cs
│   │   │   │   │   │   ├── ChangeInPrepaidAssetsCashFlowStatement.cs
│   │   │   │   │   │   ├── ChangeInReceivablesCashFlowStatement.cs
│   │   │   │   │   │   ├── ChangeinReinsuranceReceivablesCashFlowStatement.cs
│   │   │   │   │   │   ├── ChangeInReinsuranceRecoverableOnPaidAndUnpaidLossesCashFlowStatement.cs
│   │   │   │   │   │   ├── ChangeInRestrictedCashCashFlowStatement.cs
│   │   │   │   │   │   ├── ChangeInTaxPayableCashFlowStatement.cs
│   │   │   │   │   │   ├── ChangeinTheGrossProvisionforUnearnedPremiumsIncomeStatement.cs
│   │   │   │   │   │   ├── ChangeinTheGrossProvisionforUnearnedPremiumsReinsurersShareIncomeStatement.cs
│   │   │   │   │   │   ├── ChangeInTradingAccountSecuritiesCashFlowStatement.cs
│   │   │   │   │   │   ├── ChangeInUnearnedPremiumsCashFlowStatement.cs
│   │   │   │   │   │   ├── ChangeInWorkingCapitalCashFlowStatement.cs
│   │   │   │   │   │   ├── ChangesInAccountReceivablesCashFlowStatement.cs
│   │   │   │   │   │   ├── ChangesInCashCashFlowStatement.cs
│   │   │   │   │   │   ├── ClaimsandChangeinInsuranceLiabilitiesIncomeStatement.cs
│   │   │   │   │   │   ├── ClaimsandPaidIncurredIncomeStatement.cs
│   │   │   │   │   │   ├── ClaimsOutstandingBalanceSheet.cs
│   │   │   │   │   │   ├── ClaimsPaidCashFlowStatement.cs
│   │   │   │   │   │   ├── ClassesofCashPaymentsCashFlowStatement.cs
│   │   │   │   │   │   ├── ClassesofCashReceiptsfromOperatingActivitiesCashFlowStatement.cs
│   │   │   │   │   │   ├── CommercialLoanBalanceSheet.cs
│   │   │   │   │   │   ├── CommercialPaperBalanceSheet.cs
│   │   │   │   │   │   ├── CommissionExpensesIncomeStatement.cs
│   │   │   │   │   │   ├── CommissionPaidCashFlowStatement.cs
│   │   │   │   │   │   ├── CommonEquityToAssets.cs
│   │   │   │   │   │   ├── CommonStockBalanceSheet.cs
│   │   │   │   │   │   ├── CommonStockDividendPaidCashFlowStatement.cs
│   │   │   │   │   │   ├── CommonStockEquityBalanceSheet.cs
│   │   │   │   │   │   ├── CommonStockIssuanceCashFlowStatement.cs
│   │   │   │   │   │   ├── CommonStockPaymentsCashFlowStatement.cs
│   │   │   │   │   │   ├── CommonUtilityPlantBalanceSheet.cs
│   │   │   │   │   │   ├── CompanyProfile.cs
│   │   │   │   │   │   ├── CompanyReference.cs
│   │   │   │   │   │   ├── ComTreShaNumBalanceSheet.cs
│   │   │   │   │   │   ├── ConstructionInProgressBalanceSheet.cs
│   │   │   │   │   │   ├── ConsumerLoanBalanceSheet.cs
│   │   │   │   │   │   ├── ContinuingAndDiscontinuedBasicEPS.cs
│   │   │   │   │   │   ├── ContinuingAndDiscontinuedDilutedEPS.cs
│   │   │   │   │   │   ├── ConvertibleLoansCurrentBalanceSheet.cs
│   │   │   │   │   │   ├── ConvertibleLoansNonCurrentBalanceSheet.cs
│   │   │   │   │   │   ├── ConvertibleLoansTotalBalanceSheet.cs
│   │   │   │   │   │   ├── CostOfRevenueIncomeStatement.cs
│   │   │   │   │   │   ├── CreditCardIncomeStatement.cs
│   │   │   │   │   │   ├── CreditLossesProvisionIncomeStatement.cs
│   │   │   │   │   │   ├── CreditRiskProvisionsIncomeStatement.cs
│   │   │   │   │   │   ├── CurrentAccruedExpensesBalanceSheet.cs
│   │   │   │   │   │   ├── CurrentAssetsBalanceSheet.cs
│   │   │   │   │   │   ├── CurrentCapitalLeaseObligationBalanceSheet.cs
│   │   │   │   │   │   ├── CurrentDebtAndCapitalLeaseObligationBalanceSheet.cs
│   │   │   │   │   │   ├── CurrentDebtBalanceSheet.cs
│   │   │   │   │   │   ├── CurrentDeferredAssetsBalanceSheet.cs
│   │   │   │   │   │   ├── CurrentDeferredLiabilitiesBalanceSheet.cs
│   │   │   │   │   │   ├── CurrentDeferredRevenueBalanceSheet.cs
│   │   │   │   │   │   ├── CurrentDeferredTaxesAssetsBalanceSheet.cs
│   │   │   │   │   │   ├── CurrentDeferredTaxesLiabilitiesBalanceSheet.cs
│   │   │   │   │   │   ├── CurrentLiabilitiesBalanceSheet.cs
│   │   │   │   │   │   ├── CurrentNotesPayableBalanceSheet.cs
│   │   │   │   │   │   ├── CurrentOtherFinancialLiabilitiesBalanceSheet.cs
│   │   │   │   │   │   ├── CurrentProvisionsBalanceSheet.cs
│   │   │   │   │   │   ├── CurrentRatio.cs
│   │   │   │   │   │   ├── CurrentRatioGrowth.cs
│   │   │   │   │   │   ├── CustomerAcceptancesBalanceSheet.cs
│   │   │   │   │   │   ├── CustomerAccountsBalanceSheet.cs
│   │   │   │   │   │   ├── DaysInInventory.cs
│   │   │   │   │   │   ├── DaysInPayment.cs
│   │   │   │   │   │   ├── DaysInSales.cs
│   │   │   │   │   │   ├── DDACostofRevenueIncomeStatement.cs
│   │   │   │   │   │   ├── DebtDueBeyondBalanceSheet.cs
│   │   │   │   │   │   ├── DebtDueInYear1BalanceSheet.cs
│   │   │   │   │   │   ├── DebtDueInYear2BalanceSheet.cs
│   │   │   │   │   │   ├── DebtDueInYear5BalanceSheet.cs
│   │   │   │   │   │   ├── DebtSecuritiesBalanceSheet.cs
│   │   │   │   │   │   ├── DebtSecuritiesinIssueBalanceSheet.cs
│   │   │   │   │   │   ├── DebttoAssets.cs
│   │   │   │   │   │   ├── DebtTotalBalanceSheet.cs
│   │   │   │   │   │   ├── DecreaseInInterestBearingDepositsInBankCashFlowStatement.cs
│   │   │   │   │   │   ├── DeferredAssetsBalanceSheet.cs
│   │   │   │   │   │   ├── DeferredCostsBalanceSheet.cs
│   │   │   │   │   │   ├── DeferredIncomeTaxCashFlowStatement.cs
│   │   │   │   │   │   ├── DeferredIncomeTotalBalanceSheet.cs
│   │   │   │   │   │   ├── DeferredPolicyAcquisitionCostsBalanceSheet.cs
│   │   │   │   │   │   ├── DeferredTaxAssetsBalanceSheet.cs
│   │   │   │   │   │   ├── DeferredTaxCashFlowStatement.cs
│   │   │   │   │   │   ├── DeferredTaxLiabilitiesTotalBalanceSheet.cs
│   │   │   │   │   │   ├── DefinedPensionBenefitBalanceSheet.cs
│   │   │   │   │   │   ├── DepletionCashFlowStatement.cs
│   │   │   │   │   │   ├── DepletionIncomeStatement.cs
│   │   │   │   │   │   ├── DepositCertificatesBalanceSheet.cs
│   │   │   │   │   │   ├── DepositsbyBankBalanceSheet.cs
│   │   │   │   │   │   ├── DepositsMadeunderAssumedReinsuranceContractBalanceSheet.cs
│   │   │   │   │   │   ├── DepositsReceivedunderCededInsuranceContractBalanceSheet.cs
│   │   │   │   │   │   ├── DepreciationAmortizationDepletionCashFlowStatement.cs
│   │   │   │   │   │   ├── DepreciationAmortizationDepletionIncomeStatement.cs
│   │   │   │   │   │   ├── DepreciationAndAmortizationCashFlowStatement.cs
│   │   │   │   │   │   ├── DepreciationAndAmortizationIncomeStatement.cs
│   │   │   │   │   │   ├── DepreciationCashFlowStatement.cs
│   │   │   │   │   │   ├── DepreciationIncomeStatement.cs
│   │   │   │   │   │   ├── DepreciationSupplementalIncomeStatement.cs
│   │   │   │   │   │   ├── DerivativeAssetsBalanceSheet.cs
│   │   │   │   │   │   ├── DerivativeProductLiabilitiesBalanceSheet.cs
│   │   │   │   │   │   ├── DilutedAccountingChange.cs
│   │   │   │   │   │   ├── DilutedAverageShares.cs
│   │   │   │   │   │   ├── DilutedContEPSGrowth.cs
│   │   │   │   │   │   ├── DilutedContinuousOperations.cs
│   │   │   │   │   │   ├── DilutedDiscontinuousOperations.cs
│   │   │   │   │   │   ├── DilutedEPS.cs
│   │   │   │   │   │   ├── DilutedEPSGrowth.cs
│   │   │   │   │   │   ├── DilutedEPSOtherGainsLosses.cs
│   │   │   │   │   │   ├── DilutedExtraordinary.cs
│   │   │   │   │   │   ├── DilutedNIAvailtoComStockholdersIncomeStatement.cs
│   │   │   │   │   │   ├── DividendCoverageRatio.cs
│   │   │   │   │   │   ├── DividendIncomeIncomeStatement.cs
│   │   │   │   │   │   ├── DividendPaidCFOCashFlowStatement.cs
│   │   │   │   │   │   ├── DividendPerShare.cs
│   │   │   │   │   │   ├── DividendReceivedCFOCashFlowStatement.cs
│   │   │   │   │   │   ├── DividendsPaidDirectCashFlowStatement.cs
│   │   │   │   │   │   ├── DividendsPayableBalanceSheet.cs
│   │   │   │   │   │   ├── DividendsReceivedCFICashFlowStatement.cs
│   │   │   │   │   │   ├── DividendsReceivedDirectCashFlowStatement.cs
│   │   │   │   │   │   ├── DPSGrowth.cs
│   │   │   │   │   │   ├── DueFromRelatedPartiesBalanceSheet.cs
│   │   │   │   │   │   ├── DuefromRelatedPartiesCurrentBalanceSheet.cs
│   │   │   │   │   │   ├── DuefromRelatedPartiesNonCurrentBalanceSheet.cs
│   │   │   │   │   │   ├── DuetoRelatedPartiesBalanceSheet.cs
│   │   │   │   │   │   ├── DuetoRelatedPartiesCurrentBalanceSheet.cs
│   │   │   │   │   │   ├── DuetoRelatedPartiesNonCurrentBalanceSheet.cs
│   │   │   │   │   │   ├── EarningRatios.cs
│   │   │   │   │   │   ├── EarningReports.cs
│   │   │   │   │   │   ├── EarningReportsAccessionNumber.cs
│   │   │   │   │   │   ├── EarningReportsFileDate.cs
│   │   │   │   │   │   ├── EarningReportsFormType.cs
│   │   │   │   │   │   ├── EarningReportsPeriodEndingDate.cs
│   │   │   │   │   │   ├── EarningReportsPeriodType.cs
│   │   │   │   │   │   ├── EarningsFromEquityInterestIncomeStatement.cs
│   │   │   │   │   │   ├── EarningsfromEquityInterestNetOfTaxIncomeStatement.cs
│   │   │   │   │   │   ├── EarningsLossesFromEquityInvestmentsCashFlowStatement.cs
│   │   │   │   │   │   ├── EBITDAGrowth.cs
│   │   │   │   │   │   ├── EBITDAIncomeStatement.cs
│   │   │   │   │   │   ├── EBITDAMargin.cs
│   │   │   │   │   │   ├── EBITIncomeStatement.cs
│   │   │   │   │   │   ├── EBITMargin.cs
│   │   │   │   │   │   ├── EffectiveTaxRateAsReportedIncomeStatement.cs
│   │   │   │   │   │   ├── EffectOfExchangeRateChangesCashFlowStatement.cs
│   │   │   │   │   │   ├── ElectricUtilityPlantBalanceSheet.cs
│   │   │   │   │   │   ├── EmployeeBenefitsBalanceSheet.cs
│   │   │   │   │   │   ├── EndCashPositionCashFlowStatement.cs
│   │   │   │   │   │   ├── EquipmentIncomeStatement.cs
│   │   │   │   │   │   ├── EquityAttributableToOwnersOfParentBalanceSheet.cs
│   │   │   │   │   │   ├── EquityInvestmentsBalanceSheet.cs
│   │   │   │   │   │   ├── EquityPerShareGrowth.cs
│   │   │   │   │   │   ├── EquitySharesInvestmentsBalanceSheet.cs
│   │   │   │   │   │   ├── ExcessTaxBenefitFromStockBasedCompensationCashFlowStatement.cs
│   │   │   │   │   │   ├── ExciseTaxesIncomeStatement.cs
│   │   │   │   │   │   ├── ExpenseRatio.cs
│   │   │   │   │   │   ├── ExplorationDevelopmentAndMineralPropertyLeaseExpensesIncomeStatement.cs
│   │   │   │   │   │   ├── FCFGrowth.cs
│   │   │   │   │   │   ├── FCFNetIncomeRatio.cs
│   │   │   │   │   │   ├── FCFPerShareGrowth.cs
│   │   │   │   │   │   ├── FCFSalesRatio.cs
│   │   │   │   │   │   ├── FCFtoCFO.cs
│   │   │   │   │   │   ├── FederalFundsPurchasedAndSecuritiesSoldUnderAgreementToRepurchaseBalanceSheet.cs
│   │   │   │   │   │   ├── FederalFundsPurchasedBalanceSheet.cs
│   │   │   │   │   │   ├── FederalFundsSoldAndSecuritiesPurchaseUnderAgreementsToResellBalanceSheet.cs
│   │   │   │   │   │   ├── FederalFundsSoldBalanceSheet.cs
│   │   │   │   │   │   ├── FederalHomeLoanBankStockBalanceSheet.cs
│   │   │   │   │   │   ├── FeeRevenueAndOtherIncomeIncomeStatement.cs
│   │   │   │   │   │   ├── FeesandCommissionExpenseIncomeStatement.cs
│   │   │   │   │   │   ├── FeesandCommissionIncomeIncomeStatement.cs
│   │   │   │   │   │   ├── FeesAndCommissionsIncomeStatement.cs
│   │   │   │   │   │   ├── FinanceLeaseReceivablesBalanceSheet.cs
│   │   │   │   │   │   ├── FinanceLeaseReceivablesCurrentBalanceSheet.cs
│   │   │   │   │   │   ├── FinanceLeaseReceivablesNonCurrentBalanceSheet.cs
│   │   │   │   │   │   ├── FinancialAssetsBalanceSheet.cs
│   │   │   │   │   │   ├── FinancialAssetsDesignatedasFairValueThroughProfitorLossTotalBalanceSheet.cs
│   │   │   │   │   │   ├── FinancialInstrumentsSoldUnderAgreementsToRepurchaseBalanceSheet.cs
│   │   │   │   │   │   ├── FinancialLeverage.cs
│   │   │   │   │   │   ├── FinancialLiabilitiesCurrentBalanceSheet.cs
│   │   │   │   │   │   ├── FinancialLiabilitiesDesignatedasFairValueThroughProfitorLossTotalBalanceSheet.cs
│   │   │   │   │   │   ├── FinancialLiabilitiesMeasuredatAmortizedCostTotalBalanceSheet.cs
│   │   │   │   │   │   ├── FinancialLiabilitiesNonCurrentBalanceSheet.cs
│   │   │   │   │   │   ├── FinancialOrDerivativeInvestmentCurrentLiabilitiesBalanceSheet.cs
│   │   │   │   │   │   ├── FinancialStatements.cs
│   │   │   │   │   │   ├── FinancialStatementsAccessionNumber.cs
│   │   │   │   │   │   ├── FinancialStatementsFileDate.cs
│   │   │   │   │   │   ├── FinancialStatementsFormType.cs
│   │   │   │   │   │   ├── FinancialStatementsPeriodEndingDate.cs
│   │   │   │   │   │   ├── FinancialStatementsPeriodType.cs
│   │   │   │   │   │   ├── FinancingCashFlowCashFlowStatement.cs
│   │   │   │   │   │   ├── FineFundamental.cs
│   │   │   │   │   │   ├── FinishedGoodsBalanceSheet.cs
│   │   │   │   │   │   ├── FixAssetsTuronver.cs
│   │   │   │   │   │   ├── FixedAssetsRevaluationReserveBalanceSheet.cs
│   │   │   │   │   │   ├── FixedMaturityInvestmentsBalanceSheet.cs
│   │   │   │   │   │   ├── FlightFleetVehicleAndRelatedEquipmentsBalanceSheet.cs
│   │   │   │   │   │   ├── ForeclosedAssetsBalanceSheet.cs
│   │   │   │   │   │   ├── ForeignCurrencyTranslationAdjustmentsBalanceSheet.cs
│   │   │   │   │   │   ├── ForeignExchangeTradingGainsIncomeStatement.cs
│   │   │   │   │   │   ├── FreeCashFlowCashFlowStatement.cs
│   │   │   │   │   │   ├── FuelAndPurchasePowerIncomeStatement.cs
│   │   │   │   │   │   ├── FuelIncomeStatement.cs
│   │   │   │   │   │   ├── FundFromOperationCashFlowStatement.cs
│   │   │   │   │   │   ├── FuturePolicyBenefitsBalanceSheet.cs
│   │   │   │   │   │   ├── GainLossonDerecognitionofAvailableForSaleFinancialAssetsIncomeStatement.cs
│   │   │   │   │   │   ├── GainLossonFinancialInstrumentsDesignatedasCashFlowHedgesIncomeStatement.cs
│   │   │   │   │   │   ├── GainLossOnInvestmentSecuritiesCashFlowStatement.cs
│   │   │   │   │   │   ├── GainLossonSaleofAssetsIncomeStatement.cs
│   │   │   │   │   │   ├── GainLossOnSaleOfBusinessCashFlowStatement.cs
│   │   │   │   │   │   ├── GainLossOnSaleOfPPECashFlowStatement.cs
│   │   │   │   │   │   ├── GainonInvestmentPropertiesIncomeStatement.cs
│   │   │   │   │   │   ├── GainOnSaleOfBusinessIncomeStatement.cs
│   │   │   │   │   │   ├── GainonSaleofInvestmentPropertyIncomeStatement.cs
│   │   │   │   │   │   ├── GainonSaleofLoansIncomeStatement.cs
│   │   │   │   │   │   ├── GainOnSaleOfPPEIncomeStatement.cs
│   │   │   │   │   │   ├── GainOnSaleOfSecurityIncomeStatement.cs
│   │   │   │   │   │   ├── GainsLossesNotAffectingRetainedEarningsBalanceSheet.cs
│   │   │   │   │   │   ├── GainsLossesonFinancialInstrumentsDuetoFairValueAdjustmentsinHedgeAccountingTotalIncomeStatement.cs
│   │   │   │   │   │   ├── GeneralAndAdministrativeExpenseIncomeStatement.cs
│   │   │   │   │   │   ├── GeneralPartnershipCapitalBalanceSheet.cs
│   │   │   │   │   │   ├── GoodwillAndOtherIntangibleAssetsBalanceSheet.cs
│   │   │   │   │   │   ├── GoodwillBalanceSheet.cs
│   │   │   │   │   │   ├── GrossAccountsReceivableBalanceSheet.cs
│   │   │   │   │   │   ├── GrossDividendPaymentIncomeStatement.cs
│   │   │   │   │   │   ├── GrossLoanBalanceSheet.cs
│   │   │   │   │   │   ├── GrossMargin.cs
│   │   │   │   │   │   ├── GrossMargin5YrAvg.cs
│   │   │   │   │   │   ├── GrossNotesReceivableBalanceSheet.cs
│   │   │   │   │   │   ├── GrossPPEBalanceSheet.cs
│   │   │   │   │   │   ├── GrossPremiumsWrittenIncomeStatement.cs
│   │   │   │   │   │   ├── GrossProfitAnnual5YrGrowth.cs
│   │   │   │   │   │   ├── GrossProfitIncomeStatement.cs
│   │   │   │   │   │   ├── HedgingAssetsCurrentBalanceSheet.cs
│   │   │   │   │   │   ├── HeldToMaturitySecuritiesBalanceSheet.cs
│   │   │   │   │   │   ├── ImpairmentLossesReversalsFinancialInstrumentsNetIncomeStatement.cs
│   │   │   │   │   │   ├── ImpairmentLossReversalRecognizedinProfitorLossCashFlowStatement.cs
│   │   │   │   │   │   ├── ImpairmentOfCapitalAssetsIncomeStatement.cs
│   │   │   │   │   │   ├── IncomefromAssociatesandOtherParticipatingInterestsIncomeStatement.cs
│   │   │   │   │   │   ├── IncomeStatement.cs
│   │   │   │   │   │   ├── IncomeStatementFileDate.cs
│   │   │   │   │   │   ├── IncomeTaxPaidSupplementalDataCashFlowStatement.cs
│   │   │   │   │   │   ├── IncomeTaxPayableBalanceSheet.cs
│   │   │   │   │   │   ├── IncreaseDecreaseInDepositCashFlowStatement.cs
│   │   │   │   │   │   ├── IncreaseDecreaseInLeaseFinancingCashFlowStatement.cs
│   │   │   │   │   │   ├── IncreaseDecreaseInNetUnearnedPremiumReservesIncomeStatement.cs
│   │   │   │   │   │   ├── IncreaseInInterestBearingDepositsInBankCashFlowStatement.cs
│   │   │   │   │   │   ├── IncreaseInLeaseFinancingCashFlowStatement.cs
│   │   │   │   │   │   ├── InsuranceAndClaimsIncomeStatement.cs
│   │   │   │   │   │   ├── InsuranceContractAssetsBalanceSheet.cs
│   │   │   │   │   │   ├── InsuranceContractLiabilitiesBalanceSheet.cs
│   │   │   │   │   │   ├── InsuranceFundsNonCurrentBalanceSheet.cs
│   │   │   │   │   │   ├── InterestandCommissionPaidCashFlowStatement.cs
│   │   │   │   │   │   ├── InterestBearingBorrowingsNonCurrentBalanceSheet.cs
│   │   │   │   │   │   ├── InterestBearingDepositsAssetsBalanceSheet.cs
│   │   │   │   │   │   ├── InterestBearingDepositsLiabilitiesBalanceSheet.cs
│   │   │   │   │   │   ├── InterestCoverage.cs
│   │   │   │   │   │   ├── InterestCreditedOnPolicyholderDepositsCashFlowStatement.cs
│   │   │   │   │   │   ├── InterestExpenseForDepositIncomeStatement.cs
│   │   │   │   │   │   ├── InterestExpenseForFederalFundsSoldAndSecuritiesPurchaseUnderAgreementsToResellIncomeStatement.cs
│   │   │   │   │   │   ├── InterestExpenseForLongTermDebtAndCapitalSecuritiesIncomeStatement.cs
│   │   │   │   │   │   ├── InterestExpenseForShortTermDebtIncomeStatement.cs
│   │   │   │   │   │   ├── InterestExpenseIncomeStatement.cs
│   │   │   │   │   │   ├── InterestExpenseNonOperatingIncomeStatement.cs
│   │   │   │   │   │   ├── InterestIncomeAfterProvisionForLoanLossIncomeStatement.cs
│   │   │   │   │   │   ├── InterestIncomeFromDepositsIncomeStatement.cs
│   │   │   │   │   │   ├── InterestIncomeFromFederalFundsSoldAndSecuritiesPurchaseUnderAgreementsToResellIncomeStatement.cs
│   │   │   │   │   │   ├── InterestIncomeFromLeasesIncomeStatement.cs
│   │   │   │   │   │   ├── InterestIncomeFromLoansAndLeaseIncomeStatement.cs
│   │   │   │   │   │   ├── InterestIncomeFromLoansIncomeStatement.cs
│   │   │   │   │   │   ├── InterestIncomeFromSecuritiesIncomeStatement.cs
│   │   │   │   │   │   ├── InterestIncomeIncomeStatement.cs
│   │   │   │   │   │   ├── InterestIncomeNonOperatingIncomeStatement.cs
│   │   │   │   │   │   ├── InterestPaidCFFCashFlowStatement.cs
│   │   │   │   │   │   ├── InterestPaidCFOCashFlowStatement.cs
│   │   │   │   │   │   ├── InterestPaidDirectCashFlowStatement.cs
│   │   │   │   │   │   ├── InterestPaidSupplementalDataCashFlowStatement.cs
│   │   │   │   │   │   ├── InterestPayableBalanceSheet.cs
│   │   │   │   │   │   ├── InterestReceivedCFICashFlowStatement.cs
│   │   │   │   │   │   ├── InterestReceivedCFOCashFlowStatement.cs
│   │   │   │   │   │   ├── InterestReceivedDirectCashFlowStatement.cs
│   │   │   │   │   │   ├── InventoriesAdjustmentsAllowancesBalanceSheet.cs
│   │   │   │   │   │   ├── InventoryBalanceSheet.cs
│   │   │   │   │   │   ├── InventoryTurnover.cs
│   │   │   │   │   │   ├── InventoryValuationMethod.cs
│   │   │   │   │   │   ├── InvestedCapitalBalanceSheet.cs
│   │   │   │   │   │   ├── InvestingCashFlowCashFlowStatement.cs
│   │   │   │   │   │   ├── InvestmentBankingProfitIncomeStatement.cs
│   │   │   │   │   │   ├── InvestmentContractLiabilitiesBalanceSheet.cs
│   │   │   │   │   │   ├── InvestmentContractLiabilitiesIncurredIncomeStatement.cs
│   │   │   │   │   │   ├── InvestmentinFinancialAssetsBalanceSheet.cs
│   │   │   │   │   │   ├── InvestmentPropertiesBalanceSheet.cs
│   │   │   │   │   │   ├── InvestmentsAndAdvancesBalanceSheet.cs
│   │   │   │   │   │   ├── InvestmentsinAssociatesatCostBalanceSheet.cs
│   │   │   │   │   │   ├── InvestmentsinJointVenturesatCostBalanceSheet.cs
│   │   │   │   │   │   ├── InvestmentsInOtherVenturesUnderEquityMethodBalanceSheet.cs
│   │   │   │   │   │   ├── InvestmentsinSubsidiariesatCostBalanceSheet.cs
│   │   │   │   │   │   ├── IssuanceOfCapitalStockCashFlowStatement.cs
│   │   │   │   │   │   ├── IssuanceOfDebtCashFlowStatement.cs
│   │   │   │   │   │   ├── IssueExpensesCashFlowStatement.cs
│   │   │   │   │   │   ├── ItemsinTheCourseofTransmissiontoOtherBanksBalanceSheet.cs
│   │   │   │   │   │   ├── LandAndImprovementsBalanceSheet.cs
│   │   │   │   │   │   ├── LeasesBalanceSheet.cs
│   │   │   │   │   │   ├── LiabilitiesHeldforSaleCurrentBalanceSheet.cs
│   │   │   │   │   │   ├── LiabilitiesHeldforSaleNonCurrentBalanceSheet.cs
│   │   │   │   │   │   ├── LiabilitiesHeldforSaleTotalBalanceSheet.cs
│   │   │   │   │   │   ├── LiabilitiesOfDiscontinuedOperationsBalanceSheet.cs
│   │   │   │   │   │   ├── LimitedPartnershipCapitalBalanceSheet.cs
│   │   │   │   │   │   ├── LineOfCreditBalanceSheet.cs
│   │   │   │   │   │   ├── LoansandAdvancestoBankBalanceSheet.cs
│   │   │   │   │   │   ├── LoansandAdvancestoCustomerBalanceSheet.cs
│   │   │   │   │   │   ├── LoansHeldForSaleBalanceSheet.cs
│   │   │   │   │   │   ├── LoansReceivableBalanceSheet.cs
│   │   │   │   │   │   ├── LongTermCapitalLeaseObligationBalanceSheet.cs
│   │   │   │   │   │   ├── LongTermDebtAndCapitalLeaseObligationBalanceSheet.cs
│   │   │   │   │   │   ├── LongTermDebtBalanceSheet.cs
│   │   │   │   │   │   ├── LongTermDebtEquityRatio.cs
│   │   │   │   │   │   ├── LongTermDebtIssuanceCashFlowStatement.cs
│   │   │   │   │   │   ├── LongTermDebtPaymentsCashFlowStatement.cs
│   │   │   │   │   │   ├── LongTermDebtTotalCapitalRatio.cs
│   │   │   │   │   │   ├── LongTermInvestmentsBalanceSheet.cs
│   │   │   │   │   │   ├── LongTermProvisionsBalanceSheet.cs
│   │   │   │   │   │   ├── LossAdjustmentExpenseIncomeStatement.cs
│   │   │   │   │   │   ├── LossonExtinguishmentofDebtIncomeStatement.cs
│   │   │   │   │   │   ├── LossRatio.cs
│   │   │   │   │   │   ├── MachineryFurnitureEquipmentBalanceSheet.cs
│   │   │   │   │   │   ├── MaintenanceAndRepairsIncomeStatement.cs
│   │   │   │   │   │   ├── MaterialsAndSuppliesBalanceSheet.cs
│   │   │   │   │   │   ├── MineralPropertiesBalanceSheet.cs
│   │   │   │   │   │   ├── MinimumPensionLiabilitiesBalanceSheet.cs
│   │   │   │   │   │   ├── MinorityInterestBalanceSheet.cs
│   │   │   │   │   │   ├── MinorityInterestCashFlowStatement.cs
│   │   │   │   │   │   ├── MinorityInterestsIncomeStatement.cs
│   │   │   │   │   │   ├── MoneyMarketInvestmentsBalanceSheet.cs
│   │   │   │   │   │   ├── MortgageAndConsumerloansBalanceSheet.cs
│   │   │   │   │   │   ├── MortgageLoanBalanceSheet.cs
│   │   │   │   │   │   ├── NaturalGasFuelAndOtherBalanceSheet.cs
│   │   │   │   │   │   ├── NegativeGoodwillImmediatelyRecognizedIncomeStatement.cs
│   │   │   │   │   │   ├── NetBusinessPurchaseAndSaleCashFlowStatement.cs
│   │   │   │   │   │   ├── NetCashFromDiscontinuedOperationsCashFlowStatement.cs
│   │   │   │   │   │   ├── NetCommonStockIssuanceCashFlowStatement.cs
│   │   │   │   │   │   ├── NetDebtBalanceSheet.cs
│   │   │   │   │   │   ├── NetForeignCurrencyExchangeGainLossCashFlowStatement.cs
│   │   │   │   │   │   ├── NetForeignExchangeGainLossIncomeStatement.cs
│   │   │   │   │   │   ├── NetIncomeCommonStockholdersIncomeStatement.cs
│   │   │   │   │   │   ├── NetIncomeContinuousOperationsIncomeStatement.cs
│   │   │   │   │   │   ├── NetIncomeContinuousOperationsNetMinorityInterestIncomeStatement.cs
│   │   │   │   │   │   ├── NetIncomeContOpsGrowth.cs
│   │   │   │   │   │   ├── NetIncomeDiscontinuousOperationsIncomeStatement.cs
│   │   │   │   │   │   ├── NetIncomeExtraordinaryIncomeStatement.cs
│   │   │   │   │   │   ├── NetIncomeFromContinuingAndDiscontinuedOperationIncomeStatement.cs
│   │   │   │   │   │   ├── NetIncomeFromContinuingOperationNetMinorityInterestIncomeStatement.cs
│   │   │   │   │   │   ├── NetIncomeFromContinuingOperationsCashFlowStatement.cs
│   │   │   │   │   │   ├── NetIncomeFromTaxLossCarryforwardIncomeStatement.cs
│   │   │   │   │   │   ├── NetIncomeGrowth.cs
│   │   │   │   │   │   ├── NetIncomeIncludingNoncontrollingInterestsIncomeStatement.cs
│   │   │   │   │   │   ├── NetIncomeIncomeStatement.cs
│   │   │   │   │   │   ├── NetIncomePerEmployee.cs
│   │   │   │   │   │   ├── NetIntangiblesPurchaseAndSaleCashFlowStatement.cs
│   │   │   │   │   │   ├── NetInterestIncomeIncomeStatement.cs
│   │   │   │   │   │   ├── NetInvestmentIncomeIncomeStatement.cs
│   │   │   │   │   │   ├── NetInvestmentPropertiesPurchaseAndSaleCashFlowStatement.cs
│   │   │   │   │   │   ├── NetInvestmentPurchaseAndSaleCashFlowStatement.cs
│   │   │   │   │   │   ├── NetIssuancePaymentsOfDebtCashFlowStatement.cs
│   │   │   │   │   │   ├── NetLoanBalanceSheet.cs
│   │   │   │   │   │   ├── NetLongTermDebtIssuanceCashFlowStatement.cs
│   │   │   │   │   │   ├── NetMargin.cs
│   │   │   │   │   │   ├── NetNonOperatingInterestIncomeExpenseIncomeStatement.cs
│   │   │   │   │   │   ├── NetOccupancyExpenseIncomeStatement.cs
│   │   │   │   │   │   ├── NetOtherFinancingChargesCashFlowStatement.cs
│   │   │   │   │   │   ├── NetOtherInvestingChangesCashFlowStatement.cs
│   │   │   │   │   │   ├── NetOutwardLoansCashFlowStatement.cs
│   │   │   │   │   │   ├── NetPolicyholderBenefitsAndClaimsIncomeStatement.cs
│   │   │   │   │   │   ├── NetPPEBalanceSheet.cs
│   │   │   │   │   │   ├── NetPPEPurchaseAndSaleCashFlowStatement.cs
│   │   │   │   │   │   ├── NetPreferredStockIssuanceCashFlowStatement.cs
│   │   │   │   │   │   ├── NetPremiumsWrittenIncomeStatement.cs
│   │   │   │   │   │   ├── NetProceedsPaymentForLoanCashFlowStatement.cs
│   │   │   │   │   │   ├── NetRealizedGainLossOnInvestmentsIncomeStatement.cs
│   │   │   │   │   │   ├── NetShortTermDebtIssuanceCashFlowStatement.cs
│   │   │   │   │   │   ├── NetTangibleAssetsBalanceSheet.cs
│   │   │   │   │   │   ├── NetTradingIncomeIncomeStatement.cs
│   │   │   │   │   │   ├── NetUtilityPlantBalanceSheet.cs
│   │   │   │   │   │   ├── NonCurrentAccountsReceivableBalanceSheet.cs
│   │   │   │   │   │   ├── NonCurrentAccruedExpensesBalanceSheet.cs
│   │   │   │   │   │   ├── NonCurrentDeferredAssetsBalanceSheet.cs
│   │   │   │   │   │   ├── NonCurrentDeferredLiabilitiesBalanceSheet.cs
│   │   │   │   │   │   ├── NonCurrentDeferredRevenueBalanceSheet.cs
│   │   │   │   │   │   ├── NonCurrentDeferredTaxesAssetsBalanceSheet.cs
│   │   │   │   │   │   ├── NonCurrentDeferredTaxesLiabilitiesBalanceSheet.cs
│   │   │   │   │   │   ├── NonCurrentNoteReceivablesBalanceSheet.cs
│   │   │   │   │   │   ├── NonCurrentOtherFinancialLiabilitiesBalanceSheet.cs
│   │   │   │   │   │   ├── NonCurrentPensionAndOtherPostretirementBenefitPlansBalanceSheet.cs
│   │   │   │   │   │   ├── NonCurrentPrepaidAssetsBalanceSheet.cs
│   │   │   │   │   │   ├── NonInterestBearingBorrowingsCurrentBalanceSheet.cs
│   │   │   │   │   │   ├── NonInterestBearingBorrowingsNonCurrentBalanceSheet.cs
│   │   │   │   │   │   ├── NonInterestBearingBorrowingsTotalBalanceSheet.cs
│   │   │   │   │   │   ├── NonInterestBearingDepositsBalanceSheet.cs
│   │   │   │   │   │   ├── NonInterestExpenseIncomeStatement.cs
│   │   │   │   │   │   ├── NonInterestIncomeIncomeStatement.cs
│   │   │   │   │   │   ├── NormalizedBasicEPS.cs
│   │   │   │   │   │   ├── NormalizedBasicEPSGrowth.cs
│   │   │   │   │   │   ├── NormalizedDilutedEPS.cs
│   │   │   │   │   │   ├── NormalizedDilutedEPSGrowth.cs
│   │   │   │   │   │   ├── NormalizedEBITAsReportedIncomeStatement.cs
│   │   │   │   │   │   ├── NormalizedEBITDAAsReportedIncomeStatement.cs
│   │   │   │   │   │   ├── NormalizedEBITDAIncomeStatement.cs
│   │   │   │   │   │   ├── NormalizedIncomeAsReportedIncomeStatement.cs
│   │   │   │   │   │   ├── NormalizedIncomeIncomeStatement.cs
│   │   │   │   │   │   ├── NormalizedNetProfitMargin.cs
│   │   │   │   │   │   ├── NormalizedOperatingProfitAsReportedIncomeStatement.cs
│   │   │   │   │   │   ├── NormalizedPreTaxIncomeIncomeStatement.cs
│   │   │   │   │   │   ├── NormalizedROIC.cs
│   │   │   │   │   │   ├── NotesReceivableBalanceSheet.cs
│   │   │   │   │   │   ├── NumberOfShareHolders.cs
│   │   │   │   │   │   ├── OccupancyAndEquipmentIncomeStatement.cs
│   │   │   │   │   │   ├── OperatingCashFlowCashFlowStatement.cs
│   │   │   │   │   │   ├── OperatingExpenseAsReportedIncomeStatement.cs
│   │   │   │   │   │   ├── OperatingExpenseIncomeStatement.cs
│   │   │   │   │   │   ├── OperatingGainsLossesCashFlowStatement.cs
│   │   │   │   │   │   ├── OperatingIncomeIncomeStatement.cs
│   │   │   │   │   │   ├── OperatingLeaseAssetsBalanceSheet.cs
│   │   │   │   │   │   ├── OperatingRevenueIncomeStatement.cs
│   │   │   │   │   │   ├── OperationAndMaintenanceIncomeStatement.cs
│   │   │   │   │   │   ├── OperationIncomeGrowth.cs
│   │   │   │   │   │   ├── OperationMargin.cs
│   │   │   │   │   │   ├── OperationRatios.cs
│   │   │   │   │   │   ├── OperationRevenueGrowth3MonthAvg.cs
│   │   │   │   │   │   ├── OrdinarySharesNumberBalanceSheet.cs
│   │   │   │   │   │   ├── OtherAssetsBalanceSheet.cs
│   │   │   │   │   │   ├── OtherBorrowedFundsBalanceSheet.cs
│   │   │   │   │   │   ├── OtherCapitalStockBalanceSheet.cs
│   │   │   │   │   │   ├── OtherCashAdjustExcludeFromChangeinCashCashFlowStatement.cs
│   │   │   │   │   │   ├── OtherCashAdjustIncludedIntoChangeinCashCashFlowStatement.cs
│   │   │   │   │   │   ├── OtherCashPaymentsfromOperatingActivitiesCashFlowStatement.cs
│   │   │   │   │   │   ├── OtherCashReceiptsfromOperatingActivitiesCashFlowStatement.cs
│   │   │   │   │   │   ├── OtherCostofRevenueIncomeStatement.cs
│   │   │   │   │   │   ├── OtherCurrentAssetsBalanceSheet.cs
│   │   │   │   │   │   ├── OtherCurrentBorrowingsBalanceSheet.cs
│   │   │   │   │   │   ├── OtherCurrentLiabilitiesBalanceSheet.cs
│   │   │   │   │   │   ├── OtherCustomerServicesIncomeStatement.cs
│   │   │   │   │   │   ├── OtherEquityAdjustmentsBalanceSheet.cs
│   │   │   │   │   │   ├── OtherEquityInterestBalanceSheet.cs
│   │   │   │   │   │   ├── OtherFinancialLiabilitiesBalanceSheet.cs
│   │   │   │   │   │   ├── OtherGAIncomeStatement.cs
│   │   │   │   │   │   ├── OtherIncomeExpenseIncomeStatement.cs
│   │   │   │   │   │   ├── OtherIntangibleAssetsBalanceSheet.cs
│   │   │   │   │   │   ├── OtherInterestExpenseIncomeStatement.cs
│   │   │   │   │   │   ├── OtherInterestIncomeIncomeStatement.cs
│   │   │   │   │   │   ├── OtherInventoriesBalanceSheet.cs
│   │   │   │   │   │   ├── OtherInvestedAssetsBalanceSheet.cs
│   │   │   │   │   │   ├── OtherInvestmentsBalanceSheet.cs
│   │   │   │   │   │   ├── OtherLiabilitiesBalanceSheet.cs
│   │   │   │   │   │   ├── OtherLoanAssetsBalanceSheet.cs
│   │   │   │   │   │   ├── OtherLoansCurrentBalanceSheet.cs
│   │   │   │   │   │   ├── OtherLoansNonCurrentBalanceSheet.cs
│   │   │   │   │   │   ├── OtherLoansTotalBalanceSheet.cs
│   │   │   │   │   │   ├── OtherNonCashItemsCashFlowStatement.cs
│   │   │   │   │   │   ├── OtherNonCurrentAssetsBalanceSheet.cs
│   │   │   │   │   │   ├── OtherNonCurrentLiabilitiesBalanceSheet.cs
│   │   │   │   │   │   ├── OtherNonInterestExpenseIncomeStatement.cs
│   │   │   │   │   │   ├── OtherNonInterestIncomeIncomeStatement.cs
│   │   │   │   │   │   ├── OtherNonOperatingExpensesIncomeStatement.cs
│   │   │   │   │   │   ├── OtherNonOperatingIncomeExpensesIncomeStatement.cs
│   │   │   │   │   │   ├── OtherNonOperatingIncomeIncomeStatement.cs
│   │   │   │   │   │   ├── OtherOperatingExpensesIncomeStatement.cs
│   │   │   │   │   │   ├── OtherOperatingIncomeTotalIncomeStatement.cs
│   │   │   │   │   │   ├── OtherOperatingInflowsOutflowsofCashCashFlowStatement.cs
│   │   │   │   │   │   ├── OtherPayableBalanceSheet.cs
│   │   │   │   │   │   ├── OtherPropertiesBalanceSheet.cs
│   │   │   │   │   │   ├── OtherRealEstateOwnedBalanceSheet.cs
│   │   │   │   │   │   ├── OtherReceivablesBalanceSheet.cs
│   │   │   │   │   │   ├── OtherReservesBalanceSheet.cs
│   │   │   │   │   │   ├── OtherShortTermInvestmentsBalanceSheet.cs
│   │   │   │   │   │   ├── OtherSpecialChargesIncomeStatement.cs
│   │   │   │   │   │   ├── OtherStaffCostsIncomeStatement.cs
│   │   │   │   │   │   ├── OtherTaxesIncomeStatement.cs
│   │   │   │   │   │   ├── OtherunderPreferredStockDividendIncomeStatement.cs
│   │   │   │   │   │   ├── OtherUnderwritingExpensesPaidCashFlowStatement.cs
│   │   │   │   │   │   ├── PayablesAndAccruedExpensesBalanceSheet.cs
│   │   │   │   │   │   ├── PayablesBalanceSheet.cs
│   │   │   │   │   │   ├── PaymentForLoansCashFlowStatement.cs
│   │   │   │   │   │   ├── PaymentsonBehalfofEmployeesCashFlowStatement.cs
│   │   │   │   │   │   ├── PaymentstoSuppliersforGoodsandServicesCashFlowStatement.cs
│   │   │   │   │   │   ├── PaymentTurnover.cs
│   │   │   │   │   │   ├── PensionAndEmployeeBenefitExpenseCashFlowStatement.cs
│   │   │   │   │   │   ├── PensionandOtherPostRetirementBenefitPlansCurrentBalanceSheet.cs
│   │   │   │   │   │   ├── PensionAndOtherPostretirementBenefitPlansTotalBalanceSheet.cs
│   │   │   │   │   │   ├── PensionCostsIncomeStatement.cs
│   │   │   │   │   │   ├── PeriodAuditor.cs
│   │   │   │   │   │   ├── PolicyAcquisitionExpenseIncomeStatement.cs
│   │   │   │   │   │   ├── PolicyholderBenefitsCededIncomeStatement.cs
│   │   │   │   │   │   ├── PolicyholderBenefitsGrossIncomeStatement.cs
│   │   │   │   │   │   ├── PolicyholderDepositInvestmentReceivedCashFlowStatement.cs
│   │   │   │   │   │   ├── PolicyholderDividendsIncomeStatement.cs
│   │   │   │   │   │   ├── PolicyholderFundsBalanceSheet.cs
│   │   │   │   │   │   ├── PolicyholderInterestIncomeStatement.cs
│   │   │   │   │   │   ├── PolicyLoansBalanceSheet.cs
│   │   │   │   │   │   ├── PolicyReservesBenefitsBalanceSheet.cs
│   │   │   │   │   │   ├── PostTaxMargin5YrAvg.cs
│   │   │   │   │   │   ├── PreferredSecuritiesOutsideStockEquityBalanceSheet.cs
│   │   │   │   │   │   ├── PreferredSharesNumberBalanceSheet.cs
│   │   │   │   │   │   ├── PreferredStockBalanceSheet.cs
│   │   │   │   │   │   ├── PreferredStockDividendPaidCashFlowStatement.cs
│   │   │   │   │   │   ├── PreferredStockDividendsIncomeStatement.cs
│   │   │   │   │   │   ├── PreferredStockEquityBalanceSheet.cs
│   │   │   │   │   │   ├── PreferredStockIssuanceCashFlowStatement.cs
│   │   │   │   │   │   ├── PreferredStockPaymentsCashFlowStatement.cs
│   │   │   │   │   │   ├── PremiumReceivedCashFlowStatement.cs
│   │   │   │   │   │   ├── PrepaidAssetsBalanceSheet.cs
│   │   │   │   │   │   ├── PretaxIncomeIncomeStatement.cs
│   │   │   │   │   │   ├── PretaxMargin.cs
│   │   │   │   │   │   ├── PreTaxMargin5YrAvg.cs
│   │   │   │   │   │   ├── PreTreShaNumBalanceSheet.cs
│   │   │   │   │   │   ├── ProceedsFromLoansCashFlowStatement.cs
│   │   │   │   │   │   ├── ProceedsFromStockOptionExercisedCashFlowStatement.cs
│   │   │   │   │   │   ├── ProceedsPaymentFederalFundsSoldAndSecuritiesPurchasedUnderAgreementToResellCashFlowStatement.cs
│   │   │   │   │   │   ├── ProceedsPaymentInInterestBearingDepositsInBankCashFlowStatement.cs
│   │   │   │   │   │   ├── ProfessionalExpenseAndContractServicesExpenseIncomeStatement.cs
│   │   │   │   │   │   ├── ProfitMargin5YrAvg.cs
│   │   │   │   │   │   ├── ProfitOnDisposalsCashFlowStatement.cs
│   │   │   │   │   │   ├── PropertiesBalanceSheet.cs
│   │   │   │   │   │   ├── ProvisionandWriteOffofAssetsCashFlowStatement.cs
│   │   │   │   │   │   ├── ProvisionForDoubtfulAccountsIncomeStatement.cs
│   │   │   │   │   │   ├── ProvisionForLoanLeaseAndOtherLossesCashFlowStatement.cs
│   │   │   │   │   │   ├── ProvisionsTotalBalanceSheet.cs
│   │   │   │   │   │   ├── PurchaseOfBusinessCashFlowStatement.cs
│   │   │   │   │   │   ├── PurchaseOfIntangiblesCashFlowStatement.cs
│   │   │   │   │   │   ├── PurchaseOfInvestmentCashFlowStatement.cs
│   │   │   │   │   │   ├── PurchaseOfInvestmentPropertiesCashFlowStatement.cs
│   │   │   │   │   │   ├── PurchaseOfJointVentureAssociateCashFlowStatement.cs
│   │   │   │   │   │   ├── PurchaseOfPPECashFlowStatement.cs
│   │   │   │   │   │   ├── PurchaseOfSubsidiariesCashFlowStatement.cs
│   │   │   │   │   │   ├── QuickRatio.cs
│   │   │   │   │   │   ├── RawMaterialsBalanceSheet.cs
│   │   │   │   │   │   ├── RealizedGainLossOnSaleOfLoansAndLeaseCashFlowStatement.cs
│   │   │   │   │   │   ├── ReceiptsfromCustomersCashFlowStatement.cs
│   │   │   │   │   │   ├── ReceiptsfromGovernmentGrantsCashFlowStatement.cs
│   │   │   │   │   │   ├── ReceivablesAdjustmentsAllowancesBalanceSheet.cs
│   │   │   │   │   │   ├── ReceivablesBalanceSheet.cs
│   │   │   │   │   │   ├── ReceivableTurnover.cs
│   │   │   │   │   │   ├── ReconciledCostOfRevenueIncomeStatement.cs
│   │   │   │   │   │   ├── ReconciledDepreciationIncomeStatement.cs
│   │   │   │   │   │   ├── RegressionGrowthofDividends5Years.cs
│   │   │   │   │   │   ├── RegressionGrowthOperatingRevenue5Years.cs
│   │   │   │   │   │   ├── RegulatoryAssetsBalanceSheet.cs
│   │   │   │   │   │   ├── RegulatoryLiabilitiesBalanceSheet.cs
│   │   │   │   │   │   ├── ReinsuranceandOtherRecoveriesReceivedCashFlowStatement.cs
│   │   │   │   │   │   ├── ReinsuranceAssetsBalanceSheet.cs
│   │   │   │   │   │   ├── ReinsuranceBalancesPayableBalanceSheet.cs
│   │   │   │   │   │   ├── ReinsuranceRecoverableBalanceSheet.cs
│   │   │   │   │   │   ├── ReinsuranceRecoveriesClaimsandBenefitsIncomeStatement.cs
│   │   │   │   │   │   ├── ReinsuranceRecoveriesofInsuranceLiabilitiesIncomeStatement.cs
│   │   │   │   │   │   ├── ReinsuranceRecoveriesofInvestmentContractIncomeStatement.cs
│   │   │   │   │   │   ├── RentandLandingFeesCostofRevenueIncomeStatement.cs
│   │   │   │   │   │   ├── RentAndLandingFeesIncomeStatement.cs
│   │   │   │   │   │   ├── RentExpenseSupplementalIncomeStatement.cs
│   │   │   │   │   │   ├── ReorganizationOtherCostsCashFlowStatement.cs
│   │   │   │   │   │   ├── RepaymentInLeaseFinancingCashFlowStatement.cs
│   │   │   │   │   │   ├── RepaymentOfDebtCashFlowStatement.cs
│   │   │   │   │   │   ├── ReportedNormalizedBasicEPS.cs
│   │   │   │   │   │   ├── ReportedNormalizedDilutedEPS.cs
│   │   │   │   │   │   ├── RepurchaseOfCapitalStockCashFlowStatement.cs
│   │   │   │   │   │   ├── ResearchAndDevelopmentExpensesSupplementalIncomeStatement.cs
│   │   │   │   │   │   ├── ResearchAndDevelopmentIncomeStatement.cs
│   │   │   │   │   │   ├── RestrictedCashAndCashEquivalentsBalanceSheet.cs
│   │   │   │   │   │   ├── RestrictedCashAndInvestmentsBalanceSheet.cs
│   │   │   │   │   │   ├── RestrictedCashBalanceSheet.cs
│   │   │   │   │   │   ├── RestrictedCommonStockBalanceSheet.cs
│   │   │   │   │   │   ├── RestrictedInvestmentsBalanceSheet.cs
│   │   │   │   │   │   ├── RestructuringAndMergernAcquisitionIncomeStatement.cs
│   │   │   │   │   │   ├── RetainedEarningsBalanceSheet.cs
│   │   │   │   │   │   ├── RevenueGrowth.cs
│   │   │   │   │   │   ├── ROA.cs
│   │   │   │   │   │   ├── ROA5YrAvg.cs
│   │   │   │   │   │   ├── ROE.cs
│   │   │   │   │   │   ├── ROE5YrAvg.cs
│   │   │   │   │   │   ├── ROIC.cs
│   │   │   │   │   │   ├── SalariesAndWagesIncomeStatement.cs
│   │   │   │   │   │   ├── SaleOfBusinessCashFlowStatement.cs
│   │   │   │   │   │   ├── SaleOfIntangiblesCashFlowStatement.cs
│   │   │   │   │   │   ├── SaleOfInvestmentCashFlowStatement.cs
│   │   │   │   │   │   ├── SaleOfInvestmentPropertiesCashFlowStatement.cs
│   │   │   │   │   │   ├── SaleOfJointVentureAssociateCashFlowStatement.cs
│   │   │   │   │   │   ├── SaleOfPPECashFlowStatement.cs
│   │   │   │   │   │   ├── SaleOfSubsidiariesCashFlowStatement.cs
│   │   │   │   │   │   ├── SalesPerEmployee.cs
│   │   │   │   │   │   ├── SecuritiesActivitiesIncomeStatement.cs
│   │   │   │   │   │   ├── SecuritiesAmortizationIncomeStatement.cs
│   │   │   │   │   │   ├── SecuritiesAndInvestmentsBalanceSheet.cs
│   │   │   │   │   │   ├── SecuritiesLendingCollateralBalanceSheet.cs
│   │   │   │   │   │   ├── SecuritiesLoanedBalanceSheet.cs
│   │   │   │   │   │   ├── SecurityAgreeToBeResellBalanceSheet.cs
│   │   │   │   │   │   ├── SecurityBorrowedBalanceSheet.cs
│   │   │   │   │   │   ├── SecurityReference.cs
│   │   │   │   │   │   ├── SecuritySoldNotYetRepurchasedBalanceSheet.cs
│   │   │   │   │   │   ├── SellingAndMarketingExpenseIncomeStatement.cs
│   │   │   │   │   │   ├── SellingGeneralAndAdministrationIncomeStatement.cs
│   │   │   │   │   │   ├── SeparateAccountAssetsBalanceSheet.cs
│   │   │   │   │   │   ├── SeparateAccountBusinessBalanceSheet.cs
│   │   │   │   │   │   ├── ServiceChargeOnDepositorAccountsIncomeStatement.cs
│   │   │   │   │   │   ├── ShareIssuedBalanceSheet.cs
│   │   │   │   │   │   ├── ShareOfAssociatesCashFlowStatement.cs
│   │   │   │   │   │   ├── ShortTermDebtIssuanceCashFlowStatement.cs
│   │   │   │   │   │   ├── ShortTermDebtPaymentsCashFlowStatement.cs
│   │   │   │   │   │   ├── ShortTermInvestmentsAvailableForSaleBalanceSheet.cs
│   │   │   │   │   │   ├── ShortTermInvestmentsHeldToMaturityBalanceSheet.cs
│   │   │   │   │   │   ├── ShortTermInvestmentsTradingBalanceSheet.cs
│   │   │   │   │   │   ├── SocialSecurityCostsIncomeStatement.cs
│   │   │   │   │   │   ├── SolvencyRatio.cs
│   │   │   │   │   │   ├── SpecialIncomeChargesIncomeStatement.cs
│   │   │   │   │   │   ├── StaffCostsIncomeStatement.cs
│   │   │   │   │   │   ├── StockBasedCompensationCashFlowStatement.cs
│   │   │   │   │   │   ├── StockBasedCompensationIncomeStatement.cs
│   │   │   │   │   │   ├── StockholdersEquityBalanceSheet.cs
│   │   │   │   │   │   ├── StockholdersEquityGrowth.cs
│   │   │   │   │   │   ├── SubordinatedLiabilitiesBalanceSheet.cs
│   │   │   │   │   │   ├── TangibleBookValueBalanceSheet.cs
│   │   │   │   │   │   ├── TaxAssetsTotalBalanceSheet.cs
│   │   │   │   │   │   ├── TaxEffectOfUnusualItemsIncomeStatement.cs
│   │   │   │   │   │   ├── TaxesAssetsCurrentBalanceSheet.cs
│   │   │   │   │   │   ├── TaxesReceivableBalanceSheet.cs
│   │   │   │   │   │   ├── TaxesRefundPaidCashFlowStatement.cs
│   │   │   │   │   │   ├── TaxesRefundPaidDirectCashFlowStatement.cs
│   │   │   │   │   │   ├── TaxLossCarryforwardBasicEPS.cs
│   │   │   │   │   │   ├── TaxLossCarryforwardDilutedEPS.cs
│   │   │   │   │   │   ├── TaxProvisionIncomeStatement.cs
│   │   │   │   │   │   ├── TaxRate.cs
│   │   │   │   │   │   ├── TaxRateForCalcsIncomeStatement.cs
│   │   │   │   │   │   ├── TotalAdjustmentsforNonCashItemsCashFlowStatement.cs
│   │   │   │   │   │   ├── TotalAssetsBalanceSheet.cs
│   │   │   │   │   │   ├── TotalAssetsGrowth.cs
│   │   │   │   │   │   ├── TotalCapitalizationBalanceSheet.cs
│   │   │   │   │   │   ├── TotalDebtBalanceSheet.cs
│   │   │   │   │   │   ├── TotalDebtEquityRatio.cs
│   │   │   │   │   │   ├── TotalDebtEquityRatioGrowth.cs
│   │   │   │   │   │   ├── TotalDebtInMaturityScheduleBalanceSheet.cs
│   │   │   │   │   │   ├── TotalDeferredCreditsAndOtherNonCurrentLiabilitiesBalanceSheet.cs
│   │   │   │   │   │   ├── TotalDepositsBalanceSheet.cs
│   │   │   │   │   │   ├── TotalDividendPaymentofEquitySharesIncomeStatement.cs
│   │   │   │   │   │   ├── TotalDividendPaymentofNonEquitySharesIncomeStatement.cs
│   │   │   │   │   │   ├── TotalDividendPerShare.cs
│   │   │   │   │   │   ├── TotalEquityAsReportedBalanceSheet.cs
│   │   │   │   │   │   ├── TotalEquityBalanceSheet.cs
│   │   │   │   │   │   ├── TotalEquityGrossMinorityInterestBalanceSheet.cs
│   │   │   │   │   │   ├── TotalExpensesIncomeStatement.cs
│   │   │   │   │   │   ├── TotalFinancialLeaseObligationsBalanceSheet.cs
│   │   │   │   │   │   ├── TotalInvestmentsBalanceSheet.cs
│   │   │   │   │   │   ├── TotalLiabilitiesAsReportedBalanceSheet.cs
│   │   │   │   │   │   ├── TotalLiabilitiesGrowth.cs
│   │   │   │   │   │   ├── TotalLiabilitiesNetMinorityInterestBalanceSheet.cs
│   │   │   │   │   │   ├── TotalMoneyMarketInvestmentsIncomeStatement.cs
│   │   │   │   │   │   ├── TotalNonCurrentAssetsBalanceSheet.cs
│   │   │   │   │   │   ├── TotalNonCurrentLiabilitiesNetMinorityInterestBalanceSheet.cs
│   │   │   │   │   │   ├── TotalOperatingIncomeAsReportedIncomeStatement.cs
│   │   │   │   │   │   ├── TotalOtherFinanceCostIncomeStatement.cs
│   │   │   │   │   │   ├── TotalPartnershipCapitalBalanceSheet.cs
│   │   │   │   │   │   ├── TotalPremiumsEarnedIncomeStatement.cs
│   │   │   │   │   │   ├── TotalRevenueAsReportedIncomeStatement.cs
│   │   │   │   │   │   ├── TotalRevenueIncomeStatement.cs
│   │   │   │   │   │   ├── TotalRiskBasedCapital.cs
│   │   │   │   │   │   ├── TotalTaxPayableBalanceSheet.cs
│   │   │   │   │   │   ├── TotalUnusualItemsExcludingGoodwillIncomeStatement.cs
│   │   │   │   │   │   ├── TotalUnusualItemsIncomeStatement.cs
│   │   │   │   │   │   ├── TradeandOtherPayablesNonCurrentBalanceSheet.cs
│   │   │   │   │   │   ├── TradeAndOtherReceivablesNonCurrentBalanceSheet.cs
│   │   │   │   │   │   ├── TradingandFinancialLiabilitiesBalanceSheet.cs
│   │   │   │   │   │   ├── TradingAndOtherReceivableBalanceSheet.cs
│   │   │   │   │   │   ├── TradingAssetsBalanceSheet.cs
│   │   │   │   │   │   ├── TradingGainLossIncomeStatement.cs
│   │   │   │   │   │   ├── TradingLiabilitiesBalanceSheet.cs
│   │   │   │   │   │   ├── TradingSecuritiesBalanceSheet.cs
│   │   │   │   │   │   ├── TreasuryBillsandOtherEligibleBillsBalanceSheet.cs
│   │   │   │   │   │   ├── TreasurySharesNumberBalanceSheet.cs
│   │   │   │   │   │   ├── TreasuryStockBalanceSheet.cs
│   │   │   │   │   │   ├── TrustFeesbyCommissionsIncomeStatement.cs
│   │   │   │   │   │   ├── UnallocatedSurplusBalanceSheet.cs
│   │   │   │   │   │   ├── UnbilledReceivablesBalanceSheet.cs
│   │   │   │   │   │   ├── UnderwritingExpensesIncomeStatement.cs
│   │   │   │   │   │   ├── UnearnedIncomeBalanceSheet.cs
│   │   │   │   │   │   ├── UnearnedPremiumsBalanceSheet.cs
│   │   │   │   │   │   ├── UnpaidLossAndLossReserveBalanceSheet.cs
│   │   │   │   │   │   ├── UnrealizedGainLossBalanceSheet.cs
│   │   │   │   │   │   ├── UnrealizedGainLossOnInvestmentSecuritiesCashFlowStatement.cs
│   │   │   │   │   │   ├── UnrealizedGainsLossesOnDerivativesCashFlowStatement.cs
│   │   │   │   │   │   ├── ValuationRatios.cs
│   │   │   │   │   │   ├── WagesandSalariesIncomeStatement.cs
│   │   │   │   │   │   ├── WaterProductionBalanceSheet.cs
│   │   │   │   │   │   ├── WorkingCapitalBalanceSheet.cs
│   │   │   │   │   │   ├── WorkingCapitalTurnoverRatio.cs
│   │   │   │   │   │   ├── WorkInProcessBalanceSheet.cs
│   │   │   │   │   │   └── WriteOffIncomeStatement.cs
│   │   │   │   │   ├── MultiPeriodField.cs
│   │   │   │   │   └── Period.cs
│   │   │   │   ├── GetSetPropertyDynamicMetaObject.cs
│   │   │   │   ├── HistoryExtensions.cs
│   │   │   │   ├── HistoryProviderBase.cs
│   │   │   │   ├── HistoryProviderInitializeParameters.cs
│   │   │   │   ├── HistoryRequest.cs
│   │   │   │   ├── HistoryRequestFactory.cs
│   │   │   │   ├── IBaseData.cs
│   │   │   │   ├── IDataAggregator.cs
│   │   │   │   ├── IDividendYieldModel.cs
│   │   │   │   ├── IndexedBasedData.cs
│   │   │   │   ├── IndicatorHistory.cs
│   │   │   │   ├── InterestRateProvider.cs
│   │   │   │   ├── IRiskFreeInterestRateModel.cs
│   │   │   │   ├── ISubscriptionEnumeratorFactory.cs
│   │   │   │   ├── ISymbolProvider.cs
│   │   │   │   ├── LeanDataWriter.cs
│   │   │   │   ├── Market
│   │   │   │   │   ├── Bar.cs
│   │   │   │   │   ├── BarDirection.cs
│   │   │   │   │   ├── BaseChain.cs
│   │   │   │   │   ├── BaseChains.cs
│   │   │   │   │   ├── BaseContract.cs
│   │   │   │   │   ├── BaseRenkoBar.cs
│   │   │   │   │   ├── DataDictionary.cs
│   │   │   │   │   ├── Delisting.cs
│   │   │   │   │   ├── Delistings.cs
│   │   │   │   │   ├── Dividend.cs
│   │   │   │   │   ├── Dividends.cs
│   │   │   │   │   ├── FuturesChain.cs
│   │   │   │   │   ├── FuturesChains.cs
│   │   │   │   │   ├── FuturesContract.cs
│   │   │   │   │   ├── FuturesContracts.cs
│   │   │   │   │   ├── Greeks.cs
│   │   │   │   │   ├── IBar.cs
│   │   │   │   │   ├── IBaseDataBar.cs
│   │   │   │   │   ├── MarginInterestRate.cs
│   │   │   │   │   ├── MarginInterestRates.cs
│   │   │   │   │   ├── ModeledGreeks.cs
│   │   │   │   │   ├── NullGreeks.cs
│   │   │   │   │   ├── OpenInterest.cs
│   │   │   │   │   ├── OptionChain.cs
│   │   │   │   │   ├── OptionChains.cs
│   │   │   │   │   ├── OptionContract.cs
│   │   │   │   │   ├── OptionContracts.cs
│   │   │   │   │   ├── QuoteBar.cs
│   │   │   │   │   ├── QuoteBars.cs
│   │   │   │   │   ├── RangeBar.cs
│   │   │   │   │   ├── RenkoBar.cs
│   │   │   │   │   ├── RenkoType.cs
│   │   │   │   │   ├── Session.cs
│   │   │   │   │   ├── SessionBar.cs
│   │   │   │   │   ├── Split.cs
│   │   │   │   │   ├── Splits.cs
│   │   │   │   │   ├── SymbolChangedEvent.cs
│   │   │   │   │   ├── SymbolChangedEvents.cs
│   │   │   │   │   ├── Tick.cs
│   │   │   │   │   ├── Ticks.cs
│   │   │   │   │   ├── TradeBar.cs
│   │   │   │   │   ├── TradeBars.cs
│   │   │   │   │   └── VolumeRenkoBar.cs
│   │   │   │   ├── Shortable
│   │   │   │   │   ├── InteractiveBrokersShortableProvider.cs
│   │   │   │   │   ├── LocalDiskShortableProvider.cs
│   │   │   │   │   ├── NullShortableProvider.cs
│   │   │   │   │   └── ShortableProviderPythonWrapper.cs
│   │   │   │   ├── Slice.cs
│   │   │   │   ├── SliceExtensions.cs
│   │   │   │   ├── SubscriptionDataConfig.cs
│   │   │   │   ├── SubscriptionDataConfigExtensions.cs
│   │   │   │   ├── SubscriptionDataConfigList.cs
│   │   │   │   ├── SubscriptionDataSource.cs
│   │   │   │   ├── SubscriptionManager.cs
│   │   │   │   └── UniverseSelection
│   │   │   │       ├── BaseChainUniverseData.cs
│   │   │   │       ├── BaseDataCollection.cs
│   │   │   │       ├── BaseFundamentalDataProvider.cs
│   │   │   │       ├── CoarseFundamental.cs
│   │   │   │       ├── CoarseFundamentalDataProvider.cs
│   │   │   │       ├── CoarseFundamentalUniverse.cs
│   │   │   │       ├── ConstituentsUniverse.cs
│   │   │   │       ├── ConstituentsUniverseData.cs
│   │   │   │       ├── ContinuousContractUniverse.cs
│   │   │   │       ├── DerivativeUniverseData.cs
│   │   │   │       ├── ETFConstituentsUniverseFactory.cs
│   │   │   │       ├── ETFConstituentUniverse.cs
│   │   │   │       ├── FineFundamentalFilteredUniverse.cs
│   │   │   │       ├── FineFundamentalUniverse.cs
│   │   │   │       ├── FuncUniverse.cs
│   │   │   │       ├── FundamentalFilteredUniverse.cs
│   │   │   │       ├── FundamentalService.cs
│   │   │   │       ├── FundamentalUniverseFactory.cs
│   │   │   │       ├── FuturesChainUniverse.cs
│   │   │   │       ├── FutureUniverse.cs
│   │   │   │       ├── GetSubscriptionRequestsUniverseDecorator.cs
│   │   │   │       ├── IFundamentalDataProvider.cs
│   │   │   │       ├── ITimeTriggeredUniverse.cs
│   │   │   │       ├── OptionChainUniverse.cs
│   │   │   │       ├── OptionUniverse.cs
│   │   │   │       ├── Schedule.cs
│   │   │   │       ├── ScheduledUniverse.cs
│   │   │   │       ├── SecurityChanges.cs
│   │   │   │       ├── SelectSymbolsUniverseDecorator.cs
│   │   │   │       ├── SubscriptionRequest.cs
│   │   │   │       ├── Universe.cs
│   │   │   │       ├── UniverseDecorator.cs
│   │   │   │       ├── UniverseExtensions.cs
│   │   │   │       ├── UniversePythonWrapper.cs
│   │   │   │       ├── UniverseSettings.cs
│   │   │   │       └── UserDefinedUniverse.cs
│   │   │   ├── DataDownloaderGetParameters.cs
│   │   │   ├── DataMonitorReport.cs
│   │   │   ├── DataProviderEvents.cs
│   │   │   ├── DataUniverseDownloaderGetParameters.cs
│   │   │   ├── DefaultConverter.cs
│   │   │   ├── DocumentationAttribute.cs
│   │   │   ├── Exceptions
│   │   │   │   ├── ClrBubbledExceptionInterpreter.cs
│   │   │   │   ├── DllNotFoundPythonExceptionInterpreter.cs
│   │   │   │   ├── IExceptionInterpreter.cs
│   │   │   │   ├── InvalidTokenPythonExceptionInterpreter.cs
│   │   │   │   ├── KeyErrorPythonExceptionInterpreter.cs
│   │   │   │   ├── ModuleNotFoundPythonExceptionInterpreter.cs
│   │   │   │   ├── MultipleInheritancePythonExceptionInterpreter.cs
│   │   │   │   ├── NoMethodMatchPythonExceptionInterpreter.cs
│   │   │   │   ├── PythonExceptionInterpreter.cs
│   │   │   │   ├── ScheduledEventExceptionInterpreter.cs
│   │   │   │   ├── StackExceptionInterpreter.cs
│   │   │   │   ├── SystemExceptionInterpreter.cs
│   │   │   │   └── UnsupportedOperandPythonExceptionInterpreter.cs
│   │   │   ├── Exchange.cs
│   │   │   ├── Expiry.cs
│   │   │   ├── ExtendedDictionary.cs
│   │   │   ├── Extensions.cs
│   │   │   ├── Field.cs
│   │   │   ├── FileExtension.cs
│   │   │   ├── Global.cs
│   │   │   ├── Globals.cs
│   │   │   ├── IDataDownloader.cs
│   │   │   ├── IIsolatorLimitResultProvider.cs
│   │   │   ├── Indicators
│   │   │   │   ├── IIndicator.cs
│   │   │   │   ├── IIndicatorWarmUpPeriodProvider.cs
│   │   │   │   ├── IndicatorDataPoint.cs
│   │   │   │   ├── IndicatorUpdatedHandler.cs
│   │   │   │   ├── InternalIndicatorValues.cs
│   │   │   │   ├── IReadOnlyWindow.cs
│   │   │   │   ├── OptionPricingModelType.cs
│   │   │   │   ├── RollingWindow.cs
│   │   │   │   └── WindowBase.cs
│   │   │   ├── Interfaces
│   │   │   │   ├── DataProviderDataFetchedEventArgs.cs
│   │   │   │   ├── IAccountCurrencyProvider.cs
│   │   │   │   ├── IAlgorithm.cs
│   │   │   │   ├── IAlgorithmSettings.cs
│   │   │   │   ├── IAlgorithmSubscriptionManager.cs
│   │   │   │   ├── IApi.cs
│   │   │   │   ├── IBrokerage.cs
│   │   │   │   ├── IBrokerageCashSynchronizer.cs
│   │   │   │   ├── IBrokerageFactory.cs
│   │   │   │   ├── IBusyCollection.cs
│   │   │   │   ├── IDataCacheProvider.cs
│   │   │   │   ├── IDataChannelProvider.cs
│   │   │   │   ├── IDataMonitor.cs
│   │   │   │   ├── IDataPermissionManager.cs
│   │   │   │   ├── IDataProvider.cs
│   │   │   │   ├── IDataProviderEvents.cs
│   │   │   │   ├── IDataQueueHandler.cs
│   │   │   │   ├── IDataQueueUniverseProvider.cs
│   │   │   │   ├── IDownloadProvider.cs
│   │   │   │   ├── IExtendedDictionary.cs
│   │   │   │   ├── IFactorFileProvider.cs
│   │   │   │   ├── IFutureChainProvider.cs
│   │   │   │   ├── IHistoryProvider.cs
│   │   │   │   ├── IJobQueueHandler.cs
│   │   │   │   ├── IMapFileProvider.cs
│   │   │   │   ├── IMessagingHandler.cs
│   │   │   │   ├── IObjectStore.cs
│   │   │   │   ├── IOptionChainProvider.cs
│   │   │   │   ├── IOptionPrice.cs
│   │   │   │   ├── IOrderProperties.cs
│   │   │   │   ├── IPrimaryExchangeProvider.cs
│   │   │   │   ├── IRegressionAlgorithmDefinition.cs
│   │   │   │   ├── IRegressionResearchDefinition.cs
│   │   │   │   ├── ISecurityInitializerProvider.cs
│   │   │   │   ├── ISecurityPrice.cs
│   │   │   │   ├── ISecurityService.cs
│   │   │   │   ├── IShortableProvider.cs
│   │   │   │   ├── ISignalExportTarget.cs
│   │   │   │   ├── IStreamReader.cs
│   │   │   │   ├── ISubscriptionDataConfigProvider.cs
│   │   │   │   ├── ISubscriptionDataConfigService.cs
│   │   │   │   ├── ITimeInForceHandler.cs
│   │   │   │   ├── ITimeKeeper.cs
│   │   │   │   ├── ITradeBuilder.cs
│   │   │   │   ├── MessagingHandlerInitializeParameters.cs
│   │   │   │   └── ObjectStoreErrorRaisedEventArgs.cs
│   │   │   ├── ISeriesPoint.cs
│   │   │   ├── Isolator.cs
│   │   │   ├── IsolatorLimitResult.cs
│   │   │   ├── IsolatorLimitResultProvider.cs
│   │   │   ├── ITimeProvider.cs
│   │   │   ├── LocalTimeKeeper.cs
│   │   │   ├── Market.cs
│   │   │   ├── Messages
│   │   │   │   ├── Messages.Algorithm.cs
│   │   │   │   ├── Messages.Algorithm.Framework.Alphas.Analysis.cs
│   │   │   │   ├── Messages.Algorithm.Framework.Alphas.cs
│   │   │   │   ├── Messages.Algorithm.Framework.Portfolio.cs
│   │   │   │   ├── Messages.Benchmarks.cs
│   │   │   │   ├── Messages.Brokerages.cs
│   │   │   │   ├── Messages.Commands.cs
│   │   │   │   ├── Messages.Exceptions.cs
│   │   │   │   ├── Messages.Indicators.cs
│   │   │   │   ├── Messages.Notifications.cs
│   │   │   │   ├── Messages.Optimizer.Objectives.cs
│   │   │   │   ├── Messages.Optimizer.Parameters.cs
│   │   │   │   ├── Messages.Orders.cs
│   │   │   │   ├── Messages.Orders.Fees.cs
│   │   │   │   ├── Messages.Orders.Fills.cs
│   │   │   │   ├── Messages.Orders.OptionExercise.cs
│   │   │   │   ├── Messages.Orders.Slippage.cs
│   │   │   │   ├── Messages.Python.cs
│   │   │   │   ├── Messages.QuantConnect.cs
│   │   │   │   ├── Messages.Securities.cs
│   │   │   │   └── Messages.Securities.Positions.cs
│   │   │   ├── Notifications
│   │   │   │   ├── Notification.cs
│   │   │   │   ├── NotificationJsonConverter.cs
│   │   │   │   └── NotificationManager.cs
│   │   │   ├── Optimizer
│   │   │   │   ├── Analysis
│   │   │   │   │   └── OptimizationAnalysisRunParameters.cs
│   │   │   │   ├── BacktestSummary.cs
│   │   │   │   ├── Cluster.cs
│   │   │   │   ├── FailedBacktestSummary.cs
│   │   │   │   ├── LinearSegment.cs
│   │   │   │   ├── Mode.cs
│   │   │   │   ├── Objectives
│   │   │   │   │   ├── Constraint.cs
│   │   │   │   │   ├── Extremum.cs
│   │   │   │   │   ├── ExtremumJsonConverter.cs
│   │   │   │   │   ├── Maximization.cs
│   │   │   │   │   ├── Minimization.cs
│   │   │   │   │   ├── Objective.cs
│   │   │   │   │   └── Target.cs
│   │   │   │   ├── OptimizationAnalysis.cs
│   │   │   │   ├── OptimizationBacktestMetrics.cs
│   │   │   │   ├── OptimizationStatus.cs
│   │   │   │   ├── ParameterReport.cs
│   │   │   │   ├── Parameters
│   │   │   │   │   ├── OptimizationParameter.cs
│   │   │   │   │   ├── OptimizationParameterJsonConverter.cs
│   │   │   │   │   ├── OptimizationStepParameter.cs
│   │   │   │   │   ├── ParameterSet.cs
│   │   │   │   │   └── StaticOptimizationParameter.cs
│   │   │   │   ├── SharpeSummary.cs
│   │   │   │   └── SliceFit.cs
│   │   │   ├── Orders
│   │   │   │   ├── AlpacaOrderProperties.cs
│   │   │   │   ├── BinanceOrderProperties.cs
│   │   │   │   ├── BitfinexOrderProperties.cs
│   │   │   │   ├── BloombergFixOrderProperties.cs
│   │   │   │   ├── BrokerageOrderIdChangedEvent.cs
│   │   │   │   ├── BybitOrderProperties.cs
│   │   │   │   ├── CancelOrderRequest.cs
│   │   │   │   ├── CharlesSchwabOrderProperties.cs
│   │   │   │   ├── CoinbaseOrderProperties.cs
│   │   │   │   ├── ComboLegLimitOrder.cs
│   │   │   │   ├── ComboLimitOrder.cs
│   │   │   │   ├── ComboMarketOrder.cs
│   │   │   │   ├── ComboOrder.cs
│   │   │   │   ├── dYdXOrderProperties.cs
│   │   │   │   ├── EzeOrderProperties.cs
│   │   │   │   ├── Fees
│   │   │   │   │   ├── AlpacaFeeModel.cs
│   │   │   │   │   ├── AlphaStreamsFeeModel.cs
│   │   │   │   │   ├── AxosFeeModel.cs
│   │   │   │   │   ├── BinanceCoinFuturesFeeModel.cs
│   │   │   │   │   ├── BinanceFeeModel.cs
│   │   │   │   │   ├── BinanceFuturesFeeModel.cs
│   │   │   │   │   ├── BitfinexFeeModel.cs
│   │   │   │   │   ├── BybitFeeModel.cs
│   │   │   │   │   ├── BybitFuturesFeeModel.cs
│   │   │   │   │   ├── CharlesSchwabFeeModel.cs
│   │   │   │   │   ├── CoinbaseFeeModel.cs
│   │   │   │   │   ├── ConstantFeeModel.cs
│   │   │   │   │   ├── dYdXFeeModel.cs
│   │   │   │   │   ├── ExanteFeeModel.cs
│   │   │   │   │   ├── EzeFeeModel.cs
│   │   │   │   │   ├── FeeModel.cs
│   │   │   │   │   ├── FTXFeeModel.cs
│   │   │   │   │   ├── FTXUSFeeModel.cs
│   │   │   │   │   ├── FxcmFeeModel.cs
│   │   │   │   │   ├── GDAXFeeModel.cs
│   │   │   │   │   ├── IFeeModel.cs
│   │   │   │   │   ├── IndiaFeeModel.cs
│   │   │   │   │   ├── InteractiveBrokersFeeModel.cs
│   │   │   │   │   ├── KrakenFeeModel.cs
│   │   │   │   │   ├── ModifiedFillQuantityOrderFee.cs
│   │   │   │   │   ├── OrderFee.cs
│   │   │   │   │   ├── OrderFeeParameters.cs
│   │   │   │   │   ├── PublicFeeModel.cs
│   │   │   │   │   ├── RBIFeeModel.cs
│   │   │   │   │   ├── SamcoFeeModel.cs
│   │   │   │   │   ├── TastytradeFeeModel.cs
│   │   │   │   │   ├── TDAmeritradeFeeModel.cs
│   │   │   │   │   ├── TradeStationFeeModel.cs
│   │   │   │   │   ├── WebullFeeModel.cs
│   │   │   │   │   ├── WolverineFeeModel.cs
│   │   │   │   │   └── ZerodhaFeeModel.cs
│   │   │   │   ├── Fills
│   │   │   │   │   ├── EquityFillModel.cs
│   │   │   │   │   ├── Fill.cs
│   │   │   │   │   ├── FillModel.cs
│   │   │   │   │   ├── FillModelParameters.cs
│   │   │   │   │   ├── FutureFillModel.cs
│   │   │   │   │   ├── FutureOptionFillModel.cs
│   │   │   │   │   ├── IFillModel.cs
│   │   │   │   │   ├── ImmediateFillModel.cs
│   │   │   │   │   ├── LatestPriceFillModel.cs
│   │   │   │   │   └── Prices.cs
│   │   │   │   ├── FixOrderProperites.cs
│   │   │   │   ├── FixOrderProperties.cs
│   │   │   │   ├── FTXOrderProperties.cs
│   │   │   │   ├── GDAXOrderProperties.cs
│   │   │   │   ├── GroupOrderCacheManager.cs
│   │   │   │   ├── GroupOrderExtensions.cs
│   │   │   │   ├── GroupOrderManager.cs
│   │   │   │   ├── IndiaOrderProperties.cs
│   │   │   │   ├── InteractiveBrokersFixOrderProperties.cs
│   │   │   │   ├── InteractiveBrokersOrderProperties.cs
│   │   │   │   ├── KrakenOrderProperties.cs
│   │   │   │   ├── Leg.cs
│   │   │   │   ├── LimitIfTouchedOrder.cs
│   │   │   │   ├── LimitOrder.cs
│   │   │   │   ├── MarketOnCloseOrder.cs
│   │   │   │   ├── MarketOnOpenOrder.cs
│   │   │   │   ├── MarketOrder.cs
│   │   │   │   ├── OptionExercise
│   │   │   │   │   ├── DefaultExerciseModel.cs
│   │   │   │   │   ├── IOptionExerciseModel.cs
│   │   │   │   │   └── OptionExerciseModelPythonWrapper.cs
│   │   │   │   ├── OptionExerciseOrder.cs
│   │   │   │   ├── Order.cs
│   │   │   │   ├── OrderError.cs
│   │   │   │   ├── OrderEvent.cs
│   │   │   │   ├── OrderExtensions.cs
│   │   │   │   ├── OrderField.cs
│   │   │   │   ├── OrderJsonConverter.cs
│   │   │   │   ├── OrderProperties.cs
│   │   │   │   ├── OrderRequest.cs
│   │   │   │   ├── OrderRequestStatus.cs
│   │   │   │   ├── OrderRequestType.cs
│   │   │   │   ├── OrderResponse.cs
│   │   │   │   ├── OrderResponseErrorCode.cs
│   │   │   │   ├── OrderSizing.cs
│   │   │   │   ├── OrdersResponseWrapper.cs
│   │   │   │   ├── OrderSubmissionData.cs
│   │   │   │   ├── OrderTicket.cs
│   │   │   │   ├── OrderTypes.cs
│   │   │   │   ├── OrderUpdateEvent.cs
│   │   │   │   ├── PublicOrderProperties.cs
│   │   │   │   ├── RBIOrderProperties.cs
│   │   │   │   ├── ReadOrdersResponseJsonConverter.cs
│   │   │   │   ├── Serialization
│   │   │   │   │   ├── OrderEventJsonConverter.cs
│   │   │   │   │   └── SerializedOrderEvent.cs
│   │   │   │   ├── Slippage
│   │   │   │   │   ├── AlphaStreamsSlippageModel.cs
│   │   │   │   │   ├── ConstantSlippageModel.cs
│   │   │   │   │   ├── ISlippageModel.cs
│   │   │   │   │   ├── MarketImpactSlippageModel.cs
│   │   │   │   │   ├── NullSlippageModel.cs
│   │   │   │   │   ├── VolumeShareSlippageModel.cs
│   │   │   │   │   └── VolumeShareSlippageModel.py
│   │   │   │   ├── StopLimitOrder.cs
│   │   │   │   ├── StopMarketOrder.cs
│   │   │   │   ├── SubmitOrderRequest.cs
│   │   │   │   ├── TastytradeOrderProperties.cs
│   │   │   │   ├── TDAmeritradeOrderProperties.cs
│   │   │   │   ├── TerminalLinkOrderProperties.cs
│   │   │   │   ├── TimeInForce.cs
│   │   │   │   ├── TimeInForceJsonConverter.cs
│   │   │   │   ├── TimeInForces
│   │   │   │   │   ├── DayTimeInForce.cs
│   │   │   │   │   ├── GoodTilCanceledTimeInForce.cs
│   │   │   │   │   └── GoodTilDateTimeInForce.cs
│   │   │   │   ├── TradeStationOrderProperties.cs
│   │   │   │   ├── TradierOrderProperties.cs
│   │   │   │   ├── TradingTechnologiesOrderProperties.cs
│   │   │   │   ├── TrailingStopOrder.cs
│   │   │   │   ├── UpdateOrderFields.cs
│   │   │   │   ├── UpdateOrderRequest.cs
│   │   │   │   ├── WebullOrderProperties.cs
│   │   │   │   └── WolverineOrderProperties.cs
│   │   │   ├── OS.cs
│   │   │   ├── Packets
│   │   │   │   ├── AlgorithmNameUpdatePacket.cs
│   │   │   │   ├── AlgorithmNodePacket.cs
│   │   │   │   ├── AlgorithmStatusPacket.cs
│   │   │   │   ├── AlgorithmTagsUpdatePacket.cs
│   │   │   │   ├── AlphaNodePacket.cs
│   │   │   │   ├── AlphaResultPacket.cs
│   │   │   │   ├── BacktestNodePacket.cs
│   │   │   │   ├── BacktestResultPacket.cs
│   │   │   │   ├── BacktestResultParameters.cs
│   │   │   │   ├── BaseResultParameters.cs
│   │   │   │   ├── Controls.cs
│   │   │   │   ├── DebugPacket.cs
│   │   │   │   ├── HandledErrorPacket.cs
│   │   │   │   ├── HistoryPacket.cs
│   │   │   │   ├── LeakyBucketControlParameters.cs
│   │   │   │   ├── LiveNodePacket.cs
│   │   │   │   ├── LiveResultPacket.cs
│   │   │   │   ├── LiveResultParameters.cs
│   │   │   │   ├── LogPacket.cs
│   │   │   │   ├── MarketTodayPacket.cs
│   │   │   │   ├── OrderEventPacket.cs
│   │   │   │   ├── Packet.cs
│   │   │   │   ├── PythonEnvironmentPacket.cs
│   │   │   │   ├── ResearchNodePacket.cs
│   │   │   │   ├── RuntimeErrorPacket.cs
│   │   │   │   ├── SecurityTypesPacket.cs
│   │   │   │   ├── StoragePermissions.cs
│   │   │   │   └── SystemDebugPacket.cs
│   │   │   ├── PandasMapper.py
│   │   │   ├── Parameters
│   │   │   │   └── ParameterAttribute.cs
│   │   │   ├── Parse.cs
│   │   │   ├── Properties
│   │   │   │   ├── AssemblyInfo.cs
│   │   │   │   └── SharedAssemblyInfo.cs
│   │   │   ├── Python
│   │   │   │   ├── BasePythonWrapper.cs
│   │   │   │   ├── BenchmarkPythonWrapper.cs
│   │   │   │   ├── BrokerageMessageHandlerPythonWrapper.cs
│   │   │   │   ├── BrokerageModelPythonWrapper.cs
│   │   │   │   ├── BuyingPowerModelPythonWrapper.cs
│   │   │   │   ├── CommandPythonWrapper.cs
│   │   │   │   ├── DataConsolidatorPythonWrapper.cs
│   │   │   │   ├── DividendYieldModelPythonWrapper.cs
│   │   │   │   ├── FeeModelPythonWrapper.cs
│   │   │   │   ├── FillModelPythonWrapper.cs
│   │   │   │   ├── MarginCallModelPythonWrapper.cs
│   │   │   │   ├── MarginInterestRateModelPythonWrapper.cs
│   │   │   │   ├── OptionAssignmentModelPythonWrapper.cs
│   │   │   │   ├── OptionPriceModelPythonWrapper.cs
│   │   │   │   ├── PandasColumnAttribute.cs
│   │   │   │   ├── PandasConverter.cs
│   │   │   │   ├── PandasConverter.DataFrameGenerator.cs
│   │   │   │   ├── PandasData.cs
│   │   │   │   ├── PandasData.DataTypeMember.cs
│   │   │   │   ├── PandasIgnoreAttribute.cs
│   │   │   │   ├── PandasIgnoreMembersAttribute.cs
│   │   │   │   ├── PandasNonExpandableAttribute.cs
│   │   │   │   ├── Python.Runtime.dll.config
│   │   │   │   ├── PythonActivator.cs
│   │   │   │   ├── PythonConsolidator.cs
│   │   │   │   ├── PythonData.cs
│   │   │   │   ├── PythonInitializer.cs
│   │   │   │   ├── PythonWrapper.cs
│   │   │   │   ├── RiskFreeInterestRateModelPythonWrapper.cs
│   │   │   │   ├── SecurityInitializerPythonWrapper.cs
│   │   │   │   ├── SettlementModelPythonWrapper.cs
│   │   │   │   ├── SignalExportTargetPythonWrapper.cs
│   │   │   │   ├── SlippageModelPythonWrapper.cs
│   │   │   │   └── VolatilityModelPythonWrapper.cs
│   │   │   ├── QuantConnect.csproj
│   │   │   ├── RealTimeProvider.cs
│   │   │   ├── RealTimeSynchronizedTimer.cs
│   │   │   ├── RegressionTestException.cs
│   │   │   ├── Result.cs
│   │   │   ├── ScatterChartPoint.cs
│   │   │   ├── ScatterChartPointJsonConverter.cs
│   │   │   ├── Scheduling
│   │   │   │   ├── BaseScheduleRules.cs
│   │   │   │   ├── CompositeTimeRule.cs
│   │   │   │   ├── DateRules.cs
│   │   │   │   ├── FluentScheduledEventBuilder.cs
│   │   │   │   ├── FuncDateRule.cs
│   │   │   │   ├── FuncTimeRule.cs
│   │   │   │   ├── IDateRule.cs
│   │   │   │   ├── IEventSchedule.cs
│   │   │   │   ├── ITimeRule.cs
│   │   │   │   ├── ScheduledEvent.cs
│   │   │   │   ├── ScheduledEventException.cs
│   │   │   │   ├── ScheduleManager.cs
│   │   │   │   ├── TimeConsumer.cs
│   │   │   │   ├── TimeMonitor.cs
│   │   │   │   └── TimeRules.cs
│   │   │   ├── Securities
│   │   │   │   ├── AccountCurrencyImmediateSettlementModel.cs
│   │   │   │   ├── AccountEvent.cs
│   │   │   │   ├── AdjustedPriceVariationModel.cs
│   │   │   │   ├── ApplyFundsSettlementModelParameters.cs
│   │   │   │   ├── BaseSecurityDatabase.cs
│   │   │   │   ├── BrokerageModelSecurityInitializer.cs
│   │   │   │   ├── BuyingPower.cs
│   │   │   │   ├── BuyingPowerModel.cs
│   │   │   │   ├── BuyingPowerModelExtensions.cs
│   │   │   │   ├── BuyingPowerParameters.cs
│   │   │   │   ├── Cash.cs
│   │   │   │   ├── CashAmount.cs
│   │   │   │   ├── CashBook.cs
│   │   │   │   ├── CashBookUpdatedEventArgs.cs
│   │   │   │   ├── CashBuyingPowerModel.cs
│   │   │   │   ├── Cfd
│   │   │   │   │   ├── Cfd.cs
│   │   │   │   │   ├── CfdCache.cs
│   │   │   │   │   ├── CfdDataFilter.cs
│   │   │   │   │   ├── CfdExchange.cs
│   │   │   │   │   └── CfdHolding.cs
│   │   │   │   ├── CompositeSecurityInitializer.cs
│   │   │   │   ├── ConstantBuyingPowerModel.cs
│   │   │   │   ├── ContractSecurityFilterUniverse.cs
│   │   │   │   ├── ContractSymbolProperties.cs
│   │   │   │   ├── ConvertibleCashAmount.cs
│   │   │   │   ├── Crypto
│   │   │   │   │   ├── Crypto.cs
│   │   │   │   │   ├── CryptoExchange.cs
│   │   │   │   │   └── CryptoHolding.cs
│   │   │   │   ├── CryptoFuture
│   │   │   │   │   ├── BinanceCryptoFutureMarginModel.cs
│   │   │   │   │   ├── BinanceFutureMarginInterestRateModel.cs
│   │   │   │   │   ├── BybitFutureMarginInterestRateModel.cs
│   │   │   │   │   ├── CryptoFuture.cs
│   │   │   │   │   ├── CryptoFutureExchange.cs
│   │   │   │   │   ├── CryptoFutureHolding.cs
│   │   │   │   │   ├── CryptoFutureMarginModel.cs
│   │   │   │   │   └── dYdXFutureMarginInterestRateModel.cs
│   │   │   │   ├── CurrencyConversion
│   │   │   │   │   ├── ConstantCurrencyConversion.cs
│   │   │   │   │   ├── ICurrencyConversion.cs
│   │   │   │   │   └── SecurityCurrencyConversion.cs
│   │   │   │   ├── DefaultMarginCallModel.cs
│   │   │   │   ├── DelayedSettlementModel.cs
│   │   │   │   ├── DynamicSecurityData.cs
│   │   │   │   ├── EmptyContractFilter.cs
│   │   │   │   ├── Equity
│   │   │   │   │   ├── Equity.cs
│   │   │   │   │   ├── EquityCache.cs
│   │   │   │   │   ├── EquityDataFilter.cs
│   │   │   │   │   ├── EquityExchange.cs
│   │   │   │   │   ├── EquityHolding.cs
│   │   │   │   │   └── ShortMarginInterestRateModel.cs
│   │   │   │   ├── EquityPriceVariationModel.cs
│   │   │   │   ├── ErrorCurrencyConverter.cs
│   │   │   │   ├── Forex
│   │   │   │   │   ├── Forex.cs
│   │   │   │   │   ├── ForexCache.cs
│   │   │   │   │   ├── ForexDataFilter.cs
│   │   │   │   │   ├── ForexExchange.cs
│   │   │   │   │   └── ForexHolding.cs
│   │   │   │   ├── FuncSecurityDerivativeFilter.cs
│   │   │   │   ├── FuncSecurityInitializer.cs
│   │   │   │   ├── FuncSecuritySeeder.cs
│   │   │   │   ├── Future
│   │   │   │   │   ├── EmptyFutureChainProvider.cs
│   │   │   │   │   ├── Future.cs
│   │   │   │   │   ├── FutureCache.cs
│   │   │   │   │   ├── FutureExchange.cs
│   │   │   │   │   ├── FutureExpirationCycles.cs
│   │   │   │   │   ├── FutureFilterUniverse.cs
│   │   │   │   │   ├── FutureHolding.cs
│   │   │   │   │   ├── FutureMarginModel.cs
│   │   │   │   │   ├── Futures.cs
│   │   │   │   │   ├── FutureSettlementModel.cs
│   │   │   │   │   ├── FuturesExpiryFunctions.cs
│   │   │   │   │   ├── FuturesExpiryUtilityFunctions.cs
│   │   │   │   │   ├── FuturesListings.cs
│   │   │   │   │   ├── FutureSymbol.cs
│   │   │   │   │   └── MarginRequirementsEntry.cs
│   │   │   │   ├── FutureOption
│   │   │   │   │   ├── Api
│   │   │   │   │   │   ├── CMEOptionChainQuotes.cs
│   │   │   │   │   │   ├── CMEOptionsCategoryList.cs
│   │   │   │   │   │   ├── CMEProductSlateV2.cs
│   │   │   │   │   │   └── CMEStrikePriceScalingFactors.cs
│   │   │   │   │   ├── FutureOption.cs
│   │   │   │   │   ├── FutureOptionCache.cs
│   │   │   │   │   ├── FutureOptionSymbol.cs
│   │   │   │   │   ├── FuturesOptionsExpiryFunctions.cs
│   │   │   │   │   ├── FuturesOptionsMarginModel.cs
│   │   │   │   │   ├── FuturesOptionsSymbolMappings.cs
│   │   │   │   │   └── FuturesOptionsUnderlyingMapper.cs
│   │   │   │   ├── GetMaximumOrderQuantityForDeltaBuyingPowerParameters.cs
│   │   │   │   ├── GetMaximumOrderQuantityForTargetBuyingPowerParameters.cs
│   │   │   │   ├── GetMaximumOrderQuantityResult.cs
│   │   │   │   ├── GetMinimumPriceVariationParameters.cs
│   │   │   │   ├── HasSufficientBuyingPowerForOrderParameters.cs
│   │   │   │   ├── HasSufficientBuyingPowerForOrderResult.cs
│   │   │   │   ├── IBaseCurrencySymbol.cs
│   │   │   │   ├── IBuyingPowerModel.cs
│   │   │   │   ├── IChainUniverseData.cs
│   │   │   │   ├── IContinuousSecurity.cs
│   │   │   │   ├── ICurrencyConverter.cs
│   │   │   │   ├── IdentityCurrencyConverter.cs
│   │   │   │   ├── IDerivativeSecurity.cs
│   │   │   │   ├── IDerivativeSecurityFilter.cs
│   │   │   │   ├── IDerivativeSecurityFilterUniverse.cs
│   │   │   │   ├── IMarginCallModel.cs
│   │   │   │   ├── IMarginInterestRateModel.cs
│   │   │   │   ├── ImmediateSettlementModel.cs
│   │   │   │   ├── Index
│   │   │   │   │   ├── Index.cs
│   │   │   │   │   ├── IndexCache.cs
│   │   │   │   │   ├── IndexDataFilter.cs
│   │   │   │   │   ├── IndexExchange.cs
│   │   │   │   │   ├── IndexHolding.cs
│   │   │   │   │   └── IndexSymbol.cs
│   │   │   │   ├── IndexOption
│   │   │   │   │   ├── IndexOption.cs
│   │   │   │   │   ├── IndexOptionCache.cs
│   │   │   │   │   ├── IndexOptionPriceVariationModel.cs
│   │   │   │   │   ├── IndexOptionSymbol.cs
│   │   │   │   │   └── IndexOptionSymbolProperties.cs
│   │   │   │   ├── InitialMargin.cs
│   │   │   │   ├── InitialMarginParameters.cs
│   │   │   │   ├── InitialMarginRequiredForOrderParameters.cs
│   │   │   │   ├── Interfaces
│   │   │   │   │   ├── IContinuousContractModel.cs
│   │   │   │   │   └── ISecurityDataFilter.cs
│   │   │   │   ├── IOrderEventProvider.cs
│   │   │   │   ├── IOrderProcessor.cs
│   │   │   │   ├── IOrderProvider.cs
│   │   │   │   ├── IPriceVariationModel.cs
│   │   │   │   ├── IRegisteredSecurityDataTypesProvider.cs
│   │   │   │   ├── ISecurityInitializer.cs
│   │   │   │   ├── ISecurityPortfolioModel.cs
│   │   │   │   ├── ISecurityProvider.cs
│   │   │   │   ├── ISecuritySeeder.cs
│   │   │   │   ├── ISettlementModel.cs
│   │   │   │   ├── LocalMarketHours.cs
│   │   │   │   ├── MaintenanceMargin.cs
│   │   │   │   ├── MaintenanceMarginParameters.cs
│   │   │   │   ├── MarginCallOrdersParameters.cs
│   │   │   │   ├── MarginInterestRateParameters.cs
│   │   │   │   ├── MarketHoursDatabase.cs
│   │   │   │   ├── MarketHoursSegment.cs
│   │   │   │   ├── MarketHoursState.cs
│   │   │   │   ├── NullBuyingPowerModel.cs
│   │   │   │   ├── Option
│   │   │   │   │   ├── ConstantQLDividendYieldEstimator.cs
│   │   │   │   │   ├── ConstantQLRiskFreeRateEstimator.cs
│   │   │   │   │   ├── ConstantQLUnderlyingVolatilityEstimator.cs
│   │   │   │   │   ├── CurrentPriceOptionPriceModel.cs
│   │   │   │   │   ├── DefaultOptionAssignmentModel.cs
│   │   │   │   │   ├── EmptyOptionChainProvider.cs
│   │   │   │   │   ├── FedRateQLRiskFreeRateEstimator.cs
│   │   │   │   │   ├── IOptionAssignmentModel.cs
│   │   │   │   │   ├── IOptionPriceModel.cs
│   │   │   │   │   ├── IOptionPriceModelProvider.cs
│   │   │   │   │   ├── IQLDividendYieldEstimator.cs
│   │   │   │   │   ├── IQLRiskFreeRateEstimator.cs
│   │   │   │   │   ├── IQLUnderlyingVolatilityEstimator.cs
│   │   │   │   │   ├── NullOptionAssignmentModel.cs
│   │   │   │   │   ├── Option.cs
│   │   │   │   │   ├── OptionAssignmentParameters.cs
│   │   │   │   │   ├── OptionAssignmentResult.cs
│   │   │   │   │   ├── OptionCache.cs
│   │   │   │   │   ├── OptionDataFilter.cs
│   │   │   │   │   ├── OptionExchange.cs
│   │   │   │   │   ├── OptionFilterUniverse.cs
│   │   │   │   │   ├── OptionHolding.cs
│   │   │   │   │   ├── OptionMarginModel.cs
│   │   │   │   │   ├── OptionPortfolioModel.cs
│   │   │   │   │   ├── OptionPriceModel.cs
│   │   │   │   │   ├── OptionPriceModelParameters.cs
│   │   │   │   │   ├── OptionPriceModelResult.cs
│   │   │   │   │   ├── OptionPriceModels.cs
│   │   │   │   │   ├── OptionPriceModels.QuantLib.cs
│   │   │   │   │   ├── OptionStrategies.cs
│   │   │   │   │   ├── OptionStrategy.cs
│   │   │   │   │   ├── OptionStrategyPositionGroupBuyingPowerModel.cs
│   │   │   │   │   ├── OptionSymbol.cs
│   │   │   │   │   ├── OptionSymbolProperties.cs
│   │   │   │   │   ├── QLOptionPriceModel.cs
│   │   │   │   │   ├── QLOptionPriceModelProvider.cs
│   │   │   │   │   └── StrategyMatcher
│   │   │   │   │       ├── AbsoluteRiskOptionPositionCollectionEnumerator.cs
│   │   │   │   │       ├── ConstantOptionStrategyLegPredicateReferenceValue.cs
│   │   │   │   │       ├── DefaultOptionPositionCollectionEnumerator.cs
│   │   │   │   │       ├── DescendingByLegCountOptionStrategyDefinitionEnumerator.cs
│   │   │   │   │       ├── FunctionalOptionPositionCollectionEnumerator.cs
│   │   │   │   │       ├── IdentityOptionStrategyDefinitionEnumerator.cs
│   │   │   │   │       ├── IOptionPositionCollectionEnumerator.cs
│   │   │   │   │       ├── IOptionStrategyDefinitionEnumerator.cs
│   │   │   │   │       ├── IOptionStrategyLegPredicateReferenceValue.cs
│   │   │   │   │       ├── IOptionStrategyMatchObjectiveFunction.cs
│   │   │   │   │       ├── OptionPosition.cs
│   │   │   │   │       ├── OptionPositionCollection.cs
│   │   │   │   │       ├── OptionStrategyDefinition.cs
│   │   │   │   │       ├── OptionStrategyDefinitionMatch.cs
│   │   │   │   │       ├── OptionStrategyDefinitions.cs
│   │   │   │   │       ├── OptionStrategyLegDefinition.cs
│   │   │   │   │       ├── OptionStrategyLegDefinitionMatch.cs
│   │   │   │   │       ├── OptionStrategyLegPredicate.cs
│   │   │   │   │       ├── OptionStrategyLegPredicateReferenceValue.cs
│   │   │   │   │       ├── OptionStrategyMatch.cs
│   │   │   │   │       ├── OptionStrategyMatcher.cs
│   │   │   │   │       ├── OptionStrategyMatcherOptions.cs
│   │   │   │   │       ├── PredicateTargetValue.cs
│   │   │   │   │       ├── UncoveredShortQuantityOptionStrategyMatchObjectiveFunction.cs
│   │   │   │   │       └── UnmatchedPositionCountOptionStrategyMatchObjectiveFunction.cs
│   │   │   │   ├── OptionInitialMargin.cs
│   │   │   │   ├── PatternDayTradingMarginModel.cs
│   │   │   │   ├── Positions
│   │   │   │   │   ├── CompositePositionGroupResolver.cs
│   │   │   │   │   ├── GetMaximumLotsForDeltaBuyingPowerParameters.cs
│   │   │   │   │   ├── GetMaximumLotsForTargetBuyingPowerParameters.cs
│   │   │   │   │   ├── GetMaximumLotsResult.cs
│   │   │   │   │   ├── HasSufficientPositionGroupBuyingPowerForOrderParameters.cs
│   │   │   │   │   ├── IPosition.cs
│   │   │   │   │   ├── IPositionGroup.cs
│   │   │   │   │   ├── IPositionGroupBuyingPowerModel.cs
│   │   │   │   │   ├── IPositionGroupResolver.cs
│   │   │   │   │   ├── NullSecurityPositionGroupModel.cs
│   │   │   │   │   ├── OptionStrategyPositionGroupResolver.cs
│   │   │   │   │   ├── PortfolioMarginChart.cs
│   │   │   │   │   ├── PortfolioState.cs
│   │   │   │   │   ├── Position.cs
│   │   │   │   │   ├── PositionCollection.cs
│   │   │   │   │   ├── PositionExtensions.cs
│   │   │   │   │   ├── PositionGroup.cs
│   │   │   │   │   ├── PositionGroupBuyingPower.cs
│   │   │   │   │   ├── PositionGroupBuyingPowerModel.cs
│   │   │   │   │   ├── PositionGroupBuyingPowerModelExtensions.cs
│   │   │   │   │   ├── PositionGroupBuyingPowerParameters.cs
│   │   │   │   │   ├── PositionGroupCollection.cs
│   │   │   │   │   ├── PositionGroupExtensions.cs
│   │   │   │   │   ├── PositionGroupInitialMarginForOrderParameters.cs
│   │   │   │   │   ├── PositionGroupInitialMarginParameters.cs
│   │   │   │   │   ├── PositionGroupKey.cs
│   │   │   │   │   ├── PositionGroupMaintenanceMarginParameters.cs
│   │   │   │   │   ├── readme.md
│   │   │   │   │   ├── ReservedBuyingPowerForPositionGroup.cs
│   │   │   │   │   ├── ReservedBuyingPowerForPositionGroupParameters.cs
│   │   │   │   │   ├── ReservedBuyingPowerImpact.cs
│   │   │   │   │   ├── ReservedBuyingPowerImpactParameters.cs
│   │   │   │   │   ├── SecurityPositionGroupBuyingPowerModel.cs
│   │   │   │   │   ├── SecurityPositionGroupModel.cs
│   │   │   │   │   └── SecurityPositionGroupResolver.cs
│   │   │   │   ├── ProjectedHoldings.cs
│   │   │   │   ├── RegisteredSecurityDataTypesProvider.cs
│   │   │   │   ├── ReservedBuyingPowerForPosition.cs
│   │   │   │   ├── ReservedBuyingPowerForPositionParameters.cs
│   │   │   │   ├── ScanSettlementModelParameters.cs
│   │   │   │   ├── Security.cs
│   │   │   │   ├── SecurityCache.cs
│   │   │   │   ├── SecurityCacheDataStoredEventArgs.cs
│   │   │   │   ├── SecurityCacheProvider.cs
│   │   │   │   ├── SecurityDatabaseKey.cs
│   │   │   │   ├── SecurityDataFilter.cs
│   │   │   │   ├── SecurityDataFilterPythonWrapper.cs
│   │   │   │   ├── SecurityDefinition.cs
│   │   │   │   ├── SecurityDefinitionSymbolResolver.cs
│   │   │   │   ├── SecurityEventArgs.cs
│   │   │   │   ├── SecurityExchange.cs
│   │   │   │   ├── SecurityExchangeHours.cs
│   │   │   │   ├── SecurityHolding.cs
│   │   │   │   ├── SecurityHoldingQuantityChangedEventArgs.cs
│   │   │   │   ├── SecurityManager.cs
│   │   │   │   ├── SecurityMarginModel.cs
│   │   │   │   ├── SecurityPortfolioManager.cs
│   │   │   │   ├── SecurityPortfolioModel.cs
│   │   │   │   ├── SecurityPriceVariationModel.cs
│   │   │   │   ├── SecurityService.cs
│   │   │   │   ├── SecurityTransactionManager.cs
│   │   │   │   ├── SymbolProperties.cs
│   │   │   │   ├── SymbolPropertiesDatabase.cs
│   │   │   │   ├── UniverseManager.cs
│   │   │   │   ├── UniverseManagerChanged.cs
│   │   │   │   ├── UnsettledCashAmount.cs
│   │   │   │   └── Volatility
│   │   │   │       ├── BaseVolatilityModel.cs
│   │   │   │       ├── IndicatorVolatilityModel.cs
│   │   │   │       ├── IVolatilityModel.cs
│   │   │   │       ├── RelativeStandardDeviationVolatilityModel.cs
│   │   │   │       ├── StandardDeviationOfReturnsVolatilityModel.cs
│   │   │   │       └── VolatilityModelExtensions.cs
│   │   │   ├── SecurityIdentifier.cs
│   │   │   ├── Series.cs
│   │   │   ├── SeriesSampler.cs
│   │   │   ├── Statistics
│   │   │   │   ├── AlgorithmPerformance.cs
│   │   │   │   ├── DrawdownMetrics.cs
│   │   │   │   ├── IStatisticsService.cs
│   │   │   │   ├── PerformanceMetrics.cs
│   │   │   │   ├── PortfolioStatistics.cs
│   │   │   │   ├── Statistics.cs
│   │   │   │   ├── StatisticsBuilder.cs
│   │   │   │   ├── StatisticsResults.cs
│   │   │   │   ├── Trade.cs
│   │   │   │   ├── TradeBuilder.cs
│   │   │   │   ├── TradeEnums.cs
│   │   │   │   └── TradeStatistics.cs
│   │   │   ├── Storage
│   │   │   │   └── ObjectStore.cs
│   │   │   ├── StringExtensions.cs
│   │   │   ├── StubsAvoidImplicitsAttribute.cs
│   │   │   ├── StubsIgnoreAttribute.cs
│   │   │   ├── Symbol.cs
│   │   │   ├── SymbolCache.cs
│   │   │   ├── SymbolCapacity.cs
│   │   │   ├── SymbolJsonConverter.cs
│   │   │   ├── SymbolRepresentation.cs
│   │   │   ├── SymbolValueJsonConverter.cs
│   │   │   ├── Time.cs
│   │   │   ├── TimeKeeper.cs
│   │   │   ├── TimeUpdatedEventArgs.cs
│   │   │   ├── TimeZoneOffsetProvider.cs
│   │   │   ├── TimeZones.cs
│   │   │   ├── TradingCalendar.cs
│   │   │   ├── TradingDay.cs
│   │   │   └── Util
│   │   │       ├── BaseExtendedDictionary.cs
│   │   │       ├── BusyBlockingCollection.cs
│   │   │       ├── BusyCollection.cs
│   │   │       ├── CandlestickJsonConverter.cs
│   │   │       ├── CashAmountUtil.cs
│   │   │       ├── CastingEnumerable.cs
│   │   │       ├── ChartPointJsonConverter.cs
│   │   │       ├── CircularQueue.cs
│   │   │       ├── ColorJsonConverter.cs
│   │   │       ├── ComparisonOperator.cs
│   │   │       ├── ComparisonOperatorTypes.cs
│   │   │       ├── Composer.cs
│   │   │       ├── ConcurrentSet.cs
│   │   │       ├── CurrencyPairUtil.cs
│   │   │       ├── DateTimeJsonConverter.cs
│   │   │       ├── DecimalJsonConverter.cs
│   │   │       ├── DisposableExtensions.cs
│   │   │       ├── DoubleUnixSecondsDateTimeJsonConverter.cs
│   │   │       ├── EnumeratorExtensions.cs
│   │   │       ├── ExpressionBuilder.cs
│   │   │       ├── FixedSizeHashQueue.cs
│   │   │       ├── FixedSizeQueue.cs
│   │   │       ├── FuncTextWriter.cs
│   │   │       ├── JsonRoundingConverter.cs
│   │   │       ├── KeyStringSynchronizer.cs
│   │   │       ├── LeanData.cs
│   │   │       ├── LeanDataPathComponents.cs
│   │   │       ├── LinqExtensions.cs
│   │   │       ├── ListComparer.cs
│   │   │       ├── MarketHoursDatabaseJsonConverter.cs
│   │   │       ├── MemoizingEnumerable.cs
│   │   │       ├── NullStringValueConverter.cs
│   │   │       ├── ObjectActivator.cs
│   │   │       ├── OptionPayoff.cs
│   │   │       ├── PerformanceTimer.cs
│   │   │       ├── PerformanceTrackingTool.cs
│   │   │       ├── PythonUtil.cs
│   │   │       ├── RateGate.cs
│   │   │       ├── RateLimit
│   │   │       │   ├── BusyWaitSleepStrategy.cs
│   │   │       │   ├── FixedIntervalRefillStrategy.cs
│   │   │       │   ├── IRefillStrategy.cs
│   │   │       │   ├── ISleepStrategy.cs
│   │   │       │   ├── ITokenBucket.cs
│   │   │       │   ├── LeakyBucket.cs
│   │   │       │   ├── ThreadSleepStrategy.cs
│   │   │       │   └── TokenBucket.cs
│   │   │       ├── ReaderWriterLockSlimExtensions.cs
│   │   │       ├── ReadOnlyExtendedDictionary.cs
│   │   │       ├── Ref.cs
│   │   │       ├── ReferenceWrapper.cs
│   │   │       ├── SecurityExtensions.cs
│   │   │       ├── SecurityIdentifierJsonConverter.cs
│   │   │       ├── SeriesJsonConverter.cs
│   │   │       ├── SingleValueListConverter.cs
│   │   │       ├── StreamReaderEnumerable.cs
│   │   │       ├── StreamReaderExtensions.cs
│   │   │       ├── StringDecimalJsonConverter.cs
│   │   │       ├── TypeChangeJsonConverter.cs
│   │   │       ├── Validate.cs
│   │   │       ├── WorkerThread.cs
│   │   │       └── XElementExtensions.cs
│   │   ├── compare_benchmarks.py
│   │   ├── Compression
│   │   │   ├── Compression.cs
│   │   │   ├── Properties
│   │   │   │   └── AssemblyInfo.cs
│   │   │   ├── QuantConnect.Compression.csproj
│   │   │   └── ZipStreamWriter.cs
│   │   ├── Configuration
│   │   │   ├── ApplicationParser.cs
│   │   │   ├── CommandLineOption.cs
│   │   │   ├── Config.cs
│   │   │   ├── LeanArgumentParser.cs
│   │   │   ├── OptimizerArgumentParser.cs
│   │   │   ├── Properties
│   │   │   │   └── AssemblyInfo.cs
│   │   │   ├── QuantConnect.Configuration.csproj
│   │   │   ├── ReportArgumentParser.cs
│   │   │   └── ToolboxArgumentParser.cs
│   │   ├── CONTRIBUTING.md
│   │   ├── Data
│   │   │   ├── alternative
│   │   │   │   ├── alphastreams
│   │   │   │   │   └── portfoliostate
│   │   │   │   │       ├── 623b06b231eb1cc1aa3643a46
│   │   │   │   │       │   ├── 20180403.json
│   │   │   │   │       │   └── 20180404.json
│   │   │   │   │       ├── 94d820a93fff127fa46c15231d
│   │   │   │   │       │   ├── 20180403.json
│   │   │   │   │       │   └── 20180404.json
│   │   │   │   │       └── 9fc8ef73792331b11dbd5429a
│   │   │   │   │           ├── 20180403.json
│   │   │   │   │           └── 20180404.json
│   │   │   │   ├── estimize
│   │   │   │   │   ├── consensus
│   │   │   │   │   │   └── aapl
│   │   │   │   │   ├── estimate
│   │   │   │   │   └── release
│   │   │   │   ├── interest-rate
│   │   │   │   │   └── usa
│   │   │   │   │       └── interest-rate.csv
│   │   │   │   ├── sec
│   │   │   │   │   └── aapl
│   │   │   │   └── trading-economics
│   │   │   │       ├── calendar
│   │   │   │       ├── earnings
│   │   │   │       └── indicator
│   │   │   ├── cfd
│   │   │   │   ├── oanda
│   │   │   │   │   ├── daily
│   │   │   │   │   │   └── xauusd.zip
│   │   │   │   │   ├── hour
│   │   │   │   │   │   └── xauusd.zip
│   │   │   │   │   ├── minute
│   │   │   │   │   │   ├── de30eur
│   │   │   │   │   │   │   ├── 20190220_quote.zip
│   │   │   │   │   │   │   ├── 20190221_quote.zip
│   │   │   │   │   │   │   └── 20190222_quote.zip
│   │   │   │   │   │   └── xauusd
│   │   │   │   │   │       ├── 20140501_quote.zip
│   │   │   │   │   │       ├── 20140502_quote.zip
│   │   │   │   │   │       ├── 20140504_quote.zip
│   │   │   │   │   │       ├── 20140505_quote.zip
│   │   │   │   │   │       ├── 20140506_quote.zip
│   │   │   │   │   │       ├── 20140507_quote.zip
│   │   │   │   │   │       ├── 20140508_quote.zip
│   │   │   │   │   │       ├── 20140509_quote.zip
│   │   │   │   │   │       ├── 20140511_quote.zip
│   │   │   │   │   │       ├── 20140512_quote.zip
│   │   │   │   │   │       ├── 20140513_quote.zip
│   │   │   │   │   │       ├── 20140514_quote.zip
│   │   │   │   │   │       └── 20140515_quote.zip
│   │   │   │   │   ├── second
│   │   │   │   │   │   └── xauusd
│   │   │   │   │   │       ├── 20140501_quote.zip
│   │   │   │   │   │       ├── 20140502_quote.zip
│   │   │   │   │   │       ├── 20140504_quote.zip
│   │   │   │   │   │       ├── 20140505_quote.zip
│   │   │   │   │   │       ├── 20140506_quote.zip
│   │   │   │   │   │       ├── 20140507_quote.zip
│   │   │   │   │   │       ├── 20140508_quote.zip
│   │   │   │   │   │       ├── 20140509_quote.zip
│   │   │   │   │   │       ├── 20140511_quote.zip
│   │   │   │   │   │       ├── 20140512_quote.zip
│   │   │   │   │   │       ├── 20140513_quote.zip
│   │   │   │   │   │       ├── 20140514_quote.zip
│   │   │   │   │   │       └── 20140515_quote.zip
│   │   │   │   │   └── tick
│   │   │   │   │       └── xauusd
│   │   │   │   │           ├── 20140501_quote.zip
│   │   │   │   │           ├── 20140502_quote.zip
│   │   │   │   │           ├── 20140504_quote.zip
│   │   │   │   │           ├── 20140505_quote.zip
│   │   │   │   │           ├── 20140506_quote.zip
│   │   │   │   │           ├── 20140507_quote.zip
│   │   │   │   │           ├── 20140508_quote.zip
│   │   │   │   │           ├── 20140509_quote.zip
│   │   │   │   │           ├── 20140511_quote.zip
│   │   │   │   │           ├── 20140512_quote.zip
│   │   │   │   │           ├── 20140513_quote.zip
│   │   │   │   │           ├── 20140514_quote.zip
│   │   │   │   │           └── 20140515_quote.zip
│   │   │   │   └── readme.md
│   │   │   ├── crypto
│   │   │   │   ├── binance
│   │   │   │   │   ├── hour
│   │   │   │   │   │   └── btcusdt_trade.zip
│   │   │   │   │   └── minute
│   │   │   │   │       └── btcbusd
│   │   │   │   │           └── 20221213_trade.zip
│   │   │   │   ├── bitfinex
│   │   │   │   │   └── hour
│   │   │   │   │       └── btcusd_trade.zip
│   │   │   │   ├── bybit
│   │   │   │   │   └── minute
│   │   │   │   │       └── btcusdt
│   │   │   │   │           ├── 20221213_quote.zip
│   │   │   │   │           └── 20221213_trade.zip
│   │   │   │   ├── coinbase
│   │   │   │   │   ├── daily
│   │   │   │   │   │   ├── btcusd_quote.zip
│   │   │   │   │   │   └── btcusd_trade.zip
│   │   │   │   │   ├── minute
│   │   │   │   │   │   ├── btceur
│   │   │   │   │   │   │   ├── 20180404_quote.zip
│   │   │   │   │   │   │   ├── 20180404_trade.zip
│   │   │   │   │   │   │   ├── 20180405_quote.zip
│   │   │   │   │   │   │   ├── 20180405_trade.zip
│   │   │   │   │   │   │   ├── 20180406_quote.zip
│   │   │   │   │   │   │   └── 20180406_trade.zip
│   │   │   │   │   │   ├── btcusd
│   │   │   │   │   │   │   ├── 20161007_trade.zip
│   │   │   │   │   │   │   ├── 20161008_trade.zip
│   │   │   │   │   │   │   ├── 20161009_trade.zip
│   │   │   │   │   │   │   ├── 20170903_quote.zip
│   │   │   │   │   │   │   ├── 20170903_trade.zip
│   │   │   │   │   │   │   ├── 20170904_quote.zip
│   │   │   │   │   │   │   ├── 20170904_trade.zip
│   │   │   │   │   │   │   ├── 20171217_quote.zip
│   │   │   │   │   │   │   ├── 20171217_trade.zip
│   │   │   │   │   │   │   ├── 20180404_quote.zip
│   │   │   │   │   │   │   ├── 20180404_trade.zip
│   │   │   │   │   │   │   ├── 20180405_quote.zip
│   │   │   │   │   │   │   ├── 20180405_trade.zip
│   │   │   │   │   │   │   └── 20180406_trade.zip
│   │   │   │   │   │   ├── ethusd
│   │   │   │   │   │   │   ├── 20170903_quote.zip
│   │   │   │   │   │   │   ├── 20170903_trade.zip
│   │   │   │   │   │   │   ├── 20170904_quote.zip
│   │   │   │   │   │   │   ├── 20170904_trade.zip
│   │   │   │   │   │   │   ├── 20180404_quote.zip
│   │   │   │   │   │   │   ├── 20180404_trade.zip
│   │   │   │   │   │   │   ├── 20180405_quote.zip
│   │   │   │   │   │   │   └── 20180405_trade.zip
│   │   │   │   │   │   └── ltcusd
│   │   │   │   │   │       ├── 20180404_quote.zip
│   │   │   │   │   │       ├── 20180404_trade.zip
│   │   │   │   │   │       ├── 20180405_quote.zip
│   │   │   │   │   │       ├── 20180405_trade.zip
│   │   │   │   │   │       ├── 20180406_quote.zip
│   │   │   │   │   │       └── 20180406_trade.zip
│   │   │   │   │   └── second
│   │   │   │   │       └── btcusd
│   │   │   │   │           ├── 20161007_trade.zip
│   │   │   │   │           ├── 20161008_trade.zip
│   │   │   │   │           └── 20161009_trade.zip
│   │   │   │   └── readme.md
│   │   │   ├── cryptofuture
│   │   │   │   ├── binance
│   │   │   │   │   ├── daily
│   │   │   │   │   │   ├── adausdt_quote.zip
│   │   │   │   │   │   └── adausdt_trade.zip
│   │   │   │   │   ├── hour
│   │   │   │   │   │   ├── adausdt_quote.zip
│   │   │   │   │   │   └── adausdt_trade.zip
│   │   │   │   │   ├── margin_interest
│   │   │   │   │   │   ├── adausdt.csv
│   │   │   │   │   │   └── btcusd.csv
│   │   │   │   │   └── minute
│   │   │   │   │       ├── adausdt
│   │   │   │   │       │   ├── 20221213_quote.zip
│   │   │   │   │       │   └── 20221213_trade.zip
│   │   │   │   │       └── btcusd
│   │   │   │   │           ├── 20221213_quote.zip
│   │   │   │   │           └── 20221213_trade.zip
│   │   │   │   ├── bybit
│   │   │   │   │   ├── margin_interest
│   │   │   │   │   │   ├── btcusd.csv
│   │   │   │   │   │   └── btcusdt.csv
│   │   │   │   │   └── minute
│   │   │   │   │       ├── btcusd
│   │   │   │   │       │   ├── 20221213_quote.zip
│   │   │   │   │       │   └── 20221213_trade.zip
│   │   │   │   │       └── btcusdt
│   │   │   │   │           ├── 20221213_quote.zip
│   │   │   │   │           └── 20221213_trade.zip
│   │   │   │   └── dydx
│   │   │   │       └── minute
│   │   │   │           └── btcusd
│   │   │   │               ├── 20260101_quote.zip
│   │   │   │               └── 20260101_trade.zip
│   │   │   ├── equity
│   │   │   │   ├── india
│   │   │   │   │   ├── daily
│   │   │   │   │   │   └── cccl.zip
│   │   │   │   │   ├── factor_files
│   │   │   │   │   │   └── cccl.csv
│   │   │   │   │   ├── map_files
│   │   │   │   │   │   └── 3mindia.csv
│   │   │   │   │   └── minute
│   │   │   │   │       ├── juniorbees
│   │   │   │   │       │   ├── 20190101_trade.zip
│   │   │   │   │       │   ├── 20190102_trade.zip
│   │   │   │   │       │   ├── 20190103_trade.zip
│   │   │   │   │       │   └── 20190104_trade.zip
│   │   │   │   │       └── yesbank
│   │   │   │   │           ├── 20190709_trade.zip
│   │   │   │   │           ├── 20190710_trade.zip
│   │   │   │   │           └── 20190711_trade.zip
│   │   │   │   ├── readme.md
│   │   │   │   └── usa
│   │   │   │       ├── daily
│   │   │   │       │   ├── aaa.zip
│   │   │   │       │   ├── aapl.zip
│   │   │   │       │   ├── aig.zip
│   │   │   │       │   ├── bac.zip
│   │   │   │       │   ├── bno.zip
│   │   │   │       │   ├── eem.zip
│   │   │   │       │   ├── fb.zip
│   │   │   │       │   ├── foxa.zip
│   │   │   │       │   ├── gooav.zip
│   │   │   │       │   ├── goocv.zip
│   │   │   │       │   ├── goog.zip
│   │   │   │       │   ├── googl.zip
│   │   │   │       │   ├── ibm.zip
│   │   │   │       │   ├── iwm.zip
│   │   │   │       │   ├── nwsa.zip
│   │   │   │       │   ├── qqq.zip
│   │   │   │       │   ├── spy.zip
│   │   │   │       │   ├── uso.zip
│   │   │   │       │   ├── uw.zip
│   │   │   │       │   ├── wm.zip
│   │   │   │       │   └── wmi.zip
│   │   │   │       ├── factor_files
│   │   │   │       │   ├── aaa.1.csv
│   │   │   │       │   ├── aapl.csv
│   │   │   │       │   ├── aig.csv
│   │   │   │       │   ├── bac.csv
│   │   │   │       │   ├── bno.csv
│   │   │   │       │   ├── eem.csv
│   │   │   │       │   ├── fb.csv
│   │   │   │       │   ├── gbsn.csv
│   │   │   │       │   ├── goog.csv
│   │   │   │       │   ├── googl.csv
│   │   │   │       │   ├── ibm.csv
│   │   │   │       │   ├── iwm.csv
│   │   │   │       │   ├── nwsa.csv
│   │   │   │       │   ├── qqq.csv
│   │   │   │       │   ├── spy.csv
│   │   │   │       │   ├── tap.a.csv
│   │   │   │       │   ├── tfcfa.csv
│   │   │   │       │   ├── twx.1.csv
│   │   │   │       │   ├── twx.csv
│   │   │   │       │   ├── uso.csv
│   │   │   │       │   ├── vxx.1.csv
│   │   │   │       │   └── wm.csv
│   │   │   │       ├── fundamental
│   │   │   │       │   └── coarse
│   │   │   │       │       ├── 20140324.csv
│   │   │   │       │       ├── 20140325.csv
│   │   │   │       │       ├── 20140326.csv
│   │   │   │       │       ├── 20140327.csv
│   │   │   │       │       ├── 20140328.csv
│   │   │   │       │       ├── 20140331.csv
│   │   │   │       │       ├── 20140401.csv
│   │   │   │       │       ├── 20140402.csv
│   │   │   │       │       ├── 20140403.csv
│   │   │   │       │       ├── 20140404.csv
│   │   │   │       │       └── 20140407.csv
│   │   │   │       ├── hour
│   │   │   │       │   ├── aapl.zip
│   │   │   │       │   ├── aig.zip
│   │   │   │       │   ├── bac.zip
│   │   │   │       │   ├── gdvd.zip
│   │   │   │       │   ├── ibm.zip
│   │   │   │       │   ├── spwr.zip
│   │   │   │       │   ├── spwra.zip
│   │   │   │       │   ├── spy.zip
│   │   │   │       │   ├── tapa.zip
│   │   │   │       │   └── vxx.zip
│   │   │   │       ├── map_files
│   │   │   │       │   ├── aaa.1.csv
│   │   │   │       │   ├── aaa.csv
│   │   │   │       │   ├── aapl.csv
│   │   │   │       │   ├── aig.csv
│   │   │   │       │   ├── bac.csv
│   │   │   │       │   ├── bno.csv
│   │   │   │       │   ├── eem.csv
│   │   │   │       │   ├── fb.1.csv
│   │   │   │       │   ├── fb.csv
│   │   │   │       │   ├── gdvd.csv
│   │   │   │       │   ├── gooav.csv
│   │   │   │       │   ├── goog.csv
│   │   │   │       │   ├── googl.csv
│   │   │   │       │   ├── ibm.csv
│   │   │   │       │   ├── iwm.csv
│   │   │   │       │   ├── qqq.csv
│   │   │   │       │   ├── spwr.csv
│   │   │   │       │   ├── spy.csv
│   │   │   │       │   ├── tap.a.csv
│   │   │   │       │   ├── tfcfa.csv
│   │   │   │       │   ├── twx.1.csv
│   │   │   │       │   ├── twx.csv
│   │   │   │       │   ├── uso.csv
│   │   │   │       │   ├── vxx.1.csv
│   │   │   │       │   ├── vxx.csv
│   │   │   │       │   └── wm.csv
│   │   │   │       ├── minute
│   │   │   │       │   ├── aapl
│   │   │   │       │   │   ├── 20140605_quote.zip
│   │   │   │       │   │   ├── 20140605_trade.zip
│   │   │   │       │   │   ├── 20140606_quote.zip
│   │   │   │       │   │   ├── 20140606_trade.zip
│   │   │   │       │   │   ├── 20140609_quote.zip
│   │   │   │       │   │   └── 20140609_trade.zip
│   │   │   │       │   ├── aig
│   │   │   │       │   │   ├── 20131004_quote.zip
│   │   │   │       │   │   ├── 20131004_trade.zip
│   │   │   │       │   │   ├── 20131007_quote.zip
│   │   │   │       │   │   ├── 20131007_trade.zip
│   │   │   │       │   │   ├── 20131008_quote.zip
│   │   │   │       │   │   ├── 20131008_trade.zip
│   │   │   │       │   │   ├── 20131009_quote.zip
│   │   │   │       │   │   ├── 20131009_trade.zip
│   │   │   │       │   │   ├── 20131010_quote.zip
│   │   │   │       │   │   ├── 20131010_trade.zip
│   │   │   │       │   │   ├── 20131011_quote.zip
│   │   │   │       │   │   └── 20131011_trade.zip
│   │   │   │       │   ├── bac
│   │   │   │       │   │   ├── 20131004_quote.zip
│   │   │   │       │   │   ├── 20131004_trade.zip
│   │   │   │       │   │   ├── 20131007_quote.zip
│   │   │   │       │   │   ├── 20131007_trade.zip
│   │   │   │       │   │   ├── 20131008_quote.zip
│   │   │   │       │   │   ├── 20131008_trade.zip
│   │   │   │       │   │   ├── 20131009_quote.zip
│   │   │   │       │   │   ├── 20131009_trade.zip
│   │   │   │       │   │   ├── 20131010_quote.zip
│   │   │   │       │   │   ├── 20131010_trade.zip
│   │   │   │       │   │   ├── 20131011_quote.zip
│   │   │   │       │   │   └── 20131011_trade.zip
│   │   │   │       │   ├── foxa
│   │   │   │       │   │   ├── 20130701_quote.zip
│   │   │   │       │   │   ├── 20130701_trade.zip
│   │   │   │       │   │   ├── 20130702_quote.zip
│   │   │   │       │   │   └── 20130702_trade.zip
│   │   │   │       │   ├── goog
│   │   │   │       │   │   ├── 20151223_trade.zip
│   │   │   │       │   │   ├── 20151224_quote.zip
│   │   │   │       │   │   ├── 20151224_trade.zip
│   │   │   │       │   │   ├── 20151228_quote.zip
│   │   │   │       │   │   └── 20151228_trade.zip
│   │   │   │       │   ├── ibm
│   │   │   │       │   │   ├── 20131004_quote.zip
│   │   │   │       │   │   ├── 20131004_trade.zip
│   │   │   │       │   │   ├── 20131007_quote.zip
│   │   │   │       │   │   ├── 20131007_trade.zip
│   │   │   │       │   │   ├── 20131008_quote.zip
│   │   │   │       │   │   ├── 20131008_trade.zip
│   │   │   │       │   │   ├── 20131009_quote.zip
│   │   │   │       │   │   ├── 20131009_trade.zip
│   │   │   │       │   │   ├── 20131010_quote.zip
│   │   │   │       │   │   ├── 20131010_trade.zip
│   │   │   │       │   │   ├── 20131011_quote.zip
│   │   │   │       │   │   └── 20131011_trade.zip
│   │   │   │       │   ├── nwsa
│   │   │   │       │   │   ├── 20130627_quote.zip
│   │   │   │       │   │   ├── 20130627_trade.zip
│   │   │   │       │   │   ├── 20130628_quote.zip
│   │   │   │       │   │   └── 20130628_trade.zip
│   │   │   │       │   ├── shy
│   │   │   │       │   │   ├── 20080307_quote.zip
│   │   │   │       │   │   ├── 20080307_trade.zip
│   │   │   │       │   │   ├── 20080310_quote.zip
│   │   │   │       │   │   └── 20080310_trade.zip
│   │   │   │       │   ├── spy
│   │   │   │       │   │   ├── 20131004_quote.zip
│   │   │   │       │   │   ├── 20131004_trade.zip
│   │   │   │       │   │   ├── 20131007_quote.zip
│   │   │   │       │   │   ├── 20131007_trade.zip
│   │   │   │       │   │   ├── 20131008_quote.zip
│   │   │   │       │   │   ├── 20131008_trade.zip
│   │   │   │       │   │   ├── 20131009_quote.zip
│   │   │   │       │   │   ├── 20131009_trade.zip
│   │   │   │       │   │   ├── 20131010_quote.zip
│   │   │   │       │   │   ├── 20131010_trade.zip
│   │   │   │       │   │   ├── 20131011_quote.zip
│   │   │   │       │   │   ├── 20131011_trade.zip
│   │   │   │       │   │   ├── 20230803_quote.zip
│   │   │   │       │   │   └── 20230803_trade.zip
│   │   │   │       │   └── twx
│   │   │   │       │       ├── 20140605_quote.zip
│   │   │   │       │       ├── 20140605_trade.zip
│   │   │   │       │       ├── 20140606_quote.zip
│   │   │   │       │       ├── 20140606_trade.zip
│   │   │   │       │       ├── 20140609_quote.zip
│   │   │   │       │       ├── 20140609_trade.zip
│   │   │   │       │       └── 20140623_trade.zip
│   │   │   │       ├── readme.md
│   │   │   │       ├── second
│   │   │   │       │   ├── aig
│   │   │   │       │   │   ├── 20131004_trade.zip
│   │   │   │       │   │   ├── 20131007_quote.zip
│   │   │   │       │   │   ├── 20131007_trade.zip
│   │   │   │       │   │   ├── 20131008_quote.zip
│   │   │   │       │   │   ├── 20131008_trade.zip
│   │   │   │       │   │   ├── 20131009_quote.zip
│   │   │   │       │   │   ├── 20131009_trade.zip
│   │   │   │       │   │   ├── 20131010_quote.zip
│   │   │   │       │   │   ├── 20131010_trade.zip
│   │   │   │       │   │   ├── 20131011_quote.zip
│   │   │   │       │   │   └── 20131011_trade.zip
│   │   │   │       │   ├── bac
│   │   │   │       │   │   ├── 20131007_quote.zip
│   │   │   │       │   │   ├── 20131007_trade.zip
│   │   │   │       │   │   ├── 20131008_quote.zip
│   │   │   │       │   │   ├── 20131008_trade.zip
│   │   │   │       │   │   ├── 20131009_quote.zip
│   │   │   │       │   │   ├── 20131009_trade.zip
│   │   │   │       │   │   ├── 20131010_quote.zip
│   │   │   │       │   │   ├── 20131010_trade.zip
│   │   │   │       │   │   ├── 20131011_quote.zip
│   │   │   │       │   │   └── 20131011_trade.zip
│   │   │   │       │   ├── ibm
│   │   │   │       │   │   ├── 20131007_quote.zip
│   │   │   │       │   │   ├── 20131007_trade.zip
│   │   │   │       │   │   ├── 20131008_quote.zip
│   │   │   │       │   │   ├── 20131008_trade.zip
│   │   │   │       │   │   ├── 20131009_quote.zip
│   │   │   │       │   │   ├── 20131009_trade.zip
│   │   │   │       │   │   ├── 20131010_quote.zip
│   │   │   │       │   │   ├── 20131010_trade.zip
│   │   │   │       │   │   ├── 20131011_quote.zip
│   │   │   │       │   │   └── 20131011_trade.zip
│   │   │   │       │   └── spy
│   │   │   │       │       ├── 20131007_quote.zip
│   │   │   │       │       ├── 20131007_trade.zip
│   │   │   │       │       ├── 20131008_quote.zip
│   │   │   │       │       ├── 20131008_trade.zip
│   │   │   │       │       ├── 20131009_quote.zip
│   │   │   │       │       ├── 20131009_trade.zip
│   │   │   │       │       ├── 20131010_quote.zip
│   │   │   │       │       ├── 20131010_trade.zip
│   │   │   │       │       ├── 20131011_quote.zip
│   │   │   │       │       ├── 20131011_trade.zip
│   │   │   │       │       └── 20140605_trade.zip
│   │   │   │       ├── shortable
│   │   │   │       │   └── testbrokerage
│   │   │   │       │       ├── dates
│   │   │   │       │       │   ├── 20140325.csv
│   │   │   │       │       │   ├── 20140326.csv
│   │   │   │       │       │   ├── 20140327.csv
│   │   │   │       │       │   └── 20140328.csv
│   │   │   │       │       └── symbols
│   │   │   │       │           ├── aapl.csv
│   │   │   │       │           ├── aig.csv
│   │   │   │       │           ├── bac.csv
│   │   │   │       │           ├── goocv.csv
│   │   │   │       │           ├── qqq.csv
│   │   │   │       │           └── spy.csv
│   │   │   │       ├── tick
│   │   │   │       │   ├── aig
│   │   │   │       │   │   ├── 20131007_quote.zip
│   │   │   │       │   │   ├── 20131007_trade.zip
│   │   │   │       │   │   ├── 20131008_quote.zip
│   │   │   │       │   │   ├── 20131008_trade.zip
│   │   │   │       │   │   ├── 20131009_quote.zip
│   │   │   │       │   │   ├── 20131009_trade.zip
│   │   │   │       │   │   ├── 20131010_quote.zip
│   │   │   │       │   │   ├── 20131010_trade.zip
│   │   │   │       │   │   ├── 20131011_quote.zip
│   │   │   │       │   │   └── 20131011_trade.zip
│   │   │   │       │   ├── bac
│   │   │   │       │   │   ├── 20131007_quote.zip
│   │   │   │       │   │   ├── 20131007_trade.zip
│   │   │   │       │   │   ├── 20131008_quote.zip
│   │   │   │       │   │   ├── 20131008_trade.zip
│   │   │   │       │   │   ├── 20131009_quote.zip
│   │   │   │       │   │   ├── 20131009_trade.zip
│   │   │   │       │   │   ├── 20131010_quote.zip
│   │   │   │       │   │   ├── 20131010_trade.zip
│   │   │   │       │   │   ├── 20131011_quote.zip
│   │   │   │       │   │   └── 20131011_trade.zip
│   │   │   │       │   ├── ibm
│   │   │   │       │   │   ├── 20131007_quote.zip
│   │   │   │       │   │   ├── 20131007_trade.zip
│   │   │   │       │   │   ├── 20131008_quote.zip
│   │   │   │       │   │   ├── 20131008_trade.zip
│   │   │   │       │   │   ├── 20131009_quote.zip
│   │   │   │       │   │   ├── 20131009_trade.zip
│   │   │   │       │   │   ├── 20131010_quote.zip
│   │   │   │       │   │   ├── 20131010_trade.zip
│   │   │   │       │   │   ├── 20131011_quote.zip
│   │   │   │       │   │   └── 20131011_trade.zip
│   │   │   │       │   └── spy
│   │   │   │       │       ├── 20131007_quote.zip
│   │   │   │       │       ├── 20131007_trade.zip
│   │   │   │       │       ├── 20131008_quote.zip
│   │   │   │       │       ├── 20131008_trade.zip
│   │   │   │       │       ├── 20131009_quote.zip
│   │   │   │       │       ├── 20131009_trade.zip
│   │   │   │       │       ├── 20131010_quote.zip
│   │   │   │       │       ├── 20131010_trade.zip
│   │   │   │       │       ├── 20131011_quote.zip
│   │   │   │       │       └── 20131011_trade.zip
│   │   │   │       └── universes
│   │   │   │           ├── daily
│   │   │   │           │   └── qctest
│   │   │   │           │       ├── 20131007.csv
│   │   │   │           │       ├── 20131008.csv
│   │   │   │           │       ├── 20131009.csv
│   │   │   │           │       ├── 20131010.csv
│   │   │   │           │       └── 20141007.csv
│   │   │   │           └── etf
│   │   │   │               ├── gdvd
│   │   │   │               │   └── 20201210.csv
│   │   │   │               ├── qqq
│   │   │   │               │   └── 20110330.csv
│   │   │   │               ├── qqqq
│   │   │   │               │   └── 20110228.csv
│   │   │   │               └── spy
│   │   │   │                   ├── 20201130.csv
│   │   │   │                   └── 20201201.csv
│   │   │   ├── forex
│   │   │   │   ├── fxcm
│   │   │   │   │   ├── daily
│   │   │   │   │   │   ├── eurgbp.zip
│   │   │   │   │   │   ├── eurusd.zip
│   │   │   │   │   │   ├── gbpusd.zip
│   │   │   │   │   │   └── nzdusd.zip
│   │   │   │   │   ├── hour
│   │   │   │   │   │   ├── eurusd.zip
│   │   │   │   │   │   └── nzdusd.zip
│   │   │   │   │   ├── minute
│   │   │   │   │   │   ├── eurusd
│   │   │   │   │   │   │   ├── 20110307_quote.zip
│   │   │   │   │   │   │   ├── 20111031_quote.zip
│   │   │   │   │   │   │   ├── 20140501_quote.zip
│   │   │   │   │   │   │   ├── 20140502_quote.zip
│   │   │   │   │   │   │   ├── 20140504_quote.zip
│   │   │   │   │   │   │   ├── 20140505_quote.zip
│   │   │   │   │   │   │   ├── 20140506_quote.zip
│   │   │   │   │   │   │   ├── 20140507_quote.zip
│   │   │   │   │   │   │   ├── 20140508_quote.zip
│   │   │   │   │   │   │   ├── 20140509_quote.zip
│   │   │   │   │   │   │   ├── 20140511_quote.zip
│   │   │   │   │   │   │   ├── 20140512_quote.zip
│   │   │   │   │   │   │   ├── 20140513_quote.zip
│   │   │   │   │   │   │   ├── 20140514_quote.zip
│   │   │   │   │   │   │   ├── 20140515_quote.zip
│   │   │   │   │   │   │   ├── 20180403_quote.zip
│   │   │   │   │   │   │   └── 20180404_quote.zip
│   │   │   │   │   │   └── nzdusd
│   │   │   │   │   │       ├── 20140501_quote.zip
│   │   │   │   │   │       ├── 20140502_quote.zip
│   │   │   │   │   │       ├── 20140504_quote.zip
│   │   │   │   │   │       ├── 20140505_quote.zip
│   │   │   │   │   │       ├── 20140506_quote.zip
│   │   │   │   │   │       ├── 20140507_quote.zip
│   │   │   │   │   │       ├── 20140508_quote.zip
│   │   │   │   │   │       ├── 20140509_quote.zip
│   │   │   │   │   │       ├── 20140511_quote.zip
│   │   │   │   │   │       ├── 20140512_quote.zip
│   │   │   │   │   │       ├── 20140513_quote.zip
│   │   │   │   │   │       ├── 20140514_quote.zip
│   │   │   │   │   │       └── 20140515_quote.zip
│   │   │   │   │   ├── second
│   │   │   │   │   │   ├── eurusd
│   │   │   │   │   │   │   ├── 20140501_quote.zip
│   │   │   │   │   │   │   ├── 20140502_quote.zip
│   │   │   │   │   │   │   ├── 20140504_quote.zip
│   │   │   │   │   │   │   ├── 20140505_quote.zip
│   │   │   │   │   │   │   ├── 20140506_quote.zip
│   │   │   │   │   │   │   ├── 20140507_quote.zip
│   │   │   │   │   │   │   ├── 20140508_quote.zip
│   │   │   │   │   │   │   ├── 20140509_quote.zip
│   │   │   │   │   │   │   ├── 20140511_quote.zip
│   │   │   │   │   │   │   ├── 20140512_quote.zip
│   │   │   │   │   │   │   ├── 20140513_quote.zip
│   │   │   │   │   │   │   ├── 20140514_quote.zip
│   │   │   │   │   │   │   └── 20140515_quote.zip
│   │   │   │   │   │   └── nzdusd
│   │   │   │   │   │       ├── 20140501_quote.zip
│   │   │   │   │   │       ├── 20140502_quote.zip
│   │   │   │   │   │       ├── 20140504_quote.zip
│   │   │   │   │   │       ├── 20140505_quote.zip
│   │   │   │   │   │       ├── 20140506_quote.zip
│   │   │   │   │   │       ├── 20140507_quote.zip
│   │   │   │   │   │       ├── 20140508_quote.zip
│   │   │   │   │   │       ├── 20140509_quote.zip
│   │   │   │   │   │       ├── 20140511_quote.zip
│   │   │   │   │   │       ├── 20140512_quote.zip
│   │   │   │   │   │       ├── 20140513_quote.zip
│   │   │   │   │   │       ├── 20140514_quote.zip
│   │   │   │   │   │       └── 20140515_quote.zip
│   │   │   │   │   └── tick
│   │   │   │   │       ├── eurusd
│   │   │   │   │       │   ├── 20140501_quote.zip
│   │   │   │   │       │   ├── 20140502_quote.zip
│   │   │   │   │       │   ├── 20140504_quote.zip
│   │   │   │   │       │   ├── 20140505_quote.zip
│   │   │   │   │       │   ├── 20140506_quote.zip
│   │   │   │   │       │   ├── 20140507_quote.zip
│   │   │   │   │       │   ├── 20140508_quote.zip
│   │   │   │   │       │   ├── 20140509_quote.zip
│   │   │   │   │       │   ├── 20140511_quote.zip
│   │   │   │   │       │   ├── 20140512_quote.zip
│   │   │   │   │       │   ├── 20140513_quote.zip
│   │   │   │   │       │   ├── 20140514_quote.zip
│   │   │   │   │       │   └── 20140515_quote.zip
│   │   │   │   │       └── nzdusd
│   │   │   │   │           ├── 20140501_quote.zip
│   │   │   │   │           ├── 20140502_quote.zip
│   │   │   │   │           ├── 20140504_quote.zip
│   │   │   │   │           ├── 20140505_quote.zip
│   │   │   │   │           ├── 20140506_quote.zip
│   │   │   │   │           ├── 20140507_quote.zip
│   │   │   │   │           ├── 20140508_quote.zip
│   │   │   │   │           ├── 20140509_quote.zip
│   │   │   │   │           ├── 20140511_quote.zip
│   │   │   │   │           ├── 20140512_quote.zip
│   │   │   │   │           ├── 20140513_quote.zip
│   │   │   │   │           ├── 20140514_quote.zip
│   │   │   │   │           └── 20140515_quote.zip
│   │   │   │   ├── oanda
│   │   │   │   │   ├── daily
│   │   │   │   │   │   ├── eurgbp.zip
│   │   │   │   │   │   ├── eurusd.zip
│   │   │   │   │   │   ├── gbpusd.zip
│   │   │   │   │   │   └── nzdusd.zip
│   │   │   │   │   ├── hour
│   │   │   │   │   │   ├── eurusd.zip
│   │   │   │   │   │   └── nzdusd.zip
│   │   │   │   │   ├── minute
│   │   │   │   │   │   ├── eurusd
│   │   │   │   │   │   │   ├── 20140501_quote.zip
│   │   │   │   │   │   │   ├── 20140502_quote.zip
│   │   │   │   │   │   │   ├── 20140504_quote.zip
│   │   │   │   │   │   │   ├── 20140505_quote.zip
│   │   │   │   │   │   │   ├── 20140506_quote.zip
│   │   │   │   │   │   │   ├── 20140507_quote.zip
│   │   │   │   │   │   │   ├── 20140508_quote.zip
│   │   │   │   │   │   │   ├── 20140509_quote.zip
│   │   │   │   │   │   │   ├── 20140511_quote.zip
│   │   │   │   │   │   │   ├── 20140512_quote.zip
│   │   │   │   │   │   │   ├── 20140513_quote.zip
│   │   │   │   │   │   │   ├── 20140514_quote.zip
│   │   │   │   │   │   │   ├── 20140515_quote.zip
│   │   │   │   │   │   │   ├── 20180403_quote.zip
│   │   │   │   │   │   │   └── 20180404_quote.zip
│   │   │   │   │   │   └── nzdusd
│   │   │   │   │   │       ├── 20140501_quote.zip
│   │   │   │   │   │       ├── 20140502_quote.zip
│   │   │   │   │   │       ├── 20140504_quote.zip
│   │   │   │   │   │       ├── 20140505_quote.zip
│   │   │   │   │   │       ├── 20140506_quote.zip
│   │   │   │   │   │       ├── 20140507_quote.zip
│   │   │   │   │   │       ├── 20140508_quote.zip
│   │   │   │   │   │       ├── 20140509_quote.zip
│   │   │   │   │   │       ├── 20140511_quote.zip
│   │   │   │   │   │       ├── 20140512_quote.zip
│   │   │   │   │   │       ├── 20140513_quote.zip
│   │   │   │   │   │       ├── 20140514_quote.zip
│   │   │   │   │   │       └── 20140515_quote.zip
│   │   │   │   │   ├── second
│   │   │   │   │   │   ├── eurusd
│   │   │   │   │   │   │   ├── 20140501_quote.zip
│   │   │   │   │   │   │   ├── 20140502_quote.zip
│   │   │   │   │   │   │   ├── 20140504_quote.zip
│   │   │   │   │   │   │   ├── 20140505_quote.zip
│   │   │   │   │   │   │   ├── 20140506_quote.zip
│   │   │   │   │   │   │   ├── 20140507_quote.zip
│   │   │   │   │   │   │   ├── 20140508_quote.zip
│   │   │   │   │   │   │   ├── 20140509_quote.zip
│   │   │   │   │   │   │   ├── 20140511_quote.zip
│   │   │   │   │   │   │   ├── 20140512_quote.zip
│   │   │   │   │   │   │   ├── 20140513_quote.zip
│   │   │   │   │   │   │   ├── 20140514_quote.zip
│   │   │   │   │   │   │   └── 20140515_quote.zip
│   │   │   │   │   │   └── nzdusd
│   │   │   │   │   │       ├── 20140501_quote.zip
│   │   │   │   │   │       ├── 20140502_quote.zip
│   │   │   │   │   │       ├── 20140504_quote.zip
│   │   │   │   │   │       ├── 20140505_quote.zip
│   │   │   │   │   │       ├── 20140506_quote.zip
│   │   │   │   │   │       ├── 20140507_quote.zip
│   │   │   │   │   │       ├── 20140508_quote.zip
│   │   │   │   │   │       ├── 20140509_quote.zip
│   │   │   │   │   │       ├── 20140511_quote.zip
│   │   │   │   │   │       ├── 20140512_quote.zip
│   │   │   │   │   │       ├── 20140513_quote.zip
│   │   │   │   │   │       ├── 20140514_quote.zip
│   │   │   │   │   │       └── 20140515_quote.zip
│   │   │   │   │   └── tick
│   │   │   │   │       ├── eurusd
│   │   │   │   │       │   ├── 20140501_quote.zip
│   │   │   │   │       │   ├── 20140502_quote.zip
│   │   │   │   │       │   ├── 20140504_quote.zip
│   │   │   │   │       │   ├── 20140505_quote.zip
│   │   │   │   │       │   ├── 20140506_quote.zip
│   │   │   │   │       │   ├── 20140507_quote.zip
│   │   │   │   │       │   ├── 20140508_quote.zip
│   │   │   │   │       │   ├── 20140509_quote.zip
│   │   │   │   │       │   ├── 20140511_quote.zip
│   │   │   │   │       │   ├── 20140512_quote.zip
│   │   │   │   │       │   ├── 20140513_quote.zip
│   │   │   │   │       │   ├── 20140514_quote.zip
│   │   │   │   │       │   └── 20140515_quote.zip
│   │   │   │   │       └── nzdusd
│   │   │   │   │           ├── 20140501_quote.zip
│   │   │   │   │           ├── 20140502_quote.zip
│   │   │   │   │           ├── 20140504_quote.zip
│   │   │   │   │           ├── 20140505_quote.zip
│   │   │   │   │           ├── 20140506_quote.zip
│   │   │   │   │           ├── 20140507_quote.zip
│   │   │   │   │           ├── 20140508_quote.zip
│   │   │   │   │           ├── 20140509_quote.zip
│   │   │   │   │           ├── 20140511_quote.zip
│   │   │   │   │           ├── 20140512_quote.zip
│   │   │   │   │           ├── 20140513_quote.zip
│   │   │   │   │           ├── 20140514_quote.zip
│   │   │   │   │           └── 20140515_quote.zip
│   │   │   │   └── readme.md
│   │   │   ├── future
│   │   │   │   ├── cbot
│   │   │   │   │   ├── daily
│   │   │   │   │   │   ├── zc_openinterest.zip
│   │   │   │   │   │   ├── zs_openinterest.zip
│   │   │   │   │   │   └── zw_openinterest.zip
│   │   │   │   │   ├── hour
│   │   │   │   │   │   ├── zc_openinterest.zip
│   │   │   │   │   │   ├── zs_openinterest.zip
│   │   │   │   │   │   └── zw_openinterest.zip
│   │   │   │   │   ├── margins
│   │   │   │   │   │   ├── 10Y.csv
│   │   │   │   │   │   ├── 2YY.csv
│   │   │   │   │   │   ├── 30Y.csv
│   │   │   │   │   │   ├── 5YY.csv
│   │   │   │   │   │   ├── AW.csv
│   │   │   │   │   │   ├── BCF.csv
│   │   │   │   │   │   ├── BWF.csv
│   │   │   │   │   │   ├── EH.csv
│   │   │   │   │   │   ├── F1U.csv
│   │   │   │   │   │   ├── KE.csv
│   │   │   │   │   │   ├── MYM.csv
│   │   │   │   │   │   ├── readme.md
│   │   │   │   │   │   ├── TN.csv
│   │   │   │   │   │   ├── UB.csv
│   │   │   │   │   │   ├── YM.csv
│   │   │   │   │   │   ├── ZB.csv
│   │   │   │   │   │   ├── ZC.csv
│   │   │   │   │   │   ├── ZF.csv
│   │   │   │   │   │   ├── ZL.csv
│   │   │   │   │   │   ├── ZM.csv
│   │   │   │   │   │   ├── ZN.csv
│   │   │   │   │   │   ├── ZO.csv
│   │   │   │   │   │   ├── ZS.csv
│   │   │   │   │   │   ├── ZT.csv
│   │   │   │   │   │   └── ZW.csv
│   │   │   │   │   └── minute
│   │   │   │   │       ├── zc
│   │   │   │   │       │   └── 20210101_openinterest.zip
│   │   │   │   │       ├── zs
│   │   │   │   │       │   └── 20210101_openinterest.zip
│   │   │   │   │       └── zw
│   │   │   │   │           └── 20210101_openinterest.zip
│   │   │   │   ├── cfe
│   │   │   │   │   └── margins
│   │   │   │   │       ├── readme.md
│   │   │   │   │       ├── VX.csv
│   │   │   │   │       └── VXM.csv
│   │   │   │   ├── cme
│   │   │   │   │   ├── daily
│   │   │   │   │   │   ├── es_openinterest.zip
│   │   │   │   │   │   ├── es_quote.zip
│   │   │   │   │   │   └── es_trade.zip
│   │   │   │   │   ├── factor_files
│   │   │   │   │   │   └── es.csv
│   │   │   │   │   ├── hour
│   │   │   │   │   │   ├── es_openinterest.zip
│   │   │   │   │   │   ├── es_quote.zip
│   │   │   │   │   │   └── es_trade.zip
│   │   │   │   │   ├── map_files
│   │   │   │   │   │   └── es.csv
│   │   │   │   │   ├── margins
│   │   │   │   │   │   ├── 6A.csv
│   │   │   │   │   │   ├── 6B.csv
│   │   │   │   │   │   ├── 6C.csv
│   │   │   │   │   │   ├── 6E.csv
│   │   │   │   │   │   ├── 6J.csv
│   │   │   │   │   │   ├── 6L.csv
│   │   │   │   │   │   ├── 6M.csv
│   │   │   │   │   │   ├── 6N.csv
│   │   │   │   │   │   ├── 6R.csv
│   │   │   │   │   │   ├── 6S.csv
│   │   │   │   │   │   ├── 6Z.csv
│   │   │   │   │   │   ├── ACD.csv
│   │   │   │   │   │   ├── AJY.csv
│   │   │   │   │   │   ├── ANE.csv
│   │   │   │   │   │   ├── BIO.csv
│   │   │   │   │   │   ├── BTC.csv
│   │   │   │   │   │   ├── CJY.csv
│   │   │   │   │   │   ├── CNH.csv
│   │   │   │   │   │   ├── E7.csv
│   │   │   │   │   │   ├── EAD.csv
│   │   │   │   │   │   ├── ECD.csv
│   │   │   │   │   │   ├── EI.csv
│   │   │   │   │   │   ├── EMD.csv
│   │   │   │   │   │   ├── ES.csv
│   │   │   │   │   │   ├── ESK.csv
│   │   │   │   │   │   ├── GD.csv
│   │   │   │   │   │   ├── GE.csv
│   │   │   │   │   │   ├── GF.csv
│   │   │   │   │   │   ├── HE.csv
│   │   │   │   │   │   ├── IBV.csv
│   │   │   │   │   │   ├── J7.csv
│   │   │   │   │   │   ├── LBS.csv
│   │   │   │   │   │   ├── LE.csv
│   │   │   │   │   │   ├── M2K.csv
│   │   │   │   │   │   ├── M6A.csv
│   │   │   │   │   │   ├── M6B.csv
│   │   │   │   │   │   ├── M6C.csv
│   │   │   │   │   │   ├── M6E.csv
│   │   │   │   │   │   ├── MBT.csv
│   │   │   │   │   │   ├── MCD.csv
│   │   │   │   │   │   ├── MES.csv
│   │   │   │   │   │   ├── MET.csv
│   │   │   │   │   │   ├── MIR.csv
│   │   │   │   │   │   ├── MJY.csv
│   │   │   │   │   │   ├── MNH.csv
│   │   │   │   │   │   ├── MNQ.csv
│   │   │   │   │   │   ├── MRB.csv
│   │   │   │   │   │   ├── MSF.csv
│   │   │   │   │   │   ├── NKD.csv
│   │   │   │   │   │   ├── NQ.csv
│   │   │   │   │   │   ├── readme.md
│   │   │   │   │   │   └── RTY.csv
│   │   │   │   │   ├── minute
│   │   │   │   │   │   └── es
│   │   │   │   │   │       ├── 20131006_openinterest.zip
│   │   │   │   │   │       ├── 20131006_quote.zip
│   │   │   │   │   │       ├── 20131006_trade.zip
│   │   │   │   │   │       ├── 20131007_openinterest.zip
│   │   │   │   │   │       ├── 20131007_quote.zip
│   │   │   │   │   │       ├── 20131007_trade.zip
│   │   │   │   │   │       ├── 20131008_openinterest.zip
│   │   │   │   │   │       ├── 20131008_quote.zip
│   │   │   │   │   │       ├── 20131008_trade.zip
│   │   │   │   │   │       ├── 20131009_openinterest.zip
│   │   │   │   │   │       ├── 20131009_quote.zip
│   │   │   │   │   │       ├── 20131009_trade.zip
│   │   │   │   │   │       ├── 20131010_openinterest.zip
│   │   │   │   │   │       ├── 20131010_quote.zip
│   │   │   │   │   │       ├── 20131010_trade.zip
│   │   │   │   │   │       ├── 20131011_openinterest.zip
│   │   │   │   │   │       ├── 20131011_quote.zip
│   │   │   │   │   │       ├── 20131011_trade.zip
│   │   │   │   │   │       ├── 20131014_quote.zip
│   │   │   │   │   │       ├── 20131014_trade.zip
│   │   │   │   │   │       ├── 20131029_quote.zip
│   │   │   │   │   │       ├── 20131029_trade.zip
│   │   │   │   │   │       ├── 20131030_quote.zip
│   │   │   │   │   │       ├── 20131030_trade.zip
│   │   │   │   │   │       ├── 20131118_openinterest.zip
│   │   │   │   │   │       ├── 20131118_quote.zip
│   │   │   │   │   │       ├── 20131118_trade.zip
│   │   │   │   │   │       ├── 20131202_openinterest.zip
│   │   │   │   │   │       ├── 20131202_quote.zip
│   │   │   │   │   │       ├── 20131202_trade.zip
│   │   │   │   │   │       ├── 20131203_quote.zip
│   │   │   │   │   │       ├── 20131203_trade.zip
│   │   │   │   │   │       ├── 20131218_openinterest.zip
│   │   │   │   │   │       ├── 20131218_quote.zip
│   │   │   │   │   │       ├── 20131218_trade.zip
│   │   │   │   │   │       ├── 20131220_openinterest.zip
│   │   │   │   │   │       ├── 20131220_quote.zip
│   │   │   │   │   │       ├── 20131220_trade.zip
│   │   │   │   │   │       ├── 20200105_openinterest.zip
│   │   │   │   │   │       ├── 20200105_quote.zip
│   │   │   │   │   │       ├── 20200105_trade.zip
│   │   │   │   │   │       ├── 20200106_openinterest.zip
│   │   │   │   │   │       ├── 20200106_quote.zip
│   │   │   │   │   │       └── 20200106_trade.zip
│   │   │   │   │   └── universes
│   │   │   │   │       └── es
│   │   │   │   │           ├── 20130710.csv
│   │   │   │   │           ├── 20130711.csv
│   │   │   │   │           ├── 20131003.csv
│   │   │   │   │           ├── 20131004.csv
│   │   │   │   │           ├── 20131007.csv
│   │   │   │   │           ├── 20131008.csv
│   │   │   │   │           ├── 20131009.csv
│   │   │   │   │           ├── 20131010.csv
│   │   │   │   │           ├── 20131011.csv
│   │   │   │   │           ├── 20131015.csv
│   │   │   │   │           ├── 20131016.csv
│   │   │   │   │           ├── 20131028.csv
│   │   │   │   │           ├── 20131125.csv
│   │   │   │   │           ├── 20131217.csv
│   │   │   │   │           ├── 20131219.csv
│   │   │   │   │           ├── 20131226.csv
│   │   │   │   │           ├── 20131227.csv
│   │   │   │   │           ├── 20140224.csv
│   │   │   │   │           ├── 20140225.csv
│   │   │   │   │           ├── 20140318.csv
│   │   │   │   │           ├── 20140320.csv
│   │   │   │   │           ├── 20140425.csv
│   │   │   │   │           ├── 20140606.csv
│   │   │   │   │           ├── 20140609.csv
│   │   │   │   │           ├── 20200102.csv
│   │   │   │   │           ├── 20200103.csv
│   │   │   │   │           ├── 20200106.csv
│   │   │   │   │           ├── 20200107.csv
│   │   │   │   │           ├── 20200131.csv
│   │   │   │   │           ├── 20200203.csv
│   │   │   │   │           ├── 20200204.csv
│   │   │   │   │           ├── 20200205.csv
│   │   │   │   │           ├── 20200206.csv
│   │   │   │   │           ├── 20200207.csv
│   │   │   │   │           ├── 20200210.csv
│   │   │   │   │           ├── 20200211.csv
│   │   │   │   │           └── 20201006.csv
│   │   │   │   ├── comex
│   │   │   │   │   ├── daily
│   │   │   │   │   │   ├── gc_openinterest.zip
│   │   │   │   │   │   ├── gc_quote.zip
│   │   │   │   │   │   └── gc_trade.zip
│   │   │   │   │   ├── factor_files
│   │   │   │   │   │   └── gc.csv
│   │   │   │   │   ├── hour
│   │   │   │   │   │   ├── gc_openinterest.zip
│   │   │   │   │   │   ├── gc_quote.zip
│   │   │   │   │   │   └── gc_trade.zip
│   │   │   │   │   ├── map_files
│   │   │   │   │   │   └── gc.csv
│   │   │   │   │   ├── margins
│   │   │   │   │   │   ├── AUP.csv
│   │   │   │   │   │   ├── EDP.csv
│   │   │   │   │   │   ├── GC.csv
│   │   │   │   │   │   ├── HG.csv
│   │   │   │   │   │   ├── MGC.csv
│   │   │   │   │   │   ├── MGT.csv
│   │   │   │   │   │   ├── readme.md
│   │   │   │   │   │   ├── SI.csv
│   │   │   │   │   │   └── SIL.csv
│   │   │   │   │   ├── minute
│   │   │   │   │   │   └── gc
│   │   │   │   │   │       ├── 20131007_openinterest.zip
│   │   │   │   │   │       ├── 20131007_quote.zip
│   │   │   │   │   │       ├── 20131007_trade.zip
│   │   │   │   │   │       ├── 20131008_openinterest.zip
│   │   │   │   │   │       ├── 20131008_quote.zip
│   │   │   │   │   │       ├── 20131008_trade.zip
│   │   │   │   │   │       ├── 20131009_openinterest.zip
│   │   │   │   │   │       ├── 20131009_quote.zip
│   │   │   │   │   │       ├── 20131009_trade.zip
│   │   │   │   │   │       ├── 20131010_openinterest.zip
│   │   │   │   │   │       ├── 20131010_quote.zip
│   │   │   │   │   │       ├── 20131010_trade.zip
│   │   │   │   │   │       ├── 20131011_openinterest.zip
│   │   │   │   │   │       ├── 20131011_quote.zip
│   │   │   │   │   │       ├── 20131011_trade.zip
│   │   │   │   │   │       ├── 20200105_quote.zip
│   │   │   │   │   │       ├── 20200105_trade.zip
│   │   │   │   │   │       ├── 20200106_quote.zip
│   │   │   │   │   │       └── 20200106_trade.zip
│   │   │   │   │   ├── tick
│   │   │   │   │   │   └── gc
│   │   │   │   │   │       ├── 20131007_openinterest.zip
│   │   │   │   │   │       ├── 20131007_quote.zip
│   │   │   │   │   │       ├── 20131007_trade.zip
│   │   │   │   │   │       ├── 20131008_openinterest.zip
│   │   │   │   │   │       ├── 20131008_quote.zip
│   │   │   │   │   │       ├── 20131008_trade.zip
│   │   │   │   │   │       ├── 20131009_openinterest.zip
│   │   │   │   │   │       ├── 20131009_quote.zip
│   │   │   │   │   │       └── 20131009_trade.zip
│   │   │   │   │   └── universes
│   │   │   │   │       └── gc
│   │   │   │   │           ├── 20131004.csv
│   │   │   │   │           ├── 20131007.csv
│   │   │   │   │           ├── 20131008.csv
│   │   │   │   │           ├── 20131009.csv
│   │   │   │   │           ├── 20131015.csv
│   │   │   │   │           ├── 20131016.csv
│   │   │   │   │           ├── 20131028.csv
│   │   │   │   │           ├── 20131125.csv
│   │   │   │   │           ├── 20131217.csv
│   │   │   │   │           ├── 20140225.csv
│   │   │   │   │           ├── 20200102.csv
│   │   │   │   │           └── 20200103.csv
│   │   │   │   ├── eurex
│   │   │   │   │   ├── factor_files
│   │   │   │   │   │   └── fesx.csv
│   │   │   │   │   ├── map_files
│   │   │   │   │   │   └── fesx.csv
│   │   │   │   │   ├── margins
│   │   │   │   │   │   ├── FDAX.csv
│   │   │   │   │   │   ├── FDIV.csv
│   │   │   │   │   │   ├── FDXM.csv
│   │   │   │   │   │   ├── FDXS.csv
│   │   │   │   │   │   ├── FESX.csv
│   │   │   │   │   │   ├── FSDX.csv
│   │   │   │   │   │   ├── FSMX.csv
│   │   │   │   │   │   └── FTDX.csv
│   │   │   │   │   ├── minute
│   │   │   │   │   │   └── fesx
│   │   │   │   │   │       ├── 20240603_trade.zip
│   │   │   │   │   │       ├── 20240604_trade.zip
│   │   │   │   │   │       └── 20240621_trade.zip
│   │   │   │   │   └── universes
│   │   │   │   │       └── fesx
│   │   │   │   │           ├── 20240531.csv
│   │   │   │   │           ├── 20240603.csv
│   │   │   │   │           └── 20240620.csv
│   │   │   │   ├── hkfe
│   │   │   │   │   ├── daily
│   │   │   │   │   │   ├── hsi_quote.zip
│   │   │   │   │   │   └── hsi_trade.zip
│   │   │   │   │   ├── factor_files
│   │   │   │   │   │   └── hsi.csv
│   │   │   │   │   ├── hour
│   │   │   │   │   │   ├── hsi_quote.zip
│   │   │   │   │   │   └── hsi_trade.zip
│   │   │   │   │   ├── map_files
│   │   │   │   │   │   └── hsi.csv
│   │   │   │   │   ├── margins
│   │   │   │   │   │   └── HSI.csv
│   │   │   │   │   └── universes
│   │   │   │   │       └── hsi
│   │   │   │   │           ├── 20131004.csv
│   │   │   │   │           ├── 20131017.csv
│   │   │   │   │           ├── 20131018.csv
│   │   │   │   │           ├── 20131021.csv
│   │   │   │   │           ├── 20131022.csv
│   │   │   │   │           ├── 20131023.csv
│   │   │   │   │           ├── 20131024.csv
│   │   │   │   │           ├── 20131025.csv
│   │   │   │   │           ├── 20131028.csv
│   │   │   │   │           └── 20131029.csv
│   │   │   │   ├── ice
│   │   │   │   │   └── margins
│   │   │   │   │       ├── CC.csv
│   │   │   │   │       ├── CT.csv
│   │   │   │   │       ├── DX.csv
│   │   │   │   │       ├── KC.csv
│   │   │   │   │       ├── OJ.csv
│   │   │   │   │       ├── readme.md
│   │   │   │   │       └── SB.csv
│   │   │   │   ├── krx
│   │   │   │   │   └── margins
│   │   │   │   │       └── KM.csv
│   │   │   │   ├── nymex
│   │   │   │   │   └── margins
│   │   │   │   │       ├── 1S.csv
│   │   │   │   │       ├── 22.csv
│   │   │   │   │       ├── A0D.csv
│   │   │   │   │       ├── A0F.csv
│   │   │   │   │       ├── A1L.csv
│   │   │   │   │       ├── A1M.csv
│   │   │   │   │       ├── A1R.csv
│   │   │   │   │       ├── A32.csv
│   │   │   │   │       ├── A3G.csv
│   │   │   │   │       ├── A7E.csv
│   │   │   │   │       ├── A7I.csv
│   │   │   │   │       ├── A7Q.csv
│   │   │   │   │       ├── A8J.csv
│   │   │   │   │       ├── A8K.csv
│   │   │   │   │       ├── A8O.csv
│   │   │   │   │       ├── A91.csv
│   │   │   │   │       ├── A9N.csv
│   │   │   │   │       ├── AA6.csv
│   │   │   │   │       ├── AA8.csv
│   │   │   │   │       ├── ABS.csv
│   │   │   │   │       ├── ABT.csv
│   │   │   │   │       ├── AC0.csv
│   │   │   │   │       ├── AD0.csv
│   │   │   │   │       ├── ADB.csv
│   │   │   │   │       ├── AE5.csv
│   │   │   │   │       ├── AGA.csv
│   │   │   │   │       ├── AJL.csv
│   │   │   │   │       ├── AJS.csv
│   │   │   │   │       ├── AKL.csv
│   │   │   │   │       ├── AKZ.csv
│   │   │   │   │       ├── APS.csv
│   │   │   │   │       ├── AR0.csv
│   │   │   │   │       ├── ARE.csv
│   │   │   │   │       ├── AVZ.csv
│   │   │   │   │       ├── AYV.csv
│   │   │   │   │       ├── AYX.csv
│   │   │   │   │       ├── AZ1.csv
│   │   │   │   │       ├── B0.csv
│   │   │   │   │       ├── B7H.csv
│   │   │   │   │       ├── BK.csv
│   │   │   │   │       ├── BOO.csv
│   │   │   │   │       ├── BR7.csv
│   │   │   │   │       ├── BZ.csv
│   │   │   │   │       ├── CL.csv
│   │   │   │   │       ├── CRB.csv
│   │   │   │   │       ├── CSW.csv
│   │   │   │   │       ├── CSX.csv
│   │   │   │   │       ├── CU.csv
│   │   │   │   │       ├── D1N.csv
│   │   │   │   │       ├── DCB.csv
│   │   │   │   │       ├── E6.csv
│   │   │   │   │       ├── EN.csv
│   │   │   │   │       ├── EPN.csv
│   │   │   │   │       ├── EVC.csv
│   │   │   │   │       ├── EWG.csv
│   │   │   │   │       ├── EWN.csv
│   │   │   │   │       ├── EXR.csv
│   │   │   │   │       ├── FO.csv
│   │   │   │   │       ├── FRC.csv
│   │   │   │   │       ├── FSS.csv
│   │   │   │   │       ├── GCU.csv
│   │   │   │   │       ├── HCL.csv
│   │   │   │   │       ├── HH.csv
│   │   │   │   │       ├── HO.csv
│   │   │   │   │       ├── HP.csv
│   │   │   │   │       ├── HRC.csv
│   │   │   │   │       ├── HTT.csv
│   │   │   │   │       ├── M1B.csv
│   │   │   │   │       ├── M35.csv
│   │   │   │   │       ├── M5F.csv
│   │   │   │   │       ├── MAF.csv
│   │   │   │   │       ├── MCL.csv
│   │   │   │   │       ├── MEF.csv
│   │   │   │   │       ├── NG.csv
│   │   │   │   │       ├── PA.csv
│   │   │   │   │       ├── PAM.csv
│   │   │   │   │       ├── PL.csv
│   │   │   │   │       ├── R5O.csv
│   │   │   │   │       ├── RB.csv
│   │   │   │   │       ├── readme.md
│   │   │   │   │       ├── S5O.csv
│   │   │   │   │       └── YO.csv
│   │   │   │   ├── nyseliffe
│   │   │   │   │   └── margins
│   │   │   │   │       ├── M1EU.csv
│   │   │   │   │       ├── M1JP.csv
│   │   │   │   │       ├── M1MSA.csv
│   │   │   │   │       ├── MXEA.csv
│   │   │   │   │       ├── MXEF.csv
│   │   │   │   │       ├── MXUS.csv
│   │   │   │   │       ├── YG.csv
│   │   │   │   │       ├── YI.csv
│   │   │   │   │       ├── ZG.csv
│   │   │   │   │       └── ZI.csv
│   │   │   │   ├── readme.md
│   │   │   │   └── sgx
│   │   │   │       └── margins
│   │   │   │           ├── IN.csv
│   │   │   │           ├── NK.csv
│   │   │   │           └── TW.csv
│   │   │   ├── futureoption
│   │   │   │   ├── cme
│   │   │   │   │   ├── daily
│   │   │   │   │   │   └── es
│   │   │   │   │   │       └── 202003
│   │   │   │   │   │           └── es_2020_trade_american.zip
│   │   │   │   │   ├── hour
│   │   │   │   │   │   └── es
│   │   │   │   │   │       └── 202003
│   │   │   │   │   │           └── es_2020_trade_american.zip
│   │   │   │   │   ├── minute
│   │   │   │   │   │   └── es
│   │   │   │   │   │       ├── 202003
│   │   │   │   │   │       │   ├── 20200105_quote_american.zip
│   │   │   │   │   │       │   ├── 20200105_trade_american.zip
│   │   │   │   │   │       │   ├── 20200106_quote_american.zip
│   │   │   │   │   │       │   └── 20200106_trade_american.zip
│   │   │   │   │   │       └── 202006
│   │   │   │   │   │           ├── 20200105_quote_american.zip
│   │   │   │   │   │           ├── 20200105_trade_american.zip
│   │   │   │   │   │           ├── 20200106_quote_american.zip
│   │   │   │   │   │           └── 20200106_trade_american.zip
│   │   │   │   │   └── universes
│   │   │   │   │       └── es
│   │   │   │   │           ├── 202003
│   │   │   │   │           │   ├── 20200102.csv
│   │   │   │   │           │   ├── 20200103.csv
│   │   │   │   │           │   ├── 20200106.csv
│   │   │   │   │           │   ├── 20200107.csv
│   │   │   │   │           │   └── 20200108.csv
│   │   │   │   │           └── 202006
│   │   │   │   │               ├── 20200102.csv
│   │   │   │   │               ├── 20200103.csv
│   │   │   │   │               ├── 20200106.csv
│   │   │   │   │               ├── 20200107.csv
│   │   │   │   │               └── 20200108.csv
│   │   │   │   └── comex
│   │   │   │       ├── daily
│   │   │   │       │   └── og
│   │   │   │       │       └── 202004
│   │   │   │       │           └── og_2020_quote_american.zip
│   │   │   │       ├── hour
│   │   │   │       │   └── og
│   │   │   │       │       └── 202004
│   │   │   │       │           └── og_2020_quote_american.zip
│   │   │   │       ├── minute
│   │   │   │       │   └── og
│   │   │   │       │       └── 202004
│   │   │   │       │           ├── 20200105_quote_american.zip
│   │   │   │       │           └── 20200106_quote_american.zip
│   │   │   │       └── universes
│   │   │   │           └── og
│   │   │   │               └── 202004
│   │   │   │                   ├── 20200102.csv
│   │   │   │                   └── 20200103.csv
│   │   │   ├── index
│   │   │   │   ├── eurex
│   │   │   │   │   └── minute
│   │   │   │   │       └── sx5e
│   │   │   │   │           ├── 20240729_trade.zip
│   │   │   │   │           └── 20240730_trade.zip
│   │   │   │   ├── hkfe
│   │   │   │   │   ├── daily
│   │   │   │   │   │   └── hsi.zip
│   │   │   │   │   └── hour
│   │   │   │   │       └── hsi.zip
│   │   │   │   ├── india
│   │   │   │   │   └── minute
│   │   │   │   │       └── nifty50
│   │   │   │   │           ├── 20190101_trade.zip
│   │   │   │   │           ├── 20190102_trade.zip
│   │   │   │   │           ├── 20190103_trade.zip
│   │   │   │   │           └── 20190104_trade.zip
│   │   │   │   ├── ose
│   │   │   │   │   └── minute
│   │   │   │   │       └── n225
│   │   │   │   │           └── 20210114_trade.zip
│   │   │   │   └── usa
│   │   │   │       ├── daily
│   │   │   │       │   └── spx.zip
│   │   │   │       ├── hour
│   │   │   │       │   ├── ndx.zip
│   │   │   │       │   └── spx.zip
│   │   │   │       └── minute
│   │   │   │           └── spx
│   │   │   │               ├── 20210104_trade.zip
│   │   │   │               ├── 20210114_trade.zip
│   │   │   │               ├── 20230626_trade.zip
│   │   │   │               ├── 20230630_trade.zip
│   │   │   │               └── 20230703_trade.zip
│   │   │   ├── indexoption
│   │   │   │   └── usa
│   │   │   │       ├── daily
│   │   │   │       │   ├── spx_2021_openinterest_european.zip
│   │   │   │       │   ├── spx_2021_quote_european.zip
│   │   │   │       │   └── spx_2021_trade_european.zip
│   │   │   │       ├── hour
│   │   │   │       │   ├── nqx_2021_openinterest_european.zip
│   │   │   │       │   ├── nqx_2021_quote_european.zip
│   │   │   │       │   ├── nqx_2021_trade_european.zip
│   │   │   │       │   ├── spx_2021_openinterest_european.zip
│   │   │   │       │   ├── spx_2021_quote_european.zip
│   │   │   │       │   └── spx_2021_trade_european.zip
│   │   │   │       ├── minute
│   │   │   │       │   ├── spx
│   │   │   │       │   │   ├── 20210104_openinterest_european.zip
│   │   │   │       │   │   ├── 20210104_quote_european.zip
│   │   │   │       │   │   ├── 20210104_trade_european.zip
│   │   │   │       │   │   ├── 20210114_openinterest_european.zip
│   │   │   │       │   │   ├── 20210114_quote_european.zip
│   │   │   │       │   │   └── 20210114_trade_european.zip
│   │   │   │       │   └── spxw
│   │   │   │       │       ├── 20210104_openinterest_european.zip.zip
│   │   │   │       │       ├── 20210104_quote_european.zip
│   │   │   │       │       ├── 20210104_trade_european.zip.zip
│   │   │   │       │       ├── 20210105_quote_european.zip
│   │   │   │       │       ├── 20210105_trade_european.zip
│   │   │   │       │       ├── 20210106_quote_european.zip
│   │   │   │       │       ├── 20210106_trade_european.zip
│   │   │   │       │       ├── 20210107_quote_european.zip
│   │   │   │       │       ├── 20210107_trade_european.zip
│   │   │   │       │       ├── 20210108_quote_european.zip
│   │   │   │       │       ├── 20210108_trade_european.zip
│   │   │   │       │       ├── 20230626_openinterest_european.zip
│   │   │   │       │       ├── 20230626_quote_european.zip
│   │   │   │       │       └── 20230626_trade_european.zip
│   │   │   │       └── universes
│   │   │   │           ├── nqx
│   │   │   │           │   ├── 20210316.csv
│   │   │   │           │   ├── 20210317.csv
│   │   │   │           │   └── 20210318.csv
│   │   │   │           ├── spx
│   │   │   │           │   ├── 20151222.csv
│   │   │   │           │   ├── 20151223.csv
│   │   │   │           │   ├── 20201230.csv
│   │   │   │           │   ├── 20201231.csv
│   │   │   │           │   ├── 20210104.csv
│   │   │   │           │   ├── 20210105.csv
│   │   │   │           │   ├── 20210106.csv
│   │   │   │           │   ├── 20210107.csv
│   │   │   │           │   ├── 20210108.csv
│   │   │   │           │   ├── 20210111.csv
│   │   │   │           │   ├── 20210112.csv
│   │   │   │           │   ├── 20210113.csv
│   │   │   │           │   └── 20210114.csv
│   │   │   │           └── spxw
│   │   │   │               ├── 20201231.csv
│   │   │   │               └── 20230623.csv
│   │   │   ├── market-hours
│   │   │   │   └── market-hours-database.json
│   │   │   ├── option
│   │   │   │   ├── readme.md
│   │   │   │   └── usa
│   │   │   │       ├── daily
│   │   │   │       │   ├── aapl_2014_openinterest_american.zip
│   │   │   │       │   ├── aapl_2014_quote_american.zip
│   │   │   │       │   ├── aapl_2014_trade_american.zip
│   │   │   │       │   ├── aapl_2015_quote_american.zip
│   │   │   │       │   ├── aapl_2015_trade_american.zip
│   │   │   │       │   ├── foxa_2013_quote_american.zip
│   │   │   │       │   ├── foxa_2013_trade_american.zip
│   │   │   │       │   ├── goog_2015_openinterest_american.zip
│   │   │   │       │   ├── goog_2015_quote_american.zip
│   │   │   │       │   ├── goog_2015_trade_american.zip
│   │   │   │       │   ├── nwsa_2013_quote_american.zip
│   │   │   │       │   ├── nwsa_2013_trade_american.zip
│   │   │   │       │   ├── twx_2014_openinterest_american.zip
│   │   │   │       │   ├── twx_2014_quote_american.zip
│   │   │   │       │   └── twx_2014_trade_american.zip
│   │   │   │       ├── hour
│   │   │   │       │   ├── aapl_2014_openinterest_american.zip
│   │   │   │       │   ├── aapl_2014_quote_american.zip
│   │   │   │       │   ├── aapl_2014_trade_american.zip
│   │   │   │       │   ├── foxa_2013_quote_american.zip
│   │   │   │       │   ├── foxa_2013_trade_american.zip
│   │   │   │       │   ├── goog_2015_openinterest_american.zip
│   │   │   │       │   ├── goog_2015_quote_american.zip
│   │   │   │       │   ├── goog_2015_trade_american.zip
│   │   │   │       │   ├── nwsa_2013_quote_american.zip
│   │   │   │       │   ├── nwsa_2013_trade_american.zip
│   │   │   │       │   ├── twx_2014_openinterest_american.zip
│   │   │   │       │   ├── twx_2014_quote_american.zip
│   │   │   │       │   └── twx_2014_trade_american.zip
│   │   │   │       ├── minute
│   │   │   │       │   ├── aapl
│   │   │   │       │   │   ├── 20140606_openinterest_american.zip
│   │   │   │       │   │   ├── 20140606_quote_american.zip
│   │   │   │       │   │   ├── 20140606_trade_american.zip
│   │   │   │       │   │   ├── 20140609_openinterest_american.zip
│   │   │   │       │   │   ├── 20140609_quote_american.zip
│   │   │   │       │   │   └── 20140609_trade_american.zip
│   │   │   │       │   ├── foxa
│   │   │   │       │   │   ├── 20130702_quote_american.zip
│   │   │   │       │   │   └── 20130702_trade_american.zip
│   │   │   │       │   ├── goog
│   │   │   │       │   │   ├── 20151223_openinterest_american.zip
│   │   │   │       │   │   ├── 20151223_quote_american.zip
│   │   │   │       │   │   ├── 20151223_trade_american.zip
│   │   │   │       │   │   ├── 20151224_openinterest_american.zip
│   │   │   │       │   │   ├── 20151224_quote_american.zip
│   │   │   │       │   │   ├── 20151224_trade_american.zip
│   │   │   │       │   │   ├── 20151228_quote_american.zip
│   │   │   │       │   │   └── 20151228_trade_american.zip
│   │   │   │       │   ├── nwsa
│   │   │   │       │   │   ├── 20130628_quote_american.zip
│   │   │   │       │   │   └── 20130628_trade_american.zip
│   │   │   │       │   ├── spy
│   │   │   │       │   │   ├── 20230803_quote_american.zip
│   │   │   │       │   │   └── 20230803_trade_american.zip
│   │   │   │       │   └── twx
│   │   │   │       │       ├── 20140605_openinterest_american.zip
│   │   │   │       │       ├── 20140605_quote_american.zip
│   │   │   │       │       ├── 20140605_trade_american.zip
│   │   │   │       │       ├── 20140606_openinterest_american.zip
│   │   │   │       │       ├── 20140606_quote_american.zip
│   │   │   │       │       └── 20140606_trade_american.zip
│   │   │   │       └── universes
│   │   │   │           ├── aapl
│   │   │   │           │   ├── 20140602.csv
│   │   │   │           │   ├── 20140603.csv
│   │   │   │           │   ├── 20140604.csv
│   │   │   │           │   ├── 20140605.csv
│   │   │   │           │   ├── 20140606.csv
│   │   │   │           │   ├── 20140609.csv
│   │   │   │           │   ├── 20140610.csv
│   │   │   │           │   ├── 20140611.csv
│   │   │   │           │   ├── 20140612.csv
│   │   │   │           │   ├── 20140613.csv
│   │   │   │           │   ├── 20140616.csv
│   │   │   │           │   ├── 20151211.csv
│   │   │   │           │   └── 20151214.csv
│   │   │   │           ├── goog
│   │   │   │           │   ├── 20151222.csv
│   │   │   │           │   ├── 20151223.csv
│   │   │   │           │   ├── 20151224.csv
│   │   │   │           │   ├── 20151228.csv
│   │   │   │           │   ├── 20151229.csv
│   │   │   │           │   ├── 20151230.csv
│   │   │   │           │   └── 20151231.csv
│   │   │   │           ├── nwsa
│   │   │   │           │   ├── 20130625.csv
│   │   │   │           │   ├── 20130626.csv
│   │   │   │           │   ├── 20130627.csv
│   │   │   │           │   ├── 20130628.csv
│   │   │   │           │   ├── 20130701.csv
│   │   │   │           │   └── 20130702.csv
│   │   │   │           ├── spy
│   │   │   │           │   ├── 20231228.csv
│   │   │   │           │   ├── 20231229.csv
│   │   │   │           │   ├── 20240102.csv
│   │   │   │           │   ├── 20240103.csv
│   │   │   │           │   ├── 20240104.csv
│   │   │   │           │   ├── 20240105.csv
│   │   │   │           │   ├── 20240108.csv
│   │   │   │           │   └── 20240109.csv
│   │   │   │           └── twx
│   │   │   │               ├── 20140604.csv
│   │   │   │               ├── 20140605.csv
│   │   │   │               ├── 20140606.csv
│   │   │   │               ├── 20140609.csv
│   │   │   │               └── 20140610.csv
│   │   │   ├── readme.md
│   │   │   └── symbol-properties
│   │   │       ├── security-database.csv
│   │   │       └── symbol-properties-database.csv
│   │   ├── Dockerfile
│   │   ├── DockerfileJupyter
│   │   ├── DockerfileLeanFoundation
│   │   ├── DockerfileLeanFoundationARM
│   │   ├── Documentation
│   │   │   ├── 1-Overview-Simple.jpg
│   │   │   ├── 2-Overview-Detailed-New.png
│   │   │   ├── 2-Overview-Detailed.jpg
│   │   │   ├── 3-Initializing Algorithms.jpg
│   │   │   ├── 4-Security Object.jpg
│   │   │   ├── 5-QCAlgorithm-IAlgorithm.jpg
│   │   │   ├── 6-QCAlgorithm-Portfolio.jpg
│   │   │   ├── logo.white.small.png
│   │   │   └── readme.md
│   │   ├── DownloaderDataProvider
│   │   │   ├── config.example.json
│   │   │   ├── DownloaderDataProviderArgumentParser.cs
│   │   │   ├── Models
│   │   │   │   ├── BaseDataDownloadConfig.cs
│   │   │   │   ├── BrokerageDataDownloader.cs
│   │   │   │   ├── Constants
│   │   │   │   │   └── DownloaderCommandArguments.cs
│   │   │   │   ├── DataDownloadConfig.cs
│   │   │   │   └── DataUniverseDownloadConfig.cs
│   │   │   ├── Program.cs
│   │   │   └── QuantConnect.DownloaderDataProvider.Launcher.csproj
│   │   ├── Engine
│   │   │   ├── AlgorithmManager.cs
│   │   │   ├── AlgorithmTimeLimitManager.cs
│   │   │   ├── DataFeeds
│   │   │   │   ├── AggregationManager.cs
│   │   │   │   ├── ApiDataProvider.cs
│   │   │   │   ├── BacktestingChainProvider.cs
│   │   │   │   ├── BacktestingFutureChainProvider.cs
│   │   │   │   ├── BacktestingOptionChainProvider.cs
│   │   │   │   ├── BaseDataCollectionAggregatorReader.cs
│   │   │   │   ├── BaseDataExchange.cs
│   │   │   │   ├── BaseDownloaderDataProvider.cs
│   │   │   │   ├── BaseSubscriptionDataSourceReader.cs
│   │   │   │   ├── CachingFutureChainProvider.cs
│   │   │   │   ├── CachingOptionChainProvider.cs
│   │   │   │   ├── ChainProviderInitializeParameters.cs
│   │   │   │   ├── CollectionSubscriptionDataSourceReader.cs
│   │   │   │   ├── CompositeDataProvider.cs
│   │   │   │   ├── CompositeTimeProvider.cs
│   │   │   │   ├── CreateStreamReaderErrorEventArgs.cs
│   │   │   │   ├── CurrencySubscriptionDataConfigManager.cs
│   │   │   │   ├── DataChannelProvider.cs
│   │   │   │   ├── DataDownloader
│   │   │   │   │   ├── CanonicalDataDownloaderDecorator.cs
│   │   │   │   │   └── DataDownloaderSelector.cs
│   │   │   │   ├── DataFeedPacket.cs
│   │   │   │   ├── DataManager.cs
│   │   │   │   ├── DataPermissionManager.cs
│   │   │   │   ├── DataQueueHandlerManager.cs
│   │   │   │   ├── DateChangeTimeKeeper.cs
│   │   │   │   ├── DefaultDataProvider.cs
│   │   │   │   ├── DownloaderDataProvider.cs
│   │   │   │   ├── Enumerators
│   │   │   │   │   ├── AuxiliaryDataEnumerator.cs
│   │   │   │   │   ├── BaseDataCollectionAggregatorEnumerator.cs
│   │   │   │   │   ├── ConcatEnumerator.cs
│   │   │   │   │   ├── DelistingEventProvider.cs
│   │   │   │   │   ├── DividendEventProvider.cs
│   │   │   │   │   ├── EnqueueableEnumerator.cs
│   │   │   │   │   ├── Factories
│   │   │   │   │   │   ├── BaseDataCollectionSubscriptionEnumeratorFactory.cs
│   │   │   │   │   │   ├── CorporateEventEnumeratorFactory.cs
│   │   │   │   │   │   ├── LiveCustomDataSubscriptionEnumeratorFactory.cs
│   │   │   │   │   │   ├── SubscriptionDataReaderSubscriptionEnumeratorFactory.cs
│   │   │   │   │   │   └── TimeTriggeredUniverseSubscriptionEnumeratorFactory.cs
│   │   │   │   │   ├── FastForwardEnumerator.cs
│   │   │   │   │   ├── FillForwardEnumerator.cs
│   │   │   │   │   ├── FilterEnumerator.cs
│   │   │   │   │   ├── FrontierAwareEnumerator.cs
│   │   │   │   │   ├── ITradableDateEventProvider.cs
│   │   │   │   │   ├── ITradableDatesNotifier.cs
│   │   │   │   │   ├── LastPointTracker.cs
│   │   │   │   │   ├── LiveAuxiliaryDataEnumerator.cs
│   │   │   │   │   ├── LiveAuxiliaryDataSynchronizingEnumerator.cs
│   │   │   │   │   ├── LiveDelistingEventProvider.cs
│   │   │   │   │   ├── LiveDividendEventProvider.cs
│   │   │   │   │   ├── LiveFillForwardEnumerator.cs
│   │   │   │   │   ├── LiveMappingEventProvider.cs
│   │   │   │   │   ├── LiveSplitEventProvider.cs
│   │   │   │   │   ├── LiveSubscriptionEnumerator.cs
│   │   │   │   │   ├── MappingEventProvider.cs
│   │   │   │   │   ├── NewDataAvailableEventArgs.cs
│   │   │   │   │   ├── PriceScaleFactorEnumerator.cs
│   │   │   │   │   ├── QuoteBarFillForwardEnumerator.cs
│   │   │   │   │   ├── RateLimitEnumerator.cs
│   │   │   │   │   ├── RefreshEnumerator.cs
│   │   │   │   │   ├── ScannableEnumerator.cs
│   │   │   │   │   ├── ScheduledEnumerator.cs
│   │   │   │   │   ├── SortEnumerator.cs
│   │   │   │   │   ├── SplitEventProvider.cs
│   │   │   │   │   ├── StrictDailyEndTimesEnumerator.cs
│   │   │   │   │   ├── SubscriptionDataEnumerator.cs
│   │   │   │   │   ├── SubscriptionFilterEnumerator.cs
│   │   │   │   │   ├── SynchronizingBaseDataEnumerator.cs
│   │   │   │   │   ├── SynchronizingEnumerator.cs
│   │   │   │   │   └── SynchronizingSliceEnumerator.cs
│   │   │   │   ├── FileSystemDataFeed.cs
│   │   │   │   ├── FillForwardResolutionChangedEvent.cs
│   │   │   │   ├── IDataFeed.cs
│   │   │   │   ├── IDataFeedSubscriptionManager.cs
│   │   │   │   ├── IDataFeedTimeProvider.cs
│   │   │   │   ├── IDataManager.cs
│   │   │   │   ├── IndexSubscriptionDataSourceReader.cs
│   │   │   │   ├── InternalSubscriptionManager.cs
│   │   │   │   ├── InvalidSourceEventArgs.cs
│   │   │   │   ├── ISubscriptionDataSourceReader.cs
│   │   │   │   ├── ISubscriptionSynchronizer.cs
│   │   │   │   ├── ISynchronizer.cs
│   │   │   │   ├── LiveFutureChainProvider.cs
│   │   │   │   ├── LiveOptionChainProvider.cs
│   │   │   │   ├── LiveSynchronizer.cs
│   │   │   │   ├── LiveTimeProvider.cs
│   │   │   │   ├── LiveTradingDataFeed.cs
│   │   │   │   ├── ManualTimeProvider.cs
│   │   │   │   ├── NullDataFeed.cs
│   │   │   │   ├── PendingRemovalsManager.cs
│   │   │   │   ├── PrecalculatedSubscriptionData.cs
│   │   │   │   ├── PredicateTimeProvider.cs
│   │   │   │   ├── ProcessedDataProvider.cs
│   │   │   │   ├── Queues
│   │   │   │   │   ├── DataQueue.cs
│   │   │   │   │   └── FakeDataQueue.cs
│   │   │   │   ├── ReaderErrorEventArgs.cs
│   │   │   │   ├── RealTimeScheduleEventService.cs
│   │   │   │   ├── SingleEntryDataCacheProvider.cs
│   │   │   │   ├── Subscription.cs
│   │   │   │   ├── SubscriptionCollection.cs
│   │   │   │   ├── SubscriptionData.cs
│   │   │   │   ├── SubscriptionDataReader.cs
│   │   │   │   ├── SubscriptionDataSourceReader.cs
│   │   │   │   ├── SubscriptionFrontierTimeProvider.cs
│   │   │   │   ├── SubscriptionSynchronizer.cs
│   │   │   │   ├── SubscriptionUtils.cs
│   │   │   │   ├── Synchronizer.cs
│   │   │   │   ├── TextSubscriptionDataSourceReader.cs
│   │   │   │   ├── TimeSlice.cs
│   │   │   │   ├── TimeSliceFactory.cs
│   │   │   │   ├── Transport
│   │   │   │   │   ├── LocalFileSubscriptionStreamReader.cs
│   │   │   │   │   ├── ObjectStoreSubscriptionStreamReader.cs
│   │   │   │   │   ├── RemoteFileSubscriptionStreamReader.cs
│   │   │   │   │   └── RestSubscriptionStreamReader.cs
│   │   │   │   ├── UniverseSelection.cs
│   │   │   │   ├── UpdateData.cs
│   │   │   │   ├── WorkScheduling
│   │   │   │   │   ├── BaseWorkScheduler.cs
│   │   │   │   │   ├── WeightedWorkQueue.cs
│   │   │   │   │   ├── WeightedWorkScheduler.cs
│   │   │   │   │   └── WorkItem.cs
│   │   │   │   ├── ZipDataCacheProvider.cs
│   │   │   │   └── ZipEntryNameSubscriptionDataSourceReader.cs
│   │   │   ├── Engine.cs
│   │   │   ├── HistoricalData
│   │   │   │   ├── BrokerageHistoryProvider.cs
│   │   │   │   ├── FakeHistoryProvider.cs
│   │   │   │   ├── HistoryProviderManager.cs
│   │   │   │   ├── MappedSynchronizingHistoryProvider.cs
│   │   │   │   ├── SineHistoryProvider.cs
│   │   │   │   ├── SubscriptionDataReaderHistoryProvider.cs
│   │   │   │   └── SynchronizingHistoryProvider.cs
│   │   │   ├── Initializer.cs
│   │   │   ├── LeanEngineAlgorithmHandlers.cs
│   │   │   ├── LeanEngineSystemHandlers.cs
│   │   │   ├── Properties
│   │   │   │   └── AssemblyInfo.cs
│   │   │   ├── QuantConnect.Lean.Engine.csproj
│   │   │   ├── RealTime
│   │   │   │   ├── BacktestingRealTimeHandler.cs
│   │   │   │   ├── BaseRealTimeHandler.cs
│   │   │   │   ├── IRealTimeHandler.cs
│   │   │   │   ├── LiveTradingRealTimeHandler.cs
│   │   │   │   └── ScheduledEventFactory.cs
│   │   │   ├── Results
│   │   │   │   ├── Analysis
│   │   │   │   │   ├── AlgorithmSpeedSample.cs
│   │   │   │   │   ├── AlgorithmSpeedTracker.cs
│   │   │   │   │   ├── Analyses
│   │   │   │   │   │   ├── AlgorithmSpeedAnalysis.cs
│   │   │   │   │   │   ├── BaseResultsAnalysis.cs
│   │   │   │   │   │   ├── CrisisEventsAnalysis.cs
│   │   │   │   │   │   ├── FlatEquityCurveAnalysis.cs
│   │   │   │   │   │   ├── InsightsEmittedForDelistedSecuritiesAnalysis.cs
│   │   │   │   │   │   ├── MarginCallsAnalysis.cs
│   │   │   │   │   │   ├── Messages
│   │   │   │   │   │   │   ├── AlpacaBrokerageModel
│   │   │   │   │   │   │   │   └── TradingOutsideRegularHoursNotSupportedAnalysis.cs
│   │   │   │   │   │   │   ├── BinanceBrokerageModel
│   │   │   │   │   │   │   │   └── UnsupportedOrderTypeWithLinkToSupportedTypesAnalysis.cs
│   │   │   │   │   │   │   ├── CoinbaseBrokerageModel
│   │   │   │   │   │   │   │   └── StopMarketOrdersNoLongerSupportedAnalysis.cs
│   │   │   │   │   │   │   ├── DefaultBrokerageModel
│   │   │   │   │   │   │   │   ├── InvalidOrderQuantityAnalysis.cs
│   │   │   │   │   │   │   │   ├── InvalidOrderSizeAnalysis.cs
│   │   │   │   │   │   │   │   ├── NoDataForSymbolAnalysis.cs
│   │   │   │   │   │   │   │   ├── OrderUpdateNotSupportedAnalysis.cs
│   │   │   │   │   │   │   │   ├── UnsupportedCrossZeroByOrderTypeAnalysis.cs
│   │   │   │   │   │   │   │   ├── UnsupportedCrossZeroOrderUpdateAnalysis.cs
│   │   │   │   │   │   │   │   ├── UnsupportedMarketOnOpenOrdersForFutureAndFutureOptionsAnalysis.cs
│   │   │   │   │   │   │   │   ├── UnsupportedMarketOnOpenOrderTimeAnalysis.cs
│   │   │   │   │   │   │   │   ├── UnsupportedOrderTypeAnalysis.cs
│   │   │   │   │   │   │   │   ├── UnsupportedSecurityTypeAnalysis.cs
│   │   │   │   │   │   │   │   ├── UnsupportedTimeInForceAnalysis.cs
│   │   │   │   │   │   │   │   └── UnsupportedUpdateQuantityOrderAnalysis.cs
│   │   │   │   │   │   │   ├── InteractiveBrokersBrokerageModel
│   │   │   │   │   │   │   │   ├── InvalidForexOrderSizeAnalysis.cs
│   │   │   │   │   │   │   │   └── UnsupportedExerciseForIndexAndCashSettledOptionsAnalysis.cs
│   │   │   │   │   │   │   ├── MessageAnalysis.cs
│   │   │   │   │   │   │   ├── RbiBrokerageModel
│   │   │   │   │   │   │   │   └── RbiUnsupportedOrderTypeAnalysis.cs
│   │   │   │   │   │   │   ├── TradierBrokerageModel
│   │   │   │   │   │   │   │   ├── ExtendedMarketHoursTradingNotSupportedOutsideExtendedSessionAnalysis.cs
│   │   │   │   │   │   │   │   ├── IncorrectOrderQuantityAnalysis.cs
│   │   │   │   │   │   │   │   ├── SellShortOrderLastPriceBelow5Analysis.cs
│   │   │   │   │   │   │   │   ├── ShortOrderIsGtcAnalysis.cs
│   │   │   │   │   │   │   │   ├── TradierUnsupportedSecurityTypeAnalysis.cs
│   │   │   │   │   │   │   │   └── UnsupportedTimeInForceTypeAnalysis.cs
│   │   │   │   │   │   │   ├── TradingTechnologiesBrokerageModel
│   │   │   │   │   │   │   │   ├── InvalidStopLimitOrderLimitPriceAnalysis.cs
│   │   │   │   │   │   │   │   ├── InvalidStopLimitOrderPriceAnalysis.cs
│   │   │   │   │   │   │   │   └── InvalidStopMarketOrderPriceAnalysis.cs
│   │   │   │   │   │   │   └── WolverineBrokerageModel
│   │   │   │   │   │   │       └── WolverineUnsupportedOrderTypeAnalysis.cs
│   │   │   │   │   │   ├── MonteCarloPercentileAnalysis.cs
│   │   │   │   │   │   ├── OrderFillsDuringExtendedMarketHoursAnalysis.cs
│   │   │   │   │   │   ├── OrderResponseErrorsAnalyses
│   │   │   │   │   │   │   ├── AlgorithmWarmingUpOrderResponseErrorAnalysis.cs
│   │   │   │   │   │   │   ├── BrokerageModelRefusedToSubmitOrderOrderResponseErrorAnalysis.cs
│   │   │   │   │   │   │   ├── BrokerageModelRefusedToUpdateOrderOrderResponseErrorAnalysis.cs
│   │   │   │   │   │   │   ├── EuropeanOptionNotExpiredOnExerciseOrderResponseErrorAnalysis.cs
│   │   │   │   │   │   │   ├── ExceededMaximumOrdersOrderResponseErrorAnalysis.cs
│   │   │   │   │   │   │   ├── ExceedsShortableQuantityOrderResponseErrorAnalysis.cs
│   │   │   │   │   │   │   ├── ExchangeNotOpenOrderResponseErrorAnalysis.cs
│   │   │   │   │   │   │   ├── ForexConversionRateZeroOrderResponseErrorAnalysis.cs
│   │   │   │   │   │   │   ├── InsufficientBuyingPowerOrderResponseErrorAnalysis.cs
│   │   │   │   │   │   │   ├── MarketOnCloseOrderTooLateOrderResponseErrorAnalysis.cs
│   │   │   │   │   │   │   ├── MarketOnOpenNotAllowedDuringRegularHoursOrderResponseErrorAnalysis.cs
│   │   │   │   │   │   │   ├── NonTradableSecurityOrderResponseErrorAnalysis.cs
│   │   │   │   │   │   │   ├── OptionOrderOnStockSplitOrderResponseErrorAnalysis.cs
│   │   │   │   │   │   │   ├── OrderQuantityLessThanLotSizeOrderResponseErrorAnalysis.cs
│   │   │   │   │   │   │   ├── OrderQuantityZeroOrderResponseErrorAnalysis.cs
│   │   │   │   │   │   │   ├── OrderResponseErrorAnalysis.cs
│   │   │   │   │   │   │   ├── SecurityPriceZeroOrderResponseErrorAnalysis.cs
│   │   │   │   │   │   │   ├── UnsupportedOptionExerciseQuantityAnalysis.cs
│   │   │   │   │   │   │   └── UnsupportedOptionShortPositionExerciseAnalysis.cs
│   │   │   │   │   │   ├── ParameterCountAnalysis.cs
│   │   │   │   │   │   ├── PerformanceRelativeToBenchmarkAnalysis.cs
│   │   │   │   │   │   ├── PortfolioMarginUsageAnalysis.cs
│   │   │   │   │   │   ├── PortfolioValueIsNotPositiveAnalysis.cs
│   │   │   │   │   │   ├── SingleTimeLoopTimeoutRuntimeErrorAnalysis.cs
│   │   │   │   │   │   ├── StaleOrderFillsAnalysis.cs
│   │   │   │   │   │   ├── StatisticalSignificanceOfDailyReturnsAnalysis.cs
│   │   │   │   │   │   └── TakeProfitAndStopLossOrdersAnalysis.cs
│   │   │   │   │   ├── ResultsAnalysisRunParameters.cs
│   │   │   │   │   └── ResultsAnalyzer.cs
│   │   │   │   ├── BacktestingResultHandler.cs
│   │   │   │   ├── BacktestProgressMonitor.cs
│   │   │   │   ├── BaseResultsHandler.cs
│   │   │   │   ├── IResultHandler.cs
│   │   │   │   ├── LiveTradingResultHandler.cs
│   │   │   │   ├── RegressionResultHandler.cs
│   │   │   │   └── ResultHandlerInitializeParameters.cs
│   │   │   ├── Server
│   │   │   │   ├── ILeanManager.cs
│   │   │   │   └── LocalLeanManager.cs
│   │   │   ├── Setup
│   │   │   │   ├── AlgorithmSetupException.cs
│   │   │   │   ├── BacktestingSetupHandler.cs
│   │   │   │   ├── BaseSetupHandler.cs
│   │   │   │   ├── BrokerageSetupHandler.cs
│   │   │   │   ├── ConsoleSetupHandler.cs
│   │   │   │   ├── ISetupHandler.cs
│   │   │   │   └── SetupHandlerParameters.cs
│   │   │   ├── Storage
│   │   │   │   ├── FileHandler.cs
│   │   │   │   ├── LocalObjectStore.cs
│   │   │   │   └── StorageLimitExceededException.cs
│   │   │   └── TransactionHandlers
│   │   │       ├── BacktestingTransactionHandler.cs
│   │   │       ├── BrokerageTransactionHandler.cs
│   │   │       ├── CancelPendingOrders.cs
│   │   │       ├── ITransactionHandler.cs
│   │   │       └── OrderRequestProcessingPool.cs
│   │   ├── find_datasource_repos.py
│   │   ├── google9161359af9633398.html
│   │   ├── Indicators
│   │   │   ├── AbsolutePriceOscillator.cs
│   │   │   ├── AccelerationBands.cs
│   │   │   ├── AccumulationDistribution.cs
│   │   │   ├── AccumulationDistributionOscillator.cs
│   │   │   ├── AdvanceDeclineDifference.cs
│   │   │   ├── AdvanceDeclineIndicator.cs
│   │   │   ├── AdvanceDeclineRatio.cs
│   │   │   ├── AdvanceDeclineVolumeRatio.cs
│   │   │   ├── Alpha.cs
│   │   │   ├── ArmsIndex.cs
│   │   │   ├── ArnaudLegouxMovingAverage.cs
│   │   │   ├── AroonOscillator.cs
│   │   │   ├── AugenPriceSpike.cs
│   │   │   ├── AutoRegressiveIntegratedMovingAverage.cs
│   │   │   ├── AverageDirectionalIndex.cs
│   │   │   ├── AverageDirectionalMovementIndexRating.cs
│   │   │   ├── AverageRange.cs
│   │   │   ├── AverageTrueRange.cs
│   │   │   ├── AwesomeOscillator.cs
│   │   │   ├── BalanceOfPower.cs
│   │   │   ├── BarIndicator.cs
│   │   │   ├── Beta.cs
│   │   │   ├── BollingerBands.cs
│   │   │   ├── CandlestickPatterns
│   │   │   │   ├── AbandonedBaby.cs
│   │   │   │   ├── AdvanceBlock.cs
│   │   │   │   ├── BeltHold.cs
│   │   │   │   ├── Breakaway.cs
│   │   │   │   ├── CandleEnums.cs
│   │   │   │   ├── CandleSettings.cs
│   │   │   │   ├── CandlestickPattern.cs
│   │   │   │   ├── ClosingMarubozu.cs
│   │   │   │   ├── ConcealedBabySwallow.cs
│   │   │   │   ├── Counterattack.cs
│   │   │   │   ├── DarkCloudCover.cs
│   │   │   │   ├── Doji.cs
│   │   │   │   ├── DojiStar.cs
│   │   │   │   ├── DragonflyDoji.cs
│   │   │   │   ├── Engulfing.cs
│   │   │   │   ├── EveningDojiStar.cs
│   │   │   │   ├── EveningStar.cs
│   │   │   │   ├── GapSideBySideWhite.cs
│   │   │   │   ├── GravestoneDoji.cs
│   │   │   │   ├── Hammer.cs
│   │   │   │   ├── HangingMan.cs
│   │   │   │   ├── Harami.cs
│   │   │   │   ├── HaramiCross.cs
│   │   │   │   ├── HighWaveCandle.cs
│   │   │   │   ├── Hikkake.cs
│   │   │   │   ├── HikkakeModified.cs
│   │   │   │   ├── HomingPigeon.cs
│   │   │   │   ├── IdenticalThreeCrows.cs
│   │   │   │   ├── InNeck.cs
│   │   │   │   ├── InvertedHammer.cs
│   │   │   │   ├── Kicking.cs
│   │   │   │   ├── KickingByLength.cs
│   │   │   │   ├── LadderBottom.cs
│   │   │   │   ├── LongLeggedDoji.cs
│   │   │   │   ├── LongLineCandle.cs
│   │   │   │   ├── Marubozu.cs
│   │   │   │   ├── MatchingLow.cs
│   │   │   │   ├── MatHold.cs
│   │   │   │   ├── MorningDojiStar.cs
│   │   │   │   ├── MorningStar.cs
│   │   │   │   ├── OnNeck.cs
│   │   │   │   ├── Piercing.cs
│   │   │   │   ├── RickshawMan.cs
│   │   │   │   ├── RiseFallThreeMethods.cs
│   │   │   │   ├── SeparatingLines.cs
│   │   │   │   ├── ShootingStar.cs
│   │   │   │   ├── ShortLineCandle.cs
│   │   │   │   ├── SpinningTop.cs
│   │   │   │   ├── StalledPattern.cs
│   │   │   │   ├── StickSandwich.cs
│   │   │   │   ├── Takuri.cs
│   │   │   │   ├── TasukiGap.cs
│   │   │   │   ├── ThreeBlackCrows.cs
│   │   │   │   ├── ThreeInside.cs
│   │   │   │   ├── ThreeLineStrike.cs
│   │   │   │   ├── ThreeOutside.cs
│   │   │   │   ├── ThreeStarsInSouth.cs
│   │   │   │   ├── ThreeWhiteSoldiers.cs
│   │   │   │   ├── Thrusting.cs
│   │   │   │   ├── Tristar.cs
│   │   │   │   ├── TwoCrows.cs
│   │   │   │   ├── UniqueThreeRiver.cs
│   │   │   │   ├── UpDownGapThreeMethods.cs
│   │   │   │   └── UpsideGapTwoCrows.cs
│   │   │   ├── ChaikinMoneyFlow.cs
│   │   │   ├── ChaikinOscillator.cs
│   │   │   ├── ChandeKrollStop.cs
│   │   │   ├── ChandeMomentumOscillator.cs
│   │   │   ├── ChoppinessIndex.cs
│   │   │   ├── CommodityChannelIndex.cs
│   │   │   ├── CompositeIndicator.cs
│   │   │   ├── ConnorsRelativeStrengthIndex.cs
│   │   │   ├── ConstantIndicator.cs
│   │   │   ├── CoppockCurve.cs
│   │   │   ├── Correlation.cs
│   │   │   ├── CorrelationType.cs
│   │   │   ├── Covariance.cs
│   │   │   ├── Delay.cs
│   │   │   ├── Delta.cs
│   │   │   ├── DeMarkerIndicator.cs
│   │   │   ├── DerivativeOscillator.cs
│   │   │   ├── DetrendedPriceOscillator.cs
│   │   │   ├── DonchianChannel.cs
│   │   │   ├── DoubleExponentialMovingAverage.cs
│   │   │   ├── DualSymbolIndicator.cs
│   │   │   ├── EaseOfMovementValue.cs
│   │   │   ├── ExponentialMovingAverage.cs
│   │   │   ├── FilteredIdentity.cs
│   │   │   ├── FisherTransform.cs
│   │   │   ├── ForceIndex.cs
│   │   │   ├── FractalAdaptiveMovingAverage.cs
│   │   │   ├── FunctionalIndicator.cs
│   │   │   ├── Gamma.cs
│   │   │   ├── GreeksIndicators.cs
│   │   │   ├── HeikinAshi.cs
│   │   │   ├── HilbertTransform.cs
│   │   │   ├── HullMovingAverage.cs
│   │   │   ├── HurstExponent.cs
│   │   │   ├── IchimokuKinkoHyo.cs
│   │   │   ├── Identity.cs
│   │   │   ├── ImpliedVolatility.cs
│   │   │   ├── Indicator.cs
│   │   │   ├── IndicatorBase.cs
│   │   │   ├── IndicatorBase.Operators.cs
│   │   │   ├── IndicatorBasedOptionPriceModel.cs
│   │   │   ├── IndicatorBasedOptionPriceModelProvider.cs
│   │   │   ├── IndicatorExtensions.cs
│   │   │   ├── IndicatorResult.cs
│   │   │   ├── IndicatorStatus.cs
│   │   │   ├── InternalBarStrength.cs
│   │   │   ├── IntradayVwap.cs
│   │   │   ├── KaufmanAdaptiveMovingAverage.cs
│   │   │   ├── KaufmanEfficiencyRatio.cs
│   │   │   ├── KeltnerChannels.cs
│   │   │   ├── KlingerVolumeOscillator.cs
│   │   │   ├── KnowSureThing.cs
│   │   │   ├── LeastSquaresMovingAverage.cs
│   │   │   ├── LinearWeightedMovingAverage.cs
│   │   │   ├── LogReturn.cs
│   │   │   ├── MarketProfile.cs
│   │   │   ├── MassIndex.cs
│   │   │   ├── Maximum.cs
│   │   │   ├── McClellanOscillator.cs
│   │   │   ├── McClellanSummationIndex.cs
│   │   │   ├── McGinleyDynamic.cs
│   │   │   ├── MeanAbsoluteDeviation.cs
│   │   │   ├── MesaAdaptiveMovingAverage.cs
│   │   │   ├── MidPoint.cs
│   │   │   ├── MidPrice.cs
│   │   │   ├── Minimum.cs
│   │   │   ├── Momentum.cs
│   │   │   ├── MomentumPercent.cs
│   │   │   ├── Momersion.cs
│   │   │   ├── MomersionIndicator.cs
│   │   │   ├── MoneyFlowIndex.cs
│   │   │   ├── MovingAverageConvergenceDivergence.cs
│   │   │   ├── MovingAverageType.cs
│   │   │   ├── MovingAverageTypeExtensions.cs
│   │   │   ├── MultiSymbolIndicator.cs
│   │   │   ├── NewHighsNewLows.cs
│   │   │   ├── NewHighsNewLowsVolume.cs
│   │   │   ├── NormalizedAverageTrueRange.cs
│   │   │   ├── OnBalanceVolume.cs
│   │   │   ├── OptionGreekIndicatorBase.cs
│   │   │   ├── OptionGreekIndicatorsHelper.cs
│   │   │   ├── OptionIndicatorBase.cs
│   │   │   ├── ParabolicStopAndReverse.cs
│   │   │   ├── ParabolicStopAndReverseExtended.cs
│   │   │   ├── PercentagePriceOscillator.cs
│   │   │   ├── PivotPointsHighLow.cs
│   │   │   ├── PremierStochasticOscillator.cs
│   │   │   ├── Properties
│   │   │   │   └── AssemblyInfo.cs
│   │   │   ├── PythonIndicator.cs
│   │   │   ├── QuantConnect.Indicators.csproj
│   │   │   ├── RateOfChange.cs
│   │   │   ├── RateOfChangePercent.cs
│   │   │   ├── RateOfChangeRatio.cs
│   │   │   ├── RegressionChannel.cs
│   │   │   ├── RelativeDailyVolume.cs
│   │   │   ├── RelativeMovingAverage.cs
│   │   │   ├── RelativeStrengthIndex.cs
│   │   │   ├── RelativeVigorIndex.cs
│   │   │   ├── RelativeVigorIndexSignal.cs
│   │   │   ├── ResetCompositeIndicator.cs
│   │   │   ├── Rho.cs
│   │   │   ├── RogersSatchellVolatility.cs
│   │   │   ├── SchaffTrendCycle.cs
│   │   │   ├── SharpeRatio.cs
│   │   │   ├── SimpleMovingAverage.cs
│   │   │   ├── SmoothedOnBalanceVolume.cs
│   │   │   ├── SortinoRatio.cs
│   │   │   ├── SqueezeMomentum.cs
│   │   │   ├── StandardDeviation.cs
│   │   │   ├── Stochastic.cs
│   │   │   ├── StochasticRelativeStrengthIndex.cs
│   │   │   ├── Sum.cs
│   │   │   ├── SuperTrend.cs
│   │   │   ├── SwissArmyKnife.cs
│   │   │   ├── T3MovingAverage.cs
│   │   │   ├── TargetDownsideDeviation.cs
│   │   │   ├── Theta.cs
│   │   │   ├── TimeProfile.cs
│   │   │   ├── TimeSeriesForecast.cs
│   │   │   ├── TimeSeriesIndicator.cs
│   │   │   ├── TomDemarkSequential.cs
│   │   │   ├── TradeBarIndicator.cs
│   │   │   ├── TriangularMovingAverage.cs
│   │   │   ├── TripleExponentialMovingAverage.cs
│   │   │   ├── Trix.cs
│   │   │   ├── TrueRange.cs
│   │   │   ├── TrueStrengthIndex.cs
│   │   │   ├── UltimateOscillator.cs
│   │   │   ├── ValueAtRisk.cs
│   │   │   ├── VariableIndexDynamicAverage.cs
│   │   │   ├── Variance.cs
│   │   │   ├── Vega.cs
│   │   │   ├── VolumeProfile.cs
│   │   │   ├── VolumeWeightedAveragePriceIndicator.cs
│   │   │   ├── VolumeWeightedMovingAverage.cs
│   │   │   ├── Vortex.cs
│   │   │   ├── WaveTrendOscillator.cs
│   │   │   ├── WilderAccumulativeSwingIndex.cs
│   │   │   ├── WilderMovingAverage.cs
│   │   │   ├── WilderSwingIndex.cs
│   │   │   ├── WilliamsPercentR.cs
│   │   │   ├── WindowIdentity.cs
│   │   │   ├── WindowIndicator.cs
│   │   │   ├── ZeroLagExponentialMovingAverage.cs
│   │   │   └── ZigZag.cs
│   │   ├── Launcher
│   │   │   ├── config.json
│   │   │   ├── Program.cs
│   │   │   ├── Properties
│   │   │   │   └── AssemblyInfo.cs
│   │   │   └── QuantConnect.Lean.Launcher.csproj
│   │   ├── lean.ico
│   │   ├── LICENSE
│   │   ├── LocalPackages
│   │   │   └── readme.md
│   │   ├── Logging
│   │   │   ├── CompositeLogHandler.cs
│   │   │   ├── ConsoleErrorLogHandler.cs
│   │   │   ├── ConsoleLogHandler.cs
│   │   │   ├── FileLogHandler.cs
│   │   │   ├── FunctionalLogHandler.cs
│   │   │   ├── ILogHandler.cs
│   │   │   ├── ILogHandlerExtensions.cs
│   │   │   ├── Log.cs
│   │   │   ├── LogEntry.cs
│   │   │   ├── LogType.cs
│   │   │   ├── Properties
│   │   │   │   └── AssemblyInfo.cs
│   │   │   ├── QuantConnect.Logging.csproj
│   │   │   ├── QueueLogHandler.cs
│   │   │   ├── RegressionFileLogHandler.cs
│   │   │   └── WhoCalledMe.cs
│   │   ├── Messaging
│   │   │   ├── EventMessagingHandler.cs
│   │   │   ├── Messaging.cs
│   │   │   ├── Properties
│   │   │   │   └── AssemblyInfo.cs
│   │   │   ├── QuantConnect.Messaging.csproj
│   │   │   └── StreamingMessageHandler.cs
│   │   ├── mypy.ini
│   │   ├── Optimizer
│   │   │   ├── Analysis
│   │   │   │   ├── OptimizationAnalyzer.cs
│   │   │   │   ├── OptimizationClustering.cs
│   │   │   │   ├── OptimizationFailedBacktests.cs
│   │   │   │   ├── OptimizationModes.cs
│   │   │   │   └── OptimizationSlicing.cs
│   │   │   ├── LeanOptimizer.cs
│   │   │   ├── OptimizationNodePacket.cs
│   │   │   ├── OptimizationResult.cs
│   │   │   ├── Parameters
│   │   │   │   ├── OptimizationParameterEnumerator.cs
│   │   │   │   └── OptimizationStepParameterEnumerator.cs
│   │   │   ├── Properties
│   │   │   │   └── AssemblyInfo.cs
│   │   │   ├── QuantConnect.Optimizer.csproj
│   │   │   └── Strategies
│   │   │       ├── EulerSearchOptimizationStrategy.cs
│   │   │       ├── GridSearchOptimizationStrategy.cs
│   │   │       ├── IOptimizationStrategy.cs
│   │   │       ├── OptimizationStrategySettings.cs
│   │   │       ├── StepBaseOptimizationStrategy.cs
│   │   │       └── StepBaseOptimizationStrategySettings.cs
│   │   ├── Optimizer.Launcher
│   │   │   ├── config.example.json
│   │   │   ├── ConsoleLeanOptimizer.cs
│   │   │   ├── Program.cs
│   │   │   ├── Properties
│   │   │   │   └── AssemblyInfo.cs
│   │   │   └── QuantConnect.Optimizer.Launcher.csproj
│   │   ├── QuantConnect.Lean.sln
│   │   ├── QuantConnect.Lean.sln.DotSettings
│   │   ├── Queues
│   │   │   ├── JobQueue.cs
│   │   │   ├── Properties
│   │   │   │   └── AssemblyInfo.cs
│   │   │   └── QuantConnect.Queues.csproj
│   │   ├── readme.md
│   │   ├── rebase_organization_branches.sh
│   │   ├── Report
│   │   │   ├── config.example.json
│   │   │   ├── Crisis.cs
│   │   │   ├── CrisisEvent.cs
│   │   │   ├── css
│   │   │   │   ├── report_override.css
│   │   │   │   └── report.css
│   │   │   ├── DeedleUtil.cs
│   │   │   ├── DrawdownCollection.cs
│   │   │   ├── DrawdownPeriod.cs
│   │   │   ├── Metrics.cs
│   │   │   ├── NullResultValueTypeJsonConverter.cs
│   │   │   ├── OrderTypeNormalizingJsonConverter.cs
│   │   │   ├── PointInTimePortfolio.cs
│   │   │   ├── PortfolioLooper
│   │   │   │   ├── MockDataFeed.cs
│   │   │   │   ├── PortfolioLooper.cs
│   │   │   │   └── PortfolioLooperAlgorithm.cs
│   │   │   ├── Program.cs
│   │   │   ├── Properties
│   │   │   │   └── AssemblyInfo.cs
│   │   │   ├── QuantConnect.Report.csproj
│   │   │   ├── Report.cs
│   │   │   ├── ReportCharts.py
│   │   │   ├── ReportChartTests.py
│   │   │   ├── ReportElements
│   │   │   │   ├── AnnualReturnsReportElement.cs
│   │   │   │   ├── AssetAllocationReportElement.cs
│   │   │   │   ├── CAGRReportElement.cs
│   │   │   │   ├── ChartReportElement.cs
│   │   │   │   ├── CrisisReportElement.cs
│   │   │   │   ├── CumulativeReturnsReportElement.cs
│   │   │   │   ├── DailyReturnsReportElement.cs
│   │   │   │   ├── DrawdownReportElement.cs
│   │   │   │   ├── EstimatedCapacityReportElement.cs
│   │   │   │   ├── ExposureReportElement.cs
│   │   │   │   ├── InformationRatioReportElement.cs
│   │   │   │   ├── IReportElement.cs
│   │   │   │   ├── LeverageUtilizationReportElement.cs
│   │   │   │   ├── MarketsReportElement.cs
│   │   │   │   ├── MaxDrawdownRecoveryReportElement.cs
│   │   │   │   ├── MaxDrawdownReportElement.cs
│   │   │   │   ├── MonthlyReturnsReportElement.cs
│   │   │   │   ├── ParametersReportElement.cs
│   │   │   │   ├── PSRReportElement.cs
│   │   │   │   ├── ReportElement.cs
│   │   │   │   ├── ReturnsPerTradeReportElement.cs
│   │   │   │   ├── RollingPortfolioBetaReportElement.cs
│   │   │   │   ├── RollingSharpeReportElement.cs
│   │   │   │   ├── RuntimeDaysReportElement.cs
│   │   │   │   ├── SharpeRatioReportElement.cs
│   │   │   │   ├── SortinoRatioReportElement.cs
│   │   │   │   ├── TextReportElement.cs
│   │   │   │   ├── TradesPerDayReportElement.cs
│   │   │   │   └── TurnoverReportElement.cs
│   │   │   ├── ReportKey.cs
│   │   │   ├── ResultsUtil.cs
│   │   │   ├── Rolling.cs
│   │   │   └── template.html
│   │   ├── Research
│   │   │   ├── BasicCSharpQuantBookTemplate.ipynb
│   │   │   ├── BasicQuantBookTemplate.ipynb
│   │   │   ├── docker.cfg
│   │   │   ├── FutureHistory.cs
│   │   │   ├── Initialize.csx
│   │   │   ├── KitchenSinkCSharpQuantBookTemplate.ipynb
│   │   │   ├── KitchenSinkQuantBookTemplate.ipynb
│   │   │   ├── OptionHistory.cs
│   │   │   ├── Properties
│   │   │   │   └── AssemblyInfo.cs
│   │   │   ├── QuantBook.cs
│   │   │   ├── QuantConnect.csx
│   │   │   ├── QuantConnect.Research.csproj
│   │   │   ├── readme.md
│   │   │   └── start.py
│   │   ├── run_benchmarks.py
│   │   ├── run_syntax_check.py
│   │   ├── Tests
│   │   │   ├── Algorithm
│   │   │   │   ├── AlgorithmAddDataTests.cs
│   │   │   │   ├── AlgorithmAddSecurityTests.cs
│   │   │   │   ├── AlgorithmAddUniverseTests.cs
│   │   │   │   ├── AlgorithmBenchmarkTests.cs
│   │   │   │   ├── AlgorithmChainsTests.cs
│   │   │   │   ├── AlgorithmDownloadTests.cs
│   │   │   │   ├── AlgorithmGetParameterTests.cs
│   │   │   │   ├── AlgorithmHistoryTests.cs
│   │   │   │   ├── AlgorithmIndicatorsTests.cs
│   │   │   │   ├── AlgorithmInitializeTests.cs
│   │   │   │   ├── AlgorithmLiveTradingTests.cs
│   │   │   │   ├── AlgorithmNamingTests.cs
│   │   │   │   ├── AlgorithmPlottingTests.cs
│   │   │   │   ├── AlgorithmRegisterIndicatorTests.cs
│   │   │   │   ├── AlgorithmResolveConsolidatorTests.cs
│   │   │   │   ├── AlgorithmSetBrokerageTests.cs
│   │   │   │   ├── AlgorithmSetHoldingsTests.cs
│   │   │   │   ├── AlgorithmSettingsTest.cs
│   │   │   │   ├── AlgorithmSubscriptionManagerRemoveConsolidatorTests.cs
│   │   │   │   ├── AlgorithmTradingTests.cs
│   │   │   │   ├── AlgorithmUniverseSettingsTests.cs
│   │   │   │   ├── AlgorithmWarmupTests.cs
│   │   │   │   ├── CashModelAlgorithmTradingTests.cs
│   │   │   │   ├── Framework
│   │   │   │   │   ├── Alphas
│   │   │   │   │   │   ├── BasePairsTradingAlphaModelTests.cs
│   │   │   │   │   │   ├── CommonAlphaModelTests.cs
│   │   │   │   │   │   ├── ConstantAlphaModelTests.cs
│   │   │   │   │   │   ├── EmaCrossAlphaModelTests.cs
│   │   │   │   │   │   ├── InsightCollectionTests.cs
│   │   │   │   │   │   ├── InsightManagerTests.cs
│   │   │   │   │   │   ├── MacdAlphaModelTests.cs
│   │   │   │   │   │   ├── RsiAlphaModelTests.cs
│   │   │   │   │   │   ├── Serialization
│   │   │   │   │   │   │   └── InsightJsonConverterTests.cs
│   │   │   │   │   │   ├── TestEmaCrossAlphaModel.cs
│   │   │   │   │   │   └── TestMacdAlphaModel.cs
│   │   │   │   │   ├── Execution
│   │   │   │   │   │   ├── ImmediateExecutionModelTests.cs
│   │   │   │   │   │   ├── SpreadExecutionModelTests.cs
│   │   │   │   │   │   ├── StandardDeviationExecutionModelTests.cs
│   │   │   │   │   │   └── VolumeWeightedAveragePriceExecutionModelTests.cs
│   │   │   │   │   ├── FrameworkModelsPythonInheritanceTests.cs
│   │   │   │   │   ├── InsightTests.cs
│   │   │   │   │   ├── NotifiedSecurityChangesTests.cs
│   │   │   │   │   ├── Portfolio
│   │   │   │   │   │   ├── AccumulativeInsightPortfolioConstructionModelTests.cs
│   │   │   │   │   │   ├── BaseWeightingPortfolioConstructionModelTests.cs
│   │   │   │   │   │   ├── BlackLittermanOptimizationPortfolioConstructionModelTests.cs
│   │   │   │   │   │   ├── ConfidenceWeightedPortfolioConstructionModelTests.cs
│   │   │   │   │   │   ├── EqualWeightingPortfolioConstructionModelTests.cs
│   │   │   │   │   │   ├── InsightWeightingPortfolioConstructionModelTests.cs
│   │   │   │   │   │   ├── LongOnlyEqualWeightingPortfolioConstructionModelTests.cs
│   │   │   │   │   │   ├── LongOnlyInsightWeightingPortfolioConstructionModelTests.cs
│   │   │   │   │   │   ├── MaximumSharpeRatioPortfolioOptimizerTests.cs
│   │   │   │   │   │   ├── MeanReversionPortfolioConstructionModelTest.cs
│   │   │   │   │   │   ├── MeanVarianceOptimizationPortfolioConstructionModelTests.cs
│   │   │   │   │   │   ├── MinimumVariancePortfolioOptimizerTests.cs
│   │   │   │   │   │   ├── PortfolioConstructionModelPythonWrapperTests.cs
│   │   │   │   │   │   ├── PortfolioConstructionModelTests.cs
│   │   │   │   │   │   ├── PortfolioOptimizerPythonWrapperTests.cs
│   │   │   │   │   │   ├── PortfolioOptimizerTestsBase.cs
│   │   │   │   │   │   ├── PortfolioTargetCollectionTests.cs
│   │   │   │   │   │   ├── PortfolioTargetTests.cs
│   │   │   │   │   │   ├── ReturnsSymbolDataTests.cs
│   │   │   │   │   │   ├── RiskParityPortfolioConstructionModelTests.cs
│   │   │   │   │   │   ├── RiskParityPortfolioOptimizerTests.cs
│   │   │   │   │   │   ├── SectorWeightingPortfolioConstructionModelTests.cs
│   │   │   │   │   │   ├── SignalExportTargetTests.cs
│   │   │   │   │   │   └── UnconstrainedMeanVariancePortfolioOptimizerTests.cs
│   │   │   │   │   ├── QCAlgorithmFrameworkTests.cs
│   │   │   │   │   ├── Risk
│   │   │   │   │   │   ├── MaximumDrawdownPercentPerSecurityTests.cs
│   │   │   │   │   │   ├── MaximumDrawdownPercentPortfolioTests.cs
│   │   │   │   │   │   └── TrailingStopRiskManagementModelTests.cs
│   │   │   │   │   └── Selection
│   │   │   │   │       ├── ETFConstituentsUniverseSelectionModelTests.cs
│   │   │   │   │       ├── ManualUniverseSelectionModelTests.cs
│   │   │   │   │       ├── OpenInterestFutureUniverseSelectionModelTests.cs
│   │   │   │   │       └── QC500UniverseSelectionModelTests.cs
│   │   │   │   └── UniverseDefinitionsTests.cs
│   │   │   ├── AlgorithmFactory
│   │   │   │   └── LoaderTests.cs
│   │   │   ├── AlgorithmRunner.cs
│   │   │   ├── AlgorithmRunnerResults.cs
│   │   │   ├── Api
│   │   │   │   ├── AccountTests.cs
│   │   │   │   ├── ApiTestBase.cs
│   │   │   │   ├── ApiTests.cs
│   │   │   │   ├── AuthenticationTests.cs
│   │   │   │   ├── CommandTests.cs
│   │   │   │   ├── DataTests.cs
│   │   │   │   ├── LiveTradingTests.cs
│   │   │   │   ├── ObjectStoreTests.cs
│   │   │   │   ├── OptimizationBacktestJsonConverterTests.cs
│   │   │   │   ├── OptimizationTests.cs
│   │   │   │   ├── OrganizationTests.cs
│   │   │   │   ├── ParameterSetJsonConverterTests.cs
│   │   │   │   └── ProjectTests.cs
│   │   │   ├── AssemblyInitialize.cs
│   │   │   ├── Brokerages
│   │   │   │   ├── Authentication
│   │   │   │   │   ├── AccessTokenMetaDataResponseTests.cs
│   │   │   │   │   └── TokenHandlerTests.cs
│   │   │   │   ├── BaseOrderTestParameters.cs
│   │   │   │   ├── BrokerageConcurrentMessageHandlerTests.cs
│   │   │   │   ├── BrokerageFactoryTests.cs
│   │   │   │   ├── BrokerageTests.cs
│   │   │   │   ├── ComboLimitOrderTestParameters.cs
│   │   │   │   ├── DefaultBrokerageTests.cs
│   │   │   │   ├── DowngradeErrorCodeToWarningBrokerageMessageHandlerTests.cs
│   │   │   │   ├── Exante
│   │   │   │   │   └── ExanteFeeModelTests.cs
│   │   │   │   ├── Kraken
│   │   │   │   │   ├── KrakenBrokerageModelTests.cs
│   │   │   │   │   └── KrakenFeeModelTests.cs
│   │   │   │   ├── LevelOneOrderBook
│   │   │   │   │   └── LevelOneMarketDataTests.cs
│   │   │   │   ├── LimitIfTouchedOrderTestParameters.cs
│   │   │   │   ├── LimitOrderTestParameters.cs
│   │   │   │   ├── MarketOnCloseOrderTestParameters.cs
│   │   │   │   ├── MarketOnOpenOrderTestParameters.cs
│   │   │   │   ├── MarketOrderTestParameters.cs
│   │   │   │   ├── Models
│   │   │   │   │   └── PaperBrokerageWithManualCashBalance.cs
│   │   │   │   ├── OrderCrossingBrokerageTests.cs
│   │   │   │   ├── OrderProvider.cs
│   │   │   │   ├── OrderTestParameters.cs
│   │   │   │   ├── Paper
│   │   │   │   │   └── PaperBrokerageTests.cs
│   │   │   │   ├── SecurityProvider.cs
│   │   │   │   ├── StopLimitOrderTestParameters.cs
│   │   │   │   ├── StopMarketOrderTestParameters.cs
│   │   │   │   ├── SymbolPropertiesDatabaseSymbolMapperTests.cs
│   │   │   │   ├── Tastytrade
│   │   │   │   │   └── TastytradeFeeModelTests.cs
│   │   │   │   ├── TestHelpers.cs
│   │   │   │   ├── TradeStation
│   │   │   │   │   └── TradeStationBrokerageModelTests.cs
│   │   │   │   └── TrailingStopOrderTestParameters.cs
│   │   │   ├── Common
│   │   │   │   ├── AlgorithmConfigurationTests.cs
│   │   │   │   ├── BaseExtendedDictionaryTests.cs
│   │   │   │   ├── Benchmarks
│   │   │   │   │   └── SecurityBenchmarkTests.cs
│   │   │   │   ├── BinaryComparisonTests.cs
│   │   │   │   ├── BrokerageNameTests.cs
│   │   │   │   ├── Brokerages
│   │   │   │   │   ├── AlpacaBrokerageModelTests.cs
│   │   │   │   │   ├── BinanceBrokerageModelTests.cs
│   │   │   │   │   ├── BinanceUSBrokerageModelTests.cs
│   │   │   │   │   ├── BitfinexBrokerageModelTests.cs
│   │   │   │   │   ├── BloombergFixBrokerageModelTests.cs
│   │   │   │   │   ├── BrokerageModelTests.cs
│   │   │   │   │   ├── BybitBrokerageModelTests.cs
│   │   │   │   │   ├── CoinbaseBrokerageModelTests.cs
│   │   │   │   │   ├── DefaultBrokerageModelTests.cs
│   │   │   │   │   ├── ExanteBrokerageModelTests.cs
│   │   │   │   │   ├── FTXBrokerageModelTests.cs
│   │   │   │   │   ├── FTXUSBrokerageModelTests.cs
│   │   │   │   │   ├── FxcmBrokerageModelTests.cs
│   │   │   │   │   ├── InteractiveBrokersBrokerageModelTests.cs
│   │   │   │   │   ├── InteractiveBrokersFixModelTests.cs
│   │   │   │   │   ├── KrakenBrokerageModelTests.cs
│   │   │   │   │   ├── PublicBrokerageModelTests.cs
│   │   │   │   │   ├── TastytradeBrokerageModelTests.cs
│   │   │   │   │   ├── TerminalLinkBrokerageModelTests.cs
│   │   │   │   │   ├── TradierBrokerageModelTests.cs
│   │   │   │   │   └── WebullBrokerageModelTests.cs
│   │   │   │   ├── CandlestickSeriesTests.cs
│   │   │   │   ├── ChartTests.cs
│   │   │   │   ├── Commands
│   │   │   │   │   ├── BaseCommandTests.cs
│   │   │   │   │   ├── CallbackCommandTests.cs
│   │   │   │   │   ├── FileCommandHandlerTests.cs
│   │   │   │   │   └── OrderCommandTests.cs
│   │   │   │   ├── CurrenciesTests.cs
│   │   │   │   ├── Data
│   │   │   │   │   ├── Auxiliary
│   │   │   │   │   │   ├── AuxiliaryDataSerializationTests.cs
│   │   │   │   │   │   ├── FactorFileRowTests.cs
│   │   │   │   │   │   ├── FactorFileTests.cs
│   │   │   │   │   │   ├── LocalDiskFactorFileProviderTests.cs
│   │   │   │   │   │   ├── LocalDiskMapFileProviderTests.cs
│   │   │   │   │   │   ├── LocalZipFactorFileProviderTests.cs
│   │   │   │   │   │   ├── LocalZipMapFileProviderTests.cs
│   │   │   │   │   │   └── MapFileTests.cs
│   │   │   │   │   ├── BaseConsolidatorTests.cs
│   │   │   │   │   ├── BaseDataConsolidatorTests.cs
│   │   │   │   │   ├── BaseDataTests.cs
│   │   │   │   │   ├── CalendarConsolidatorsTests.cs
│   │   │   │   │   ├── ChannelTests.cs
│   │   │   │   │   ├── ClassicRangeConsolidatorTests.cs
│   │   │   │   │   ├── ClassicRenkoConsolidatorTests.cs
│   │   │   │   │   ├── ConsolidatorBaseTests.cs
│   │   │   │   │   ├── ConsolidatorWrapperTests.cs
│   │   │   │   │   ├── Custom
│   │   │   │   │   │   └── PythonCustomDataTests.cs
│   │   │   │   │   ├── DataQueueHandlerSubscriptionManagerTests.cs
│   │   │   │   │   ├── DividendYieldProviderTests.cs
│   │   │   │   │   ├── DollarVolumeRenkoConsolidatorTests.cs
│   │   │   │   │   ├── DynamicDataConsolidatorTests.cs
│   │   │   │   │   ├── DynamicDataTests.cs
│   │   │   │   │   ├── FakeDataQueuehandlerSubscriptionManager.cs
│   │   │   │   │   ├── Fundamental
│   │   │   │   │   │   ├── BaseFundamentalDataProviderTests.cs
│   │   │   │   │   │   ├── FundamentalTests.cs
│   │   │   │   │   │   ├── FundamentalUniverseSelectionModelTests.cs
│   │   │   │   │   │   ├── MultiPeriodFieldTests.cs
│   │   │   │   │   │   ├── NullFundamentalDataProvider.cs
│   │   │   │   │   │   └── TestFundamentalDataProvider.cs
│   │   │   │   │   ├── IdentityDataConsolidatorTests.cs
│   │   │   │   │   ├── InterestRateProviderTests.cs
│   │   │   │   │   ├── Market
│   │   │   │   │   │   ├── BarTests.cs
│   │   │   │   │   │   ├── FuturesContractTests.cs
│   │   │   │   │   │   ├── OptionContractTests.cs
│   │   │   │   │   │   ├── QuoteBarTests.cs
│   │   │   │   │   │   ├── TickTests.cs
│   │   │   │   │   │   └── TradeBarTests.cs
│   │   │   │   │   ├── MarketHourAwareConsolidatorTests.cs
│   │   │   │   │   ├── MockSubscriptionDataConfigProvider.cs
│   │   │   │   │   ├── OpenInterestConsolidatorTests.cs
│   │   │   │   │   ├── PeriodCountConsolidatorTests.cs
│   │   │   │   │   ├── QuoteBarConsolidatorTests.cs
│   │   │   │   │   ├── RangeConsolidatorTests.cs
│   │   │   │   │   ├── RenkoConsolidatorTests.cs
│   │   │   │   │   ├── SequentialConsolidatorTests.cs
│   │   │   │   │   ├── SessionConsolidatorTests.cs
│   │   │   │   │   ├── Shortable
│   │   │   │   │   │   └── ShortableProviderTests.cs
│   │   │   │   │   ├── SliceTests.cs
│   │   │   │   │   ├── SubscriptionDataSourceTests.cs
│   │   │   │   │   ├── SubscriptionManagerTests.cs
│   │   │   │   │   ├── TickConsolidatorTests.cs
│   │   │   │   │   ├── TickQuoteBarConsolidatorTests.cs
│   │   │   │   │   ├── TradeBarConsolidatorTests.cs
│   │   │   │   │   ├── UniverseSelection
│   │   │   │   │   │   ├── CoarseFundamentalTests.cs
│   │   │   │   │   │   ├── ConstituentsUniverseDataTests.cs
│   │   │   │   │   │   ├── OptionUniverseTests.cs
│   │   │   │   │   │   ├── ScheduledUniverseTests.cs
│   │   │   │   │   │   ├── SecurityChangesTests.cs
│   │   │   │   │   │   ├── UniverseTests.cs
│   │   │   │   │   │   └── UserDefinedUniverseTests.cs
│   │   │   │   │   └── VolumeRenkoConsolidatorTests.cs
│   │   │   │   ├── DataMonitorReportTests.cs
│   │   │   │   ├── DocumentationAttributeTest.cs
│   │   │   │   ├── Exceptions
│   │   │   │   │   ├── ClrBubbledExceptionInterpreterTests.cs
│   │   │   │   │   ├── DllNotFoundPythonExceptionInterpreterTests.cs
│   │   │   │   │   ├── FakeExceptionInterpreter.cs
│   │   │   │   │   ├── InvalidTokenPythonExceptionInterpreterTests.cs
│   │   │   │   │   ├── KeyErrorPythonExceptionInterpreterTests.cs
│   │   │   │   │   ├── ModuleNotFoundPythonExceptionInterpreterTests.cs
│   │   │   │   │   ├── MultipleInheritancePythonExceptionInterpreterTests.cs
│   │   │   │   │   ├── NoMethodMatchPythonExceptionInterpreterTests.cs
│   │   │   │   │   ├── NullExceptionInterpreter.cs
│   │   │   │   │   ├── PythonExceptionInterpreterTests.cs
│   │   │   │   │   ├── ScheduledEventExceptionInterpreterTests.cs
│   │   │   │   │   ├── StackExceptionInterpreterTests.cs
│   │   │   │   │   ├── SystemExceptionInterpreterTests.cs
│   │   │   │   │   └── UnsupportedOperandPythonExceptionInterpreterTests.cs
│   │   │   │   ├── ExchangeTest.cs
│   │   │   │   ├── ExpiryTests.cs
│   │   │   │   ├── ExtendedDictionaryTests.cs
│   │   │   │   ├── HoldingTests.cs
│   │   │   │   ├── IsolatorLimitResultProviderTests.cs
│   │   │   │   ├── IsolatorTests.cs
│   │   │   │   ├── MarketTests.cs
│   │   │   │   ├── Notifications
│   │   │   │   │   ├── NotificationEmailTests.cs
│   │   │   │   │   ├── NotificationFtpTests.cs
│   │   │   │   │   ├── NotificationJsonConverterTests.cs
│   │   │   │   │   └── NotificationManagerTests.cs
│   │   │   │   ├── NullTimeKeeper.cs
│   │   │   │   ├── Orders
│   │   │   │   │   ├── CoinbaseOrderPropertiesTests.cs
│   │   │   │   │   ├── dYdXOrderPropertiesTests.cs
│   │   │   │   │   ├── Fees
│   │   │   │   │   │   ├── AlpacaFeeModelTests.cs
│   │   │   │   │   │   ├── AlphaStreamsFeeModelTests.cs
│   │   │   │   │   │   ├── BackwardsCompatibilityFeeModelTests.cs
│   │   │   │   │   │   ├── BinanceCoinFuturesFeeModelTests.cs
│   │   │   │   │   │   ├── BinanceFeeModelTests.cs
│   │   │   │   │   │   ├── BinanceFuturesFeeModelTests.cs
│   │   │   │   │   │   ├── BitfinexFeeModelTests.cs
│   │   │   │   │   │   ├── BybitFeeModelTests.cs
│   │   │   │   │   │   ├── BybitFuturesFeeModelTests.cs
│   │   │   │   │   │   ├── CoinbaseFeeModelTests.cs
│   │   │   │   │   │   ├── FTXFeeTests.cs
│   │   │   │   │   │   ├── FTXUSFeeTests.cs
│   │   │   │   │   │   ├── InteractiveBrokersFeeModelTests.cs
│   │   │   │   │   │   ├── OrderFeesTests.cs
│   │   │   │   │   │   ├── PublicFeeModelTests.cs
│   │   │   │   │   │   ├── SamcoFeeModelTests.cs
│   │   │   │   │   │   └── WebullFeeModelTests.cs
│   │   │   │   │   ├── Fills
│   │   │   │   │   │   ├── BackwardsCompatibilityFillModelsTests.cs
│   │   │   │   │   │   ├── EquityFillModelTests.cs
│   │   │   │   │   │   ├── EquityFillModelTests.LimitFill.cs
│   │   │   │   │   │   ├── EquityFillModelTests.StopMarketFill.cs
│   │   │   │   │   │   ├── FutureFillModelTests.cs
│   │   │   │   │   │   ├── FutureOptionFillModelTests.cs
│   │   │   │   │   │   ├── ImmediateFillModelTests.cs
│   │   │   │   │   │   ├── LatestPriceFillModelTests.cs
│   │   │   │   │   │   └── PartialMarketFillModelTests.cs
│   │   │   │   │   ├── FixOrderPropertiesTests.cs
│   │   │   │   │   ├── GroupOrderExtensionsTests.cs
│   │   │   │   │   ├── OrderEventTests.cs
│   │   │   │   │   ├── OrderJsonConverterTests.cs
│   │   │   │   │   ├── OrderSizingTests.cs
│   │   │   │   │   ├── OrderTests.cs
│   │   │   │   │   ├── OrderTicketTests.cs
│   │   │   │   │   ├── ReadOrdersResponseJsonConverterTests.cs
│   │   │   │   │   ├── Slippage
│   │   │   │   │   │   ├── MarketImpactSlippageModelTest.cs
│   │   │   │   │   │   └── SlippageModelsTests.cs
│   │   │   │   │   ├── TerminalLinkOrderPropertiesTests.cs
│   │   │   │   │   └── TimeInForces
│   │   │   │   │       └── TimeInForceTests.cs
│   │   │   │   ├── OrderTargetsByMarginImpactTests.cs
│   │   │   │   ├── OSTests.cs
│   │   │   │   ├── Packets
│   │   │   │   │   ├── BacktestNodePacketTests.cs
│   │   │   │   │   ├── ControlsTests.cs
│   │   │   │   │   └── LiveNodePacketTests.cs
│   │   │   │   ├── Parameters
│   │   │   │   │   └── ParameterAttributeTests.cs
│   │   │   │   ├── ParseTests.cs
│   │   │   │   ├── ProtobufSerializationTests.cs
│   │   │   │   ├── Python
│   │   │   │   │   └── PythonInitializerTests.cs
│   │   │   │   ├── ScatterChartPointTests.cs
│   │   │   │   ├── Scheduling
│   │   │   │   │   ├── DateRulesTests.cs
│   │   │   │   │   ├── ScheduledEventTests.cs
│   │   │   │   │   ├── ScheduleManagerTests.cs
│   │   │   │   │   └── TimeRulesTests.cs
│   │   │   │   ├── Securities
│   │   │   │   │   ├── AccountCurrencyImmediateSettlementModelTests.cs
│   │   │   │   │   ├── BaseVolatilityModelTests.cs
│   │   │   │   │   ├── BrokerageModelSecurityInitializerTests.cs
│   │   │   │   │   ├── BuyingPowerModelComparator.cs
│   │   │   │   │   ├── BuyingPowerModelTests.cs
│   │   │   │   │   ├── CashAmountTests.cs
│   │   │   │   │   ├── CashBookTests.cs
│   │   │   │   │   ├── CashBuyingPowerModelTests.cs
│   │   │   │   │   ├── CashTests.cs
│   │   │   │   │   ├── Cfd
│   │   │   │   │   │   └── CfdTests.cs
│   │   │   │   │   ├── CryptoFuture
│   │   │   │   │   │   ├── BybitCryptoFutureMarginModelTests.cs
│   │   │   │   │   │   └── CryptoFutureMarginModelTests.cs
│   │   │   │   │   ├── Cryptos
│   │   │   │   │   │   └── CryptoTests.cs
│   │   │   │   │   ├── CurrencyConversion
│   │   │   │   │   │   └── SecurityCurrencyConversionTests.cs
│   │   │   │   │   ├── DelayedSettlementModelTests.cs
│   │   │   │   │   ├── DynamicSecurityDataTests.cs
│   │   │   │   │   ├── ErrorCurrencyConverterTests.cs
│   │   │   │   │   ├── FakeOrderProcessor.cs
│   │   │   │   │   ├── Forex
│   │   │   │   │   │   ├── ForexHoldingTest.cs
│   │   │   │   │   │   └── ForexTests.cs
│   │   │   │   │   ├── FutureFilterTests.cs
│   │   │   │   │   ├── FutureMarginBuyingPowerModelTests.cs
│   │   │   │   │   ├── FutureOption
│   │   │   │   │   │   ├── FuturesOptionsExpiryFunctionsTests.cs
│   │   │   │   │   │   └── FuturesOptionsUnderlyingMapperTests.cs
│   │   │   │   │   ├── FutureOptionMarginBuyingPowerModelTests.cs
│   │   │   │   │   ├── Futures
│   │   │   │   │   │   ├── FutureSettlementModelTests.cs
│   │   │   │   │   │   ├── FuturesExpiryFunctionsTests.cs
│   │   │   │   │   │   ├── FuturesExpiryUtilityFunctionsTests.cs
│   │   │   │   │   │   └── FuturesListingsTests.cs
│   │   │   │   │   ├── IdentityCurrencyConverterTests.cs
│   │   │   │   │   ├── ImmediateSettlementModelTests.cs
│   │   │   │   │   ├── Index
│   │   │   │   │   │   └── IndexTests.cs
│   │   │   │   │   ├── IndexOption
│   │   │   │   │   │   └── IndexOptionSymbolTests.cs
│   │   │   │   │   ├── IndicatorVolatilityModelTests.cs
│   │   │   │   │   ├── LocalMarketHoursTests.cs
│   │   │   │   │   ├── MarginCallModelTests.cs
│   │   │   │   │   ├── MarketHoursDatabaseTests.cs
│   │   │   │   │   ├── OptionFilterTests.cs
│   │   │   │   │   ├── OptionMarginBuyingPowerModelTests.cs
│   │   │   │   │   ├── OptionPriceModelTests.cs
│   │   │   │   │   ├── Options
│   │   │   │   │   │   ├── FedRateQLRiskFreeRateEstimatorTests.cs
│   │   │   │   │   │   ├── OptionChainProviderTests.cs
│   │   │   │   │   │   ├── OptionChainsTests.cs
│   │   │   │   │   │   ├── OptionFilterUniverseTests.cs
│   │   │   │   │   │   ├── OptionPortfolioModelTests.cs
│   │   │   │   │   │   ├── OptionSecurityTests.cs
│   │   │   │   │   │   ├── OptionStrategiesTests.cs
│   │   │   │   │   │   ├── OptionSymbolTests.cs
│   │   │   │   │   │   └── StrategyMatcher
│   │   │   │   │   │       ├── Option.cs
│   │   │   │   │   │       ├── OptionPositionCollectionTests.cs
│   │   │   │   │   │       ├── OptionPositionTests.cs
│   │   │   │   │   │       ├── OptionStrategyDefinitionMatchTests.cs
│   │   │   │   │   │       ├── OptionStrategyDefinitionTests.cs
│   │   │   │   │   │       ├── OptionStrategyLegDefinitionMatchTests.cs
│   │   │   │   │   │       ├── OptionStrategyLegPredicateTests.cs
│   │   │   │   │   │       └── OptionStrategyMatcherTests.cs
│   │   │   │   │   ├── OptionStrategyFilterTests.cs
│   │   │   │   │   ├── OptionStrategyPositionGroupBuyingPowerModelTests.cs
│   │   │   │   │   ├── PatternDayTradingMarginBuyingPowerModelTests.cs
│   │   │   │   │   ├── Positions
│   │   │   │   │   │   ├── PositionGroupCollectionTests.cs
│   │   │   │   │   │   └── PositionGroupTests.cs
│   │   │   │   │   ├── PriceVariationModelsTests.cs
│   │   │   │   │   ├── ProcessVolatilityHistoryRequirementsTests.cs
│   │   │   │   │   ├── RelativeStandardDeviationVolatilityModelTests.cs
│   │   │   │   │   ├── SecurityCacheProviderTests.cs
│   │   │   │   │   ├── SecurityCacheTests.cs
│   │   │   │   │   ├── SecurityDatabaseKeyTests.cs
│   │   │   │   │   ├── SecurityDefinitionSymbolResolverTests.cs
│   │   │   │   │   ├── SecurityDefinitionTests.cs
│   │   │   │   │   ├── SecurityExchangeHoursTests.cs
│   │   │   │   │   ├── SecurityHoldingTests.cs
│   │   │   │   │   ├── SecurityIdentifierTests.cs
│   │   │   │   │   ├── SecurityManagerTests.cs
│   │   │   │   │   ├── SecurityMarginModelTests.cs
│   │   │   │   │   ├── SecurityPortfolioManagerTests.cs
│   │   │   │   │   ├── SecurityPortfolioModelTests.cs
│   │   │   │   │   ├── SecurityPositionGroupBuyingPowerModelTests.cs
│   │   │   │   │   ├── SecurityServiceTests.cs
│   │   │   │   │   ├── SecurityTests.cs
│   │   │   │   │   ├── SecurityTransactionManagerTests.cs
│   │   │   │   │   ├── StandardDeviationOfReturnsVolatilityModelTests.cs
│   │   │   │   │   ├── SubscriptionDataConfigTests.cs
│   │   │   │   │   ├── SymbolPropertiesDatabaseTests.cs
│   │   │   │   │   ├── TestAccountCurrencyProvider.cs
│   │   │   │   │   ├── TestDefaultMarginCallModel.cs
│   │   │   │   │   ├── TradingCalendarTests.cs
│   │   │   │   │   └── UniverseManagerTests.cs
│   │   │   │   ├── SeriesSamplerTests.cs
│   │   │   │   ├── SeriesTests.cs
│   │   │   │   ├── Statistics
│   │   │   │   │   ├── AnnualPerformanceTests.cs
│   │   │   │   │   ├── DrawdownRecoveryTests.cs
│   │   │   │   │   ├── PortfolioStatisticsTests.cs
│   │   │   │   │   ├── ProbabilisticSharpeRatioTests.cs
│   │   │   │   │   ├── StatisticsBuilderTests.cs
│   │   │   │   │   ├── TrackingErrorTests.cs
│   │   │   │   │   ├── TradeBuilderTests.cs
│   │   │   │   │   ├── TradeStatisticsTests.cs
│   │   │   │   │   └── TradeTests.cs
│   │   │   │   ├── Storage
│   │   │   │   │   └── LocalObjectStoreTests.cs
│   │   │   │   ├── StringExtensionsTests.cs
│   │   │   │   ├── SymbolCacheTests.cs
│   │   │   │   ├── SymbolJsonConverterTests.cs
│   │   │   │   ├── SymbolRepresentationTests.cs
│   │   │   │   ├── SymbolTests.cs
│   │   │   │   ├── TimeKeeperTests.cs
│   │   │   │   ├── TimeTests.cs
│   │   │   │   ├── TimeZoneOffsetProviderTests.cs
│   │   │   │   ├── TimeZonesTest.cs
│   │   │   │   └── Util
│   │   │   │       ├── BaseDataExtensionsTests.cs
│   │   │   │       ├── BusyBlockingCollectionTests.cs
│   │   │   │       ├── CandlestickJsonConverterTests.cs
│   │   │   │       ├── CastingEnumerableTests.cs
│   │   │   │       ├── ColorJsonConverterTests.cs
│   │   │   │       ├── ComparisonOperatorTests.cs
│   │   │   │       ├── ComposerTests.cs
│   │   │   │       ├── ConcurrentSetTests.cs
│   │   │   │       ├── CurrencyPairUtilTests.cs
│   │   │   │       ├── DataDownloaderGetParameterExtensionsTests.cs
│   │   │   │       ├── DateTimeJsonConverterTests.cs
│   │   │   │       ├── DecimalJsonConverterTests.cs
│   │   │   │       ├── DisposableExtensionsTests.cs
│   │   │   │       ├── ExpressionBuilderTests.cs
│   │   │   │       ├── ExtensionsTests.cs
│   │   │   │       ├── FileExtensionTests.cs
│   │   │   │       ├── FuncTextWriterTests.cs
│   │   │   │       ├── HistoryExtensionsTests.cs
│   │   │   │       ├── JsonRoundingConverterTests.cs
│   │   │   │       ├── KeyStringSynchronizerTests.cs
│   │   │   │       ├── LeanDataPathComponentsTests.cs
│   │   │   │       ├── LeanDataTests.cs
│   │   │   │       ├── LinqExtensionsTests.cs
│   │   │   │       ├── ListComparerTests.cs
│   │   │   │       ├── MarketHoursDatabaseJsonConverterTests.cs
│   │   │   │       ├── MemoizingEnumerableTests.cs
│   │   │   │       ├── ObjectActivatorTests.cs
│   │   │   │       ├── ObjectToListJsonConverterTests.cs
│   │   │   │       ├── PythonUtilTests.cs
│   │   │   │       ├── RateGateTests.cs
│   │   │   │       ├── RateLimit
│   │   │   │       │   ├── FixedIntervalRefillStrategyTests.cs
│   │   │   │       │   └── LeakyBucketTests.cs
│   │   │   │       ├── ReaderWriterLockSlimExtensionsTests.cs
│   │   │   │       ├── SeriesJsonConverterTests.cs
│   │   │   │       ├── StreamReaderEnumerableTests.cs
│   │   │   │       ├── StreamReaderExtensionsTests.cs
│   │   │   │       ├── ValidateTests.cs
│   │   │   │       └── WhoCalledMeTests.cs
│   │   │   ├── Compression
│   │   │   │   ├── CompressionTests.cs
│   │   │   │   └── ZipStreamWriterTests.cs
│   │   │   ├── Configuration
│   │   │   │   ├── ApplicationParserTests.cs
│   │   │   │   └── ConfigTests.cs
│   │   │   ├── DownloaderDataProvider
│   │   │   │   ├── DataDownloadConfigTests.cs
│   │   │   │   └── DownloadHelperTests.cs
│   │   │   ├── Engine
│   │   │   │   ├── AlgorithmLogTests.cs
│   │   │   │   ├── AlgorithmManagerTests.cs
│   │   │   │   ├── AlgorithmTimeLimitManagerTests.cs
│   │   │   │   ├── BrokerageTransactionHandlerTests
│   │   │   │   │   ├── BacktestingTransactionHandlerTests.cs
│   │   │   │   │   └── BrokerageTransactionHandlerTests.cs
│   │   │   │   ├── CustomBrokerageMessageHandlerTests.cs
│   │   │   │   ├── DataCacheProviders
│   │   │   │   │   ├── DataCacheProviderTests.cs
│   │   │   │   │   ├── DiskDataCacheProviderTests.cs
│   │   │   │   │   ├── SingleEntryDataCacheProviderTests.cs
│   │   │   │   │   └── ZipDataCacheProviderTests.cs
│   │   │   │   ├── DataFeeds
│   │   │   │   │   ├── AggregationManagerTests.cs
│   │   │   │   │   ├── AlgorithmStub.cs
│   │   │   │   │   ├── Auxiliary
│   │   │   │   │   │   └── MapFileResolverTests.cs
│   │   │   │   │   ├── BacktestingFutureChainProviderTests.cs
│   │   │   │   │   ├── BaseDataCollectionAggregatorReaderTests.cs
│   │   │   │   │   ├── BaseDataExchangeTests.cs
│   │   │   │   │   ├── CollectionSubscriptionDataSourceReaderTests.cs
│   │   │   │   │   ├── CompositeTimeProviderTests.cs
│   │   │   │   │   ├── CustomLiveDataFeedTests.cs
│   │   │   │   │   ├── CustomMockedFileBaseData.cs
│   │   │   │   │   ├── DataDownloader
│   │   │   │   │   │   ├── CanonicalDataDownloaderDecoratorTests.cs
│   │   │   │   │   │   └── DataDownloaderSelectorTests.cs
│   │   │   │   │   ├── DataManagerStub.cs
│   │   │   │   │   ├── DataManagerTests.cs
│   │   │   │   │   ├── DataPermissionManagerTests.cs
│   │   │   │   │   ├── DataQueueHandlerManagerTests.cs
│   │   │   │   │   ├── DateChangeTimeKeeperTests.cs
│   │   │   │   │   ├── DownloaderDataProviderTests.cs
│   │   │   │   │   ├── Enumerators
│   │   │   │   │   │   ├── AuxiliaryDataEnumeratorTests.cs
│   │   │   │   │   │   ├── BaseDataCollectionAggregatorEnumeratorTests.cs
│   │   │   │   │   │   ├── ConcatEnumeratorTests.cs
│   │   │   │   │   │   ├── DelistingEnumeratorTests.cs
│   │   │   │   │   │   ├── DividendEventProviderTests.cs
│   │   │   │   │   │   ├── EnqueableEnumeratorTests.cs
│   │   │   │   │   │   ├── Factories
│   │   │   │   │   │   │   ├── BaseDataCollectionSubscriptionEnumeratorFactoryTests.cs
│   │   │   │   │   │   │   └── LiveCustomDataSubscriptionEnumeratorFactoryTests.cs
│   │   │   │   │   │   ├── FastForwardEnumeratorTests.cs
│   │   │   │   │   │   ├── FillForwardEnumeratorTests.cs
│   │   │   │   │   │   ├── FrontierAwareEnumeratorTests.cs
│   │   │   │   │   │   ├── LiveAuxiliaryDataEnumeratorTests.cs
│   │   │   │   │   │   ├── LiveEquityDataSynchronizingEnumeratorTests.cs
│   │   │   │   │   │   ├── LiveFillForwardEnumeratorTests.cs
│   │   │   │   │   │   ├── LiveSubscriptionEnumeratorTests.cs
│   │   │   │   │   │   ├── MappingEventProviderTests.cs
│   │   │   │   │   │   ├── PriceScaleFactorEnumeratorTests.cs
│   │   │   │   │   │   ├── QuoteBarFillForwardEnumeratorTests.cs
│   │   │   │   │   │   ├── RateLimitEnumeratorTests.cs
│   │   │   │   │   │   ├── RefreshEnumeratorTests.cs
│   │   │   │   │   │   ├── ScannableEnumeratorTests.cs
│   │   │   │   │   │   ├── ScheduledEnumeratorTests.cs
│   │   │   │   │   │   ├── SubscriptionDataEnumeratorTests.cs
│   │   │   │   │   │   ├── SynchronizingBaseDataEnumeratorTests.cs
│   │   │   │   │   │   └── SynchronizingSliceEnumeratorTests.cs
│   │   │   │   │   ├── FakeDataQueueTests.cs
│   │   │   │   │   ├── FileSystemDataFeedTests.cs
│   │   │   │   │   ├── FuncDataQueueHandler.cs
│   │   │   │   │   ├── FuncDataQueueHandlerUniverseProvider.cs
│   │   │   │   │   ├── IndexSubscriptionDataSourceReaderTests.cs
│   │   │   │   │   ├── InternalSubscriptionManagerTests.cs
│   │   │   │   │   ├── LiveCoarseUniverseTests.cs
│   │   │   │   │   ├── LiveTradingDataFeedTests.cs
│   │   │   │   │   ├── MockDataFeed.cs
│   │   │   │   │   ├── PendingRemovalsManagerTests.cs
│   │   │   │   │   ├── PrecalculatedSubscriptionDataTests.cs
│   │   │   │   │   ├── PredicateTimeProviderTests.cs
│   │   │   │   │   ├── RealTimeScheduleEventServiceTests.cs
│   │   │   │   │   ├── RestApiBaseData.cs
│   │   │   │   │   ├── SubscriptionCollectionTests.cs
│   │   │   │   │   ├── SubscriptionDataReaderTests.cs
│   │   │   │   │   ├── SubscriptionDataTests.cs
│   │   │   │   │   ├── SubscriptionSynchronizerTests.cs
│   │   │   │   │   ├── SubscriptionTests.cs
│   │   │   │   │   ├── SubscriptionUtilsTests.cs
│   │   │   │   │   ├── TextSubscriptionDataSourceReaderTests.cs
│   │   │   │   │   ├── TimeSliceTests.cs
│   │   │   │   │   ├── Transport
│   │   │   │   │   │   └── RemoteFileSubscriptionStreamReaderTests.cs
│   │   │   │   │   ├── UniverseSelectionTests.cs
│   │   │   │   │   └── ZipEntryNameSubscriptionFactoryTests.cs
│   │   │   │   ├── DataProviders
│   │   │   │   │   ├── ApiDataProviderTests.cs
│   │   │   │   │   ├── DefaultDataProviderTests.cs
│   │   │   │   │   └── ProcessedDataProviderTests.cs
│   │   │   │   ├── DefaultBrokerageMessageHandlerTests.cs
│   │   │   │   ├── DefaultOptionAssignmentModelTests.cs
│   │   │   │   ├── HistoricalData
│   │   │   │   │   ├── FakeHistoryProvider.cs
│   │   │   │   │   ├── HistoryProviderManagerTests.cs
│   │   │   │   │   └── SubscriptionDataReaderHistoryProviderTests.cs
│   │   │   │   ├── PartialFillModel.cs
│   │   │   │   ├── PerformanceBenchmarkAlgorithms.cs
│   │   │   │   ├── ProcessSplitSymbolsDuringWarmupTests.cs
│   │   │   │   ├── RealTime
│   │   │   │   │   ├── BacktestingRealTimeHandlerTests.cs
│   │   │   │   │   └── LiveTradingRealTimeHandlerTests.cs
│   │   │   │   ├── Results
│   │   │   │   │   ├── AlgorithmSpeedAnalysisTests.cs
│   │   │   │   │   ├── AlgorithmSpeedTrackerTests.cs
│   │   │   │   │   ├── AlgorithmWarmingUpOrderResponseErrorAnalysisTests.cs
│   │   │   │   │   ├── BacktestingResultHandlerTests.cs
│   │   │   │   │   ├── BacktestProgressMonitorTests.cs
│   │   │   │   │   ├── BaseResultsHandlerTests.cs
│   │   │   │   │   ├── FlatEquityCurveAnalysisTests.cs
│   │   │   │   │   ├── LiveTradingResultHandlerTests.cs
│   │   │   │   │   ├── MarketOnCloseOrderTooLateOrderResponseErrorAnalysisTests.cs
│   │   │   │   │   ├── PortfolioValueIsNotPositiveAnalysisTests.cs
│   │   │   │   │   ├── ResultsAnalyzerInRunTests.cs
│   │   │   │   │   ├── ResultsAnalyzerTests.cs
│   │   │   │   │   └── SingleTimeLoopTimeoutRuntimeErrorAnalysisTests.cs
│   │   │   │   ├── Setup
│   │   │   │   │   ├── BacktestingSetupHandlerTests.cs
│   │   │   │   │   ├── BaseSetupHandlerTests.cs
│   │   │   │   │   └── BrokerageSetupHandlerTests.cs
│   │   │   │   └── TestResultHandler.cs
│   │   │   ├── Indicators
│   │   │   │   ├── AbsolutePriceOscillatorTests.cs
│   │   │   │   ├── AccelerationBandsTests.cs
│   │   │   │   ├── AccumulationDistributionOscillatorTests.cs
│   │   │   │   ├── AccumulationDistributionTests.cs
│   │   │   │   ├── AdvanceDeclineDifferenceTests.cs
│   │   │   │   ├── AdvanceDeclineRatioTests.cs
│   │   │   │   ├── AdvanceDeclineRatioVolumeTests.cs
│   │   │   │   ├── AlphaIndicatorTests.cs
│   │   │   │   ├── ArmsIndexTests.cs
│   │   │   │   ├── ArnaudLegouxMovingAverageTests.cs
│   │   │   │   ├── AroonOscillatorTests.cs
│   │   │   │   ├── AugenPriceSpikeTests.cs
│   │   │   │   ├── AutoregressiveIntegratedMovingAverageTests.cs
│   │   │   │   ├── AverageDirectionalIndexTests.cs
│   │   │   │   ├── AverageDirectionalMovementIndexRatingTests.cs
│   │   │   │   ├── AverageRangeTests.cs
│   │   │   │   ├── AverageTrueRangeTests.cs
│   │   │   │   ├── AwesomeOscillatorTests.cs
│   │   │   │   ├── BalanceOfPowerTests.cs
│   │   │   │   ├── BetaIndicatorTests.cs
│   │   │   │   ├── BollingerBandsTests.cs
│   │   │   │   ├── CandlestickPatterns
│   │   │   │   │   └── CandlestickPatternTests.cs
│   │   │   │   ├── ChaikinMoneyFlowTests.cs
│   │   │   │   ├── ChaikinOscillatorTests.cs
│   │   │   │   ├── ChandeKrollStopTests.cs
│   │   │   │   ├── ChandeMomentumOscillatorTests.cs
│   │   │   │   ├── ChoppinessIndexTests.cs
│   │   │   │   ├── CommodityChannelIndexTests.cs
│   │   │   │   ├── CommonIndicatorTests.cs
│   │   │   │   ├── CompositeIndicatorTests.cs
│   │   │   │   ├── ConnorsRelativeStrengthIndexTests.cs
│   │   │   │   ├── ConstantIndicatorTests.cs
│   │   │   │   ├── CoppockCurveTests.cs
│   │   │   │   ├── CorrelationPearsonTests.cs
│   │   │   │   ├── CorrelationSpearmanTests.cs
│   │   │   │   ├── CovarianceTests.cs
│   │   │   │   ├── DelayTests.cs
│   │   │   │   ├── DeltaTests.cs
│   │   │   │   ├── DeMarkerIndicatorTests.cs
│   │   │   │   ├── DerivativeOscillatorIndicatorTests.cs
│   │   │   │   ├── DetrendedPriceOscillatorTests.cs
│   │   │   │   ├── DonchianChannelTests.cs
│   │   │   │   ├── DoubleExponentialMovingAverageTests.cs
│   │   │   │   ├── DualSymbolIndicatorTests.cs
│   │   │   │   ├── EaseOfMovementValueTests.cs
│   │   │   │   ├── ExponentialMovingAverageTests.cs
│   │   │   │   ├── FilteredIdentityTests.cs
│   │   │   │   ├── FisherTransformTests.cs
│   │   │   │   ├── ForceIndexTests.cs
│   │   │   │   ├── FractalAdaptiveMovingAverageTests.cs
│   │   │   │   ├── FunctionalIndicatorTests.cs
│   │   │   │   ├── GammaTests.cs
│   │   │   │   ├── HeikinAshiTests.cs
│   │   │   │   ├── HilbertTransformTests.cs
│   │   │   │   ├── HullMovingAverageTests.cs
│   │   │   │   ├── HurstExponentTests.cs
│   │   │   │   ├── IchimokuKinkoHyoTests.cs
│   │   │   │   ├── IdentityTests.cs
│   │   │   │   ├── ImpliedVolatilityTests.cs
│   │   │   │   ├── IndicatorBasedOptionPriceModelTests.cs
│   │   │   │   ├── IndicatorExtensionsTests.cs
│   │   │   │   ├── IndicatorTests.cs
│   │   │   │   ├── InternalBarStrengthTests.cs
│   │   │   │   ├── KaufmanAdaptiveMovingAverageTests.cs
│   │   │   │   ├── KaufmanEfficiencyRatioTests.cs
│   │   │   │   ├── KeltnerChannelsTests.cs
│   │   │   │   ├── KlingerVolumeOscillatorTests.cs
│   │   │   │   ├── KnowSureThingTests.cs
│   │   │   │   ├── LeastSquaresMovingAverageTests.cs
│   │   │   │   ├── LinearWeightedMovingAverageTests.cs
│   │   │   │   ├── LogReturnTests.cs
│   │   │   │   ├── MassIndexTests.cs
│   │   │   │   ├── MaximumTests.cs
│   │   │   │   ├── McClellanIndicatorsTestHelper.cs
│   │   │   │   ├── McClellanOscillatorTests.cs
│   │   │   │   ├── McClellanSummationIndexTests.cs
│   │   │   │   ├── McGinleyDynamicTests.cs
│   │   │   │   ├── MeanAbsoluteDeviationTests.cs
│   │   │   │   ├── MesaAdaptiveMovingAverageTests.cs
│   │   │   │   ├── MidPointTests.cs
│   │   │   │   ├── MidPriceTests.cs
│   │   │   │   ├── MinimumTests.cs
│   │   │   │   ├── MomentumPercentTests.cs
│   │   │   │   ├── MomentumTests.cs
│   │   │   │   ├── MomersionTests.cs
│   │   │   │   ├── MoneyFlowIndexTests.cs
│   │   │   │   ├── MovingAverageConvergenceDivergenceTests.cs
│   │   │   │   ├── MovingAverageTypeExtensionsTests.cs
│   │   │   │   ├── NewHighsNewLowsDifferenceTests.cs
│   │   │   │   ├── NewHighsNewLowsRatioTests.cs
│   │   │   │   ├── NewHighsNewLowsTestsBase.cs
│   │   │   │   ├── NewHighsNewLowsVolumeRatioTests.cs
│   │   │   │   ├── NormalizedAverageTrueRangeTests.cs
│   │   │   │   ├── OnBalanceVolumeTests.cs
│   │   │   │   ├── OptionBaseIndicatorTests.cs
│   │   │   │   ├── ParabolicStopAndReverseExtendedTests.cs
│   │   │   │   ├── ParabolicStopAndReverseTests.cs
│   │   │   │   ├── PercentagePriceOscillatorTests.cs
│   │   │   │   ├── PivotPointsHighLowTests.cs
│   │   │   │   ├── PremierStochasticOscillatorTests.cs
│   │   │   │   ├── PythonIndicatorNoinheritanceTests.cs
│   │   │   │   ├── PythonIndicatorNoinheritanceTestsLegacy.cs
│   │   │   │   ├── PythonIndicatorTests.cs
│   │   │   │   ├── RateOfChangePercentTests.cs
│   │   │   │   ├── RateOfChangeRatioTests.cs
│   │   │   │   ├── RateOfChangeTests.cs
│   │   │   │   ├── RegressionChannelTests.cs
│   │   │   │   ├── RelativeDailyVolumeTests.cs
│   │   │   │   ├── RelativeMovingAverageTests.cs
│   │   │   │   ├── RelativeStrengthIndexTests.cs
│   │   │   │   ├── RelativeVigorIndexTests.cs
│   │   │   │   ├── ResetCompositeIndicatorTests.cs
│   │   │   │   ├── RhoTests.cs
│   │   │   │   ├── RogersSatchellVolatilityTests.cs
│   │   │   │   ├── RollingWindowTests.cs
│   │   │   │   ├── SchaffTrendCycleTests.cs
│   │   │   │   ├── SessionTests.cs
│   │   │   │   ├── SharpeRatioTests.cs
│   │   │   │   ├── SimpleMovingAverageTests.cs
│   │   │   │   ├── SmoothedOnBalanceVolumeTests.cs
│   │   │   │   ├── SortinoRatioTests.cs
│   │   │   │   ├── SqueezeMomentumTests.cs
│   │   │   │   ├── StandardDeviationTests.cs
│   │   │   │   ├── StochasticRelativeStrengthIndexTests.cs
│   │   │   │   ├── StochasticTests.cs
│   │   │   │   ├── SumTests.cs
│   │   │   │   ├── SuperTrendTests.cs
│   │   │   │   ├── SwissArmyKnifeTests.cs
│   │   │   │   ├── T3MovingAverageTests.cs
│   │   │   │   ├── TargetDownsideDeviationTests.cs
│   │   │   │   ├── TestHelper.cs
│   │   │   │   ├── ThetaTests.cs
│   │   │   │   ├── TimeProfileTests.cs
│   │   │   │   ├── TimeSeriesForecastTests.cs
│   │   │   │   ├── TimeSeriesIndicatorTests.cs
│   │   │   │   ├── TomDemarkSequentialTests.cs
│   │   │   │   ├── TriangularMovingAverageTests.cs
│   │   │   │   ├── TripleExponentialMovingAverageTests.cs
│   │   │   │   ├── TrixTests.cs
│   │   │   │   ├── TrueRangeTests.cs
│   │   │   │   ├── TrueStrengthIndexTests.cs
│   │   │   │   ├── UltimateOscillatorTests.cs
│   │   │   │   ├── ValueAtRiskTests.cs
│   │   │   │   ├── VariableIndexDynamicAverageTests.cs
│   │   │   │   ├── VarianceTests.cs
│   │   │   │   ├── VegaTests.cs
│   │   │   │   ├── VolumeProfileTests.cs
│   │   │   │   ├── VolumeWeightedAveragePriceIndicatorTests.cs
│   │   │   │   ├── VolumeWeightedMovingAverageTests.cs
│   │   │   │   ├── VortexTests.cs
│   │   │   │   ├── WaveTrendOscillatorTests.cs
│   │   │   │   ├── WilderAccumulativeSwingIndexTests.cs
│   │   │   │   ├── WilderSwingIndexTests.cs
│   │   │   │   ├── WilliamsPercentRTests.cs
│   │   │   │   ├── WindowIdentityTests.cs
│   │   │   │   ├── ZeroLagExponentialMovingAverageTests.cs
│   │   │   │   └── ZigZagTests.cs
│   │   │   ├── JobQueueTests.cs
│   │   │   ├── Logging
│   │   │   │   └── FileLogHandlerTests.cs
│   │   │   ├── Messaging
│   │   │   │   └── StreamingMessageHandlerTests.cs
│   │   │   ├── NUnitLogHandler.cs
│   │   │   ├── Optimizer
│   │   │   │   ├── Analysis
│   │   │   │   │   ├── LeanOptimizerAnalysisTests.cs
│   │   │   │   │   └── OptimizationAnalyzerTests.cs
│   │   │   │   ├── FakeLeanOptimizer.cs
│   │   │   │   ├── LeanOptimizerTests.cs
│   │   │   │   ├── Models.cs
│   │   │   │   ├── Objectives
│   │   │   │   │   ├── ConstraintTests.cs
│   │   │   │   │   ├── ExtremumTests.cs
│   │   │   │   │   └── TargetTests.cs
│   │   │   │   ├── OptimizationNodePacketTests.cs
│   │   │   │   ├── Parameters
│   │   │   │   │   ├── OptimizationParameterEnumeratorTests.cs
│   │   │   │   │   └── OptimizationParameterTests.cs
│   │   │   │   └── Strategies
│   │   │   │       ├── EulerSearchOptimizationStrategyTests.cs
│   │   │   │       ├── GridSearchOptimizationStrategyTests.cs
│   │   │   │       ├── OptimizationStrategyTests.cs
│   │   │   │       └── StepBaseOptimizationStrategyTests.cs
│   │   │   ├── Properties
│   │   │   │   └── AssemblyInfo.cs
│   │   │   ├── Python
│   │   │   │   ├── AlgorithmPythonWrapperTests.cs
│   │   │   │   ├── BasePythonWrapperTests.cs
│   │   │   │   ├── DataConsolidatorPythonWrapperTests.cs
│   │   │   │   ├── Indicators
│   │   │   │   │   └── IndicatorExtensionsTests.py
│   │   │   │   ├── MethodOverloadTests.cs
│   │   │   │   ├── NamedArgumentsTests.cs
│   │   │   │   ├── PandasConverterTests.BackwardsCompatibility.cs
│   │   │   │   ├── PandasConverterTests.cs
│   │   │   │   ├── PandasConverterUnwrappingTests.cs
│   │   │   │   ├── PandasIndexingTests.cs
│   │   │   │   ├── PandasTests
│   │   │   │   │   ├── PandasIndexingTests.py
│   │   │   │   │   └── PandasMapperTests.py
│   │   │   │   ├── PortfolioCustomModelTests.cs
│   │   │   │   ├── PythonCollectionsTests.cs
│   │   │   │   ├── PythonDataTests.cs
│   │   │   │   ├── PythonMemoryLeakTests.cs
│   │   │   │   ├── PythonOptionTests.cs
│   │   │   │   ├── PythonPackagesTests.cs
│   │   │   │   ├── PythonRegressionAlgorithmsTests.cs
│   │   │   │   ├── PythonSliceGetByTypeTest.cs
│   │   │   │   ├── PythonTestingUtils.cs
│   │   │   │   ├── PythonThreadingTests.cs
│   │   │   │   ├── PythonVirtualEnvironmentTests.cs
│   │   │   │   ├── PythonWrapperTests.cs
│   │   │   │   ├── SecurityCustomModelTests.cs
│   │   │   │   └── SettlementModelPythonWrapperTests.cs
│   │   │   ├── QuantConnect.Tests.csproj
│   │   │   ├── readme.md
│   │   │   ├── RegressionAlgorithms
│   │   │   │   ├── Test_AlgorithmPythonWrapper.py
│   │   │   │   ├── Test_CustomDataAlgorithm.py
│   │   │   │   ├── Test_MethodOverload.py
│   │   │   │   └── Test_PythonExceptionInterpreter.py
│   │   │   ├── RegressionTestMessageHandler.cs
│   │   │   ├── RegressionTests.cs
│   │   │   ├── Report
│   │   │   │   ├── CalculationTests.cs
│   │   │   │   ├── DrawdownCollectionTests.cs
│   │   │   │   ├── PortfolioLooperAlgorithmTests.cs
│   │   │   │   ├── PortfolioLooperTests.cs
│   │   │   │   ├── ReportChartsTest.cs
│   │   │   │   └── ResultDeserializationTests.cs
│   │   │   ├── Research
│   │   │   │   ├── QuantBookFundamentalTests.cs
│   │   │   │   ├── QuantBookHistoryTests.cs
│   │   │   │   ├── QuantBookIndicatorsTests.cs
│   │   │   │   ├── QuantBookSelectionTests.cs
│   │   │   │   ├── QuantBookTests.cs
│   │   │   │   ├── RegressionScripts
│   │   │   │   │   ├── custom_data.py
│   │   │   │   │   ├── Test_QuantBookHistory.py
│   │   │   │   │   └── Test_QuantBookIndicator.py
│   │   │   │   ├── RegressionTemplates
│   │   │   │   │   ├── BasicTemplateCustomDataTypeHistoryResearchCSharp.cs
│   │   │   │   │   ├── BasicTemplateCustomDataTypeHistoryResearchCSharp.ipynb
│   │   │   │   │   ├── BasicTemplateCustomDataTypeHistoryResearchPython.cs
│   │   │   │   │   ├── BasicTemplateCustomDataTypeHistoryResearchPython.ipynb
│   │   │   │   │   ├── BasicTemplateResearchCSharp.cs
│   │   │   │   │   ├── BasicTemplateResearchCSharp.ipynb
│   │   │   │   │   ├── BasicTemplateResearchPython.cs
│   │   │   │   │   └── BasicTemplateResearchPython.ipynb
│   │   │   │   └── StartTests.cs
│   │   │   ├── ResearchRegressionTests.cs
│   │   │   ├── Symbols.cs
│   │   │   ├── TestData
│   │   │   │   ├── 00010101_05_example_psychsignal_testdata.csv
│   │   │   │   ├── 20151224_quote_american.zip
│   │   │   │   ├── aapl_chain.csv
│   │   │   │   ├── aapl_fine_fundamental.json
│   │   │   │   ├── alpha_indicator_datatest.csv
│   │   │   │   ├── arms_data.txt
│   │   │   │   ├── bi_datatest.csv
│   │   │   │   ├── CashTestingStrategy.csv
│   │   │   │   ├── custom_future_chris_cme_es1.csv
│   │   │   │   ├── custom_future_chris_cme_es2.csv
│   │   │   │   ├── daily-stock-picker-backtest.csv
│   │   │   │   ├── daily-stock-picker-live.csv
│   │   │   │   ├── dwac_supertrend.txt
│   │   │   │   ├── dynamic-market-hours
│   │   │   │   │   ├── modified-close
│   │   │   │   │   │   └── market-hours
│   │   │   │   │   │       └── market-hours-database.json
│   │   │   │   │   ├── modified-holidays
│   │   │   │   │   │   └── market-hours
│   │   │   │   │   │       └── market-hours-database.json
│   │   │   │   │   └── original
│   │   │   │   │       └── market-hours
│   │   │   │   │           └── market-hours-database.json
│   │   │   │   ├── dynamic-symbol-properties
│   │   │   │   │   ├── modified
│   │   │   │   │   │   └── symbol-properties
│   │   │   │   │   │       └── symbol-properties-database.csv
│   │   │   │   │   └── original
│   │   │   │   │       └── symbol-properties
│   │   │   │   │           └── symbol-properties-database.csv
│   │   │   │   ├── equity
│   │   │   │   │   └── usa
│   │   │   │   │       └── shortable
│   │   │   │   │           ├── testbrokerage
│   │   │   │   │           │   ├── dates
│   │   │   │   │           │   │   ├── 20201221.csv
│   │   │   │   │           │   │   └── 20201222.csv
│   │   │   │   │           │   └── symbols
│   │   │   │   │           │       ├── aapl.csv
│   │   │   │   │           │       └── goog.csv
│   │   │   │   │           └── testinteractivebrokers
│   │   │   │   │               ├── dates
│   │   │   │   │               │   ├── 20201221.csv
│   │   │   │   │               │   └── 20201222.csv
│   │   │   │   │               └── symbols
│   │   │   │   │                   ├── aapl.csv
│   │   │   │   │                   └── goog.csv
│   │   │   │   ├── eurusd_candle_patterns.txt
│   │   │   │   ├── eurusd60_dem.txt
│   │   │   │   ├── ewz_candle_patterns.txt
│   │   │   │   ├── FillForwardBars.zip
│   │   │   │   ├── FillForwardStrictEndTimeDailyRegressionAlgorithm.zip
│   │   │   │   ├── FillForwardStrictEndTimeHourRegressionAlgorithm.zip
│   │   │   │   ├── FillForwardStrictEndTimeMinuteRegressionAlgorithm.zip
│   │   │   │   ├── frama.txt
│   │   │   │   ├── FuturesExpiryFunctionsTestData.xml
│   │   │   │   ├── fxVolumeDaily.csv
│   │   │   │   ├── fxVolumeHourly.csv
│   │   │   │   ├── fxVolumeMinute.csv
│   │   │   │   ├── generate_reference_data_from_talib.py
│   │   │   │   ├── generate_reference_data_from_talipp.py
│   │   │   │   ├── generate_reference_data_from_tulip.py
│   │   │   │   ├── greeks
│   │   │   │   │   ├── SPX230811C04300000.csv
│   │   │   │   │   ├── SPX230811C04500000.csv
│   │   │   │   │   ├── SPX230811C04700000.csv
│   │   │   │   │   ├── SPX230811P04300000.csv
│   │   │   │   │   ├── SPX230811P04500000.csv
│   │   │   │   │   ├── SPX230811P04700000.csv
│   │   │   │   │   ├── SPX230901C04300000.csv
│   │   │   │   │   ├── SPX230901C04500000.csv
│   │   │   │   │   ├── SPX230901C04700000.csv
│   │   │   │   │   ├── SPX230901P04300000.csv
│   │   │   │   │   ├── SPX230901P04500000.csv
│   │   │   │   │   ├── SPX230901P04700000.csv
│   │   │   │   │   ├── SPY230811C00430000.csv
│   │   │   │   │   ├── SPY230811C00450000.csv
│   │   │   │   │   ├── SPY230811C00470000.csv
│   │   │   │   │   ├── SPY230811P00430000.csv
│   │   │   │   │   ├── SPY230811P00450000.csv
│   │   │   │   │   ├── SPY230811P00470000.csv
│   │   │   │   │   ├── SPY230901C00430000.csv
│   │   │   │   │   ├── SPY230901C00450000.csv
│   │   │   │   │   ├── SPY230901C00470000.csv
│   │   │   │   │   ├── SPY230901P00430000.csv
│   │   │   │   │   ├── SPY230901P00450000.csv
│   │   │   │   │   └── SPY230901P00470000.csv
│   │   │   │   ├── greeksindicator
│   │   │   │   │   └── american
│   │   │   │   │       ├── third_party_1_greeks.csv
│   │   │   │   │       └── third_party_2_greeks.csv
│   │   │   │   ├── mcclellan_data.csv
│   │   │   │   ├── multizip.zip
│   │   │   │   ├── nhnl_data.csv
│   │   │   │   ├── portfolio_targets.csv
│   │   │   │   ├── SampleMarketHoursDatabase.json
│   │   │   │   ├── spx_lwma.csv
│   │   │   │   ├── spy_10_min.txt
│   │   │   │   ├── spy_acceleration_bands_20_4.txt
│   │   │   │   ├── spy_ad_osc.txt
│   │   │   │   ├── spy_ad.txt
│   │   │   │   ├── spy_adr.csv
│   │   │   │   ├── spy_alma.txt
│   │   │   │   ├── spy_ao.txt
│   │   │   │   ├── spy_apo.txt
│   │   │   │   ├── spy_aps.txt
│   │   │   │   ├── spy_arima.csv
│   │   │   │   ├── spy_aroon_oscillator.txt
│   │   │   │   ├── spy_asi.csv
│   │   │   │   ├── spy_atr_wilder.txt
│   │   │   │   ├── spy_atr.txt
│   │   │   │   ├── spy_bollinger_bands.txt
│   │   │   │   ├── spy_bop.txt
│   │   │   │   ├── spy_candle_patterns.txt
│   │   │   │   ├── spy_cmf.txt
│   │   │   │   ├── spy_cmo.txt
│   │   │   │   ├── spy_coppock_curve.csv
│   │   │   │   ├── spy_crsi.csv
│   │   │   │   ├── spy_dema.txt
│   │   │   │   ├── spy_do.csv
│   │   │   │   ├── spy_dpo.csv
│   │   │   │   ├── spy_ema.csv
│   │   │   │   ├── spy_emv.txt
│   │   │   │   ├── spy_heikin_ashi.txt
│   │   │   │   ├── spy_hma.txt
│   │   │   │   ├── spy_hurst_exponent.csv
│   │   │   │   ├── spy_kama.txt
│   │   │   │   ├── spy_ker.txt
│   │   │   │   ├── spy_logr14.txt
│   │   │   │   ├── spy_mama.csv
│   │   │   │   ├── spy_mass_index_25.txt
│   │   │   │   ├── spy_max.txt
│   │   │   │   ├── spy_mfi.txt
│   │   │   │   ├── spy_midpoint.txt
│   │   │   │   ├── spy_midprice.txt
│   │   │   │   ├── spy_min.txt
│   │   │   │   ├── spy_natr.txt
│   │   │   │   ├── spy_ohlcv.txt
│   │   │   │   ├── spy_pivot_pnt_hl.txt
│   │   │   │   ├── spy_ppo.txt
│   │   │   │   ├── spy_pso.csv
│   │   │   │   ├── spy_qqq_corr.csv
│   │   │   │   ├── spy_qqq_cov.csv
│   │   │   │   ├── spy_rdv.txt
│   │   │   │   ├── spy_rocr.txt
│   │   │   │   ├── spy_rvi.txt
│   │   │   │   ├── spy_sarext.txt
│   │   │   │   ├── spy_si.csv
│   │   │   │   ├── spy_sm.csv
│   │   │   │   ├── spy_sortino.csv
│   │   │   │   ├── spy_sr.txt
│   │   │   │   ├── spy_stc.txt
│   │   │   │   ├── spy_swiss.txt
│   │   │   │   ├── spy_t3.txt
│   │   │   │   ├── spy_tdd.csv
│   │   │   │   ├── spy_tema.txt
│   │   │   │   ├── spy_tr.txt
│   │   │   │   ├── spy_trima.txt
│   │   │   │   ├── spy_trix.txt
│   │   │   │   ├── spy_tsf.csv
│   │   │   │   ├── spy_tsi.csv
│   │   │   │   ├── spy_ultosc.txt
│   │   │   │   ├── spy_valueatrisk.csv
│   │   │   │   ├── spy_var.txt
│   │   │   │   ├── spy_vidya.txt
│   │   │   │   ├── spy_with_adx.txt
│   │   │   │   ├── spy_with_cci.txt
│   │   │   │   ├── spy_with_ChandeKrollStop.csv
│   │   │   │   ├── spy_with_chop.csv
│   │   │   │   ├── spy_with_don50.txt
│   │   │   │   ├── spy_with_fisher.txt
│   │   │   │   ├── spy_with_ForceIndex.csv
│   │   │   │   ├── spy_with_hilbert.csv
│   │   │   │   ├── spy_with_ibs.csv
│   │   │   │   ├── spy_with_ichimoku.csv
│   │   │   │   ├── spy_with_ichimoku.ods
│   │   │   │   ├── spy_with_indicators.txt
│   │   │   │   ├── spy_with_keltner.csv
│   │   │   │   ├── spy_with_kst.csv
│   │   │   │   ├── spy_with_kvo.csv
│   │   │   │   ├── spy_with_macd.txt
│   │   │   │   ├── spy_with_McGinleyDynamic.csv
│   │   │   │   ├── spy_with_obv.txt
│   │   │   │   ├── spy_with_rma.csv
│   │   │   │   ├── spy_with_roc50.txt
│   │   │   │   ├── spy_with_rocp50.txt
│   │   │   │   ├── spy_with_rsv.csv
│   │   │   │   ├── spy_with_sobv.csv
│   │   │   │   ├── spy_with_stoch12k3.txt
│   │   │   │   ├── spy_with_StochRSI.csv
│   │   │   │   ├── spy_with_vtx.csv
│   │   │   │   ├── spy_with_vwap.txt
│   │   │   │   ├── spy_with_vwma.csv
│   │   │   │   ├── spy_with_williamsR14.txt
│   │   │   │   ├── spy_with_zlema.csv
│   │   │   │   ├── spy_wto.csv
│   │   │   │   ├── spy_zigzag.csv
│   │   │   │   ├── stock_prices.csv
│   │   │   │   ├── symbol-properties
│   │   │   │   │   └── symbol-properties-database.csv
│   │   │   │   ├── td_sequential_test_data.csv
│   │   │   │   ├── test_cash_equity.xml
│   │   │   │   ├── test_cash_fills.xml
│   │   │   │   ├── test_forex_equity.xml
│   │   │   │   ├── test_forex_fills_jwb_quantity.xml
│   │   │   │   ├── test_forex_fills_mch_quantity.xml
│   │   │   │   ├── test_forex_fills.xml
│   │   │   │   ├── test_report_data.json
│   │   │   │   ├── test.csv
│   │   │   │   ├── tp_datatest.csv
│   │   │   │   └── vp_datatest.csv
│   │   │   ├── TestExtensions.cs
│   │   │   ├── TestGlobals.cs
│   │   │   ├── TestProcess.cs
│   │   │   └── ToolBox
│   │   │       ├── LeanDataReaderTests.cs
│   │   │       ├── LeanDataWriterTests.cs
│   │   │       ├── PsychSignalDataTests.cs
│   │   │       ├── RandomDataGenerator
│   │   │       │   ├── BaseSymbolGeneratorTests.cs
│   │   │       │   ├── DefaultSymbolGeneratorTests.cs
│   │   │       │   ├── DividendSplitMapGeneratorTests.cs
│   │   │       │   ├── FutureSymbolGeneratorTests.cs
│   │   │       │   ├── OptionPriceModelPriceGeneratorTests.cs
│   │   │       │   ├── OptionSymbolGeneratorTests.cs
│   │   │       │   ├── RandomDataGeneratorTests.cs
│   │   │       │   ├── RandomPriceGeneratorTests.cs
│   │   │       │   ├── RandomValueGeneratorTests.cs
│   │   │       │   ├── SecurityInitializerProviderTests.cs
│   │   │       │   └── TickGeneratorTests.cs
│   │   │       └── ToolBoxTests.cs
│   │   └── ToolBox
│   │       ├── AlgoSeekFuturesConverter
│   │       │   ├── AlgoSeek.US.Futures.PriceMultipliers.1.1.csv
│   │       │   ├── AlgoSeekFuturesConverter.cs
│   │       │   ├── AlgoSeekFuturesProcessor.cs
│   │       │   ├── AlgoSeekFuturesProgram.cs
│   │       │   └── AlgoSeekFuturesReader.cs
│   │       ├── Bz2StreamProvider.cs
│   │       ├── CoarseUniverseGenerator
│   │       │   ├── blacklisted-tickers.txt
│   │       │   ├── CoarseUniverseGeneratorProgram.cs
│   │       │   └── SecurityIdentifierContext.cs
│   │       ├── ConsolidatorDataProcessor.cs
│   │       ├── CsvDataProcessor.cs
│   │       ├── ExchangeInfoUpdater.cs
│   │       ├── FactorFileGenerator.cs
│   │       ├── FileStreamProvider.cs
│   │       ├── FilteredDataProcessor.cs
│   │       ├── GzipStreamProvider.cs
│   │       ├── IDataProcessor.cs
│   │       ├── IExchangeInfoDownloader.cs
│   │       ├── IStreamParser.cs
│   │       ├── IStreamProvider.cs
│   │       ├── KaikoDataConverter
│   │       │   ├── KaikoCryptoReader.cs
│   │       │   └── KaikoDataConverterProgram.cs
│   │       ├── LazyStreamWriter.cs
│   │       ├── LeanDataReader.cs
│   │       ├── LeanInstrument.cs
│   │       ├── LeanParser.cs
│   │       ├── PipeDataProcessor.cs
│   │       ├── Program.cs
│   │       ├── Properties
│   │       │   └── AssemblyInfo.cs
│   │       ├── QuantConnect.ToolBox.csproj
│   │       ├── RandomDataGenerator
│   │       │   ├── BaseSymbolGenerator.cs
│   │       │   ├── DataDensity.cs
│   │       │   ├── DefaultSymbolGenerator.cs
│   │       │   ├── DividendSplitMapGenerator.cs
│   │       │   ├── FutureSymbolGenerator.cs
│   │       │   ├── IPriceGenerator.cs
│   │       │   ├── IRandomValueGenerator.cs
│   │       │   ├── ITickGenerator.cs
│   │       │   ├── NoTickersAvailableException.cs
│   │       │   ├── OptionPriceModelPriceGenerator.cs
│   │       │   ├── OptionSymbolGenerator.cs
│   │       │   ├── RandomDataGenerator.cs
│   │       │   ├── RandomDataGeneratorHelper.cs
│   │       │   ├── RandomDataGeneratorProgram.cs
│   │       │   ├── RandomDataGeneratorSettings.cs
│   │       │   ├── RandomPriceGenerator.cs
│   │       │   ├── RandomValueGenerator.cs
│   │       │   ├── RandomValueGeneratorException.cs
│   │       │   ├── SecurityInitializerProvider.cs
│   │       │   ├── TickGenerator.cs
│   │       │   └── TooManyFailedAttemptsException.cs
│   │       ├── RawFileProcessor.cs
│   │       ├── README.md
│   │       ├── TemporaryPathProvider.cs
│   │       ├── TickAggregator.cs
│   │       └── ZipStreamProvider.cs
│   ├── MoonDev-Trading-Ai-Agents
│   │   ├── docs
│   │   │   ├── api.md
│   │   │   ├── examples
│   │   │   │   └── examplespan.md
│   │   │   └── README.md
│   │   ├── moondev.png
│   │   ├── README.md
│   │   ├── requirements.txt
│   │   └── src
│   │       ├── __init__.py
│   │       ├── agents
│   │       │   ├── __init__.py
│   │       │   ├── api.py
│   │       │   ├── base_agent.py
│   │       │   ├── chartanalysis_agent.py
│   │       │   ├── coingecko_agent.py
│   │       │   ├── copybot_agent.py
│   │       │   ├── focus_agent.py
│   │       │   ├── funding_agent.py
│   │       │   ├── fundingarb_agent.py
│   │       │   ├── liquidation_agent.py
│   │       │   ├── listingarb_agent.py
│   │       │   ├── rbi_agent.py
│   │       │   ├── README.md
│   │       │   ├── risk_agent.py
│   │       │   ├── sentiment_agent.py
│   │       │   ├── strategy_agent.py
│   │       │   ├── trading_agent.py
│   │       │   ├── tweet_agent.py
│   │       │   └── whale_agent.py
│   │       ├── config.py
│   │       ├── data
│   │       │   ├── __init__.py
│   │       │   ├── agent_discussed_tokens.csv
│   │       │   ├── ai_analysis_buys.csv
│   │       │   ├── charts
│   │       │   │   └── BTC_15m_1737367731.png
│   │       │   ├── current_allocation.csv
│   │       │   ├── funding_history_backup.csv
│   │       │   ├── funding_history.csv
│   │       │   ├── liquidation_history.csv
│   │       │   ├── ohlcv_collector.py
│   │       │   ├── oi_history.csv
│   │       │   ├── portfolio_balance.csv
│   │       │   ├── rbi
│   │       │   │   ├── backtests
│   │       │   │   │   ├── EMAVolumeSync_BT.py
│   │       │   │   │   ├── MomentumRejection_BT.py
│   │       │   │   │   ├── TrendVengeance_BT.py
│   │       │   │   │   ├── VengeanceTrend_BT.py
│   │       │   │   │   └── VengeanceTrender_BT.py
│   │       │   │   ├── backtests_final
│   │       │   │   │   ├── EMAVolumeSync_BTFinal.py
│   │       │   │   │   ├── MomentumRejection_BTFinal.py
│   │       │   │   │   └── VengeanceTrend_BTFinal.py
│   │       │   │   ├── backtests_package
│   │       │   │   │   ├── EMAVolumeSync_PKG.py
│   │       │   │   │   ├── MomentumRejection_PKG.py
│   │       │   │   │   └── VengeanceTrend_PKG.py
│   │       │   │   ├── BTC-USD-15m.csv
│   │       │   │   ├── ideas.txt
│   │       │   │   ├── research
│   │       │   │   │   ├── AdaptiveTrendline_strategy_0125_1116.txt
│   │       │   │   │   ├── AdaptiveTrendline1118_strategy_0125_1118.txt
│   │       │   │   │   ├── AdaptiveTrendline1124_strategy_0125_1124.txt
│   │       │   │   │   ├── AdaptiveTrendSync_strategy_0125_1120.txt
│   │       │   │   │   ├── AdaptiveTrendSync1122_strategy_0125_1122.txt
│   │       │   │   │   ├── DualEMAMomentum_strategy_0125_1132.txt
│   │       │   │   │   ├── DualEMAMomentum1141_strategy_0125_1141.txt
│   │       │   │   │   ├── DynamicTrendSync_strategy_0125_1126.txt
│   │       │   │   │   ├── EMAFusionTrend_strategy_0125_1136.txt
│   │       │   │   │   ├── EMAVolumeSync_strategy.txt
│   │       │   │   │   ├── EMAWaveRider_strategy.txt
│   │       │   │   │   ├── MomentumLine_strategy_0125_1138.txt
│   │       │   │   │   ├── MomentumRejection_strategy_0125_1142.txt
│   │       │   │   │   ├── MomentumRejection_strategy.txt
│   │       │   │   │   ├── MomentumSurge_strategy_0125_1041.txt
│   │       │   │   │   ├── MomentumSurge_strategy_0125_1043.txt
│   │       │   │   │   ├── MomentumSurge_strategy_0125_1044.txt
│   │       │   │   │   ├── strategy_DC_20250125_105216.txt
│   │       │   │   │   ├── TrendFollower_strategy_0125_1109.txt
│   │       │   │   │   ├── TrendFollower_strategy_0125_1112.txt
│   │       │   │   │   ├── TrendFollower_strategy_0125_1113.txt
│   │       │   │   │   ├── TrendPulse_strategy_0125_1039.txt
│   │       │   │   │   ├── TrendReversal_strategy_0125_1104.txt
│   │       │   │   │   ├── TrendVengeance_strategy.txt
│   │       │   │   │   ├── TrendVengeanceTrailing_strategy_0125_1139.txt
│   │       │   │   │   ├── UnknownStrategy_strategy_0125_1053.txt
│   │       │   │   │   ├── UnknownStrategy_strategy_0125_1055.txt
│   │       │   │   │   ├── UnknownStrategy_strategy_0125_1057.txt
│   │       │   │   │   ├── UnknownStrategy_strategy_0125_1100.txt
│   │       │   │   │   ├── UnknownStrategy_strategy_0125_1102.txt
│   │       │   │   │   ├── VengeanceTrend_strategy_0125_1130.txt
│   │       │   │   │   ├── VengeanceTrend_strategy.txt
│   │       │   │   │   ├── VengeanceTrender_strategy_0125_1133.txt
│   │       │   │   │   └── VengeanceTrender_strategy.txt
│   │       │   │   └── run_0125_1142
│   │       │   │       └── research
│   │       │   │           └── MomentumRejection_strategy_0125_1142.txt
│   │       │   ├── sentiment_history.csv
│   │       │   └── tweets
│   │       │       ├── generated_tweets_20250127_085138.txt
│   │       │       ├── generated_tweets_20250127_090040.txt
│   │       │       ├── generated_tweets_20250127_091321.txt
│   │       │       ├── generated_tweets_20250127_091622.txt
│   │       │       ├── generated_tweets_20250127_092123.txt
│   │       │       ├── generated_tweets_20250127_092231.txt
│   │       │       └── og_tweet_text.txt
│   │       ├── ezbot.py
│   │       ├── frontend
│   │       │   ├── main.py
│   │       │   ├── static
│   │       │   │   ├── css
│   │       │   │   │   └── styles.css
│   │       │   │   ├── images
│   │       │   │   │   └── moondev.png
│   │       │   │   └── js
│   │       │   │       └── main.js
│   │       │   └── templates
│   │       │       └── index.html
│   │       ├── main.py
│   │       ├── nice_funcs_hl.py
│   │       ├── nice_funcs.py
│   │       ├── scripts
│   │       │   ├── coingecko_exchangeless_tokens.py
│   │       │   ├── deepseek_backtest.py
│   │       │   ├── fundingarb_calc.py
│   │       │   ├── openlinks_intabs.py
│   │       │   ├── token_list_tool.py
│   │       │   └── twitter_login.py
│   │       └── strategies
│   │           ├── __init__.py
│   │           ├── base_strategy.py
│   │           ├── custom
│   │           │   ├── __init__.py
│   │           │   ├── example_strategy.py
│   │           │   └── README.md
│   │           ├── example_strategy.py
│   │           └── README.md
│   ├── nautilus_trader
│   │   ├── ADAPTERS.md
│   │   ├── AGENTS.md
│   │   ├── AI_POLICY.md
│   │   ├── assets
│   │   │   ├── architecture-overview.png
│   │   │   ├── ferris.png
│   │   │   ├── nautilus-art.png
│   │   │   ├── nautilus-logo-white.png
│   │   │   ├── nautilus-trader-logo.png
│   │   │   ├── nautilus-trader.png
│   │   │   └── ns-logo.png
│   │   ├── BENCHMARKING.md
│   │   ├── Cargo.lock
│   │   ├── Cargo.toml
│   │   ├── CLA.md
│   │   ├── CLAUDE.md
│   │   ├── clippy.toml
│   │   ├── CODE_OF_CONDUCT.md
│   │   ├── CONTRIBUTING.md
│   │   ├── crates
│   │   │   ├── adapters
│   │   │   │   ├── architect_ax
│   │   │   │   │   ├── benches
│   │   │   │   │   │   ├── deserialization.rs
│   │   │   │   │   │   └── parsing.rs
│   │   │   │   │   ├── bin
│   │   │   │   │   │   ├── flatten.rs
│   │   │   │   │   │   ├── http_public.rs
│   │   │   │   │   │   ├── ws_data.rs
│   │   │   │   │   │   └── ws_orders.rs
│   │   │   │   │   ├── Cargo.toml
│   │   │   │   │   ├── examples
│   │   │   │   │   │   ├── node_data_tester.rs
│   │   │   │   │   │   └── node_exec_tester.rs
│   │   │   │   │   ├── LICENSE -> ../../../LICENSE
│   │   │   │   │   ├── README.md
│   │   │   │   │   ├── src
│   │   │   │   │   │   ├── common
│   │   │   │   │   │   │   ├── auth.rs
│   │   │   │   │   │   │   ├── consts.rs
│   │   │   │   │   │   │   ├── credential.rs
│   │   │   │   │   │   │   ├── enums.rs
│   │   │   │   │   │   │   ├── mod.rs
│   │   │   │   │   │   │   └── parse.rs
│   │   │   │   │   │   ├── config.rs
│   │   │   │   │   │   ├── data.rs
│   │   │   │   │   │   ├── execution.rs
│   │   │   │   │   │   ├── factories.rs
│   │   │   │   │   │   ├── http
│   │   │   │   │   │   │   ├── client.rs
│   │   │   │   │   │   │   ├── error.rs
│   │   │   │   │   │   │   ├── mod.rs
│   │   │   │   │   │   │   ├── models.rs
│   │   │   │   │   │   │   ├── parse.rs
│   │   │   │   │   │   │   └── query.rs
│   │   │   │   │   │   ├── lib.rs
│   │   │   │   │   │   ├── python
│   │   │   │   │   │   │   ├── config.rs
│   │   │   │   │   │   │   ├── factories.rs
│   │   │   │   │   │   │   ├── http.rs
│   │   │   │   │   │   │   ├── mod.rs
│   │   │   │   │   │   │   └── websocket.rs
│   │   │   │   │   │   └── websocket
│   │   │   │   │   │       ├── data
│   │   │   │   │   │       │   ├── client.rs
│   │   │   │   │   │       │   ├── handler.rs
│   │   │   │   │   │       │   ├── mod.rs
│   │   │   │   │   │       │   ├── parse.rs
│   │   │   │   │   │       │   └── subscription.rs
│   │   │   │   │   │       ├── error.rs
│   │   │   │   │   │       ├── messages.rs
│   │   │   │   │   │       ├── mod.rs
│   │   │   │   │   │       ├── orders
│   │   │   │   │   │       │   ├── client.rs
│   │   │   │   │   │       │   ├── handler.rs
│   │   │   │   │   │       │   └── mod.rs
│   │   │   │   │   │       └── parse.rs
│   │   │   │   │   ├── test_data
│   │   │   │   │   │   ├── http_authenticate.json
│   │   │   │   │   │   ├── http_cancel_all_orders.json
│   │   │   │   │   │   ├── http_cancel_order.json
│   │   │   │   │   │   ├── http_get_balances.json
│   │   │   │   │   │   ├── http_get_book.json
│   │   │   │   │   │   ├── http_get_candle.json
│   │   │   │   │   │   ├── http_get_candles.json
│   │   │   │   │   │   ├── http_get_dated_instruments.json
│   │   │   │   │   │   ├── http_get_fills.json
│   │   │   │   │   │   ├── http_get_funding_rates.json
│   │   │   │   │   │   ├── http_get_funding_slots.json
│   │   │   │   │   │   ├── http_get_instruments.json
│   │   │   │   │   │   ├── http_get_open_orders.json
│   │   │   │   │   │   ├── http_get_order_status.json
│   │   │   │   │   │   ├── http_get_orders.json
│   │   │   │   │   │   ├── http_get_positions.json
│   │   │   │   │   │   ├── http_get_risk_snapshot.json
│   │   │   │   │   │   ├── http_get_tickers.json
│   │   │   │   │   │   ├── http_get_trades.json
│   │   │   │   │   │   ├── http_get_transactions.json
│   │   │   │   │   │   ├── http_get_whoami.json
│   │   │   │   │   │   ├── http_initial_margin_requirement.json
│   │   │   │   │   │   ├── http_place_order.json
│   │   │   │   │   │   ├── http_preview_aggressive_limit_order.json
│   │   │   │   │   │   ├── http_replace_order.json
│   │   │   │   │   │   ├── ws_cancel_rejected.json
│   │   │   │   │   │   ├── ws_md_book_l1_captured.json
│   │   │   │   │   │   ├── ws_md_book_l1.json
│   │   │   │   │   │   ├── ws_md_book_l2_captured.json
│   │   │   │   │   │   ├── ws_md_book_l2.json
│   │   │   │   │   │   ├── ws_md_book_l3_captured.json
│   │   │   │   │   │   ├── ws_md_book_l3.json
│   │   │   │   │   │   ├── ws_md_candle.json
│   │   │   │   │   │   ├── ws_md_heartbeat_captured.json
│   │   │   │   │   │   ├── ws_md_heartbeat.json
│   │   │   │   │   │   ├── ws_md_ticker_captured.json
│   │   │   │   │   │   ├── ws_md_ticker_null_prices.json
│   │   │   │   │   │   ├── ws_md_ticker.json
│   │   │   │   │   │   ├── ws_md_trade_captured.json
│   │   │   │   │   │   ├── ws_md_trade.json
│   │   │   │   │   │   ├── ws_order_acknowledged.json
│   │   │   │   │   │   ├── ws_order_cancel_response.json
│   │   │   │   │   │   ├── ws_order_canceled.json
│   │   │   │   │   │   ├── ws_order_done_for_day.json
│   │   │   │   │   │   ├── ws_order_error_response.json
│   │   │   │   │   │   ├── ws_order_expired.json
│   │   │   │   │   │   ├── ws_order_filled.json
│   │   │   │   │   │   ├── ws_order_heartbeat.json
│   │   │   │   │   │   ├── ws_order_list_response_with_orders.json
│   │   │   │   │   │   ├── ws_order_list_response.json
│   │   │   │   │   │   ├── ws_order_open_orders_response_invalid_direct_array.json
│   │   │   │   │   │   ├── ws_order_open_orders_response.json
│   │   │   │   │   │   ├── ws_order_partially_filled.json
│   │   │   │   │   │   ├── ws_order_place_response.json
│   │   │   │   │   │   ├── ws_order_rejected.json
│   │   │   │   │   │   ├── ws_order_replaced_invalid_single_order.json
│   │   │   │   │   │   └── ws_order_replaced_live.json
│   │   │   │   │   └── tests
│   │   │   │   │       ├── common
│   │   │   │   │       │   ├── mod.rs
│   │   │   │   │       │   └── server.rs
│   │   │   │   │       ├── data_client.rs
│   │   │   │   │       ├── exec_client.rs
│   │   │   │   │       ├── http.rs
│   │   │   │   │       └── websocket.rs
│   │   │   │   ├── betfair
│   │   │   │   │   ├── Cargo.toml
│   │   │   │   │   ├── examples
│   │   │   │   │   │   ├── betfair_backtest.rs
│   │   │   │   │   │   ├── load_betfair_file.rs
│   │   │   │   │   │   ├── node_data_tester.rs
│   │   │   │   │   │   └── node_exec_tester.rs
│   │   │   │   │   ├── LICENSE -> ../../../LICENSE
│   │   │   │   │   ├── README.md
│   │   │   │   │   ├── src
│   │   │   │   │   │   ├── common
│   │   │   │   │   │   │   ├── consts.rs
│   │   │   │   │   │   │   ├── credential.rs
│   │   │   │   │   │   │   ├── enums.rs
│   │   │   │   │   │   │   ├── mod.rs
│   │   │   │   │   │   │   ├── parse.rs
│   │   │   │   │   │   │   ├── testing.rs
│   │   │   │   │   │   │   └── types.rs
│   │   │   │   │   │   ├── config.rs
│   │   │   │   │   │   ├── data_types.rs
│   │   │   │   │   │   ├── data.rs
│   │   │   │   │   │   ├── execution.rs
│   │   │   │   │   │   ├── factories.rs
│   │   │   │   │   │   ├── http
│   │   │   │   │   │   │   ├── client.rs
│   │   │   │   │   │   │   ├── error.rs
│   │   │   │   │   │   │   ├── mod.rs
│   │   │   │   │   │   │   ├── models.rs
│   │   │   │   │   │   │   └── parse.rs
│   │   │   │   │   │   ├── lib.rs
│   │   │   │   │   │   ├── loader.rs
│   │   │   │   │   │   ├── provider.rs
│   │   │   │   │   │   ├── python
│   │   │   │   │   │   │   ├── config.rs
│   │   │   │   │   │   │   ├── factories.rs
│   │   │   │   │   │   │   └── mod.rs
│   │   │   │   │   │   └── stream
│   │   │   │   │   │       ├── client.rs
│   │   │   │   │   │       ├── config.rs
│   │   │   │   │   │       ├── error.rs
│   │   │   │   │   │       ├── messages.rs
│   │   │   │   │   │       ├── mod.rs
│   │   │   │   │   │       ├── ocm.rs
│   │   │   │   │   │       └── parse.rs
│   │   │   │   │   ├── test_data
│   │   │   │   │   │   ├── rest
│   │   │   │   │   │   │   ├── account_details.json
│   │   │   │   │   │   │   ├── account_funds_error.json
│   │   │   │   │   │   │   ├── account_funds_no_exposure.json
│   │   │   │   │   │   │   ├── account_funds_with_exposure.json
│   │   │   │   │   │   │   ├── betting_cancel_orders_batch_partial_failure.json
│   │   │   │   │   │   │   ├── betting_cancel_orders_batch_success.json
│   │   │   │   │   │   │   ├── betting_cancel_orders_bet_taken_or_lapsed.json
│   │   │   │   │   │   │   ├── betting_cancel_orders_error.json
│   │   │   │   │   │   │   ├── betting_cancel_orders_result_failure.json
│   │   │   │   │   │   │   ├── betting_cancel_orders_size_reduction.json
│   │   │   │   │   │   │   ├── betting_cancel_orders_success.json
│   │   │   │   │   │   │   ├── betting_list_market_catalogue.json
│   │   │   │   │   │   │   ├── betting_place_order_batch_partial_failure.json
│   │   │   │   │   │   │   ├── betting_place_order_batch_success.json
│   │   │   │   │   │   │   ├── betting_place_order_error.json
│   │   │   │   │   │   │   ├── betting_place_order_success.json
│   │   │   │   │   │   │   ├── betting_replace_orders_success_multi.json
│   │   │   │   │   │   │   ├── betting_replace_orders_success.json
│   │   │   │   │   │   │   ├── cert_login.json
│   │   │   │   │   │   │   ├── list_cleared_orders.json
│   │   │   │   │   │   │   ├── list_current_orders_empty.json
│   │   │   │   │   │   │   ├── list_current_orders_executable.json
│   │   │   │   │   │   │   ├── list_current_orders_execution_complete.json
│   │   │   │   │   │   │   ├── list_current_orders_harness_canceled.json
│   │   │   │   │   │   │   ├── list_current_orders_harness_open.json
│   │   │   │   │   │   │   ├── list_current_orders_lapsed.json
│   │   │   │   │   │   │   ├── list_current_orders_on_close_execution_complete.json
│   │   │   │   │   │   │   ├── list_current_orders_single.json
│   │   │   │   │   │   │   ├── list_market_catalogue.json
│   │   │   │   │   │   │   ├── login_failure.json
│   │   │   │   │   │   │   ├── login_success.json
│   │   │   │   │   │   │   ├── market_definition_closed.json
│   │   │   │   │   │   │   ├── market_definition_open.json
│   │   │   │   │   │   │   ├── market_definition_runner_removed.json
│   │   │   │   │   │   │   └── navigation_list_navigation.json
│   │   │   │   │   │   └── stream
│   │   │   │   │   │       ├── ccm_single.json
│   │   │   │   │   │       ├── connection.json
│   │   │   │   │   │       ├── market_definition_racing.json
│   │   │   │   │   │       ├── market_definition_runner_removed.json
│   │   │   │   │   │       ├── market_definition.json
│   │   │   │   │   │       ├── market_updates.json
│   │   │   │   │   │       ├── mcm_BSP_settled.json
│   │   │   │   │   │       ├── mcm_BSP.json
│   │   │   │   │   │       ├── mcm_HEARTBEAT.json
│   │   │   │   │   │       ├── mcm_latency.json
│   │   │   │   │   │       ├── mcm_live_IMAGE.json
│   │   │   │   │   │       ├── mcm_live_UPDATE.json
│   │   │   │   │   │       ├── mcm_RESUB_DELTA.json
│   │   │   │   │   │       ├── mcm_SUB_IMAGE_no_market_def.json
│   │   │   │   │   │       ├── mcm_SUB_IMAGE.json
│   │   │   │   │   │       ├── mcm_UPDATE_md.json
│   │   │   │   │   │       ├── mcm_UPDATE_tv.json
│   │   │   │   │   │       ├── mcm_UPDATE.json
│   │   │   │   │   │       ├── ocm_CANCEL.json
│   │   │   │   │   │       ├── ocm_DUPLICATE_EXECUTION.json
│   │   │   │   │   │       ├── ocm_EMPTY_IMAGE.json
│   │   │   │   │   │       ├── ocm_error_fill.json
│   │   │   │   │   │       ├── ocm_filled_different_price.json
│   │   │   │   │   │       ├── ocm_FILLED_no_avp.json
│   │   │   │   │   │       ├── ocm_FILLED_sv_zero.json
│   │   │   │   │   │       ├── ocm_FILLED.json
│   │   │   │   │   │       ├── ocm_FULL_IMAGE_STRATEGY.json
│   │   │   │   │   │       ├── ocm_FULL_IMAGE.json
│   │   │   │   │   │       ├── ocm_harness_cancel.json
│   │   │   │   │   │       ├── ocm_harness_external.json
│   │   │   │   │   │       ├── ocm_harness_fill.json
│   │   │   │   │   │       ├── ocm_harness_partial_fill.json
│   │   │   │   │   │       ├── ocm_harness_void.json
│   │   │   │   │   │       ├── ocm_MIXED.json
│   │   │   │   │   │       ├── ocm_multiple_fills.json
│   │   │   │   │   │       ├── ocm_NEW_FULL_IMAGE.json
│   │   │   │   │   │       ├── ocm_order_update.json
│   │   │   │   │   │       ├── ocm_SUB_IMAGE.json
│   │   │   │   │   │       ├── ocm_UPDATE.json
│   │   │   │   │   │       ├── ocm_VOIDED_partial.json
│   │   │   │   │   │       ├── ocm_VOIDED.json
│   │   │   │   │   │       ├── rcm_multi_runner.json
│   │   │   │   │   │       ├── rcm_single.json
│   │   │   │   │   │       ├── sample.bz2
│   │   │   │   │   │       └── status.json
│   │   │   │   │   └── tests
│   │   │   │   │       ├── common
│   │   │   │   │       │   └── mod.rs
│   │   │   │   │       ├── data_client.rs
│   │   │   │   │       ├── exec_client.rs
│   │   │   │   │       ├── harness
│   │   │   │   │       │   └── mod.rs
│   │   │   │   │       ├── http_client.rs
│   │   │   │   │       ├── live.rs
│   │   │   │   │       ├── node.rs
│   │   │   │   │       ├── python.rs
│   │   │   │   │       ├── README.md
│   │   │   │   │       └── stream_client.rs
│   │   │   │   ├── binance
│   │   │   │   │   ├── benches
│   │   │   │   │   │   └── encoder.rs
│   │   │   │   │   ├── bin
│   │   │   │   │   │   ├── capture_spot_http_fixtures.rs
│   │   │   │   │   │   ├── capture_spot_ws_user_data.rs
│   │   │   │   │   │   ├── http_public.rs
│   │   │   │   │   │   └── ws_spot_data.rs
│   │   │   │   │   ├── Cargo.toml
│   │   │   │   │   ├── examples
│   │   │   │   │   │   ├── futures
│   │   │   │   │   │   │   ├── node_data_tester.rs
│   │   │   │   │   │   │   ├── node_exec_tester.rs
│   │   │   │   │   │   │   └── node_exec_trailing_stop_tester.rs
│   │   │   │   │   │   └── spot
│   │   │   │   │   │       ├── node_data_tester.rs
│   │   │   │   │   │       └── node_exec_tester.rs
│   │   │   │   │   ├── LICENSE -> ../../../LICENSE
│   │   │   │   │   ├── licenses
│   │   │   │   │   │   ├── Apache-2.0-RealLogic-SBE.txt
│   │   │   │   │   │   └── THIRD_PARTY_LICENSES.md
│   │   │   │   │   ├── README.md
│   │   │   │   │   ├── src
│   │   │   │   │   │   ├── arrow
│   │   │   │   │   │   │   ├── bar.rs
│   │   │   │   │   │   │   └── mod.rs
│   │   │   │   │   │   ├── common
│   │   │   │   │   │   │   ├── bar.rs
│   │   │   │   │   │   │   ├── consts.rs
│   │   │   │   │   │   │   ├── credential.rs
│   │   │   │   │   │   │   ├── dispatch.rs
│   │   │   │   │   │   │   ├── encoder.rs
│   │   │   │   │   │   │   ├── enums.rs
│   │   │   │   │   │   │   ├── error.rs
│   │   │   │   │   │   │   ├── execution.rs
│   │   │   │   │   │   │   ├── fees.rs
│   │   │   │   │   │   │   ├── instruments.rs
│   │   │   │   │   │   │   ├── mod.rs
│   │   │   │   │   │   │   ├── models.rs
│   │   │   │   │   │   │   ├── parse.rs
│   │   │   │   │   │   │   ├── status.rs
│   │   │   │   │   │   │   ├── symbol.rs
│   │   │   │   │   │   │   ├── testing.rs
│   │   │   │   │   │   │   └── urls.rs
│   │   │   │   │   │   ├── config.rs
│   │   │   │   │   │   ├── data_types.rs
│   │   │   │   │   │   ├── factories.rs
│   │   │   │   │   │   ├── futures
│   │   │   │   │   │   │   ├── conversions.rs
│   │   │   │   │   │   │   ├── data.rs
│   │   │   │   │   │   │   ├── execution.rs
│   │   │   │   │   │   │   ├── http
│   │   │   │   │   │   │   │   ├── client.rs
│   │   │   │   │   │   │   │   ├── error.rs
│   │   │   │   │   │   │   │   ├── mod.rs
│   │   │   │   │   │   │   │   ├── models.rs
│   │   │   │   │   │   │   │   └── query.rs
│   │   │   │   │   │   │   ├── mod.rs
│   │   │   │   │   │   │   └── websocket
│   │   │   │   │   │   │       ├── mod.rs
│   │   │   │   │   │   │       ├── streams
│   │   │   │   │   │   │       │   ├── client.rs
│   │   │   │   │   │   │       │   ├── dispatch.rs
│   │   │   │   │   │   │       │   ├── error.rs
│   │   │   │   │   │   │       │   ├── handler.rs
│   │   │   │   │   │   │       │   ├── messages.rs
│   │   │   │   │   │   │       │   ├── mod.rs
│   │   │   │   │   │   │       │   ├── parse_data.rs
│   │   │   │   │   │   │       │   ├── parse_exec.rs
│   │   │   │   │   │   │       │   └── recovery.rs
│   │   │   │   │   │   │       └── trading
│   │   │   │   │   │   │           ├── client.rs
│   │   │   │   │   │   │           ├── dispatch.rs
│   │   │   │   │   │   │           ├── error.rs
│   │   │   │   │   │   │           ├── handler.rs
│   │   │   │   │   │   │           ├── messages.rs
│   │   │   │   │   │   │           └── mod.rs
│   │   │   │   │   │   ├── lib.rs
│   │   │   │   │   │   ├── python
│   │   │   │   │   │   │   ├── arrow.rs
│   │   │   │   │   │   │   ├── config.rs
│   │   │   │   │   │   │   ├── data.rs
│   │   │   │   │   │   │   ├── enums.rs
│   │   │   │   │   │   │   ├── factories.rs
│   │   │   │   │   │   │   ├── instruments.rs
│   │   │   │   │   │   │   ├── mod.rs
│   │   │   │   │   │   │   └── types.rs
│   │   │   │   │   │   └── spot
│   │   │   │   │   │       ├── data.rs
│   │   │   │   │   │       ├── enums.rs
│   │   │   │   │   │       ├── execution.rs
│   │   │   │   │   │       ├── http
│   │   │   │   │   │       │   ├── client.rs
│   │   │   │   │   │       │   ├── error.rs
│   │   │   │   │   │       │   ├── mod.rs
│   │   │   │   │   │       │   ├── models.rs
│   │   │   │   │   │       │   ├── parse.rs
│   │   │   │   │   │       │   └── query.rs
│   │   │   │   │   │       ├── mod.rs
│   │   │   │   │   │       ├── sbe
│   │   │   │   │   │       │   ├── cursor.rs
│   │   │   │   │   │       │   ├── error.rs
│   │   │   │   │   │       │   ├── generated
│   │   │   │   │   │       │   │   ├── account_commission_response_codec.rs
│   │   │   │   │   │       │   │   ├── account_order_rate_limit_response_codec.rs
│   │   │   │   │   │       │   │   ├── account_prevented_matches_response_codec.rs
│   │   │   │   │   │       │   │   ├── account_response_codec.rs
│   │   │   │   │   │       │   │   ├── account_trades_response_codec.rs
│   │   │   │   │   │       │   │   ├── account_type.rs
│   │   │   │   │   │       │   │   ├── agg_trades_response_codec.rs
│   │   │   │   │   │       │   │   ├── allowed_self_trade_prevention_modes.rs
│   │   │   │   │   │       │   │   ├── average_price_response_codec.rs
│   │   │   │   │   │       │   │   ├── balance_update_event_codec.rs
│   │   │   │   │   │       │   │   ├── book_ticker_response_codec.rs
│   │   │   │   │   │       │   │   ├── book_ticker_symbol_response_codec.rs
│   │   │   │   │   │       │   │   ├── bool_enum.rs
│   │   │   │   │   │       │   │   ├── calculation_type.rs
│   │   │   │   │   │       │   │   ├── cancel_open_orders_response_codec.rs
│   │   │   │   │   │       │   │   ├── cancel_order_list_response_codec.rs
│   │   │   │   │   │       │   │   ├── cancel_order_response_codec.rs
│   │   │   │   │   │       │   │   ├── cancel_replace_order_response_codec.rs
│   │   │   │   │   │       │   │   ├── cancel_replace_status.rs
│   │   │   │   │   │       │   │   ├── contingency_type.rs
│   │   │   │   │   │       │   │   ├── depth_response_codec.rs
│   │   │   │   │   │       │   │   ├── error_response_codec.rs
│   │   │   │   │   │       │   │   ├── event_stream_terminated_event_codec.rs
│   │   │   │   │   │       │   │   ├── exchange_info_response_codec.rs
│   │   │   │   │   │       │   │   ├── exchange_max_num_algo_orders_filter_codec.rs
│   │   │   │   │   │       │   │   ├── exchange_max_num_iceberg_orders_filter_codec.rs
│   │   │   │   │   │       │   │   ├── exchange_max_num_order_lists_filter_codec.rs
│   │   │   │   │   │       │   │   ├── exchange_max_num_orders_filter_codec.rs
│   │   │   │   │   │       │   │   ├── execution_report_event_codec.rs
│   │   │   │   │   │       │   │   ├── execution_rule_type.rs
│   │   │   │   │   │       │   │   ├── execution_rules_response_codec.rs
│   │   │   │   │   │       │   │   ├── execution_type.rs
│   │   │   │   │   │       │   │   ├── expiry_reason.rs
│   │   │   │   │   │       │   │   ├── external_lock_update_event_codec.rs
│   │   │   │   │   │       │   │   ├── filter_type.rs
│   │   │   │   │   │       │   │   ├── floor.rs
│   │   │   │   │   │       │   │   ├── group_size_16_encoding_codec.rs
│   │   │   │   │   │       │   │   ├── group_size_encoding_codec.rs
│   │   │   │   │   │       │   │   ├── iceberg_parts_filter_codec.rs
│   │   │   │   │   │       │   │   ├── klines_response_codec.rs
│   │   │   │   │   │       │   │   ├── list_order_status.rs
│   │   │   │   │   │       │   │   ├── list_status_event_codec.rs
│   │   │   │   │   │       │   │   ├── list_status_type.rs
│   │   │   │   │   │       │   │   ├── lot_size_filter_codec.rs
│   │   │   │   │   │       │   │   ├── market_lot_size_filter_codec.rs
│   │   │   │   │   │       │   │   ├── match_type.rs
│   │   │   │   │   │       │   │   ├── max_asset_filter_codec.rs
│   │   │   │   │   │       │   │   ├── max_num_algo_orders_filter_codec.rs
│   │   │   │   │   │       │   │   ├── max_num_iceberg_orders_filter_codec.rs
│   │   │   │   │   │       │   │   ├── max_num_order_amends_filter_codec.rs
│   │   │   │   │   │       │   │   ├── max_num_order_lists_filter_codec.rs
│   │   │   │   │   │       │   │   ├── max_num_orders_filter_codec.rs
│   │   │   │   │   │       │   │   ├── max_position_filter_codec.rs
│   │   │   │   │   │       │   │   ├── message_data_16_codec.rs
│   │   │   │   │   │       │   │   ├── message_data_8_codec.rs
│   │   │   │   │   │       │   │   ├── message_data_codec.rs
│   │   │   │   │   │       │   │   ├── message_header_codec.rs
│   │   │   │   │   │       │   │   ├── min_notional_filter_codec.rs
│   │   │   │   │   │       │   │   ├── mod.rs
│   │   │   │   │   │       │   │   ├── my_filters_response_codec.rs
│   │   │   │   │   │       │   │   ├── new_order_ack_response_codec.rs
│   │   │   │   │   │       │   │   ├── new_order_full_response_codec.rs
│   │   │   │   │   │       │   │   ├── new_order_list_ack_response_codec.rs
│   │   │   │   │   │       │   │   ├── new_order_list_full_response_codec.rs
│   │   │   │   │   │       │   │   ├── new_order_list_result_response_codec.rs
│   │   │   │   │   │       │   │   ├── new_order_result_response_codec.rs
│   │   │   │   │   │       │   │   ├── non_representable_message_codec.rs
│   │   │   │   │   │       │   │   ├── notional_filter_codec.rs
│   │   │   │   │   │       │   │   ├── optional_message_data_16_codec.rs
│   │   │   │   │   │       │   │   ├── optional_message_data_codec.rs
│   │   │   │   │   │       │   │   ├── optional_var_string_8_codec.rs
│   │   │   │   │   │       │   │   ├── optional_var_string_codec.rs
│   │   │   │   │   │       │   │   ├── order_capacity.rs
│   │   │   │   │   │       │   │   ├── order_list_response_codec.rs
│   │   │   │   │   │       │   │   ├── order_lists_response_codec.rs
│   │   │   │   │   │       │   │   ├── order_response_codec.rs
│   │   │   │   │   │       │   │   ├── order_side.rs
│   │   │   │   │   │       │   │   ├── order_status.rs
│   │   │   │   │   │       │   │   ├── order_test_response_codec.rs
│   │   │   │   │   │       │   │   ├── order_test_with_commissions_response_codec.rs
│   │   │   │   │   │       │   │   ├── order_type.rs
│   │   │   │   │   │       │   │   ├── order_types.rs
│   │   │   │   │   │       │   │   ├── orders_response_codec.rs
│   │   │   │   │   │       │   │   ├── outbound_account_position_event_codec.rs
│   │   │   │   │   │       │   │   ├── peg_offset_type.rs
│   │   │   │   │   │       │   │   ├── peg_price_type.rs
│   │   │   │   │   │       │   │   ├── percent_price_by_side_filter_codec.rs
│   │   │   │   │   │       │   │   ├── percent_price_filter_codec.rs
│   │   │   │   │   │       │   │   ├── ping_response_codec.rs
│   │   │   │   │   │       │   │   ├── price_filter_codec.rs
│   │   │   │   │   │       │   │   ├── price_range_execution_rule_codec.rs
│   │   │   │   │   │       │   │   ├── price_ticker_response_codec.rs
│   │   │   │   │   │       │   │   ├── price_ticker_symbol_response_codec.rs
│   │   │   │   │   │       │   │   ├── rate_limit_interval.rs
│   │   │   │   │   │       │   │   ├── rate_limit_type.rs
│   │   │   │   │   │       │   │   ├── reference_price_calculation_response_codec.rs
│   │   │   │   │   │       │   │   ├── reference_price_response_codec.rs
│   │   │   │   │   │       │   │   ├── self_trade_prevention_mode.rs
│   │   │   │   │   │       │   │   ├── server_shutdown_event_codec.rs
│   │   │   │   │   │       │   │   ├── server_time_response_codec.rs
│   │   │   │   │   │       │   │   ├── symbol_status.rs
│   │   │   │   │   │       │   │   ├── ticker_24_hf_ull_response_codec.rs
│   │   │   │   │   │       │   │   ├── ticker_24_hm_ini_response_codec.rs
│   │   │   │   │   │       │   │   ├── ticker_24_hs_ymbol_full_response_codec.rs
│   │   │   │   │   │       │   │   ├── ticker_24_hs_ymbol_mini_response_codec.rs
│   │   │   │   │   │       │   │   ├── ticker_full_response_codec.rs
│   │   │   │   │   │       │   │   ├── ticker_mini_response_codec.rs
│   │   │   │   │   │       │   │   ├── ticker_symbol_full_response_codec.rs
│   │   │   │   │   │       │   │   ├── ticker_symbol_mini_response_codec.rs
│   │   │   │   │   │       │   │   ├── time_in_force.rs
│   │   │   │   │   │       │   │   ├── tp_lus_sell_filter_codec.rs
│   │   │   │   │   │       │   │   ├── trades_response_codec.rs
│   │   │   │   │   │       │   │   ├── trailing_delta_filter_codec.rs
│   │   │   │   │   │       │   │   ├── var_string_8_codec.rs
│   │   │   │   │   │       │   │   ├── var_string_codec.rs
│   │   │   │   │   │       │   │   ├── web_socket_response_codec.rs
│   │   │   │   │   │       │   │   ├── web_socket_session_logon_response_codec.rs
│   │   │   │   │   │       │   │   ├── web_socket_session_logout_response_codec.rs
│   │   │   │   │   │       │   │   ├── web_socket_session_status_response_codec.rs
│   │   │   │   │   │       │   │   └── web_socket_session_subscriptions_response_codec.rs
│   │   │   │   │   │       │   ├── mod.rs
│   │   │   │   │   │       │   ├── README.md
│   │   │   │   │   │       │   └── stream
│   │   │   │   │   │       │       ├── best_bid_ask.rs
│   │   │   │   │   │       │       ├── depth_diff.rs
│   │   │   │   │   │       │       ├── depth_snapshot.rs
│   │   │   │   │   │       │       ├── mod.rs
│   │   │   │   │   │       │       └── trades.rs
│   │   │   │   │   │       └── websocket
│   │   │   │   │   │           ├── error.rs
│   │   │   │   │   │           ├── mod.rs
│   │   │   │   │   │           ├── public_json
│   │   │   │   │   │           │   ├── client.rs
│   │   │   │   │   │           │   ├── handler.rs
│   │   │   │   │   │           │   ├── messages.rs
│   │   │   │   │   │           │   ├── mod.rs
│   │   │   │   │   │           │   └── parse.rs
│   │   │   │   │   │           ├── streams
│   │   │   │   │   │           │   ├── client.rs
│   │   │   │   │   │           │   ├── handler.rs
│   │   │   │   │   │           │   ├── messages.rs
│   │   │   │   │   │           │   ├── mod.rs
│   │   │   │   │   │           │   ├── parse.rs
│   │   │   │   │   │           │   └── subscription.rs
│   │   │   │   │   │           └── trading
│   │   │   │   │   │               ├── client.rs
│   │   │   │   │   │               ├── decode_sbe.rs
│   │   │   │   │   │               ├── error.rs
│   │   │   │   │   │               ├── handler.rs
│   │   │   │   │   │               ├── messages.rs
│   │   │   │   │   │               ├── mod.rs
│   │   │   │   │   │               ├── parse.rs
│   │   │   │   │   │               └── user_data.rs
│   │   │   │   │   ├── test_data
│   │   │   │   │   │   ├── futures
│   │   │   │   │   │   │   ├── http_json
│   │   │   │   │   │   │   │   ├── account_info_v2.json
│   │   │   │   │   │   │   │   ├── algo_order_response.json
│   │   │   │   │   │   │   │   ├── balance.json
│   │   │   │   │   │   │   │   ├── exchange_info_delivery_coinm.json
│   │   │   │   │   │   │   │   ├── exchange_info_usdm.json
│   │   │   │   │   │   │   │   ├── open_algo_orders.json
│   │   │   │   │   │   │   │   ├── order_response.json
│   │   │   │   │   │   │   │   ├── position_risk_hedge.json
│   │   │   │   │   │   │   │   ├── position_risk.json
│   │   │   │   │   │   │   │   └── user_trade.json
│   │   │   │   │   │   │   ├── market_data_json
│   │   │   │   │   │   │   │   ├── agg_trade_stream.json
│   │   │   │   │   │   │   │   ├── book_ticker_stream.json
│   │   │   │   │   │   │   │   ├── depth_update_stream.json
│   │   │   │   │   │   │   │   ├── kline_stream_closed.json
│   │   │   │   │   │   │   │   ├── kline_stream_open.json
│   │   │   │   │   │   │   │   ├── liquidation_stream.json
│   │   │   │   │   │   │   │   ├── mark_price_stream.json
│   │   │   │   │   │   │   │   ├── ticker_stream.json
│   │   │   │   │   │   │   │   └── trade_stream.json
│   │   │   │   │   │   │   └── user_data_json
│   │   │   │   │   │   │       ├── account_update_bnfcr.json
│   │   │   │   │   │   │       ├── account_update.json
│   │   │   │   │   │   │       ├── algo_update_canceled.json
│   │   │   │   │   │   │       ├── algo_update_new.json
│   │   │   │   │   │   │       ├── order_update_adl.json
│   │   │   │   │   │   │       ├── order_update_calculated_pending.json
│   │   │   │   │   │   │       ├── order_update_calculated.json
│   │   │   │   │   │   │       ├── order_update_delivery.json
│   │   │   │   │   │   │       ├── order_update_insurance.json
│   │   │   │   │   │   │       ├── order_update_new.json
│   │   │   │   │   │   │       ├── order_update_settlement.json
│   │   │   │   │   │   │       ├── order_update_trade_partial.json
│   │   │   │   │   │   │       ├── order_update_trade.json
│   │   │   │   │   │   │       └── trade_lite.json
│   │   │   │   │   │   ├── README.md
│   │   │   │   │   │   ├── SOURCES.md
│   │   │   │   │   │   └── spot
│   │   │   │   │   │       ├── http_json
│   │   │   │   │   │       │   ├── account_response.json
│   │   │   │   │   │       │   ├── account_trades_response.json
│   │   │   │   │   │       │   ├── all_orders_response.json
│   │   │   │   │   │       │   ├── avg_price_response.json
│   │   │   │   │   │       │   ├── book_ticker_response.json
│   │   │   │   │   │       │   ├── cancel_open_orders_response.json
│   │   │   │   │   │       │   ├── cancel_order_response.json
│   │   │   │   │   │       │   ├── depth_response.json
│   │   │   │   │   │       │   ├── exchange_info_response.json
│   │   │   │   │   │       │   ├── klines_response.json
│   │   │   │   │   │       │   ├── new_order_full_response.json
│   │   │   │   │   │       │   ├── open_orders_response.json
│   │   │   │   │   │       │   ├── order_response.json
│   │   │   │   │   │       │   ├── ping_response.json
│   │   │   │   │   │       │   ├── server_time_response.json
│   │   │   │   │   │       │   ├── ticker_24hr_response.json
│   │   │   │   │   │       │   ├── ticker_price_response.json
│   │   │   │   │   │       │   └── trades_response.json
│   │   │   │   │   │       ├── user_data_json
│   │   │   │   │   │       │   ├── account_position_wrapped.json
│   │   │   │   │   │       │   ├── account_position.json
│   │   │   │   │   │       │   ├── balance_update_wrapped.json
│   │   │   │   │   │       │   ├── balance_update.json
│   │   │   │   │   │       │   ├── execution_report_canceled.json
│   │   │   │   │   │       │   ├── execution_report_expired.json
│   │   │   │   │   │       │   ├── execution_report_new.json
│   │   │   │   │   │       │   ├── execution_report_stop_loss.json
│   │   │   │   │   │       │   ├── execution_report_trade.json
│   │   │   │   │   │       │   ├── execution_report_wrapped.json
│   │   │   │   │   │       │   └── list_status_wrapped.json
│   │   │   │   │   │       └── user_data_sbe
│   │   │   │   │   │           └── mainnet
│   │   │   │   │   │               ├── execution_report_event_1.metadata.json
│   │   │   │   │   │               ├── execution_report_event_1.sbe
│   │   │   │   │   │               ├── execution_report_event_2.metadata.json
│   │   │   │   │   │               ├── execution_report_event_2.sbe
│   │   │   │   │   │               ├── manifest.json
│   │   │   │   │   │               ├── outbound_account_position_event_1.metadata.json
│   │   │   │   │   │               ├── outbound_account_position_event_1.sbe
│   │   │   │   │   │               ├── outbound_account_position_event_2.metadata.json
│   │   │   │   │   │               ├── outbound_account_position_event_2.sbe
│   │   │   │   │   │               ├── web_socket_response_1.metadata.json
│   │   │   │   │   │               ├── web_socket_response_1.sbe
│   │   │   │   │   │               ├── web_socket_response_2.metadata.json
│   │   │   │   │   │               └── web_socket_response_2.sbe
│   │   │   │   │   └── tests
│   │   │   │   │       ├── futures
│   │   │   │   │       │   ├── data_client.rs
│   │   │   │   │       │   ├── exec_client.rs
│   │   │   │   │       │   ├── http.rs
│   │   │   │   │       │   ├── websocket_streams.rs
│   │   │   │   │       │   └── websocket_trading.rs
│   │   │   │   │       ├── futures.rs
│   │   │   │   │       ├── python.rs
│   │   │   │   │       ├── spot
│   │   │   │   │       │   ├── data_client.rs
│   │   │   │   │       │   ├── exec_client.rs
│   │   │   │   │       │   ├── http.rs
│   │   │   │   │       │   ├── websocket_streams.rs
│   │   │   │   │       │   └── websocket_trading.rs
│   │   │   │   │       └── spot.rs
│   │   │   │   ├── bitmex
│   │   │   │   │   ├── bin
│   │   │   │   │   │   ├── http.rs
│   │   │   │   │   │   ├── ws_data.rs
│   │   │   │   │   │   └── ws_exec.rs
│   │   │   │   │   ├── Cargo.toml
│   │   │   │   │   ├── examples
│   │   │   │   │   │   ├── node_data_tester.rs
│   │   │   │   │   │   ├── node_exec_tester.rs
│   │   │   │   │   │   └── node_grid_mm.rs
│   │   │   │   │   ├── LICENSE -> ../../../LICENSE
│   │   │   │   │   ├── README.md
│   │   │   │   │   ├── src
│   │   │   │   │   │   ├── broadcast
│   │   │   │   │   │   │   ├── canceller.rs
│   │   │   │   │   │   │   ├── mod.rs
│   │   │   │   │   │   │   └── submitter.rs
│   │   │   │   │   │   ├── common
│   │   │   │   │   │   │   ├── consts.rs
│   │   │   │   │   │   │   ├── credential.rs
│   │   │   │   │   │   │   ├── enums.rs
│   │   │   │   │   │   │   ├── mod.rs
│   │   │   │   │   │   │   ├── parse.rs
│   │   │   │   │   │   │   ├── retry.rs
│   │   │   │   │   │   │   ├── serialization.rs
│   │   │   │   │   │   │   ├── testing.rs
│   │   │   │   │   │   │   └── urls.rs
│   │   │   │   │   │   ├── config.rs
│   │   │   │   │   │   ├── data.rs
│   │   │   │   │   │   ├── execution.rs
│   │   │   │   │   │   ├── factories.rs
│   │   │   │   │   │   ├── http
│   │   │   │   │   │   │   ├── client.rs
│   │   │   │   │   │   │   ├── error.rs
│   │   │   │   │   │   │   ├── mod.rs
│   │   │   │   │   │   │   ├── models.rs
│   │   │   │   │   │   │   ├── parse.rs
│   │   │   │   │   │   │   └── query.rs
│   │   │   │   │   │   ├── lib.rs
│   │   │   │   │   │   ├── python
│   │   │   │   │   │   │   ├── canceller.rs
│   │   │   │   │   │   │   ├── config.rs
│   │   │   │   │   │   │   ├── enums.rs
│   │   │   │   │   │   │   ├── factories.rs
│   │   │   │   │   │   │   ├── http.rs
│   │   │   │   │   │   │   ├── mod.rs
│   │   │   │   │   │   │   ├── submitter.rs
│   │   │   │   │   │   │   └── websocket.rs
│   │   │   │   │   │   └── websocket
│   │   │   │   │   │       ├── client.rs
│   │   │   │   │   │       ├── dispatch.rs
│   │   │   │   │   │       ├── enums.rs
│   │   │   │   │   │       ├── error.rs
│   │   │   │   │   │       ├── handler.rs
│   │   │   │   │   │       ├── messages.rs
│   │   │   │   │   │       ├── mod.rs
│   │   │   │   │   │       └── parse.rs
│   │   │   │   │   ├── test_data
│   │   │   │   │   │   ├── credential_post_order.json
│   │   │   │   │   │   ├── http_cancel_all_canceled.json
│   │   │   │   │   │   ├── http_cancel_all_close_race.json
│   │   │   │   │   │   ├── http_error_response.json
│   │   │   │   │   │   ├── http_get_executions.json
│   │   │   │   │   │   ├── http_get_instrument_xbtm26_xbtu26_spread.json
│   │   │   │   │   │   ├── http_get_instrument_xbtusd.json
│   │   │   │   │   │   ├── http_get_orders.json
│   │   │   │   │   │   ├── http_get_positions.json
│   │   │   │   │   │   ├── http_get_trade_bins.json
│   │   │   │   │   │   ├── http_get_trades.json
│   │   │   │   │   │   ├── http_get_wallet.json
│   │   │   │   │   │   ├── ws_execution_cancel_reject.json
│   │   │   │   │   │   ├── ws_execution.json
│   │   │   │   │   │   ├── ws_funding_rate.json
│   │   │   │   │   │   ├── ws_instrument_index_update.json
│   │   │   │   │   │   ├── ws_instrument_mark_update.json
│   │   │   │   │   │   ├── ws_instrument.json
│   │   │   │   │   │   ├── ws_liquidation.json
│   │   │   │   │   │   ├── ws_margin.json
│   │   │   │   │   │   ├── ws_order_avg_px.json
│   │   │   │   │   │   ├── ws_order_update_canceled.json
│   │   │   │   │   │   ├── ws_order_update_nulls.json
│   │   │   │   │   │   ├── ws_order_update_values.json
│   │   │   │   │   │   ├── ws_order.json
│   │   │   │   │   │   ├── ws_orderbook_10.json
│   │   │   │   │   │   ├── ws_orderbook_l2.json
│   │   │   │   │   │   ├── ws_position.json
│   │   │   │   │   │   ├── ws_quote.json
│   │   │   │   │   │   ├── ws_trade_bin_1m.json
│   │   │   │   │   │   ├── ws_trade.json
│   │   │   │   │   │   └── ws_wallet.json
│   │   │   │   │   └── tests
│   │   │   │   │       ├── http.rs
│   │   │   │   │       ├── python.rs
│   │   │   │   │       └── websocket.rs
│   │   │   │   ├── blockchain
│   │   │   │   │   ├── bin
│   │   │   │   │   │   └── node_wallet.rs
│   │   │   │   │   ├── Cargo.toml
│   │   │   │   │   ├── examples
│   │   │   │   │   │   └── node_data_tester.rs
│   │   │   │   │   ├── LICENSE -> ../../../LICENSE
│   │   │   │   │   ├── README.md
│   │   │   │   │   ├── src
│   │   │   │   │   │   ├── cache
│   │   │   │   │   │   │   ├── consistency.rs
│   │   │   │   │   │   │   ├── copy.rs
│   │   │   │   │   │   │   ├── database.rs
│   │   │   │   │   │   │   ├── mod.rs
│   │   │   │   │   │   │   ├── rows.rs
│   │   │   │   │   │   │   └── types.rs
│   │   │   │   │   │   ├── config.rs
│   │   │   │   │   │   ├── constants.rs
│   │   │   │   │   │   ├── contracts
│   │   │   │   │   │   │   ├── base.rs
│   │   │   │   │   │   │   ├── erc20.rs
│   │   │   │   │   │   │   ├── mod.rs
│   │   │   │   │   │   │   └── uniswap_v3_pool.rs
│   │   │   │   │   │   ├── data
│   │   │   │   │   │   │   ├── client.rs
│   │   │   │   │   │   │   ├── core.rs
│   │   │   │   │   │   │   ├── mod.rs
│   │   │   │   │   │   │   └── subscription.rs
│   │   │   │   │   │   ├── decode.rs
│   │   │   │   │   │   ├── events
│   │   │   │   │   │   │   ├── burn.rs
│   │   │   │   │   │   │   ├── collect.rs
│   │   │   │   │   │   │   ├── fee_protocol_collect.rs
│   │   │   │   │   │   │   ├── fee_protocol_update.rs
│   │   │   │   │   │   │   ├── flash.rs
│   │   │   │   │   │   │   ├── initialize.rs
│   │   │   │   │   │   │   ├── mint.rs
│   │   │   │   │   │   │   ├── mod.rs
│   │   │   │   │   │   │   ├── pool_created.rs
│   │   │   │   │   │   │   └── swap.rs
│   │   │   │   │   │   ├── exchanges
│   │   │   │   │   │   │   ├── arbitrum
│   │   │   │   │   │   │   │   ├── camelot_v3.rs
│   │   │   │   │   │   │   │   ├── curve_finance.rs
│   │   │   │   │   │   │   │   ├── fluid.rs
│   │   │   │   │   │   │   │   ├── mod.rs
│   │   │   │   │   │   │   │   ├── pancakeswap_v3.rs
│   │   │   │   │   │   │   │   ├── sushiswap_v2.rs
│   │   │   │   │   │   │   │   ├── sushiswap_v3.rs
│   │   │   │   │   │   │   │   ├── uniswap_v2.rs
│   │   │   │   │   │   │   │   ├── uniswap_v3.rs
│   │   │   │   │   │   │   │   └── uniswap_v4.rs
│   │   │   │   │   │   │   ├── base
│   │   │   │   │   │   │   │   ├── aerodrome_slipstream.rs
│   │   │   │   │   │   │   │   ├── aerodrome_v1.rs
│   │   │   │   │   │   │   │   ├── baseswap_v2.rs
│   │   │   │   │   │   │   │   ├── basex.rs
│   │   │   │   │   │   │   │   ├── mod.rs
│   │   │   │   │   │   │   │   ├── pancakeswap_v3.rs
│   │   │   │   │   │   │   │   ├── sushiswap_v3.rs
│   │   │   │   │   │   │   │   ├── uniswap_v2.rs
│   │   │   │   │   │   │   │   ├── uniswap_v3.rs
│   │   │   │   │   │   │   │   └── uniswap_v4.rs
│   │   │   │   │   │   │   ├── bsc
│   │   │   │   │   │   │   │   ├── mod.rs
│   │   │   │   │   │   │   │   ├── pancakeswap_v3.rs
│   │   │   │   │   │   │   │   └── uniswap_v3.rs
│   │   │   │   │   │   │   ├── ethereum
│   │   │   │   │   │   │   │   ├── curve_finance.rs
│   │   │   │   │   │   │   │   ├── fluid.rs
│   │   │   │   │   │   │   │   ├── mod.rs
│   │   │   │   │   │   │   │   ├── pancakeswap_v3.rs
│   │   │   │   │   │   │   │   ├── uniswap_v2.rs
│   │   │   │   │   │   │   │   ├── uniswap_v3.rs
│   │   │   │   │   │   │   │   └── uniswap_v4.rs
│   │   │   │   │   │   │   ├── extended.rs
│   │   │   │   │   │   │   ├── mod.rs
│   │   │   │   │   │   │   └── parsing
│   │   │   │   │   │   │       ├── core.rs
│   │   │   │   │   │   │       ├── mod.rs
│   │   │   │   │   │   │       ├── pancakeswap_v3
│   │   │   │   │   │   │       │   ├── fee_protocol_update.rs
│   │   │   │   │   │   │       │   ├── mod.rs
│   │   │   │   │   │   │       │   └── swap.rs
│   │   │   │   │   │   │       ├── uniswap_v2
│   │   │   │   │   │   │       │   ├── mod.rs
│   │   │   │   │   │   │       │   └── pool_created.rs
│   │   │   │   │   │   │       ├── uniswap_v3
│   │   │   │   │   │   │       │   ├── burn.rs
│   │   │   │   │   │   │       │   ├── collect.rs
│   │   │   │   │   │   │       │   ├── fee_protocol_collect.rs
│   │   │   │   │   │   │       │   ├── fee_protocol_update.rs
│   │   │   │   │   │   │       │   ├── flash.rs
│   │   │   │   │   │   │       │   ├── initialize.rs
│   │   │   │   │   │   │       │   ├── mint.rs
│   │   │   │   │   │   │       │   ├── mod.rs
│   │   │   │   │   │   │       │   ├── pool_created.rs
│   │   │   │   │   │   │       │   └── swap.rs
│   │   │   │   │   │   │       └── uniswap_v4
│   │   │   │   │   │   │           ├── initialize.rs
│   │   │   │   │   │   │           └── mod.rs
│   │   │   │   │   │   ├── execution
│   │   │   │   │   │   │   ├── client.rs
│   │   │   │   │   │   │   └── mod.rs
│   │   │   │   │   │   ├── factories.rs
│   │   │   │   │   │   ├── hypersync
│   │   │   │   │   │   │   ├── client.rs
│   │   │   │   │   │   │   ├── helpers.rs
│   │   │   │   │   │   │   ├── mod.rs
│   │   │   │   │   │   │   └── transform.rs
│   │   │   │   │   │   ├── lib.rs
│   │   │   │   │   │   ├── math.rs
│   │   │   │   │   │   ├── python
│   │   │   │   │   │   │   ├── cache.rs
│   │   │   │   │   │   │   ├── config.rs
│   │   │   │   │   │   │   ├── factories.rs
│   │   │   │   │   │   │   └── mod.rs
│   │   │   │   │   │   ├── reporting.rs
│   │   │   │   │   │   ├── rpc
│   │   │   │   │   │   │   ├── chains
│   │   │   │   │   │   │   │   ├── arbitrum.rs
│   │   │   │   │   │   │   │   ├── base.rs
│   │   │   │   │   │   │   │   ├── bsc.rs
│   │   │   │   │   │   │   │   ├── ethereum.rs
│   │   │   │   │   │   │   │   ├── mod.rs
│   │   │   │   │   │   │   │   └── polygon.rs
│   │   │   │   │   │   │   ├── core.rs
│   │   │   │   │   │   │   ├── error.rs
│   │   │   │   │   │   │   ├── helpers.rs
│   │   │   │   │   │   │   ├── http.rs
│   │   │   │   │   │   │   ├── mod.rs
│   │   │   │   │   │   │   ├── providers.rs
│   │   │   │   │   │   │   ├── types.rs
│   │   │   │   │   │   │   └── utils.rs
│   │   │   │   │   │   └── services
│   │   │   │   │   │       ├── mod.rs
│   │   │   │   │   │       └── pool_discovery.rs
│   │   │   │   │   ├── test_data
│   │   │   │   │   │   ├── pancakeswap_v3_set_fee_protocol_hypersync.json
│   │   │   │   │   │   ├── pancakeswap_v3_set_fee_protocol_rpc.json
│   │   │   │   │   │   ├── pancakeswap_v3_swap_hypersync.json
│   │   │   │   │   │   ├── pancakeswap_v3_swap_rpc.json
│   │   │   │   │   │   ├── uniswap_v3_set_fee_protocol_hypersync.json
│   │   │   │   │   │   └── uniswap_v3_set_fee_protocol_rpc.json
│   │   │   │   │   └── tests
│   │   │   │   │       ├── python.rs
│   │   │   │   │       └── rpc_reconnection.rs
│   │   │   │   ├── bybit
│   │   │   │   │   ├── benches
│   │   │   │   │   │   └── websocket.rs
│   │   │   │   │   ├── bin
│   │   │   │   │   │   ├── flatten.rs
│   │   │   │   │   │   ├── http.rs
│   │   │   │   │   │   ├── ws_data.rs
│   │   │   │   │   │   └── ws_exec.rs
│   │   │   │   │   ├── Cargo.toml
│   │   │   │   │   ├── examples
│   │   │   │   │   │   ├── node_data_tester.rs
│   │   │   │   │   │   ├── node_delta_neutral.rs
│   │   │   │   │   │   ├── node_exec_tester.rs
│   │   │   │   │   │   ├── node_greeks.rs
│   │   │   │   │   │   └── node_option_chain.rs
│   │   │   │   │   ├── LICENSE -> ../../../LICENSE
│   │   │   │   │   ├── README.md
│   │   │   │   │   ├── src
│   │   │   │   │   │   ├── common
│   │   │   │   │   │   │   ├── consts.rs
│   │   │   │   │   │   │   ├── credential.rs
│   │   │   │   │   │   │   ├── enums.rs
│   │   │   │   │   │   │   ├── instruments.rs
│   │   │   │   │   │   │   ├── mod.rs
│   │   │   │   │   │   │   ├── models.rs
│   │   │   │   │   │   │   ├── parse.rs
│   │   │   │   │   │   │   ├── status.rs
│   │   │   │   │   │   │   ├── symbol.rs
│   │   │   │   │   │   │   ├── testing.rs
│   │   │   │   │   │   │   ├── types.rs
│   │   │   │   │   │   │   └── urls.rs
│   │   │   │   │   │   ├── config.rs
│   │   │   │   │   │   ├── data.rs
│   │   │   │   │   │   ├── execution.rs
│   │   │   │   │   │   ├── factories.rs
│   │   │   │   │   │   ├── http
│   │   │   │   │   │   │   ├── client.rs
│   │   │   │   │   │   │   ├── error.rs
│   │   │   │   │   │   │   ├── mod.rs
│   │   │   │   │   │   │   ├── models.rs
│   │   │   │   │   │   │   ├── parse.rs
│   │   │   │   │   │   │   └── query.rs
│   │   │   │   │   │   ├── lib.rs
│   │   │   │   │   │   ├── python
│   │   │   │   │   │   │   ├── config.rs
│   │   │   │   │   │   │   ├── enums.rs
│   │   │   │   │   │   │   ├── factories.rs
│   │   │   │   │   │   │   ├── http.rs
│   │   │   │   │   │   │   ├── mod.rs
│   │   │   │   │   │   │   ├── params.rs
│   │   │   │   │   │   │   ├── types.rs
│   │   │   │   │   │   │   └── websocket.rs
│   │   │   │   │   │   ├── repay.rs
│   │   │   │   │   │   └── websocket
│   │   │   │   │   │       ├── client.rs
│   │   │   │   │   │       ├── dispatch.rs
│   │   │   │   │   │       ├── enums.rs
│   │   │   │   │   │       ├── error.rs
│   │   │   │   │   │       ├── handler.rs
│   │   │   │   │   │       ├── messages.rs
│   │   │   │   │   │       ├── mod.rs
│   │   │   │   │   │       └── parse.rs
│   │   │   │   │   ├── test_data
│   │   │   │   │   │   ├── http_get_account_info.json
│   │   │   │   │   │   ├── http_get_executions.json
│   │   │   │   │   │   ├── http_get_fee_rate.json
│   │   │   │   │   │   ├── http_get_funding_history.json
│   │   │   │   │   │   ├── http_get_instruments_inverse_symbol_type.json
│   │   │   │   │   │   ├── http_get_instruments_inverse.json
│   │   │   │   │   │   ├── http_get_instruments_linear_symbol_type.json
│   │   │   │   │   │   ├── http_get_instruments_linear.json
│   │   │   │   │   │   ├── http_get_instruments_option_symbol_id.json
│   │   │   │   │   │   ├── http_get_instruments_option.json
│   │   │   │   │   │   ├── http_get_instruments_spot_xstocks.json
│   │   │   │   │   │   ├── http_get_instruments_spot.json
│   │   │   │   │   │   ├── http_get_klines_linear.json
│   │   │   │   │   │   ├── http_get_order_partially_filled_rejected.json
│   │   │   │   │   │   ├── http_get_orderbook.json
│   │   │   │   │   │   ├── http_get_orders_history_with_duplicate.json
│   │   │   │   │   │   ├── http_get_orders_history.json
│   │   │   │   │   │   ├── http_get_orders_realtime_tp_sl.json
│   │   │   │   │   │   ├── http_get_orders_realtime.json
│   │   │   │   │   │   ├── http_get_positions_with_open_time.json
│   │   │   │   │   │   ├── http_get_positions.json
│   │   │   │   │   │   ├── http_get_trades_recent.json
│   │   │   │   │   │   ├── http_get_user_escrow_sub_members.json
│   │   │   │   │   │   ├── http_get_user_query_api.json
│   │   │   │   │   │   ├── http_get_user_sub_apikeys.json
│   │   │   │   │   │   ├── http_get_user_sub_members_paged.json
│   │   │   │   │   │   ├── http_get_user_sub_members.json
│   │   │   │   │   │   ├── http_get_wallet_balance_spot_short.json
│   │   │   │   │   │   ├── http_get_wallet_balance_with_spot_borrow.json
│   │   │   │   │   │   ├── http_get_wallet_balance.json
│   │   │   │   │   │   ├── http_post_user_update_master_api.json
│   │   │   │   │   │   ├── http_post_user_update_sub_api.json
│   │   │   │   │   │   ├── ws_account_execution_adl.json
│   │   │   │   │   │   ├── ws_account_execution_fast_envelope_id.json
│   │   │   │   │   │   ├── ws_account_execution_fast.json
│   │   │   │   │   │   ├── ws_account_execution.json
│   │   │   │   │   │   ├── ws_account_order_buy_stop_market.json
│   │   │   │   │   │   ├── ws_account_order_filled.json
│   │   │   │   │   │   ├── ws_account_order_limit_if_touched.json
│   │   │   │   │   │   ├── ws_account_order_market_if_touched.json
│   │   │   │   │   │   ├── ws_account_order_partially_filled_rejected.json
│   │   │   │   │   │   ├── ws_account_order_sell_market_if_touched.json
│   │   │   │   │   │   ├── ws_account_order_stop_limit.json
│   │   │   │   │   │   ├── ws_account_order_stop_loss.json
│   │   │   │   │   │   ├── ws_account_order_stop_market.json
│   │   │   │   │   │   ├── ws_account_order_take_profit.json
│   │   │   │   │   │   ├── ws_account_order.json
│   │   │   │   │   │   ├── ws_account_position_short.json
│   │   │   │   │   │   ├── ws_account_position_with_open_time.json
│   │   │   │   │   │   ├── ws_account_position.json
│   │   │   │   │   │   ├── ws_account_wallet_locked_exceeds_total.json
│   │   │   │   │   │   ├── ws_account_wallet_small_order.json
│   │   │   │   │   │   ├── ws_account_wallet.json
│   │   │   │   │   │   ├── ws_auth_failure.json
│   │   │   │   │   │   ├── ws_auth_success.json
│   │   │   │   │   │   ├── ws_kline.json
│   │   │   │   │   │   ├── ws_order_response.json
│   │   │   │   │   │   ├── ws_orderbook_delta.json
│   │   │   │   │   │   ├── ws_orderbook_snapshot.json
│   │   │   │   │   │   ├── ws_public_trade.json
│   │   │   │   │   │   ├── ws_subscription_ack.json
│   │   │   │   │   │   ├── ws_subscription_failure.json
│   │   │   │   │   │   ├── ws_ticker_linear.json
│   │   │   │   │   │   └── ws_ticker_option.json
│   │   │   │   │   └── tests
│   │   │   │   │       ├── data_client.rs
│   │   │   │   │       ├── exec_client.rs
│   │   │   │   │       ├── http.rs
│   │   │   │   │       ├── pagination.rs
│   │   │   │   │       ├── python.rs
│   │   │   │   │       └── websocket.rs
│   │   │   │   ├── coinbase
│   │   │   │   │   ├── bin
│   │   │   │   │   │   ├── cancel_all_open.rs
│   │   │   │   │   │   ├── http_private.rs
│   │   │   │   │   │   └── http_public.rs
│   │   │   │   │   ├── Cargo.toml
│   │   │   │   │   ├── examples
│   │   │   │   │   │   ├── node_data_tester.rs
│   │   │   │   │   │   └── node_exec_tester.rs
│   │   │   │   │   ├── LICENSE -> ../../../LICENSE
│   │   │   │   │   ├── README.md
│   │   │   │   │   ├── src
│   │   │   │   │   │   ├── common
│   │   │   │   │   │   │   ├── consts.rs
│   │   │   │   │   │   │   ├── credential.rs
│   │   │   │   │   │   │   ├── enums.rs
│   │   │   │   │   │   │   ├── mod.rs
│   │   │   │   │   │   │   ├── parse.rs
│   │   │   │   │   │   │   ├── testing.rs
│   │   │   │   │   │   │   └── urls.rs
│   │   │   │   │   │   ├── config.rs
│   │   │   │   │   │   ├── data
│   │   │   │   │   │   │   ├── mod.rs
│   │   │   │   │   │   │   └── poll.rs
│   │   │   │   │   │   ├── execution.rs
│   │   │   │   │   │   ├── factories.rs
│   │   │   │   │   │   ├── http
│   │   │   │   │   │   │   ├── client.rs
│   │   │   │   │   │   │   ├── error.rs
│   │   │   │   │   │   │   ├── mod.rs
│   │   │   │   │   │   │   ├── models.rs
│   │   │   │   │   │   │   ├── parse.rs
│   │   │   │   │   │   │   └── query.rs
│   │   │   │   │   │   ├── lib.rs
│   │   │   │   │   │   ├── provider.rs
│   │   │   │   │   │   ├── python
│   │   │   │   │   │   │   ├── config.rs
│   │   │   │   │   │   │   ├── enums.rs
│   │   │   │   │   │   │   ├── factories.rs
│   │   │   │   │   │   │   └── mod.rs
│   │   │   │   │   │   └── websocket
│   │   │   │   │   │       ├── client.rs
│   │   │   │   │   │       ├── error.rs
│   │   │   │   │   │       ├── handler.rs
│   │   │   │   │   │       ├── messages.rs
│   │   │   │   │   │       ├── mod.rs
│   │   │   │   │   │       └── parse.rs
│   │   │   │   │   ├── test_data
│   │   │   │   │   │   ├── http_accounts.json
│   │   │   │   │   │   ├── http_candles.json
│   │   │   │   │   │   ├── http_cfm_balance_summary.json
│   │   │   │   │   │   ├── http_cfm_position.json
│   │   │   │   │   │   ├── http_cfm_positions.json
│   │   │   │   │   │   ├── http_fills.json
│   │   │   │   │   │   ├── http_order.json
│   │   │   │   │   │   ├── http_orders_list.json
│   │   │   │   │   │   ├── http_product_book.json
│   │   │   │   │   │   ├── http_product.json
│   │   │   │   │   │   ├── http_products_future.json
│   │   │   │   │   │   ├── http_products.json
│   │   │   │   │   │   ├── http_ticker.json
│   │   │   │   │   │   ├── ws_candles.json
│   │   │   │   │   │   ├── ws_heartbeats.json
│   │   │   │   │   │   ├── ws_l2_data_snapshot.json
│   │   │   │   │   │   ├── ws_l2_data_update.json
│   │   │   │   │   │   ├── ws_market_trades.json
│   │   │   │   │   │   ├── ws_subscriptions.json
│   │   │   │   │   │   ├── ws_ticker.json
│   │   │   │   │   │   └── ws_user.json
│   │   │   │   │   └── tests
│   │   │   │   │       ├── data_client.rs
│   │   │   │   │       ├── exec_client.rs
│   │   │   │   │       ├── python.rs
│   │   │   │   │       └── websocket.rs
│   │   │   │   ├── databento
│   │   │   │   │   ├── benches
│   │   │   │   │   │   ├── BENCHMARKS.md
│   │   │   │   │   │   ├── clients.rs
│   │   │   │   │   │   ├── common
│   │   │   │   │   │   │   └── mod.rs
│   │   │   │   │   │   ├── data.rs
│   │   │   │   │   │   └── micros.rs
│   │   │   │   │   ├── Cargo.toml
│   │   │   │   │   ├── examples
│   │   │   │   │   │   └── node_data_tester.rs
│   │   │   │   │   ├── LICENSE -> ../../../LICENSE
│   │   │   │   │   ├── publishers.json
│   │   │   │   │   ├── README.md
│   │   │   │   │   ├── src
│   │   │   │   │   │   ├── arrow
│   │   │   │   │   │   │   ├── imbalance.rs
│   │   │   │   │   │   │   ├── mod.rs
│   │   │   │   │   │   │   └── statistics.rs
│   │   │   │   │   │   ├── common.rs
│   │   │   │   │   │   ├── data.rs
│   │   │   │   │   │   ├── decode
│   │   │   │   │   │   │   ├── custom.rs
│   │   │   │   │   │   │   ├── expiration.rs
│   │   │   │   │   │   │   ├── instruments.rs
│   │   │   │   │   │   │   ├── market_data.rs
│   │   │   │   │   │   │   ├── mod.rs
│   │   │   │   │   │   │   ├── primitives.rs
│   │   │   │   │   │   │   └── tests.rs
│   │   │   │   │   │   ├── enums.rs
│   │   │   │   │   │   ├── factories.rs
│   │   │   │   │   │   ├── historical.rs
│   │   │   │   │   │   ├── lib.rs
│   │   │   │   │   │   ├── live.rs
│   │   │   │   │   │   ├── loader.rs
│   │   │   │   │   │   ├── python
│   │   │   │   │   │   │   ├── arrow.rs
│   │   │   │   │   │   │   ├── data.rs
│   │   │   │   │   │   │   ├── enums.rs
│   │   │   │   │   │   │   ├── factories.rs
│   │   │   │   │   │   │   ├── historical.rs
│   │   │   │   │   │   │   ├── live.rs
│   │   │   │   │   │   │   ├── loader.rs
│   │   │   │   │   │   │   ├── mod.rs
│   │   │   │   │   │   │   └── types.rs
│   │   │   │   │   │   ├── symbology.rs
│   │   │   │   │   │   └── types.rs
│   │   │   │   │   ├── test_data
│   │   │   │   │   │   ├── test_data.bbo-1m.dbn.zst
│   │   │   │   │   │   ├── test_data.bbo-1s.dbn.zst
│   │   │   │   │   │   ├── test_data.cbbo-1s.dbn.zst
│   │   │   │   │   │   ├── test_data.cmbp-1.dbn.zst
│   │   │   │   │   │   ├── test_data.definition.equity.dbn.zst
│   │   │   │   │   │   ├── test_data.definition.futures_contract.dbn.zst
│   │   │   │   │   │   ├── test_data.definition.futures_spread.dbn.zst
│   │   │   │   │   │   ├── test_data.definition.option_spread.dbn.zst
│   │   │   │   │   │   ├── test_data.definition.option.dbn.zst
│   │   │   │   │   │   ├── test_data.imbalance.dbn.zst
│   │   │   │   │   │   ├── test_data.mbo.dbn
│   │   │   │   │   │   ├── test_data.mbo.dbn.zst
│   │   │   │   │   │   ├── test_data.mbp-1.dbn.zst
│   │   │   │   │   │   ├── test_data.mbp-10.dbn.zst
│   │   │   │   │   │   ├── test_data.ohlcv-1d.dbn.zst
│   │   │   │   │   │   ├── test_data.ohlcv-1h.dbn.zst
│   │   │   │   │   │   ├── test_data.ohlcv-1m.dbn.zst
│   │   │   │   │   │   ├── test_data.ohlcv-1s.dbn.zst
│   │   │   │   │   │   ├── test_data.statistics.dbn.zst
│   │   │   │   │   │   ├── test_data.status.dbn.zst
│   │   │   │   │   │   ├── test_data.tbbo.dbn.zst
│   │   │   │   │   │   └── test_data.trades.dbn.zst
│   │   │   │   │   └── tests
│   │   │   │   │       ├── common
│   │   │   │   │       │   ├── mock_server.rs
│   │   │   │   │       │   └── mod.rs
│   │   │   │   │       ├── feed_handler.rs
│   │   │   │   │       └── python.rs
│   │   │   │   ├── deribit
│   │   │   │   │   ├── benches
│   │   │   │   │   │   └── websocket.rs
│   │   │   │   │   ├── bin
│   │   │   │   │   │   ├── http_private.rs
│   │   │   │   │   │   ├── http_public.rs
│   │   │   │   │   │   └── ws_data.rs
│   │   │   │   │   ├── Cargo.toml
│   │   │   │   │   ├── examples
│   │   │   │   │   │   ├── node_data_tester.rs
│   │   │   │   │   │   ├── node_exec_tester.rs
│   │   │   │   │   │   ├── node_greeks.rs
│   │   │   │   │   │   └── node_option_chain.rs
│   │   │   │   │   ├── LICENSE -> ../../../LICENSE
│   │   │   │   │   ├── README.md
│   │   │   │   │   ├── src
│   │   │   │   │   │   ├── common
│   │   │   │   │   │   │   ├── consts.rs
│   │   │   │   │   │   │   ├── credential.rs
│   │   │   │   │   │   │   ├── enums.rs
│   │   │   │   │   │   │   ├── mod.rs
│   │   │   │   │   │   │   ├── models.rs
│   │   │   │   │   │   │   ├── parse.rs
│   │   │   │   │   │   │   ├── rpc.rs
│   │   │   │   │   │   │   ├── testing.rs
│   │   │   │   │   │   │   └── urls.rs
│   │   │   │   │   │   ├── config.rs
│   │   │   │   │   │   ├── data_types.rs
│   │   │   │   │   │   ├── data.rs
│   │   │   │   │   │   ├── execution.rs
│   │   │   │   │   │   ├── factories.rs
│   │   │   │   │   │   ├── http
│   │   │   │   │   │   │   ├── client.rs
│   │   │   │   │   │   │   ├── error.rs
│   │   │   │   │   │   │   ├── mod.rs
│   │   │   │   │   │   │   ├── models.rs
│   │   │   │   │   │   │   └── query.rs
│   │   │   │   │   │   ├── lib.rs
│   │   │   │   │   │   ├── python
│   │   │   │   │   │   │   ├── config.rs
│   │   │   │   │   │   │   ├── enums.rs
│   │   │   │   │   │   │   ├── factories.rs
│   │   │   │   │   │   │   ├── http.rs
│   │   │   │   │   │   │   ├── mod.rs
│   │   │   │   │   │   │   ├── urls.rs
│   │   │   │   │   │   │   └── websocket.rs
│   │   │   │   │   │   └── websocket
│   │   │   │   │   │       ├── auth.rs
│   │   │   │   │   │       ├── client.rs
│   │   │   │   │   │       ├── enums.rs
│   │   │   │   │   │       ├── error.rs
│   │   │   │   │   │       ├── handler.rs
│   │   │   │   │   │       ├── messages.rs
│   │   │   │   │   │       ├── mod.rs
│   │   │   │   │   │       └── parse.rs
│   │   │   │   │   ├── test_data
│   │   │   │   │   │   ├── http_get_account_summaries_cross_margin.json
│   │   │   │   │   │   ├── http_get_account_summaries.json
│   │   │   │   │   │   ├── http_get_book_summary_by_currency.json
│   │   │   │   │   │   ├── http_get_combos.json
│   │   │   │   │   │   ├── http_get_expirations_any.json
│   │   │   │   │   │   ├── http_get_expirations_btc_option.json
│   │   │   │   │   │   ├── http_get_instrument_option.json
│   │   │   │   │   │   ├── http_get_instrument.json
│   │   │   │   │   │   ├── http_get_instruments_future_combo.json
│   │   │   │   │   │   ├── http_get_instruments_option_combo.json
│   │   │   │   │   │   ├── http_get_instruments.json
│   │   │   │   │   │   ├── http_get_last_trades_future_combo.json
│   │   │   │   │   │   ├── http_get_last_trades_historical_combo.json
│   │   │   │   │   │   ├── http_get_last_trades_option_combo.json
│   │   │   │   │   │   ├── http_get_last_trades_perpetual_with_combo_tags.json
│   │   │   │   │   │   ├── http_get_last_trades.json
│   │   │   │   │   │   ├── http_get_order_book.json
│   │   │   │   │   │   ├── http_get_time.json
│   │   │   │   │   │   ├── http_get_tradingview_chart_data.json
│   │   │   │   │   │   ├── http_test.json
│   │   │   │   │   │   ├── ws_book_delta.json
│   │   │   │   │   │   ├── ws_book_grouped_snapshot.json
│   │   │   │   │   │   ├── ws_book_snapshot.json
│   │   │   │   │   │   ├── ws_chart.json
│   │   │   │   │   │   ├── ws_error.json
│   │   │   │   │   │   ├── ws_order_buy_response.json
│   │   │   │   │   │   ├── ws_order_cancel_response.json
│   │   │   │   │   │   ├── ws_order_edit_response.json
│   │   │   │   │   │   ├── ws_order_sell_response.json
│   │   │   │   │   │   ├── ws_order_stop_market_no_filled_amount.json
│   │   │   │   │   │   ├── ws_order_stop_market_response.json
│   │   │   │   │   │   ├── ws_portfolio.json
│   │   │   │   │   │   ├── ws_quote.json
│   │   │   │   │   │   ├── ws_subscribe_response.json
│   │   │   │   │   │   ├── ws_test_request.json
│   │   │   │   │   │   ├── ws_ticker.json
│   │   │   │   │   │   ├── ws_trades_option_combo.json
│   │   │   │   │   │   ├── ws_trades.json
│   │   │   │   │   │   └── ws_volatility_index.json
│   │   │   │   │   └── tests
│   │   │   │   │       ├── data_client.rs
│   │   │   │   │       ├── exec_client.rs
│   │   │   │   │       ├── http_private.rs
│   │   │   │   │       ├── http_public.rs
│   │   │   │   │       ├── python.rs
│   │   │   │   │       └── websocket.rs
│   │   │   │   ├── derive
│   │   │   │   │   ├── benches
│   │   │   │   │   │   ├── BENCHMARKS.md
│   │   │   │   │   │   ├── common
│   │   │   │   │   │   │   └── mod.rs
│   │   │   │   │   │   ├── data.rs
│   │   │   │   │   │   ├── exec.rs
│   │   │   │   │   │   ├── micros.rs
│   │   │   │   │   │   └── signing.rs
│   │   │   │   │   ├── bin
│   │   │   │   │   │   ├── flatten.rs
│   │   │   │   │   │   └── spot_research.rs
│   │   │   │   │   ├── Cargo.toml
│   │   │   │   │   ├── examples
│   │   │   │   │   │   ├── node_data_tester.rs
│   │   │   │   │   │   ├── node_delta_neutral.rs
│   │   │   │   │   │   └── node_exec_tester.rs
│   │   │   │   │   ├── fuzz
│   │   │   │   │   │   ├── fuzz_targets
│   │   │   │   │   │   │   ├── fuzz_action_hash.rs
│   │   │   │   │   │   │   ├── fuzz_decimal_decode.rs
│   │   │   │   │   │   │   ├── fuzz_nonce_sequence.rs
│   │   │   │   │   │   │   ├── fuzz_trade_module_encode.rs
│   │   │   │   │   │   │   └── fuzz_ws_decode.rs
│   │   │   │   │   │   └── README.md
│   │   │   │   │   ├── README.md
│   │   │   │   │   ├── src
│   │   │   │   │   │   ├── common
│   │   │   │   │   │   │   ├── consts.rs
│   │   │   │   │   │   │   ├── credential.rs
│   │   │   │   │   │   │   ├── enums.rs
│   │   │   │   │   │   │   ├── error.rs
│   │   │   │   │   │   │   ├── mod.rs
│   │   │   │   │   │   │   ├── parse.rs
│   │   │   │   │   │   │   ├── rate_limit.rs
│   │   │   │   │   │   │   ├── retry.rs
│   │   │   │   │   │   │   └── urls.rs
│   │   │   │   │   │   ├── config.rs
│   │   │   │   │   │   ├── data.rs
│   │   │   │   │   │   ├── execution.rs
│   │   │   │   │   │   ├── factories.rs
│   │   │   │   │   │   ├── http
│   │   │   │   │   │   │   ├── client.rs
│   │   │   │   │   │   │   ├── error.rs
│   │   │   │   │   │   │   ├── mod.rs
│   │   │   │   │   │   │   ├── models.rs
│   │   │   │   │   │   │   ├── parse.rs
│   │   │   │   │   │   │   └── query.rs
│   │   │   │   │   │   ├── lib.rs
│   │   │   │   │   │   ├── providers.rs
│   │   │   │   │   │   ├── python
│   │   │   │   │   │   │   ├── config.rs
│   │   │   │   │   │   │   ├── enums.rs
│   │   │   │   │   │   │   ├── factories.rs
│   │   │   │   │   │   │   └── mod.rs
│   │   │   │   │   │   ├── signing
│   │   │   │   │   │   │   ├── auth.rs
│   │   │   │   │   │   │   ├── context.rs
│   │   │   │   │   │   │   ├── eip712.rs
│   │   │   │   │   │   │   ├── encoding.rs
│   │   │   │   │   │   │   ├── mod.rs
│   │   │   │   │   │   │   ├── modules
│   │   │   │   │   │   │   │   ├── mod.rs
│   │   │   │   │   │   │   │   └── trade.rs
│   │   │   │   │   │   │   └── nonce.rs
│   │   │   │   │   │   └── websocket
│   │   │   │   │   │       ├── client.rs
│   │   │   │   │   │       ├── context.rs
│   │   │   │   │   │       ├── dispatch.rs
│   │   │   │   │   │       ├── error.rs
│   │   │   │   │   │       ├── handler.rs
│   │   │   │   │   │       ├── messages.rs
│   │   │   │   │   │       ├── mod.rs
│   │   │   │   │   │       └── parse.rs
│   │   │   │   │   ├── test_data
│   │   │   │   │   │   ├── common
│   │   │   │   │   │   │   ├── http_get_instruments_btc_empty.json
│   │   │   │   │   │   │   ├── http_get_instruments_eth_all.json
│   │   │   │   │   │   │   ├── http_subaccount_high_scale.json
│   │   │   │   │   │   │   ├── http_subaccount_unknown_variants.json
│   │   │   │   │   │   │   ├── http_subaccount_usdc.json
│   │   │   │   │   │   │   ├── private_order_history_params_required.json
│   │   │   │   │   │   │   ├── private_order_params_limit.json
│   │   │   │   │   │   │   ├── private_replace_params_reduce_mmp.json
│   │   │   │   │   │   │   ├── private_trigger_order_params_stop_market.json
│   │   │   │   │   │   │   ├── ws_cancel_by_label_nonzero.json
│   │   │   │   │   │   │   └── ws_cancel_by_label_zero.json
│   │   │   │   │   │   ├── options
│   │   │   │   │   │   │   ├── http_ticker_eth_snapshot.json
│   │   │   │   │   │   │   ├── instrument_eth.json
│   │   │   │   │   │   │   ├── ws_ticker_slim_eth_call.json
│   │   │   │   │   │   │   ├── ws_ticker_slim_eth_put.json
│   │   │   │   │   │   │   └── ws_trade_eth.json
│   │   │   │   │   │   ├── perps
│   │   │   │   │   │   │   ├── http_get_instrument_eth.json
│   │   │   │   │   │   │   ├── http_get_instruments_eth.json
│   │   │   │   │   │   │   ├── http_order_eth_partially_filled.json
│   │   │   │   │   │   │   ├── http_orders_result_eth_unknown_variants.json
│   │   │   │   │   │   │   ├── http_position_eth.json
│   │   │   │   │   │   │   ├── http_positions_result_eth.json
│   │   │   │   │   │   │   ├── http_private_trade_eth.json
│   │   │   │   │   │   │   ├── http_public_candles_eth.json
│   │   │   │   │   │   │   ├── http_public_funding_rate_history_eth.json
│   │   │   │   │   │   │   ├── http_public_trade_eth_sell.json
│   │   │   │   │   │   │   ├── http_public_trades_result_eth.json
│   │   │   │   │   │   │   ├── http_ticker_eth_snapshot.json
│   │   │   │   │   │   │   ├── http_trades_result_eth_unknown_variants.json
│   │   │   │   │   │   │   ├── http_trades_result_eth.json
│   │   │   │   │   │   │   ├── instrument_eth.json
│   │   │   │   │   │   │   ├── ws_orderbook_eth.json
│   │   │   │   │   │   │   ├── ws_ticker_eth.json
│   │   │   │   │   │   │   ├── ws_ticker_slim_eth.json
│   │   │   │   │   │   │   └── ws_trade_eth.json
│   │   │   │   │   │   └── spot
│   │   │   │   │   │       ├── http_get_instruments_eth.json
│   │   │   │   │   │       ├── http_submit_order_request.json
│   │   │   │   │   │       ├── http_submit_order_response_mainnet.json
│   │   │   │   │   │       ├── http_submit_order_response.json
│   │   │   │   │   │       ├── instrument_eth_mainnet.json
│   │   │   │   │   │       ├── instrument_eth.json
│   │   │   │   │   │       ├── ws_orderbook_eth_mainnet.json
│   │   │   │   │   │       ├── ws_orderbook_eth.json
│   │   │   │   │   │       ├── ws_subscribe_ack.json
│   │   │   │   │   │       ├── ws_ticker_slim_eth_mainnet.json
│   │   │   │   │   │       ├── ws_ticker_slim_eth.json
│   │   │   │   │   │       └── ws_trade_eth.json
│   │   │   │   │   └── tests
│   │   │   │   │       ├── data_client.rs
│   │   │   │   │       ├── exec_client.rs
│   │   │   │   │       ├── http.rs
│   │   │   │   │       ├── providers.rs
│   │   │   │   │       ├── python.rs
│   │   │   │   │       └── websocket.rs
│   │   │   │   ├── dydx
│   │   │   │   │   ├── bin
│   │   │   │   │   │   ├── grpc_exec.rs
│   │   │   │   │   │   ├── http_private.rs
│   │   │   │   │   │   ├── http_public.rs
│   │   │   │   │   │   ├── ws_data.rs
│   │   │   │   │   │   └── ws_exec.rs
│   │   │   │   │   ├── Cargo.toml
│   │   │   │   │   ├── examples
│   │   │   │   │   │   ├── node_data_tester.rs
│   │   │   │   │   │   ├── node_exec_tester.rs
│   │   │   │   │   │   └── node_grid_mm.rs
│   │   │   │   │   ├── LICENSE -> ../../../LICENSE
│   │   │   │   │   ├── README.md
│   │   │   │   │   ├── src
│   │   │   │   │   │   ├── common
│   │   │   │   │   │   │   ├── consts.rs
│   │   │   │   │   │   │   ├── credential.rs
│   │   │   │   │   │   │   ├── enums.rs
│   │   │   │   │   │   │   ├── instrument_cache.rs
│   │   │   │   │   │   │   ├── mod.rs
│   │   │   │   │   │   │   ├── models.rs
│   │   │   │   │   │   │   ├── parse.rs
│   │   │   │   │   │   │   ├── testing.rs
│   │   │   │   │   │   │   └── urls.rs
│   │   │   │   │   │   ├── config.rs
│   │   │   │   │   │   ├── data.rs
│   │   │   │   │   │   ├── error.rs
│   │   │   │   │   │   ├── execution
│   │   │   │   │   │   │   ├── block_time.rs
│   │   │   │   │   │   │   ├── broadcaster.rs
│   │   │   │   │   │   │   ├── encoder.rs
│   │   │   │   │   │   │   ├── mod.rs
│   │   │   │   │   │   │   ├── order_builder.rs
│   │   │   │   │   │   │   ├── submitter.rs
│   │   │   │   │   │   │   ├── tx_manager.rs
│   │   │   │   │   │   │   ├── types.rs
│   │   │   │   │   │   │   └── wallet.rs
│   │   │   │   │   │   ├── factories.rs
│   │   │   │   │   │   ├── grpc
│   │   │   │   │   │   │   ├── builder.rs
│   │   │   │   │   │   │   ├── client.rs
│   │   │   │   │   │   │   ├── mod.rs
│   │   │   │   │   │   │   ├── order.rs
│   │   │   │   │   │   │   └── types.rs
│   │   │   │   │   │   ├── http
│   │   │   │   │   │   │   ├── client.rs
│   │   │   │   │   │   │   ├── error.rs
│   │   │   │   │   │   │   ├── mod.rs
│   │   │   │   │   │   │   ├── models.rs
│   │   │   │   │   │   │   ├── parse.rs
│   │   │   │   │   │   │   └── query.rs
│   │   │   │   │   │   ├── lib.rs
│   │   │   │   │   │   ├── proto
│   │   │   │   │   │   │   └── mod.rs
│   │   │   │   │   │   ├── python
│   │   │   │   │   │   │   ├── config.rs
│   │   │   │   │   │   │   ├── encoder.rs
│   │   │   │   │   │   │   ├── enums.rs
│   │   │   │   │   │   │   ├── factories.rs
│   │   │   │   │   │   │   ├── grpc.rs
│   │   │   │   │   │   │   ├── http.rs
│   │   │   │   │   │   │   ├── mod.rs
│   │   │   │   │   │   │   ├── submitter.rs
│   │   │   │   │   │   │   ├── types.rs
│   │   │   │   │   │   │   ├── urls.rs
│   │   │   │   │   │   │   ├── wallet.rs
│   │   │   │   │   │   │   └── websocket.rs
│   │   │   │   │   │   ├── types.rs
│   │   │   │   │   │   └── websocket
│   │   │   │   │   │       ├── client.rs
│   │   │   │   │   │       ├── dispatch.rs
│   │   │   │   │   │       ├── enums.rs
│   │   │   │   │   │       ├── error.rs
│   │   │   │   │   │       ├── handler.rs
│   │   │   │   │   │       ├── messages.rs
│   │   │   │   │   │       ├── mod.rs
│   │   │   │   │   │       └── parse.rs
│   │   │   │   │   ├── test_data
│   │   │   │   │   │   ├── http_get_block_height.json
│   │   │   │   │   │   ├── http_get_candles.json
│   │   │   │   │   │   ├── http_get_fills.json
│   │   │   │   │   │   ├── http_get_historical_funding.json
│   │   │   │   │   │   ├── http_get_orderbook.json
│   │   │   │   │   │   ├── http_get_orders.json
│   │   │   │   │   │   ├── http_get_perpetual_markets.json
│   │   │   │   │   │   ├── http_get_subaccount.json
│   │   │   │   │   │   ├── http_get_time.json
│   │   │   │   │   │   ├── http_get_trades.json
│   │   │   │   │   │   ├── http_get_transfers.json
│   │   │   │   │   │   ├── ws_block_height_subscribed.json
│   │   │   │   │   │   ├── ws_block_height_update.json
│   │   │   │   │   │   ├── ws_candles_subscribed.json
│   │   │   │   │   │   ├── ws_candles_update.json
│   │   │   │   │   │   ├── ws_error.json
│   │   │   │   │   │   ├── ws_markets_status_update.json
│   │   │   │   │   │   ├── ws_markets_subscribed.json
│   │   │   │   │   │   ├── ws_markets_update.json
│   │   │   │   │   │   ├── ws_orderbook_subscribed.json
│   │   │   │   │   │   ├── ws_orderbook_update.json
│   │   │   │   │   │   ├── ws_subaccounts_subscribed.json
│   │   │   │   │   │   ├── ws_subaccounts_update.json
│   │   │   │   │   │   ├── ws_trades_subscribed.json
│   │   │   │   │   │   └── ws_trades_update.json
│   │   │   │   │   └── tests
│   │   │   │   │       ├── data_client.rs
│   │   │   │   │       ├── exec_client.rs
│   │   │   │   │       ├── grpc.rs
│   │   │   │   │       ├── http.rs
│   │   │   │   │       ├── python.rs
│   │   │   │   │       └── websocket.rs
│   │   │   │   ├── hyperliquid
│   │   │   │   │   ├── benches
│   │   │   │   │   │   ├── BENCHMARKS.md
│   │   │   │   │   │   ├── common
│   │   │   │   │   │   │   └── mod.rs
│   │   │   │   │   │   ├── data.rs
│   │   │   │   │   │   ├── exec.rs
│   │   │   │   │   │   ├── micros.rs
│   │   │   │   │   │   └── signing.rs
│   │   │   │   │   ├── bin
│   │   │   │   │   │   ├── builder_fee_approve.rs
│   │   │   │   │   │   ├── builder_fee_revoke.rs
│   │   │   │   │   │   ├── capture_test_data.rs
│   │   │   │   │   │   ├── flatten.rs
│   │   │   │   │   │   ├── http_exec.rs
│   │   │   │   │   │   ├── http_outcome_order.rs
│   │   │   │   │   │   ├── http_private.rs
│   │   │   │   │   │   ├── http_public.rs
│   │   │   │   │   │   ├── http_user_outcome.rs
│   │   │   │   │   │   ├── ws_data.rs
│   │   │   │   │   │   └── ws_exec.rs
│   │   │   │   │   ├── Cargo.toml
│   │   │   │   │   ├── examples
│   │   │   │   │   │   ├── chained_modify_smoke.rs
│   │   │   │   │   │   ├── node_data_tester.rs
│   │   │   │   │   │   ├── node_exec_tester.rs
│   │   │   │   │   │   └── node_outcome_exec_tester.rs
│   │   │   │   │   ├── LICENSE -> ../../../LICENSE
│   │   │   │   │   ├── README.md
│   │   │   │   │   ├── src
│   │   │   │   │   │   ├── account.rs
│   │   │   │   │   │   ├── common
│   │   │   │   │   │   │   ├── builder_fee.rs
│   │   │   │   │   │   │   ├── consts.rs
│   │   │   │   │   │   │   ├── converters.rs
│   │   │   │   │   │   │   ├── credential.rs
│   │   │   │   │   │   │   ├── enums.rs
│   │   │   │   │   │   │   ├── mod.rs
│   │   │   │   │   │   │   ├── models.rs
│   │   │   │   │   │   │   ├── parse.rs
│   │   │   │   │   │   │   ├── testing.rs
│   │   │   │   │   │   │   └── types.rs
│   │   │   │   │   │   ├── config.rs
│   │   │   │   │   │   ├── data_types.rs
│   │   │   │   │   │   ├── data.rs
│   │   │   │   │   │   ├── execution.rs
│   │   │   │   │   │   ├── factories.rs
│   │   │   │   │   │   ├── http
│   │   │   │   │   │   │   ├── client.rs
│   │   │   │   │   │   │   ├── error.rs
│   │   │   │   │   │   │   ├── mod.rs
│   │   │   │   │   │   │   ├── models.rs
│   │   │   │   │   │   │   ├── parse.rs
│   │   │   │   │   │   │   ├── query.rs
│   │   │   │   │   │   │   └── rate_limits.rs
│   │   │   │   │   │   ├── lib.rs
│   │   │   │   │   │   ├── outcome_settlement.rs
│   │   │   │   │   │   ├── python
│   │   │   │   │   │   │   ├── arrow.rs
│   │   │   │   │   │   │   ├── config.rs
│   │   │   │   │   │   │   ├── enums.rs
│   │   │   │   │   │   │   ├── factories.rs
│   │   │   │   │   │   │   ├── http.rs
│   │   │   │   │   │   │   ├── mod.rs
│   │   │   │   │   │   │   └── websocket.rs
│   │   │   │   │   │   ├── signing
│   │   │   │   │   │   │   ├── mod.rs
│   │   │   │   │   │   │   ├── nonce.rs
│   │   │   │   │   │   │   ├── signers.rs
│   │   │   │   │   │   │   └── types.rs
│   │   │   │   │   │   └── websocket
│   │   │   │   │   │       ├── book.rs
│   │   │   │   │   │       ├── client.rs
│   │   │   │   │   │       ├── dispatch.rs
│   │   │   │   │   │       ├── enums.rs
│   │   │   │   │   │       ├── error.rs
│   │   │   │   │   │       ├── handler.rs
│   │   │   │   │   │       ├── messages.rs
│   │   │   │   │   │       ├── mod.rs
│   │   │   │   │   │       ├── parse.rs
│   │   │   │   │   │       ├── post.rs
│   │   │   │   │   │       └── trades.rs
│   │   │   │   │   ├── test_data
│   │   │   │   │   │   ├── http_all_perp_metas_non_usdc_collateral.json
│   │   │   │   │   │   ├── http_clearinghouse_state_negative_total_raw_usd.json
│   │   │   │   │   │   ├── http_funding_history.json
│   │   │   │   │   │   ├── http_l2_book_btc.json
│   │   │   │   │   │   ├── http_l2_book_snapshot.json
│   │   │   │   │   │   ├── http_meta_perp_sample.json
│   │   │   │   │   │   ├── http_recent_trades_btc.json
│   │   │   │   │   │   ├── http_spot_clearinghouse_state.json
│   │   │   │   │   │   ├── http_spot_meta_non_usdc_collateral.json
│   │   │   │   │   │   ├── http_user_fills_dust_conversion.json
│   │   │   │   │   │   ├── README.md
│   │   │   │   │   │   ├── ws_all_dexs_asset_ctxs.json
│   │   │   │   │   │   ├── ws_allmids.json
│   │   │   │   │   │   ├── ws_book_data.json
│   │   │   │   │   │   ├── ws_user_fill_liquidation.json
│   │   │   │   │   │   ├── ws_user_twap_history.json
│   │   │   │   │   │   └── ws_user_twap_slice_fills.json
│   │   │   │   │   └── tests
│   │   │   │   │       ├── catalog.rs
│   │   │   │   │       ├── data_client.rs
│   │   │   │   │       ├── dispatch.rs
│   │   │   │   │       ├── exec_client.rs
│   │   │   │   │       ├── http.rs
│   │   │   │   │       ├── python.rs
│   │   │   │   │       └── websocket.rs
│   │   │   │   ├── interactive_brokers
│   │   │   │   │   ├── Cargo.toml
│   │   │   │   │   ├── examples
│   │   │   │   │   │   ├── node_data_tester.rs
│   │   │   │   │   │   └── node_exec_tester.rs
│   │   │   │   │   ├── LICENSE -> ../../../LICENSE
│   │   │   │   │   ├── README.md
│   │   │   │   │   ├── src
│   │   │   │   │   │   ├── common
│   │   │   │   │   │   │   ├── connection.rs
│   │   │   │   │   │   │   ├── consts.rs
│   │   │   │   │   │   │   ├── contracts.rs
│   │   │   │   │   │   │   ├── enums
│   │   │   │   │   │   │   │   ├── contracts.rs
│   │   │   │   │   │   │   │   ├── market_data.rs
│   │   │   │   │   │   │   │   ├── misc.rs
│   │   │   │   │   │   │   │   └── order.rs
│   │   │   │   │   │   │   ├── enums.rs
│   │   │   │   │   │   │   ├── mod.rs
│   │   │   │   │   │   │   ├── parse.rs
│   │   │   │   │   │   │   ├── shared_client.rs
│   │   │   │   │   │   │   └── types.rs
│   │   │   │   │   │   ├── config.rs
│   │   │   │   │   │   ├── data
│   │   │   │   │   │   │   ├── cache.rs
│   │   │   │   │   │   │   ├── convert.rs
│   │   │   │   │   │   │   ├── core_streams.rs
│   │   │   │   │   │   │   ├── core.rs
│   │   │   │   │   │   │   ├── mod.rs
│   │   │   │   │   │   │   └── parse.rs
│   │   │   │   │   │   ├── error.rs
│   │   │   │   │   │   ├── execution
│   │   │   │   │   │   │   ├── account.rs
│   │   │   │   │   │   │   ├── conditions.rs
│   │   │   │   │   │   │   ├── core_helpers.rs
│   │   │   │   │   │   │   ├── core_orders.rs
│   │   │   │   │   │   │   ├── core_tests.rs
│   │   │   │   │   │   │   ├── core_updates.rs
│   │   │   │   │   │   │   ├── core.rs
│   │   │   │   │   │   │   ├── mod.rs
│   │   │   │   │   │   │   ├── parse.rs
│   │   │   │   │   │   │   ├── transform
│   │   │   │   │   │   │   │   ├── policy.rs
│   │   │   │   │   │   │   │   └── tags.rs
│   │   │   │   │   │   │   └── transform.rs
│   │   │   │   │   │   ├── factories.rs
│   │   │   │   │   │   ├── gateway
│   │   │   │   │   │   │   ├── dockerized.rs
│   │   │   │   │   │   │   └── mod.rs
│   │   │   │   │   │   ├── historical
│   │   │   │   │   │   │   ├── client.rs
│   │   │   │   │   │   │   └── mod.rs
│   │   │   │   │   │   ├── lib.rs
│   │   │   │   │   │   ├── providers
│   │   │   │   │   │   │   ├── instruments.rs
│   │   │   │   │   │   │   ├── mod.rs
│   │   │   │   │   │   │   ├── parse.rs
│   │   │   │   │   │   │   └── tests.rs
│   │   │   │   │   │   └── python
│   │   │   │   │   │       ├── config.rs
│   │   │   │   │   │       ├── conversion.rs
│   │   │   │   │   │       ├── enums.rs
│   │   │   │   │   │       ├── factories.rs
│   │   │   │   │   │       ├── gateway.rs
│   │   │   │   │   │       ├── historical.rs
│   │   │   │   │   │       ├── mod.rs
│   │   │   │   │   │       └── providers.rs
│   │   │   │   │   ├── test_data
│   │   │   │   │   │   └── instrument_cache_chrono.json
│   │   │   │   │   └── tests
│   │   │   │   │       ├── connection.rs
│   │   │   │   │       └── python.rs
│   │   │   │   ├── kraken
│   │   │   │   │   ├── benches
│   │   │   │   │   │   └── websocket.rs
│   │   │   │   │   ├── bin
│   │   │   │   │   │   ├── http_spot_public.rs
│   │   │   │   │   │   ├── http_spot_raw.rs
│   │   │   │   │   │   └── ws_spot_data.rs
│   │   │   │   │   ├── Cargo.toml
│   │   │   │   │   ├── examples
│   │   │   │   │   │   ├── engine_hurst_vpin_backtest.rs
│   │   │   │   │   │   ├── node_data_tester.rs
│   │   │   │   │   │   ├── node_exec_tester.rs
│   │   │   │   │   │   └── node_hurst_vpin_live.rs
│   │   │   │   │   ├── LICENSE -> ../../../LICENSE
│   │   │   │   │   ├── README.md
│   │   │   │   │   ├── src
│   │   │   │   │   │   ├── common
│   │   │   │   │   │   │   ├── consts.rs
│   │   │   │   │   │   │   ├── credential.rs
│   │   │   │   │   │   │   ├── enums.rs
│   │   │   │   │   │   │   ├── mod.rs
│   │   │   │   │   │   │   ├── models.rs
│   │   │   │   │   │   │   ├── order_params.rs
│   │   │   │   │   │   │   ├── parse.rs
│   │   │   │   │   │   │   ├── serialization.rs
│   │   │   │   │   │   │   └── urls.rs
│   │   │   │   │   │   ├── config.rs
│   │   │   │   │   │   ├── data
│   │   │   │   │   │   │   ├── futures.rs
│   │   │   │   │   │   │   ├── mod.rs
│   │   │   │   │   │   │   └── spot.rs
│   │   │   │   │   │   ├── execution
│   │   │   │   │   │   │   ├── futures.rs
│   │   │   │   │   │   │   ├── mod.rs
│   │   │   │   │   │   │   └── spot.rs
│   │   │   │   │   │   ├── factories.rs
│   │   │   │   │   │   ├── http
│   │   │   │   │   │   │   ├── error.rs
│   │   │   │   │   │   │   ├── futures
│   │   │   │   │   │   │   │   ├── client.rs
│   │   │   │   │   │   │   │   ├── mod.rs
│   │   │   │   │   │   │   │   ├── models.rs
│   │   │   │   │   │   │   │   └── query.rs
│   │   │   │   │   │   │   ├── mod.rs
│   │   │   │   │   │   │   ├── models.rs
│   │   │   │   │   │   │   └── spot
│   │   │   │   │   │   │       ├── client.rs
│   │   │   │   │   │   │       ├── mod.rs
│   │   │   │   │   │   │       ├── models.rs
│   │   │   │   │   │   │       └── query.rs
│   │   │   │   │   │   ├── lib.rs
│   │   │   │   │   │   ├── python
│   │   │   │   │   │   │   ├── config.rs
│   │   │   │   │   │   │   ├── enums.rs
│   │   │   │   │   │   │   ├── factories.rs
│   │   │   │   │   │   │   ├── http_futures.rs
│   │   │   │   │   │   │   ├── http_spot.rs
│   │   │   │   │   │   │   ├── mod.rs
│   │   │   │   │   │   │   ├── websocket_futures.rs
│   │   │   │   │   │   │   └── websocket_spot.rs
│   │   │   │   │   │   └── websocket
│   │   │   │   │   │       ├── dispatch
│   │   │   │   │   │       │   ├── futures.rs
│   │   │   │   │   │       │   ├── mod.rs
│   │   │   │   │   │       │   ├── spot_orders.rs
│   │   │   │   │   │       │   └── spot.rs
│   │   │   │   │   │       ├── error.rs
│   │   │   │   │   │       ├── futures
│   │   │   │   │   │       │   ├── client.rs
│   │   │   │   │   │       │   ├── handler.rs
│   │   │   │   │   │       │   ├── messages.rs
│   │   │   │   │   │       │   ├── mod.rs
│   │   │   │   │   │       │   └── parse.rs
│   │   │   │   │   │       ├── mod.rs
│   │   │   │   │   │       └── spot_v2
│   │   │   │   │   │           ├── client.rs
│   │   │   │   │   │           ├── enums.rs
│   │   │   │   │   │           ├── handler.rs
│   │   │   │   │   │           ├── level_2.rs
│   │   │   │   │   │           ├── level_3
│   │   │   │   │   │           │   ├── book_id.rs
│   │   │   │   │   │           │   ├── checksum.rs
│   │   │   │   │   │           │   ├── messages.rs
│   │   │   │   │   │           │   ├── mod.rs
│   │   │   │   │   │           │   ├── parse.rs
│   │   │   │   │   │           │   ├── resync.rs
│   │   │   │   │   │           │   └── runtime.rs
│   │   │   │   │   │           ├── messages.rs
│   │   │   │   │   │           ├── mod.rs
│   │   │   │   │   │           └── parse.rs
│   │   │   │   │   ├── test_data
│   │   │   │   │   │   ├── decimal_exact.json
│   │   │   │   │   │   ├── futures_fill_types.json
│   │   │   │   │   │   ├── http_add_order_spot.json
│   │   │   │   │   │   ├── http_asset_pairs_tokenized.json
│   │   │   │   │   │   ├── http_asset_pairs.json
│   │   │   │   │   │   ├── http_cancel_order_futures.json
│   │   │   │   │   │   ├── http_cancel_order_spot.json
│   │   │   │   │   │   ├── http_closed_orders.json
│   │   │   │   │   │   ├── http_futures_candles_mark.json
│   │   │   │   │   │   ├── http_futures_candles_spot.json
│   │   │   │   │   │   ├── http_futures_candles_trade.json
│   │   │   │   │   │   ├── http_futures_fills.json
│   │   │   │   │   │   ├── http_futures_historical_funding_rates.json
│   │   │   │   │   │   ├── http_futures_instrument_no_fee_schedule.json
│   │   │   │   │   │   ├── http_futures_instruments.json
│   │   │   │   │   │   ├── http_futures_open_orders.json
│   │   │   │   │   │   ├── http_futures_open_positions.json
│   │   │   │   │   │   ├── http_futures_order_events_unknown.json
│   │   │   │   │   │   ├── http_futures_order_events.json
│   │   │   │   │   │   ├── http_futures_orderbook_precision.json
│   │   │   │   │   │   ├── http_futures_orderbook.json
│   │   │   │   │   │   ├── http_futures_public_executions.json
│   │   │   │   │   │   ├── http_futures_tickers.json
│   │   │   │   │   │   ├── http_ohlc.json
│   │   │   │   │   │   ├── http_open_orders.json
│   │   │   │   │   │   ├── http_order_book.json
│   │   │   │   │   │   ├── http_send_order_futures_unknown_trigger.json
│   │   │   │   │   │   ├── http_send_order_futures.json
│   │   │   │   │   │   ├── http_server_time.json
│   │   │   │   │   │   ├── http_spot_balance.json
│   │   │   │   │   │   ├── http_spot_open_positions.json
│   │   │   │   │   │   ├── http_spot_trade_balance.json
│   │   │   │   │   │   ├── http_system_status.json
│   │   │   │   │   │   ├── http_ticker.json
│   │   │   │   │   │   ├── http_trades_history.json
│   │   │   │   │   │   ├── http_trades.json
│   │   │   │   │   │   ├── ws_add_order_request.json
│   │   │   │   │   │   ├── ws_add_order_response_failure.json
│   │   │   │   │   │   ├── ws_add_order_response_success.json
│   │   │   │   │   │   ├── ws_amend_order_missing_optional_decimals.json
│   │   │   │   │   │   ├── ws_amend_order_request.json
│   │   │   │   │   │   ├── ws_batch_add_request.json
│   │   │   │   │   │   ├── ws_batch_add_response_partial.json
│   │   │   │   │   │   ├── ws_book_snapshot.json
│   │   │   │   │   │   ├── ws_book_update.json
│   │   │   │   │   │   ├── ws_cancel_order_request.json
│   │   │   │   │   │   ├── ws_execution_missing_optional_decimals.json
│   │   │   │   │   │   ├── ws_futures_book_delta.json
│   │   │   │   │   │   ├── ws_futures_book_precision.json
│   │   │   │   │   │   ├── ws_futures_book_snapshot_with_zero_qty.json
│   │   │   │   │   │   ├── ws_futures_book_snapshot.json
│   │   │   │   │   │   ├── ws_futures_fills_delta.json
│   │   │   │   │   │   ├── ws_futures_fills_snapshot.json
│   │   │   │   │   │   ├── ws_futures_open_orders_cancel_post_only.json
│   │   │   │   │   │   ├── ws_futures_open_orders_cancel.json
│   │   │   │   │   │   ├── ws_futures_open_orders_delta_full_fill.json
│   │   │   │   │   │   ├── ws_futures_open_orders_delta.json
│   │   │   │   │   │   ├── ws_futures_open_orders_snapshot.json
│   │   │   │   │   │   ├── ws_futures_ticker.json
│   │   │   │   │   │   ├── ws_futures_trade_snapshot.json
│   │   │   │   │   │   ├── ws_futures_trade.json
│   │   │   │   │   │   ├── ws_l3_snapshot.json
│   │   │   │   │   │   ├── ws_l3_update_add.json
│   │   │   │   │   │   ├── ws_l3_update_delete.json
│   │   │   │   │   │   ├── ws_l3_update_modify_price.json
│   │   │   │   │   │   ├── ws_l3_update_modify_qty.json
│   │   │   │   │   │   ├── ws_ohlc_update.json
│   │   │   │   │   │   ├── ws_pong.json
│   │   │   │   │   │   ├── ws_subscribe_response.json
│   │   │   │   │   │   ├── ws_ticker_precision.json
│   │   │   │   │   │   ├── ws_ticker_snapshot.json
│   │   │   │   │   │   └── ws_trade_update.json
│   │   │   │   │   └── tests
│   │   │   │   │       ├── authentication.rs
│   │   │   │   │       ├── common
│   │   │   │   │       │   └── mod.rs
│   │   │   │   │       ├── dispatch_futures.rs
│   │   │   │   │       ├── dispatch_spot.rs
│   │   │   │   │       ├── exec_client.rs
│   │   │   │   │       ├── http.rs
│   │   │   │   │       ├── python.rs
│   │   │   │   │       ├── spot
│   │   │   │   │       │   ├── mod.rs
│   │   │   │   │       │   └── websocket_orders.rs
│   │   │   │   │       ├── spot.rs
│   │   │   │   │       ├── websocket_futures.rs
│   │   │   │   │       └── websocket_spot.rs
│   │   │   │   ├── lighter
│   │   │   │   │   ├── benches
│   │   │   │   │   │   ├── common
│   │   │   │   │   │   │   └── mod.rs
│   │   │   │   │   │   ├── data.rs
│   │   │   │   │   │   ├── exec.rs
│   │   │   │   │   │   ├── micros.rs
│   │   │   │   │   │   ├── signing_curve.rs
│   │   │   │   │   │   ├── signing_field_iai.rs
│   │   │   │   │   │   ├── signing_field.rs
│   │   │   │   │   │   ├── signing_poseidon2.rs
│   │   │   │   │   │   └── signing_sign_verify.rs
│   │   │   │   │   ├── bin
│   │   │   │   │   │   ├── flatten.rs
│   │   │   │   │   │   ├── integrator_revoke.rs
│   │   │   │   │   │   └── trades_probe.rs
│   │   │   │   │   ├── Cargo.toml
│   │   │   │   │   ├── examples
│   │   │   │   │   │   ├── node_data_tester.rs
│   │   │   │   │   │   └── node_exec_tester.rs
│   │   │   │   │   ├── fuzz
│   │   │   │   │   │   ├── fuzz_targets
│   │   │   │   │   │   │   ├── fuzz_auth_message.rs
│   │   │   │   │   │   │   ├── fuzz_compute_tx_hash.rs
│   │   │   │   │   │   │   ├── fuzz_hash_no_pad.rs
│   │   │   │   │   │   │   ├── fuzz_point_decode.rs
│   │   │   │   │   │   │   ├── fuzz_scalar_mul_ct_diff.rs
│   │   │   │   │   │   │   ├── fuzz_signature_codec.rs
│   │   │   │   │   │   │   └── fuzz_verify.rs
│   │   │   │   │   │   ├── pornin
│   │   │   │   │   │   │   ├── Cargo.lock
│   │   │   │   │   │   │   ├── Cargo.toml
│   │   │   │   │   │   │   ├── fuzz_targets
│   │   │   │   │   │   │   │   ├── fuzz_pornin_diff_algebra.rs
│   │   │   │   │   │   │   │   ├── fuzz_pornin_diff_decode.rs
│   │   │   │   │   │   │   │   └── fuzz_pornin_diff_scalar_mul.rs
│   │   │   │   │   │   │   └── grind.sh
│   │   │   │   │   │   └── README.md
│   │   │   │   │   ├── LICENSE -> ../../../LICENSE
│   │   │   │   │   ├── licenses
│   │   │   │   │   │   ├── Apache-2.0-poseidon-crypto.txt
│   │   │   │   │   │   ├── MIT-pornin-ecgfp5.txt
│   │   │   │   │   │   └── THIRD_PARTY_LICENSES.md
│   │   │   │   │   ├── README.md
│   │   │   │   │   ├── src
│   │   │   │   │   │   ├── common
│   │   │   │   │   │   │   ├── consts.rs
│   │   │   │   │   │   │   ├── credential.rs
│   │   │   │   │   │   │   ├── enums.rs
│   │   │   │   │   │   │   ├── mod.rs
│   │   │   │   │   │   │   ├── parse.rs
│   │   │   │   │   │   │   ├── rate_limit.rs
│   │   │   │   │   │   │   ├── symbol.rs
│   │   │   │   │   │   │   └── urls.rs
│   │   │   │   │   │   ├── config.rs
│   │   │   │   │   │   ├── data
│   │   │   │   │   │   │   ├── limits.rs
│   │   │   │   │   │   │   ├── market_stats.rs
│   │   │   │   │   │   │   └── mod.rs
│   │   │   │   │   │   ├── execution.rs
│   │   │   │   │   │   ├── factories.rs
│   │   │   │   │   │   ├── http
│   │   │   │   │   │   │   ├── client.rs
│   │   │   │   │   │   │   ├── error.rs
│   │   │   │   │   │   │   ├── mod.rs
│   │   │   │   │   │   │   ├── models.rs
│   │   │   │   │   │   │   ├── parse.rs
│   │   │   │   │   │   │   └── query.rs
│   │   │   │   │   │   ├── lib.rs
│   │   │   │   │   │   ├── python
│   │   │   │   │   │   │   ├── config.rs
│   │   │   │   │   │   │   ├── factories.rs
│   │   │   │   │   │   │   └── mod.rs
│   │   │   │   │   │   ├── signing
│   │   │   │   │   │   │   ├── auth_token.rs
│   │   │   │   │   │   │   ├── curve
│   │   │   │   │   │   │   │   ├── ecgfp5.rs
│   │   │   │   │   │   │   │   ├── mod.rs
│   │   │   │   │   │   │   │   └── scalar.rs
│   │   │   │   │   │   │   ├── field
│   │   │   │   │   │   │   │   ├── goldilocks.rs
│   │   │   │   │   │   │   │   ├── mod.rs
│   │   │   │   │   │   │   │   └── quintic.rs
│   │   │   │   │   │   │   ├── fixtures.rs
│   │   │   │   │   │   │   ├── hash
│   │   │   │   │   │   │   │   ├── mod.rs
│   │   │   │   │   │   │   │   ├── params.rs
│   │   │   │   │   │   │   │   └── poseidon2.rs
│   │   │   │   │   │   │   ├── mod.rs
│   │   │   │   │   │   │   ├── nonce.rs
│   │   │   │   │   │   │   ├── schnorr
│   │   │   │   │   │   │   │   ├── key.rs
│   │   │   │   │   │   │   │   ├── mod.rs
│   │   │   │   │   │   │   │   └── sig.rs
│   │   │   │   │   │   │   └── tx
│   │   │   │   │   │   │       ├── encode.rs
│   │   │   │   │   │   │       ├── mod.rs
│   │   │   │   │   │   │       └── types.rs
│   │   │   │   │   │   └── websocket
│   │   │   │   │   │       ├── account_state.rs
│   │   │   │   │   │       ├── client.rs
│   │   │   │   │   │       ├── dispatch.rs
│   │   │   │   │   │       ├── error.rs
│   │   │   │   │   │       ├── handler.rs
│   │   │   │   │   │       ├── messages.rs
│   │   │   │   │   │       ├── mod.rs
│   │   │   │   │   │       └── parse.rs
│   │   │   │   │   ├── test_data
│   │   │   │   │   │   ├── http_account.json
│   │   │   │   │   │   ├── http_candles_null.json
│   │   │   │   │   │   ├── http_candles.json
│   │   │   │   │   │   ├── http_fundings.json
│   │   │   │   │   │   ├── http_next_nonce.json
│   │   │   │   │   │   ├── http_order_book_depth_null.json
│   │   │   │   │   │   ├── http_order_book_depth.json
│   │   │   │   │   │   ├── http_order_book_details.json
│   │   │   │   │   │   ├── http_order_book_orders.json
│   │   │   │   │   │   ├── http_order_books.json
│   │   │   │   │   │   ├── http_orders.json
│   │   │   │   │   │   ├── http_recent_trades_missing.json
│   │   │   │   │   │   ├── http_recent_trades_null.json
│   │   │   │   │   │   ├── http_recent_trades_unordered.json
│   │   │   │   │   │   ├── http_recent_trades.json
│   │   │   │   │   │   ├── README.md
│   │   │   │   │   │   ├── signing_auth_token_oracle.json
│   │   │   │   │   │   ├── signing_curve_ecgfp5_vectors.json
│   │   │   │   │   │   ├── signing_field_goldilocks_vectors.json
│   │   │   │   │   │   ├── signing_field_quintic_vectors.json
│   │   │   │   │   │   ├── signing_hash_poseidon2_vectors.json
│   │   │   │   │   │   ├── signing_schnorr_vectors.json
│   │   │   │   │   │   ├── signing_tx_oracle.json
│   │   │   │   │   │   ├── ws_account_all_assets_update.json
│   │   │   │   │   │   ├── ws_account_all_assets_with_position.json
│   │   │   │   │   │   ├── ws_account_all_positions_update.json
│   │   │   │   │   │   ├── ws_account_all_trades_update.json
│   │   │   │   │   │   ├── ws_account_orders_update.json
│   │   │   │   │   │   ├── ws_candle_subscribed.json
│   │   │   │   │   │   ├── ws_candle_update.json
│   │   │   │   │   │   ├── ws_height_update.json
│   │   │   │   │   │   ├── ws_market_stats_subscribed_single.json
│   │   │   │   │   │   ├── ws_market_stats_update_all.json
│   │   │   │   │   │   ├── ws_market_stats_update_single.json
│   │   │   │   │   │   ├── ws_order_book_subscribed_empty.json
│   │   │   │   │   │   ├── ws_order_book_subscribed.json
│   │   │   │   │   │   ├── ws_order_book_update.json
│   │   │   │   │   │   ├── ws_spot_market_stats_subscribed_single.json
│   │   │   │   │   │   ├── ws_spot_market_stats_update_all.json
│   │   │   │   │   │   ├── ws_spot_market_stats_update_single.json
│   │   │   │   │   │   ├── ws_ticker_subscribed_empty.json
│   │   │   │   │   │   ├── ws_ticker_subscribed.json
│   │   │   │   │   │   ├── ws_ticker_update.json
│   │   │   │   │   │   ├── ws_trade_subscribed.json
│   │   │   │   │   │   ├── ws_trade_update.json
│   │   │   │   │   │   ├── ws_user_stats_update.json
│   │   │   │   │   │   └── ws_user_stats_with_position.json
│   │   │   │   │   └── tests
│   │   │   │   │       ├── data_client.rs
│   │   │   │   │       ├── exec_client.rs
│   │   │   │   │       ├── http.rs
│   │   │   │   │       ├── oracle-py
│   │   │   │   │       │   ├── generate_oracle.py
│   │   │   │   │       │   └── README.md
│   │   │   │   │       ├── python.rs
│   │   │   │   │       └── websocket.rs
│   │   │   │   ├── okx
│   │   │   │   │   ├── benches
│   │   │   │   │   │   ├── BENCHMARKS.md
│   │   │   │   │   │   ├── common
│   │   │   │   │   │   │   └── mod.rs
│   │   │   │   │   │   ├── data.rs
│   │   │   │   │   │   ├── exec.rs
│   │   │   │   │   │   ├── micros.rs
│   │   │   │   │   │   └── signing.rs
│   │   │   │   │   ├── bin
│   │   │   │   │   │   ├── flatten.rs
│   │   │   │   │   │   ├── http_private.rs
│   │   │   │   │   │   ├── http_public.rs
│   │   │   │   │   │   ├── ws_data.rs
│   │   │   │   │   │   └── ws_exec.rs
│   │   │   │   │   ├── Cargo.toml
│   │   │   │   │   ├── examples
│   │   │   │   │   │   ├── node_data_tester.rs
│   │   │   │   │   │   ├── node_delta_neutral.rs
│   │   │   │   │   │   ├── node_exec_tester.rs
│   │   │   │   │   │   └── node_greeks.rs
│   │   │   │   │   ├── LICENSE -> ../../../LICENSE
│   │   │   │   │   ├── README.md
│   │   │   │   │   ├── src
│   │   │   │   │   │   ├── book_sync.rs
│   │   │   │   │   │   ├── common
│   │   │   │   │   │   │   ├── consts.rs
│   │   │   │   │   │   │   ├── credential.rs
│   │   │   │   │   │   │   ├── enums.rs
│   │   │   │   │   │   │   ├── mod.rs
│   │   │   │   │   │   │   ├── models.rs
│   │   │   │   │   │   │   ├── parse.rs
│   │   │   │   │   │   │   ├── testing.rs
│   │   │   │   │   │   │   └── urls.rs
│   │   │   │   │   │   ├── config.rs
│   │   │   │   │   │   ├── data.rs
│   │   │   │   │   │   ├── execution.rs
│   │   │   │   │   │   ├── factories.rs
│   │   │   │   │   │   ├── http
│   │   │   │   │   │   │   ├── client.rs
│   │   │   │   │   │   │   ├── error.rs
│   │   │   │   │   │   │   ├── mod.rs
│   │   │   │   │   │   │   ├── models.rs
│   │   │   │   │   │   │   ├── parse.rs
│   │   │   │   │   │   │   └── query.rs
│   │   │   │   │   │   ├── lib.rs
│   │   │   │   │   │   ├── python
│   │   │   │   │   │   │   ├── config.rs
│   │   │   │   │   │   │   ├── enums.rs
│   │   │   │   │   │   │   ├── factories.rs
│   │   │   │   │   │   │   ├── http.rs
│   │   │   │   │   │   │   ├── mod.rs
│   │   │   │   │   │   │   ├── models.rs
│   │   │   │   │   │   │   ├── urls.rs
│   │   │   │   │   │   │   └── websocket.rs
│   │   │   │   │   │   └── websocket
│   │   │   │   │   │       ├── client.rs
│   │   │   │   │   │       ├── dispatch.rs
│   │   │   │   │   │       ├── enums.rs
│   │   │   │   │   │       ├── error.rs
│   │   │   │   │   │       ├── handler.rs
│   │   │   │   │   │       ├── messages.rs
│   │   │   │   │   │       ├── mod.rs
│   │   │   │   │   │       ├── parse.rs
│   │   │   │   │   │       └── subscription.rs
│   │   │   │   │   ├── test_data
│   │   │   │   │   │   ├── common_optional_string_to_u64.json
│   │   │   │   │   │   ├── http_balance_detail_new_fields.json
│   │   │   │   │   │   ├── http_balance_detail_old_fields.json
│   │   │   │   │   │   ├── http_cancel_algo_order_response.json
│   │   │   │   │   │   ├── http_get_account_balance.json
│   │   │   │   │   │   ├── http_get_account_positions-history.json
│   │   │   │   │   │   ├── http_get_candlesticks_full.json
│   │   │   │   │   │   ├── http_get_candlesticks.json
│   │   │   │   │   │   ├── http_get_funding_rate_history.json
│   │   │   │   │   │   ├── http_get_index_price.json
│   │   │   │   │   │   ├── http_get_instruments_futures.json
│   │   │   │   │   │   ├── http_get_instruments_margin.json
│   │   │   │   │   │   ├── http_get_instruments_option.json
│   │   │   │   │   │   ├── http_get_instruments_price_limit.json
│   │   │   │   │   │   ├── http_get_instruments_spot.json
│   │   │   │   │   │   ├── http_get_instruments_swap.json
│   │   │   │   │   │   ├── http_get_mark_price.json
│   │   │   │   │   │   ├── http_get_option_summary.json
│   │   │   │   │   │   ├── http_get_order_book.json
│   │   │   │   │   │   ├── http_get_orders_algo_history.json
│   │   │   │   │   │   ├── http_get_orders_algo_pending_attached_oco.json
│   │   │   │   │   │   ├── http_get_orders_algo_pending_close_fraction.json
│   │   │   │   │   │   ├── http_get_orders_algo_pending.json
│   │   │   │   │   │   ├── http_get_orders_history.json
│   │   │   │   │   │   ├── http_get_orders_pending_with_attached_tp_sl.json
│   │   │   │   │   │   ├── http_get_orders_pending.json
│   │   │   │   │   │   ├── http_get_position_tiers.json
│   │   │   │   │   │   ├── http_get_positions_long_short.json
│   │   │   │   │   │   ├── http_get_positions.json
│   │   │   │   │   │   ├── http_get_price_limit.json
│   │   │   │   │   │   ├── http_get_rpi_order_book.json
│   │   │   │   │   │   ├── http_get_spread_orders.json
│   │   │   │   │   │   ├── http_get_spread_trades.json
│   │   │   │   │   │   ├── http_get_spreads.json
│   │   │   │   │   │   ├── http_get_trade_fee_response.json
│   │   │   │   │   │   ├── http_get_trades.json
│   │   │   │   │   │   ├── http_place_algo_order_rejected.json
│   │   │   │   │   │   ├── http_place_algo_order_response.json
│   │   │   │   │   │   ├── http_place_algo_order_timeout.json
│   │   │   │   │   │   ├── http_place_order_response.json
│   │   │   │   │   │   ├── http_set_position_mode_response.json
│   │   │   │   │   │   ├── http_transaction_detail_empty_fee.json
│   │   │   │   │   │   ├── http_transaction_detail.json
│   │   │   │   │   │   ├── ws_account_empty.json
│   │   │   │   │   │   ├── ws_account.json
│   │   │   │   │   │   ├── ws_bbo_tbt.json
│   │   │   │   │   │   ├── ws_books_rpi_snapshot.json
│   │   │   │   │   │   ├── ws_books_rpi_update.json
│   │   │   │   │   │   ├── ws_books_snapshot.json
│   │   │   │   │   │   ├── ws_books_update.json
│   │   │   │   │   │   ├── ws_candle.json
│   │   │   │   │   │   ├── ws_funding_rate.json
│   │   │   │   │   │   ├── ws_instruments.json
│   │   │   │   │   │   ├── ws_opt_summary.json
│   │   │   │   │   │   ├── ws_orders_adl.json
│   │   │   │   │   │   ├── ws_orders_algo.json
│   │   │   │   │   │   ├── ws_orders_fok.json
│   │   │   │   │   │   ├── ws_orders_ioc.json
│   │   │   │   │   │   ├── ws_orders_liquidation.json
│   │   │   │   │   │   ├── ws_orders_mmp_and_post_only_canceled_first.json
│   │   │   │   │   │   ├── ws_orders_optimal_limit_ioc.json
│   │   │   │   │   │   ├── ws_orders_option.json
│   │   │   │   │   │   ├── ws_orders_post_only_canceled_first.json
│   │   │   │   │   │   ├── ws_orders_rpi_canceled_first.json
│   │   │   │   │   │   ├── ws_orders_trigger.json
│   │   │   │   │   │   ├── ws_orders.json
│   │   │   │   │   │   ├── ws_sprd_orders.json
│   │   │   │   │   │   ├── ws_tickers.json
│   │   │   │   │   │   └── ws_trades.json
│   │   │   │   │   └── tests
│   │   │   │   │       ├── data_client.rs
│   │   │   │   │       ├── exec_client.rs
│   │   │   │   │       ├── http.rs
│   │   │   │   │       ├── python.rs
│   │   │   │   │       └── websocket.rs
│   │   │   │   ├── polymarket
│   │   │   │   │   ├── benches
│   │   │   │   │   │   ├── BENCHMARKS.md
│   │   │   │   │   │   ├── common
│   │   │   │   │   │   │   └── mod.rs
│   │   │   │   │   │   ├── data.rs
│   │   │   │   │   │   ├── effective_deltas.rs
│   │   │   │   │   │   ├── exec.rs
│   │   │   │   │   │   ├── micros.rs
│   │   │   │   │   │   └── signing.rs
│   │   │   │   │   ├── bin
│   │   │   │   │   │   ├── composite_filter.rs
│   │   │   │   │   │   ├── create_api_key.rs
│   │   │   │   │   │   ├── event_discovery.rs
│   │   │   │   │   │   ├── search_markets.rs
│   │   │   │   │   │   ├── set_allowances.rs
│   │   │   │   │   │   ├── trending_markets.rs
│   │   │   │   │   │   └── updown_markets.rs
│   │   │   │   │   ├── Cargo.toml
│   │   │   │   │   ├── examples
│   │   │   │   │   │   ├── election_trade_subscriber.rs
│   │   │   │   │   │   ├── new_market_monitor.rs
│   │   │   │   │   │   ├── node_data_tester.rs
│   │   │   │   │   │   └── node_exec_tester.rs
│   │   │   │   │   ├── LICENSE -> ../../../LICENSE
│   │   │   │   │   ├── README.md
│   │   │   │   │   ├── src
│   │   │   │   │   │   ├── common
│   │   │   │   │   │   │   ├── consts.rs
│   │   │   │   │   │   │   ├── credential.rs
│   │   │   │   │   │   │   ├── enums.rs
│   │   │   │   │   │   │   ├── mod.rs
│   │   │   │   │   │   │   ├── models.rs
│   │   │   │   │   │   │   ├── parse.rs
│   │   │   │   │   │   │   ├── retry.rs
│   │   │   │   │   │   │   ├── socket.rs
│   │   │   │   │   │   │   └── urls.rs
│   │   │   │   │   │   ├── config.rs
│   │   │   │   │   │   ├── data
│   │   │   │   │   │   │   ├── auto_load.rs
│   │   │   │   │   │   │   ├── dispatch.rs
│   │   │   │   │   │   │   ├── effective_deltas.rs
│   │   │   │   │   │   │   ├── instruments.rs
│   │   │   │   │   │   │   ├── lifecycle.rs
│   │   │   │   │   │   │   ├── mod.rs
│   │   │   │   │   │   │   ├── requests.rs
│   │   │   │   │   │   │   ├── runtime.rs
│   │   │   │   │   │   │   └── subscriptions.rs
│   │   │   │   │   │   ├── data_types.rs
│   │   │   │   │   │   ├── execution
│   │   │   │   │   │   │   ├── cancellations.rs
│   │   │   │   │   │   │   ├── identity.rs
│   │   │   │   │   │   │   ├── lifecycle.rs
│   │   │   │   │   │   │   ├── mod.rs
│   │   │   │   │   │   │   ├── order_builder.rs
│   │   │   │   │   │   │   ├── order_fill_tracker.rs
│   │   │   │   │   │   │   ├── orders.rs
│   │   │   │   │   │   │   ├── parse.rs
│   │   │   │   │   │   │   ├── pending.rs
│   │   │   │   │   │   │   ├── reconciliation.rs
│   │   │   │   │   │   │   ├── reports.rs
│   │   │   │   │   │   │   ├── responses.rs
│   │   │   │   │   │   │   ├── submitter.rs
│   │   │   │   │   │   │   └── types.rs
│   │   │   │   │   │   ├── factories.rs
│   │   │   │   │   │   ├── filters.rs
│   │   │   │   │   │   ├── http
│   │   │   │   │   │   │   ├── auth.rs
│   │   │   │   │   │   │   ├── clob.rs
│   │   │   │   │   │   │   ├── data_api.rs
│   │   │   │   │   │   │   ├── error.rs
│   │   │   │   │   │   │   ├── gamma.rs
│   │   │   │   │   │   │   ├── mod.rs
│   │   │   │   │   │   │   ├── models.rs
│   │   │   │   │   │   │   ├── parse.rs
│   │   │   │   │   │   │   ├── query.rs
│   │   │   │   │   │   │   └── rate_limits.rs
│   │   │   │   │   │   ├── lib.rs
│   │   │   │   │   │   ├── providers.rs
│   │   │   │   │   │   ├── python
│   │   │   │   │   │   │   ├── config.rs
│   │   │   │   │   │   │   ├── factories.rs
│   │   │   │   │   │   │   ├── loader.rs
│   │   │   │   │   │   │   ├── mod.rs
│   │   │   │   │   │   │   └── sort.rs
│   │   │   │   │   │   ├── resolve
│   │   │   │   │   │   │   ├── apply.rs
│   │   │   │   │   │   │   ├── mod.rs
│   │   │   │   │   │   │   ├── parsing.rs
│   │   │   │   │   │   │   ├── summary.rs
│   │   │   │   │   │   │   └── watchlist.rs
│   │   │   │   │   │   ├── rtds.rs
│   │   │   │   │   │   ├── signing
│   │   │   │   │   │   │   ├── eip712.rs
│   │   │   │   │   │   │   └── mod.rs
│   │   │   │   │   │   └── websocket
│   │   │   │   │   │       ├── client.rs
│   │   │   │   │   │       ├── dispatch.rs
│   │   │   │   │   │       ├── error.rs
│   │   │   │   │   │       ├── handler.rs
│   │   │   │   │   │       ├── messages.rs
│   │   │   │   │   │       ├── mod.rs
│   │   │   │   │   │       ├── parse.rs
│   │   │   │   │   │       └── pool.rs
│   │   │   │   │   ├── test_data
│   │   │   │   │   │   ├── clob_book_response.json
│   │   │   │   │   │   ├── clob_fee_rate_response_nonzero.json
│   │   │   │   │   │   ├── clob_fee_rate_response_zero.json
│   │   │   │   │   │   ├── clob_market_closed_binary_accepting_false.json
│   │   │   │   │   │   ├── clob_market_closed_binary_accepting_true.json
│   │   │   │   │   │   ├── clob_market_response.json
│   │   │   │   │   │   ├── data_api_positions_response.json
│   │   │   │   │   │   ├── data_api_trades_captured_response.json
│   │   │   │   │   │   ├── data_api_trades_response.json
│   │   │   │   │   │   ├── gamma_event.json
│   │   │   │   │   │   ├── gamma_market_closed_binary_accepting_false.json
│   │   │   │   │   │   ├── gamma_market_closed_binary_accepting_true.json
│   │   │   │   │   │   ├── gamma_market_closed_nonbinary_legacy.json
│   │   │   │   │   │   ├── gamma_market_closed_zero_zero_legacy.json
│   │   │   │   │   │   ├── gamma_market_past_end_date_open.json
│   │   │   │   │   │   ├── gamma_market_sports_market_map_handicap.json
│   │   │   │   │   │   ├── gamma_market_sports_market_money_line.json
│   │   │   │   │   │   ├── gamma_market.json
│   │   │   │   │   │   ├── gamma_tags.json
│   │   │   │   │   │   ├── http_balance_allowance_collateral.json
│   │   │   │   │   │   ├── http_balance_allowance_conditional.json
│   │   │   │   │   │   ├── http_balance_allowance_no_allowance.json
│   │   │   │   │   │   ├── http_batch_cancel_response.json
│   │   │   │   │   │   ├── http_batch_order_response.json
│   │   │   │   │   │   ├── http_cancel_response_failed.json
│   │   │   │   │   │   ├── http_cancel_response_ok.json
│   │   │   │   │   │   ├── http_open_order_sell_fok.json
│   │   │   │   │   │   ├── http_open_order.json
│   │   │   │   │   │   ├── http_open_orders_page.json
│   │   │   │   │   │   ├── http_order_response_async_exec.json
│   │   │   │   │   │   ├── http_order_response_error_500.json
│   │   │   │   │   │   ├── http_order_response_failed.json
│   │   │   │   │   │   ├── http_order_response_ok.json
│   │   │   │   │   │   ├── http_order_response_trade_ids_only.json
│   │   │   │   │   │   ├── http_signed_order.json
│   │   │   │   │   │   ├── http_trade_report.json
│   │   │   │   │   │   ├── http_trades_page.json
│   │   │   │   │   │   ├── rtds_crypto_prices_subscribe.json
│   │   │   │   │   │   ├── rtds_crypto_prices_update.json
│   │   │   │   │   │   ├── rtds_equity_prices_subscribe.json
│   │   │   │   │   │   ├── rtds_equity_prices_update.json
│   │   │   │   │   │   ├── search_response.json
│   │   │   │   │   │   ├── ws_book_snapshot_missing_hash.json
│   │   │   │   │   │   ├── ws_book_snapshot.json
│   │   │   │   │   │   ├── ws_last_trade_missing_transaction_hash.json
│   │   │   │   │   │   ├── ws_last_trade.json
│   │   │   │   │   │   ├── ws_market_best_bid_ask_msg.json
│   │   │   │   │   │   ├── ws_market_book_msg.json
│   │   │   │   │   │   ├── ws_market_last_trade_msg.json
│   │   │   │   │   │   ├── ws_market_mixed_known_unknown.json
│   │   │   │   │   │   ├── ws_market_new_market_msg.json
│   │   │   │   │   │   ├── ws_market_price_change_msg.json
│   │   │   │   │   │   ├── ws_market_resolved_msg.json
│   │   │   │   │   │   ├── ws_market_tick_size_msg.json
│   │   │   │   │   │   ├── ws_quotes.json
│   │   │   │   │   │   ├── ws_tick_size_change.json
│   │   │   │   │   │   ├── ws_user_batch_msg.json
│   │   │   │   │   │   ├── ws_user_order_cancellation.json
│   │   │   │   │   │   ├── ws_user_order_fok_buy_pusd_size.json
│   │   │   │   │   │   ├── ws_user_order_fok_killed.json
│   │   │   │   │   │   ├── ws_user_order_matched.json
│   │   │   │   │   │   ├── ws_user_order_msg.json
│   │   │   │   │   │   ├── ws_user_order_placement.json
│   │   │   │   │   │   ├── ws_user_order_update.json
│   │   │   │   │   │   ├── ws_user_order_venue_cancel.json
│   │   │   │   │   │   ├── ws_user_trade_msg.json
│   │   │   │   │   │   └── ws_user_trade.json
│   │   │   │   │   └── tests
│   │   │   │   │       ├── data_client.rs
│   │   │   │   │       ├── exec_client.rs
│   │   │   │   │       ├── http.rs
│   │   │   │   │       ├── python.rs
│   │   │   │   │       └── websocket.rs
│   │   │   │   ├── sandbox
│   │   │   │   │   ├── Cargo.toml
│   │   │   │   │   ├── examples
│   │   │   │   │   │   └── databento_cme.rs
│   │   │   │   │   ├── LICENSE -> ../../../LICENSE
│   │   │   │   │   ├── README.md
│   │   │   │   │   ├── src
│   │   │   │   │   │   ├── config.rs
│   │   │   │   │   │   ├── execution.rs
│   │   │   │   │   │   ├── factory.rs
│   │   │   │   │   │   ├── lib.rs
│   │   │   │   │   │   └── python
│   │   │   │   │   │       ├── config.rs
│   │   │   │   │   │       ├── factories.rs
│   │   │   │   │   │       └── mod.rs
│   │   │   │   │   └── tests
│   │   │   │   │       ├── execution.rs
│   │   │   │   │       └── python.rs
│   │   │   │   └── tardis
│   │   │   │       ├── benches
│   │   │   │       │   └── messages.rs
│   │   │   │       ├── bin
│   │   │   │       │   ├── example_config.json
│   │   │   │       │   ├── example_csv.rs
│   │   │   │       │   ├── example_http.rs
│   │   │   │       │   ├── example_replay.rs
│   │   │   │       │   └── stream_deltas_bench.rs
│   │   │   │       ├── Cargo.toml
│   │   │   │       ├── examples
│   │   │   │       │   └── node_data_tester.rs
│   │   │   │       ├── LICENSE -> ../../../LICENSE
│   │   │   │       ├── README.md
│   │   │   │       ├── src
│   │   │   │       │   ├── common
│   │   │   │       │   │   ├── consts.rs
│   │   │   │       │   │   ├── credential.rs
│   │   │   │       │   │   ├── enums.rs
│   │   │   │       │   │   ├── error.rs
│   │   │   │       │   │   ├── mod.rs
│   │   │   │       │   │   ├── parse.rs
│   │   │   │       │   │   ├── testing.rs
│   │   │   │       │   │   └── urls.rs
│   │   │   │       │   ├── config.rs
│   │   │   │       │   ├── csv
│   │   │   │       │   │   ├── convert.rs
│   │   │   │       │   │   ├── load.rs
│   │   │   │       │   │   ├── mod.rs
│   │   │   │       │   │   ├── record.rs
│   │   │   │       │   │   └── stream.rs
│   │   │   │       │   ├── data.rs
│   │   │   │       │   ├── factories.rs
│   │   │   │       │   ├── http
│   │   │   │       │   │   ├── client.rs
│   │   │   │       │   │   ├── error.rs
│   │   │   │       │   │   ├── instruments.rs
│   │   │   │       │   │   ├── mod.rs
│   │   │   │       │   │   ├── models.rs
│   │   │   │       │   │   ├── parse.rs
│   │   │   │       │   │   └── query.rs
│   │   │   │       │   ├── lib.rs
│   │   │   │       │   ├── machine
│   │   │   │       │   │   ├── cache.rs
│   │   │   │       │   │   ├── client.rs
│   │   │   │       │   │   ├── message.rs
│   │   │   │       │   │   ├── mod.rs
│   │   │   │       │   │   ├── parse.rs
│   │   │   │       │   │   └── types.rs
│   │   │   │       │   ├── python
│   │   │   │       │   │   ├── config.rs
│   │   │   │       │   │   ├── csv.rs
│   │   │   │       │   │   ├── enums.rs
│   │   │   │       │   │   ├── factories.rs
│   │   │   │       │   │   ├── http.rs
│   │   │   │       │   │   ├── machine.rs
│   │   │   │       │   │   └── mod.rs
│   │   │   │       │   └── replay.rs
│   │   │   │       ├── test_data
│   │   │   │       │   ├── bar.json
│   │   │   │       │   ├── book_change.json
│   │   │   │       │   ├── book_snapshot.json
│   │   │   │       │   ├── csv
│   │   │   │       │   │   ├── deltas_1.csv
│   │   │   │       │   │   ├── deltas_with_snapshot.csv
│   │   │   │       │   │   ├── derivative_ticker_1.csv
│   │   │   │       │   │   └── trades_1.csv
│   │   │   │       │   ├── derivative_ticker.json
│   │   │   │       │   ├── disconnect.json
│   │   │   │       │   ├── instrument_combo.json
│   │   │   │       │   ├── instrument_future.json
│   │   │   │       │   ├── instrument_option.json
│   │   │   │       │   ├── instrument_perpetual.json
│   │   │   │       │   ├── instrument_spot.json
│   │   │   │       │   ├── mexc_book_snapshot_5000.json
│   │   │   │       │   ├── mexc_futures_derivative_ticker.json
│   │   │   │       │   ├── option_book_snapshot.json
│   │   │   │       │   ├── option_summary.json
│   │   │   │       │   ├── options_chain.csv
│   │   │   │       │   └── trade.json
│   │   │   │       └── tests
│   │   │   │           ├── data_client.rs
│   │   │   │           ├── http.rs
│   │   │   │           ├── python.rs
│   │   │   │           └── websocket.rs
│   │   │   ├── analysis
│   │   │   │   ├── Cargo.toml
│   │   │   │   ├── LICENSE -> ../../LICENSE
│   │   │   │   ├── README.md
│   │   │   │   └── src
│   │   │   │       ├── analyzer.rs
│   │   │   │       ├── lib.rs
│   │   │   │       ├── python
│   │   │   │       │   ├── analyzer.rs
│   │   │   │       │   ├── mod.rs
│   │   │   │       │   ├── snapshot.rs
│   │   │   │       │   └── statistics
│   │   │   │       │       ├── alpha.rs
│   │   │   │       │       ├── beta_ratio.rs
│   │   │   │       │       ├── cagr.rs
│   │   │   │       │       ├── calmar_ratio.rs
│   │   │   │       │       ├── down_capture_ratio.rs
│   │   │   │       │       ├── expectancy.rs
│   │   │   │       │       ├── expected_shortfall.rs
│   │   │   │       │       ├── information_ratio.rs
│   │   │   │       │       ├── long_ratio.rs
│   │   │   │       │       ├── loser_avg.rs
│   │   │   │       │       ├── loser_max.rs
│   │   │   │       │       ├── loser_min.rs
│   │   │   │       │       ├── max_drawdown.rs
│   │   │   │       │       ├── mod.rs
│   │   │   │       │       ├── omega_ratio.rs
│   │   │   │       │       ├── profit_factor.rs
│   │   │   │       │       ├── returns_avg_loss.rs
│   │   │   │       │       ├── returns_avg_win.rs
│   │   │   │       │       ├── returns_avg.rs
│   │   │   │       │       ├── returns_kurtosis.rs
│   │   │   │       │       ├── returns_skewness.rs
│   │   │   │       │       ├── returns_volatility.rs
│   │   │   │       │       ├── risk_return_ratio.rs
│   │   │   │       │       ├── sharpe_ratio.rs
│   │   │   │       │       ├── sortino_ratio.rs
│   │   │   │       │       ├── tail_ratio.rs
│   │   │   │       │       ├── tracking_error.rs
│   │   │   │       │       ├── treynor_ratio.rs
│   │   │   │       │       ├── ulcer_index.rs
│   │   │   │       │       ├── up_capture_ratio.rs
│   │   │   │       │       ├── value_at_risk.rs
│   │   │   │       │       ├── win_rate.rs
│   │   │   │       │       ├── winner_avg.rs
│   │   │   │       │       ├── winner_max.rs
│   │   │   │       │       └── winner_min.rs
│   │   │   │       ├── snapshot.rs
│   │   │   │       ├── statistic.rs
│   │   │   │       └── statistics
│   │   │   │           ├── alpha.rs
│   │   │   │           ├── beta_ratio.rs
│   │   │   │           ├── cagr.rs
│   │   │   │           ├── calmar_ratio.rs
│   │   │   │           ├── down_capture_ratio.rs
│   │   │   │           ├── expectancy.rs
│   │   │   │           ├── expected_shortfall.rs
│   │   │   │           ├── information_ratio.rs
│   │   │   │           ├── long_ratio.rs
│   │   │   │           ├── loser_avg.rs
│   │   │   │           ├── loser_max.rs
│   │   │   │           ├── loser_min.rs
│   │   │   │           ├── max_drawdown.rs
│   │   │   │           ├── mod.rs
│   │   │   │           ├── omega_ratio.rs
│   │   │   │           ├── profit_factor.rs
│   │   │   │           ├── returns_avg_loss.rs
│   │   │   │           ├── returns_avg_win.rs
│   │   │   │           ├── returns_avg.rs
│   │   │   │           ├── returns_kurtosis.rs
│   │   │   │           ├── returns_skewness.rs
│   │   │   │           ├── returns_volatility.rs
│   │   │   │           ├── risk_return_ratio.rs
│   │   │   │           ├── sharpe_ratio.rs
│   │   │   │           ├── sortino_ratio.rs
│   │   │   │           ├── tail_ratio.rs
│   │   │   │           ├── tracking_error.rs
│   │   │   │           ├── treynor_ratio.rs
│   │   │   │           ├── ulcer_index.rs
│   │   │   │           ├── up_capture_ratio.rs
│   │   │   │           ├── value_at_risk.rs
│   │   │   │           ├── win_rate.rs
│   │   │   │           ├── winner_avg.rs
│   │   │   │           ├── winner_max.rs
│   │   │   │           └── winner_min.rs
│   │   │   ├── backtest
│   │   │   │   ├── benches
│   │   │   │   │   ├── BENCHMARKS.md
│   │   │   │   │   ├── engine
│   │   │   │   │   │   └── canonical.rs
│   │   │   │   │   └── engine.rs
│   │   │   │   ├── Cargo.toml
│   │   │   │   ├── examples
│   │   │   │   │   ├── engine_ema_cross.rs
│   │   │   │   │   ├── node_ema_cross.rs
│   │   │   │   │   └── tardis_option_chain.rs
│   │   │   │   ├── LICENSE -> ../../LICENSE
│   │   │   │   ├── README.md
│   │   │   │   ├── src
│   │   │   │   │   ├── accumulator.rs
│   │   │   │   │   ├── config.rs
│   │   │   │   │   ├── data_client.rs
│   │   │   │   │   ├── data_iterator.rs
│   │   │   │   │   ├── defi
│   │   │   │   │   │   ├── engine.rs
│   │   │   │   │   │   ├── mod.rs
│   │   │   │   │   │   └── replay.rs
│   │   │   │   │   ├── engine.rs
│   │   │   │   │   ├── exchange.rs
│   │   │   │   │   ├── execution_client.rs
│   │   │   │   │   ├── lib.rs
│   │   │   │   │   ├── modules
│   │   │   │   │   │   ├── fx_rollover.rs
│   │   │   │   │   │   └── mod.rs
│   │   │   │   │   ├── node.rs
│   │   │   │   │   ├── python
│   │   │   │   │   │   ├── config.rs
│   │   │   │   │   │   ├── engine.rs
│   │   │   │   │   │   ├── mod.rs
│   │   │   │   │   │   ├── modules.rs
│   │   │   │   │   │   ├── node.rs
│   │   │   │   │   │   └── result.rs
│   │   │   │   │   └── result.rs
│   │   │   │   └── tests
│   │   │   │       ├── backtest_engine.rs
│   │   │   │       ├── backtest_node_itch.rs
│   │   │   │       ├── backtest_node_workload.rs
│   │   │   │       ├── backtest_node.rs
│   │   │   │       ├── book_imbalance.rs
│   │   │   │       ├── canonical_backtest_workloads.rs
│   │   │   │       ├── ema_cross.rs
│   │   │   │       ├── exchange.rs
│   │   │   │       ├── grid_mm_itch.rs
│   │   │   │       ├── grid_mm.rs
│   │   │   │       ├── netting_fill_void.rs
│   │   │   │       ├── option_chain_backtest.rs
│   │   │   │       └── option_chain_data_client.rs
│   │   │   ├── Cargo.toml
│   │   │   ├── cli
│   │   │   │   ├── Cargo.toml
│   │   │   │   ├── LICENSE -> ../../LICENSE
│   │   │   │   ├── README.md
│   │   │   │   ├── src
│   │   │   │   │   ├── bin
│   │   │   │   │   │   └── cli.rs
│   │   │   │   │   ├── blockchain
│   │   │   │   │   │   ├── analyze.rs
│   │   │   │   │   │   ├── help.rs
│   │   │   │   │   │   ├── mod.rs
│   │   │   │   │   │   └── sync.rs
│   │   │   │   │   ├── database
│   │   │   │   │   │   ├── mod.rs
│   │   │   │   │   │   └── postgres.rs
│   │   │   │   │   ├── lib.rs
│   │   │   │   │   └── opt.rs
│   │   │   │   └── tests
│   │   │   │       └── exit_code.rs
│   │   │   ├── common
│   │   │   │   ├── benches
│   │   │   │   │   ├── cache
│   │   │   │   │   │   ├── orders.rs
│   │   │   │   │   │   ├── query_sets.rs
│   │   │   │   │   │   └── xrate.rs
│   │   │   │   │   ├── client_order_id.rs
│   │   │   │   │   ├── logging.rs
│   │   │   │   │   ├── matching_iai.rs
│   │   │   │   │   ├── matching.rs
│   │   │   │   │   ├── msgbus.rs
│   │   │   │   │   ├── mstr.rs
│   │   │   │   │   ├── order_list_id.rs
│   │   │   │   │   ├── position_id.rs
│   │   │   │   │   └── throttler.rs
│   │   │   │   ├── Cargo.toml
│   │   │   │   ├── examples
│   │   │   │   │   ├── greeks_actor_example.rs
│   │   │   │   │   └── greeks.md
│   │   │   │   ├── LICENSE -> ../../LICENSE
│   │   │   │   ├── proptest-regressions
│   │   │   │   │   ├── throttler.txt
│   │   │   │   │   └── timer.txt
│   │   │   │   ├── README.md
│   │   │   │   └── src
│   │   │   │       ├── actor
│   │   │   │       │   ├── data_actor.rs
│   │   │   │       │   ├── indicators.rs
│   │   │   │       │   ├── mod.rs
│   │   │   │       │   ├── registry.rs
│   │   │   │       │   └── tests.rs
│   │   │   │       ├── cache
│   │   │   │       │   ├── bounded.rs
│   │   │   │       │   ├── config.rs
│   │   │   │       │   ├── database.rs
│   │   │   │       │   ├── error.rs
│   │   │   │       │   ├── fifo.rs
│   │   │   │       │   ├── index.rs
│   │   │   │       │   ├── mod.rs
│   │   │   │       │   ├── position.rs
│   │   │   │       │   ├── quote.rs
│   │   │   │       │   ├── refs.rs
│   │   │   │       │   └── tests.rs
│   │   │   │       ├── clients
│   │   │   │       │   ├── data.rs
│   │   │   │       │   ├── execution.rs
│   │   │   │       │   └── mod.rs
│   │   │   │       ├── clock.rs
│   │   │   │       ├── component.rs
│   │   │   │       ├── config.rs
│   │   │   │       ├── custom.rs
│   │   │   │       ├── defi
│   │   │   │       │   ├── cache.rs
│   │   │   │       │   ├── data_actor.rs
│   │   │   │       │   ├── mod.rs
│   │   │   │       │   ├── msgbus.rs
│   │   │   │       │   └── switchboard.rs
│   │   │   │       ├── enums.rs
│   │   │   │       ├── factories
│   │   │   │       │   ├── client.rs
│   │   │   │       │   ├── event.rs
│   │   │   │       │   ├── mod.rs
│   │   │   │       │   └── order.rs
│   │   │   │       ├── generators
│   │   │   │       │   ├── client_order_id.rs
│   │   │   │       │   ├── mod.rs
│   │   │   │       │   ├── order_list_id.rs
│   │   │   │       │   └── position_id.rs
│   │   │   │       ├── greeks.rs
│   │   │   │       ├── lib.rs
│   │   │   │       ├── live
│   │   │   │       │   ├── clock.rs
│   │   │   │       │   ├── dst.rs
│   │   │   │       │   ├── listener.rs
│   │   │   │       │   ├── mod.rs
│   │   │   │       │   ├── runner.rs
│   │   │   │       │   ├── runtime.rs
│   │   │   │       │   ├── task.rs
│   │   │   │       │   └── timer.rs
│   │   │   │       ├── logging
│   │   │   │       │   ├── bridge.rs
│   │   │   │       │   ├── config.rs
│   │   │   │       │   ├── headers.rs
│   │   │   │       │   ├── logger.rs
│   │   │   │       │   ├── macros.rs
│   │   │   │       │   ├── mod.rs
│   │   │   │       │   └── writer.rs
│   │   │   │       ├── macros.rs
│   │   │   │       ├── messages
│   │   │   │       │   ├── data
│   │   │   │       │   │   ├── mod.rs
│   │   │   │       │   │   ├── request.rs
│   │   │   │       │   │   ├── response.rs
│   │   │   │       │   │   ├── subscribe.rs
│   │   │   │       │   │   └── unsubscribe.rs
│   │   │   │       │   ├── defi
│   │   │   │       │   │   ├── mod.rs
│   │   │   │       │   │   ├── request.rs
│   │   │   │       │   │   ├── subscribe.rs
│   │   │   │       │   │   └── unsubscribe.rs
│   │   │   │       │   ├── execution
│   │   │   │       │   │   ├── cancel.rs
│   │   │   │       │   │   ├── mod.rs
│   │   │   │       │   │   ├── modify.rs
│   │   │   │       │   │   ├── query.rs
│   │   │   │       │   │   ├── report.rs
│   │   │   │       │   │   └── submit.rs
│   │   │   │       │   ├── mod.rs
│   │   │   │       │   └── system
│   │   │   │       │       ├── component.rs
│   │   │   │       │       ├── mod.rs
│   │   │   │       │       ├── queue.rs
│   │   │   │       │       ├── shutdown.rs
│   │   │   │       │       ├── socket.rs
│   │   │   │       │       └── trading.rs
│   │   │   │       ├── msgbus
│   │   │   │       │   ├── api.rs
│   │   │   │       │   ├── backing.rs
│   │   │   │       │   ├── config.rs
│   │   │   │       │   ├── core.rs
│   │   │   │       │   ├── external
│   │   │   │       │   │   ├── codec
│   │   │   │       │   │   │   ├── capnp_unavailable.rs
│   │   │   │       │   │   │   ├── capnp.rs
│   │   │   │       │   │   │   ├── json.rs
│   │   │   │       │   │   │   ├── mod.rs
│   │   │   │       │   │   │   ├── msgpack.rs
│   │   │   │       │   │   │   ├── sbe_unavailable.rs
│   │   │   │       │   │   │   └── sbe.rs
│   │   │   │       │   │   └── mod.rs
│   │   │   │       │   ├── matching.rs
│   │   │   │       │   ├── message.rs
│   │   │   │       │   ├── mod.rs
│   │   │   │       │   ├── mstr.rs
│   │   │   │       │   ├── stubs.rs
│   │   │   │       │   ├── switchboard.rs
│   │   │   │       │   ├── typed_endpoints.rs
│   │   │   │       │   ├── typed_handler.rs
│   │   │   │       │   └── typed_router.rs
│   │   │   │       ├── providers.rs
│   │   │   │       ├── python
│   │   │   │       │   ├── actor.rs
│   │   │   │       │   ├── cache.rs
│   │   │   │       │   ├── clock.rs
│   │   │   │       │   ├── custom.rs
│   │   │   │       │   ├── enums.rs
│   │   │   │       │   ├── factory.rs
│   │   │   │       │   ├── fifo.rs
│   │   │   │       │   ├── greeks.rs
│   │   │   │       │   ├── indicators.rs
│   │   │   │       │   ├── listener.rs
│   │   │   │       │   ├── logging.rs
│   │   │   │       │   ├── mod.rs
│   │   │   │       │   ├── msgbus.rs
│   │   │   │       │   ├── order_factory.rs
│   │   │   │       │   ├── runtime.rs
│   │   │   │       │   ├── signal.rs
│   │   │   │       │   ├── system.rs
│   │   │   │       │   ├── timer.rs
│   │   │   │       │   └── xrate.rs
│   │   │   │       ├── runner.rs
│   │   │   │       ├── serialization
│   │   │   │       │   ├── capnp
│   │   │   │       │   │   ├── mod.rs
│   │   │   │       │   │   └── trading.rs
│   │   │   │       │   └── mod.rs
│   │   │   │       ├── signal.rs
│   │   │   │       ├── testing.rs
│   │   │   │       ├── throttler.rs
│   │   │   │       ├── timer.rs
│   │   │   │       └── xrate.rs
│   │   │   ├── core
│   │   │   │   ├── benches
│   │   │   │   │   ├── concurrent_map.rs
│   │   │   │   │   ├── correctness.rs
│   │   │   │   │   ├── datetime.rs
│   │   │   │   │   ├── decimal_deserialization.rs
│   │   │   │   │   ├── hash_map.rs
│   │   │   │   │   ├── hex.rs
│   │   │   │   │   ├── identifier_comparison.rs
│   │   │   │   │   ├── stack_str_iai.rs
│   │   │   │   │   ├── stack_str.rs
│   │   │   │   │   ├── time.rs
│   │   │   │   │   ├── to_snake_case.rs
│   │   │   │   │   ├── urlencoding.rs
│   │   │   │   │   └── uuid.rs
│   │   │   │   ├── build.rs
│   │   │   │   ├── Cargo.toml
│   │   │   │   ├── cbindgen.toml
│   │   │   │   ├── LICENSE -> ../../LICENSE
│   │   │   │   ├── README.md
│   │   │   │   ├── src
│   │   │   │   │   ├── collections.rs
│   │   │   │   │   ├── consts.rs
│   │   │   │   │   ├── correctness.rs
│   │   │   │   │   ├── datetime.rs
│   │   │   │   │   ├── drop.rs
│   │   │   │   │   ├── env.rs
│   │   │   │   │   ├── ffi
│   │   │   │   │   │   ├── cvec.rs
│   │   │   │   │   │   ├── datetime.rs
│   │   │   │   │   │   ├── mod.rs
│   │   │   │   │   │   ├── parsing.rs
│   │   │   │   │   │   ├── string.rs
│   │   │   │   │   │   └── uuid.rs
│   │   │   │   │   ├── hex.rs
│   │   │   │   │   ├── lib.rs
│   │   │   │   │   ├── math.rs
│   │   │   │   │   ├── nanos.rs
│   │   │   │   │   ├── params.rs
│   │   │   │   │   ├── paths.rs
│   │   │   │   │   ├── python
│   │   │   │   │   │   ├── casing.rs
│   │   │   │   │   │   ├── datetime.rs
│   │   │   │   │   │   ├── enums.rs
│   │   │   │   │   │   ├── mod.rs
│   │   │   │   │   │   ├── params.rs
│   │   │   │   │   │   ├── parsing.rs
│   │   │   │   │   │   ├── serialization.rs
│   │   │   │   │   │   ├── string.rs
│   │   │   │   │   │   ├── uuid.rs
│   │   │   │   │   │   └── version.rs
│   │   │   │   │   ├── serialization.rs
│   │   │   │   │   ├── shared.rs
│   │   │   │   │   ├── string
│   │   │   │   │   │   ├── conversions.rs
│   │   │   │   │   │   ├── formatting.rs
│   │   │   │   │   │   ├── mod.rs
│   │   │   │   │   │   ├── parsing.rs
│   │   │   │   │   │   ├── secret.rs
│   │   │   │   │   │   ├── semver.rs
│   │   │   │   │   │   ├── stack_str.rs
│   │   │   │   │   │   └── urlencoding.rs
│   │   │   │   │   ├── time.rs
│   │   │   │   │   └── uuid.rs
│   │   │   │   └── tests
│   │   │   │       └── layout.rs
│   │   │   ├── cryptography
│   │   │   │   ├── Cargo.toml
│   │   │   │   ├── LICENSE -> ../../LICENSE
│   │   │   │   ├── README.md
│   │   │   │   └── src
│   │   │   │       ├── lib.rs
│   │   │   │       ├── providers.rs
│   │   │   │       ├── python
│   │   │   │       │   ├── mod.rs
│   │   │   │       │   └── signing.rs
│   │   │   │       ├── signing.rs
│   │   │   │       └── tls.rs
│   │   │   ├── data
│   │   │   │   ├── benches
│   │   │   │   │   ├── aggregation.rs
│   │   │   │   │   └── engine.rs
│   │   │   │   ├── Cargo.toml
│   │   │   │   ├── LICENSE -> ../../LICENSE
│   │   │   │   ├── proptest-regressions
│   │   │   │   │   └── aggregation.txt
│   │   │   │   ├── README.md
│   │   │   │   ├── src
│   │   │   │   │   ├── aggregation.rs
│   │   │   │   │   ├── client.rs
│   │   │   │   │   ├── defi
│   │   │   │   │   │   ├── client.rs
│   │   │   │   │   │   ├── engine.rs
│   │   │   │   │   │   └── mod.rs
│   │   │   │   │   ├── engine
│   │   │   │   │   │   ├── bar.rs
│   │   │   │   │   │   ├── book.rs
│   │   │   │   │   │   ├── commands.rs
│   │   │   │   │   │   ├── config.rs
│   │   │   │   │   │   ├── handlers.rs
│   │   │   │   │   │   ├── mod.rs
│   │   │   │   │   │   ├── pool.rs
│   │   │   │   │   │   ├── requests.rs
│   │   │   │   │   │   ├── streaming.rs
│   │   │   │   │   │   └── time_range.rs
│   │   │   │   │   ├── lib.rs
│   │   │   │   │   ├── option_chains
│   │   │   │   │   │   ├── aggregator.rs
│   │   │   │   │   │   ├── atm_tracker.rs
│   │   │   │   │   │   ├── constants.rs
│   │   │   │   │   │   ├── handlers.rs
│   │   │   │   │   │   ├── manager.rs
│   │   │   │   │   │   └── mod.rs
│   │   │   │   │   └── python
│   │   │   │   │       ├── config.rs
│   │   │   │   │       └── mod.rs
│   │   │   │   └── tests
│   │   │   │       ├── client.rs
│   │   │   │       ├── common
│   │   │   │       │   ├── mocks.rs
│   │   │   │       │   └── mod.rs
│   │   │   │       └── engine.rs
│   │   │   ├── event_store
│   │   │   │   ├── benches
│   │   │   │   │   ├── codec.rs
│   │   │   │   │   └── hash.rs
│   │   │   │   ├── Cargo.toml
│   │   │   │   ├── LICENSE -> ../../LICENSE
│   │   │   │   ├── README.md
│   │   │   │   ├── src
│   │   │   │   │   ├── backend
│   │   │   │   │   │   ├── memory.rs
│   │   │   │   │   │   ├── mod.rs
│   │   │   │   │   │   └── redb.rs
│   │   │   │   │   ├── bin
│   │   │   │   │   │   └── verify.rs
│   │   │   │   │   ├── capture
│   │   │   │   │   │   ├── adapter.rs
│   │   │   │   │   │   ├── builtins.rs
│   │   │   │   │   │   ├── encoder.rs
│   │   │   │   │   │   ├── mod.rs
│   │   │   │   │   │   └── registry.rs
│   │   │   │   │   ├── codec.rs
│   │   │   │   │   ├── entry.rs
│   │   │   │   │   ├── error.rs
│   │   │   │   │   ├── format.rs
│   │   │   │   │   ├── hash.rs
│   │   │   │   │   ├── headers.rs
│   │   │   │   │   ├── kernel.rs
│   │   │   │   │   ├── lib.rs
│   │   │   │   │   ├── manifest.rs
│   │   │   │   │   ├── markers
│   │   │   │   │   │   ├── backend.rs
│   │   │   │   │   │   ├── capture.rs
│   │   │   │   │   │   ├── cursor.rs
│   │   │   │   │   │   ├── extractor.rs
│   │   │   │   │   │   ├── join.rs
│   │   │   │   │   │   ├── marker.rs
│   │   │   │   │   │   ├── mod.rs
│   │   │   │   │   │   ├── reader.rs
│   │   │   │   │   │   ├── redb.rs
│   │   │   │   │   │   ├── test_support.rs
│   │   │   │   │   │   ├── verifier.rs
│   │   │   │   │   │   └── writer.rs
│   │   │   │   │   ├── reader
│   │   │   │   │   │   └── mod.rs
│   │   │   │   │   ├── replay
│   │   │   │   │   │   └── catalog.rs
│   │   │   │   │   ├── replay.rs
│   │   │   │   │   ├── retention.rs
│   │   │   │   │   ├── snapshot.rs
│   │   │   │   │   ├── verifier
│   │   │   │   │   │   └── mod.rs
│   │   │   │   │   ├── wire.rs
│   │   │   │   │   └── writer
│   │   │   │   │       ├── batcher.rs
│   │   │   │   │       ├── halt.rs
│   │   │   │   │       └── mod.rs
│   │   │   │   └── tests
│   │   │   │       ├── capture.rs
│   │   │   │       ├── envelope.rs
│   │   │   │       ├── lifecycle.rs
│   │   │   │       ├── reader.rs
│   │   │   │       ├── redb.rs
│   │   │   │       ├── replay.rs
│   │   │   │       ├── retention.rs
│   │   │   │       ├── verifier.rs
│   │   │   │       └── writer.rs
│   │   │   ├── execution
│   │   │   │   ├── benches
│   │   │   │   │   ├── matching_core.rs
│   │   │   │   │   └── matching_engine.rs
│   │   │   │   ├── Cargo.toml
│   │   │   │   ├── LICENSE -> ../../LICENSE
│   │   │   │   ├── proptest-regressions
│   │   │   │   │   ├── matching_engine
│   │   │   │   │   │   └── engine.txt
│   │   │   │   │   └── reconciliation
│   │   │   │   │       └── proptests.txt
│   │   │   │   ├── README.md
│   │   │   │   ├── src
│   │   │   │   │   ├── client
│   │   │   │   │   │   ├── core.rs
│   │   │   │   │   │   └── mod.rs
│   │   │   │   │   ├── engine
│   │   │   │   │   │   ├── config.rs
│   │   │   │   │   │   ├── mod.rs
│   │   │   │   │   │   ├── position.rs
│   │   │   │   │   │   └── stubs.rs
│   │   │   │   │   ├── lib.rs
│   │   │   │   │   ├── matching_core.rs
│   │   │   │   │   ├── matching_engine
│   │   │   │   │   │   ├── config.rs
│   │   │   │   │   │   ├── ids_generator.rs
│   │   │   │   │   │   ├── mod.rs
│   │   │   │   │   │   └── settlement.rs
│   │   │   │   │   ├── models
│   │   │   │   │   │   ├── fee.rs
│   │   │   │   │   │   ├── fill.rs
│   │   │   │   │   │   ├── latency.rs
│   │   │   │   │   │   └── mod.rs
│   │   │   │   │   ├── order_emulator
│   │   │   │   │   │   ├── adapter.rs
│   │   │   │   │   │   ├── config.rs
│   │   │   │   │   │   ├── emulator.rs
│   │   │   │   │   │   ├── handlers.rs
│   │   │   │   │   │   └── mod.rs
│   │   │   │   │   ├── order_manager
│   │   │   │   │   │   ├── manager.rs
│   │   │   │   │   │   └── mod.rs
│   │   │   │   │   ├── protection.rs
│   │   │   │   │   ├── python
│   │   │   │   │   │   ├── config.rs
│   │   │   │   │   │   ├── fee.rs
│   │   │   │   │   │   ├── fill.rs
│   │   │   │   │   │   ├── latency.rs
│   │   │   │   │   │   └── mod.rs
│   │   │   │   │   ├── reconciliation
│   │   │   │   │   │   ├── ids.rs
│   │   │   │   │   │   ├── mod.rs
│   │   │   │   │   │   ├── orders.rs
│   │   │   │   │   │   ├── positions.rs
│   │   │   │   │   │   ├── proptests.rs
│   │   │   │   │   │   ├── tests.rs
│   │   │   │   │   │   └── types.rs
│   │   │   │   │   └── trailing.rs
│   │   │   │   └── tests
│   │   │   │       ├── exec_engine.rs
│   │   │   │       ├── matching_engine
│   │   │   │       │   └── cache_database.rs
│   │   │   │       ├── matching_engine.rs
│   │   │   │       └── order_emulator.rs
│   │   │   ├── indicators
│   │   │   │   ├── Cargo.toml
│   │   │   │   ├── LICENSE -> ../../LICENSE
│   │   │   │   ├── README.md
│   │   │   │   └── src
│   │   │   │       ├── average
│   │   │   │       │   ├── ama.rs
│   │   │   │       │   ├── dema.rs
│   │   │   │       │   ├── ema.rs
│   │   │   │       │   ├── hma.rs
│   │   │   │       │   ├── lr.rs
│   │   │   │       │   ├── mod.rs
│   │   │   │       │   ├── rma.rs
│   │   │   │       │   ├── sma.rs
│   │   │   │       │   ├── vidya.rs
│   │   │   │       │   ├── vwap.rs
│   │   │   │       │   └── wma.rs
│   │   │   │       ├── book
│   │   │   │       │   ├── imbalance.rs
│   │   │   │       │   └── mod.rs
│   │   │   │       ├── indicator.rs
│   │   │   │       ├── lib.rs
│   │   │   │       ├── momentum
│   │   │   │       │   ├── amat.rs
│   │   │   │       │   ├── aroon.rs
│   │   │   │       │   ├── bb.rs
│   │   │   │       │   ├── bias.rs
│   │   │   │       │   ├── cci.rs
│   │   │   │       │   ├── cmo.rs
│   │   │   │       │   ├── dm.rs
│   │   │   │       │   ├── ichimoku.rs
│   │   │   │       │   ├── kvo.rs
│   │   │   │       │   ├── macd.rs
│   │   │   │       │   ├── mod.rs
│   │   │   │       │   ├── obv.rs
│   │   │   │       │   ├── pressure.rs
│   │   │   │       │   ├── psl.rs
│   │   │   │       │   ├── roc.rs
│   │   │   │       │   ├── rsi.rs
│   │   │   │       │   ├── stochastics.rs
│   │   │   │       │   ├── swings.rs
│   │   │   │       │   └── vhf.rs
│   │   │   │       ├── python
│   │   │   │       │   ├── average
│   │   │   │       │   │   ├── ama.rs
│   │   │   │       │   │   ├── dema.rs
│   │   │   │       │   │   ├── ema.rs
│   │   │   │       │   │   ├── hma.rs
│   │   │   │       │   │   ├── lr.rs
│   │   │   │       │   │   ├── mod.rs
│   │   │   │       │   │   ├── rma.rs
│   │   │   │       │   │   ├── sma.rs
│   │   │   │       │   │   ├── vidya.rs
│   │   │   │       │   │   ├── vwap.rs
│   │   │   │       │   │   └── wma.rs
│   │   │   │       │   ├── book
│   │   │   │       │   │   ├── imbalance.rs
│   │   │   │       │   │   └── mod.rs
│   │   │   │       │   ├── mod.rs
│   │   │   │       │   ├── momentum
│   │   │   │       │   │   ├── amat.rs
│   │   │   │       │   │   ├── aroon.rs
│   │   │   │       │   │   ├── bb.rs
│   │   │   │       │   │   ├── bias.rs
│   │   │   │       │   │   ├── cci.rs
│   │   │   │       │   │   ├── cmo.rs
│   │   │   │       │   │   ├── dm.rs
│   │   │   │       │   │   ├── ichimoku.rs
│   │   │   │       │   │   ├── kvo.rs
│   │   │   │       │   │   ├── macd.rs
│   │   │   │       │   │   ├── mod.rs
│   │   │   │       │   │   ├── obv.rs
│   │   │   │       │   │   ├── pressure.rs
│   │   │   │       │   │   ├── psl.rs
│   │   │   │       │   │   ├── roc.rs
│   │   │   │       │   │   ├── rsi.rs
│   │   │   │       │   │   ├── stochastics.rs
│   │   │   │       │   │   ├── swings.rs
│   │   │   │       │   │   └── vhf.rs
│   │   │   │       │   ├── ratio
│   │   │   │       │   │   ├── efficiency_ratio.rs
│   │   │   │       │   │   ├── mod.rs
│   │   │   │       │   │   └── spread_analyzer.rs
│   │   │   │       │   └── volatility
│   │   │   │       │       ├── atr.rs
│   │   │   │       │       ├── dc.rs
│   │   │   │       │       ├── fuzzy.rs
│   │   │   │       │       ├── kc.rs
│   │   │   │       │       ├── kp.rs
│   │   │   │       │       ├── mod.rs
│   │   │   │       │       ├── rvi.rs
│   │   │   │       │       └── vr.rs
│   │   │   │       ├── ratio
│   │   │   │       │   ├── efficiency_ratio.rs
│   │   │   │       │   ├── mod.rs
│   │   │   │       │   └── spread_analyzer.rs
│   │   │   │       ├── stubs.rs
│   │   │   │       ├── testing.rs
│   │   │   │       └── volatility
│   │   │   │           ├── atr.rs
│   │   │   │           ├── dc.rs
│   │   │   │           ├── fuzzy.rs
│   │   │   │           ├── kc.rs
│   │   │   │           ├── kp.rs
│   │   │   │           ├── mod.rs
│   │   │   │           ├── rvi.rs
│   │   │   │           └── vr.rs
│   │   │   ├── infrastructure
│   │   │   │   ├── Cargo.toml
│   │   │   │   ├── LICENSE -> ../../LICENSE
│   │   │   │   ├── README.md
│   │   │   │   ├── src
│   │   │   │   │   ├── lib.rs
│   │   │   │   │   ├── python
│   │   │   │   │   │   ├── mod.rs
│   │   │   │   │   │   ├── redis
│   │   │   │   │   │   │   ├── cache.rs
│   │   │   │   │   │   │   ├── mod.rs
│   │   │   │   │   │   │   └── msgbus.rs
│   │   │   │   │   │   └── sql
│   │   │   │   │   │       ├── cache.rs
│   │   │   │   │   │       ├── mod.rs
│   │   │   │   │   │       └── pg.rs
│   │   │   │   │   ├── redis
│   │   │   │   │   │   ├── cache.rs
│   │   │   │   │   │   ├── mod.rs
│   │   │   │   │   │   ├── msgbus.rs
│   │   │   │   │   │   └── queries.rs
│   │   │   │   │   └── sql
│   │   │   │   │       ├── cache.rs
│   │   │   │   │       ├── mod.rs
│   │   │   │   │       ├── models
│   │   │   │   │       │   ├── accounts.rs
│   │   │   │   │       │   ├── data.rs
│   │   │   │   │       │   ├── enums.rs
│   │   │   │   │       │   ├── general.rs
│   │   │   │   │       │   ├── instruments.rs
│   │   │   │   │       │   ├── mod.rs
│   │   │   │   │       │   ├── orders.rs
│   │   │   │   │       │   ├── positions.rs
│   │   │   │   │       │   └── types.rs
│   │   │   │   │       ├── pg.rs
│   │   │   │   │       └── queries.rs
│   │   │   │   ├── test_data
│   │   │   │   │   ├── redis_cache_timestamp_chrono.json
│   │   │   │   │   └── redis_msgbus_heartbeat_chrono.txt
│   │   │   │   ├── tests
│   │   │   │   │   ├── test_cache_database_postgres.rs
│   │   │   │   │   ├── test_cache_postgres.rs
│   │   │   │   │   ├── test_cache_redis.rs
│   │   │   │   │   └── test_redis_queries.rs
│   │   │   │   └── TESTS.md
│   │   │   ├── lib.rs
│   │   │   ├── live
│   │   │   │   ├── benches
│   │   │   │   │   ├── queue_monitor.rs
│   │   │   │   │   └── runner.rs
│   │   │   │   ├── Cargo.toml
│   │   │   │   ├── LICENSE -> ../../LICENSE
│   │   │   │   ├── README.md
│   │   │   │   ├── src
│   │   │   │   │   ├── execution
│   │   │   │   │   │   ├── client.rs
│   │   │   │   │   │   ├── context.rs
│   │   │   │   │   │   ├── emitter.rs
│   │   │   │   │   │   ├── failure.rs
│   │   │   │   │   │   ├── manager.rs
│   │   │   │   │   │   ├── mod.rs
│   │   │   │   │   │   └── recency.rs
│   │   │   │   │   ├── fuzz
│   │   │   │   │   │   └── mod.rs
│   │   │   │   │   ├── lib.rs
│   │   │   │   │   ├── node
│   │   │   │   │   │   ├── builder.rs
│   │   │   │   │   │   ├── config.rs
│   │   │   │   │   │   ├── metrics.rs
│   │   │   │   │   │   ├── mod.rs
│   │   │   │   │   │   ├── plugin.rs
│   │   │   │   │   │   ├── queue.rs
│   │   │   │   │   │   └── state.rs
│   │   │   │   │   ├── python
│   │   │   │   │   │   ├── config.rs
│   │   │   │   │   │   ├── mod.rs
│   │   │   │   │   │   └── node.rs
│   │   │   │   │   └── runner.rs
│   │   │   │   └── tests
│   │   │   │       ├── manager.rs
│   │   │   │       ├── node.rs
│   │   │   │       └── stress.rs
│   │   │   ├── model
│   │   │   │   ├── benches
│   │   │   │   │   ├── black_scholes_criterion.rs
│   │   │   │   │   ├── book_iai.rs
│   │   │   │   │   ├── expressions_criterion.rs
│   │   │   │   │   ├── f64_vs_decimal_to_price_quantity.rs
│   │   │   │   │   ├── fixed_precision_criterion.rs
│   │   │   │   │   ├── fixed_precision_iai.rs
│   │   │   │   │   ├── greeks_criterion.rs
│   │   │   │   │   ├── money_criterion.rs
│   │   │   │   │   ├── order_fills_criterion.rs
│   │   │   │   │   ├── position_replay_criterion.rs
│   │   │   │   │   ├── price_criterion.rs
│   │   │   │   │   └── quantity_criterion.rs
│   │   │   │   ├── Cargo.toml
│   │   │   │   ├── cbindgen.toml
│   │   │   │   ├── LICENSE -> ../../LICENSE
│   │   │   │   ├── proptest-regressions
│   │   │   │   │   ├── orderbook
│   │   │   │   │   │   └── tests.txt
│   │   │   │   │   ├── position.txt
│   │   │   │   │   └── types
│   │   │   │   │       ├── money.txt
│   │   │   │   │       ├── price.txt
│   │   │   │   │       └── quantity.txt
│   │   │   │   ├── README.md
│   │   │   │   └── src
│   │   │   │       ├── accounts
│   │   │   │       │   ├── any.rs
│   │   │   │       │   ├── base.rs
│   │   │   │       │   ├── betting.rs
│   │   │   │       │   ├── cash.rs
│   │   │   │       │   ├── margin_model.rs
│   │   │   │       │   ├── margin.rs
│   │   │   │       │   ├── mod.rs
│   │   │   │       │   └── stubs.rs
│   │   │   │       ├── currencies.rs
│   │   │   │       ├── data
│   │   │   │       │   ├── bar.rs
│   │   │   │       │   ├── bet.rs
│   │   │   │       │   ├── black_scholes.rs
│   │   │   │       │   ├── close.rs
│   │   │   │       │   ├── custom.rs
│   │   │   │       │   ├── delta.rs
│   │   │   │       │   ├── deltas.rs
│   │   │   │       │   ├── depth.rs
│   │   │   │       │   ├── forward.rs
│   │   │   │       │   ├── funding.rs
│   │   │   │       │   ├── greeks.rs
│   │   │   │       │   ├── mod.rs
│   │   │   │       │   ├── option_chain.rs
│   │   │   │       │   ├── order.rs
│   │   │   │       │   ├── prices.rs
│   │   │   │       │   ├── quote.rs
│   │   │   │       │   ├── registry.rs
│   │   │   │       │   ├── status.rs
│   │   │   │       │   ├── stubs.rs
│   │   │   │       │   └── trade.rs
│   │   │   │       ├── defi
│   │   │   │       │   ├── amm.rs
│   │   │   │       │   ├── chain.rs
│   │   │   │       │   ├── data
│   │   │   │       │   │   ├── block.rs
│   │   │   │       │   │   ├── collect.rs
│   │   │   │       │   │   ├── fee_protocol_collect.rs
│   │   │   │       │   │   ├── fee_protocol_update.rs
│   │   │   │       │   │   ├── flash.rs
│   │   │   │       │   │   ├── liquidity.rs
│   │   │   │       │   │   ├── mod.rs
│   │   │   │       │   │   ├── swap_trade_info.rs
│   │   │   │       │   │   ├── swap.rs
│   │   │   │       │   │   └── transaction.rs
│   │   │   │       │   ├── dex.rs
│   │   │   │       │   ├── hex.rs
│   │   │   │       │   ├── mod.rs
│   │   │   │       │   ├── pool_analysis
│   │   │   │       │   │   ├── compare.rs
│   │   │   │       │   │   ├── error.rs
│   │   │   │       │   │   ├── mod.rs
│   │   │   │       │   │   ├── position.rs
│   │   │   │       │   │   ├── profiler.rs
│   │   │   │       │   │   ├── quote.rs
│   │   │   │       │   │   ├── size_estimator.rs
│   │   │   │       │   │   ├── snapshot.rs
│   │   │   │       │   │   ├── swap_math.rs
│   │   │   │       │   │   └── tests.rs
│   │   │   │       │   ├── pool_identifier.rs
│   │   │   │       │   ├── reporting.rs
│   │   │   │       │   ├── rpc.rs
│   │   │   │       │   ├── stubs.rs
│   │   │   │       │   ├── tick_map
│   │   │   │       │   │   ├── bit_math.rs
│   │   │   │       │   │   ├── full_math.rs
│   │   │   │       │   │   ├── liquidity_math.rs
│   │   │   │       │   │   ├── mod.rs
│   │   │   │       │   │   ├── sqrt_price_math.rs
│   │   │   │       │   │   ├── tick_bitmap.rs
│   │   │   │       │   │   ├── tick_math.rs
│   │   │   │       │   │   └── tick.rs
│   │   │   │       │   ├── token.rs
│   │   │   │       │   ├── types
│   │   │   │       │   │   ├── mod.rs
│   │   │   │       │   │   ├── money.rs
│   │   │   │       │   │   ├── price.rs
│   │   │   │       │   │   └── quantity.rs
│   │   │   │       │   ├── validation.rs
│   │   │   │       │   └── wallet.rs
│   │   │   │       ├── enums.rs
│   │   │   │       ├── events
│   │   │   │       │   ├── account
│   │   │   │       │   │   ├── mod.rs
│   │   │   │       │   │   ├── state.rs
│   │   │   │       │   │   └── stubs.rs
│   │   │   │       │   ├── funding
│   │   │   │       │   │   ├── mod.rs
│   │   │   │       │   │   └── settlement.rs
│   │   │   │       │   ├── mod.rs
│   │   │   │       │   ├── order
│   │   │   │       │   │   ├── accepted_batch.rs
│   │   │   │       │   │   ├── accepted.rs
│   │   │   │       │   │   ├── any.rs
│   │   │   │       │   │   ├── cancel_rejected.rs
│   │   │   │       │   │   ├── canceled_batch.rs
│   │   │   │       │   │   ├── canceled.rs
│   │   │   │       │   │   ├── denied_reason.rs
│   │   │   │       │   │   ├── denied.rs
│   │   │   │       │   │   ├── emulated.rs
│   │   │   │       │   │   ├── expired.rs
│   │   │   │       │   │   ├── fill_voided.rs
│   │   │   │       │   │   ├── filled.rs
│   │   │   │       │   │   ├── initialized.rs
│   │   │   │       │   │   ├── mod.rs
│   │   │   │       │   │   ├── modify_rejected.rs
│   │   │   │       │   │   ├── pending_cancel.rs
│   │   │   │       │   │   ├── pending_update.rs
│   │   │   │       │   │   ├── rejected.rs
│   │   │   │       │   │   ├── released.rs
│   │   │   │       │   │   ├── snapshot.rs
│   │   │   │       │   │   ├── spec
│   │   │   │       │   │   │   ├── accepted.rs
│   │   │   │       │   │   │   ├── cancel_rejected.rs
│   │   │   │       │   │   │   ├── canceled.rs
│   │   │   │       │   │   │   ├── denied.rs
│   │   │   │       │   │   │   ├── emulated.rs
│   │   │   │       │   │   │   ├── expired.rs
│   │   │   │       │   │   │   ├── fill_voided.rs
│   │   │   │       │   │   │   ├── filled.rs
│   │   │   │       │   │   │   ├── initialized.rs
│   │   │   │       │   │   │   ├── mod.rs
│   │   │   │       │   │   │   ├── modify_rejected.rs
│   │   │   │       │   │   │   ├── pending_cancel.rs
│   │   │   │       │   │   │   ├── pending_update.rs
│   │   │   │       │   │   │   ├── rejected.rs
│   │   │   │       │   │   │   ├── released.rs
│   │   │   │       │   │   │   ├── submitted.rs
│   │   │   │       │   │   │   ├── triggered.rs
│   │   │   │       │   │   │   └── updated.rs
│   │   │   │       │   │   ├── stubs.rs
│   │   │   │       │   │   ├── submitted_batch.rs
│   │   │   │       │   │   ├── submitted.rs
│   │   │   │       │   │   ├── triggered.rs
│   │   │   │       │   │   └── updated.rs
│   │   │   │       │   ├── portfolio
│   │   │   │       │   │   ├── mod.rs
│   │   │   │       │   │   └── snapshot.rs
│   │   │   │       │   └── position
│   │   │   │       │       ├── adjusted.rs
│   │   │   │       │       ├── changed.rs
│   │   │   │       │       ├── closed.rs
│   │   │   │       │       ├── mod.rs
│   │   │   │       │       ├── opened.rs
│   │   │   │       │       └── snapshot.rs
│   │   │   │       ├── expressions
│   │   │   │       │   ├── error.rs
│   │   │   │       │   ├── eval.rs
│   │   │   │       │   ├── lexer.rs
│   │   │   │       │   ├── mod.rs
│   │   │   │       │   └── parser.rs
│   │   │   │       ├── ffi
│   │   │   │       │   ├── data
│   │   │   │       │   │   ├── bar.rs
│   │   │   │       │   │   ├── delta.rs
│   │   │   │       │   │   ├── deltas.rs
│   │   │   │       │   │   ├── depth.rs
│   │   │   │       │   │   ├── mod.rs
│   │   │   │       │   │   ├── order.rs
│   │   │   │       │   │   ├── prices.rs
│   │   │   │       │   │   ├── quote.rs
│   │   │   │       │   │   └── trade.rs
│   │   │   │       │   ├── enums.rs
│   │   │   │       │   ├── events
│   │   │   │       │   │   ├── mod.rs
│   │   │   │       │   │   └── order.rs
│   │   │   │       │   ├── identifiers
│   │   │   │       │   │   ├── account_id.rs
│   │   │   │       │   │   ├── client_id.rs
│   │   │   │       │   │   ├── client_order_id.rs
│   │   │   │       │   │   ├── component_id.rs
│   │   │   │       │   │   ├── exec_algorithm_id.rs
│   │   │   │       │   │   ├── instrument_id.rs
│   │   │   │       │   │   ├── mod.rs
│   │   │   │       │   │   ├── order_list_id.rs
│   │   │   │       │   │   ├── position_id.rs
│   │   │   │       │   │   ├── strategy_id.rs
│   │   │   │       │   │   ├── symbol.rs
│   │   │   │       │   │   ├── trade_id.rs
│   │   │   │       │   │   ├── trader_id.rs
│   │   │   │       │   │   ├── venue_order_id.rs
│   │   │   │       │   │   └── venue.rs
│   │   │   │       │   ├── instruments
│   │   │   │       │   │   ├── mod.rs
│   │   │   │       │   │   └── synthetic.rs
│   │   │   │       │   ├── mod.rs
│   │   │   │       │   ├── orderbook
│   │   │   │       │   │   ├── book.rs
│   │   │   │       │   │   ├── level.rs
│   │   │   │       │   │   └── mod.rs
│   │   │   │       │   └── types
│   │   │   │       │       ├── currency.rs
│   │   │   │       │       ├── mod.rs
│   │   │   │       │       ├── money.rs
│   │   │   │       │       ├── price.rs
│   │   │   │       │       └── quantity.rs
│   │   │   │       ├── identifiers
│   │   │   │       │   ├── account_id.rs
│   │   │   │       │   ├── actor_id.rs
│   │   │   │       │   ├── client_id.rs
│   │   │   │       │   ├── client_order_id.rs
│   │   │   │       │   ├── component_id.rs
│   │   │   │       │   ├── exec_algorithm_id.rs
│   │   │   │       │   ├── instrument_id.rs
│   │   │   │       │   ├── macros.rs
│   │   │   │       │   ├── mod.rs
│   │   │   │       │   ├── option_series_id.rs
│   │   │   │       │   ├── order_list_id.rs
│   │   │   │       │   ├── position_id.rs
│   │   │   │       │   ├── strategy_id.rs
│   │   │   │       │   ├── stubs.rs
│   │   │   │       │   ├── symbol.rs
│   │   │   │       │   ├── trade_id.rs
│   │   │   │       │   ├── trader_id.rs
│   │   │   │       │   ├── venue_order_id.rs
│   │   │   │       │   └── venue.rs
│   │   │   │       ├── instruments
│   │   │   │       │   ├── any.rs
│   │   │   │       │   ├── betting.rs
│   │   │   │       │   ├── binary_option.rs
│   │   │   │       │   ├── cfd.rs
│   │   │   │       │   ├── commodity.rs
│   │   │   │       │   ├── crypto_future.rs
│   │   │   │       │   ├── crypto_futures_spread.rs
│   │   │   │       │   ├── crypto_option_spread.rs
│   │   │   │       │   ├── crypto_option.rs
│   │   │   │       │   ├── crypto_perpetual.rs
│   │   │   │       │   ├── currency_pair.rs
│   │   │   │       │   ├── equity.rs
│   │   │   │       │   ├── futures_contract.rs
│   │   │   │       │   ├── futures_spread.rs
│   │   │   │       │   ├── index_instrument.rs
│   │   │   │       │   ├── mod.rs
│   │   │   │       │   ├── option_contract.rs
│   │   │   │       │   ├── option_spread.rs
│   │   │   │       │   ├── perpetual_contract.rs
│   │   │   │       │   ├── stubs.rs
│   │   │   │       │   ├── synthetic.rs
│   │   │   │       │   ├── tick_scheme.rs
│   │   │   │       │   └── tokenized_asset.rs
│   │   │   │       ├── lib.rs
│   │   │   │       ├── macros.rs
│   │   │   │       ├── orderbook
│   │   │   │       │   ├── aggregation.rs
│   │   │   │       │   ├── analysis.rs
│   │   │   │       │   ├── book.rs
│   │   │   │       │   ├── display.rs
│   │   │   │       │   ├── error.rs
│   │   │   │       │   ├── ladder.rs
│   │   │   │       │   ├── level.rs
│   │   │   │       │   ├── mod.rs
│   │   │   │       │   ├── own.rs
│   │   │   │       │   └── tests.rs
│   │   │   │       ├── orders
│   │   │   │       │   ├── any.rs
│   │   │   │       │   ├── builder.rs
│   │   │   │       │   ├── limit_if_touched.rs
│   │   │   │       │   ├── limit.rs
│   │   │   │       │   ├── list.rs
│   │   │   │       │   ├── market_if_touched.rs
│   │   │   │       │   ├── market_to_limit.rs
│   │   │   │       │   ├── market.rs
│   │   │   │       │   ├── mod.rs
│   │   │   │       │   ├── stop_limit.rs
│   │   │   │       │   ├── stop_market.rs
│   │   │   │       │   ├── stubs.rs
│   │   │   │       │   ├── trailing_stop_limit.rs
│   │   │   │       │   └── trailing_stop_market.rs
│   │   │   │       ├── position.rs
│   │   │   │       ├── python
│   │   │   │       │   ├── account
│   │   │   │       │   │   ├── betting.rs
│   │   │   │       │   │   ├── cash.rs
│   │   │   │       │   │   ├── margin_model.rs
│   │   │   │       │   │   ├── margin.rs
│   │   │   │       │   │   ├── mod.rs
│   │   │   │       │   │   └── transformer.rs
│   │   │   │       │   ├── common.rs
│   │   │   │       │   ├── data
│   │   │   │       │   │   ├── bar.rs
│   │   │   │       │   │   ├── bet.rs
│   │   │   │       │   │   ├── close.rs
│   │   │   │       │   │   ├── custom.rs
│   │   │   │       │   │   ├── delta.rs
│   │   │   │       │   │   ├── deltas.rs
│   │   │   │       │   │   ├── depth.rs
│   │   │   │       │   │   ├── forward.rs
│   │   │   │       │   │   ├── funding.rs
│   │   │   │       │   │   ├── greeks.rs
│   │   │   │       │   │   ├── mod.rs
│   │   │   │       │   │   ├── option_chain.rs
│   │   │   │       │   │   ├── order.rs
│   │   │   │       │   │   ├── prices.rs
│   │   │   │       │   │   ├── quote.rs
│   │   │   │       │   │   ├── status.rs
│   │   │   │       │   │   └── trade.rs
│   │   │   │       │   ├── defi
│   │   │   │       │   │   ├── data.rs
│   │   │   │       │   │   ├── enums.rs
│   │   │   │       │   │   ├── mod.rs
│   │   │   │       │   │   ├── profiler.rs
│   │   │   │       │   │   ├── quote.rs
│   │   │   │       │   │   ├── size_estimator.rs
│   │   │   │       │   │   └── types.rs
│   │   │   │       │   ├── enums.rs
│   │   │   │       │   ├── events
│   │   │   │       │   │   ├── account
│   │   │   │       │   │   │   ├── mod.rs
│   │   │   │       │   │   │   └── state.rs
│   │   │   │       │   │   ├── mod.rs
│   │   │   │       │   │   ├── order
│   │   │   │       │   │   │   ├── accepted.rs
│   │   │   │       │   │   │   ├── cancel_rejected.rs
│   │   │   │       │   │   │   ├── canceled.rs
│   │   │   │       │   │   │   ├── denied.rs
│   │   │   │       │   │   │   ├── emulated.rs
│   │   │   │       │   │   │   ├── expired.rs
│   │   │   │       │   │   │   ├── fill_voided.rs
│   │   │   │       │   │   │   ├── filled.rs
│   │   │   │       │   │   │   ├── initialized.rs
│   │   │   │       │   │   │   ├── mod.rs
│   │   │   │       │   │   │   ├── modify_rejected.rs
│   │   │   │       │   │   │   ├── pending_cancel.rs
│   │   │   │       │   │   │   ├── pending_update.rs
│   │   │   │       │   │   │   ├── rejected.rs
│   │   │   │       │   │   │   ├── released.rs
│   │   │   │       │   │   │   ├── snapshot.rs
│   │   │   │       │   │   │   ├── submitted.rs
│   │   │   │       │   │   │   ├── triggered.rs
│   │   │   │       │   │   │   └── updated.rs
│   │   │   │       │   │   ├── portfolio
│   │   │   │       │   │   │   ├── mod.rs
│   │   │   │       │   │   │   └── snapshot.rs
│   │   │   │       │   │   └── position
│   │   │   │       │   │       ├── adjusted.rs
│   │   │   │       │   │       ├── changed.rs
│   │   │   │       │   │       ├── closed.rs
│   │   │   │       │   │       ├── mod.rs
│   │   │   │       │   │       ├── opened.rs
│   │   │   │       │   │       └── snapshot.rs
│   │   │   │       │   ├── identifiers
│   │   │   │       │   │   ├── instrument_id.rs
│   │   │   │       │   │   ├── mod.rs
│   │   │   │       │   │   ├── option_series_id.rs
│   │   │   │       │   │   ├── symbol.rs
│   │   │   │       │   │   └── trade_id.rs
│   │   │   │       │   ├── instruments
│   │   │   │       │   │   ├── betting.rs
│   │   │   │       │   │   ├── binary_option.rs
│   │   │   │       │   │   ├── cfd.rs
│   │   │   │       │   │   ├── commodity.rs
│   │   │   │       │   │   ├── crypto_future.rs
│   │   │   │       │   │   ├── crypto_futures_spread.rs
│   │   │   │       │   │   ├── crypto_option_spread.rs
│   │   │   │       │   │   ├── crypto_option.rs
│   │   │   │       │   │   ├── crypto_perpetual.rs
│   │   │   │       │   │   ├── currency_pair.rs
│   │   │   │       │   │   ├── equity.rs
│   │   │   │       │   │   ├── futures_contract.rs
│   │   │   │       │   │   ├── futures_spread.rs
│   │   │   │       │   │   ├── index_instrument.rs
│   │   │   │       │   │   ├── mod.rs
│   │   │   │       │   │   ├── option_contract.rs
│   │   │   │       │   │   ├── option_spread.rs
│   │   │   │       │   │   ├── perpetual_contract.rs
│   │   │   │       │   │   ├── synthetic.rs
│   │   │   │       │   │   └── tokenized_asset.rs
│   │   │   │       │   ├── macros.rs
│   │   │   │       │   ├── mod.rs
│   │   │   │       │   ├── orderbook
│   │   │   │       │   │   ├── book.rs
│   │   │   │       │   │   ├── level.rs
│   │   │   │       │   │   ├── mod.rs
│   │   │   │       │   │   └── own.rs
│   │   │   │       │   ├── orders
│   │   │   │       │   │   ├── limit_if_touched.rs
│   │   │   │       │   │   ├── limit.rs
│   │   │   │       │   │   ├── list.rs
│   │   │   │       │   │   ├── market_if_touched.rs
│   │   │   │       │   │   ├── market_to_limit.rs
│   │   │   │       │   │   ├── market.rs
│   │   │   │       │   │   ├── mod.rs
│   │   │   │       │   │   ├── stop_limit.rs
│   │   │   │       │   │   ├── stop_market.rs
│   │   │   │       │   │   ├── trailing_stop_limit.rs
│   │   │   │       │   │   └── trailing_stop_market.rs
│   │   │   │       │   ├── position.rs
│   │   │   │       │   ├── reports
│   │   │   │       │   │   ├── fill.rs
│   │   │   │       │   │   ├── mass_status.rs
│   │   │   │       │   │   ├── mod.rs
│   │   │   │       │   │   ├── order.rs
│   │   │   │       │   │   └── position.rs
│   │   │   │       │   └── types
│   │   │   │       │       ├── balance.rs
│   │   │   │       │       ├── currency.rs
│   │   │   │       │       ├── mod.rs
│   │   │   │       │       ├── money.rs
│   │   │   │       │       ├── price.rs
│   │   │   │       │       └── quantity.rs
│   │   │   │       ├── reports
│   │   │   │       │   ├── fill.rs
│   │   │   │       │   ├── mass_status.rs
│   │   │   │       │   ├── mod.rs
│   │   │   │       │   ├── order.rs
│   │   │   │       │   └── position.rs
│   │   │   │       ├── stubs.rs
│   │   │   │       ├── types
│   │   │   │       │   ├── balance.rs
│   │   │   │       │   ├── currency.rs
│   │   │   │       │   ├── fixed.rs
│   │   │   │       │   ├── mod.rs
│   │   │   │       │   ├── money.rs
│   │   │   │       │   ├── price.rs
│   │   │   │       │   ├── quantity.rs
│   │   │   │       │   └── stubs.rs
│   │   │   │       └── venues.rs
│   │   │   ├── network
│   │   │   │   ├── benches
│   │   │   │   │   ├── BENCHMARKS.md
│   │   │   │   │   ├── http_response.rs
│   │   │   │   │   ├── ratelimiter.rs
│   │   │   │   │   ├── test_client.rs
│   │   │   │   │   ├── test_server.rs
│   │   │   │   │   ├── websocket_latency.rs
│   │   │   │   │   └── websocket_transport.rs
│   │   │   │   ├── Cargo.toml
│   │   │   │   ├── LICENSE -> ../../LICENSE
│   │   │   │   ├── proptest-regressions
│   │   │   │   │   ├── backoff.txt
│   │   │   │   │   ├── ratelimiter.txt
│   │   │   │   │   ├── retry.txt
│   │   │   │   │   └── subscription.txt
│   │   │   │   ├── README.md
│   │   │   │   ├── src
│   │   │   │   │   ├── backoff.rs
│   │   │   │   │   ├── dst.rs
│   │   │   │   │   ├── error.rs
│   │   │   │   │   ├── http
│   │   │   │   │   │   ├── client.rs
│   │   │   │   │   │   ├── error.rs
│   │   │   │   │   │   ├── mod.rs
│   │   │   │   │   │   └── types.rs
│   │   │   │   │   ├── lib.rs
│   │   │   │   │   ├── logging.rs
│   │   │   │   │   ├── mode.rs
│   │   │   │   │   ├── net.rs
│   │   │   │   │   ├── python
│   │   │   │   │   │   └── mod.rs
│   │   │   │   │   ├── ratelimiter
│   │   │   │   │   │   ├── clock.rs
│   │   │   │   │   │   ├── gcra.rs
│   │   │   │   │   │   ├── mod.rs
│   │   │   │   │   │   ├── nanos.rs
│   │   │   │   │   │   └── quota.rs
│   │   │   │   │   ├── retry.rs
│   │   │   │   │   ├── sink.rs
│   │   │   │   │   ├── socket
│   │   │   │   │   │   ├── client.rs
│   │   │   │   │   │   ├── config.rs
│   │   │   │   │   │   ├── mod.rs
│   │   │   │   │   │   └── types.rs
│   │   │   │   │   ├── tls.rs
│   │   │   │   │   ├── transport
│   │   │   │   │   │   ├── error.rs
│   │   │   │   │   │   ├── message.rs
│   │   │   │   │   │   ├── mod.rs
│   │   │   │   │   │   ├── sockudo.rs
│   │   │   │   │   │   ├── stream.rs
│   │   │   │   │   │   └── tungstenite.rs
│   │   │   │   │   └── websocket
│   │   │   │   │       ├── auth.rs
│   │   │   │   │       ├── client.rs
│   │   │   │   │       ├── config.rs
│   │   │   │   │       ├── consts.rs
│   │   │   │   │       ├── mod.rs
│   │   │   │   │       ├── proxy.rs
│   │   │   │   │       ├── subscription.rs
│   │   │   │   │       └── types.rs
│   │   │   │   └── tests
│   │   │   │       ├── common
│   │   │   │       │   ├── mod.rs
│   │   │   │       │   └── turmoil.rs
│   │   │   │       ├── property_backoff.rs
│   │   │   │       ├── property_ratelimiter.rs
│   │   │   │       ├── turmoil_socket.rs
│   │   │   │       ├── turmoil_sockudo.rs
│   │   │   │       ├── turmoil_websocket.rs
│   │   │   │       └── websocket_proxy.rs
│   │   │   ├── persistence
│   │   │   │   ├── benches
│   │   │   │   │   └── persistence.rs
│   │   │   │   ├── bin
│   │   │   │   │   ├── to_json.rs
│   │   │   │   │   └── to_parquet.rs
│   │   │   │   ├── Cargo.toml
│   │   │   │   ├── LICENSE -> ../../LICENSE
│   │   │   │   ├── licenses
│   │   │   │   │   ├── MIT-binary-heap-plus.txt
│   │   │   │   │   ├── MIT-compare.txt
│   │   │   │   │   └── THIRD_PARTY_LICENSES.md
│   │   │   │   ├── macros
│   │   │   │   │   ├── Cargo.toml
│   │   │   │   │   └── src
│   │   │   │   │       ├── custom.rs
│   │   │   │   │       └── lib.rs
│   │   │   │   ├── README.md
│   │   │   │   ├── src
│   │   │   │   │   ├── backend
│   │   │   │   │   │   ├── binary_heap.rs
│   │   │   │   │   │   ├── catalog_operations.rs
│   │   │   │   │   │   ├── catalog.rs
│   │   │   │   │   │   ├── compare.rs
│   │   │   │   │   │   ├── custom.rs
│   │   │   │   │   │   ├── feather.rs
│   │   │   │   │   │   ├── kmerge_batch.rs
│   │   │   │   │   │   ├── mod.rs
│   │   │   │   │   │   └── session.rs
│   │   │   │   │   ├── config.rs
│   │   │   │   │   ├── lib.rs
│   │   │   │   │   ├── parquet.rs
│   │   │   │   │   ├── python
│   │   │   │   │   │   ├── backend
│   │   │   │   │   │   │   ├── mod.rs
│   │   │   │   │   │   │   └── session.rs
│   │   │   │   │   │   ├── catalog.rs
│   │   │   │   │   │   ├── feather.rs
│   │   │   │   │   │   ├── mod.rs
│   │   │   │   │   │   └── wranglers
│   │   │   │   │   │       ├── bar.rs
│   │   │   │   │   │       ├── delta.rs
│   │   │   │   │   │       ├── depth.rs
│   │   │   │   │   │       ├── mod.rs
│   │   │   │   │   │       ├── quote.rs
│   │   │   │   │   │       └── trade.rs
│   │   │   │   │   └── test_data.rs
│   │   │   │   └── tests
│   │   │   │       ├── test_catalog.rs
│   │   │   │       ├── test_feather.rs
│   │   │   │       └── test_pinned_data_direct_session.rs
│   │   │   ├── plugin
│   │   │   │   ├── build.rs
│   │   │   │   ├── Cargo.toml
│   │   │   │   ├── LICENSE -> ../../LICENSE
│   │   │   │   ├── README.md
│   │   │   │   └── src
│   │   │   │       ├── boundary.rs
│   │   │   │       ├── host.rs
│   │   │   │       ├── lib.rs
│   │   │   │       ├── macros.rs
│   │   │   │       ├── manifest.rs
│   │   │   │       └── panic.rs
│   │   │   ├── portfolio
│   │   │   │   ├── benches
│   │   │   │   │   └── portfolio.rs
│   │   │   │   ├── Cargo.toml
│   │   │   │   ├── LICENSE -> ../../LICENSE
│   │   │   │   ├── README.md
│   │   │   │   ├── src
│   │   │   │   │   ├── config.rs
│   │   │   │   │   ├── lib.rs
│   │   │   │   │   ├── manager.rs
│   │   │   │   │   ├── portfolio.rs
│   │   │   │   │   └── python
│   │   │   │   │       └── mod.rs
│   │   │   │   └── tests
│   │   │   │       └── portfolio.rs
│   │   │   ├── pyo3
│   │   │   │   ├── bin
│   │   │   │   │   └── stub_gen.rs
│   │   │   │   ├── Cargo.toml
│   │   │   │   ├── LICENSE -> ../../LICENSE
│   │   │   │   ├── README.md
│   │   │   │   └── src
│   │   │   │       └── lib.rs
│   │   │   ├── README.md
│   │   │   ├── risk
│   │   │   │   ├── Cargo.toml
│   │   │   │   ├── LICENSE -> ../../LICENSE
│   │   │   │   ├── README.md
│   │   │   │   ├── src
│   │   │   │   │   ├── engine
│   │   │   │   │   │   ├── config.rs
│   │   │   │   │   │   └── mod.rs
│   │   │   │   │   ├── lib.rs
│   │   │   │   │   ├── python
│   │   │   │   │   │   ├── config.rs
│   │   │   │   │   │   ├── mod.rs
│   │   │   │   │   │   └── sizing.rs
│   │   │   │   │   └── sizing.rs
│   │   │   │   └── tests
│   │   │   │       └── risk_engine.rs
│   │   │   ├── serialization
│   │   │   │   ├── benches
│   │   │   │   │   ├── capnp_serialization.rs
│   │   │   │   │   ├── market_data_capnp_vs_sbe.rs
│   │   │   │   │   ├── sbe_decoding.rs
│   │   │   │   │   └── serialization_comparison.rs
│   │   │   │   ├── build.rs
│   │   │   │   ├── Cargo.toml
│   │   │   │   ├── generated
│   │   │   │   │   └── capnp
│   │   │   │   │       ├── commands
│   │   │   │   │       │   ├── data_capnp.rs
│   │   │   │   │       │   └── trading_capnp.rs
│   │   │   │   │       ├── common
│   │   │   │   │       │   ├── base_capnp.rs
│   │   │   │   │       │   ├── enums_capnp.rs
│   │   │   │   │       │   ├── identifiers_capnp.rs
│   │   │   │   │       │   └── types_capnp.rs
│   │   │   │   │       ├── data
│   │   │   │   │       │   └── market_capnp.rs
│   │   │   │   │       └── events
│   │   │   │   │           ├── account_capnp.rs
│   │   │   │   │           ├── order_capnp.rs
│   │   │   │   │           ├── position_capnp.rs
│   │   │   │   │           └── system_capnp.rs
│   │   │   │   ├── LICENSE -> ../../LICENSE
│   │   │   │   ├── README.md
│   │   │   │   ├── schemas
│   │   │   │   │   └── capnp
│   │   │   │   │       ├── commands
│   │   │   │   │       │   ├── data.capnp
│   │   │   │   │       │   └── trading.capnp
│   │   │   │   │       ├── common
│   │   │   │   │       │   ├── base.capnp
│   │   │   │   │       │   ├── enums.capnp
│   │   │   │   │       │   ├── identifiers.capnp
│   │   │   │   │       │   └── types.capnp
│   │   │   │   │       ├── data
│   │   │   │   │       │   └── market.capnp
│   │   │   │   │       └── events
│   │   │   │   │           ├── account.capnp
│   │   │   │   │           ├── order.capnp
│   │   │   │   │           ├── position.capnp
│   │   │   │   │           └── system.capnp
│   │   │   │   ├── src
│   │   │   │   │   ├── arrow
│   │   │   │   │   │   ├── account_state.rs
│   │   │   │   │   │   ├── bar.rs
│   │   │   │   │   │   ├── close.rs
│   │   │   │   │   │   ├── custom.rs
│   │   │   │   │   │   ├── delta.rs
│   │   │   │   │   │   ├── depth.rs
│   │   │   │   │   │   ├── display
│   │   │   │   │   │   │   ├── account_state.rs
│   │   │   │   │   │   │   ├── bar.rs
│   │   │   │   │   │   │   ├── close.rs
│   │   │   │   │   │   │   ├── delta.rs
│   │   │   │   │   │   │   ├── depth.rs
│   │   │   │   │   │   │   ├── index_price.rs
│   │   │   │   │   │   │   ├── instrument.rs
│   │   │   │   │   │   │   ├── mark_price.rs
│   │   │   │   │   │   │   ├── mod.rs
│   │   │   │   │   │   │   ├── order_filled.rs
│   │   │   │   │   │   │   ├── position.rs
│   │   │   │   │   │   │   ├── quote.rs
│   │   │   │   │   │   │   ├── report.rs
│   │   │   │   │   │   │   └── trade.rs
│   │   │   │   │   │   ├── funding.rs
│   │   │   │   │   │   ├── index_price.rs
│   │   │   │   │   │   ├── instrument
│   │   │   │   │   │   │   ├── betting.rs
│   │   │   │   │   │   │   ├── binary_option.rs
│   │   │   │   │   │   │   ├── cfd.rs
│   │   │   │   │   │   │   ├── commodity.rs
│   │   │   │   │   │   │   ├── crypto_future.rs
│   │   │   │   │   │   │   ├── crypto_futures_spread.rs
│   │   │   │   │   │   │   ├── crypto_option_spread.rs
│   │   │   │   │   │   │   ├── crypto_option.rs
│   │   │   │   │   │   │   ├── crypto_perpetual.rs
│   │   │   │   │   │   │   ├── currency_pair.rs
│   │   │   │   │   │   │   ├── equity.rs
│   │   │   │   │   │   │   ├── futures_contract.rs
│   │   │   │   │   │   │   ├── futures_spread.rs
│   │   │   │   │   │   │   ├── index_instrument.rs
│   │   │   │   │   │   │   ├── mod.rs
│   │   │   │   │   │   │   ├── option_contract.rs
│   │   │   │   │   │   │   ├── option_spread.rs
│   │   │   │   │   │   │   ├── perpetual_contract.rs
│   │   │   │   │   │   │   └── tokenized_asset.rs
│   │   │   │   │   │   ├── instrument_status.rs
│   │   │   │   │   │   ├── json.rs
│   │   │   │   │   │   ├── mark_price.rs
│   │   │   │   │   │   ├── mod.rs
│   │   │   │   │   │   ├── option_greeks.rs
│   │   │   │   │   │   ├── order_event.rs
│   │   │   │   │   │   ├── position_event.rs
│   │   │   │   │   │   ├── quote.rs
│   │   │   │   │   │   ├── report.rs
│   │   │   │   │   │   ├── snapshot.rs
│   │   │   │   │   │   └── trade.rs
│   │   │   │   │   ├── capnp
│   │   │   │   │   │   ├── conversions.rs
│   │   │   │   │   │   └── mod.rs
│   │   │   │   │   ├── lib.rs
│   │   │   │   │   ├── numeric.rs
│   │   │   │   │   ├── python
│   │   │   │   │   │   ├── arrow.rs
│   │   │   │   │   │   └── mod.rs
│   │   │   │   │   └── sbe
│   │   │   │   │       ├── cursor.rs
│   │   │   │   │       ├── error.rs
│   │   │   │   │       ├── market
│   │   │   │   │       │   ├── bars.rs
│   │   │   │   │       │   ├── book.rs
│   │   │   │   │       │   ├── common.rs
│   │   │   │   │       │   ├── data_any.rs
│   │   │   │   │       │   └── ticks.rs
│   │   │   │   │       ├── market.rs
│   │   │   │   │       ├── mod.rs
│   │   │   │   │       ├── primitives.rs
│   │   │   │   │       └── writer.rs
│   │   │   │   └── tests
│   │   │   │       ├── test_enums_capnp.rs
│   │   │   │       ├── test_identifiers_capnp.rs
│   │   │   │       ├── test_market_data_capnp.rs
│   │   │   │       ├── test_market_data_sbe.rs
│   │   │   │       └── test_types_capnp.rs
│   │   │   ├── system
│   │   │   │   ├── Cargo.toml
│   │   │   │   ├── LICENSE -> ../../LICENSE
│   │   │   │   ├── README.md
│   │   │   │   └── src
│   │   │   │       ├── builder.rs
│   │   │   │       ├── clock_factory.rs
│   │   │   │       ├── config.rs
│   │   │   │       ├── controller.rs
│   │   │   │       ├── event_store.rs
│   │   │   │       ├── kernel.rs
│   │   │   │       ├── lib.rs
│   │   │   │       ├── messages
│   │   │   │       │   ├── controller.rs
│   │   │   │       │   └── mod.rs
│   │   │   │       ├── python
│   │   │   │       │   ├── controller.rs
│   │   │   │       │   ├── mod.rs
│   │   │   │       │   └── registry.rs
│   │   │   │       ├── registration.rs
│   │   │   │       └── trader.rs
│   │   │   ├── testkit
│   │   │   │   ├── Cargo.toml
│   │   │   │   ├── LICENSE -> ../../LICENSE
│   │   │   │   ├── README.md
│   │   │   │   ├── src
│   │   │   │   │   ├── cache.rs
│   │   │   │   │   ├── common.rs
│   │   │   │   │   ├── components.rs
│   │   │   │   │   ├── events.rs
│   │   │   │   │   ├── files.rs
│   │   │   │   │   ├── itch
│   │   │   │   │   │   ├── mod.rs
│   │   │   │   │   │   └── parse.rs
│   │   │   │   │   ├── lib.rs
│   │   │   │   │   ├── python
│   │   │   │   │   │   ├── files.rs
│   │   │   │   │   │   ├── mod.rs
│   │   │   │   │   │   └── testers.rs
│   │   │   │   │   └── testers
│   │   │   │   │       ├── data
│   │   │   │   │       │   ├── actor.rs
│   │   │   │   │       │   ├── config.rs
│   │   │   │   │       │   ├── mod.rs
│   │   │   │   │       │   └── tests.rs
│   │   │   │   │       ├── exec
│   │   │   │   │       │   ├── config.rs
│   │   │   │   │       │   ├── mod.rs
│   │   │   │   │       │   ├── strategy.rs
│   │   │   │   │       │   └── tests.rs
│   │   │   │   │       └── mod.rs
│   │   │   │   └── tests
│   │   │   │       ├── common.rs
│   │   │   │       ├── large_data.rs
│   │   │   │       └── orderbook_integration.rs
│   │   │   └── trading
│   │   │       ├── Cargo.toml
│   │   │       ├── LICENSE -> ../../LICENSE
│   │   │       ├── README.md
│   │   │       └── src
│   │   │           ├── algorithm
│   │   │           │   ├── config.rs
│   │   │           │   ├── core.rs
│   │   │           │   ├── mod.rs
│   │   │           │   └── twap.rs
│   │   │           ├── controller.rs
│   │   │           ├── examples
│   │   │           │   ├── actors
│   │   │           │   │   ├── imbalance
│   │   │           │   │   │   ├── actor.rs
│   │   │           │   │   │   ├── config.rs
│   │   │           │   │   │   ├── mod.rs
│   │   │           │   │   │   └── tests.rs
│   │   │           │   │   └── mod.rs
│   │   │           │   ├── mod.rs
│   │   │           │   └── strategies
│   │   │           │       ├── composite_market_maker
│   │   │           │       │   ├── config.rs
│   │   │           │       │   ├── mod.rs
│   │   │           │       │   ├── README.md
│   │   │           │       │   ├── strategy.rs
│   │   │           │       │   └── tests.rs
│   │   │           │       ├── delta_neutral_vol
│   │   │           │       │   ├── config.rs
│   │   │           │       │   ├── mod.rs
│   │   │           │       │   ├── README.md
│   │   │           │       │   ├── strategy.rs
│   │   │           │       │   └── tests.rs
│   │   │           │       ├── ema_cross
│   │   │           │       │   ├── config.rs
│   │   │           │       │   ├── mod.rs
│   │   │           │       │   ├── README.md
│   │   │           │       │   ├── strategy.rs
│   │   │           │       │   └── tests.rs
│   │   │           │       ├── grid_mm
│   │   │           │       │   ├── config.rs
│   │   │           │       │   ├── mod.rs
│   │   │           │       │   ├── README.md
│   │   │           │       │   ├── strategy.rs
│   │   │           │       │   └── tests.rs
│   │   │           │       ├── hurst_vpin_directional
│   │   │           │       │   ├── config.rs
│   │   │           │       │   ├── mod.rs
│   │   │           │       │   ├── README.md
│   │   │           │       │   ├── strategy.rs
│   │   │           │       │   └── tests.rs
│   │   │           │       └── mod.rs
│   │   │           ├── lib.rs
│   │   │           ├── macros.rs
│   │   │           ├── python
│   │   │           │   ├── algorithm.rs
│   │   │           │   ├── controller.rs
│   │   │           │   ├── examples.rs
│   │   │           │   ├── mod.rs
│   │   │           │   ├── sessions.rs
│   │   │           │   └── strategy.rs
│   │   │           ├── sessions.rs
│   │   │           └── strategy
│   │   │               ├── api.rs
│   │   │               ├── config.rs
│   │   │               ├── core.rs
│   │   │               └── mod.rs
│   │   ├── deny.toml
│   │   ├── docs
│   │   │   ├── api_reference
│   │   │   │   ├── _static
│   │   │   │   │   └── custom.css
│   │   │   │   ├── accounting.md
│   │   │   │   ├── adapters
│   │   │   │   │   ├── architect_ax.md
│   │   │   │   │   ├── betfair.md
│   │   │   │   │   ├── binance.md
│   │   │   │   │   ├── bitmex.md
│   │   │   │   │   ├── bybit.md
│   │   │   │   │   ├── databento.md
│   │   │   │   │   ├── deribit.md
│   │   │   │   │   ├── dydx.md
│   │   │   │   │   ├── hyperliquid.md
│   │   │   │   │   ├── index.md
│   │   │   │   │   ├── interactive_brokers.md
│   │   │   │   │   ├── kraken.md
│   │   │   │   │   ├── okx.md
│   │   │   │   │   ├── polymarket.md
│   │   │   │   │   ├── sandbox.md
│   │   │   │   │   └── tardis.md
│   │   │   │   ├── analysis.md
│   │   │   │   ├── backtest.md
│   │   │   │   ├── cache.md
│   │   │   │   ├── common.md
│   │   │   │   ├── conf.py
│   │   │   │   ├── config.md
│   │   │   │   ├── core.md
│   │   │   │   ├── data.md
│   │   │   │   ├── execution.md
│   │   │   │   ├── index.md
│   │   │   │   ├── indicators.md
│   │   │   │   ├── live.md
│   │   │   │   ├── model
│   │   │   │   │   ├── book.md
│   │   │   │   │   ├── data.md
│   │   │   │   │   ├── events.md
│   │   │   │   │   ├── identifiers.md
│   │   │   │   │   ├── index.md
│   │   │   │   │   ├── instruments.md
│   │   │   │   │   ├── objects.md
│   │   │   │   │   ├── orders.md
│   │   │   │   │   ├── position.md
│   │   │   │   │   └── reports.md
│   │   │   │   ├── persistence.md
│   │   │   │   ├── portfolio.md
│   │   │   │   ├── risk.md
│   │   │   │   ├── serialization.md
│   │   │   │   └── trading.md
│   │   │   ├── concepts
│   │   │   │   ├── accounting.md
│   │   │   │   ├── actors.md
│   │   │   │   ├── adapters.md
│   │   │   │   ├── architecture.md
│   │   │   │   ├── backtesting
│   │   │   │   │   ├── accounts-and-margin.md
│   │   │   │   │   ├── apis-and-runs.md
│   │   │   │   │   ├── bar-execution.md
│   │   │   │   │   ├── data-and-venues.md
│   │   │   │   │   ├── execution-flow.md
│   │   │   │   │   ├── fill-models.md
│   │   │   │   │   ├── fill-prices-and-matching.md
│   │   │   │   │   ├── index.md
│   │   │   │   │   └── trade-execution.md
│   │   │   │   ├── cache.md
│   │   │   │   ├── configuration.md
│   │   │   │   ├── continuous_futures.md
│   │   │   │   ├── custom_data.md
│   │   │   │   ├── data
│   │   │   │   │   ├── bar.md
│   │   │   │   │   ├── funding_rate_update.md
│   │   │   │   │   ├── index_price_update.md
│   │   │   │   │   ├── index.md
│   │   │   │   │   ├── instrument_close.md
│   │   │   │   │   ├── instrument_status.md
│   │   │   │   │   ├── mark_price_update.md
│   │   │   │   │   ├── option_greeks.md
│   │   │   │   │   ├── order_book_delta.md
│   │   │   │   │   ├── order_book_deltas.md
│   │   │   │   │   ├── order_book_depth10.md
│   │   │   │   │   ├── quote_tick.md
│   │   │   │   │   └── trade_tick.md
│   │   │   │   ├── dst.md
│   │   │   │   ├── event_sourcing.md
│   │   │   │   ├── events
│   │   │   │   │   ├── account_state.md
│   │   │   │   │   ├── index.md
│   │   │   │   │   ├── order_accepted.md
│   │   │   │   │   ├── order_cancel_rejected.md
│   │   │   │   │   ├── order_canceled.md
│   │   │   │   │   ├── order_denied.md
│   │   │   │   │   ├── order_emulated.md
│   │   │   │   │   ├── order_expired.md
│   │   │   │   │   ├── order_fill_voided.md
│   │   │   │   │   ├── order_filled.md
│   │   │   │   │   ├── order_initialized.md
│   │   │   │   │   ├── order_modify_rejected.md
│   │   │   │   │   ├── order_pending_cancel.md
│   │   │   │   │   ├── order_pending_update.md
│   │   │   │   │   ├── order_rejected.md
│   │   │   │   │   ├── order_released.md
│   │   │   │   │   ├── order_submitted.md
│   │   │   │   │   ├── order_triggered.md
│   │   │   │   │   ├── order_updated.md
│   │   │   │   │   ├── position_changed.md
│   │   │   │   │   ├── position_closed.md
│   │   │   │   │   └── position_opened.md
│   │   │   │   ├── execution.md
│   │   │   │   ├── greeks.md
│   │   │   │   ├── index.md
│   │   │   │   ├── instruments
│   │   │   │   │   ├── betting_instrument.md
│   │   │   │   │   ├── binary_option.md
│   │   │   │   │   ├── cfd.md
│   │   │   │   │   ├── commodity.md
│   │   │   │   │   ├── crypto_future.md
│   │   │   │   │   ├── crypto_futures_spread.md
│   │   │   │   │   ├── crypto_option_spread.md
│   │   │   │   │   ├── crypto_option.md
│   │   │   │   │   ├── crypto_perpetual.md
│   │   │   │   │   ├── currency_pair.md
│   │   │   │   │   ├── equity.md
│   │   │   │   │   ├── futures_contract.md
│   │   │   │   │   ├── futures_spread.md
│   │   │   │   │   ├── index_instrument.md
│   │   │   │   │   ├── index.md
│   │   │   │   │   ├── option_contract.md
│   │   │   │   │   ├── option_spread.md
│   │   │   │   │   ├── perpetual_contract.md
│   │   │   │   │   ├── synthetic_instrument.md
│   │   │   │   │   └── tokenized_asset.md
│   │   │   │   ├── live.md
│   │   │   │   ├── logging.md
│   │   │   │   ├── message_bus.md
│   │   │   │   ├── options.md
│   │   │   │   ├── order_book.md
│   │   │   │   ├── orders
│   │   │   │   │   ├── advanced.md
│   │   │   │   │   ├── emulated.md
│   │   │   │   │   ├── index.md
│   │   │   │   │   ├── limit_if_touched.md
│   │   │   │   │   ├── limit.md
│   │   │   │   │   ├── market_if_touched.md
│   │   │   │   │   ├── market_to_limit.md
│   │   │   │   │   ├── market.md
│   │   │   │   │   ├── stop_limit.md
│   │   │   │   │   ├── stop_market.md
│   │   │   │   │   ├── trailing_stop_limit.md
│   │   │   │   │   └── trailing_stop_market.md
│   │   │   │   ├── overview.md
│   │   │   │   ├── portfolio.md
│   │   │   │   ├── positions.md
│   │   │   │   ├── reconciliation.md
│   │   │   │   ├── reports.md
│   │   │   │   ├── rust.md
│   │   │   │   ├── strategies.md
│   │   │   │   ├── synthetics.md
│   │   │   │   ├── value_types.md
│   │   │   │   └── visualization.md
│   │   │   ├── dev_templates
│   │   │   │   ├── criterion_template.rs
│   │   │   │   └── iai_template.rs
│   │   │   ├── developer_guide
│   │   │   │   ├── adapters.md
│   │   │   │   ├── benchmarking.md
│   │   │   │   ├── coding_standards.md
│   │   │   │   ├── design_principles.md
│   │   │   │   ├── docs.md
│   │   │   │   ├── environment_setup.md
│   │   │   │   ├── ffi.md
│   │   │   │   ├── index.md
│   │   │   │   ├── markdown_style.md
│   │   │   │   ├── plugins.md
│   │   │   │   ├── python.md
│   │   │   │   ├── releases.md
│   │   │   │   ├── rust.md
│   │   │   │   ├── security.md
│   │   │   │   ├── shell.md
│   │   │   │   ├── spec_data_testing.md
│   │   │   │   ├── spec_exec_testing.md
│   │   │   │   ├── test_datasets.md
│   │   │   │   └── testing.md
│   │   │   ├── getting_started
│   │   │   │   ├── backtest_high_level.py
│   │   │   │   ├── backtest_low_level.py
│   │   │   │   ├── index.md
│   │   │   │   ├── installation.md
│   │   │   │   └── quickstart.py
│   │   │   ├── how_to
│   │   │   │   ├── configure_live_trading.md
│   │   │   │   ├── data_catalog_databento.py
│   │   │   │   ├── get_started_lighter.md
│   │   │   │   ├── index.md
│   │   │   │   ├── loading_external_data.py
│   │   │   │   ├── run_rust_backtest.md
│   │   │   │   ├── run_rust_live_trading.md
│   │   │   │   ├── write_rust_actor.md
│   │   │   │   └── write_rust_strategy.md
│   │   │   ├── integrations
│   │   │   │   ├── architect_ax.md
│   │   │   │   ├── betfair.md
│   │   │   │   ├── binance.md
│   │   │   │   ├── bitmex.md
│   │   │   │   ├── blockchain.md
│   │   │   │   ├── bybit.md
│   │   │   │   ├── coinbase.md
│   │   │   │   ├── databento.md
│   │   │   │   ├── deribit.md
│   │   │   │   ├── derive.md
│   │   │   │   ├── dydx.md
│   │   │   │   ├── hyperliquid.md
│   │   │   │   ├── index.md
│   │   │   │   ├── interactive_brokers.md
│   │   │   │   ├── kraken.md
│   │   │   │   ├── lighter.md
│   │   │   │   ├── okx.md
│   │   │   │   ├── polymarket.md
│   │   │   │   └── tardis.md
│   │   │   └── tutorials
│   │   │       ├── assets
│   │   │       │   ├── backtest_book_imbalance_betfair
│   │   │       │   │   ├── panel_a_imbalance_lines.png
│   │   │       │   │   ├── panel_b_batch_distribution.png
│   │   │       │   │   ├── panel_c_cumulative_volume.png
│   │   │       │   │   └── render_panels.py
│   │   │       │   ├── backtest_fx_bars
│   │   │       │   │   ├── panel_a_price_overview.png
│   │   │       │   │   ├── panel_b_zoom.png
│   │   │       │   │   ├── panel_c_pnl_curve.png
│   │   │       │   │   ├── panel_d_distributions.png
│   │   │       │   │   └── render_panels.py
│   │   │       │   ├── backtest_orderbook_binance
│   │   │       │   │   ├── panel_a_top_book.png
│   │   │       │   │   ├── panel_b_imbalance_dist.png
│   │   │       │   │   ├── panel_c_size_landscape.png
│   │   │       │   │   ├── panel_d_position.png
│   │   │       │   │   └── render_panels.py
│   │   │       │   ├── backtest_orderbook_bybit
│   │   │       │   │   ├── panel_a_top_book.png
│   │   │       │   │   ├── panel_b_imbalance_dist.png
│   │   │       │   │   ├── panel_c_size_landscape.png
│   │   │       │   │   ├── panel_d_position.png
│   │   │       │   │   └── render_panels.py
│   │   │       │   ├── delta_neutral_options_bybit
│   │   │       │   │   ├── panel_a_strangle_payoff.png
│   │   │       │   │   ├── panel_b_delta_drift.png
│   │   │       │   │   ├── panel_c_hedge_threshold.png
│   │   │       │   │   ├── panel_d_strike_picker.png
│   │   │       │   │   └── render_panels.py
│   │   │       │   ├── delta_neutral_options_derive
│   │   │       │   │   ├── panel_a_strangle_payoff.png
│   │   │       │   │   ├── panel_b_delta_drift.png
│   │   │       │   │   ├── panel_c_hedge_threshold.png
│   │   │       │   │   ├── panel_d_strike_picker.png
│   │   │       │   │   └── render_panels.py
│   │   │       │   ├── fx_mean_reversion_ax
│   │   │       │   │   ├── panel_a_overview.png
│   │   │       │   │   ├── panel_b_zoom.png
│   │   │       │   │   ├── panel_c_decision_scatter.png
│   │   │       │   │   ├── panel_d_pnl.png
│   │   │       │   │   └── render_panels.py
│   │   │       │   ├── gold_book_imbalance_ax
│   │   │       │   │   ├── panel_a_top_book.png
│   │   │       │   │   ├── panel_b_imbalance_dist.png
│   │   │       │   │   ├── panel_c_size_landscape.png
│   │   │       │   │   ├── panel_d_pnl.png
│   │   │       │   │   └── render_panels.py
│   │   │       │   ├── grid_market_maker_bitmex
│   │   │       │   │   ├── panel_a_grid_overlay.png
│   │   │       │   │   ├── panel_b_requote_rate.png
│   │   │       │   │   ├── panel_c_position.png
│   │   │       │   │   ├── panel_d_deadman_timeline.png
│   │   │       │   │   └── render_panels.py
│   │   │       │   ├── grid_market_maker_dydx
│   │   │       │   │   ├── panel_a_grid_overlay.png
│   │   │       │   │   ├── panel_b_order_lifetime.png
│   │   │       │   │   ├── panel_c_orders_per_cycle.png
│   │   │       │   │   ├── panel_d_short_term_timeline.png
│   │   │       │   │   └── render_panels.py
│   │   │       │   ├── hurst_vpin_kraken
│   │   │       │   │   ├── panel_a_price_regime.png
│   │   │       │   │   ├── panel_b_dashboard.png
│   │   │       │   │   ├── panel_c_decision_scatter.png
│   │   │       │   │   ├── panel_d_vpin_hist.png
│   │   │       │   │   ├── panel_e_hurst_only.png
│   │   │       │   │   └── render_panels.py
│   │   │       │   ├── lighter_rwa_composite_mm
│   │   │       │   │   ├── panel_a_reference_overlay.png
│   │   │       │   │   ├── panel_b_signal_basis.png
│   │   │       │   │   ├── panel_c_inventory_skew.png
│   │   │       │   │   ├── panel_d_session_clock.png
│   │   │       │   │   └── render_panels.py
│   │   │       │   └── options_data_bybit
│   │   │       │       ├── panel_a_delta_vs_strike.png
│   │   │       │       ├── panel_b_iv_smile.png
│   │   │       │       ├── panel_c_underlying_oi.png
│   │   │       │       ├── panel_d_call_spread.png
│   │   │       │       └── render_panels.py
│   │   │       ├── backtest_book_imbalance_betfair.md
│   │   │       ├── backtest_fx_bars.py
│   │   │       ├── backtest_orderbook_binance.py
│   │   │       ├── backtest_orderbook_bybit.py
│   │   │       ├── delta_neutral_options_bybit.md
│   │   │       ├── delta_neutral_options_derive.md
│   │   │       ├── fx_mean_reversion_ax.md
│   │   │       ├── gold_book_imbalance_ax.md
│   │   │       ├── grid_market_maker_bitmex.md
│   │   │       ├── grid_market_maker_dydx.md
│   │   │       ├── hurst_vpin_kraken.md
│   │   │       ├── index.md
│   │   │       ├── lighter_rwa_composite_mm.md
│   │   │       ├── options_data_bybit.md
│   │   │       ├── orderbook_data.py
│   │   │       └── orderbook_imbalance.py
│   │   ├── examples
│   │   │   ├── __init__.py
│   │   │   ├── backtest
│   │   │   │   ├── architect_ax_book_imbalance.py
│   │   │   │   ├── architect_ax_mean_reversion.py
│   │   │   │   ├── betfair_backtest_orderbook_imbalance.py
│   │   │   │   ├── bitmex_grid_market_maker.py
│   │   │   │   ├── crypto_ema_cross_ethusdt_trade_ticks.py
│   │   │   │   ├── crypto_ema_cross_ethusdt_trailing_stop.py
│   │   │   │   ├── crypto_ema_cross_with_binance_provider.py
│   │   │   │   ├── crypto_orderbook_imbalance.py
│   │   │   │   ├── databento_cme_quoter.py
│   │   │   │   ├── databento_ema_cross_long_only_aapl_bars.py
│   │   │   │   ├── databento_ema_cross_long_only_spy_trades.py
│   │   │   │   ├── databento_ema_cross_long_only_tsla_trades.py
│   │   │   │   ├── example_01_load_bars_from_custom_csv
│   │   │   │   │   ├── 6EH4.XCME_1min_bars.csv
│   │   │   │   │   ├── run_example.py
│   │   │   │   │   └── strategy.py
│   │   │   │   ├── example_02_use_clock_timer
│   │   │   │   │   ├── README.md
│   │   │   │   │   ├── run_example.py
│   │   │   │   │   └── strategy.py
│   │   │   │   ├── example_03_bar_aggregation
│   │   │   │   │   ├── README.md
│   │   │   │   │   ├── run_example.py
│   │   │   │   │   └── strategy.py
│   │   │   │   ├── example_04_using_data_catalog
│   │   │   │   │   ├── README.md
│   │   │   │   │   ├── run_example.py
│   │   │   │   │   └── strategy.py
│   │   │   │   ├── example_05_using_portfolio
│   │   │   │   │   ├── README.md
│   │   │   │   │   ├── run_example.py
│   │   │   │   │   └── strategy.py
│   │   │   │   ├── example_06_using_cache
│   │   │   │   │   ├── README.md
│   │   │   │   │   ├── run_example.py
│   │   │   │   │   └── strategy.py
│   │   │   │   ├── example_07_using_indicators
│   │   │   │   │   ├── README.md
│   │   │   │   │   ├── run_example.py
│   │   │   │   │   └── strategy.py
│   │   │   │   ├── example_08_cascaded_indicator
│   │   │   │   │   ├── README.md
│   │   │   │   │   ├── run_example.py
│   │   │   │   │   └── strategy.py
│   │   │   │   ├── example_09_messaging_with_msgbus
│   │   │   │   │   ├── README.md
│   │   │   │   │   ├── run_example.py
│   │   │   │   │   └── strategy.py
│   │   │   │   ├── example_10_messaging_with_actor_data
│   │   │   │   │   ├── README.md
│   │   │   │   │   ├── run_example.py
│   │   │   │   │   └── strategy.py
│   │   │   │   ├── example_11_messaging_with_actor_signals
│   │   │   │   │   ├── README.md
│   │   │   │   │   ├── run_example.py
│   │   │   │   │   └── strategy.py
│   │   │   │   ├── fx_ema_cross_audusd_bars_from_ticks.py
│   │   │   │   ├── fx_ema_cross_audusd_ticks.py
│   │   │   │   ├── fx_ema_cross_bracket_gbpusd_bars_external.py
│   │   │   │   ├── fx_ema_cross_bracket_gbpusd_bars_internal.py
│   │   │   │   ├── fx_market_maker_gbpusd_bars.py
│   │   │   │   ├── liquidation_demo.py
│   │   │   │   ├── model_configs_example.py
│   │   │   │   ├── notebooks
│   │   │   │   │   ├── databento_backtest_with_data_client.py
│   │   │   │   │   ├── databento_download.py
│   │   │   │   │   ├── databento_futures_settlement.py
│   │   │   │   │   ├── databento_option_exercise.py
│   │   │   │   │   ├── databento_option_greeks.py
│   │   │   │   │   ├── databento_test_order_book_deltas.py
│   │   │   │   │   └── databento_test_request_bars.py
│   │   │   │   ├── polymarket_simple_quoter.py
│   │   │   │   ├── synthetic_data_pnl_test.py
│   │   │   │   └── tardis_option_chain.py
│   │   │   ├── live
│   │   │   │   ├── architect_ax
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── ax_book_imbalance.py
│   │   │   │   │   ├── ax_mean_reversion.py
│   │   │   │   │   ├── data_tester.py
│   │   │   │   │   ├── exec_tester.py
│   │   │   │   │   └── strategies.py
│   │   │   │   ├── betfair
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── betfair.py
│   │   │   │   │   ├── data_tester.py
│   │   │   │   │   └── exec_tester.py
│   │   │   │   ├── binance
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── binance_data_tester.py
│   │   │   │   │   ├── binance_futures_demo_exec_tester.py
│   │   │   │   │   ├── binance_futures_testnet_exec_tester.py
│   │   │   │   │   ├── binance_spot_and_futures_market_maker.py
│   │   │   │   │   ├── binance_spot_demo_exec_tester.py
│   │   │   │   │   ├── binance_spot_ema_cross_bracket_algo.py
│   │   │   │   │   ├── binance_spot_exec_tester.py
│   │   │   │   │   ├── binance_spot_testnet_exec_tester.py
│   │   │   │   │   ├── data_tester.py
│   │   │   │   │   └── exec_tester.py
│   │   │   │   ├── bitmex
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── bitmex_data_tester.py
│   │   │   │   │   ├── bitmex_exec_tester.py
│   │   │   │   │   ├── data_tester.py
│   │   │   │   │   └── exec_tester.py
│   │   │   │   ├── blockchain
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── actors.py
│   │   │   │   │   ├── data_tester.py
│   │   │   │   │   ├── node_test_factory.py
│   │   │   │   │   └── node_test.py
│   │   │   │   ├── bybit
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── bybit_data_tester.py
│   │   │   │   │   ├── bybit_ema_cross_bracket_algo.py
│   │   │   │   │   ├── bybit_ema_cross_stop_entry.py
│   │   │   │   │   ├── bybit_ema_cross_with_trailing_stop.py
│   │   │   │   │   ├── bybit_ema_cross.py
│   │   │   │   │   ├── bybit_exec_tester.py
│   │   │   │   │   ├── bybit_option_chain.py
│   │   │   │   │   ├── bybit_option_greeks.py
│   │   │   │   │   ├── bybit_options_data_collector.py
│   │   │   │   │   ├── bybit_request_custom_endpoint.py
│   │   │   │   │   ├── data_tester.py
│   │   │   │   │   ├── exec_tester.py
│   │   │   │   │   └── README_options_data_collector.md
│   │   │   │   ├── coinbase
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── data_tester.py
│   │   │   │   │   └── exec_tester.py
│   │   │   │   ├── databento
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── data_tester.py
│   │   │   │   │   ├── databento_data_tester.py
│   │   │   │   │   └── notebooks
│   │   │   │   │       └── databento_historical_data.py
│   │   │   │   ├── deribit
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── data_tester.py
│   │   │   │   │   ├── deribit_data_tester.py
│   │   │   │   │   ├── deribit_exec_tester.py
│   │   │   │   │   ├── deribit_option_chain.py
│   │   │   │   │   ├── deribit_option_greeks.py
│   │   │   │   │   └── exec_tester.py
│   │   │   │   ├── derive
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── data_tester.py
│   │   │   │   │   └── exec_tester.py
│   │   │   │   ├── dydx
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── data_tester.py
│   │   │   │   │   ├── dydx_data_tester.py
│   │   │   │   │   ├── dydx_exec_tester.py
│   │   │   │   │   ├── dydx_market_maker.py
│   │   │   │   │   └── exec_tester.py
│   │   │   │   ├── hyperliquid
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── data_tester.py
│   │   │   │   │   ├── exec_tester.py
│   │   │   │   │   ├── hyperliquid_data_tester.py
│   │   │   │   │   ├── hyperliquid_exec_tester.py
│   │   │   │   │   └── hyperliquid_outcomes_exec_tester.py
│   │   │   │   ├── interactive_brokers
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── _common.py
│   │   │   │   │   ├── connect_with_dockerized_gateway.py
│   │   │   │   │   ├── connect_with_tws.py
│   │   │   │   │   ├── contract_download.py
│   │   │   │   │   ├── data_tester.py
│   │   │   │   │   ├── exec_tester.py
│   │   │   │   │   ├── historical_download.py
│   │   │   │   │   ├── ib_v2_order_strategies.py
│   │   │   │   │   ├── notebooks
│   │   │   │   │   │   ├── bracket_order_example.py
│   │   │   │   │   │   ├── market_order_example.py
│   │   │   │   │   │   ├── oca_group_example.py
│   │   │   │   │   │   ├── order_example_driver.py
│   │   │   │   │   │   ├── reconciliation_example.py
│   │   │   │   │   │   ├── simple_conditions_example.py
│   │   │   │   │   │   ├── spread_example.py
│   │   │   │   │   │   └── with_databento_instrument_id_example.py
│   │   │   │   │   ├── option_greeks.py
│   │   │   │   │   └── with_databento_client.py
│   │   │   │   ├── kraken
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── data_tester.py
│   │   │   │   │   ├── exec_tester.py
│   │   │   │   │   ├── kraken_data_tester.py
│   │   │   │   │   └── kraken_exec_tester.py
│   │   │   │   ├── lighter
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── data_tester.py
│   │   │   │   │   ├── exec_tester.py
│   │   │   │   │   └── nvda_composite_mm.py
│   │   │   │   ├── okx
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── data_tester.py
│   │   │   │   │   ├── exec_tester.py
│   │   │   │   │   ├── okx_data_tester.py
│   │   │   │   │   ├── okx_exec_tester.py
│   │   │   │   │   ├── okx_option_greeks.py
│   │   │   │   │   └── okx_spot_swap_quoter.py
│   │   │   │   ├── polymarket
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── data_tester.py
│   │   │   │   │   ├── exec_tester.py
│   │   │   │   │   └── updown_smoke_tester.py
│   │   │   │   ├── sandbox
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   └── exec_tester.py
│   │   │   │   └── tardis
│   │   │   │       ├── __init__.py
│   │   │   │       ├── data_tester.py
│   │   │   │       └── tardis_data_tester.py
│   │   │   ├── other
│   │   │   │   ├── debugging
│   │   │   │   │   └── debug_mixed_jupyter.ipynb
│   │   │   │   ├── minimal_reproducible_example
│   │   │   │   │   ├── README.md
│   │   │   │   │   ├── run_example.py
│   │   │   │   │   └── strategy.py
│   │   │   │   └── state_machine
│   │   │   │       ├── README.md
│   │   │   │       └── run_example.py
│   │   │   ├── quickstarts
│   │   │   │   └── lighter-rust-data-client
│   │   │   │       ├── Cargo.toml
│   │   │   │       ├── README.md
│   │   │   │       └── src
│   │   │   │           └── main.rs
│   │   │   ├── README.md
│   │   │   ├── sandbox
│   │   │   │   ├── betfair_sandbox.py
│   │   │   │   ├── binance_futures_testnet_sandbox.py
│   │   │   │   ├── binance_spot_futures_sandbox.py
│   │   │   │   ├── bybit_sandbox.py
│   │   │   │   ├── databento_cme_sandbox.py
│   │   │   │   ├── dydx_sandbox.py
│   │   │   │   ├── hyperliquid_testnet_sandbox.py
│   │   │   │   └── interactive_brokers_sandbox.py
│   │   │   ├── tutorials
│   │   │   │   ├── Cargo.toml
│   │   │   │   └── src
│   │   │   │       └── bin
│   │   │   │           └── lighter_nvda_composite_mm.rs
│   │   │   └── utils
│   │   │       ├── __init__.py
│   │   │       └── data_provider.py
│   │   ├── hawk.toml
│   │   ├── LICENSE
│   │   ├── Makefile
│   │   ├── MIGRATION_V2.md
│   │   ├── osv-scanner.toml
│   │   ├── patches
│   │   │   ├── pyo3-stub-gen
│   │   │   │   ├── Cargo.toml
│   │   │   │   ├── LICENSE-APACHE
│   │   │   │   ├── LICENSE-MIT
│   │   │   │   ├── README.md
│   │   │   │   └── src
│   │   │   │       ├── docgen
│   │   │   │       │   ├── builder.rs
│   │   │   │       │   ├── config.rs
│   │   │   │       │   ├── default_parser.rs
│   │   │   │       │   ├── export.rs
│   │   │   │       │   ├── ir.rs
│   │   │   │       │   ├── link.rs
│   │   │   │       │   ├── mod.rs
│   │   │   │       │   ├── render.rs
│   │   │   │       │   ├── sphinx_ext.py
│   │   │   │       │   ├── types.rs
│   │   │   │       │   └── util.rs
│   │   │   │       ├── exception.rs
│   │   │   │       ├── generate
│   │   │   │       │   ├── class.rs
│   │   │   │       │   ├── deprecated.rs
│   │   │   │       │   ├── docstring.rs
│   │   │   │       │   ├── enum_.rs
│   │   │   │       │   ├── function.rs
│   │   │   │       │   ├── member.rs
│   │   │   │       │   ├── method.rs
│   │   │   │       │   ├── module.rs
│   │   │   │       │   ├── parameters.rs
│   │   │   │       │   ├── qualifier.rs
│   │   │   │       │   ├── stub_info.rs
│   │   │   │       │   ├── type_alias.rs
│   │   │   │       │   ├── variable.rs
│   │   │   │       │   └── variant_methods.rs
│   │   │   │       ├── generate.rs
│   │   │   │       ├── lib.rs
│   │   │   │       ├── pyproject.rs
│   │   │   │       ├── rule_name.rs
│   │   │   │       ├── stub_type
│   │   │   │       │   ├── builtins.rs
│   │   │   │       │   ├── collections.rs
│   │   │   │       │   ├── either.rs
│   │   │   │       │   ├── numpy.rs
│   │   │   │       │   ├── pyo3.rs
│   │   │   │       │   └── rust_decimal.rs
│   │   │   │       ├── stub_type.rs
│   │   │   │       ├── type_info.rs
│   │   │   │       └── util.rs
│   │   │   └── README.md
│   │   ├── python
│   │   │   ├── generate_docstrings.py
│   │   │   ├── generate_stubs.py
│   │   │   ├── nautilus_trader
│   │   │   │   ├── __init__.py
│   │   │   │   ├── __init__.pyi
│   │   │   │   ├── _fixup.py
│   │   │   │   ├── _libnautilus
│   │   │   │   │   └── __init__.pyi
│   │   │   │   ├── adapters
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── __init__.pyi
│   │   │   │   │   ├── architect_ax
│   │   │   │   │   │   ├── __init__.py
│   │   │   │   │   │   └── __init__.pyi
│   │   │   │   │   ├── betfair
│   │   │   │   │   │   ├── __init__.py
│   │   │   │   │   │   └── __init__.pyi
│   │   │   │   │   ├── binance
│   │   │   │   │   │   ├── __init__.py
│   │   │   │   │   │   ├── __init__.pyi
│   │   │   │   │   │   └── instruments.py
│   │   │   │   │   ├── bitmex
│   │   │   │   │   │   ├── __init__.py
│   │   │   │   │   │   └── __init__.pyi
│   │   │   │   │   ├── blockchain
│   │   │   │   │   │   ├── __init__.py
│   │   │   │   │   │   └── __init__.pyi
│   │   │   │   │   ├── bybit
│   │   │   │   │   │   ├── __init__.py
│   │   │   │   │   │   └── __init__.pyi
│   │   │   │   │   ├── coinbase
│   │   │   │   │   │   ├── __init__.py
│   │   │   │   │   │   └── __init__.pyi
│   │   │   │   │   ├── databento
│   │   │   │   │   │   ├── __init__.py
│   │   │   │   │   │   └── __init__.pyi
│   │   │   │   │   ├── deribit
│   │   │   │   │   │   ├── __init__.py
│   │   │   │   │   │   └── __init__.pyi
│   │   │   │   │   ├── derive
│   │   │   │   │   │   ├── __init__.py
│   │   │   │   │   │   └── __init__.pyi
│   │   │   │   │   ├── dydx
│   │   │   │   │   │   ├── __init__.py
│   │   │   │   │   │   └── __init__.pyi
│   │   │   │   │   ├── hyperliquid
│   │   │   │   │   │   ├── __init__.py
│   │   │   │   │   │   └── __init__.pyi
│   │   │   │   │   ├── interactive_brokers
│   │   │   │   │   │   ├── __init__.py
│   │   │   │   │   │   └── __init__.pyi
│   │   │   │   │   ├── kraken
│   │   │   │   │   │   ├── __init__.py
│   │   │   │   │   │   └── __init__.pyi
│   │   │   │   │   ├── lighter
│   │   │   │   │   │   ├── __init__.py
│   │   │   │   │   │   └── __init__.pyi
│   │   │   │   │   ├── okx
│   │   │   │   │   │   ├── __init__.py
│   │   │   │   │   │   └── __init__.pyi
│   │   │   │   │   ├── polymarket
│   │   │   │   │   │   ├── __init__.py
│   │   │   │   │   │   └── __init__.pyi
│   │   │   │   │   ├── sandbox
│   │   │   │   │   │   ├── __init__.py
│   │   │   │   │   │   └── __init__.pyi
│   │   │   │   │   └── tardis
│   │   │   │   │       ├── __init__.py
│   │   │   │   │       └── __init__.pyi
│   │   │   │   ├── analysis
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── __init__.pyi
│   │   │   │   │   ├── config.py
│   │   │   │   │   ├── reporter.py
│   │   │   │   │   ├── tearsheet.py
│   │   │   │   │   └── themes.py
│   │   │   │   ├── backtest
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   └── __init__.pyi
│   │   │   │   ├── common
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   └── __init__.pyi
│   │   │   │   ├── config
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   └── __init__.pyi
│   │   │   │   ├── core
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── __init__.pyi
│   │   │   │   │   └── datetime.py
│   │   │   │   ├── cryptography
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   └── __init__.pyi
│   │   │   │   ├── data
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   └── __init__.pyi
│   │   │   │   ├── execution
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   └── __init__.pyi
│   │   │   │   ├── indicators
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   └── __init__.pyi
│   │   │   │   ├── infrastructure
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   └── __init__.pyi
│   │   │   │   ├── live
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   └── __init__.pyi
│   │   │   │   ├── model
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   └── __init__.pyi
│   │   │   │   ├── network
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   └── __init__.pyi
│   │   │   │   ├── persistence
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── __init__.pyi
│   │   │   │   │   └── loaders.py
│   │   │   │   ├── portfolio
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   └── __init__.pyi
│   │   │   │   ├── py.typed
│   │   │   │   ├── risk
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   └── __init__.pyi
│   │   │   │   ├── serialization
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   └── __init__.pyi
│   │   │   │   ├── testkit
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── __init__.pyi
│   │   │   │   │   └── providers.py
│   │   │   │   └── trading
│   │   │   │       ├── __init__.py
│   │   │   │       └── __init__.pyi
│   │   │   ├── pyproject.toml
│   │   │   ├── README.md
│   │   │   ├── tests
│   │   │   │   ├── __init__.py
│   │   │   │   ├── acceptance
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── test_backtest.py
│   │   │   │   │   └── test_blackbox.py
│   │   │   │   ├── conftest.py
│   │   │   │   ├── integration
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   └── test_live_node_cache.py
│   │   │   │   ├── providers.py
│   │   │   │   ├── strategies
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── acceptance.py
│   │   │   │   │   ├── backtest_surface.py
│   │   │   │   │   ├── ema_cross_twap.py
│   │   │   │   │   └── ema_cross.py
│   │   │   │   ├── stubs.py
│   │   │   │   └── unit
│   │   │   │       ├── __init__.py
│   │   │   │       ├── adapters
│   │   │   │       │   ├── architect_ax
│   │   │   │       │   │   └── test_architect_ax_factories.py
│   │   │   │       │   ├── betfair
│   │   │   │       │   │   └── test_betfair_factories.py
│   │   │   │       │   ├── binance
│   │   │   │       │   │   ├── test_binance_factories.py
│   │   │   │       │   │   └── test_binance_migration.py
│   │   │   │       │   ├── bitmex
│   │   │   │       │   │   └── test_bitmex_factories.py
│   │   │   │       │   ├── blockchain
│   │   │   │       │   │   └── test_blockchain_factories.py
│   │   │   │       │   ├── bybit
│   │   │   │       │   │   ├── test_bybit_factories.py
│   │   │   │       │   │   └── test_bybit_parsing.py
│   │   │   │       │   ├── coinbase
│   │   │   │       │   │   └── test_factories.py
│   │   │   │       │   ├── databento
│   │   │   │       │   │   ├── test_databento_factories.py
│   │   │   │       │   │   └── test_databento_types.py
│   │   │   │       │   ├── deribit
│   │   │   │       │   │   └── test_deribit_factories.py
│   │   │   │       │   ├── derive
│   │   │   │       │   │   └── test_derive_factories.py
│   │   │   │       │   ├── dydx
│   │   │   │       │   │   └── test_dydx_factories.py
│   │   │   │       │   ├── example_modules.py
│   │   │   │       │   ├── hyperliquid
│   │   │   │       │   │   └── test_hyperliquid_factories.py
│   │   │   │       │   ├── interactive_brokers
│   │   │   │       │   │   └── test_interactive_brokers_factories.py
│   │   │   │       │   ├── kraken
│   │   │   │       │   │   └── test_kraken_factories.py
│   │   │   │       │   ├── lighter
│   │   │   │       │   │   └── test_lighter_factories.py
│   │   │   │       │   ├── okx
│   │   │   │       │   │   ├── test_okx_factories.py
│   │   │   │       │   │   ├── test_okx_urls.py
│   │   │   │       │   │   └── test_v1_spreads.py
│   │   │   │       │   ├── polymarket
│   │   │   │       │   │   ├── test_polymarket_factories.py
│   │   │   │       │   │   └── test_polymarket_loader.py
│   │   │   │       │   ├── sandbox
│   │   │   │       │   │   └── test_sandbox_factories.py
│   │   │   │       │   ├── tardis
│   │   │   │       │   │   └── test_tardis_factories.py
│   │   │   │       │   └── test_public_exports.py
│   │   │   │       ├── analysis
│   │   │   │       │   ├── __init__.py
│   │   │   │       │   ├── test_analysis.py
│   │   │   │       │   ├── test_reporter.py
│   │   │   │       │   └── test_tearsheet.py
│   │   │   │       ├── backtest
│   │   │   │       │   ├── __init__.py
│   │   │   │       │   ├── test_backtest_configs.py
│   │   │   │       │   ├── test_backtest_engine_custom_data.py
│   │   │   │       │   ├── test_backtest_engine_defi.py
│   │   │   │       │   ├── test_backtest_engine_exec_algorithms.py
│   │   │   │       │   ├── test_backtest_engine_statistics.py
│   │   │   │       │   ├── test_backtest_engine_surface.py
│   │   │   │       │   ├── test_backtest_node.py
│   │   │   │       │   ├── test_bar_aggregation.py
│   │   │   │       │   └── test_tardis_option_chain_example.py
│   │   │   │       ├── common
│   │   │   │       │   ├── __init__.py
│   │   │   │       │   ├── actor.py
│   │   │   │       │   ├── test_actor.py
│   │   │   │       │   ├── test_cache.py
│   │   │   │       │   ├── test_clock.py
│   │   │   │       │   ├── test_configs.py
│   │   │   │       │   ├── test_logging.py
│   │   │   │       │   ├── test_order_factory.py
│   │   │   │       │   └── test_runtime.py
│   │   │   │       ├── core
│   │   │   │       │   ├── __init__.py
│   │   │   │       │   ├── test_time.py
│   │   │   │       │   ├── test_utils.py
│   │   │   │       │   └── test_uuid.py
│   │   │   │       ├── data
│   │   │   │       │   ├── __init__.py
│   │   │   │       │   └── test_data_configs.py
│   │   │   │       ├── execution
│   │   │   │       │   ├── __init__.py
│   │   │   │       │   ├── test_execution_configs.py
│   │   │   │       │   └── test_models.py
│   │   │   │       ├── indicators
│   │   │   │       │   ├── __init__.py
│   │   │   │       │   ├── test_aroon.py
│   │   │   │       │   ├── test_atr.py
│   │   │   │       │   ├── test_dema.py
│   │   │   │       │   ├── test_efficiency_ratio.py
│   │   │   │       │   ├── test_ema.py
│   │   │   │       │   ├── test_hma.py
│   │   │   │       │   ├── test_imbalance.py
│   │   │   │       │   ├── test_inspection.py
│   │   │   │       │   ├── test_python_handlers.py
│   │   │   │       │   ├── test_rma.py
│   │   │   │       │   ├── test_rsi.py
│   │   │   │       │   ├── test_sma.py
│   │   │   │       │   └── test_vwap.py
│   │   │   │       ├── infrastructure
│   │   │   │       │   ├── __init__.py
│   │   │   │       │   └── test_configs.py
│   │   │   │       ├── live
│   │   │   │       │   ├── __init__.py
│   │   │   │       │   └── test_live_configs.py
│   │   │   │       ├── model
│   │   │   │       │   ├── factories.py
│   │   │   │       │   ├── test_accounts.py
│   │   │   │       │   ├── test_balance.py
│   │   │   │       │   ├── test_bar.py
│   │   │   │       │   ├── test_betting.py
│   │   │   │       │   ├── test_binary_market_book_view.py
│   │   │   │       │   ├── test_book.py
│   │   │   │       │   ├── test_currency.py
│   │   │   │       │   ├── test_data.py
│   │   │   │       │   ├── test_defi.py
│   │   │   │       │   ├── test_enums.py
│   │   │   │       │   ├── test_events.py
│   │   │   │       │   ├── test_funding.py
│   │   │   │       │   ├── test_identifiers.py
│   │   │   │       │   ├── test_index_price.py
│   │   │   │       │   ├── test_instruments.py
│   │   │   │       │   ├── test_mark_price.py
│   │   │   │       │   ├── test_money.py
│   │   │   │       │   ├── test_orders.py
│   │   │   │       │   ├── test_own_order_book.py
│   │   │   │       │   ├── test_position.py
│   │   │   │       │   ├── test_price.py
│   │   │   │       │   ├── test_prices.py
│   │   │   │       │   ├── test_pricing.py
│   │   │   │       │   ├── test_quantity.py
│   │   │   │       │   ├── test_quote.py
│   │   │   │       │   ├── test_reports.py
│   │   │   │       │   ├── test_status.py
│   │   │   │       │   ├── test_synthetic.py
│   │   │   │       │   └── test_trade.py
│   │   │   │       ├── network
│   │   │   │       │   ├── __init__.py
│   │   │   │       │   └── test_configs.py
│   │   │   │       ├── persistence
│   │   │   │       │   ├── __init__.py
│   │   │   │       │   ├── test_custom_data.py
│   │   │   │       │   ├── test_option_greeks_replay.py
│   │   │   │       │   └── test_persistence.py
│   │   │   │       ├── portfolio
│   │   │   │       │   ├── __init__.py
│   │   │   │       │   └── test_portfolio.py
│   │   │   │       ├── risk
│   │   │   │       │   ├── __init__.py
│   │   │   │       │   ├── test_risk_configs.py
│   │   │   │       │   └── test_sizing.py
│   │   │   │       ├── serialization
│   │   │   │       │   ├── __init__.py
│   │   │   │       │   └── test_arrow.py
│   │   │   │       ├── test_config.py
│   │   │   │       ├── test_generate_docstrings.py
│   │   │   │       ├── test_generate_stubs.py
│   │   │   │       ├── test_live_node.py
│   │   │   │       ├── test_macos_extension.py
│   │   │   │       ├── test_msgbus.py
│   │   │   │       ├── test_public_module_names.py
│   │   │   │       ├── testkit
│   │   │   │       │   ├── test_providers.py
│   │   │   │       │   └── test_tester_configs.py
│   │   │   │       └── trading
│   │   │   │           ├── __init__.py
│   │   │   │           ├── test_example_configs.py
│   │   │   │           └── test_trading.py
│   │   │   └── uv.lock
│   │   ├── README.md
│   │   ├── RELEASES.md
│   │   ├── ROADMAP.md
│   │   ├── rust-toolchain.toml
│   │   ├── rustfmt.toml
│   │   ├── schema
│   │   │   └── sql
│   │   │       ├── functions.sql
│   │   │       ├── partitions.sql
│   │   │       ├── tables.sql
│   │   │       └── types.sql
│   │   ├── scripts
│   │   │   ├── cargo-tool-version.sh
│   │   │   ├── check-cargo-cooldown.sh
│   │   │   ├── check-markdown-tables.py
│   │   │   ├── check-no-build-packages.sh
│   │   │   ├── check-outdated.sh
│   │   │   ├── ci
│   │   │   │   ├── build-sdist-release-asset.bash
│   │   │   │   ├── check_commit_message.py
│   │   │   │   ├── check-crates-io-trusted-publishing.sh
│   │   │   │   ├── check-docker-toolchain-pins.bash
│   │   │   │   ├── check-generated-drift.bash
│   │   │   │   ├── check-github-action-shas.sh
│   │   │   │   ├── check-miri-toolchain.bash
│   │   │   │   ├── check-rekor-ready.bash
│   │   │   │   ├── check-security-audit-result.sh
│   │   │   │   ├── check-security-gate-result.bash
│   │   │   │   ├── check-workspace-test-coverage.sh
│   │   │   │   ├── configure-linux-swap.bash
│   │   │   │   ├── cosign-sign-retry.bash
│   │   │   │   ├── docker-pull-retry.sh
│   │   │   │   ├── free-disk-space.sh
│   │   │   │   ├── install-cargo-nextest.sh
│   │   │   │   ├── install-nautilus-cli.sh
│   │   │   │   ├── install-prek.sh
│   │   │   │   ├── install-rust.sh
│   │   │   │   ├── osv-severity-gate.sh
│   │   │   │   ├── plan-wheel-publication.bash
│   │   │   │   ├── plan.sh
│   │   │   │   ├── preload-buildx-base-image-retry.sh
│   │   │   │   ├── prepare-release-attestation-siblings.bash
│   │   │   │   ├── publish-cargo-crates.sh
│   │   │   │   ├── publish-cli-r2-prune.sh
│   │   │   │   ├── publish-cli-r2-upload-installer.sh
│   │   │   │   ├── publish-cli-r2-upload.sh
│   │   │   │   ├── publish-cli-r2-verify.sh
│   │   │   │   ├── publish-github-release.bash
│   │   │   │   ├── publish-pypi-trusted.bash
│   │   │   │   ├── publish-release-checksums.sh
│   │   │   │   ├── publish-wheels-delete-artifacts.sh
│   │   │   │   ├── publish-wheels-generate-index.sh
│   │   │   │   ├── publish-wheels-policy.bash
│   │   │   │   ├── publish-wheels-r2-remove-old-wheels.sh
│   │   │   │   ├── publish-wheels-r2-upload-index.sh
│   │   │   │   ├── publish-wheels-r2-upload-new-wheels.sh
│   │   │   │   ├── publish-wheels-r2-verify-files.sh
│   │   │   │   ├── publish-wheels-r2.bash
│   │   │   │   ├── publish-wheels-sha256.bash
│   │   │   │   ├── release-verification-retry.bash
│   │   │   │   ├── release-version-policy.bash
│   │   │   │   ├── report-disk-space.bash
│   │   │   │   ├── security-audit-gate.sh
│   │   │   │   ├── set-cargo-build-jobs.sh
│   │   │   │   ├── sign-pypi-attestations.bash
│   │   │   │   ├── test_check_commit_message.py
│   │   │   │   ├── test-check-docker-toolchain-pins.bash
│   │   │   │   ├── test-check-miri-toolchain.bash
│   │   │   │   ├── test-check-workspace-test-coverage.bash
│   │   │   │   ├── test-github-action-shas.bash
│   │   │   │   ├── test-plan.bash
│   │   │   │   ├── test-postgres-bootstrap.bash
│   │   │   │   ├── test-publish-cargo-crates-check.bash
│   │   │   │   ├── test-publish-cli-r2-upload-installer.bash
│   │   │   │   ├── test-publish-wheels.bash
│   │   │   │   ├── test-python-doctests.bash
│   │   │   │   ├── test-python-types.bash
│   │   │   │   ├── test-release-github-assets.bash
│   │   │   │   ├── test-release-verification-retry.bash
│   │   │   │   ├── test-rust-toolchain.bash
│   │   │   │   ├── test-verify-published-registries-crates.bash
│   │   │   │   ├── test-wheel.bash
│   │   │   │   ├── update-pyproject-version.sh
│   │   │   │   ├── upload-github-release-assets.bash
│   │   │   │   ├── upload-release-attestation-siblings.bash
│   │   │   │   ├── validate-wheel-artifacts.bash
│   │   │   │   ├── verify-ci-inputs.sh
│   │   │   │   ├── verify-docker-image-attestations.bash
│   │   │   │   ├── verify-gh-attestations.bash
│   │   │   │   ├── verify-github-release-assets.bash
│   │   │   │   ├── verify-github-release-attestation.bash
│   │   │   │   └── verify-published-registries.bash
│   │   │   ├── cli
│   │   │   │   └── install.sh
│   │   │   ├── clippy-changed.sh
│   │   │   ├── crate-test-features.sh
│   │   │   ├── curate-dataset.sh
│   │   │   ├── doc-changed.sh
│   │   │   ├── find-replace.sh
│   │   │   ├── fuzz-adapter.sh
│   │   │   ├── install-capnp.sh
│   │   │   ├── install-osv-scanner.sh
│   │   │   ├── maturin-version.bash
│   │   │   ├── package-version.sh
│   │   │   ├── purge-orphan-dev-wheels.sh
│   │   │   ├── README.md
│   │   │   ├── regen-capnp.sh
│   │   │   ├── rust-toolchain.sh
│   │   │   ├── soak-network-turmoil.sh
│   │   │   ├── tool-version.sh
│   │   │   └── uv-version.sh
│   │   ├── SECURITY.md
│   │   ├── test_data
│   │   │   ├── ADABTC-1m-2021-11-27.csv
│   │   │   ├── ADABTC-1m-2021-11-28.csv
│   │   │   ├── betfair
│   │   │   │   ├── 1-166564490.bz2
│   │   │   │   ├── 1-166811431.bz2
│   │   │   │   ├── 1-180305278.bz2
│   │   │   │   ├── 1-206064380.bz2
│   │   │   │   ├── badly_formatted.txt
│   │   │   │   ├── betfair_match_odds
│   │   │   │   │   ├── manifest.json
│   │   │   │   │   ├── metadata.json
│   │   │   │   │   └── README.md
│   │   │   │   └── betfair_racing_win
│   │   │   │       ├── manifest.json
│   │   │   │       ├── metadata.json
│   │   │   │       └── README.md
│   │   │   ├── binance
│   │   │   │   ├── btcusdt-depth-snap.csv
│   │   │   │   ├── btcusdt-depth-update.csv
│   │   │   │   ├── btcusdt-instrument-repr.txt
│   │   │   │   ├── btcusdt-instrument.txt
│   │   │   │   ├── btcusdt-quotes.parquet
│   │   │   │   ├── btcusdt-trades.parquet
│   │   │   │   └── ethusdt-trades.csv
│   │   │   ├── btc-perp-20211231-20220201_1m.csv
│   │   │   ├── bybit
│   │   │   │   └── xrpusdt-ob500.data.zip
│   │   │   ├── crypto_instruments.json
│   │   │   ├── databento
│   │   │   │   ├── definition-glbx-es-fut.dbn.zst
│   │   │   │   ├── definition-glbx-es-futspread.dbn.zst
│   │   │   │   ├── definition-glbx-es-opt.dbn.zst
│   │   │   │   ├── definition-opra.dbn.zst
│   │   │   │   ├── esh4-glbx-mdp3-20231224.mbo.dbn.zst
│   │   │   │   ├── esh4-glbx-mdp3-20231225.mbo.dbn.zst
│   │   │   │   ├── esh4-glbx-mdp3-20231225.mbo.json
│   │   │   │   ├── futures_settlement
│   │   │   │   │   └── databento
│   │   │   │   │       ├── futures_settlement_bbo-1m_2025-12-19T14-25-00_2025-12-19T14-35-00.dbn.zst
│   │   │   │   │       └── futures_settlement_definition.dbn.zst
│   │   │   │   ├── historical_bars_catalog
│   │   │   │   │   └── databento
│   │   │   │   │       ├── futures_definition.dbn.zst
│   │   │   │   │       ├── futures_mbp-1_2024-07-01T23-58_2024-07-02T00-02.dbn.zst
│   │   │   │   │       ├── futures_ohlcv-1m_2024-07-01T23-40_2024-07-02T00-10.dbn.zst
│   │   │   │   │       └── futures_trades_2024-07-01T23-58_2024-07-02T00-02.dbn.zst
│   │   │   │   ├── options_catalog
│   │   │   │   │   ├── databento
│   │   │   │   │   │   ├── futures_bbo-1m_2024-05-09T09-55_2024-05-09T10-05.dbn.zst
│   │   │   │   │   │   ├── futures_definition.dbn.zst
│   │   │   │   │   │   ├── futures_ohlcv-1m_2024-05-09T09-55_2024-05-09T10-05.dbn.zst
│   │   │   │   │   │   ├── options_bbo-1m_2024-05-09T09-55_2024-05-09T10-05.dbn.zst
│   │   │   │   │   │   └── options_definition.dbn.zst
│   │   │   │   │   └── usd_short_term_rate.xml
│   │   │   │   ├── options_exercise
│   │   │   │   │   └── databento
│   │   │   │   │       ├── futures_definition.dbn.zst
│   │   │   │   │       ├── futures_ohlcv-1m_2026-01-09T20-55_2026-01-09T21-05.dbn.zst
│   │   │   │   │       ├── options_bbo-1m_2026-01-09T20-55_2026-01-09T21-05.dbn.zst
│   │   │   │   │       └── options_definition.dbn.zst
│   │   │   │   └── order_book_deltas_catalog
│   │   │   │       └── databento
│   │   │   │           ├── orderbooks_definition.dbn.zst
│   │   │   │           └── orderbooks_mbo_2024-05-08T00-00-00_2024-05-08T00-00-02.dbn.zst
│   │   │   ├── ema_cross_config.json
│   │   │   ├── fxcm
│   │   │   │   ├── gbpusd-m1-ask-2012.csv
│   │   │   │   ├── gbpusd-m1-bid-2012.csv
│   │   │   │   ├── usdjpy-m1-ask-2013.csv
│   │   │   │   └── usdjpy-m1-bid-2013.csv
│   │   │   ├── large
│   │   │   │   ├── checksums.json
│   │   │   │   ├── histdata_EURUSD.SIM_2020-01_instrument.metadata.json
│   │   │   │   ├── histdata_EURUSD.SIM_2020-01_quotes.metadata.json
│   │   │   │   ├── itch_AAPL.XNAS_2019-01-30_deltas.metadata.json
│   │   │   │   └── tardis_BTC-PERPETUAL.DERIBIT_2020-04-01_deltas.metadata.json
│   │   │   ├── nautilus
│   │   │   │   ├── 128-bit
│   │   │   │   │   ├── bars.parquet
│   │   │   │   │   ├── deltas.parquet
│   │   │   │   │   ├── quotes-3-groups-filter-query.parquet
│   │   │   │   │   ├── quotes.parquet
│   │   │   │   │   └── trades.parquet
│   │   │   │   └── 64-bit
│   │   │   │       ├── bars.parquet
│   │   │   │       ├── deltas.parquet
│   │   │   │       ├── quotes-3-groups-filter-query.parquet
│   │   │   │       ├── quotes.parquet
│   │   │   │       └── trades.parquet
│   │   │   ├── news_events.csv
│   │   │   ├── quote_tick_data.csv
│   │   │   ├── quote_tick_eurusd_2019_sim_rust.parquet
│   │   │   ├── quote_tick_usdjpy_2019_sim_rust.parquet
│   │   │   ├── short-term-interest.csv
│   │   │   ├── tardis
│   │   │   │   ├── binance-futures_book_snapshot_25_BTCUSDT.csv
│   │   │   │   ├── binance-futures_book_snapshot_5_BTCUSDT.csv
│   │   │   │   ├── bitmex_trades_XBTUSD.csv
│   │   │   │   ├── deribit_incremental_book_L2_BTC-PERPETUAL.csv
│   │   │   │   └── huobi-dm-swap_quotes_BTC-USD.csv
│   │   │   ├── truefx
│   │   │   │   ├── audusd-ticks.csv
│   │   │   │   └── usdjpy-ticks.csv
│   │   │   └── xcme
│   │   │       ├── 6EH4.XCME_1min_bars_20240101_20240131.csv.gz
│   │   │       └── README.md
│   │   ├── tools.toml
│   │   ├── TRADEMARK.md
│   │   └── version.json
│   ├── optuna
│   │   ├── CITATION.cff
│   │   ├── CODE_OF_CONDUCT.md
│   │   ├── CONTRIBUTING.md
│   │   ├── docs
│   │   │   ├── image
│   │   │   │   ├── favicon.ico
│   │   │   │   ├── optuna-logo.png
│   │   │   │   ├── optunahub-introduction.png
│   │   │   │   └── sampling-sequence.png
│   │   │   ├── make.bat
│   │   │   ├── Makefile
│   │   │   ├── source
│   │   │   │   ├── _static
│   │   │   │   │   └── css
│   │   │   │   │       └── custom.css
│   │   │   │   ├── _templates
│   │   │   │   │   ├── autosummary
│   │   │   │   │   │   └── class.rst
│   │   │   │   │   ├── breadcrumbs.html
│   │   │   │   │   ├── footer.html
│   │   │   │   │   └── layout.html
│   │   │   │   ├── conf.py
│   │   │   │   ├── faq.rst
│   │   │   │   ├── index.rst
│   │   │   │   ├── installation.rst
│   │   │   │   ├── license_thirdparty.rst
│   │   │   │   ├── privacy.rst
│   │   │   │   ├── reference
│   │   │   │   │   ├── artifacts.rst
│   │   │   │   │   ├── cli.rst
│   │   │   │   │   ├── distributions.rst
│   │   │   │   │   ├── exceptions.rst
│   │   │   │   │   ├── importance.rst
│   │   │   │   │   ├── index.rst
│   │   │   │   │   ├── integration.rst
│   │   │   │   │   ├── logging.rst
│   │   │   │   │   ├── optuna.rst
│   │   │   │   │   ├── pruners.rst
│   │   │   │   │   ├── samplers
│   │   │   │   │   │   ├── index.rst
│   │   │   │   │   │   └── nsgaii.rst
│   │   │   │   │   ├── search_space.rst
│   │   │   │   │   ├── storages.rst
│   │   │   │   │   ├── study.rst
│   │   │   │   │   ├── terminator.rst
│   │   │   │   │   ├── trial.rst
│   │   │   │   │   └── visualization
│   │   │   │   │       ├── index.rst
│   │   │   │   │       └── matplotlib
│   │   │   │   │           └── index.rst
│   │   │   │   └── tutorial
│   │   │   │       └── index.rst
│   │   │   ├── visualization_examples
│   │   │   │   ├── GALLERY_HEADER.rst
│   │   │   │   ├── optuna.visualization.plot_contour.py
│   │   │   │   ├── optuna.visualization.plot_edf.py
│   │   │   │   ├── optuna.visualization.plot_hypervolume_history.py
│   │   │   │   ├── optuna.visualization.plot_intermediate_values.py
│   │   │   │   ├── optuna.visualization.plot_optimization_history.py
│   │   │   │   ├── optuna.visualization.plot_parallel_coordinate.py
│   │   │   │   ├── optuna.visualization.plot_param_importances.py
│   │   │   │   ├── optuna.visualization.plot_pareto_front.py
│   │   │   │   ├── optuna.visualization.plot_rank.py
│   │   │   │   ├── optuna.visualization.plot_slice.py
│   │   │   │   ├── optuna.visualization.plot_terminator_improvement.py
│   │   │   │   └── optuna.visualization.plot_timeline.py
│   │   │   └── visualization_matplotlib_examples
│   │   │       ├── GALLERY_HEADER.rst
│   │   │       ├── optuna.visualization.matplotlib.contour.py
│   │   │       ├── optuna.visualization.matplotlib.edf.py
│   │   │       ├── optuna.visualization.matplotlib.hypervolume_history.py
│   │   │       ├── optuna.visualization.matplotlib.intermediate_values.py
│   │   │       ├── optuna.visualization.matplotlib.optimization_history.py
│   │   │       ├── optuna.visualization.matplotlib.parallel_coordinate.py
│   │   │       ├── optuna.visualization.matplotlib.param_importances.py
│   │   │       ├── optuna.visualization.matplotlib.pareto_front.py
│   │   │       ├── optuna.visualization.matplotlib.rank.py
│   │   │       ├── optuna.visualization.matplotlib.slice.py
│   │   │       ├── optuna.visualization.matplotlib.terminator_improvement.py
│   │   │       └── optuna.visualization.matplotlib.timeline.py
│   │   ├── LICENSE
│   │   ├── LICENSE_THIRD_PARTY
│   │   ├── MANIFEST.in
│   │   ├── optuna
│   │   │   ├── __init__.py
│   │   │   ├── _callbacks.py
│   │   │   ├── _convert_positional_args.py
│   │   │   ├── _deprecated.py
│   │   │   ├── _experimental.py
│   │   │   ├── _gp
│   │   │   │   ├── __init__.py
│   │   │   │   ├── acqf.py
│   │   │   │   ├── batched_lbfgsb.py
│   │   │   │   ├── gp.py
│   │   │   │   ├── optim_mixed.py
│   │   │   │   ├── optim_sample.py
│   │   │   │   ├── prior.py
│   │   │   │   ├── qmc.py
│   │   │   │   ├── search_space.py
│   │   │   │   └── thread_limiting.py
│   │   │   ├── _hypervolume
│   │   │   │   ├── __init__.py
│   │   │   │   ├── box_decomposition.py
│   │   │   │   ├── hssp.py
│   │   │   │   └── wfg.py
│   │   │   ├── _imports.py
│   │   │   ├── _transform.py
│   │   │   ├── _typing.py
│   │   │   ├── _warnings.py
│   │   │   ├── artifacts
│   │   │   │   ├── __init__.py
│   │   │   │   ├── _backoff.py
│   │   │   │   ├── _boto3.py
│   │   │   │   ├── _download.py
│   │   │   │   ├── _filesystem.py
│   │   │   │   ├── _gcs.py
│   │   │   │   ├── _list_artifact_meta.py
│   │   │   │   ├── _protocol.py
│   │   │   │   ├── _upload.py
│   │   │   │   └── exceptions.py
│   │   │   ├── cli.py
│   │   │   ├── distributions.py
│   │   │   ├── exceptions.py
│   │   │   ├── importance
│   │   │   │   ├── __init__.py
│   │   │   │   ├── _base.py
│   │   │   │   ├── _fanova
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── _evaluator.py
│   │   │   │   │   ├── _fanova.py
│   │   │   │   │   └── _tree.py
│   │   │   │   ├── _mean_decrease_impurity.py
│   │   │   │   └── _ped_anova
│   │   │   │       ├── __init__.py
│   │   │   │       ├── evaluator.py
│   │   │   │       └── scott_parzen_estimator.py
│   │   │   ├── integration
│   │   │   │   ├── __init__.py
│   │   │   │   ├── botorch.py
│   │   │   │   ├── catboost.py
│   │   │   │   ├── cma.py
│   │   │   │   ├── dask.py
│   │   │   │   ├── fastaiv2.py
│   │   │   │   ├── keras.py
│   │   │   │   ├── lightgbm.py
│   │   │   │   ├── mlflow.py
│   │   │   │   ├── pytorch_distributed.py
│   │   │   │   ├── pytorch_ignite.py
│   │   │   │   ├── pytorch_lightning.py
│   │   │   │   ├── shap.py
│   │   │   │   ├── sklearn.py
│   │   │   │   ├── skorch.py
│   │   │   │   ├── tensorboard.py
│   │   │   │   ├── tensorflow.py
│   │   │   │   ├── tfkeras.py
│   │   │   │   ├── wandb.py
│   │   │   │   └── xgboost.py
│   │   │   ├── logging.py
│   │   │   ├── progress_bar.py
│   │   │   ├── pruners
│   │   │   │   ├── __init__.py
│   │   │   │   ├── _base.py
│   │   │   │   ├── _hyperband.py
│   │   │   │   ├── _median.py
│   │   │   │   ├── _nop.py
│   │   │   │   ├── _patient.py
│   │   │   │   ├── _percentile.py
│   │   │   │   ├── _successive_halving.py
│   │   │   │   ├── _threshold.py
│   │   │   │   └── _wilcoxon.py
│   │   │   ├── py.typed
│   │   │   ├── samplers
│   │   │   │   ├── __init__.py
│   │   │   │   ├── _base.py
│   │   │   │   ├── _brute_force.py
│   │   │   │   ├── _cmaes.py
│   │   │   │   ├── _ga
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   └── _base.py
│   │   │   │   ├── _gp
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   └── sampler.py
│   │   │   │   ├── _grid.py
│   │   │   │   ├── _lazy_random_state.py
│   │   │   │   ├── _nsgaiii
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── _elite_population_selection_strategy.py
│   │   │   │   │   └── _sampler.py
│   │   │   │   ├── _partial_fixed.py
│   │   │   │   ├── _qmc.py
│   │   │   │   ├── _random.py
│   │   │   │   ├── _tpe
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── _erf.py
│   │   │   │   │   ├── _truncnorm.py
│   │   │   │   │   ├── parzen_estimator.py
│   │   │   │   │   ├── probability_distributions.py
│   │   │   │   │   └── sampler.py
│   │   │   │   └── nsgaii
│   │   │   │       ├── __init__.py
│   │   │   │       ├── _after_trial_strategy.py
│   │   │   │       ├── _child_generation_strategy.py
│   │   │   │       ├── _constraints_evaluation.py
│   │   │   │       ├── _crossover.py
│   │   │   │       ├── _crossovers
│   │   │   │       │   ├── __init__.py
│   │   │   │       │   ├── _base.py
│   │   │   │       │   ├── _blxalpha.py
│   │   │   │       │   ├── _sbx.py
│   │   │   │       │   ├── _spx.py
│   │   │   │       │   ├── _undx.py
│   │   │   │       │   ├── _uniform.py
│   │   │   │       │   └── _vsbx.py
│   │   │   │       ├── _elite_population_selection_strategy.py
│   │   │   │       ├── _mutation.py
│   │   │   │       ├── _mutations
│   │   │   │       │   ├── __init__.py
│   │   │   │       │   ├── _base.py
│   │   │   │       │   └── _polynomial.py
│   │   │   │       └── _sampler.py
│   │   │   ├── search_space
│   │   │   │   ├── __init__.py
│   │   │   │   ├── group_decomposed.py
│   │   │   │   └── intersection.py
│   │   │   ├── storages
│   │   │   │   ├── __init__.py
│   │   │   │   ├── _base.py
│   │   │   │   ├── _cached_storage.py
│   │   │   │   ├── _callbacks.py
│   │   │   │   ├── _grpc
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── api.proto
│   │   │   │   │   ├── auto_generated
│   │   │   │   │   │   ├── api_pb2_grpc.py
│   │   │   │   │   │   ├── api_pb2.py
│   │   │   │   │   │   └── api_pb2.pyi
│   │   │   │   │   ├── client.py
│   │   │   │   │   ├── server.py
│   │   │   │   │   └── servicer.py
│   │   │   │   ├── _heartbeat.py
│   │   │   │   ├── _in_memory.py
│   │   │   │   ├── _rdb
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── alembic
│   │   │   │   │   │   ├── env.py
│   │   │   │   │   │   ├── script.py.mako
│   │   │   │   │   │   └── versions
│   │   │   │   │   │       ├── v0.9.0.a.py
│   │   │   │   │   │       ├── v1.2.0.a.py
│   │   │   │   │   │       ├── v1.3.0.a.py
│   │   │   │   │   │       ├── v2.4.0.a.py
│   │   │   │   │   │       ├── v2.6.0.a_.py
│   │   │   │   │   │       ├── v3.0.0.a.py
│   │   │   │   │   │       ├── v3.0.0.b.py
│   │   │   │   │   │       ├── v3.0.0.c.py
│   │   │   │   │   │       ├── v3.0.0.d.py
│   │   │   │   │   │       └── v3.2.0.a_.py
│   │   │   │   │   ├── alembic.ini
│   │   │   │   │   ├── models.py
│   │   │   │   │   └── storage.py
│   │   │   │   └── journal
│   │   │   │       ├── __init__.py
│   │   │   │       ├── _base.py
│   │   │   │       ├── _file.py
│   │   │   │       ├── _redis.py
│   │   │   │       └── _storage.py
│   │   │   ├── study
│   │   │   │   ├── __init__.py
│   │   │   │   ├── _constrained_optimization.py
│   │   │   │   ├── _dataframe.py
│   │   │   │   ├── _frozen.py
│   │   │   │   ├── _multi_objective.py
│   │   │   │   ├── _optimize.py
│   │   │   │   ├── _study_direction.py
│   │   │   │   ├── _study_summary.py
│   │   │   │   ├── _tell.py
│   │   │   │   └── study.py
│   │   │   ├── terminator
│   │   │   │   ├── __init__.py
│   │   │   │   ├── callback.py
│   │   │   │   ├── erroreval.py
│   │   │   │   ├── improvement
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── emmr.py
│   │   │   │   │   └── evaluator.py
│   │   │   │   ├── median_erroreval.py
│   │   │   │   └── terminator.py
│   │   │   ├── testing
│   │   │   │   ├── __init__.py
│   │   │   │   ├── objectives.py
│   │   │   │   ├── pruners.py
│   │   │   │   ├── pytest_importance.py
│   │   │   │   ├── pytest_samplers.py
│   │   │   │   ├── pytest_storages.py
│   │   │   │   ├── samplers.py
│   │   │   │   ├── storages.py
│   │   │   │   ├── tempfile_pool.py
│   │   │   │   ├── threading.py
│   │   │   │   ├── trials.py
│   │   │   │   └── visualization.py
│   │   │   ├── trial
│   │   │   │   ├── __init__.py
│   │   │   │   ├── _base.py
│   │   │   │   ├── _fixed.py
│   │   │   │   ├── _frozen.py
│   │   │   │   ├── _state.py
│   │   │   │   └── _trial.py
│   │   │   ├── version.py
│   │   │   └── visualization
│   │   │       ├── __init__.py
│   │   │       ├── _contour.py
│   │   │       ├── _edf.py
│   │   │       ├── _hypervolume_history.py
│   │   │       ├── _intermediate_values.py
│   │   │       ├── _optimization_history.py
│   │   │       ├── _parallel_coordinate.py
│   │   │       ├── _param_importances.py
│   │   │       ├── _pareto_front.py
│   │   │       ├── _plotly_imports.py
│   │   │       ├── _rank.py
│   │   │       ├── _slice.py
│   │   │       ├── _terminator_improvement.py
│   │   │       ├── _timeline.py
│   │   │       ├── _utils.py
│   │   │       └── matplotlib
│   │   │           ├── __init__.py
│   │   │           ├── _contour.py
│   │   │           ├── _edf.py
│   │   │           ├── _hypervolume_history.py
│   │   │           ├── _intermediate_values.py
│   │   │           ├── _matplotlib_imports.py
│   │   │           ├── _optimization_history.py
│   │   │           ├── _parallel_coordinate.py
│   │   │           ├── _param_importances.py
│   │   │           ├── _pareto_front.py
│   │   │           ├── _rank.py
│   │   │           ├── _slice.py
│   │   │           ├── _terminator_improvement.py
│   │   │           ├── _timeline.py
│   │   │           └── _utils.py
│   │   ├── pyproject.toml
│   │   ├── README.md
│   │   ├── SECURITY.md
│   │   ├── tests
│   │   │   ├── __init__.py
│   │   │   ├── artifacts_tests
│   │   │   │   ├── __init__.py
│   │   │   │   ├── stubs.py
│   │   │   │   ├── test_backoff.py
│   │   │   │   ├── test_boto3.py
│   │   │   │   ├── test_download_artifact.py
│   │   │   │   ├── test_filesystem.py
│   │   │   │   ├── test_gcs.py
│   │   │   │   ├── test_list_artifact_meta.py
│   │   │   │   └── test_upload_artifact.py
│   │   │   ├── conftest.py
│   │   │   ├── gp_tests
│   │   │   │   ├── test_acqf.py
│   │   │   │   ├── test_batched_lbfgsb.py
│   │   │   │   ├── test_gp.py
│   │   │   │   └── test_search_space.py
│   │   │   ├── hypervolume_tests
│   │   │   │   ├── __init__.py
│   │   │   │   ├── test_box_decomposition.py
│   │   │   │   ├── test_hssp.py
│   │   │   │   └── test_wfg.py
│   │   │   ├── importance_tests
│   │   │   │   ├── __init__.py
│   │   │   │   ├── fanova_tests
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   └── test_tree.py
│   │   │   │   ├── pedanova_tests
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── test_evaluator.py
│   │   │   │   │   └── test_scott_parzen_estimator.py
│   │   │   │   └── test_evaluator.py
│   │   │   ├── pruners_tests
│   │   │   │   ├── __init__.py
│   │   │   │   ├── test_hyperband.py
│   │   │   │   ├── test_median.py
│   │   │   │   ├── test_nop.py
│   │   │   │   ├── test_patient.py
│   │   │   │   ├── test_percentile.py
│   │   │   │   ├── test_successive_halving.py
│   │   │   │   ├── test_threshold.py
│   │   │   │   └── test_wilcoxon.py
│   │   │   ├── samplers_tests
│   │   │   │   ├── __init__.py
│   │   │   │   ├── test_base_gasampler.py
│   │   │   │   ├── test_brute_force.py
│   │   │   │   ├── test_cmaes.py
│   │   │   │   ├── test_gp.py
│   │   │   │   ├── test_grid.py
│   │   │   │   ├── test_lazy_random_state.py
│   │   │   │   ├── test_nsgaii.py
│   │   │   │   ├── test_nsgaiii.py
│   │   │   │   ├── test_partial_fixed.py
│   │   │   │   ├── test_qmc.py
│   │   │   │   ├── test_samplers.py
│   │   │   │   └── tpe_tests
│   │   │   │       ├── __init__.py
│   │   │   │       ├── test_multi_objective_sampler.py
│   │   │   │       ├── test_parzen_estimator.py
│   │   │   │       ├── test_probability_distributions.py
│   │   │   │       ├── test_sampler.py
│   │   │   │       └── test_truncnorm.py
│   │   │   ├── search_space_tests
│   │   │   │   ├── __init__.py
│   │   │   │   ├── test_group_decomposed.py
│   │   │   │   └── test_intersection.py
│   │   │   ├── storages_tests
│   │   │   │   ├── __init__.py
│   │   │   │   ├── journal_tests
│   │   │   │   │   ├── assets
│   │   │   │   │   │   └── 4.0.0.dev.log
│   │   │   │   │   ├── create_journal.py
│   │   │   │   │   ├── test_combination_with_grpc.py
│   │   │   │   │   ├── test_journal.py
│   │   │   │   │   └── test_log_compatibility.py
│   │   │   │   ├── rdb_tests
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── create_db.py
│   │   │   │   │   ├── test_models.py
│   │   │   │   │   ├── test_storage.py
│   │   │   │   │   └── test_upgrade_assets
│   │   │   │   │       ├── 0.9.0.a.db
│   │   │   │   │       ├── 1.2.0.a.db
│   │   │   │   │       ├── 1.3.0.a.db
│   │   │   │   │       ├── 2.4.0.a.db
│   │   │   │   │       ├── 2.6.0.a.db
│   │   │   │   │       ├── 3.0.0.a.db
│   │   │   │   │       ├── 3.0.0.b.db
│   │   │   │   │       ├── 3.0.0.c.db
│   │   │   │   │       ├── 3.0.0.d.db
│   │   │   │   │       └── 3.2.0.a.db
│   │   │   │   ├── test_cached_storage.py
│   │   │   │   ├── test_callbacks.py
│   │   │   │   ├── test_grpc.py
│   │   │   │   ├── test_heartbeat.py
│   │   │   │   ├── test_storages.py
│   │   │   │   └── test_with_server.py
│   │   │   ├── study_tests
│   │   │   │   ├── __init__.py
│   │   │   │   ├── test_constrained_optimization.py
│   │   │   │   ├── test_dataframe.py
│   │   │   │   ├── test_multi_objective.py
│   │   │   │   ├── test_optimize.py
│   │   │   │   ├── test_study_summary.py
│   │   │   │   └── test_study.py
│   │   │   ├── terminator_tests
│   │   │   │   ├── improvement_tests
│   │   │   │   │   ├── test_emmr_evaluator.py
│   │   │   │   │   └── test_evaluator.py
│   │   │   │   ├── test_callback.py
│   │   │   │   ├── test_erroreval.py
│   │   │   │   ├── test_median_erroreval.py
│   │   │   │   └── test_terminator.py
│   │   │   ├── test_callbacks.py
│   │   │   ├── test_cli.py
│   │   │   ├── test_convert_positional_args.py
│   │   │   ├── test_deprecated.py
│   │   │   ├── test_distributions.py
│   │   │   ├── test_experimental.py
│   │   │   ├── test_imports.py
│   │   │   ├── test_logging.py
│   │   │   ├── test_multi_objective.py
│   │   │   ├── test_transform.py
│   │   │   ├── trial_tests
│   │   │   │   ├── __init__.py
│   │   │   │   ├── test_fixed.py
│   │   │   │   ├── test_frozen.py
│   │   │   │   ├── test_trial.py
│   │   │   │   └── test_trials.py
│   │   │   └── visualization_tests
│   │   │       ├── __init__.py
│   │   │       ├── matplotlib_tests
│   │   │       │   ├── __init__.py
│   │   │       │   ├── test_contour.py
│   │   │       │   └── test_optimization_history.py
│   │   │       ├── test_contour.py
│   │   │       ├── test_edf.py
│   │   │       ├── test_hypervolume_history.py
│   │   │       ├── test_intermediate_plot.py
│   │   │       ├── test_optimization_history.py
│   │   │       ├── test_parallel_coordinate.py
│   │   │       ├── test_param_importances.py
│   │   │       ├── test_pareto_front.py
│   │   │       ├── test_rank.py
│   │   │       ├── test_slice.py
│   │   │       ├── test_terminator_improvement.py
│   │   │       ├── test_timeline.py
│   │   │       ├── test_utils.py
│   │   │       └── test_visualizations.py
│   │   └── tutorial
│   │       ├── 10_key_features
│   │       │   ├── 001_first.py
│   │       │   ├── 002_configurations.py
│   │       │   ├── 003_efficient_optimization_algorithms.py
│   │       │   ├── 004_distributed.py
│   │       │   ├── 005_visualization.py
│   │       │   └── README.rst
│   │       ├── 20_recipes
│   │       │   ├── 001_rdb.py
│   │       │   ├── 002_multi_objective.py
│   │       │   ├── 003_attributes.py
│   │       │   ├── 004_cli.py
│   │       │   ├── 005_user_defined_sampler.py
│   │       │   ├── 006_user_defined_pruner.py
│   │       │   ├── 007_optuna_callback.py
│   │       │   ├── 008_specify_params.py
│   │       │   ├── 009_ask_and_tell.py
│   │       │   ├── 010_reuse_best_trial.py
│   │       │   ├── 011_journal_storage.py
│   │       │   ├── 012_artifact_tutorial.py
│   │       │   ├── 013_wilcoxon_pruner.py
│   │       │   ├── 014_ablation_study_by_optuna.py
│   │       │   └── README.rst
│   │       └── README.rst
│   ├── pybroker
│   │   ├── asv.conf.json
│   │   ├── benchmarks
│   │   │   ├── __init__.py
│   │   │   └── bench_backtest.py
│   │   ├── docs
│   │   │   ├── _html
│   │   │   │   ├── robots.txt
│   │   │   │   └── sitemap-index.xml
│   │   │   ├── _static
│   │   │   │   ├── bosun03.otf
│   │   │   │   ├── email-image.png
│   │   │   │   ├── pybroker-logo.png
│   │   │   │   └── walkforward.png
│   │   │   ├── images
│   │   │   │   └── orders_dataframe.png
│   │   │   ├── locales
│   │   │   │   └── zh_CN
│   │   │   │       └── LC_MESSAGES
│   │   │   │           ├── changelog.po
│   │   │   │           ├── index.po
│   │   │   │           ├── install.po
│   │   │   │           ├── license.po
│   │   │   │           ├── notebooks
│   │   │   │           │   ├── 1. Getting Started with Data Sources.po
│   │   │   │           │   ├── 10. Rotational Trading.po
│   │   │   │           │   ├── 2. Backtesting a Strategy.po
│   │   │   │           │   ├── 3. Evaluating with Bootstrap Metrics.po
│   │   │   │           │   ├── 4. Ranking and Position Sizing.po
│   │   │   │           │   ├── 5. Writing Indicators.po
│   │   │   │           │   ├── 6. Training a Model.po
│   │   │   │           │   ├── 7. Creating a Custom Data Source.po
│   │   │   │           │   ├── 8. Applying Stops.po
│   │   │   │           │   ├── 9. Rebalancing Positions.po
│   │   │   │           │   └── FAQs.po
│   │   │   │           └── reference
│   │   │   │               ├── modules.po
│   │   │   │               ├── pybroker.cache.po
│   │   │   │               ├── pybroker.common.po
│   │   │   │               ├── pybroker.config.po
│   │   │   │               ├── pybroker.context.po
│   │   │   │               ├── pybroker.data.po
│   │   │   │               ├── pybroker.eval.po
│   │   │   │               ├── pybroker.ext.data.po
│   │   │   │               ├── pybroker.indicator.po
│   │   │   │               ├── pybroker.log.po
│   │   │   │               ├── pybroker.model.po
│   │   │   │               ├── pybroker.po
│   │   │   │               ├── pybroker.portfolio.po
│   │   │   │               ├── pybroker.scope.po
│   │   │   │               ├── pybroker.slippage.po
│   │   │   │               ├── pybroker.strategy.po
│   │   │   │               └── pybroker.vect.po
│   │   │   └── source
│   │   │       ├── benchmarking.rst
│   │   │       ├── changelog.rst
│   │   │       ├── conf.py
│   │   │       ├── index.rst
│   │   │       ├── install.rst
│   │   │       ├── license.rst
│   │   │       ├── notebooks
│   │   │       │   ├── 1. Getting Started with Data Sources.ipynb
│   │   │       │   ├── 10. Rotational Trading.ipynb
│   │   │       │   ├── 2. Backtesting a Strategy.ipynb
│   │   │       │   ├── 3. Evaluating with Bootstrap Metrics.ipynb
│   │   │       │   ├── 4. Ranking and Position Sizing.ipynb
│   │   │       │   ├── 5. Writing Indicators.ipynb
│   │   │       │   ├── 6. Training a Model.ipynb
│   │   │       │   ├── 7. Creating a Custom Data Source.ipynb
│   │   │       │   ├── 8. Applying Stops.ipynb
│   │   │       │   ├── 9. Rebalancing Positions.ipynb
│   │   │       │   ├── data
│   │   │       │   │   └── prices.csv
│   │   │       │   └── FAQs.ipynb
│   │   │       └── reference
│   │   │           ├── modules.rst
│   │   │           ├── pybroker.cache.rst
│   │   │           ├── pybroker.common.rst
│   │   │           ├── pybroker.config.rst
│   │   │           ├── pybroker.context.rst
│   │   │           ├── pybroker.data.rst
│   │   │           ├── pybroker.eval.rst
│   │   │           ├── pybroker.ext.data.rst
│   │   │           ├── pybroker.indicator.rst
│   │   │           ├── pybroker.log.rst
│   │   │           ├── pybroker.model.rst
│   │   │           ├── pybroker.portfolio.rst
│   │   │           ├── pybroker.rst
│   │   │           ├── pybroker.scope.rst
│   │   │           ├── pybroker.slippage.rst
│   │   │           ├── pybroker.strategy.rst
│   │   │           └── pybroker.vect.rst
│   │   ├── LICENSE
│   │   ├── MANIFEST.in
│   │   ├── pyproject.toml
│   │   ├── README.md
│   │   ├── requirements.txt
│   │   ├── setup.cfg
│   │   ├── skills
│   │   │   └── pybroker-strategy-creator
│   │   │       ├── agents
│   │   │       │   └── openai.yaml
│   │   │       ├── assets
│   │   │       │   └── strategy_template.py
│   │   │       ├── references
│   │   │       │   ├── api-public-surface.md
│   │   │       │   ├── pybroker-patterns.md
│   │   │       │   ├── wiki-01-getting-started-with-data-sources.md
│   │   │       │   ├── wiki-02-backtesting-a-strategy.md
│   │   │       │   ├── wiki-03-evaluating-with-bootstrap-metrics.md
│   │   │       │   ├── wiki-04-ranking-and-position-sizing.md
│   │   │       │   ├── wiki-05-writing-indicators.md
│   │   │       │   ├── wiki-06-training-a-model.md
│   │   │       │   ├── wiki-07-creating-a-custom-data-source.md
│   │   │       │   ├── wiki-08-applying-stops.md
│   │   │       │   ├── wiki-09-rebalancing-positions.md
│   │   │       │   ├── wiki-10-rotational-trading.md
│   │   │       │   ├── wiki-faqs.md
│   │   │       │   └── wiki-index.md
│   │   │       └── SKILL.md
│   │   ├── src
│   │   │   └── pybroker
│   │   │       ├── __init__.py
│   │   │       ├── cache.py
│   │   │       ├── common.py
│   │   │       ├── config.py
│   │   │       ├── context.py
│   │   │       ├── data.py
│   │   │       ├── eval.py
│   │   │       ├── ext
│   │   │       │   ├── __init__.py
│   │   │       │   └── data.py
│   │   │       ├── indicator.py
│   │   │       ├── log.py
│   │   │       ├── model.py
│   │   │       ├── portfolio.py
│   │   │       ├── py.typed
│   │   │       ├── scope.py
│   │   │       ├── slippage.py
│   │   │       ├── strategy.py
│   │   │       └── vect.py
│   │   └── tests
│   │       ├── __init__.py
│   │       ├── fixtures.py
│   │       ├── test_cache.py
│   │       ├── test_common.py
│   │       ├── test_context.py
│   │       ├── test_data.py
│   │       ├── test_eval.py
│   │       ├── test_exit_on_last_bar_perf.py
│   │       ├── test_indicator.py
│   │       ├── test_log.py
│   │       ├── test_model.py
│   │       ├── test_portfolio.py
│   │       ├── test_scope.py
│   │       ├── test_slippage.py
│   │       ├── test_strategy.py
│   │       ├── test_vect.py
│   │       └── testdata
│   │           ├── daily_1.pkl
│   │           ├── portfolio_df.pkl
│   │           ├── trades_df.pkl
│   │           ├── yfinance_single.pkl
│   │           └── yfinance.pkl
│   ├── qlib
│   │   ├── build_docker_image.sh
│   │   ├── CHANGELOG.md
│   │   ├── CHANGES.rst
│   │   ├── CODE_OF_CONDUCT.md
│   │   ├── Dockerfile
│   │   ├── docs
│   │   │   ├── _static
│   │   │   │   ├── demo.sh
│   │   │   │   └── img
│   │   │   │       ├── analysis
│   │   │   │       │   ├── analysis_model_auto_correlation.png
│   │   │   │       │   ├── analysis_model_cumulative_return.png
│   │   │   │       │   ├── analysis_model_IC.png
│   │   │   │       │   ├── analysis_model_long_short.png
│   │   │   │       │   ├── analysis_model_monthly_IC.png
│   │   │   │       │   ├── analysis_model_NDQ.png
│   │   │   │       │   ├── cumulative_return_buy_minus_sell.png
│   │   │   │       │   ├── cumulative_return_buy.png
│   │   │   │       │   ├── cumulative_return_hold.png
│   │   │   │       │   ├── cumulative_return_sell.png
│   │   │   │       │   ├── rank_label_buy.png
│   │   │   │       │   ├── rank_label_hold.png
│   │   │   │       │   ├── rank_label_sell.png
│   │   │   │       │   ├── report.png
│   │   │   │       │   ├── risk_analysis_annualized_return.png
│   │   │   │       │   ├── risk_analysis_bar.png
│   │   │   │       │   ├── risk_analysis_information_ratio.png
│   │   │   │       │   ├── risk_analysis_max_drawdown.png
│   │   │   │       │   ├── risk_analysis_std.png
│   │   │   │       │   └── score_ic.png
│   │   │   │       ├── change doc.gif
│   │   │   │       ├── framework-abstract.jpg
│   │   │   │       ├── framework.png
│   │   │   │       ├── framework.svg
│   │   │   │       ├── logo
│   │   │   │       │   ├── 1.png
│   │   │   │       │   ├── 2.png
│   │   │   │       │   ├── 3.png
│   │   │   │       │   ├── white_bg_rec+word.png
│   │   │   │       │   ├── yel_bg_rec+word.png
│   │   │   │       │   ├── yellow_bg_rec.png
│   │   │   │       │   └── yellow_bg_rec+word .png
│   │   │   │       ├── online_serving.png
│   │   │   │       ├── QlibRL_framework.png
│   │   │   │       ├── qrcode
│   │   │   │       │   └── gitter_qr.png
│   │   │   │       ├── rdagent_logo.png
│   │   │   │       ├── RL_framework.png
│   │   │   │       ├── Task-Gen-Recorder-Collector.svg
│   │   │   │       └── topk_drop.png
│   │   │   ├── advanced
│   │   │   │   ├── alpha.rst
│   │   │   │   ├── PIT.rst
│   │   │   │   ├── serial.rst
│   │   │   │   ├── server.rst
│   │   │   │   └── task_management.rst
│   │   │   ├── changelog
│   │   │   │   └── changelog.rst
│   │   │   ├── component
│   │   │   │   ├── data.rst
│   │   │   │   ├── highfreq.rst
│   │   │   │   ├── meta.rst
│   │   │   │   ├── model.rst
│   │   │   │   ├── online.rst
│   │   │   │   ├── recorder.rst
│   │   │   │   ├── report.rst
│   │   │   │   ├── rl
│   │   │   │   │   ├── framework.rst
│   │   │   │   │   ├── guidance.rst
│   │   │   │   │   ├── overall.rst
│   │   │   │   │   ├── quickstart.rst
│   │   │   │   │   └── toctree.rst
│   │   │   │   ├── strategy.rst
│   │   │   │   └── workflow.rst
│   │   │   ├── conf.py
│   │   │   ├── developer
│   │   │   │   ├── code_standard_and_dev_guide.rst
│   │   │   │   └── how_to_build_image.rst
│   │   │   ├── FAQ
│   │   │   │   └── FAQ.rst
│   │   │   ├── hidden
│   │   │   │   ├── client.rst
│   │   │   │   ├── online.rst
│   │   │   │   └── tuner.rst
│   │   │   ├── index.rst
│   │   │   ├── introduction
│   │   │   │   ├── introduction.rst
│   │   │   │   └── quick.rst
│   │   │   ├── make.bat
│   │   │   ├── Makefile
│   │   │   ├── reference
│   │   │   │   └── api.rst
│   │   │   ├── requirements.txt
│   │   │   └── start
│   │   │       ├── getdata.rst
│   │   │       ├── initialization.rst
│   │   │       ├── installation.rst
│   │   │       └── integration.rst
│   │   ├── examples
│   │   │   ├── benchmarks
│   │   │   │   ├── ADARNN
│   │   │   │   │   ├── README.md
│   │   │   │   │   ├── requirements.txt
│   │   │   │   │   └── workflow_config_adarnn_Alpha360.yaml
│   │   │   │   ├── ADD
│   │   │   │   │   ├── README.md
│   │   │   │   │   ├── requirements.txt
│   │   │   │   │   └── workflow_config_add_Alpha360.yaml
│   │   │   │   ├── ALSTM
│   │   │   │   │   ├── README.md
│   │   │   │   │   ├── requirements.txt
│   │   │   │   │   ├── workflow_config_alstm_Alpha158.yaml
│   │   │   │   │   └── workflow_config_alstm_Alpha360.yaml
│   │   │   │   ├── CatBoost
│   │   │   │   │   ├── README.md
│   │   │   │   │   ├── requirements.txt
│   │   │   │   │   ├── workflow_config_catboost_Alpha158_csi500.yaml
│   │   │   │   │   ├── workflow_config_catboost_Alpha158.yaml
│   │   │   │   │   ├── workflow_config_catboost_Alpha360_csi500.yaml
│   │   │   │   │   └── workflow_config_catboost_Alpha360.yaml
│   │   │   │   ├── DoubleEnsemble
│   │   │   │   │   ├── README.md
│   │   │   │   │   ├── requirements.txt
│   │   │   │   │   ├── workflow_config_doubleensemble_Alpha158_csi500.yaml
│   │   │   │   │   ├── workflow_config_doubleensemble_Alpha158.yaml
│   │   │   │   │   ├── workflow_config_doubleensemble_Alpha360_csi500.yaml
│   │   │   │   │   ├── workflow_config_doubleensemble_Alpha360.yaml
│   │   │   │   │   └── workflow_config_doubleensemble_early_stop_Alpha158.yaml
│   │   │   │   ├── GATs
│   │   │   │   │   ├── README.md
│   │   │   │   │   ├── requirements.txt
│   │   │   │   │   ├── workflow_config_gats_Alpha158.yaml
│   │   │   │   │   └── workflow_config_gats_Alpha360.yaml
│   │   │   │   ├── GeneralPtNN
│   │   │   │   │   ├── README.md
│   │   │   │   │   ├── workflow_config_gru.yaml
│   │   │   │   │   ├── workflow_config_gru2mlp.yaml
│   │   │   │   │   └── workflow_config_mlp.yaml
│   │   │   │   ├── GRU
│   │   │   │   │   ├── csi300_gru_ts.pkl
│   │   │   │   │   ├── model_gru_csi300.pkl
│   │   │   │   │   ├── README.md
│   │   │   │   │   ├── requirements.txt
│   │   │   │   │   ├── workflow_config_gru_Alpha158.yaml
│   │   │   │   │   └── workflow_config_gru_Alpha360.yaml
│   │   │   │   ├── HIST
│   │   │   │   │   ├── qlib_csi300_stock_index.npy
│   │   │   │   │   ├── README.md
│   │   │   │   │   ├── requirements.txt
│   │   │   │   │   └── workflow_config_hist_Alpha360.yaml
│   │   │   │   ├── IGMTF
│   │   │   │   │   ├── README.md
│   │   │   │   │   ├── requirements.txt
│   │   │   │   │   └── workflow_config_igmtf_Alpha360.yaml
│   │   │   │   ├── KRNN
│   │   │   │   │   ├── README.md
│   │   │   │   │   ├── requirements.txt
│   │   │   │   │   └── workflow_config_krnn_Alpha360.yaml
│   │   │   │   ├── LightGBM
│   │   │   │   │   ├── features_resample_N.py
│   │   │   │   │   ├── features_sample.py
│   │   │   │   │   ├── multi_freq_handler.py
│   │   │   │   │   ├── README.md
│   │   │   │   │   ├── requirements.txt
│   │   │   │   │   ├── workflow_config_lightgbm_Alpha158_csi500.yaml
│   │   │   │   │   ├── workflow_config_lightgbm_Alpha158_multi_freq.yaml
│   │   │   │   │   ├── workflow_config_lightgbm_Alpha158.yaml
│   │   │   │   │   ├── workflow_config_lightgbm_Alpha360_csi500.yaml
│   │   │   │   │   ├── workflow_config_lightgbm_Alpha360.yaml
│   │   │   │   │   ├── workflow_config_lightgbm_configurable_dataset.yaml
│   │   │   │   │   └── workflow_config_lightgbm_multi_freq.yaml
│   │   │   │   ├── Linear
│   │   │   │   │   ├── requirements.txt
│   │   │   │   │   ├── workflow_config_linear_Alpha158_csi500.yaml
│   │   │   │   │   ├── workflow_config_linear_Alpha158_multi_pass_bt.yaml
│   │   │   │   │   └── workflow_config_linear_Alpha158.yaml
│   │   │   │   ├── Localformer
│   │   │   │   │   ├── README.md
│   │   │   │   │   ├── requirements.txt
│   │   │   │   │   ├── workflow_config_localformer_Alpha158.yaml
│   │   │   │   │   └── workflow_config_localformer_Alpha360.yaml
│   │   │   │   ├── LSTM
│   │   │   │   │   ├── csi300_lstm_ts.pkl
│   │   │   │   │   ├── model_lstm_csi300.pkl
│   │   │   │   │   ├── README.md
│   │   │   │   │   ├── requirements.txt
│   │   │   │   │   ├── workflow_config_lstm_Alpha158.yaml
│   │   │   │   │   └── workflow_config_lstm_Alpha360.yaml
│   │   │   │   ├── MLP
│   │   │   │   │   ├── README.md
│   │   │   │   │   ├── requirements.txt
│   │   │   │   │   ├── workflow_config_mlp_Alpha158_csi500.yaml
│   │   │   │   │   ├── workflow_config_mlp_Alpha158.yaml
│   │   │   │   │   ├── workflow_config_mlp_Alpha360_csi500.yaml
│   │   │   │   │   └── workflow_config_mlp_Alpha360.yaml
│   │   │   │   ├── README.md
│   │   │   │   ├── Sandwich
│   │   │   │   │   ├── README.md
│   │   │   │   │   ├── requirements.txt
│   │   │   │   │   └── workflow_config_sandwich_Alpha360.yaml
│   │   │   │   ├── SFM
│   │   │   │   │   ├── README.md
│   │   │   │   │   ├── requirements.txt
│   │   │   │   │   └── workflow_config_sfm_Alpha360.yaml
│   │   │   │   ├── TabNet
│   │   │   │   │   ├── README.md
│   │   │   │   │   ├── requirements.txt
│   │   │   │   │   ├── workflow_config_TabNet_Alpha158.yaml
│   │   │   │   │   └── workflow_config_TabNet_Alpha360.yaml
│   │   │   │   ├── TCN
│   │   │   │   │   ├── README.md
│   │   │   │   │   ├── requirements.txt
│   │   │   │   │   ├── workflow_config_tcn_Alpha158.yaml
│   │   │   │   │   └── workflow_config_tcn_Alpha360.yaml
│   │   │   │   ├── TCTS
│   │   │   │   │   ├── README.md
│   │   │   │   │   ├── requirements.txt
│   │   │   │   │   ├── workflow_config_tcts_Alpha360.yaml
│   │   │   │   │   └── workflow.png
│   │   │   │   ├── TFT
│   │   │   │   │   ├── data_formatters
│   │   │   │   │   │   ├── __init__.py
│   │   │   │   │   │   ├── base.py
│   │   │   │   │   │   └── qlib_Alpha158.py
│   │   │   │   │   ├── expt_settings
│   │   │   │   │   │   ├── __init__.py
│   │   │   │   │   │   └── configs.py
│   │   │   │   │   ├── libs
│   │   │   │   │   │   ├── __init__.py
│   │   │   │   │   │   ├── hyperparam_opt.py
│   │   │   │   │   │   ├── tft_model.py
│   │   │   │   │   │   └── utils.py
│   │   │   │   │   ├── README.md
│   │   │   │   │   ├── requirements.txt
│   │   │   │   │   ├── tft.py
│   │   │   │   │   └── workflow_config_tft_Alpha158.yaml
│   │   │   │   ├── TRA
│   │   │   │   │   ├── configs
│   │   │   │   │   │   ├── config_alstm_tra_init.yaml
│   │   │   │   │   │   ├── config_alstm_tra.yaml
│   │   │   │   │   │   ├── config_alstm.yaml
│   │   │   │   │   │   ├── config_transformer_tra_init.yaml
│   │   │   │   │   │   ├── config_transformer_tra.yaml
│   │   │   │   │   │   └── config_transformer.yaml
│   │   │   │   │   ├── data
│   │   │   │   │   │   └── README.md
│   │   │   │   │   ├── example.py
│   │   │   │   │   ├── README.md
│   │   │   │   │   ├── Reports.ipynb
│   │   │   │   │   ├── requirements.txt
│   │   │   │   │   ├── run.sh
│   │   │   │   │   ├── src
│   │   │   │   │   │   ├── dataset.py
│   │   │   │   │   │   └── model.py
│   │   │   │   │   ├── workflow_config_tra_Alpha158_full.yaml
│   │   │   │   │   ├── workflow_config_tra_Alpha158.yaml
│   │   │   │   │   └── workflow_config_tra_Alpha360.yaml
│   │   │   │   ├── Transformer
│   │   │   │   │   ├── README.md
│   │   │   │   │   ├── requirements.txt
│   │   │   │   │   ├── workflow_config_transformer_Alpha158.yaml
│   │   │   │   │   └── workflow_config_transformer_Alpha360.yaml
│   │   │   │   └── XGBoost
│   │   │   │       ├── README.md
│   │   │   │       ├── requirements.txt
│   │   │   │       ├── workflow_config_xgboost_Alpha158.yaml
│   │   │   │       └── workflow_config_xgboost_Alpha360.yaml
│   │   │   ├── benchmarks_dynamic
│   │   │   │   ├── baseline
│   │   │   │   │   ├── README.md
│   │   │   │   │   ├── rolling_benchmark.py
│   │   │   │   │   ├── workflow_config_lightgbm_Alpha158.yaml
│   │   │   │   │   └── workflow_config_linear_Alpha158.yaml
│   │   │   │   ├── DDG-DA
│   │   │   │   │   ├── Makefile
│   │   │   │   │   ├── README.md
│   │   │   │   │   ├── requirements.txt
│   │   │   │   │   ├── vis_data.py
│   │   │   │   │   └── workflow.py
│   │   │   │   └── README.md
│   │   │   ├── data_demo
│   │   │   │   ├── data_cache_demo.py
│   │   │   │   ├── data_mem_resuse_demo.py
│   │   │   │   └── README.md
│   │   │   ├── highfreq
│   │   │   │   ├── highfreq_handler.py
│   │   │   │   ├── highfreq_ops.py
│   │   │   │   ├── highfreq_processor.py
│   │   │   │   ├── README.md
│   │   │   │   ├── workflow_config_High_Freq_Tree_Alpha158.yaml
│   │   │   │   └── workflow.py
│   │   │   ├── hyperparameter
│   │   │   │   └── LightGBM
│   │   │   │       ├── hyperparameter_158.py
│   │   │   │       ├── hyperparameter_360.py
│   │   │   │       ├── Readme.md
│   │   │   │       └── requirements.txt
│   │   │   ├── model_interpreter
│   │   │   │   └── feature.py
│   │   │   ├── model_rolling
│   │   │   │   ├── requirements.txt
│   │   │   │   └── task_manager_rolling.py
│   │   │   ├── nested_decision_execution
│   │   │   │   ├── README.md
│   │   │   │   └── workflow.py
│   │   │   ├── online_srv
│   │   │   │   ├── online_management_simulate.py
│   │   │   │   ├── rolling_online_management.py
│   │   │   │   └── update_online_pred.py
│   │   │   ├── orderbook_data
│   │   │   │   ├── create_dataset.py
│   │   │   │   ├── example.py
│   │   │   │   └── README.md
│   │   │   ├── portfolio
│   │   │   │   ├── config_enhanced_indexing.yaml
│   │   │   │   ├── prepare_riskdata.py
│   │   │   │   └── README.md
│   │   │   ├── README.md
│   │   │   ├── rl
│   │   │   │   └── simple_example.ipynb
│   │   │   ├── rl_order_execution
│   │   │   │   ├── exp_configs
│   │   │   │   │   ├── backtest_opds.yml
│   │   │   │   │   ├── backtest_ppo.yml
│   │   │   │   │   ├── backtest_twap.yml
│   │   │   │   │   ├── train_opds.yml
│   │   │   │   │   └── train_ppo.yml
│   │   │   │   ├── README.md
│   │   │   │   └── scripts
│   │   │   │       ├── gen_pickle_data.py
│   │   │   │       ├── gen_training_orders.py
│   │   │   │       ├── merge_orders.py
│   │   │   │       └── pickle_data_config.yml
│   │   │   ├── rolling_process_data
│   │   │   │   ├── README.md
│   │   │   │   ├── rolling_handler.py
│   │   │   │   └── workflow.py
│   │   │   ├── run_all_model.py
│   │   │   ├── tutorial
│   │   │   │   └── detailed_workflow.ipynb
│   │   │   ├── workflow_by_code.ipynb
│   │   │   └── workflow_by_code.py
│   │   ├── LICENSE
│   │   ├── Makefile
│   │   ├── MANIFEST.in
│   │   ├── pyproject.toml
│   │   ├── qlib
│   │   │   ├── __init__.py
│   │   │   ├── backtest
│   │   │   │   ├── __init__.py
│   │   │   │   ├── account.py
│   │   │   │   ├── backtest.py
│   │   │   │   ├── decision.py
│   │   │   │   ├── exchange.py
│   │   │   │   ├── executor.py
│   │   │   │   ├── high_performance_ds.py
│   │   │   │   ├── position.py
│   │   │   │   ├── profit_attribution.py
│   │   │   │   ├── report.py
│   │   │   │   ├── signal.py
│   │   │   │   └── utils.py
│   │   │   ├── cli
│   │   │   │   ├── __init__.py
│   │   │   │   ├── data.py
│   │   │   │   └── run.py
│   │   │   ├── config.py
│   │   │   ├── constant.py
│   │   │   ├── contrib
│   │   │   │   ├── __init__.py
│   │   │   │   ├── data
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── data.py
│   │   │   │   │   ├── dataset.py
│   │   │   │   │   ├── handler.py
│   │   │   │   │   ├── highfreq_handler.py
│   │   │   │   │   ├── highfreq_processor.py
│   │   │   │   │   ├── highfreq_provider.py
│   │   │   │   │   ├── loader.py
│   │   │   │   │   ├── processor.py
│   │   │   │   │   └── utils
│   │   │   │   │       ├── __init__.py
│   │   │   │   │       └── sepdf.py
│   │   │   │   ├── eva
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   └── alpha.py
│   │   │   │   ├── evaluate_portfolio.py
│   │   │   │   ├── evaluate.py
│   │   │   │   ├── meta
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   └── data_selection
│   │   │   │   │       ├── __init__.py
│   │   │   │   │       ├── dataset.py
│   │   │   │   │       ├── model.py
│   │   │   │   │       ├── net.py
│   │   │   │   │       └── utils.py
│   │   │   │   ├── model
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── catboost_model.py
│   │   │   │   │   ├── double_ensemble.py
│   │   │   │   │   ├── gbdt.py
│   │   │   │   │   ├── highfreq_gdbt_model.py
│   │   │   │   │   ├── linear.py
│   │   │   │   │   ├── pytorch_adarnn.py
│   │   │   │   │   ├── pytorch_add.py
│   │   │   │   │   ├── pytorch_alstm_ts.py
│   │   │   │   │   ├── pytorch_alstm.py
│   │   │   │   │   ├── pytorch_gats_ts.py
│   │   │   │   │   ├── pytorch_gats.py
│   │   │   │   │   ├── pytorch_general_nn.py
│   │   │   │   │   ├── pytorch_gru_ts.py
│   │   │   │   │   ├── pytorch_gru.py
│   │   │   │   │   ├── pytorch_hist.py
│   │   │   │   │   ├── pytorch_igmtf.py
│   │   │   │   │   ├── pytorch_krnn.py
│   │   │   │   │   ├── pytorch_localformer_ts.py
│   │   │   │   │   ├── pytorch_localformer.py
│   │   │   │   │   ├── pytorch_lstm_ts.py
│   │   │   │   │   ├── pytorch_lstm.py
│   │   │   │   │   ├── pytorch_nn.py
│   │   │   │   │   ├── pytorch_sandwich.py
│   │   │   │   │   ├── pytorch_sfm.py
│   │   │   │   │   ├── pytorch_tabnet.py
│   │   │   │   │   ├── pytorch_tcn_ts.py
│   │   │   │   │   ├── pytorch_tcn.py
│   │   │   │   │   ├── pytorch_tcts.py
│   │   │   │   │   ├── pytorch_tra.py
│   │   │   │   │   ├── pytorch_transformer_ts.py
│   │   │   │   │   ├── pytorch_transformer.py
│   │   │   │   │   ├── pytorch_utils.py
│   │   │   │   │   ├── tcn.py
│   │   │   │   │   └── xgboost.py
│   │   │   │   ├── online
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── manager.py
│   │   │   │   │   ├── online_model.py
│   │   │   │   │   ├── operator.py
│   │   │   │   │   ├── user.py
│   │   │   │   │   └── utils.py
│   │   │   │   ├── ops
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   └── high_freq.py
│   │   │   │   ├── report
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── analysis_model
│   │   │   │   │   │   ├── __init__.py
│   │   │   │   │   │   └── analysis_model_performance.py
│   │   │   │   │   ├── analysis_position
│   │   │   │   │   │   ├── __init__.py
│   │   │   │   │   │   ├── cumulative_return.py
│   │   │   │   │   │   ├── parse_position.py
│   │   │   │   │   │   ├── rank_label.py
│   │   │   │   │   │   ├── report.py
│   │   │   │   │   │   ├── risk_analysis.py
│   │   │   │   │   │   └── score_ic.py
│   │   │   │   │   ├── data
│   │   │   │   │   │   ├── __init__.py
│   │   │   │   │   │   ├── ana.py
│   │   │   │   │   │   └── base.py
│   │   │   │   │   ├── graph.py
│   │   │   │   │   └── utils.py
│   │   │   │   ├── rolling
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── __main__.py
│   │   │   │   │   ├── base.py
│   │   │   │   │   └── ddgda.py
│   │   │   │   ├── strategy
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── cost_control.py
│   │   │   │   │   ├── optimizer
│   │   │   │   │   │   ├── __init__.py
│   │   │   │   │   │   ├── base.py
│   │   │   │   │   │   ├── enhanced_indexing.py
│   │   │   │   │   │   └── optimizer.py
│   │   │   │   │   ├── order_generator.py
│   │   │   │   │   ├── rule_strategy.py
│   │   │   │   │   └── signal_strategy.py
│   │   │   │   ├── torch.py
│   │   │   │   ├── tuner
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── config.py
│   │   │   │   │   ├── launcher.py
│   │   │   │   │   ├── pipeline.py
│   │   │   │   │   ├── space.py
│   │   │   │   │   └── tuner.py
│   │   │   │   └── workflow
│   │   │   │       ├── __init__.py
│   │   │   │       └── record_temp.py
│   │   │   ├── data
│   │   │   │   ├── __init__.py
│   │   │   │   ├── _libs
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── expanding.pyx
│   │   │   │   │   └── rolling.pyx
│   │   │   │   ├── base.py
│   │   │   │   ├── cache.py
│   │   │   │   ├── client.py
│   │   │   │   ├── data.py
│   │   │   │   ├── dataset
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── handler.py
│   │   │   │   │   ├── loader.py
│   │   │   │   │   ├── processor.py
│   │   │   │   │   ├── storage.py
│   │   │   │   │   ├── utils.py
│   │   │   │   │   └── weight.py
│   │   │   │   ├── filter.py
│   │   │   │   ├── inst_processor.py
│   │   │   │   ├── ops.py
│   │   │   │   ├── pit.py
│   │   │   │   └── storage
│   │   │   │       ├── __init__.py
│   │   │   │       ├── file_storage.py
│   │   │   │       └── storage.py
│   │   │   ├── log.py
│   │   │   ├── model
│   │   │   │   ├── __init__.py
│   │   │   │   ├── base.py
│   │   │   │   ├── ens
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── ensemble.py
│   │   │   │   │   └── group.py
│   │   │   │   ├── interpret
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   └── base.py
│   │   │   │   ├── meta
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── dataset.py
│   │   │   │   │   ├── model.py
│   │   │   │   │   └── task.py
│   │   │   │   ├── riskmodel
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── base.py
│   │   │   │   │   ├── poet.py
│   │   │   │   │   ├── shrink.py
│   │   │   │   │   └── structured.py
│   │   │   │   ├── trainer.py
│   │   │   │   └── utils.py
│   │   │   ├── rl
│   │   │   │   ├── __init__.py
│   │   │   │   ├── aux_info.py
│   │   │   │   ├── contrib
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── backtest.py
│   │   │   │   │   ├── naive_config_parser.py
│   │   │   │   │   ├── train_onpolicy.py
│   │   │   │   │   └── utils.py
│   │   │   │   ├── data
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── base.py
│   │   │   │   │   ├── integration.py
│   │   │   │   │   ├── native.py
│   │   │   │   │   └── pickle_styled.py
│   │   │   │   ├── interpreter.py
│   │   │   │   ├── order_execution
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── interpreter.py
│   │   │   │   │   ├── network.py
│   │   │   │   │   ├── policy.py
│   │   │   │   │   ├── reward.py
│   │   │   │   │   ├── simulator_qlib.py
│   │   │   │   │   ├── simulator_simple.py
│   │   │   │   │   ├── state.py
│   │   │   │   │   ├── strategy.py
│   │   │   │   │   └── utils.py
│   │   │   │   ├── reward.py
│   │   │   │   ├── seed.py
│   │   │   │   ├── simulator.py
│   │   │   │   ├── strategy
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   └── single_order.py
│   │   │   │   ├── trainer
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── api.py
│   │   │   │   │   ├── callbacks.py
│   │   │   │   │   ├── trainer.py
│   │   │   │   │   └── vessel.py
│   │   │   │   └── utils
│   │   │   │       ├── __init__.py
│   │   │   │       ├── data_queue.py
│   │   │   │       ├── env_wrapper.py
│   │   │   │       ├── finite_env.py
│   │   │   │       └── log.py
│   │   │   ├── strategy
│   │   │   │   ├── __init__.py
│   │   │   │   └── base.py
│   │   │   ├── tests
│   │   │   │   ├── __init__.py
│   │   │   │   ├── config.py
│   │   │   │   ├── data.py
│   │   │   │   └── test_config_validation.py
│   │   │   ├── typehint.py
│   │   │   ├── utils
│   │   │   │   ├── __init__.py
│   │   │   │   ├── data.py
│   │   │   │   ├── exceptions.py
│   │   │   │   ├── file.py
│   │   │   │   ├── index_data.py
│   │   │   │   ├── mod.py
│   │   │   │   ├── objm.py
│   │   │   │   ├── paral.py
│   │   │   │   ├── pickle_utils.py
│   │   │   │   ├── resam.py
│   │   │   │   ├── serial.py
│   │   │   │   └── time.py
│   │   │   └── workflow
│   │   │       ├── __init__.py
│   │   │       ├── exp.py
│   │   │       ├── expm.py
│   │   │       ├── online
│   │   │       │   ├── __init__.py
│   │   │       │   ├── manager.py
│   │   │       │   ├── strategy.py
│   │   │       │   ├── update.py
│   │   │       │   └── utils.py
│   │   │       ├── record_temp.py
│   │   │       ├── recorder.py
│   │   │       ├── task
│   │   │       │   ├── __init__.py
│   │   │       │   ├── collect.py
│   │   │       │   ├── gen.py
│   │   │       │   ├── manage.py
│   │   │       │   └── utils.py
│   │   │       └── utils.py
│   │   ├── README.md
│   │   ├── scripts
│   │   │   ├── check_data_health.py
│   │   │   ├── check_dump_bin.py
│   │   │   ├── collect_info.py
│   │   │   ├── data_collector
│   │   │   │   ├── baostock_5min
│   │   │   │   │   ├── collector.py
│   │   │   │   │   ├── README.md
│   │   │   │   │   └── requirements.txt
│   │   │   │   ├── base.py
│   │   │   │   ├── br_index
│   │   │   │   │   ├── collector.py
│   │   │   │   │   ├── README.md
│   │   │   │   │   └── requirements.txt
│   │   │   │   ├── cn_index
│   │   │   │   │   ├── collector.py
│   │   │   │   │   ├── README.md
│   │   │   │   │   └── requirements.txt
│   │   │   │   ├── contrib
│   │   │   │   │   ├── fill_cn_1min_data
│   │   │   │   │   │   ├── fill_cn_1min_data.py
│   │   │   │   │   │   ├── README.md
│   │   │   │   │   │   └── requirements.txt
│   │   │   │   │   └── future_trading_date_collector
│   │   │   │   │       ├── future_trading_date_collector.py
│   │   │   │   │       ├── README.md
│   │   │   │   │       └── requirements.txt
│   │   │   │   ├── crowd_source
│   │   │   │   │   └── README.md
│   │   │   │   ├── crypto
│   │   │   │   │   ├── collector.py
│   │   │   │   │   ├── README.md
│   │   │   │   │   └── requirement.txt
│   │   │   │   ├── fund
│   │   │   │   │   ├── collector.py
│   │   │   │   │   ├── README.md
│   │   │   │   │   └── requirements.txt
│   │   │   │   ├── future_calendar_collector.py
│   │   │   │   ├── index.py
│   │   │   │   ├── pit
│   │   │   │   │   ├── collector.py
│   │   │   │   │   ├── README.md
│   │   │   │   │   └── requirements.txt
│   │   │   │   ├── README.md
│   │   │   │   ├── us_index
│   │   │   │   │   ├── collector.py
│   │   │   │   │   ├── README.md
│   │   │   │   │   └── requirements.txt
│   │   │   │   ├── utils.py
│   │   │   │   └── yahoo
│   │   │   │       ├── collector.py
│   │   │   │       ├── README.md
│   │   │   │       └── requirements.txt
│   │   │   ├── dump_bin.py
│   │   │   ├── dump_pit.py
│   │   │   ├── get_data.py
│   │   │   └── README.md
│   │   ├── SECURITY.md
│   │   ├── setup.py
│   │   └── tests
│   │       ├── backtest
│   │       │   ├── test_file_strategy.py
│   │       │   ├── test_high_freq_trading.py
│   │       │   ├── test_soft_topk_strategy_cold_start.py
│   │       │   └── test_soft_topk_strategy.py
│   │       ├── conftest.py
│   │       ├── data_mid_layer_tests
│   │       │   ├── README.md
│   │       │   ├── test_dataloader.py
│   │       │   ├── test_dataset.py
│   │       │   ├── test_handler_storage.py
│   │       │   ├── test_handler.py
│   │       │   └── test_processor.py
│   │       ├── dataset_tests
│   │       │   ├── README.md
│   │       │   └── test_datalayer.py
│   │       ├── dependency_tests
│   │       │   ├── README.md
│   │       │   └── test_mlflow.py
│   │       ├── misc
│   │       │   ├── test_get_multi_proc.py
│   │       │   ├── test_index_data.py
│   │       │   ├── test_sepdf.py
│   │       │   └── test_utils.py
│   │       ├── model
│   │       │   └── test_general_nn.py
│   │       ├── ops
│   │       │   ├── test_elem_operator.py
│   │       │   └── test_special_ops.py
│   │       ├── pytest.ini
│   │       ├── rl
│   │       │   ├── test_data_queue.py
│   │       │   ├── test_finite_env.py
│   │       │   ├── test_logger.py
│   │       │   ├── test_qlib_simulator.py
│   │       │   ├── test_saoe_simple.py
│   │       │   └── test_trainer.py
│   │       ├── rolling_tests
│   │       │   └── test_update_pred.py
│   │       ├── storage_tests
│   │       │   └── test_storage.py
│   │       ├── test_all_pipeline.py
│   │       ├── test_contrib_model.py
│   │       ├── test_contrib_workflow.py
│   │       ├── test_dump_data.py
│   │       ├── test_get_data.py
│   │       ├── test_pit.py
│   │       ├── test_register_ops.py
│   │       ├── test_structured_cov_estimator.py
│   │       └── test_workflow.py
│   ├── skfolio
│   │   ├── CHANGELOG.md
│   │   ├── CODE_OF_CONDUCT.md
│   │   ├── codecov.yml
│   │   ├── CONTRIBUTING.md
│   │   ├── Dockerfile
│   │   ├── docs
│   │   │   ├── _static
│   │   │   │   ├── apple-touch-icon.png
│   │   │   │   ├── css
│   │   │   │   │   └── custom.css
│   │   │   │   ├── expo-1000.jpg
│   │   │   │   ├── expo-1000.webp
│   │   │   │   ├── expo-750.jpg
│   │   │   │   ├── expo-750.webp
│   │   │   │   ├── expo.jpg
│   │   │   │   ├── expo.webp
│   │   │   │   ├── favicon-144.png
│   │   │   │   ├── favicon-16.png
│   │   │   │   ├── favicon-48.png
│   │   │   │   ├── favicon-96.png
│   │   │   │   ├── favicon.ico
│   │   │   │   ├── favicon.svg
│   │   │   │   └── logo_animate.svg
│   │   │   ├── _templates
│   │   │   │   └── layout.html
│   │   │   ├── api.rst
│   │   │   ├── binder
│   │   │   │   └── requirements.txt
│   │   │   ├── conf.py
│   │   │   ├── index.rst
│   │   │   ├── jupyter-lite.json
│   │   │   ├── make.bat
│   │   │   ├── Makefile
│   │   │   ├── robots.txt
│   │   │   └── user_guide
│   │   │       ├── cluster.rst
│   │   │       ├── covariance.rst
│   │   │       ├── cross_sectional_transformers.rst
│   │   │       ├── data_preparation.rst
│   │   │       ├── datasets.rst
│   │   │       ├── distance.rst
│   │   │       ├── expected_returns.rst
│   │   │       ├── hyper_parameters_tuning.rst
│   │   │       ├── index.rst
│   │   │       ├── install.rst
│   │   │       ├── metadata_routing.rst
│   │   │       ├── model_selection.rst
│   │   │       ├── online_learning.rst
│   │   │       ├── optimization.rst
│   │   │       ├── population.rst
│   │   │       ├── portfolio.rst
│   │   │       ├── pre_selection.rst
│   │   │       ├── prior.rst
│   │   │       ├── uncertainty_set.rst
│   │   │       └── variance.rst
│   │   ├── examples
│   │   │   ├── clustering
│   │   │   │   ├── plot_1_hrp_cvar.py
│   │   │   │   ├── plot_2_herc_cdar.py
│   │   │   │   ├── plot_3_hrp_vs_herc.py
│   │   │   │   ├── plot_4_nco.py
│   │   │   │   ├── plot_5_nco_grid_search.py
│   │   │   │   ├── plot_6_schur.py
│   │   │   │   └── README.txt
│   │   │   ├── data_preparation
│   │   │   │   ├── plot_1_investment_horizon.py
│   │   │   │   └── README.txt
│   │   │   ├── distributionally_robust_cvar
│   │   │   │   ├── plot_1_distributionally_robust_cvar.py
│   │   │   │   └── README.txt
│   │   │   ├── ensemble
│   │   │   │   ├── plot_1_stacking.py
│   │   │   │   └── README.txt
│   │   │   ├── entropy_pooling
│   │   │   │   ├── plot_1_entropy_pooling.py
│   │   │   │   ├── plot_2_opinion_pooling.py
│   │   │   │   └── README.txt
│   │   │   ├── images
│   │   │   │   └── incomplete_dataset.png
│   │   │   ├── maximum_diversification
│   │   │   │   ├── plot_1_maximum_diversification.py
│   │   │   │   └── README.txt
│   │   │   ├── mean_risk
│   │   │   │   ├── plot_1_maximum_sharpe_ratio.py
│   │   │   │   ├── plot_10_tracking_error.py
│   │   │   │   ├── plot_11_empirical_prior.py
│   │   │   │   ├── plot_12_black_and_litterman.py
│   │   │   │   ├── plot_13_factor_model.py
│   │   │   │   ├── plot_14_black_litterman_factor_model.py
│   │   │   │   ├── plot_15_mip_cardinality_constraints.py
│   │   │   │   ├── plot_16_mip_threshold_constraints.py
│   │   │   │   ├── plot_17_failure_and_fallbacks.py
│   │   │   │   ├── plot_2_minimum_CVaR.py
│   │   │   │   ├── plot_3_efficient_frontier.py
│   │   │   │   ├── plot_4_mean_variance_cdar.py
│   │   │   │   ├── plot_5_weight_constraints.py
│   │   │   │   ├── plot_6_transaction_costs.py
│   │   │   │   ├── plot_7_management_fees.py
│   │   │   │   ├── plot_8_regularization.py
│   │   │   │   ├── plot_9_uncertainty_set.py
│   │   │   │   └── README.txt
│   │   │   ├── metadata_routing
│   │   │   │   ├── plot_1_implied_volatility.py
│   │   │   │   └── README.txt
│   │   │   ├── model_selection
│   │   │   │   ├── plot_1_multiple_randomized_cv.py
│   │   │   │   └── README.txt
│   │   │   ├── online_learning
│   │   │   │   ├── plot_1_online_covariance_forecast_evaluation.py
│   │   │   │   ├── plot_2_online_hyperparameter_tuning.py
│   │   │   │   ├── plot_3_online_portfolio_optimization_evaluation.py
│   │   │   │   └── README.txt
│   │   │   ├── pre_selection
│   │   │   │   ├── plot_1_drop_correlated.py
│   │   │   │   ├── plot_2_select_best_performers.py
│   │   │   │   ├── plot_3_custom_pre_selection_volumes.py
│   │   │   │   ├── plot_4_incomplete_dataset.py
│   │   │   │   └── README.txt
│   │   │   ├── README.txt
│   │   │   ├── risk_budgeting
│   │   │   │   ├── plot_1_risk_parity_variance.py
│   │   │   │   ├── plot_2_risk_budgeting_CVaR.py
│   │   │   │   ├── plot_3_risk_parity_ledoit_wolf.py
│   │   │   │   └── README.txt
│   │   │   └── synthetic_data
│   │   │       ├── plot_1_bivariate_copulas.py
│   │   │       ├── plot_2_vine_copula.py
│   │   │       ├── plot_3_min_CVaR_stressed_factors.py
│   │   │       └── README.txt
│   │   ├── LICENSE
│   │   ├── Makefile
│   │   ├── MANIFEST.in
│   │   ├── pyproject.toml
│   │   ├── README.rst
│   │   ├── SECURITY.md
│   │   ├── src
│   │   │   └── skfolio
│   │   │       ├── __init__.py
│   │   │       ├── _constants.py
│   │   │       ├── cluster
│   │   │       │   ├── __init__.py
│   │   │       │   └── _hierarchical.py
│   │   │       ├── datasets
│   │   │       │   ├── __init__.py
│   │   │       │   ├── _base.py
│   │   │       │   └── data
│   │   │       │       ├── __init__.py
│   │   │       │       ├── factors_dataset.csv.gz
│   │   │       │       ├── sp500_dataset.csv.gz
│   │   │       │       └── sp500_index.csv.gz
│   │   │       ├── distance
│   │   │       │   ├── __init__.py
│   │   │       │   ├── _base.py
│   │   │       │   └── _distance.py
│   │   │       ├── distribution
│   │   │       │   ├── __init__.py
│   │   │       │   ├── _base.py
│   │   │       │   ├── copula
│   │   │       │   │   ├── __init__.py
│   │   │       │   │   ├── _base.py
│   │   │       │   │   ├── _clayton.py
│   │   │       │   │   ├── _gaussian.py
│   │   │       │   │   ├── _gumbel.py
│   │   │       │   │   ├── _independent.py
│   │   │       │   │   ├── _joe.py
│   │   │       │   │   ├── _selection.py
│   │   │       │   │   ├── _student_t.py
│   │   │       │   │   └── _utils.py
│   │   │       │   ├── multivariate
│   │   │       │   │   ├── __init__.py
│   │   │       │   │   ├── _base.py
│   │   │       │   │   ├── _utils.py
│   │   │       │   │   └── _vine_copula.py
│   │   │       │   └── univariate
│   │   │       │       ├── __init__.py
│   │   │       │       ├── _base.py
│   │   │       │       ├── _gaussian.py
│   │   │       │       ├── _johnson_su.py
│   │   │       │       ├── _normal_inverse_gaussian.py
│   │   │       │       ├── _selection.py
│   │   │       │       └── _student_t.py
│   │   │       ├── exceptions.py
│   │   │       ├── linear_model
│   │   │       │   ├── __init__.py
│   │   │       │   └── _cross_sectional
│   │   │       │       ├── __init__.py
│   │   │       │       ├── _base.py
│   │   │       │       ├── _cs_linear_regression.py
│   │   │       │       └── _cs_linear_regressor_wrapper.py
│   │   │       ├── measures
│   │   │       │   ├── __init__.py
│   │   │       │   ├── _enums.py
│   │   │       │   └── _measures.py
│   │   │       ├── metrics
│   │   │       │   ├── __init__.py
│   │   │       │   ├── _covariance.py
│   │   │       │   └── _scorer.py
│   │   │       ├── model_selection
│   │   │       │   ├── __init__.py
│   │   │       │   ├── _combinatorial.py
│   │   │       │   ├── _covariance_forecast_evaluation.py
│   │   │       │   ├── _multiple_randomized_cv.py
│   │   │       │   ├── _online
│   │   │       │   │   ├── __init__.py
│   │   │       │   │   ├── _covariance_forecast_evaluation.py
│   │   │       │   │   ├── _search.py
│   │   │       │   │   └── _validation.py
│   │   │       │   ├── _validation.py
│   │   │       │   └── _walk_forward.py
│   │   │       ├── moments
│   │   │       │   ├── __init__.py
│   │   │       │   ├── covariance
│   │   │       │   │   ├── __init__.py
│   │   │       │   │   ├── _base.py
│   │   │       │   │   ├── _denoise_covariance.py
│   │   │       │   │   ├── _detone_covariance.py
│   │   │       │   │   ├── _empirical_covariance.py
│   │   │       │   │   ├── _ew_covariance.py
│   │   │       │   │   ├── _gerber_covariance.py
│   │   │       │   │   ├── _graphical_lasso_cv.py
│   │   │       │   │   ├── _implied_covariance.py
│   │   │       │   │   ├── _ledoit_wolf.py
│   │   │       │   │   ├── _oas.py
│   │   │       │   │   ├── _regime_adjusted_ew_covariance.py
│   │   │       │   │   └── _shrunk_covariance.py
│   │   │       │   ├── expected_returns
│   │   │       │   │   ├── __init__.py
│   │   │       │   │   ├── _base.py
│   │   │       │   │   ├── _empirical_mu.py
│   │   │       │   │   ├── _equilibrium_mu.py
│   │   │       │   │   ├── _ew_mu.py
│   │   │       │   │   └── _shrunk_mu.py
│   │   │       │   └── variance
│   │   │       │       ├── __init__.py
│   │   │       │       ├── _base.py
│   │   │       │       ├── _empirical_variance.py
│   │   │       │       ├── _ew_variance.py
│   │   │       │       └── _regime_adjusted_ew_variance.py
│   │   │       ├── optimization
│   │   │       │   ├── __init__.py
│   │   │       │   ├── _base.py
│   │   │       │   ├── cluster
│   │   │       │   │   ├── __init__.py
│   │   │       │   │   ├── _nco.py
│   │   │       │   │   └── hierarchical
│   │   │       │   │       ├── __init__.py
│   │   │       │   │       ├── _base.py
│   │   │       │   │       ├── _herc.py
│   │   │       │   │       ├── _hrp.py
│   │   │       │   │       └── _schur.py
│   │   │       │   ├── convex
│   │   │       │   │   ├── __init__.py
│   │   │       │   │   ├── _base.py
│   │   │       │   │   ├── _benchmark_tracker.py
│   │   │       │   │   ├── _distributionally_robust.py
│   │   │       │   │   ├── _maximum_diversification.py
│   │   │       │   │   ├── _mean_risk.py
│   │   │       │   │   └── _risk_budgeting.py
│   │   │       │   ├── ensemble
│   │   │       │   │   ├── __init__.py
│   │   │       │   │   └── _stacking.py
│   │   │       │   └── naive
│   │   │       │       ├── __init__.py
│   │   │       │       └── _naive.py
│   │   │       ├── population
│   │   │       │   ├── __init__.py
│   │   │       │   └── _population.py
│   │   │       ├── portfolio
│   │   │       │   ├── __init__.py
│   │   │       │   ├── _base.py
│   │   │       │   ├── _failed_portfolio.py
│   │   │       │   ├── _multi_period_portfolio.py
│   │   │       │   └── _portfolio.py
│   │   │       ├── pre_selection
│   │   │       │   ├── __init__.py
│   │   │       │   ├── _drop_correlated.py
│   │   │       │   ├── _drop_zero_variance.py
│   │   │       │   ├── _select_complete.py
│   │   │       │   ├── _select_k_extremes.py
│   │   │       │   ├── _select_non_dominated.py
│   │   │       │   └── _select_non_expiring.py
│   │   │       ├── preprocessing
│   │   │       │   ├── __init__.py
│   │   │       │   ├── _returns.py
│   │   │       │   └── _transformer
│   │   │       │       ├── __init__.py
│   │   │       │       └── _cross_sectional
│   │   │       │           ├── __init__.py
│   │   │       │           ├── _base.py
│   │   │       │           ├── _cs_gaussian_rank_scaler.py
│   │   │       │           ├── _cs_percentile_rank_scaler.py
│   │   │       │           ├── _cs_standard_scaler.py
│   │   │       │           ├── _cs_tanh_shrinker.py
│   │   │       │           ├── _cs_winsorizer.py
│   │   │       │           └── _utils.py
│   │   │       ├── prior
│   │   │       │   ├── __init__.py
│   │   │       │   ├── _base.py
│   │   │       │   ├── _black_litterman.py
│   │   │       │   ├── _empirical.py
│   │   │       │   ├── _entropy_pooling.py
│   │   │       │   ├── _opinion_pooling.py
│   │   │       │   ├── _synthetic_data.py
│   │   │       │   └── _time_series_factor_model.py
│   │   │       ├── typing.py
│   │   │       ├── uncertainty_set
│   │   │       │   ├── __init__.py
│   │   │       │   ├── _base.py
│   │   │       │   ├── _bootstrap.py
│   │   │       │   └── _empirical.py
│   │   │       └── utils
│   │   │           ├── __init__.py
│   │   │           ├── _array_buffer.py
│   │   │           ├── bootstrap.py
│   │   │           ├── composition.py
│   │   │           ├── equations.py
│   │   │           ├── figure.py
│   │   │           ├── sorting.py
│   │   │           ├── stats.py
│   │   │           ├── tools.py
│   │   │           └── validation.py
│   │   └── tests
│   │       ├── __init__.py
│   │       ├── conftest.py
│   │       ├── test_cluster
│   │       │   ├── __init__.py
│   │       │   └── test_hierarchical.py
│   │       ├── test_dataset
│   │       │   ├── __init__.py
│   │       │   └── test_dataset.py
│   │       ├── test_distance
│   │       │   ├── __init__.py
│   │       │   └── test_distance.py
│   │       ├── test_distribution
│   │       │   ├── __init__.py
│   │       │   ├── test_copula
│   │       │   │   ├── __init__.py
│   │       │   │   ├── test_base.py
│   │       │   │   ├── test_clayton.py
│   │       │   │   ├── test_gaussian.py
│   │       │   │   ├── test_gumbel.py
│   │       │   │   ├── test_independent.py
│   │       │   │   ├── test_joe.py
│   │       │   │   ├── test_selection.py
│   │       │   │   ├── test_student_t.py
│   │       │   │   └── test_utils.py
│   │       │   ├── test_multivariate
│   │       │   │   ├── __init__.py
│   │       │   │   ├── test_utils.py
│   │       │   │   └── test_vine_copula.py
│   │       │   └── test_univariate
│   │       │       ├── __init__.py
│   │       │       ├── test_base.py
│   │       │       ├── test_gaussian.py
│   │       │       ├── test_johnson_su.py
│   │       │       ├── test_normal_inverse_gaussian.py
│   │       │       ├── test_selection.py
│   │       │       └── test_student_t.py
│   │       ├── test_linear_model
│   │       │   ├── __init__.py
│   │       │   └── test_cross_sectional
│   │       │       ├── __init__.py
│   │       │       ├── test_cs_linear_regression.py
│   │       │       └── test_cs_linear_regressor_wrapper.py
│   │       ├── test_measures
│   │       │   ├── __init__.py
│   │       │   └── test_measures.py
│   │       ├── test_metrics
│   │       │   ├── __init__.py
│   │       │   ├── test_covariance.py
│   │       │   └── test_scorer.py
│   │       ├── test_model_selection
│   │       │   ├── __init__.py
│   │       │   ├── test_combinatorial.py
│   │       │   ├── test_covariance_evaluation.py
│   │       │   ├── test_multiple_randomized_cv.py
│   │       │   ├── test_online
│   │       │   │   ├── __init__.py
│   │       │   │   ├── test_covariance_evaluation.py
│   │       │   │   ├── test_search.py
│   │       │   │   └── test_validation.py
│   │       │   ├── test_validation.py
│   │       │   └── test_walk_forward.py
│   │       ├── test_moment
│   │       │   ├── __init__.py
│   │       │   ├── test_covariance
│   │       │   │   ├── __init__.py
│   │       │   │   ├── test_covariance.py
│   │       │   │   ├── test_ew_covariance.py
│   │       │   │   ├── test_implied_covariance.py
│   │       │   │   └── test_regime_adjusted_ew_covariance.py
│   │       │   ├── test_expected_returns
│   │       │   │   ├── __init__.py
│   │       │   │   └── test_expected_returns.py
│   │       │   └── test_variance
│   │       │       ├── __init__.py
│   │       │       ├── test_empirical_variance.py
│   │       │       ├── test_ew_variance.py
│   │       │       └── test_regime_adjusted_ew_variance.py
│   │       ├── test_optimization
│   │       │   ├── __init__.py
│   │       │   ├── test_cluster
│   │       │   │   ├── __init__.py
│   │       │   │   ├── test_hierarchical
│   │       │   │   │   ├── __init__.py
│   │       │   │   │   ├── test_herc.py
│   │       │   │   │   ├── test_hrp.py
│   │       │   │   │   └── test_schur.py
│   │       │   │   └── test_nco.py
│   │       │   ├── test_convex
│   │       │   │   ├── __init__.py
│   │       │   │   ├── test_benchmark_tracker.py
│   │       │   │   ├── test_distributionally_robust_cvar.py
│   │       │   │   ├── test_maximum_diversification.py
│   │       │   │   ├── test_mean_risk.py
│   │       │   │   └── test_risk_budgeting.py
│   │       │   ├── test_ensemble
│   │       │   │   ├── __init__.py
│   │       │   │   └── test_stacking.py
│   │       │   ├── test_fallback.py
│   │       │   └── test_naive
│   │       │       ├── __init__.py
│   │       │       └── test_naive.py
│   │       ├── test_pipeline
│   │       │   ├── __init__.py
│   │       │   └── test_pipeline.py
│   │       ├── test_population
│   │       │   ├── __init__.py
│   │       │   └── test_population.py
│   │       ├── test_portfolio
│   │       │   ├── __init__.py
│   │       │   ├── test_failed_portfolio.py
│   │       │   ├── test_multi_period_portfolio.py
│   │       │   └── test_portfolio.py
│   │       ├── test_pre_selection
│   │       │   ├── __init__.py
│   │       │   ├── test_drop_high_correlation.py
│   │       │   ├── test_drop_zero_variance.py
│   │       │   ├── test_select_complete.py
│   │       │   ├── test_select_k_extremes.py
│   │       │   ├── test_select_non_dominated.py
│   │       │   └── test_select_non_expiring.py
│   │       ├── test_preprocessing
│   │       │   ├── __init__.py
│   │       │   ├── test_returns.py
│   │       │   └── test_transformer
│   │       │       ├── __init__.py
│   │       │       └── test_cross_sectional
│   │       │           ├── __init__.py
│   │       │           ├── test_base.py
│   │       │           ├── test_cs_gaussian_rank_scaler.py
│   │       │           ├── test_cs_percentile_rank_scaler.py
│   │       │           ├── test_cs_standard_scaler.py
│   │       │           ├── test_cs_tanh_shrinker.py
│   │       │           └── test_cs_winsorizer.py
│   │       ├── test_prior
│   │       │   ├── __init__.py
│   │       │   ├── test_black_litterman.py
│   │       │   ├── test_empirical.py
│   │       │   ├── test_entropy_pooling.py
│   │       │   ├── test_opinion_pooling.py
│   │       │   ├── test_synthetic_data.py
│   │       │   └── test_time_series_factor_model.py
│   │       ├── test_uncertainty_set
│   │       │   ├── __init__.py
│   │       │   ├── test_bootstrap.py
│   │       │   └── test_empirical.py
│   │       └── test_utils
│   │           ├── __init__.py
│   │           ├── test_array_buffer.py
│   │           ├── test_bootstrap.py
│   │           ├── test_equations.py
│   │           ├── test_figure.py
│   │           ├── test_sorting.py
│   │           ├── test_stats.py
│   │           ├── test_tools.py
│   │           └── test_validation.py
│   ├── stable-baselines3-contrib
│   │   ├── CITATION.bib
│   │   ├── CONTRIBUTING.md
│   │   ├── docs
│   │   │   ├── _static
│   │   │   │   ├── css
│   │   │   │   │   └── baselines_theme.css
│   │   │   │   └── img
│   │   │   │       ├── colab-badge.svg
│   │   │   │       ├── colab.svg
│   │   │   │       └── logo.png
│   │   │   ├── common
│   │   │   │   ├── torch_layers.md
│   │   │   │   ├── utils.md
│   │   │   │   └── wrappers.md
│   │   │   ├── conda_env.yml
│   │   │   ├── conf.py
│   │   │   ├── guide
│   │   │   │   ├── algos.md
│   │   │   │   ├── examples.md
│   │   │   │   └── install.md
│   │   │   ├── images
│   │   │   │   ├── 10x10_combined.png
│   │   │   │   ├── 10x10_mask.png
│   │   │   │   ├── 10x10_no_mask.png
│   │   │   │   ├── 4x4_combined.png
│   │   │   │   ├── 4x4_mask.png
│   │   │   │   ├── 4x4_no_mask.png
│   │   │   │   └── crossQ_performance.png
│   │   │   ├── index.rst
│   │   │   ├── make.bat
│   │   │   ├── Makefile
│   │   │   ├── misc
│   │   │   │   └── changelog.md
│   │   │   ├── modules
│   │   │   │   ├── ars.md
│   │   │   │   ├── crossq.md
│   │   │   │   ├── ppo_mask.md
│   │   │   │   ├── ppo_recurrent.md
│   │   │   │   ├── qrdqn.md
│   │   │   │   ├── tqc.md
│   │   │   │   └── trpo.md
│   │   │   ├── README.md
│   │   │   └── spelling_wordlist.txt
│   │   ├── LICENSE
│   │   ├── Makefile
│   │   ├── pyproject.toml
│   │   ├── README.md
│   │   ├── sb3_contrib
│   │   │   ├── __init__.py
│   │   │   ├── ars
│   │   │   │   ├── __init__.py
│   │   │   │   ├── ars.py
│   │   │   │   └── policies.py
│   │   │   ├── common
│   │   │   │   ├── __init__.py
│   │   │   │   ├── envs
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   └── invalid_actions_env.py
│   │   │   │   ├── maskable
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── buffers.py
│   │   │   │   │   ├── callbacks.py
│   │   │   │   │   ├── distributions.py
│   │   │   │   │   ├── evaluation.py
│   │   │   │   │   ├── policies.py
│   │   │   │   │   └── utils.py
│   │   │   │   ├── recurrent
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── buffers.py
│   │   │   │   │   ├── policies.py
│   │   │   │   │   └── type_aliases.py
│   │   │   │   ├── torch_layers.py
│   │   │   │   ├── utils.py
│   │   │   │   ├── vec_env
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   └── async_eval.py
│   │   │   │   └── wrappers
│   │   │   │       ├── __init__.py
│   │   │   │       ├── action_masker.py
│   │   │   │       └── time_feature.py
│   │   │   ├── crossq
│   │   │   │   ├── __init__.py
│   │   │   │   ├── crossq.py
│   │   │   │   └── policies.py
│   │   │   ├── ppo_mask
│   │   │   │   ├── __init__.py
│   │   │   │   ├── policies.py
│   │   │   │   └── ppo_mask.py
│   │   │   ├── ppo_recurrent
│   │   │   │   ├── __init__.py
│   │   │   │   ├── policies.py
│   │   │   │   └── ppo_recurrent.py
│   │   │   ├── py.typed
│   │   │   ├── qrdqn
│   │   │   │   ├── __init__.py
│   │   │   │   ├── policies.py
│   │   │   │   └── qrdqn.py
│   │   │   ├── tqc
│   │   │   │   ├── __init__.py
│   │   │   │   ├── policies.py
│   │   │   │   └── tqc.py
│   │   │   ├── trpo
│   │   │   │   ├── __init__.py
│   │   │   │   ├── policies.py
│   │   │   │   └── trpo.py
│   │   │   └── version.txt
│   │   ├── scripts
│   │   │   └── run_tests.sh
│   │   ├── setup.py
│   │   └── tests
│   │       ├── test_cnn.py
│   │       ├── test_deterministic.py
│   │       ├── test_dict_env.py
│   │       ├── test_distributions.py
│   │       ├── test_identity.py
│   │       ├── test_invalid_actions.py
│   │       ├── test_lstm.py
│   │       ├── test_run.py
│   │       ├── test_save_load.py
│   │       ├── test_train_eval_mode.py
│   │       ├── test_utils.py
│   │       └── wrappers
│   │           ├── test_action_masker.py
│   │           └── test_time_feature.py
│   ├── vectorbt
│   │   ├── apps
│   │   │   └── candlestick-patterns
│   │   │       ├── app.py
│   │   │       ├── assets
│   │   │       │   ├── default.css
│   │   │       │   ├── favicon.ico
│   │   │       │   ├── screenshot.png
│   │   │       │   ├── style.css
│   │   │       │   └── teaser.png
│   │   │       ├── Dockerfile
│   │   │       ├── Procfile
│   │   │       ├── README.md
│   │   │       └── requirements.txt
│   │   ├── benchmarks
│   │   │   ├── bench_engine.py
│   │   │   ├── bench_matrix.py
│   │   │   ├── BENCHMARKS_NUMBA.md
│   │   │   ├── BENCHMARKS_RUST.md
│   │   │   ├── BENCHMARKS.md
│   │   │   └── README.md
│   │   ├── conftest.py
│   │   ├── Dockerfile
│   │   ├── docs
│   │   │   ├── docs
│   │   │   │   ├── assets
│   │   │   │   │   ├── images
│   │   │   │   │   │   ├── ATR.svg
│   │   │   │   │   │   ├── Bar_updated.svg
│   │   │   │   │   │   ├── Bar.svg
│   │   │   │   │   │   ├── basic_price.svg
│   │   │   │   │   │   ├── BBANDS.svg
│   │   │   │   │   │   ├── Box.svg
│   │   │   │   │   │   ├── context_info.png
│   │   │   │   │   │   ├── data_plot.svg
│   │   │   │   │   │   ├── data_plots.svg
│   │   │   │   │   │   ├── df_barplot.svg
│   │   │   │   │   │   ├── df_boxplot.svg
│   │   │   │   │   │   ├── df_heatmap.svg
│   │   │   │   │   │   ├── df_histplot.svg
│   │   │   │   │   │   ├── df_lineplot.svg
│   │   │   │   │   │   ├── df_plot.svg
│   │   │   │   │   │   ├── df_scatterplot.svg
│   │   │   │   │   │   ├── drawdowns_plot.svg
│   │   │   │   │   │   ├── drawdowns_plots.svg
│   │   │   │   │   │   ├── expanding_split_plot.svg
│   │   │   │   │   │   ├── features_qs_plot_snapshot.png
│   │   │   │   │   │   ├── features_scheduler.svg
│   │   │   │   │   │   ├── from_order_func_g1.svg
│   │   │   │   │   │   ├── from_order_func_g2.svg
│   │   │   │   │   │   ├── Gauge.svg
│   │   │   │   │   │   ├── generic_plots.svg
│   │   │   │   │   │   ├── Heatmap.svg
│   │   │   │   │   │   ├── Histogram.svg
│   │   │   │   │   │   ├── index_by_any.svg
│   │   │   │   │   │   ├── index_by_symbol.svg
│   │   │   │   │   │   ├── IndicatorFactory_plots.svg
│   │   │   │   │   │   ├── MA.svg
│   │   │   │   │   │   ├── MACD.svg
│   │   │   │   │   │   ├── mapped_boxplot.svg
│   │   │   │   │   │   ├── mapped_to_pd_plot.svg
│   │   │   │   │   │   ├── MSTD.svg
│   │   │   │   │   │   ├── MyInd_plot.svg
│   │   │   │   │   │   ├── OBV.svg
│   │   │   │   │   │   ├── OHLCSTX.svg
│   │   │   │   │   │   ├── ohlcv_plot.svg
│   │   │   │   │   │   ├── ohlcv_plots.svg
│   │   │   │   │   │   ├── orders_plot.svg
│   │   │   │   │   │   ├── orders_plots.svg
│   │   │   │   │   │   ├── plot_cumulative.svg
│   │   │   │   │   │   ├── portfolio_plot_custom.svg
│   │   │   │   │   │   ├── portfolio_plot_drawdowns.svg
│   │   │   │   │   │   ├── portfolio_plot_path.svg
│   │   │   │   │   │   ├── portfolio_plot_snapshot.png
│   │   │   │   │   │   ├── portfolio_plot.svg
│   │   │   │   │   │   ├── portfolio_value.svg
│   │   │   │   │   │   ├── px_bar.svg
│   │   │   │   │   │   ├── range_split_plot.svg
│   │   │   │   │   │   ├── ranges_plot.svg
│   │   │   │   │   │   ├── ranges_plots.svg
│   │   │   │   │   │   ├── RSI.svg
│   │   │   │   │   │   ├── Scatter.svg
│   │   │   │   │   │   ├── signals_df_plot.svg
│   │   │   │   │   │   ├── signals_plot_as_markers.svg
│   │   │   │   │   │   ├── simulate_nb.gif
│   │   │   │   │   │   ├── simulate_nb.svg
│   │   │   │   │   │   ├── simulate_row_wise_nb.gif
│   │   │   │   │   │   ├── split_plot.svg
│   │   │   │   │   │   ├── sr_heatmap_slider.gif
│   │   │   │   │   │   ├── sr_heatmap.svg
│   │   │   │   │   │   ├── sr_overlay_with_heatmap.svg
│   │   │   │   │   │   ├── sr_plot_against.svg
│   │   │   │   │   │   ├── sr_qqplot.svg
│   │   │   │   │   │   ├── sr_volume.svg
│   │   │   │   │   │   ├── STOCH.svg
│   │   │   │   │   │   ├── trades_plot_pnl.svg
│   │   │   │   │   │   ├── trades_plot.svg
│   │   │   │   │   │   ├── trades_plots.svg
│   │   │   │   │   │   ├── usage_bbands.gif
│   │   │   │   │   │   ├── usage_dmac_heatmap.gif
│   │   │   │   │   │   ├── usage_dmac_portfolio.svg
│   │   │   │   │   │   ├── usage_rand_scatter.svg
│   │   │   │   │   │   └── Volume.svg
│   │   │   │   │   ├── interactive
│   │   │   │   │   │   ├── features_gbm_data.html
│   │   │   │   │   │   ├── features_golden_crossover.html
│   │   │   │   │   │   ├── features_local_extrema.html
│   │   │   │   │   │   ├── features_plot_against.html
│   │   │   │   │   │   ├── features_portfolio_plot.html
│   │   │   │   │   │   ├── features_rolling_split.html
│   │   │   │   │   │   ├── features_top_drawdowns.html
│   │   │   │   │   │   └── features_volume.html
│   │   │   │   │   ├── javascripts
│   │   │   │   │   │   └── extra.js
│   │   │   │   │   ├── logo
│   │   │   │   │   │   ├── apple-touch-icon.png
│   │   │   │   │   │   ├── favicon-96x96.png
│   │   │   │   │   │   ├── favicon.ico
│   │   │   │   │   │   ├── favicon.svg
│   │   │   │   │   │   ├── header-pro.svg
│   │   │   │   │   │   ├── header.svg
│   │   │   │   │   │   ├── logo-white.svg
│   │   │   │   │   │   ├── logo.svg
│   │   │   │   │   │   ├── site.webmanifest
│   │   │   │   │   │   ├── web-app-manifest-192x192.png
│   │   │   │   │   │   └── web-app-manifest-512x512.png
│   │   │   │   │   ├── misc
│   │   │   │   │   │   └── AlgoTradingCookbook.jpg
│   │   │   │   │   └── stylesheets
│   │   │   │   │       └── extra.css
│   │   │   │   ├── CNAME
│   │   │   │   ├── context7.json
│   │   │   │   ├── getting-started
│   │   │   │   │   ├── contributing.md
│   │   │   │   │   ├── features.md
│   │   │   │   │   ├── installation.md
│   │   │   │   │   ├── resources.md
│   │   │   │   │   └── usage.md
│   │   │   │   ├── index.md
│   │   │   │   └── terms
│   │   │   │       ├── index.md
│   │   │   │       └── license.md
│   │   │   ├── generate_api.py
│   │   │   ├── LICENSE.md
│   │   │   ├── mkdocs.yml
│   │   │   ├── overrides
│   │   │   │   └── main.html
│   │   │   ├── README.md
│   │   │   ├── templates
│   │   │   │   └── markdown.mako
│   │   │   └── update_api_nav.py
│   │   ├── examples
│   │   │   ├── BitcoinDMAC.ipynb
│   │   │   ├── dmac_heatmap.gif
│   │   │   ├── MACDVolume.ipynb
│   │   │   ├── PairsTrading.ipynb
│   │   │   ├── PortfolioOptimization.ipynb
│   │   │   ├── PortingBTStrategy.ipynb
│   │   │   ├── requirements-backtrader.txt
│   │   │   ├── StopSignals.ipynb
│   │   │   ├── TelegramSignals.ipynb
│   │   │   ├── TradingSessions.ipynb
│   │   │   └── WalkForwardOptimization.ipynb
│   │   ├── LICENSE.md
│   │   ├── MANIFEST.in
│   │   ├── mypy.ini
│   │   ├── pyproject.toml
│   │   ├── README.md
│   │   ├── rust
│   │   │   ├── Cargo.lock
│   │   │   ├── Cargo.toml
│   │   │   ├── pyproject.toml
│   │   │   ├── README.md
│   │   │   ├── rustfmt.toml
│   │   │   └── src
│   │   │       ├── generic.rs
│   │   │       ├── indicators.rs
│   │   │       ├── labels.rs
│   │   │       ├── lib.rs
│   │   │       ├── portfolio.rs
│   │   │       ├── records.rs
│   │   │       ├── returns.rs
│   │   │       └── signals.rs
│   │   ├── setup.py
│   │   ├── tests
│   │   │   ├── __init__.py
│   │   │   ├── conftest.py
│   │   │   ├── notebooks
│   │   │   │   ├── base.ipynb
│   │   │   │   ├── generic.ipynb
│   │   │   │   ├── indicators.ipynb
│   │   │   │   ├── labels.ipynb
│   │   │   │   ├── ohlcv.ipynb
│   │   │   │   ├── plotting.ipynb
│   │   │   │   ├── portfolio.ipynb
│   │   │   │   ├── records.ipynb
│   │   │   │   ├── returns.ipynb
│   │   │   │   ├── shortcash.ipynb
│   │   │   │   ├── signals.ipynb
│   │   │   │   └── utils.ipynb
│   │   │   ├── test_base.py
│   │   │   ├── test_data.py
│   │   │   ├── test_engine.py
│   │   │   ├── test_generic.py
│   │   │   ├── test_indicators.py
│   │   │   ├── test_labels.py
│   │   │   ├── test_plotting.py
│   │   │   ├── test_portfolio.py
│   │   │   ├── test_records.py
│   │   │   ├── test_returns.py
│   │   │   ├── test_settings.py
│   │   │   ├── test_signals.py
│   │   │   ├── test_utils.py
│   │   │   └── utils.py
│   │   └── vectorbt
│   │       ├── __init__.py
│   │       ├── _engine.py
│   │       ├── _settings.py
│   │       ├── _typing.py
│   │       ├── _version.py
│   │       ├── base
│   │       │   ├── __init__.py
│   │       │   ├── accessors.py
│   │       │   ├── array_wrapper.py
│   │       │   ├── column_grouper.py
│   │       │   ├── combine_fns.py
│   │       │   ├── index_fns.py
│   │       │   ├── indexing.py
│   │       │   └── reshape_fns.py
│   │       ├── data
│   │       │   ├── __init__.py
│   │       │   ├── base.py
│   │       │   ├── custom.py
│   │       │   └── updater.py
│   │       ├── generic
│   │       │   ├── __init__.py
│   │       │   ├── accessors.py
│   │       │   ├── decorators.py
│   │       │   ├── dispatch.py
│   │       │   ├── drawdowns.py
│   │       │   ├── enums.py
│   │       │   ├── nb.py
│   │       │   ├── plots_builder.py
│   │       │   ├── plotting.py
│   │       │   ├── ranges.py
│   │       │   ├── splitters.py
│   │       │   └── stats_builder.py
│   │       ├── indicators
│   │       │   ├── __init__.py
│   │       │   ├── basic.py
│   │       │   ├── configs.py
│   │       │   ├── dispatch.py
│   │       │   ├── factory.py
│   │       │   └── nb.py
│   │       ├── labels
│   │       │   ├── __init__.py
│   │       │   ├── dispatch.py
│   │       │   ├── enums.py
│   │       │   ├── generators.py
│   │       │   └── nb.py
│   │       ├── messaging
│   │       │   ├── __init__.py
│   │       │   └── telegram.py
│   │       ├── ohlcv_accessors.py
│   │       ├── portfolio
│   │       │   ├── __init__.py
│   │       │   ├── base.py
│   │       │   ├── decorators.py
│   │       │   ├── dispatch.py
│   │       │   ├── enums.py
│   │       │   ├── logs.py
│   │       │   ├── nb.py
│   │       │   ├── orders.py
│   │       │   └── trades.py
│   │       ├── px_accessors.py
│   │       ├── records
│   │       │   ├── __init__.py
│   │       │   ├── base.py
│   │       │   ├── col_mapper.py
│   │       │   ├── decorators.py
│   │       │   ├── dispatch.py
│   │       │   ├── mapped_array.py
│   │       │   └── nb.py
│   │       ├── returns
│   │       │   ├── __init__.py
│   │       │   ├── accessors.py
│   │       │   ├── dispatch.py
│   │       │   ├── metrics.py
│   │       │   ├── nb.py
│   │       │   └── qs_adapter.py
│   │       ├── root_accessors.py
│   │       ├── signals
│   │       │   ├── __init__.py
│   │       │   ├── accessors.py
│   │       │   ├── dispatch.py
│   │       │   ├── enums.py
│   │       │   ├── factory.py
│   │       │   ├── generators.py
│   │       │   └── nb.py
│   │       ├── templates
│   │       │   ├── dark.json
│   │       │   ├── light.json
│   │       │   └── seaborn.json
│   │       └── utils
│   │           ├── __init__.py
│   │           ├── array_.py
│   │           ├── attr_.py
│   │           ├── checks.py
│   │           ├── colors.py
│   │           ├── config.py
│   │           ├── datetime_.py
│   │           ├── decorators.py
│   │           ├── docs.py
│   │           ├── enum_.py
│   │           ├── figure.py
│   │           ├── image_.py
│   │           ├── mapping.py
│   │           ├── math_.py
│   │           ├── module_.py
│   │           ├── params.py
│   │           ├── random_.py
│   │           ├── requests_.py
│   │           ├── schedule_.py
│   │           ├── tags.py
│   │           └── template.py
│   ├── vnpy
│   │   ├── CHANGELOG.md
│   │   ├── docs
│   │   │   ├── _static
│   │   │   │   ├── custom.css
│   │   │   │   ├── vendor.css
│   │   │   │   └── vnpy.ico
│   │   │   ├── _templates
│   │   │   │   ├── layout.html
│   │   │   │   ├── relations.html
│   │   │   │   ├── searchbox.html
│   │   │   │   └── sidebarintro.html
│   │   │   ├── community
│   │   │   │   ├── app
│   │   │   │   │   ├── algo_trading.md
│   │   │   │   │   ├── chart_wizard.md
│   │   │   │   │   ├── cta_backtester.md
│   │   │   │   │   ├── cta_strategy.md
│   │   │   │   │   ├── data_manager.md
│   │   │   │   │   ├── data_recorder.md
│   │   │   │   │   ├── excel_rtd.md
│   │   │   │   │   ├── index.rst
│   │   │   │   │   ├── option_master.md
│   │   │   │   │   ├── paper_account.md
│   │   │   │   │   ├── portfolio_manager.md
│   │   │   │   │   ├── portfolio_strategy.md
│   │   │   │   │   ├── risk_manager.md
│   │   │   │   │   ├── rpc_service.md
│   │   │   │   │   ├── script_trader.md
│   │   │   │   │   ├── spread_trading.md
│   │   │   │   │   └── web_trader.md
│   │   │   │   ├── index.rst
│   │   │   │   ├── info
│   │   │   │   │   ├── alpha.md
│   │   │   │   │   ├── contribution.md
│   │   │   │   │   ├── database.md
│   │   │   │   │   ├── datafeed.md
│   │   │   │   │   ├── gateway.md
│   │   │   │   │   ├── i18n.md
│   │   │   │   │   ├── index.rst
│   │   │   │   │   ├── introduction.md
│   │   │   │   │   ├── pycharm.md
│   │   │   │   │   ├── veighna_station.md
│   │   │   │   │   ├── veighna_trader.md
│   │   │   │   │   └── vscode.md
│   │   │   │   └── install
│   │   │   │       ├── index.rst
│   │   │   │       ├── mac_install.md
│   │   │   │       ├── ubuntu_install.md
│   │   │   │       └── windows_install.md
│   │   │   ├── conf.py
│   │   │   ├── elite
│   │   │   │   ├── extension
│   │   │   │   │   ├── elite_algotrading.md
│   │   │   │   │   ├── elite_dingtalk.md
│   │   │   │   │   ├── elite_feishu.md
│   │   │   │   │   ├── elite_ladder.md
│   │   │   │   │   └── index.rst
│   │   │   │   ├── index.rst
│   │   │   │   ├── info
│   │   │   │   │   ├── elite_install.md
│   │   │   │   │   ├── elite_lab.md
│   │   │   │   │   ├── elite_trader.md
│   │   │   │   │   └── index.rst
│   │   │   │   └── strategy
│   │   │   │       ├── elite_algotrading.md
│   │   │   │       ├── elite_ctastrategy.md
│   │   │   │       ├── elite_datamanager.md
│   │   │   │       ├── elite_filter.md
│   │   │   │       ├── elite_function.md
│   │   │   │       ├── elite_optionstrategy.md
│   │   │   │       ├── elite_portfoliostrategy.md
│   │   │   │       ├── elite_riskmanager.md
│   │   │   │       ├── elite_spreadtrading.md
│   │   │   │       └── index.rst
│   │   │   ├── fusion
│   │   │   │   ├── agent
│   │   │   │   │   ├── fusion_agent_config.md
│   │   │   │   │   ├── fusion_agent_intro.md
│   │   │   │   │   ├── fusion_agent_notice.md
│   │   │   │   │   ├── fusion_agent_workflow.md
│   │   │   │   │   └── index.rst
│   │   │   │   ├── index.rst
│   │   │   │   ├── info
│   │   │   │   │   ├── fusion_ctp.md
│   │   │   │   │   ├── fusion_faq.md
│   │   │   │   │   ├── fusion_install.md
│   │   │   │   │   ├── fusion_introduction.md
│   │   │   │   │   ├── fusion_login.md
│   │   │   │   │   ├── fusion_trader.md
│   │   │   │   │   └── index.rst
│   │   │   │   └── strategy
│   │   │   │       ├── fusion_backtester.md
│   │   │   │       ├── fusion_cta.md
│   │   │   │       ├── fusion_data.md
│   │   │   │       ├── fusion_risk.md
│   │   │   │       └── index.rst
│   │   │   └── index.rst
│   │   ├── examples
│   │   │   ├── alpha_research
│   │   │   │   ├── download_data_rq.ipynb
│   │   │   │   ├── download_data_xt.ipynb
│   │   │   │   ├── research_workflow_alpha101.ipynb
│   │   │   │   ├── research_workflow_lasso.ipynb
│   │   │   │   ├── research_workflow_lgb.ipynb
│   │   │   │   └── research_workflow_mlp.ipynb
│   │   │   ├── candle_chart
│   │   │   │   └── run.py
│   │   │   ├── client_server
│   │   │   │   ├── run_client.py
│   │   │   │   └── run_server.py
│   │   │   ├── cta_backtesting
│   │   │   │   ├── backtesting_demo.ipynb
│   │   │   │   └── portfolio_backtesting.ipynb
│   │   │   ├── data_recorder
│   │   │   │   └── data_recorder.py
│   │   │   ├── download_bars
│   │   │   │   └── download_bars.ipynb
│   │   │   ├── no_ui
│   │   │   │   └── run.py
│   │   │   ├── notebook_trading
│   │   │   │   └── demo_notebook.ipynb
│   │   │   ├── portfolio_backtesting
│   │   │   │   └── backtesting_demo.ipynb
│   │   │   ├── simple_rpc
│   │   │   │   ├── test_client.py
│   │   │   │   └── test_server.py
│   │   │   ├── spread_backtesting
│   │   │   │   └── backtesting.ipynb
│   │   │   └── veighna_trader
│   │   │       ├── demo_script.py
│   │   │       └── run.py
│   │   ├── install_osx.sh
│   │   ├── install.bat
│   │   ├── install.sh
│   │   ├── LICENSE
│   │   ├── pyproject.toml
│   │   ├── README_ENG.md
│   │   ├── README.md
│   │   ├── tests
│   │   │   ├── alpha
│   │   │   │   └── test_dataproxy.py
│   │   │   └── test_alpha101.py
│   │   └── vnpy
│   │       ├── __init__.py
│   │       ├── __pycache__
│   │       │   └── __init__.cpython-312.pyc
│   │       ├── alpha
│   │       │   ├── __init__.py
│   │       │   ├── __pycache__
│   │       │   │   ├── __init__.cpython-312.pyc
│   │       │   │   ├── lab.cpython-312.pyc
│   │       │   │   └── logger.cpython-312.pyc
│   │       │   ├── dataset
│   │       │   │   ├── __init__.py
│   │       │   │   ├── __pycache__
│   │       │   │   │   ├── __init__.cpython-312.pyc
│   │       │   │   │   ├── processor.cpython-312.pyc
│   │       │   │   │   ├── template.cpython-312.pyc
│   │       │   │   │   └── utility.cpython-312.pyc
│   │       │   │   ├── cs_function.py
│   │       │   │   ├── datasets
│   │       │   │   │   ├── __init__.py
│   │       │   │   │   ├── alpha_101.py
│   │       │   │   │   └── alpha_158.py
│   │       │   │   ├── math_function.py
│   │       │   │   ├── processor.py
│   │       │   │   ├── ta_function.py
│   │       │   │   ├── template.py
│   │       │   │   ├── ts_function.py
│   │       │   │   └── utility.py
│   │       │   ├── lab.py
│   │       │   ├── logger.py
│   │       │   ├── model
│   │       │   │   ├── __init__.py
│   │       │   │   ├── __pycache__
│   │       │   │   │   ├── __init__.cpython-312.pyc
│   │       │   │   │   └── template.cpython-312.pyc
│   │       │   │   ├── models
│   │       │   │   │   ├── __init__.py
│   │       │   │   │   ├── lasso_model.py
│   │       │   │   │   ├── lgb_model.py
│   │       │   │   │   └── mlp_model.py
│   │       │   │   └── template.py
│   │       │   └── strategy
│   │       │       ├── __init__.py
│   │       │       ├── __pycache__
│   │       │       │   ├── __init__.cpython-312.pyc
│   │       │       │   ├── backtesting.cpython-312.pyc
│   │       │       │   └── template.cpython-312.pyc
│   │       │       ├── backtesting.py
│   │       │       ├── strategies
│   │       │       │   ├── __init__.py
│   │       │       │   └── equity_demo_strategy.py
│   │       │       └── template.py
│   │       ├── chart
│   │       │   ├── __init__.py
│   │       │   ├── axis.py
│   │       │   ├── base.py
│   │       │   ├── item.py
│   │       │   ├── manager.py
│   │       │   └── widget.py
│   │       ├── event
│   │       │   ├── __init__.py
│   │       │   ├── __pycache__
│   │       │   │   ├── __init__.cpython-312.pyc
│   │       │   │   └── engine.cpython-312.pyc
│   │       │   └── engine.py
│   │       ├── py.typed
│   │       ├── rpc
│   │       │   ├── __init__.py
│   │       │   ├── client.py
│   │       │   ├── common.py
│   │       │   └── server.py
│   │       └── trader
│   │           ├── __init__.py
│   │           ├── __pycache__
│   │           │   ├── __init__.cpython-312.pyc
│   │           │   ├── constant.cpython-312.pyc
│   │           │   ├── event.cpython-312.pyc
│   │           │   ├── gateway.cpython-312.pyc
│   │           │   ├── object.cpython-312.pyc
│   │           │   └── utility.cpython-312.pyc
│   │           ├── app.py
│   │           ├── constant.py
│   │           ├── converter.py
│   │           ├── database.py
│   │           ├── datafeed.py
│   │           ├── engine.py
│   │           ├── event.py
│   │           ├── gateway.py
│   │           ├── locale
│   │           │   ├── __init__.py
│   │           │   ├── __pycache__
│   │           │   │   ├── __init__.cpython-312.pyc
│   │           │   │   └── build_hook.cpython-312.pyc
│   │           │   ├── build_hook.py
│   │           │   ├── en
│   │           │   │   └── LC_MESSAGES
│   │           │   │       ├── vnpy.mo
│   │           │   │       └── vnpy.po
│   │           │   ├── generate_mo.bat
│   │           │   ├── generate_pot.bat
│   │           │   └── vnpy.pot
│   │           ├── logger.py
│   │           ├── object.py
│   │           ├── optimize.py
│   │           ├── setting.py
│   │           ├── ui
│   │           │   ├── __init__.py
│   │           │   ├── ico
│   │           │   │   ├── __init__.py
│   │           │   │   ├── about.ico
│   │           │   │   ├── connect.ico
│   │           │   │   ├── contract.ico
│   │           │   │   ├── database.ico
│   │           │   │   ├── editor.ico
│   │           │   │   ├── email.ico
│   │           │   │   ├── exit.ico
│   │           │   │   ├── forum.ico
│   │           │   │   ├── restore.ico
│   │           │   │   ├── test.ico
│   │           │   │   └── vnpy.ico
│   │           │   ├── mainwindow.py
│   │           │   ├── qt.py
│   │           │   └── widget.py
│   │           ├── utility.py
│   │           └── wechat.py
│   └── vnpy_ib
│       ├── CHANGELOG.md
│       ├── LICENSE
│       ├── pyproject.toml
│       ├── README.md
│       ├── script
│       │   └── run.py
│       └── vnpy_ib
│           ├── __init__.py
│           ├── __pycache__
│           │   ├── __init__.cpython-312.pyc
│           │   └── ib_gateway.cpython-312.pyc
│           └── ib_gateway.py
├── REPO_TREE.txt
├── scripts
│   ├── adjust_intraday_splits.py
│   ├── download_market_data.py
│   ├── evaluate_rl.py
│   ├── generate_smoke_data.py
│   ├── run_shadow_policy.py
│   ├── train_rl.py
│   └── validate_rl_data.py
├── setup_extra_agents_vnpy_macos.sh
├── setup_quant_stack_macos.sh
├── src
│   ├── stocks
│   │   ├── __init__.py
│   │   ├── __pycache__
│   │   │   └── __init__.cpython-312.pyc
│   │   ├── contracts
│   │   │   ├── __init__.py
│   │   │   ├── __pycache__
│   │   │   │   ├── __init__.cpython-312.pyc
│   │   │   │   └── trade_intent.cpython-312.pyc
│   │   │   └── trade_intent.py
│   │   ├── intelligence_agent
│   │   │   ├── __init__.py
│   │   │   ├── __pycache__
│   │   │   │   ├── __init__.cpython-312.pyc
│   │   │   │   ├── agent.cpython-312.pyc
│   │   │   │   ├── allocator.cpython-312.pyc
│   │   │   │   ├── config.cpython-312.pyc
│   │   │   │   ├── indicators.cpython-312.pyc
│   │   │   │   ├── models.cpython-312.pyc
│   │   │   │   └── scoring.cpython-312.pyc
│   │   │   ├── agent.py
│   │   │   ├── allocator.py
│   │   │   ├── config.py
│   │   │   ├── indicators.py
│   │   │   ├── models.py
│   │   │   ├── nlp
│   │   │   │   ├── __init__.py
│   │   │   │   ├── __pycache__
│   │   │   │   │   ├── __init__.cpython-312.pyc
│   │   │   │   │   └── engine.cpython-312.pyc
│   │   │   │   └── engine.py
│   │   │   ├── providers
│   │   │   │   ├── __init__.py
│   │   │   │   ├── eodhd.py
│   │   │   │   ├── fred.py
│   │   │   │   └── openfx.py
│   │   │   ├── scoring.py
│   │   │   └── store.py
│   │   ├── orchestration
│   │   │   ├── __init__.py
│   │   │   └── decision_pipeline.py
│   │   └── rl
│   │       ├── __init__.py
│   │       ├── __pycache__
│   │       │   ├── __init__.cpython-312.pyc
│   │       │   ├── config.cpython-312.pyc
│   │       │   ├── environment.cpython-312.pyc
│   │       │   ├── evaluator.cpython-312.pyc
│   │       │   ├── features.cpython-312.pyc
│   │       │   ├── rewards.cpython-312.pyc
│   │       │   ├── shadow_policy.cpython-312.pyc
│   │       │   ├── splits.cpython-312.pyc
│   │       │   └── trainer.cpython-312.pyc
│   │       ├── config.py
│   │       ├── environment.py
│   │       ├── evaluator.py
│   │       ├── features.py
│   │       ├── rewards.py
│   │       ├── shadow_policy.py
│   │       ├── splits.py
│   │       └── trainer.py
│   └── stocks_quant_agent_final.egg-info
│       ├── dependency_links.txt
│       ├── PKG-INFO
│       ├── requires.txt
│       ├── SOURCES.txt
│       └── top_level.txt
├── structuur.md
├── tests
│   ├── __pycache__
│   │   ├── test_intelligence_smoke.cpython-312-pytest-9.1.1.pyc
│   │   ├── test_rl_features.cpython-312-pytest-9.1.1.pyc
│   │   ├── test_rl_rewards.cpython-312-pytest-9.1.1.pyc
│   │   ├── test_splits.cpython-312-pytest-9.1.1.pyc
│   │   └── test_trade_intent.cpython-312-pytest-9.1.1.pyc
│   ├── test_intelligence_smoke.py
│   ├── test_rl_features.py
│   ├── test_rl_rewards.py
│   ├── test_splits.py
│   └── test_trade_intent.py
└── verify_extra_agents_vnpy.py

1866 directories, 13270 files
```
