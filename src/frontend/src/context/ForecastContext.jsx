import { createContext, useContext, useState, useCallback } from 'react'
import { forecastAPI, scenarioAPI } from '../utils/api'

const ForecastContext = createContext()

export function ForecastProvider({ children }) {
  const [forecast, setForecast] = useState(null)
  const [scenarios, setScenarios] = useState([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState(null)

  const generateForecast = useCallback(async (days = 42) => {
    setIsLoading(true)
    setError(null)
    try {
      const response = await forecastAPI.generate(days)
      setForecast(response.data)
      return response.data
    } catch (err) {
      setError(err.message)
      throw err
    } finally {
      setIsLoading(false)
    }
  }, [])

  const runScenario = useCallback(async (description, language = 'en') => {
    setIsLoading(true)
    setError(null)
    try {
      const response = await scenarioAPI.analyze(description, language)
      setScenarios((current) => [...current, response.data])
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
      value={{ forecast, scenarios, isLoading, error, generateForecast, runScenario }}
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
