import { createContext, useContext, useState, useCallback } from 'react'
import { forecastAPI, scenarioAPI } from '../utils/api'

const ForecastContext = createContext()

export function ForecastProvider({ children }) {
  const [forecast, setForecast] = useState(null)
  const [scenarios, setScenarios] = useState([])
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

  return (
    <ForecastContext.Provider
      value={{
        forecast,
        scenarios,
        ephemeralTransactions,
        isLoading,
        error,
        generateForecast,
        runScenario,
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
