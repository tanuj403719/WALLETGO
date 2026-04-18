import { createContext, useContext, useState, useCallback } from 'react'
import { forecastAPI, scenarioAPI } from '../utils/api'

const ForecastContext = createContext()

export function ForecastProvider({ children }) {
  const [forecast, setForecast] = useState(null)
  const [scenarios, setScenarios] = useState([])
  const [savedScenarios, setSavedScenarios] = useState([])
  const [scenarioComparison, setScenarioComparison] = useState(null)
  const [ephemeralTransactions, setEphemeralTransactions] = useState([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState(null)

  const setDemoTransactions = useCallback((transactions = []) => {
    setEphemeralTransactions(Array.isArray(transactions) ? transactions : [])
    setForecast(null)
    setScenarios([])
  }, [])

  const clearDemoTransactions = useCallback(() => {
    setEphemeralTransactions([])
  }, [])

  const generateForecast = useCallback(async (days = 42) => {
    setIsLoading(true)
    setError(null)
    try {
      const response = await forecastAPI.generate(days, ephemeralTransactions)
      setForecast(response.data)
      return response.data
    } catch (err) {
      setError(err.message)
      throw err
    } finally {
      setIsLoading(false)
    }
  }, [ephemeralTransactions])

  const runScenario = useCallback(async (description, language = 'en') => {
    setIsLoading(true)
    setError(null)
    try {
      const response = await scenarioAPI.analyze(description, language, ephemeralTransactions)
      setScenarios((current) => [...current, response.data])
      return response.data
    } catch (err) {
      setError(err.message)
      throw err
    } finally {
      setIsLoading(false)
    }
  }, [ephemeralTransactions])

  const loadSavedScenarios = useCallback(async (limit = 10) => {
    setIsLoading(true)
    setError(null)
    try {
      const response = await scenarioAPI.getSaved(limit)
      const items = response.data?.items || []
      setSavedScenarios(items)
      return items
    } catch (err) {
      setError(err.message)
      throw err
    } finally {
      setIsLoading(false)
    }
  }, [])

  const saveScenario = useCallback(async (payload) => {
    setIsLoading(true)
    setError(null)
    try {
      const response = await scenarioAPI.save(payload)
      const saved = response.data?.scenario
      if (saved) {
        setSavedScenarios((current) => [saved, ...current.filter((item) => item.id !== saved.id)])
      }
      return response.data
    } catch (err) {
      setError(err.message)
      throw err
    } finally {
      setIsLoading(false)
    }
  }, [])

  const compareSavedScenarios = useCallback(async (leftId, rightId) => {
    setIsLoading(true)
    setError(null)
    try {
      const response = await scenarioAPI.compare(leftId, rightId)
      setScenarioComparison(response.data)
      return response.data
    } catch (err) {
      setError(err.message)
      throw err
    } finally {
      setIsLoading(false)
    }
  }, [])

  return (
    <ForecastContext.Provider
      value={{
        forecast,
        scenarios,
        savedScenarios,
        scenarioComparison,
        ephemeralTransactions,
        isLoading,
        error,
        generateForecast,
        runScenario,
        loadSavedScenarios,
        saveScenario,
        compareSavedScenarios,
        setEphemeralTransactions: setDemoTransactions,
        clearEphemeralTransactions: clearDemoTransactions,
      }}
    >
      {children}
    </ForecastContext.Provider>
  )
}

export function useForecast() {
  const context = useContext(ForecastContext)
  if (!context) {
    throw new Error('useForecast must be used within ForecastProvider')
  }
  return context
}
